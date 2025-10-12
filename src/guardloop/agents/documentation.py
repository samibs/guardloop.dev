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
        issues_count = 0
        total_checks = 3

        if not self._has_readme(context):
            issues_count += 1
            suggestions.append("Provide or update a README.md with a project overview and setup instructions.")

        if not self._has_api_docs(context):
            issues_count += 1
            suggestions.append("Add detailed API documentation (e.g., docstrings) for all public functions and classes, including parameters and return values.")

        if not self._has_examples(context):
            issues_count += 1
            suggestions.append("Include clear and practical code examples or usage snippets.")

        approved = issues_count == 0
        next_agent = "evaluator" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        reason = "Documentation is comprehensive and up-to-date."
        if not approved:
            reason = f"Found {issues_count} documentation issues that need addressing."

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason=reason,
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_readme(self, context: AgentContext) -> bool:
        return self._contains_keywords(
            context.raw_output, ["readme", "# ", "## ", "getting started", "installation", "configuration"]
        )

    def _has_api_docs(self, context: AgentContext) -> bool:
        text_to_check = context.raw_output
        if context.parsed_response:
            for block in context.parsed_response.code_blocks:
                text_to_check += block.content
        return self._contains_keywords(
            text_to_check, ["@param", "@returns", "Args:", "Returns:", "/**", '"""', "Parameters", "Return"]
        )

    def _has_examples(self, context: AgentContext) -> bool:
        text_to_check = context.raw_output
        if context.parsed_response:
            for block in context.parsed_response.code_blocks:
                text_to_check += block.content
        return self._contains_keywords(text_to_check, ["example", "usage", "sample", "```"])
