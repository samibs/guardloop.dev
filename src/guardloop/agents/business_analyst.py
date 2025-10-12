"""Business Analyst agent for requirements validation"""

from guardloop.agents.base import AgentContext, AgentDecision, BaseAgent
from guardloop.utils.config import Config


class BusinessAnalystAgent(BaseAgent):
    """Business Analyst - Requirements and feature validation"""

    def __init__(self, config: Config):
        """Initialize business analyst agent

        Args:
            config: Guardrail configuration
        """
        super().__init__(
            "business_analyst",
            "~/.guardrail/guardrails/agents/business-analyst.md",
        )
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        """Evaluate business requirements

        Args:
            context: Agent context

        Returns:
            Agent decision
        """
        suggestions = []
        issues_count = 0
        total_checks = 4  # Now includes a generic check

        # Check 1: Is the prompt too generic?
        if self._is_too_generic(context.prompt):
            issues_count += 1
            suggestions.append("Prompt is too generic. Please provide a more specific request.")

        # Check 2: User story format
        if not self._has_user_story_format(context.prompt):
            issues_count += 1
            suggestions.append(
                "Use user story format: 'As a [user], I want [goal], so that [benefit]'"
            )

        # Check 3: Acceptance criteria
        if not self._has_acceptance_criteria(context):
            issues_count += 1
            suggestions.append("Define clear acceptance criteria (e.g., using 'Given/When/Then') and success metrics.")

        # Check 4: Business value
        if not self._mentions_business_value(context.prompt):
            issues_count += 1
            suggestions.append("Clarify the business value and end-user impact of this feature.")

        approved = issues_count == 0
        next_agent = "architect" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        reason = "Business requirements are clear and well-defined."
        if not approved:
            reason = f"Found {issues_count} issues with the business requirements."

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason=reason,
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _is_too_generic(self, prompt: str) -> bool:
        """Check if the prompt is too generic."""
        generic_phrases = ["build a website", "create an app", "make a program", "make a "]
        return any(phrase in prompt.lower() for phrase in generic_phrases)

    def _has_user_story_format(self, prompt: str) -> bool:
        """Check for user story format"""
        return self._contains_keywords(prompt, ["as a", "i want", "so that", "user story"])

    def _has_acceptance_criteria(self, context: AgentContext) -> bool:
        """Check for acceptance criteria"""
        return self._contains_keywords(
            context.prompt + context.raw_output,
            ["acceptance", "criteria", "given", "when", "then", "success"],
        )

    def _mentions_business_value(self, prompt: str) -> bool:
        """Check for business value mention"""
        return self._contains_keywords(
            prompt, ["value", "benefit", "impact", "revenue", "customer", "user engagement"]
        )
