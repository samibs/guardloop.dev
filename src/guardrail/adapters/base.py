"""Base adapter for AI tools"""

import asyncio
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AIResponse:
    """Response from AI tool execution"""

    raw_output: str
    execution_time_ms: int
    error: Optional[str] = None
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""


class BaseAdapter(ABC):
    """Base class for AI tool adapters"""

    def __init__(self, cli_path: str, timeout: int = 30):
        """Initialize adapter

        Args:
            cli_path: Path to the CLI tool executable
            timeout: Execution timeout in seconds
        """
        self.cli_path = cli_path
        self.timeout = timeout
        self.max_retries = 3
        self.retry_delay = 1  # seconds

        logger.info(
            "Adapter initialized", tool=self.__class__.__name__, cli_path=cli_path, timeout=timeout
        )

    @abstractmethod
    async def execute(self, prompt: str, timeout: Optional[int] = None) -> AIResponse:
        """Execute the AI tool with the given prompt

        Args:
            prompt: Enhanced prompt to send to AI
            timeout: Optional timeout override

        Returns:
            AIResponse with execution results
        """
        pass

    @abstractmethod
    def validate_installation(self) -> bool:
        """Validate that the AI tool is properly installed

        Returns:
            True if tool is available, False otherwise
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Get the version of the AI tool

        Returns:
            Version string or "unknown"
        """
        pass

    def is_installed(self) -> bool:
        """Check if the tool command exists in PATH

        Returns:
            True if command is found
        """
        return shutil.which(self.cli_path) is not None

    async def _execute_with_retry(
        self, prompt: str, timeout: Optional[int] = None
    ) -> AIResponse:
        """Execute command with retry logic

        Args:
            prompt: Prompt to execute
            timeout: Optional timeout

        Returns:
            AIResponse
        """
        timeout = timeout or self.timeout
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "Executing AI tool",
                    tool=self.__class__.__name__,
                    attempt=attempt,
                    timeout=timeout,
                )

                response = await self._execute_subprocess(prompt, timeout)

                if response.exit_code == 0:
                    logger.info(
                        "AI tool executed successfully",
                        tool=self.__class__.__name__,
                        execution_time_ms=response.execution_time_ms,
                    )
                    return response

                last_error = response.error or f"Exit code: {response.exit_code}"
                logger.warning(
                    "AI tool execution failed",
                    tool=self.__class__.__name__,
                    attempt=attempt,
                    error=last_error,
                )

            except asyncio.TimeoutError:
                last_error = f"Timeout after {timeout} seconds"
                logger.warning(
                    "AI tool timeout",
                    tool=self.__class__.__name__,
                    attempt=attempt,
                    timeout=timeout,
                )

            except Exception as e:
                last_error = str(e)
                logger.error(
                    "AI tool execution error",
                    tool=self.__class__.__name__,
                    attempt=attempt,
                    error=str(e),
                )

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                wait_time = self.retry_delay * (2 ** (attempt - 1))
                logger.debug("Retrying after delay", wait_time=wait_time)
                await asyncio.sleep(wait_time)

        # All retries failed
        logger.error(
            "AI tool execution failed after all retries",
            tool=self.__class__.__name__,
            max_retries=self.max_retries,
            last_error=last_error,
        )

        return AIResponse(
            raw_output="", execution_time_ms=0, error=last_error, exit_code=1, stdout="", stderr=""
        )

    async def _execute_subprocess(self, prompt: str, timeout: int) -> AIResponse:
        """Execute subprocess and capture output

        Args:
            prompt: Prompt to execute
            timeout: Timeout in seconds

        Returns:
            AIResponse
        """
        import time

        start_time = time.time()

        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            self.cli_path,
            prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            stdout_str = stdout.decode("utf-8", errors="replace").strip()
            stderr_str = stderr.decode("utf-8", errors="replace").strip()

            return AIResponse(
                raw_output=stdout_str,
                execution_time_ms=execution_time_ms,
                error=stderr_str if stderr_str else None,
                exit_code=process.returncode or 0,
                stdout=stdout_str,
                stderr=stderr_str,
            )

        except asyncio.TimeoutError:
            # Kill the process
            try:
                process.kill()
                await process.wait()
            except:
                pass
            raise

    def _parse_version(self, version_output: str) -> str:
        """Parse version from command output

        Args:
            version_output: Raw version command output

        Returns:
            Cleaned version string
        """
        # Extract version number from common patterns
        import re

        patterns = [
            r"version\s+([0-9.]+)",
            r"v([0-9.]+)",
            r"([0-9]+\.[0-9]+\.[0-9]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, version_output, re.IGNORECASE)
            if match:
                return match.group(1)

        return version_output.strip()[:50]  # Fallback: first 50 chars
