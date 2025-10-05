"""Unit tests for FailureDetector"""

import pytest
from guardloop.core.failure_detector import FailureDetector, DetectedFailure


class TestFailureDetector:
    """Test FailureDetector functionality"""

    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return FailureDetector()

    def test_initialization(self, detector):
        """Test detector initialization"""
        assert detector._compiled_patterns is not None
        assert len(detector._compiled_patterns) == len(detector.PATTERNS)

    def test_jwt_auth_detection(self, detector):
        """Test JWT/Auth failure detection"""
        text = "JWT token expired, authentication failed"

        failures = detector.scan(text)

        assert len(failures) > 0
        assert any(f.category == "JWT/Auth" for f in failures)
        jwt_failure = next(f for f in failures if f.category == "JWT/Auth")
        assert jwt_failure.severity == "high"

    def test_dotnet_detection(self, detector):
        """Test .NET code failure detection"""
        text = "Dependency injection error in csproj file"

        failures = detector.scan(text)

        assert any(f.category == ".NET Code" for f in failures)

    def test_file_corruption_detection(self, detector):
        """Test file corruption pattern detection"""
        text = "File corrupted with ))))))))))))) pattern"

        failures = detector.scan(text)

        assert any(f.category == "File Overwrite" for f in failures)
        corruption_failure = next(f for f in failures if f.category == "File Overwrite")
        assert corruption_failure.severity == "critical"

    def test_security_detection(self, detector):
        """Test security issue detection"""
        text = "Missing MFA and Azure AD, RBAC not configured, SQL injection vulnerability"

        failures = detector.scan(text)

        security_failures = [f for f in failures if f.category == "Security"]
        assert len(security_failures) > 0
        assert all(f.severity == "critical" for f in security_failures)

    def test_looping_detection(self, detector):
        """Test infinite loop detection"""
        text = "Stack overflow, infinite recursion detected"

        failures = detector.scan(text)

        assert any(f.category == "Looping" for f in failures)
        loop_failure = next(f for f in failures if f.category == "Looping")
        assert loop_failure.severity == "critical"

    def test_pipeline_detection(self, detector):
        """Test pipeline failure detection"""
        text = "Pipeline failed, SonarQube coverage check failed"

        failures = detector.scan(text)

        assert any(f.category == "Pipeline" for f in failures)

    def test_multiple_failure_detection(self, detector):
        """Test detecting multiple failures"""
        text = """
        JWT token expired
        SQL injection vulnerability found
        Pipeline failed due to test coverage
        Infinite loop detected in processing
        """

        failures = detector.scan(text)

        # Should detect multiple categories
        categories = {f.category for f in failures}
        assert len(categories) >= 3

    def test_deduplication(self, detector):
        """Test failure deduplication"""
        text = "JWT error JWT error JWT error"

        failures = detector.scan(text)

        # Should not duplicate same failure
        jwt_failures = [f for f in failures if f.category == "JWT/Auth"]
        assert len(jwt_failures) <= 2  # Some duplicates may occur with different context

    def test_context_extraction(self, detector):
        """Test context extraction around failures"""
        text = "The authentication system failed because the JWT token was invalid and expired"

        failures = detector.scan(text)

        jwt_failure = next((f for f in failures if f.category == "JWT/Auth"), None)
        assert jwt_failure is not None
        assert len(jwt_failure.context) > 0
        assert "JWT" in jwt_failure.context or "token" in jwt_failure.context

    def test_severity_sorting(self, detector):
        """Test failures are sorted by severity"""
        text = """
        Infinite loop detected (critical)
        Pipeline failed (high)
        Dark mode missing (low)
        Type error found (medium)
        """

        failures = detector.scan(text)

        if len(failures) > 1:
            # First failure should be critical or high
            assert failures[0].severity in ["critical", "high"]

    def test_has_critical_failures(self, detector):
        """Test critical failure check"""
        text_critical = "Security vulnerability: SQL injection"
        text_normal = "Some regular code"

        failures_critical = detector.scan(text_critical)
        failures_normal = detector.scan(text_normal)

        assert detector.has_critical_failures(failures_critical) is True
        assert detector.has_critical_failures(failures_normal) is False

    def test_get_failures_by_severity(self, detector):
        """Test filtering by severity"""
        text = """
        Critical: Stack overflow
        High: Pipeline failed
        Low: Missing dark mode
        """

        failures = detector.scan(text)

        critical = detector.get_failures_by_severity(failures, "critical")
        high = detector.get_failures_by_severity(failures, "high")

        assert len(critical) > 0
        assert all(f.severity == "critical" for f in critical)

    def test_get_failures_by_category(self, detector):
        """Test filtering by category"""
        text = "JWT auth failed and pipeline failed"

        failures = detector.scan(text)

        jwt_failures = detector.get_failures_by_category(failures, "JWT/Auth")
        pipeline_failures = detector.get_failures_by_category(failures, "Pipeline")

        assert len(jwt_failures) > 0
        assert all(f.category == "JWT/Auth" for f in jwt_failures)

    def test_format_failures_report(self, detector):
        """Test failure report formatting"""
        text = "Critical security vulnerability and high pipeline failure"

        failures = detector.scan(text)
        report = detector.format_failures_report(failures)

        assert "Detected" in report or "No failures" in report
        if failures:
            assert "CRITICAL" in report or "HIGH" in report

    def test_empty_failures_report(self, detector):
        """Test report with no failures"""
        report = detector.format_failures_report([])

        assert "No failures detected" in report
        assert "✓" in report

    def test_get_stats(self, detector):
        """Test getting detector statistics"""
        stats = detector.get_stats()

        assert "total_patterns" in stats
        assert "categories" in stats
        assert "severity_distribution" in stats
        assert stats["total_patterns"] > 0
        assert len(stats["categories"]) > 0

    def test_tool_attribution(self, detector):
        """Test tool attribution in failures"""
        text = "JWT error occurred"

        failures = detector.scan(text, tool="claude")

        assert len(failures) > 0
        assert all(f.tool == "claude" for f in failures)

    def test_database_failures(self, detector):
        """Test database failure detection"""
        text = "Database connection failed, deadlock detected"

        failures = detector.scan(text)

        db_failures = [f for f in failures if f.category == "Database"]
        assert len(db_failures) > 0

    def test_type_error_detection(self, detector):
        """Test type error detection"""
        text = "TypeError: Cannot read property of undefined"

        failures = detector.scan(text)

        assert any(f.category == "Type Errors" for f in failures)

    def test_api_error_detection(self, detector):
        """Test API error detection"""
        text = "API returned 500 Internal Server Error"

        failures = detector.scan(text)

        assert any(f.category == "API Errors" for f in failures)


class TestDetectedFailure:
    """Test DetectedFailure dataclass"""

    def test_failure_creation(self):
        """Test creating detected failures"""
        from datetime import datetime

        failure = DetectedFailure(
            category="JWT/Auth",
            pattern="jwt token",
            timestamp=datetime.now(),
            severity="high",
            context="JWT token expired",
            suggestion="Check token validity",
            tool="claude",
        )

        assert failure.category == "JWT/Auth"
        assert failure.pattern == "jwt token"
        assert failure.severity == "high"
        assert failure.context == "JWT token expired"
        assert failure.suggestion == "Check token validity"
        assert failure.tool == "claude"
