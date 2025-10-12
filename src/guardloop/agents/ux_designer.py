"""UX Designer agent for user experience validation"""

from guardloop.agents.base import AgentContext, AgentDecision, BaseAgent
from guardloop.utils.config import Config


class UXDesignerAgent(BaseAgent):
    """UX Designer - User experience and interface validation"""

    def __init__(self, config: Config):
        super().__init__("ux_designer", "~/.guardrail/guardrails/agents/ux-designer.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        suggestions = []
        issues_count = 0
        total_checks = 4

        # Check accessibility
        if not self._has_accessibility(context):
            issues_count += 1
            suggestions.append("Ensure accessibility (WCAG 2.1) by adding ARIA labels, alt text for images, and keyboard navigation support.")

        # Check responsive design
        if not self._has_responsive_design(context):
            issues_count += 1
            suggestions.append("Implement a responsive design that works on mobile, tablet, and desktop screens using CSS media queries, flexbox, or grid.")

        # Check error states
        if not self._has_error_states(context):
            issues_count += 1
            suggestions.append("Clearly define and design error states and provide helpful user feedback mechanisms.")

        # Check loading states
        if not self._has_loading_states(context):
            issues_count += 1
            suggestions.append("Implement loading states (e.g., spinners, skeleton screens) to provide feedback during long operations.")

        approved = issues_count == 0
        next_agent = "coder" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        reason = "User experience principles are well-considered."
        if not approved:
            reason = f"Found {issues_count} UX issues that need to be addressed."

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason=reason,
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_accessibility(self, context: AgentContext) -> bool:
        text_to_check = context.raw_output
        if context.parsed_response:
            for block in context.parsed_response.code_blocks:
                text_to_check += block.content
        return self._contains_keywords(
            text_to_check, ["aria", "accessible", "wcag", "alt=", "role=", "tabindex", "for="]
        )

    def _has_responsive_design(self, context: AgentContext) -> bool:
        text_to_check = context.raw_output
        if context.parsed_response:
            for block in context.parsed_response.code_blocks:
                text_to_check += block.content
        return self._contains_keywords(
            text_to_check, ["responsive", "mobile", "breakpoint", "@media", "flex", "grid", "viewport"]
        )

    def _has_error_states(self, context: AgentContext) -> bool:
        text_to_check = context.raw_output
        if context.parsed_response:
            for block in context.parsed_response.code_blocks:
                text_to_check += block.content
        return self._contains_keywords(
            text_to_check, ["error", "validation", "invalid", "warning", "danger", "alert"]
        )

    def _has_loading_states(self, context: AgentContext) -> bool:
        text_to_check = context.raw_output
        if context.parsed_response:
            for block in context.parsed_response.code_blocks:
                text_to_check += block.content
        return self._contains_keywords(
            text_to_check, ["loading", "spinner", "skeleton", "progress", "busy"]
        )
