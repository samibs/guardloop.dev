"""Coder agent for implementation validation"""

from guardrail.agents.base import AgentContext, AgentDecision, BaseAgent
from guardrail.utils.config import Config


class CoderAgent(BaseAgent):
    """Ruthless Coder - Implementation and code quality validation"""

    def __init__(self, config: Config):
        """Initialize coder agent

        Args:
            config: Guardrail configuration
        """
        super().__init__("coder", "~/.guardrail/guardrails/agents/ruthless-coder.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        """Evaluate code implementation

        Args:
            context: Agent context

        Returns:
            Agent decision
        """
        suggestions = []
        approved = True
        total_checks = 0
        issues_count = 0

        if not context.parsed_response:
            return AgentDecision(
                agent_name=self.name,
                approved=False,
                reason="No code provided for evaluation",
                suggestions=["Provide code implementation"],
                confidence=0.5,
            )

        # Check 1: Incremental edits (no full rewrites)
        total_checks += 1
        if self._is_full_rewrite(context):
            approved = False
            issues_count += 1
            suggestions.append(
                "Use incremental edits (Edit tool), not full file rewrites (Write tool)"
            )

        # Check 2: Tests included
        total_checks += 1
        if not self._has_tests(context.parsed_response):
            approved = False
            issues_count += 1
            suggestions.append("Include unit tests with implementation")

        # Check 3: Error handling
        total_checks += 1
        if not self._has_error_handling(context):
            issues_count += 1
            suggestions.append("Add comprehensive error handling and logging")

        # Check 4: Type annotations (for Python/TypeScript)
        total_checks += 1
        if not self._has_type_annotations(context):
            issues_count += 1
            suggestions.append("Add type annotations for better code safety")

        # Check 5: Documentation/comments
        total_checks += 1
        if not self._has_documentation(context):
            issues_count += 1
            suggestions.append("Add docstrings/comments for functions and classes")

        # Determine next agent
        next_agent = "tester" if approved else None

        # Calculate confidence
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="Code implementation validated"
            if approved
            else "Code incomplete or missing critical elements",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _is_full_rewrite(self, context: AgentContext) -> bool:
        """Check if response is a full file rewrite

        Args:
            context: Agent context

        Returns:
            True if appears to be full rewrite
        """
        # Check for Write tool mentions in output
        if self._contains_keywords(
            context.raw_output, ["write tool", "writing file", "create file"]
        ):
            return True

        # Check for very large code blocks (>100 lines)
        if context.parsed_response and context.parsed_response.code_blocks:
            for block in context.parsed_response.code_blocks:
                lines = block.content.split("\n")
                if len(lines) > 100:
                    return True

        return False

    def _has_tests(self, parsed) -> bool:
        """Check if tests are included

        Args:
            parsed: Parsed response

        Returns:
            True if tests present
        """
        if not parsed or not parsed.code_blocks:
            return False

        test_indicators = [
            "test_",
            "it(",
            "describe(",
            "expect(",
            "assert",
            "should",
            "@test",
            "def test",
            "class Test",
        ]

        for block in parsed.code_blocks:
            if self._contains_keywords(block.content, test_indicators):
                return True

        return False

    def _has_error_handling(self, context: AgentContext) -> bool:
        """Check if error handling is present

        Args:
            context: Agent context

        Returns:
            True if error handling present
        """
        if not context.parsed_response or not context.parsed_response.code_blocks:
            return False

        error_patterns = [
            "try",
            "catch",
            "except",
            "raise",
            "throw",
            "error",
            "logging",
            "logger",
        ]

        for block in context.parsed_response.code_blocks:
            if self._contains_keywords(block.content, error_patterns):
                return True

        return False

    def _has_type_annotations(self, context: AgentContext) -> bool:
        """Check if type annotations are present

        Args:
            context: Agent context

        Returns:
            True if type annotations present
        """
        if not context.parsed_response or not context.parsed_response.code_blocks:
            return False

        for block in context.parsed_response.code_blocks:
            # Python type hints
            if block.language == "python":
                if self._contains_keywords(
                    block.content, ["->", ": str", ": int", ": List", ": Dict", ": Optional"]
                ):
                    return True

            # TypeScript types
            elif block.language in ["typescript", "tsx"]:
                if self._contains_keywords(
                    block.content, [": string", ": number", ": boolean", "interface", "type "]
                ):
                    return True

        # Not required for other languages or if not applicable
        return True

    def _has_documentation(self, context: AgentContext) -> bool:
        """Check if documentation is present

        Args:
            context: Agent context

        Returns:
            True if documentation present
        """
        if not context.parsed_response or not context.parsed_response.code_blocks:
            return False

        doc_patterns = [
            '"""',
            "'''",
            "/**",
            "//",
            "@param",
            "@returns",
            "@description",
            "Args:",
            "Returns:",
        ]

        for block in context.parsed_response.code_blocks:
            if self._contains_keywords(block.content, doc_patterns):
                return True

        return False
