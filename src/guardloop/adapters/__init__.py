"""AI tool adapters for guardloop.dev"""

from typing import Dict, Type

import structlog

from .base import AIResponse, BaseAdapter
from .claude import ClaudeAdapter
from .codex import CodexAdapter
from .gemini import GeminiAdapter

logger = structlog.get_logger(__name__)

__all__ = [
    "AIResponse",
    "BaseAdapter",
    "ClaudeAdapter",
    "GeminiAdapter",
    "CodexAdapter",
    "AdapterFactory",
]


class AdapterFactory:
    """Factory for creating AI tool adapters"""

    _adapters: Dict[str, Type[BaseAdapter]] = {
        "claude": ClaudeAdapter,
        "gemini": GeminiAdapter,
        "codex": CodexAdapter,
    }

    @classmethod
    def get_adapter(
        cls, tool: str, cli_path: str = None, timeout: int = 30
    ) -> BaseAdapter:
        """Get an adapter for the specified tool

        Args:
            tool: Tool name (claude, gemini, codex)
            cli_path: Optional CLI path override
            timeout: Execution timeout in seconds

        Returns:
            Configured adapter instance

        Raises:
            ValueError: If tool is not supported
        """
        tool_lower = tool.lower()

        if tool_lower not in cls._adapters:
            available = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Unsupported AI tool: {tool}. Available tools: {available}"
            )

        adapter_class = cls._adapters[tool_lower]

        if cli_path:
            adapter = adapter_class(cli_path=cli_path, timeout=timeout)
        else:
            adapter = adapter_class(timeout=timeout)

        logger.info("Adapter created", tool=tool, adapter=adapter_class.__name__)
        return adapter

    @classmethod
    def get_supported_tools(cls) -> list[str]:
        """Get list of supported AI tools

        Returns:
            List of tool names
        """
        return list(cls._adapters.keys())

    @classmethod
    def validate_all_tools(cls, tools_config: dict) -> Dict[str, bool]:
        """Validate all configured tools

        Args:
            tools_config: Configuration dict with tool settings

        Returns:
            Dictionary mapping tool names to validation status
        """
        results = {}

        for tool_name, config in tools_config.items():
            if not config.get("enabled", False):
                results[tool_name] = False
                continue

            try:
                cli_path = config.get("cli_path", tool_name)
                timeout = config.get("timeout", 30)

                adapter = cls.get_adapter(tool_name, cli_path=cli_path, timeout=timeout)
                results[tool_name] = adapter.validate_installation()

            except Exception as e:
                logger.error(
                    "Error validating tool", tool=tool_name, error=str(e)
                )
                results[tool_name] = False

        return results
