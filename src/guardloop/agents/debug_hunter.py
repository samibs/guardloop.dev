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
        issues_count = 0
        total_checks = 3

        # Check for root cause analysis
        if not self._has_root_cause_analysis(context):
            issues_count += 1
            suggestions.append("Provide a clear root cause analysis for the bug. Explain why it occurred.")

        # Check for regression tests
        if not self._has_regression_tests(context):
            issues_count += 1
            suggestions.append("Include a regression test to confirm the fix and prevent recurrence.")

        # Check for logging added
        if not self._has_debug_logging(context):
            issues_count += 1
            suggestions.append("Add relevant logging statements to help with future debugging of this code path.")

        approved = issues_count == 0
        next_agent = "tester" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        reason = "Bug fix is well-documented and includes a regression test."
        if not approved:
            reason = f"Found {issues_count} issues with the proposed bug fix."

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason=reason,
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_root_cause_analysis(self, context: AgentContext) -> bool:
        return self._contains_keywords(
            context.raw_output, ["root cause", "because", "caused by", "reason", "why", "the issue was"]
        )

    def _has_regression_tests(self, context: AgentContext) -> bool:
        if context.parsed_response and context.parsed_response.code_blocks:
            return self._contains_keywords(
                " ".join([b.content for b in context.parsed_response.code_blocks]),
                ["test_", "it(", "describe(", "regression", "reproduce", "assert", "expect"],
            )
        return False

    def _has_debug_logging(self, context: AgentContext) -> bool:
        if context.parsed_response and context.parsed_response.code_blocks:
            return self._contains_keywords(
                " ".join([b.content for b in context.parsed_response.code_blocks]),
                ["logger", "logging", "log.", "console.log", "print("],
            )
        return False
