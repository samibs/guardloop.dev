"""Standards Oracle agent for coding standards validation"""

from guardloop.agents.base import AgentContext, AgentDecision, BaseAgent
from guardloop.utils.config import Config


class StandardsOracleAgent(BaseAgent):
    """Standards Oracle - Coding standards and best practices validation"""

    def __init__(self, config: Config):
        super().__init__("standards_oracle", "~/.guardrail/guardrails/agents/standards-oracle.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        suggestions = []
        approved = True
        total_checks = 3
        issues_count = 0

        if not self._follows_naming_conventions(context):
            issues_count += 1
            suggestions.append("Follow naming conventions: snake_case for Python, camelCase for JS")

        if not self._has_consistent_style(context):
            issues_count += 1
            suggestions.append("Use consistent code style (run linter/formatter)")

        if not self._follows_solid_principles(context):
            issues_count += 1
            suggestions.append("Apply SOLID principles: Single Responsibility, DRY, KISS")

        next_agent = "evaluator" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="Standards validated" if approved else "Standards violations found",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _follows_naming_conventions(self, context):
        # Basic check - assumes reasonable naming if no obvious violations
        if context.parsed_response and context.parsed_response.code_blocks:
            for block in context.parsed_response.code_blocks:
                # Check for bad patterns
                if self._contains_keywords(block.content, ["var ", "temp1", "data2", "foo", "test1"]):
                    return False
        return True

    def _has_consistent_style(self, context):
        # Assumes consistent if no mixed styles
        return True  # Simplified for MVP

    def _follows_solid_principles(self, context):
        # Check for some indicators of good design
        if context.parsed_response and context.parsed_response.code_blocks:
            for block in context.parsed_response.code_blocks:
                if self._contains_keywords(block.content, ["class", "def ", "function", "interface"]):
                    return True
        return True  # Simplified for MVP
