"""SRE agent for reliability validation"""

from guardrail.agents.base import AgentContext, AgentDecision, BaseAgent
from guardrail.utils.config import Config


class SREAgent(BaseAgent):
    """SRE - Site Reliability Engineering validation"""

    def __init__(self, config: Config):
        super().__init__("sre", "~/.guardrail/guardrails/agents/sre.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        suggestions = []
        approved = True
        total_checks = 3
        issues_count = 0

        if not self._has_monitoring(context):
            issues_count += 1
            suggestions.append("Add monitoring and alerting")

        if not self._has_error_recovery(context):
            issues_count += 1
            suggestions.append("Implement error recovery and circuit breakers")

        if not self._has_deployment_config(context):
            issues_count += 1
            suggestions.append("Include deployment configuration and health checks")

        next_agent = "evaluator" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="SRE validated" if approved else "SRE incomplete",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_monitoring(self, context):
        return self._contains_keywords(
            context.raw_output, ["metric", "monitor", "prometheus", "alert", "log"]
        )

    def _has_error_recovery(self, context):
        return self._contains_keywords(
            context.raw_output, ["retry", "circuit breaker", "fallback", "timeout"]
        )

    def _has_deployment_config(self, context):
        return self._contains_keywords(
            context.raw_output, ["docker", "kubernetes", "deploy", "health", "readiness"]
        )
