"""Unit tests for AI tool adapters"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from guardrail.adapters import (
    AIResponse,
    BaseAdapter,
    ClaudeAdapter,
    GeminiAdapter,
    CodexAdapter,
    AdapterFactory,
)


class TestAIResponse:
    """Test AIResponse dataclass"""

    def test_response_creation(self):
        """Test creating AI response"""
        response = AIResponse(
            raw_output="Test output",
            execution_time_ms=1500,
            error=None,
            exit_code=0,
            stdout="Output",
            stderr="",
        )

        assert response.raw_output == "Test output"
        assert response.execution_time_ms == 1500
        assert response.error is None
        assert response.exit_code == 0


class TestClaudeAdapter:
    """Test Claude adapter"""

    @pytest.fixture
    def adapter(self):
        """Create Claude adapter"""
        return ClaudeAdapter(cli_path="claude", timeout=30)

    def test_initialization(self, adapter):
        """Test adapter initialization"""
        assert adapter.cli_path == "claude"
        assert adapter.timeout == 30
        assert adapter.tool_name == "Claude"

    @pytest.mark.asyncio
    async def test_execute_with_mock(self, adapter):
        """Test execute with mocked subprocess"""
        mock_response = AIResponse(
            raw_output="Test response",
            execution_time_ms=1000,
            exit_code=0,
            stdout="Test response",
        )

        adapter._execute_with_retry = AsyncMock(return_value=mock_response)

        response = await adapter.execute("Test prompt")

        assert response.raw_output == "Test response"
        assert response.execution_time_ms == 1000

    def test_validate_installation_not_installed(self, adapter):
        """Test validation when tool not installed"""
        with patch.object(adapter, "is_installed", return_value=False):
            assert adapter.validate_installation() is False

    def test_validate_installation_success(self, adapter):
        """Test validation when tool is installed"""
        with patch.object(adapter, "is_installed", return_value=True):
            with patch.object(adapter, "get_version", return_value="1.0.0"):
                assert adapter.validate_installation() is True


class TestGeminiAdapter:
    """Test Gemini adapter"""

    @pytest.fixture
    def adapter(self):
        """Create Gemini adapter"""
        return GeminiAdapter(cli_path="gemini", timeout=30)

    def test_initialization(self, adapter):
        """Test adapter initialization"""
        assert adapter.cli_path == "gemini"
        assert adapter.timeout == 30
        assert adapter.tool_name == "Gemini"


class TestCodexAdapter:
    """Test Codex adapter"""

    @pytest.fixture
    def adapter(self):
        """Create Codex adapter"""
        return CodexAdapter(cli_path="codex", timeout=30)

    def test_initialization(self, adapter):
        """Test adapter initialization"""
        assert adapter.cli_path == "codex"
        assert adapter.timeout == 30
        assert adapter.tool_name == "Codex"


class TestAdapterFactory:
    """Test AdapterFactory"""

    def test_get_adapter_claude(self):
        """Test getting Claude adapter"""
        adapter = AdapterFactory.get_adapter("claude", timeout=30)

        assert isinstance(adapter, ClaudeAdapter)
        assert adapter.timeout == 30

    def test_get_adapter_gemini(self):
        """Test getting Gemini adapter"""
        adapter = AdapterFactory.get_adapter("gemini", timeout=30)

        assert isinstance(adapter, GeminiAdapter)

    def test_get_adapter_codex(self):
        """Test getting Codex adapter"""
        adapter = AdapterFactory.get_adapter("codex", timeout=30)

        assert isinstance(adapter, CodexAdapter)

    def test_get_adapter_invalid(self):
        """Test getting invalid adapter"""
        with pytest.raises(ValueError) as exc_info:
            AdapterFactory.get_adapter("invalid_tool")

        assert "Unsupported AI tool" in str(exc_info.value)

    def test_get_adapter_with_custom_path(self):
        """Test getting adapter with custom CLI path"""
        adapter = AdapterFactory.get_adapter(
            "claude", cli_path="/custom/path/claude", timeout=60
        )

        assert adapter.cli_path == "/custom/path/claude"
        assert adapter.timeout == 60

    def test_get_supported_tools(self):
        """Test getting supported tools list"""
        tools = AdapterFactory.get_supported_tools()

        assert "claude" in tools
        assert "gemini" in tools
        assert "codex" in tools
        assert len(tools) == 3

    def test_validate_all_tools(self):
        """Test validating all tools"""
        tools_config = {
            "claude": {"enabled": True, "cli_path": "claude", "timeout": 30},
            "gemini": {"enabled": False, "cli_path": "gemini", "timeout": 30},
        }

        with patch.object(ClaudeAdapter, "validate_installation", return_value=True):
            results = AdapterFactory.validate_all_tools(tools_config)

            assert "claude" in results
            assert "gemini" in results
            assert results["gemini"] is False  # Disabled


class TestBaseAdapter:
    """Test BaseAdapter functionality"""

    def test_is_installed(self):
        """Test command existence check"""
        adapter = ClaudeAdapter()

        with patch("shutil.which", return_value="/usr/bin/claude"):
            assert adapter.is_installed() is True

        with patch("shutil.which", return_value=None):
            assert adapter.is_installed() is False

    def test_parse_version(self):
        """Test version parsing"""
        adapter = ClaudeAdapter()

        assert adapter._parse_version("version 1.2.3") == "1.2.3"
        assert adapter._parse_version("v2.0.0") == "2.0.0"
        assert adapter._parse_version("Claude CLI 1.5.0") == "1.5.0"

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """Test execution timeout handling"""
        adapter = ClaudeAdapter(timeout=1)

        # Mock a long-running process that will timeout
        async def mock_long_process(prompt, timeout):
            import asyncio
            # Simulate timeout by raising TimeoutError
            raise asyncio.TimeoutError("Simulated timeout")

        adapter._execute_subprocess = mock_long_process

        response = await adapter._execute_with_retry("test", timeout=1)

        # Should fail due to timeout
        assert response.exit_code != 0
        assert response.error is not None
        assert "Timeout" in response.error

    @pytest.mark.asyncio
    async def test_retry_logic(self):
        """Test retry logic on failure"""
        adapter = ClaudeAdapter()
        adapter.max_retries = 3
        adapter.retry_delay = 0.01  # Fast retry for testing

        call_count = 0

        async def mock_failing_execute(prompt, timeout):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return AIResponse("", 0, exit_code=1, error="Failed")
            return AIResponse("Success", 100, exit_code=0)

        adapter._execute_subprocess = mock_failing_execute

        response = await adapter._execute_with_retry("test")

        # Should have retried and eventually succeeded
        assert call_count == 3
        assert response.exit_code == 0


@pytest.mark.asyncio
class TestAsyncAdapterOperations:
    """Test async adapter operations"""

    async def test_concurrent_execution(self):
        """Test executing multiple adapters concurrently"""
        import asyncio

        adapters = [
            ClaudeAdapter(),
            GeminiAdapter(),
            CodexAdapter(),
        ]

        # Mock all executions
        for adapter in adapters:
            adapter._execute_with_retry = AsyncMock(
                return_value=AIResponse("Test", 100, exit_code=0)
            )

        # Execute concurrently
        results = await asyncio.gather(
            *[adapter.execute("test") for adapter in adapters]
        )

        assert len(results) == 3
        assert all(r.exit_code == 0 for r in results)
