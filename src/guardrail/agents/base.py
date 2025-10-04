"""Base agent classes and data structures"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from guardrail.core.failure_detector import DetectedFailure
from guardrail.core.parser import ParsedResponse
from guardrail.core.validator import Violation


@dataclass
class AgentContext:
    """Context for agent evaluation"""

    prompt: str
    mode: str
    parsed_response: Optional[ParsedResponse] = None
    violations: List[Violation] = field(default_factory=list)
    failures: List[DetectedFailure] = field(default_factory=list)
    raw_output: str = ""
    tool: str = "unknown"


@dataclass
class AgentDecision:
    """Agent decision result"""

    agent_name: str
    approved: bool
    reason: str
    suggestions: List[str] = field(default_factory=list)
    next_agent: Optional[str] = None
    confidence: float = 1.0  # 0.0 to 1.0


class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(self, name: str, instructions_path: str):
        """Initialize agent

        Args:
            name: Agent name
            instructions_path: Path to agent instructions markdown file
        """
        self.name = name
        self.instructions_path = Path(instructions_path).expanduser()
        self.instructions = self._load_instructions()

    def _load_instructions(self) -> str:
        """Load agent-specific markdown instructions

        Returns:
            Instructions text or empty string if file not found
        """
        if self.instructions_path.exists():
            return self.instructions_path.read_text()
        return f"# {self.name.replace('_', ' ').title()} Agent\n\nNo instructions file found."

    @abstractmethod
    async def evaluate(self, context: AgentContext) -> AgentDecision:
        """Evaluate context and make decision

        Args:
            context: Agent evaluation context

        Returns:
            Agent decision with approval status and suggestions
        """
        pass

    def get_instructions(self) -> str:
        """Get agent instructions

        Returns:
            Agent instructions text
        """
        return self.instructions

    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords

        Args:
            text: Text to search
            keywords: List of keywords to search for

        Returns:
            True if any keyword found
        """
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _count_code_blocks(self, parsed: Optional[ParsedResponse]) -> int:
        """Count code blocks in parsed response

        Args:
            parsed: Parsed response

        Returns:
            Number of code blocks
        """
        if not parsed:
            return 0
        return len(parsed.code_blocks)

    def _has_language(self, parsed: Optional[ParsedResponse], language: str) -> bool:
        """Check if parsed response has code in specific language

        Args:
            parsed: Parsed response
            language: Language to check for

        Returns:
            True if language found
        """
        if not parsed or not parsed.code_blocks:
            return False
        return any(
            block.language.lower() == language.lower() for block in parsed.code_blocks
        )

    def _calculate_confidence(
        self, approved: bool, issues_count: int, total_checks: int
    ) -> float:
        """Calculate decision confidence

        Args:
            approved: Whether approved
            issues_count: Number of issues found
            total_checks: Total number of checks performed

        Returns:
            Confidence score 0.0-1.0
        """
        if total_checks == 0:
            return 1.0

        if approved:
            # High confidence if approved with no issues
            return 1.0 - (issues_count / total_checks) * 0.3
        else:
            # Lower confidence if blocked
            return 0.5 + (issues_count / total_checks) * 0.3
