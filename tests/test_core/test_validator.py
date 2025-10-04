"""Unit tests for GuardrailValidator"""

import pytest
from guardrail.core.validator import GuardrailValidator, Violation, Severity, GuardrailType
from guardrail.core.parser import ParsedResponse, CodeBlock


class TestGuardrailValidator:
    """Test GuardrailValidator functionality"""

    @pytest.fixture
    def validator_standard(self):
        """Create standard mode validator"""
        return GuardrailValidator(mode="standard")

    @pytest.fixture
    def validator_strict(self):
        """Create strict mode validator"""
        return GuardrailValidator(mode="strict")

    @pytest.fixture
    def sample_response(self):
        """Create sample parsed response"""
        return ParsedResponse(
            code_blocks=[CodeBlock("python", "def test(): pass")],
            test_coverage=95.0,
        )

    @pytest.mark.asyncio
    async def test_bpsbs_three_layer_check(self, validator_standard):
        """Test 3-layer architecture check"""
        text_missing = "Just a simple function"
        text_complete = "Database layer, backend API, and frontend UI"

        parsed = ParsedResponse()

        violations_missing = await validator_standard._check_bpsbs(parsed, text_missing)
        violations_complete = await validator_standard._check_bpsbs(parsed, text_complete)

        # Should have violation for missing layers
        assert any("three_layer" in v.rule for v in violations_missing)

        # Should have fewer violations with all layers
        three_layer_missing = sum(1 for v in violations_missing if "three_layer" in v.rule)
        three_layer_complete = sum(1 for v in violations_complete if "three_layer" in v.rule)
        assert three_layer_complete < three_layer_missing or three_layer_complete == 0

    @pytest.mark.asyncio
    async def test_security_checks(self, validator_standard):
        """Test security-related checks"""
        text_insecure = "Simple login without authentication"
        text_secure = "MFA enabled with Azure AD and RBAC authorization plus audit logging"

        parsed = ParsedResponse()

        violations_insecure = await validator_standard._check_bpsbs(parsed, text_insecure)
        violations_secure = await validator_standard._check_bpsbs(parsed, text_secure)

        # Insecure should have more violations
        assert len(violations_insecure) > len(violations_secure)

        # Should detect missing MFA/Azure AD
        assert any("mfa_azure_ad" in v.rule for v in violations_insecure)

    @pytest.mark.asyncio
    async def test_test_coverage_check(self, validator_standard):
        """Test coverage validation"""
        text_low = "Test coverage: 75%"
        text_high = "Test coverage: 100%"

        parsed = ParsedResponse()

        violations_low = await validator_standard._check_bpsbs(parsed, text_low)
        violations_high = await validator_standard._check_bpsbs(parsed, text_high)

        # Should flag low coverage
        coverage_violations_low = [v for v in violations_low if "test_coverage" in v.rule]
        coverage_violations_high = [v for v in violations_high if "test_coverage" in v.rule]

        assert len(coverage_violations_low) > 0
        assert len(coverage_violations_high) == 0

    @pytest.mark.asyncio
    async def test_ai_guardrails_checks(self, validator_standard):
        """Test AI guardrails"""
        text_incomplete = "Here's the code"
        text_complete = "Unit tests and E2E tests included with proper error handling using try/catch blocks"

        parsed = ParsedResponse()

        violations_incomplete = await validator_standard._check_ai_guardrails(parsed, text_incomplete)
        violations_complete = await validator_standard._check_ai_guardrails(parsed, text_complete)

        assert len(violations_incomplete) > len(violations_complete)

    @pytest.mark.asyncio
    async def test_ux_ui_checks(self, validator_standard):
        """Test UX/UI guardrails"""
        text_poor = "Button says OK with no tooltip"
        text_good = "Descriptive button label with tooltip and dark mode support"

        parsed = ParsedResponse()

        violations_poor = await validator_standard._check_ux_ui(parsed, text_poor)
        violations_good = await validator_standard._check_ux_ui(parsed, text_good)

        # Poor UX should have vague label violation
        assert any("vague_labels" in v.rule for v in violations_poor)

    @pytest.mark.asyncio
    async def test_strict_mode_blocking(self, validator_strict, sample_response):
        """Test strict mode violation blocking"""
        text = "Code without proper guardrails"

        violations = await validator_strict.validate(sample_response, text)

        # Strict mode should block if any violations
        should_block = validator_strict.should_block(violations)
        if len(violations) > 0:
            assert should_block is True

    def test_standard_mode_no_blocking(self, validator_standard):
        """Test standard mode doesn't block"""
        violations = [
            Violation(
                guardrail_type="bpsbs",
                rule="test",
                severity="high",
                description="Test",
                suggestion="Fix",
            )
        ]

        assert validator_standard.should_block(violations) is False

    def test_get_critical_violations(self, validator_standard):
        """Test critical violation filtering"""
        violations = [
            Violation("bpsbs", "test1", "critical", "Critical issue", "Fix ASAP"),
            Violation("bpsbs", "test2", "high", "High issue", "Fix soon"),
            Violation("bpsbs", "test3", "critical", "Another critical", "Fix ASAP"),
        ]

        critical = validator_standard.get_critical_violations(violations)

        assert len(critical) == 2
        assert all(v.severity == "critical" for v in critical)

    def test_format_violations_report(self, validator_standard):
        """Test violation report formatting"""
        violations = [
            Violation("bpsbs", "security", "critical", "Security issue", "Add MFA"),
            Violation("ux_ui", "labels", "low", "Vague label", "Be specific"),
        ]

        report = validator_standard.format_violations_report(violations)

        assert "2 guardrail violation(s)" in report
        assert "CRITICAL" in report
        assert "LOW" in report
        assert "Security issue" in report
        assert "Vague label" in report

    def test_empty_violations_report(self, validator_standard):
        """Test report with no violations"""
        report = validator_standard.format_violations_report([])

        assert "No violations" in report
        assert "✓" in report


class TestViolation:
    """Test Violation dataclass"""

    def test_violation_creation(self):
        """Test creating violations"""
        v = Violation(
            guardrail_type=GuardrailType.BPSBS.value,
            rule="test_rule",
            severity=Severity.HIGH.value,
            description="Test violation",
            suggestion="Fix it",
            file_path="test.py",
            line_number=42,
        )

        assert v.guardrail_type == "bpsbs"
        assert v.rule == "test_rule"
        assert v.severity == "high"
        assert v.description == "Test violation"
        assert v.suggestion == "Fix it"
        assert v.file_path == "test.py"
        assert v.line_number == 42


class TestSeverityEnum:
    """Test Severity enum"""

    def test_severity_values(self):
        """Test severity enum values"""
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
        assert Severity.CRITICAL.value == "critical"
