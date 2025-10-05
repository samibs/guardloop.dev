"""Evaluator agent for final review"""

from guardloop.agents.base import AgentContext, AgentDecision, BaseAgent
from guardloop.utils.config import Config


class EvaluatorAgent(BaseAgent):
    """Evaluator - Final quality assessment"""

    def __init__(self, config: Config):
        super().__init__("evaluator", "~/.guardrail/guardrails/agents/evaluator.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        suggestions = []
        approved = True
        total_checks = 3
        issues_count = 0

        # Overall quality check
        if context.violations:
            critical_violations = [v for v in context.violations if v.severity == "critical"]
            if critical_violations:
                approved = False
                issues_count += len(critical_violations)
                suggestions.append(f"Fix {len(critical_violations)} critical violations")

        # Failure check
        if context.failures:
            critical_failures = [f for f in context.failures if f.severity == "critical"]
            if critical_failures:
                approved = False
                issues_count += len(critical_failures)
                suggestions.append(f"Fix {len(critical_failures)} critical failures")

        # Completeness check
        if not context.parsed_response or not context.parsed_response.code_blocks:
            approved = False
            issues_count += 1
            suggestions.append("No implementation provided")

        next_agent = None  # Evaluator is always last
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="Final evaluation complete" if approved else "Quality issues found",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )
