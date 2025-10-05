"""Debug Hunter agent for bug detection and fixes"""

from guardloop.agents.base import AgentContext, AgentDecision, BaseAgent
from guardloop.utils.config import Config


class DebugHunterAgent(BaseAgent):
    """Debug Hunter - Bug detection and fix validation"""

    def __init__(self, config: Config):
        super().__init__("debug_hunter", "~/.guardrail/guardrails/agents/debug-hunter.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        suggestions = []
        approved = True
        total_checks = 3
        issues_count = 0

        # Check for root cause analysis
        if not self._has_root_cause_analysis(context):
            issues_count += 1
            suggestions.append("Document root cause analysis before applying fix")

        # Check for regression tests
        if not self._has_regression_tests(context):
            approved = False
            issues_count += 1
            suggestions.append("Add regression tests to prevent bug from recurring")

        # Check for logging added
        if not self._has_debug_logging(context):
            issues_count += 1
            suggestions.append("Add logging for future debugging")

        next_agent = "tester" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="Bug fix validated" if approved else "Bug fix incomplete",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_root_cause_analysis(self, context):
        return self._contains_keywords(
            context.raw_output, ["root cause", "because", "caused by", "reason", "why"]
        )

    def _has_regression_tests(self, context):
        if context.parsed_response:
            return self._contains_keywords(
                " ".join([b.code for b in context.parsed_response.code_blocks]),
                ["test_", "it(", "regression", "reproduce"]
            )
        return False

    def _has_debug_logging(self, context):
        if context.parsed_response:
            return self._contains_keywords(
                " ".join([b.code for b in context.parsed_response.code_blocks]),
                ["logger", "logging", "log.", "console.log", "print("]
            )
        return False
