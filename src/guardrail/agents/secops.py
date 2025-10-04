"""SecOps agent for security validation"""

from guardrail.agents.base import AgentContext, AgentDecision, BaseAgent
from guardrail.utils.config import Config


class SecOpsAgent(BaseAgent):
    """SecOps - Security operations and vulnerability validation"""

    def __init__(self, config: Config):
        super().__init__("secops", "~/.guardrail/guardrails/agents/secops.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        suggestions = []
        approved = True
        total_checks = 4
        issues_count = 0

        if not self._has_input_validation(context):
            approved = False
            issues_count += 1
            suggestions.append("Add input validation and sanitization")

        if not self._has_authentication(context):
            issues_count += 1
            suggestions.append("Implement authentication/authorization checks")

        if not self._prevents_injection(context):
            approved = False
            issues_count += 1
            suggestions.append("Prevent SQL injection and XSS attacks")

        if not self._has_secure_config(context):
            issues_count += 1
            suggestions.append("Use environment variables for secrets, not hardcoded")

        next_agent = "sre" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="Security validated" if approved else "Security issues found",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_input_validation(self, context):
        return self._contains_keywords(
            context.raw_output, ["validate", "sanitize", "escape", "clean"]
        )

    def _has_authentication(self, context):
        return self._contains_keywords(
            context.raw_output, ["auth", "jwt", "token", "session", "permission"]
        )

    def _prevents_injection(self, context):
        return self._contains_keywords(
            context.raw_output, ["prepared statement", "parameterized", "escape", "sanitize"]
        )

    def _has_secure_config(self, context):
        return self._contains_keywords(
            context.raw_output, ["env.", "process.env", "os.getenv", "config"]
        ) and not self._contains_keywords(
            context.raw_output, ["password =", "api_key =", "secret ="]
        )
