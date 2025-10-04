"""UX Designer agent for user experience validation"""

from guardrail.agents.base import AgentContext, AgentDecision, BaseAgent
from guardrail.utils.config import Config


class UXDesignerAgent(BaseAgent):
    """UX Designer - User experience and interface validation"""

    def __init__(self, config: Config):
        super().__init__("ux_designer", "~/.guardrail/guardrails/agents/ux-designer.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        suggestions = []
        approved = True
        total_checks = 4
        issues_count = 0

        # Check accessibility
        if not self._has_accessibility(context):
            issues_count += 1
            suggestions.append("Add WCAG 2.1 accessibility features: ARIA labels, keyboard navigation")

        # Check responsive design
        if not self._has_responsive_design(context):
            issues_count += 1
            suggestions.append("Implement responsive design for mobile/tablet/desktop")

        # Check error states
        if not self._has_error_states(context):
            issues_count += 1
            suggestions.append("Define error states and user feedback mechanisms")

        # Check loading states
        if not self._has_loading_states(context):
            issues_count += 1
            suggestions.append("Add loading states and progress indicators")

        next_agent = "coder" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="UX validated" if approved else "UX incomplete",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_accessibility(self, context):
        return self._contains_keywords(
            context.raw_output, ["aria", "accessible", "wcag", "alt=", "role=", "tabindex"]
        )

    def _has_responsive_design(self, context):
        return self._contains_keywords(
            context.raw_output, ["responsive", "mobile", "breakpoint", "@media", "flex", "grid"]
        )

    def _has_error_states(self, context):
        return self._contains_keywords(
            context.raw_output, ["error", "validation", "invalid", "warning"]
        )

    def _has_loading_states(self, context):
        return self._contains_keywords(
            context.raw_output, ["loading", "spinner", "skeleton", "progress"]
        )
