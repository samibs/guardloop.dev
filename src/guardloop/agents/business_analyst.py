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
        approved = True
        total_checks = 3
        issues_count = 0

        # Check 1: User story format
        if not self._has_user_story_format(context.prompt):
            issues_count += 1
            suggestions.append(
                "Use user story format: As a [user], I want [goal], so that [benefit]"
            )

        # Check 2: Acceptance criteria
        if not self._has_acceptance_criteria(context):
            issues_count += 1
            suggestions.append("Define acceptance criteria and success metrics")

        # Check 3: Business value
        if not self._mentions_business_value(context.prompt):
            issues_count += 1
            suggestions.append("Clarify business value and user impact")

        next_agent = "architect" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="Requirements validated" if approved else "Requirements incomplete",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

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
            prompt, ["value", "benefit", "impact", "revenue", "user", "customer"]
        )
