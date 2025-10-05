"""Response parser for extracting structured data from AI outputs"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CodeBlock:
    """Represents a code block from AI output"""

    language: str
    content: str
    file_path: Optional[str] = None
    line_range: Optional[Tuple[int, int]] = None
    is_inline: bool = False


@dataclass
class ParsedResponse:
    """Structured data extracted from AI response"""

    code_blocks: List[CodeBlock] = field(default_factory=list)
    file_paths: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)
    test_coverage: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseParser:
    """Parser for AI tool responses"""

    # Code block patterns
    CODE_BLOCK_PATTERN = re.compile(
        r"```(\w+)?\n(.*?)```", re.DOTALL | re.MULTILINE
    )
    INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")

    # File path patterns
    FILE_PATH_PATTERNS = [
        re.compile(r"(?:^|\s)([a-zA-Z]:/[^\s]+)"),  # Windows absolute
        re.compile(r"(?:^|\s)(/[^\s]+\.[a-zA-Z0-9]+)"),  # Unix absolute
        re.compile(r"(?:^|\s)(\.{1,2}/[^\s]+)"),  # Relative paths
        re.compile(
            r"(?:File|Path|Location):\s*([^\n]+)"
        ),  # Explicit file mentions
        re.compile(
            r"in\s+`?([a-zA-Z_][a-zA-Z0-9_/\\\.]+\.[a-zA-Z0-9]+)`?"
        ),  # "in file.py"
    ]

    # Command patterns
    COMMAND_PATTERNS = [
        re.compile(r"^\$\s+(.+)$", re.MULTILINE),  # Shell commands with $
        re.compile(r"^>\s+(.+)$", re.MULTILINE),  # Shell commands with >
        re.compile(r"^(?:npm|pip|dotnet|cargo|go)\s+(.+)$", re.MULTILINE),
        re.compile(r"Run:\s*`?(.+?)`?$", re.MULTILINE | re.IGNORECASE),
        re.compile(r"Execute:\s*`?(.+?)`?$", re.MULTILINE | re.IGNORECASE),
    ]

    # Coverage patterns
    COVERAGE_PATTERNS = [
        re.compile(r"(\d+(?:\.\d+)?)\s*%\s*coverage", re.IGNORECASE),
        re.compile(r"coverage(?:\s+is)?\s*:?\s*(\d+(?:\.\d+)?)\s*%", re.IGNORECASE),
        re.compile(r"(\d+(?:\.\d+)?)\s*%\s*tested", re.IGNORECASE),
        re.compile(r"coverage\s+is\s+(\d+(?:\.\d+)?)\s*%", re.IGNORECASE),
    ]

    # Language file extensions mapping
    LANGUAGE_EXTENSIONS = {
        "python": [".py", ".pyw"],
        "javascript": [".js", ".jsx", ".mjs"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "csharp": [".cs"],
        "c": [".c", ".h"],
        "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hh"],
        "go": [".go"],
        "rust": [".rs"],
        "ruby": [".rb"],
        "php": [".php"],
        "swift": [".swift"],
        "kotlin": [".kt"],
        "sql": [".sql"],
        "html": [".html", ".htm"],
        "css": [".css", ".scss", ".sass"],
        "yaml": [".yaml", ".yml"],
        "json": [".json"],
        "xml": [".xml"],
        "markdown": [".md"],
        "bash": [".sh", ".bash"],
    }

    def parse(self, text: str) -> ParsedResponse:
        """Parse AI response into structured data

        Args:
            text: Raw AI response text

        Returns:
            ParsedResponse with extracted data
        """
        logger.info("Parsing AI response", text_length=len(text))

        response = ParsedResponse()

        # Extract all components
        response.code_blocks = self.extract_code_blocks(text)
        response.file_paths = self.extract_file_paths(text)
        response.commands = self.extract_commands(text)
        response.explanations = self.extract_explanations(text)
        response.test_coverage = self.extract_test_coverage(text)
        response.metadata = self._extract_metadata(text)

        logger.info(
            "Response parsed",
            code_blocks=len(response.code_blocks),
            file_paths=len(response.file_paths),
            commands=len(response.commands),
            explanations=len(response.explanations),
            coverage=response.test_coverage,
        )

        return response

    def extract_code_blocks(self, text: str) -> List[CodeBlock]:
        """Extract code blocks from text

        Args:
            text: Text to parse

        Returns:
            List of CodeBlock objects
        """
        blocks = []

        # Extract fenced code blocks (```language ... ```)
        for match in self.CODE_BLOCK_PATTERN.finditer(text):
            language = (match.group(1) or "text").lower()
            content = match.group(2).strip()

            # Try to extract file path from content
            file_path = None
            line_range = None

            # Check for file path in first line comment
            first_line = content.split("\n")[0] if content else ""
            for pattern in self.FILE_PATH_PATTERNS:
                path_match = pattern.search(first_line)
                if path_match:
                    file_path = path_match.group(1).strip()
                    break

            blocks.append(
                CodeBlock(
                    language=language,
                    content=content,
                    file_path=file_path,
                    line_range=line_range,
                    is_inline=False,
                )
            )

        logger.debug("Extracted code blocks", count=len(blocks))
        return blocks

    def extract_file_paths(self, text: str) -> List[str]:
        """Extract file paths from text

        Args:
            text: Text to parse

        Returns:
            List of unique file paths
        """
        paths = set()

        for pattern in self.FILE_PATH_PATTERNS:
            for match in pattern.finditer(text):
                path = match.group(1).strip()
                # Basic validation
                if self._is_valid_file_path(path):
                    paths.add(path)

        logger.debug("Extracted file paths", count=len(paths))
        return sorted(paths)

    def extract_commands(self, text: str) -> List[str]:
        """Extract shell/package manager commands from text

        Args:
            text: Text to parse

        Returns:
            List of commands
        """
        commands = []

        for pattern in self.COMMAND_PATTERNS:
            for match in pattern.finditer(text):
                command = match.group(1).strip()
                if command and len(command) > 2:  # Basic validation
                    commands.append(command)

        logger.debug("Extracted commands", count=len(commands))
        return commands

    def extract_test_coverage(self, text: str) -> Optional[float]:
        """Extract test coverage percentage from text

        Args:
            text: Text to parse

        Returns:
            Coverage percentage or None
        """
        for pattern in self.COVERAGE_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    coverage = float(match.group(1))
                    if 0 <= coverage <= 100:
                        logger.debug("Extracted test coverage", coverage=coverage)
                        return coverage
                except ValueError:
                    continue

        return None

    def extract_explanations(self, text: str) -> List[str]:
        """Extract explanation/documentation text sections

        Args:
            text: Text to parse

        Returns:
            List of explanation paragraphs
        """
        # Remove code blocks first
        text_without_code = self.CODE_BLOCK_PATTERN.sub("", text)

        # Split into paragraphs
        paragraphs = [p.strip() for p in text_without_code.split("\n\n")]

        # Filter out empty and very short paragraphs
        explanations = [
            p
            for p in paragraphs
            if p and len(p) > 20 and not self._is_command_like(p)
        ]

        logger.debug("Extracted explanations", count=len(explanations))
        return explanations

    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from response

        Args:
            text: Text to parse

        Returns:
            Metadata dictionary
        """
        metadata: Dict[str, Any] = {}

        # Extract agent decisions/reasoning
        reasoning_patterns = [
            re.compile(r"Reasoning:\s*(.+?)(?:\n\n|\Z)", re.DOTALL | re.IGNORECASE),
            re.compile(r"Decision:\s*(.+?)(?:\n\n|\Z)", re.DOTALL | re.IGNORECASE),
            re.compile(r"Analysis:\s*(.+?)(?:\n\n|\Z)", re.DOTALL | re.IGNORECASE),
        ]

        for pattern in reasoning_patterns:
            match = pattern.search(text)
            if match:
                key = pattern.pattern.split(":")[0].lower()
                metadata[key] = match.group(1).strip()

        # Count technical terms
        metadata["has_security_mentions"] = bool(
            re.search(r"\b(security|authentication|authorization|encryption)\b", text, re.IGNORECASE)
        )
        metadata["has_test_mentions"] = bool(
            re.search(r"\b(test|testing|unit test|e2e|integration test)\b", text, re.IGNORECASE)
        )
        metadata["has_error_handling"] = bool(
            re.search(r"\b(try|catch|error|exception|handle)\b", text, re.IGNORECASE)
        )

        return metadata

    def _is_valid_file_path(self, path: str) -> bool:
        """Validate if string looks like a file path

        Args:
            path: String to validate

        Returns:
            True if looks like valid file path
        """
        if not path or len(path) < 3:
            return False

        # Must have an extension
        if "." not in path:
            return False

        # Should not contain spaces (usually)
        if " " in path and not path.startswith("/"):
            return False

        # Check for known extensions
        ext = "." + path.split(".")[-1].lower()
        all_extensions = [ext for exts in self.LANGUAGE_EXTENSIONS.values() for ext in exts]

        return ext in all_extensions or ext in [".txt", ".log", ".config", ".env"]

    def _is_command_like(self, text: str) -> bool:
        """Check if text looks like a command

        Args:
            text: Text to check

        Returns:
            True if looks like a command
        """
        # Single line and starts with common command indicators
        if "\n" not in text and (
            text.startswith(("$", ">", "npm", "pip", "dotnet", "cargo", "go"))
        ):
            return True

        return False

    def get_language_from_path(self, file_path: str) -> Optional[str]:
        """Determine programming language from file path

        Args:
            file_path: File path

        Returns:
            Language name or None
        """
        ext = "." + file_path.split(".")[-1].lower()

        for language, extensions in self.LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                return language

        return None
