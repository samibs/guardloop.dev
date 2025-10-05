"""Tester agent for test coverage and quality validation"""

from guardloop.agents.base import AgentContext, AgentDecision, BaseAgent
from guardloop.utils.config import Config


class TesterAgent(BaseAgent):
    """Ruthless Tester - Test coverage and quality validation"""

    def __init__(self, config: Config):
        """Initialize tester agent

        Args:
            config: Guardrail configuration
        """
        super().__init__("tester", "~/.guardrail/guardrails/agents/ruthless-tester.md")
        self.config = config

    async def evaluate(self, context: AgentContext) -> AgentDecision:
        """Evaluate test coverage and quality

        Args:
            context: Agent context

        Returns:
            Agent decision
        """
        suggestions = []
        approved = True
        total_checks = 0
        issues_count = 0

        if not context.parsed_response:
            return AgentDecision(
                agent_name=self.name,
                approved=False,
                reason="No tests provided for evaluation",
                suggestions=["Provide test implementation"],
                confidence=0.5,
            )

        # Check 1: Test coverage (must be 100%)
        total_checks += 1
        coverage = context.parsed_response.test_coverage or 0
        if coverage < 100:
            approved = False
            issues_count += 1
            suggestions.append(f"Test coverage is {coverage}%. Must be 100% for all critical paths")

        # Check 2: E2E tests
        total_checks += 1
        if not self._has_e2e_tests(context.parsed_response):
            approved = False
            issues_count += 1
            suggestions.append("Missing E2E tests for user flows and integration paths")

        # Check 3: Security/malicious input tests
        total_checks += 1
        if not self._has_security_tests(context.parsed_response):
            approved = False
            issues_count += 1
            suggestions.append("Add security tests: SQL injection, XSS, malicious inputs")

        # Check 4: Edge cases
        total_checks += 1
        if not self._has_edge_case_tests(context.parsed_response):
            issues_count += 1
            suggestions.append("Test edge cases: null, empty, boundary values, errors")

        # Check 5: Performance tests
        total_checks += 1
        if not self._has_performance_tests(context.parsed_response):
            issues_count += 1
            suggestions.append("Consider performance tests for critical operations")

        # Determine next agent
        next_agent = "secops" if approved else None

        # Calculate confidence
        confidence = self._calculate_confidence(approved, issues_count, total_checks)

        return AgentDecision(
            agent_name=self.name,
            approved=approved,
            reason="Tests validated" if approved else "Insufficient test coverage or quality",
            suggestions=suggestions,
            next_agent=next_agent,
            confidence=confidence,
        )

    def _has_e2e_tests(self, parsed) -> bool:
        """Check for E2E tests

        Args:
            parsed: Parsed response

        Returns:
            True if E2E tests present
        """
        if not parsed or not parsed.code_blocks:
            return False

        e2e_indicators = [
            "e2e",
            "integration",
            "playwright",
            "cypress",
            "selenium",
            "webdriver",
            "supertest",
            "request(",
            "browser.",
            "page.",
        ]

        for block in parsed.code_blocks:
            if self._contains_keywords(block.content, e2e_indicators):
                return True

        return False

    def _has_security_tests(self, parsed) -> bool:
        """Check for security tests

        Args:
            parsed: Parsed response

        Returns:
            True if security tests present
        """
        if not parsed or not parsed.code_blocks:
            return False

        security_test_indicators = [
            "sql injection",
            "xss",
            "csrf",
            "malicious",
            "sanitize",
            "escape",
            "invalid token",
            "unauthorized",
            "forbidden",
            "<script>",
            "'; drop",
        ]

        for block in parsed.code_blocks:
            if self._contains_keywords(block.content, security_test_indicators):
                return True

        return False

    def _has_edge_case_tests(self, parsed) -> bool:
        """Check for edge case tests

        Args:
            parsed: Parsed response

        Returns:
            True if edge case tests present
        """
        if not parsed or not parsed.code_blocks:
            return False

        edge_case_indicators = [
            "null",
            "undefined",
            "none",
            "empty",
            "boundary",
            "max",
            "min",
            "overflow",
            "negative",
            "zero",
            "edge case",
        ]

        for block in parsed.code_blocks:
            code_lower = block.content.lower()
            if any(indicator in code_lower for indicator in edge_case_indicators):
                return True

        return False

    def _has_performance_tests(self, parsed) -> bool:
        """Check for performance tests

        Args:
            parsed: Parsed response

        Returns:
            True if performance tests present
        """
        if not parsed or not parsed.code_blocks:
            return False

        performance_indicators = [
            "performance",
            "benchmark",
            "load test",
            "stress test",
            "response time",
            "latency",
            "throughput",
            "time.time()",
            "Date.now()",
            "@benchmark",
        ]

        for block in parsed.code_blocks:
            if self._contains_keywords(block.content, performance_indicators):
                return True

        return False
