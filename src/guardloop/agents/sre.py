"""SRE agent for reliability validation"""

from guardloop.agents.base import AgentContext, AgentDecision, BaseAgent
from guardloop.utils.config import Config


class SREAgent(BaseAgent):
    """SRE - Site Reliability Engineering validation"""

    def __init__(self, config: Config):
        super().__init__("sre", "~/.guardrail/guardrails/agents/sre.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        suggestions = []
        issues_count = 0
        total_checks = 3

        if not self._has_monitoring(context):
            issues_count += 1
            suggestions.append("Add monitoring, logging, and alerting to ensure system visibility.")

        if not self._has_error_recovery(context):
            issues_count += 1
            suggestions.append("Implement robust error recovery mechanisms like retries, circuit breakers, or fallbacks.")

        if not self._has_deployment_config(context):
            issues_count += 1
            suggestions.append("Include deployment configurations (e.g., Dockerfile, Kubernetes YAML) and health checks.")

        approved = issues_count == 0
        next_agent = "evaluator" if approved else None
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        reason = "SRE principles (monitoring, recovery, deployment) are well-defined."
        if not approved:
            reason = f"Found {issues_count} SRE issues that need addressing."

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason=reason,
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_monitoring(self, context: AgentContext) -> bool:
        text_to_check = context.raw_output
        if context.parsed_response:
            for block in context.parsed_response.code_blocks:
                text_to_check += block.content
        return self._contains_keywords(
            text_to_check, ["metric", "monitor", "prometheus", "alert", "log", "grafana", "datadog"]
        )

    def _has_error_recovery(self, context: AgentContext) -> bool:
        text_to_check = context.raw_output
        if context.parsed_response:
            for block in context.parsed_response.code_blocks:
                text_to_check += block.content
        return self._contains_keywords(
            text_to_check, ["retry", "circuit breaker", "fallback", "timeout", "resilience", "recovery"]
        )

    def _has_deployment_config(self, context: AgentContext) -> bool:
        text_to_check = context.raw_output
        if context.parsed_response:
            for block in context.parsed_response.code_blocks:
                text_to_check += block.content
        return self._contains_keywords(
            text_to_check, ["docker", "kubernetes", "deploy", "health", "readiness", "liveness"]
        )
