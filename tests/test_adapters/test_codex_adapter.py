"""Unit tests for the Codex AI tool adapter"""

import pytest
from unittest.mock import AsyncMock, patch
from guardloop.adapters.codex import CodexAdapter
from guardloop.adapters.base import AIResponse

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

    def test_build_command(self, adapter):
        """Test the _build_command method"""
        prompt = "Hello, world!"
        command = adapter._build_command(prompt)
        assert command == ["codex", "complete", prompt]

    @pytest.mark.asyncio
    async def test_execute_with_mock(self, adapter):
        """Test execute with mocked subprocess"""
        mock_response = AIResponse(
            raw_output="Test response from Codex",
            execution_time_ms=1200,
            exit_code=0,
            stdout="Test response from Codex",
        )

        adapter._execute_with_retry = AsyncMock(return_value=mock_response)

        response = await adapter.execute("Test prompt")

        assert response.raw_output == "Test response from Codex"
        assert response.execution_time_ms == 1200

    def test_validate_installation_not_installed(self, adapter):
        """Test validation when tool not installed"""
        with patch.object(adapter, "is_installed", return_value=False):
            assert adapter.validate_installation() is False

    def test_validate_installation_success(self, adapter):
        """Test validation when tool is installed"""
        with patch.object(adapter, "is_installed", return_value=True):
            with patch.object(adapter, "get_version", return_value="1.0.0"):
                assert adapter.validate_installation() is True