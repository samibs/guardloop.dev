"""Claude CLI adapter"""

import subprocess
from typing import Optional

import structlog

from .base import AIResponse, BaseAdapter

logger = structlog.get_logger(__name__)


class ClaudeAdapter(BaseAdapter):
    """Adapter for Anthropic's Claude CLI"""

    def __init__(self, cli_path: str = "claude", timeout: int = 30):
        super().__init__(cli_path, timeout)
        self.tool_name = "Claude"

    async def execute(self, prompt: str, timeout: Optional[int] = None, stream_callback=None) -> AIResponse:
        """Execute Claude with the given prompt

        Args:
            prompt: Enhanced prompt to send to Claude
            timeout: Optional timeout override
            stream_callback: Optional async callback for real-time output streaming

        Returns:
            AIResponse with Claude's output
        """
        logger.info(
            "Executing Claude",
            prompt_length=len(prompt),
            timeout=timeout or self.timeout,
        )

        return await self._execute_with_retry(prompt, timeout, stream_callback)

    def validate_installation(self) -> bool:
        """Validate that Claude CLI is installed

        Returns:
            True if Claude is available
        """
        if not self.is_installed():
            logger.warning("Claude CLI not found in PATH", cli_path=self.cli_path)
            return False

        try:
            # Try to get version to confirm it works
            version = self.get_version()
            logger.info("Claude CLI validated", version=version)
            return True

        except Exception as e:
            logger.error("Claude CLI validation failed", error=str(e))
            return False

    def get_version(self) -> str:
        """Get Claude CLI version

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
            logger.warning("Claude version check timed out")
            return "timeout"

        except Exception as e:
            logger.error("Error getting Claude version", error=str(e))
            return "error"
