"""Unit tests for CLI commands"""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from guardloop.cli.commands import cli
from guardloop.core.daemon import AIResult
from guardloop.core.parser import ParsedResponse
from guardloop.utils.config import Config


class TestCLI:
    """Test CLI basic functionality"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test CLI help output"""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "GuardLoop" in result.output

    def test_cli_version(self, runner):
        """Test CLI version output"""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "2.2.0" in result.output


class TestRunCommand:
    """Test 'guardrail run' command"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_daemon(self):
        """Mock daemon for testing"""
        with patch("guardloop.cli.commands.GuardrailDaemon") as mock:
            daemon_instance = MagicMock()
            mock.return_value = daemon_instance

            # Mock process_request to return a successful result
            async def mock_process(request):
                return AIResult(
                    raw_output="Test output",
                    parsed=ParsedResponse(),
                    violations=[],
                    failures=[],
                    approved=True,
                    execution_time_ms=100,
                    session_id="test-123",
                )

            daemon_instance.process_request = AsyncMock(side_effect=mock_process)
            yield daemon_instance

    @pytest.fixture
    def mock_config(self):
        """Mock config"""
        with patch("guardloop.cli.commands.get_config") as mock:
            mock.return_value = Config()
            yield mock

    def test_run_command_help(self, runner):
        """Test run command help"""
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "Execute AI tool with policies" in result.output

    def test_run_basic(self, runner, mock_config, mock_daemon):
        """Test basic run command"""
        result = runner.invoke(cli, ["run", "claude", "Test prompt"])
        assert result.exit_code == 0
        # Check that daemon was called
        mock_daemon.process_request.assert_called_once()

    def test_run_with_agent(self, runner, mock_config, mock_daemon):
        """Test run command with agent"""
        result = runner.invoke(cli, ["run", "claude", "Test prompt", "--agent", "architect"])
        assert result.exit_code == 0
        # Verify agent was passed
        call_args = mock_daemon.process_request.call_args[0][0]
        assert call_args.agent == "architect"

    def test_run_with_strict_mode(self, runner, mock_config, mock_daemon):
        """Test run command with strict mode"""
        result = runner.invoke(cli, ["run", "claude", "Test prompt", "--mode", "strict"])
        assert result.exit_code == 0
        # Verify mode was passed
        call_args = mock_daemon.process_request.call_args[0][0]
        assert call_args.mode == "strict"

    def test_run_invalid_tool(self, runner):
        """Test run with invalid tool"""
        result = runner.invoke(cli, ["run", "invalid", "Test prompt"])
        assert result.exit_code != 0
        assert "Invalid value" in result.output


class TestInitCommand:
    """Test 'guardrail init' command"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    def test_init_help(self, runner):
        """Test init command help"""
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize GuardLoop configuration" in result.output

    def test_init_command(self, runner):
        """Test init command execution"""
        with runner.isolated_filesystem():
            with patch("guardloop.cli.commands.ConfigManager") as mock_config:
                with patch("guardloop.cli.commands.DatabaseManager") as mock_db:
                    mock_config_instance = MagicMock()
                    mock_config.return_value = mock_config_instance
                    mock_config_instance.config_path = Path("~/.guardrail/config.yaml")
                    mock_config_instance.load.return_value = Config()

                    result = runner.invoke(cli, ["init"])

                    assert result.exit_code == 0
                    assert "Initializing GuardLoop" in result.output
                    mock_config_instance.init_directories.assert_called_once()


class TestStatusCommand:
    """Test 'guardrail status' command"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    def test_status_help(self, runner):
        """Test status command help"""
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "Show GuardLoop system status" in result.output

    def test_status_command(self, runner):
        """Test status command execution"""
        with patch("guardloop.cli.commands.get_config") as mock_config:
            with patch("guardloop.cli.commands.DatabaseManager") as mock_db:
                mock_config.return_value = Config()
                mock_db_instance = MagicMock()
                mock_db.return_value = mock_db_instance
                mock_db_instance.get_stats.return_value = {
                    "total_sessions": 10,
                    "total_failures": 2,
                    "total_violations": 5,
                    "total_agents_activity": 8,
                    "db_size_mb": 1.5,
                }

                result = runner.invoke(cli, ["status"])

                assert result.exit_code == 0
                assert "System Status" in result.output


class TestConfigCommand:
    """Test 'guardrail config' command"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    def test_config_help(self, runner):
        """Test config command help"""
        result = runner.invoke(cli, ["config", "--help"])
        assert result.exit_code == 0
        assert "Show current configuration" in result.output

    def test_config_command(self, runner):
        """Test config command execution"""
        with patch("guardloop.cli.commands.ConfigManager") as mock_config:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_config_instance.config_path = Path("~/.guardrail/config.yaml")
            mock_config_instance.load.return_value = Config()

            result = runner.invoke(cli, ["config"])

            assert result.exit_code == 0
            assert "Configuration" in result.output


class TestAnalyzeCommand:
    """Test 'guardrail analyze' command"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    def test_analyze_help(self, runner):
        """Test analyze command help"""
        result = runner.invoke(cli, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "Analyze failures and violations" in result.output

    def test_analyze_basic(self, runner):
        """Test basic analyze command"""
        with patch("guardloop.cli.commands.get_config") as mock_config:
            with patch("guardloop.cli.commands.DatabaseManager") as mock_db:
                mock_config.return_value = Config()
                mock_db_instance = MagicMock()
                mock_db.return_value = mock_db_instance
                mock_db_instance.get_stats.return_value = {
                    "total_sessions": 100,
                    "total_failures": 10,
                    "total_violations": 25,
                    "total_agents_activity": 80,
                    "db_size_mb": 5.2,
                }

                result = runner.invoke(cli, ["analyze"])

                assert result.exit_code == 0
                assert "Analyzing" in result.output

    def test_analyze_with_days(self, runner):
        """Test analyze with custom days"""
        with patch("guardloop.cli.commands.get_config") as mock_config:
            with patch("guardloop.cli.commands.DatabaseManager") as mock_db:
                mock_config.return_value = Config()
                mock_db_instance = MagicMock()
                mock_db.return_value = mock_db_instance
                mock_db_instance.get_stats.return_value = {
                    "total_sessions": 50,
                    "total_failures": 5,
                    "total_violations": 12,
                    "total_agents_activity": 40,
                    "db_size_mb": 2.1,
                }

                result = runner.invoke(cli, ["analyze", "--days", "30"])

                assert result.exit_code == 0
                assert "30 days" in result.output


class TestExportCommand:
    """Test 'guardrail export' command"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    def test_export_help(self, runner):
        """Test export command help"""
        result = runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export failures to markdown" in result.output

    def test_export_basic(self, runner):
        """Test basic export command"""
        with runner.isolated_filesystem():
            with patch("guardloop.cli.commands.get_config") as mock_config:
                with patch("guardloop.cli.commands.DatabaseManager") as mock_db:
                    mock_config.return_value = Config()

                    result = runner.invoke(cli, ["export"])

                    assert result.exit_code == 0
                    assert "Exporting" in result.output
                    assert Path("AI_Failure_Modes.md").exists()

    def test_export_custom_output(self, runner):
        """Test export with custom output file"""
        with runner.isolated_filesystem():
            with patch("guardloop.cli.commands.get_config") as mock_config:
                with patch("guardloop.cli.commands.DatabaseManager") as mock_db:
                    mock_config.return_value = Config()

                    result = runner.invoke(cli, ["export", "-o", "custom.md"])

                    assert result.exit_code == 0
                    assert Path("custom.md").exists()


class TestDaemonCommand:
    """Test 'guardrail daemon' command"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    def test_daemon_help(self, runner):
        """Test daemon command help"""
        result = runner.invoke(cli, ["daemon", "--help"])
        assert result.exit_code == 0
        assert "Start GuardLoop daemon" in result.output


class TestInteractiveCommand:
    """Test 'guardrail interactive' command"""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner"""
        return CliRunner()

    def test_interactive_help(self, runner):
        """Test interactive command help"""
        result = runner.invoke(cli, ["interactive", "--help"])
        assert result.exit_code == 0
        assert "Interactive GuardLoop session" in result.output
