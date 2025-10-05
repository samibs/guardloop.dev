"""Documentation agent for documentation validation"""

from guardloop.agents.base import AgentContext, AgentDecision, BaseAgent
from guardloop.utils.config import Config


class DocumentationAgent(BaseAgent):
    """Documentation - Documentation completeness validation"""

    def __init__(self, config: Config):
        super().__init__("documentation", "~/.guardrail/guardrails/agents/documentation.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        suggestions = []
        approved = True
        total_checks = 3
        issues_count = 0

        if not self._has_readme(context):
            issues_count += 1
            suggestions.append("Include README with usage instructions")

        if not self._has_api_docs(context):
            issues_count += 1
            suggestions.append("Document APIs/functions with parameters and return values")

        if not self._has_examples(context):
            issues_count += 1
            suggestions.append("Provide usage examples and code samples")

        next_agent = "evaluator" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="Documentation validated" if approved else "Documentation incomplete",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_readme(self, context):
        return self._contains_keywords(context.raw_output, ["readme", "# ", "## ", "getting started"])

    def _has_api_docs(self, context):
        return self._contains_keywords(context.raw_output, ["@param", "@returns", "Args:", "Returns:", "/**"])

    def _has_examples(self, context):
        return self._contains_keywords(context.raw_output, ["example", "usage", "sample", "```"])
