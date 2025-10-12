"""Codex CLI adapter"""

import subprocess
from typing import Optional

import structlog

from .base import AIResponse, BaseAdapter

logger = structlog.get_logger(__name__)


class CodexAdapter(BaseAdapter):
    """Adapter for OpenAI's Codex CLI"""

    def __init__(self, cli_path: str = "codex", timeout: int = 30):
        super().__init__(cli_path, timeout)
        self.tool_name = "Codex"

    async def execute(
        self, prompt: str, timeout: Optional[int] = None, stream_callback=None
    ) -> AIResponse:
        """Execute Codex with the given prompt

        Args:
            prompt: Enhanced prompt to send to Codex
            timeout: Optional timeout override
            stream_callback: Optional async callback for real-time output streaming

        Returns:
            AIResponse with Codex's output
        """
        logger.info(
            "Executing Codex",
            prompt_length=len(prompt),
            timeout=timeout or self.timeout,
        )

        return await self._execute_with_retry(prompt, timeout, stream_callback)

    def _build_command(self, prompt: str) -> list[str]:
        """Build the command list for the Codex CLI."""
        # Assuming a command structure like: codex complete "prompt"
        # This can be easily adjusted to the actual CLI syntax.
        return [self.cli_path, "complete", prompt]

    def validate_installation(self) -> bool:
        """Validate that Codex CLI is installed

        Returns:
            True if Codex is available
        """
        if not self.is_installed():
            logger.warning("Codex CLI not found in PATH", cli_path=self.cli_path)
            return False

        try:
            # Try to get version to confirm it works
            version = self.get_version()
            logger.info("Codex CLI validated", version=version)
            return True

        except Exception as e:
            logger.error("Codex CLI validation failed", error=str(e))
            return False

    def get_version(self) -> str:
        """Get Codex CLI version

        Returns:
            Version string or "unknown"
        """
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                version = self._parse_version(result.stdout)
                return version

            return "unknown"

        except subprocess.TimeoutExpired:
            logger.warning("Codex version check timed out")
            return "timeout"

        except Exception as e:
            logger.error("Error getting Codex version", error=str(e))
            return "error"
