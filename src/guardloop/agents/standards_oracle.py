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
        issues_count = 0
        total_checks = 3

        if not self._follows_naming_conventions(context):
            issues_count += 1
            suggestions.append("Follow language-specific naming conventions (e.g., snake_case for Python, camelCase for JS/TS). Avoid generic names like 'data' or 'temp'.")

        if not self._has_consistent_style(context):
            issues_count += 1
            suggestions.append("Ensure consistent code style. Consider using a linter (e.g., Black, Prettier) and a formatter.")

        if not self._follows_solid_principles(context):
            issues_count += 1
            suggestions.append("Adhere to SOLID principles. Check for large classes or functions that may violate the Single Responsibility Principle.")

        approved = issues_count == 0
        next_agent = "evaluator" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        reason = "Code adheres to established coding standards and best practices."
        if not approved:
            reason = f"Found {issues_count} violations of coding standards."

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason=reason,
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _follows_naming_conventions(self, context: AgentContext) -> bool:
        if not context.parsed_response or not context.parsed_response.code_blocks:
            return True  # Not applicable

        for block in context.parsed_response.code_blocks:
            if block.language == "python":
                if self._contains_keywords(block.content, ["myVar", "tempVar"]): # Simple check for camelCase
                    return False
            elif block.language in ["javascript", "typescript"]:
                if self._contains_keywords(block.content, ["my_var", "temp_var"]): # Simple check for snake_case
                    return False
            if self._contains_keywords(block.content, ["foo", "bar", "temp", "data"]):
                return False
        return True

    def _has_consistent_style(self, context: AgentContext) -> bool:
        # A simple check for mixed indentation (spaces vs. tabs)
        if not context.parsed_response or not context.parsed_response.code_blocks:
            return True

        for block in context.parsed_response.code_blocks:
            lines = block.content.split('\n')
            has_spaces = any(line.startswith(' ') for line in lines)
            has_tabs = any(line.startswith('\t') for line in lines)
            if has_spaces and has_tabs:
                return False
        return True

    def _follows_solid_principles(self, context: AgentContext) -> bool:
        # A simple check for very long functions/methods (violates SRP)
        if not context.parsed_response or not context.parsed_response.code_blocks:
            return True

        for block in context.parsed_response.code_blocks:
            if len(block.content.split('\n')) > 50: # Arbitrary threshold for long block
                return False
        return True
