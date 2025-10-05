"""Unit tests for GuardrailDaemon"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from guardloop.core.daemon import (
    GuardrailDaemon,
    AIRequest,
    AIResult,
    AIExecutionError,
)
from guardloop.adapters import AIResponse
from guardloop.core.parser import ParsedResponse, CodeBlock
from guardloop.core.validator import Violation
from guardloop.core.failure_detector import DetectedFailure
from guardloop.utils.config import Config
from datetime import datetime


class TestAIRequest:
    """Test AIRequest dataclass"""

    def test_request_creation(self):
        """Test creating AI request"""
        request = AIRequest(tool="claude", prompt="Test prompt", agent="coder")

        assert request.tool == "claude"
        assert request.prompt == "Test prompt"
        assert request.agent == "coder"
        assert request.mode == "standard"
        assert request.session_id is not None

    def test_request_with_custom_session(self):
        """Test request with custom session ID"""
        request = AIRequest(
            tool="gemini",
            prompt="Test",
            mode="strict",
            session_id="custom-123",
        )

        assert request.session_id == "custom-123"
        assert request.mode == "strict"


class TestAIResult:
    """Test AIResult dataclass"""

    def test_result_creation(self):
        """Test creating AI result"""
        parsed = ParsedResponse()
        result = AIResult(
            raw_output="Test output",
            parsed=parsed,
            violations=[],
            failures=[],
            approved=True,
            execution_time_ms=1500,
            session_id="test-123",
        )

        assert result.raw_output == "Test output"
        assert result.approved is True
        assert result.execution_time_ms == 1500
        assert result.session_id == "test-123"


class TestGuardrailDaemon:
    """Test GuardrailDaemon functionality"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return Config(
            mode="standard",
            tools={
                "claude": {
                    "enabled": True,
                    "cli_path": "claude",
                    "timeout": 30,
                }
            },
        )

    @pytest.fixture
    def daemon(self, config):
        """Create daemon instance"""
        with patch("guardrail.core.daemon.DatabaseManager"):
            return GuardrailDaemon(config)

    def test_initialization(self, daemon, config):
        """Test daemon initialization"""
        assert daemon.config == config
        assert daemon.context_manager is not None
        assert daemon.parser is not None
        assert daemon.validator is not None
        assert daemon.failure_detector is not None

    def test_get_adapter_success(self, daemon):
        """Test getting adapter for enabled tool"""
        with patch("guardrail.core.daemon.AdapterFactory.get_adapter") as mock_factory:
            mock_factory.return_value = MagicMock()
            adapter = daemon.get_adapter("claude")
            assert adapter is not None
            mock_factory.assert_called_once()

    def test_get_adapter_disabled_tool(self, daemon):
        """Test getting adapter for disabled tool"""
        with pytest.raises(ValueError) as exc_info:
            daemon.get_adapter("invalid_tool")
        assert "not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_request_success(self, daemon):
        """Test successful request processing"""
        request = AIRequest(tool="claude", prompt="Test prompt")

        # Mock all dependencies
        daemon.context_manager.build_context = MagicMock(
            return_value="<guardrails>Test</guardrails>\n\nTest prompt"
        )

        mock_adapter = AsyncMock()
        mock_adapter.execute = AsyncMock(
            return_value=AIResponse(
                raw_output="Test response",
                execution_time_ms=1000,
                exit_code=0,
            )
        )
        daemon.get_adapter = MagicMock(return_value=mock_adapter)

        daemon.parser.parse = MagicMock(return_value=ParsedResponse())
        daemon.validator.validate = AsyncMock(return_value=[])
        daemon.failure_detector.scan = MagicMock(return_value=[])
        daemon._log_session = AsyncMock()

        result = await daemon.process_request(request)

        assert isinstance(result, AIResult)
        assert result.approved is True
        assert result.raw_output == "Test response"
        assert len(result.violations) == 0
        assert len(result.failures) == 0

    @pytest.mark.asyncio
    async def test_process_request_with_violations(self, daemon):
        """Test request with violations in standard mode"""
        request = AIRequest(tool="claude", prompt="Test", mode="standard")

        daemon.context_manager.build_context = MagicMock(return_value="context")
        mock_adapter = AsyncMock()
        mock_adapter.execute = AsyncMock(
            return_value=AIResponse("output", 1000, exit_code=0)
        )
        daemon.get_adapter = MagicMock(return_value=mock_adapter)

        daemon.parser.parse = MagicMock(return_value=ParsedResponse())

        violations = [
            Violation(
                guardrail_type="bpsbs",
                rule="test",
                severity="high",
                description="Test violation",
                suggestion="Fix it",
            )
        ]
        daemon.validator.validate = AsyncMock(return_value=violations)
        daemon.failure_detector.scan = MagicMock(return_value=[])
        daemon._log_session = AsyncMock()

        result = await daemon.process_request(request)

        # Standard mode should approve despite violations
        assert result.approved is True
        assert len(result.violations) == 1

    @pytest.mark.asyncio
    async def test_process_request_strict_mode_blocking(self, daemon):
        """Test strict mode blocks critical violations"""
        daemon.config.mode = "strict"
        daemon.validator.mode = "strict"

        request = AIRequest(tool="claude", prompt="Test", mode="strict")

        daemon.context_manager.build_context = MagicMock(return_value="context")
        mock_adapter = AsyncMock()
        mock_adapter.execute = AsyncMock(
            return_value=AIResponse("output", 1000, exit_code=0)
        )
        daemon.get_adapter = MagicMock(return_value=mock_adapter)

        daemon.parser.parse = MagicMock(return_value=ParsedResponse())

        critical_violations = [
            Violation(
                guardrail_type="bpsbs",
                rule="security",
                severity="critical",
                description="Critical security issue",
                suggestion="Fix immediately",
            )
        ]
        daemon.validator.validate = AsyncMock(return_value=critical_violations)
        daemon.validator.get_critical_violations = MagicMock(
            return_value=critical_violations
        )
        daemon.failure_detector.scan = MagicMock(return_value=[])
        daemon._log_session = AsyncMock()

        result = await daemon.process_request(request)

        # Strict mode should block
        assert result.approved is False
        assert len(result.violations) == 1

    @pytest.mark.asyncio
    async def test_process_request_execution_error(self, daemon):
        """Test handling of AI execution errors"""
        request = AIRequest(tool="claude", prompt="Test")

        daemon.context_manager.build_context = MagicMock(return_value="context")

        mock_adapter = AsyncMock()
        mock_adapter.execute = AsyncMock(
            return_value=AIResponse(
                raw_output="",
                execution_time_ms=0,
                error="Execution failed",
                exit_code=1,
            )
        )
        daemon.get_adapter = MagicMock(return_value=mock_adapter)

        with pytest.raises(AIExecutionError) as exc_info:
            await daemon.process_request(request)

        assert "Execution failed" in str(exc_info.value)

    def test_enforce_standard_mode(self, daemon):
        """Test enforcement in standard mode"""
        violations = [
            Violation("bpsbs", "test", "critical", "Issue", "Fix"),
        ]
        failures = []

        approved = daemon._enforce("standard", violations, failures)

        # Standard mode always approves
        assert approved is True

    def test_enforce_strict_mode_with_critical(self, daemon):
        """Test enforcement in strict mode with critical violations"""
        violations = [
            Violation("bpsbs", "security", "critical", "Critical issue", "Fix ASAP"),
        ]
        failures = []

        approved = daemon._enforce("strict", violations, failures)

        # Strict mode blocks critical violations
        assert approved is False

    def test_enforce_strict_mode_with_critical_failure(self, daemon):
        """Test enforcement in strict mode with critical failures"""
        violations = []
        failures = [
            DetectedFailure(
                category="Security",
                pattern="sql injection",
                timestamp=datetime.now(),
                severity="critical",
                context="vulnerability detected",
            )
        ]

        approved = daemon._enforce("strict", violations, failures)

        # Strict mode blocks critical failures
        assert approved is False

    def test_enforce_strict_mode_no_critical(self, daemon):
        """Test enforcement in strict mode without critical issues"""
        violations = [
            Violation("ux_ui", "labels", "low", "Vague label", "Be specific"),
        ]
        failures = []

        approved = daemon._enforce("strict", violations, failures)

        # Strict mode approves non-critical issues
        assert approved is True

    @pytest.mark.asyncio
    async def test_log_session(self, daemon):
        """Test session logging"""
        request = AIRequest(tool="claude", prompt="Test prompt", agent="coder")
        response = AIResponse("Test output", 1500, exit_code=0)
        parsed = ParsedResponse()
        violations = []
        failures = []

        await daemon._log_session(
            request, response, parsed, violations, failures, True, 1500
        )

        # Should complete without errors
        # Actual database logging is mocked

    def test_get_stats(self, daemon):
        """Test getting daemon statistics"""
        stats = daemon.get_stats()

        assert "mode" in stats
        assert "enabled_tools" in stats
        assert "context_manager" in stats
        assert "validator_mode" in stats
        assert "failure_detector" in stats
        assert stats["mode"] == "standard"


class TestDaemonIntegration:
    """Integration tests for daemon flow"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return Config(
            mode="standard",
            tools={
                "claude": {
                    "enabled": True,
                    "cli_path": "claude",
                    "timeout": 30,
                }
            },
        )

    @pytest.mark.asyncio
    async def test_full_flow_with_code_generation(self, config):
        """Test full flow with code generation and validation"""
        with patch("guardrail.core.daemon.DatabaseManager"):
            daemon = GuardrailDaemon(config)

            request = AIRequest(
                tool="claude",
                prompt="Create a Python function to add two numbers",
            )

            # Mock context
            daemon.context_manager.build_context = MagicMock(
                return_value="<guardrails>...</guardrails>\n\nCreate function"
            )

            # Mock AI response with code
            ai_output = """
Here's a Python function:

```python
def add(a: int, b: int) -> int:
    return a + b
```

Test coverage: 100%
"""

            mock_adapter = AsyncMock()
            mock_adapter.execute = AsyncMock(
                return_value=AIResponse(ai_output, 1200, exit_code=0)
            )
            daemon.get_adapter = MagicMock(return_value=mock_adapter)

            # Mock parser
            parsed = ParsedResponse(
                code_blocks=[
                    CodeBlock("python", "def add(a: int, b: int) -> int:\n    return a + b")
                ],
                test_coverage=100.0,
            )
            daemon.parser.parse = MagicMock(return_value=parsed)

            # Mock validator (no violations for 100% coverage)
            daemon.validator.validate = AsyncMock(return_value=[])

            # Mock failure detector (no failures)
            daemon.failure_detector.scan = MagicMock(return_value=[])

            daemon._log_session = AsyncMock()

            result = await daemon.process_request(request)

            assert result.approved is True
            assert result.parsed.test_coverage == 100.0
            assert len(result.parsed.code_blocks) == 1
            assert len(result.violations) == 0
            assert len(result.failures) == 0
