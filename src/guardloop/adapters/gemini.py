"""Gemini CLI adapter"""

import subprocess
from typing import Optional

import structlog

from .base import AIResponse, BaseAdapter

logger = structlog.get_logger(__name__)


class GeminiAdapter(BaseAdapter):
    """Adapter for Google's Gemini CLI"""

    def __init__(self, cli_path: str = "gemini", timeout: int = 30):
        super().__init__(cli_path, timeout)
        self.tool_name = "Gemini"

    async def execute(self, prompt: str, timeout: Optional[int] = None) -> AIResponse:
        """Execute Gemini with the given prompt

        Args:
            prompt: Enhanced prompt to send to Gemini
            timeout: Optional timeout override

        Returns:
            AIResponse with Gemini's output
        """
        logger.info(
            "Executing Gemini",
            prompt_length=len(prompt),
            timeout=timeout or self.timeout,
        )

        return await self._execute_with_retry(prompt, timeout)

    def validate_installation(self) -> bool:
        """Validate that Gemini CLI is installed

        Returns:
            True if Gemini is available
        """
        if not self.is_installed():
            logger.warning("Gemini CLI not found in PATH", cli_path=self.cli_path)
            return False

        try:
            # Try to get version to confirm it works
            version = self.get_version()
            logger.info("Gemini CLI validated", version=version)
            return True

        except Exception as e:
            logger.error("Gemini CLI validation failed", error=str(e))
            return False

    def get_version(self) -> str:
        """Get Gemini CLI version

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
            logger.warning("Gemini version check timed out")
            return "timeout"

        except Exception as e:
            logger.error("Error getting Gemini version", error=str(e))
            return "error"
