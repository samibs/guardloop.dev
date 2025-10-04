"""Configuration tests"""

import pytest
from pathlib import Path
from guardrail.utils.config import (
    Config,
    DatabaseConfig,
    LoggingConfig,
    ToolConfig,
    GuardrailsConfig,
    TeamConfig
)


class TestDatabaseConfig:
    """Test database configuration"""

    def test_default_path(self):
        """Test default database path"""
        db_config = DatabaseConfig()
        assert db_config.path == Path.home() / ".guardrail" / "guardrail.db"

    def test_custom_path(self):
        """Test custom database path"""
        db_config = DatabaseConfig(path="/custom/path/db.sqlite")
        assert db_config.path == Path("/custom/path/db.sqlite")

    def test_memory_database(self):
        """Test in-memory database"""
        db_config = DatabaseConfig(path=":memory:")
        assert db_config.path == Path(":memory:")


class TestLoggingConfig:
    """Test logging configuration"""

    def test_default_logging(self):
        """Test default logging configuration"""
        log_config = LoggingConfig()
        assert log_config.level == "INFO"
        assert log_config.file is None

    def test_custom_level(self):
        """Test custom log level"""
        log_config = LoggingConfig(level="DEBUG")
        assert log_config.level == "DEBUG"

    def test_log_file(self):
        """Test log file configuration"""
        log_config = LoggingConfig(file="/var/log/guardrail.log")
        assert log_config.file == Path("/var/log/guardrail.log")


class TestToolConfig:
    """Test tool configuration"""

    def test_claude_config(self):
        """Test Claude tool configuration"""
        tool_config = ToolConfig(
            cli_path="claude",
            enabled=True,
            timeout=120
        )
        assert tool_config.cli_path == "claude"
        assert tool_config.enabled is True
        assert tool_config.timeout == 120

    def test_disabled_tool(self):
        """Test disabled tool"""
        tool_config = ToolConfig(
            cli_path="gemini",
            enabled=False
        )
        assert tool_config.enabled is False


class TestGuardrailsConfig:
    """Test guardrails configuration"""

    def test_default_guardrails_config(self):
        """Test default guardrails configuration"""
        guardrails_config = GuardrailsConfig()
        assert guardrails_config.base_path == Path.home() / ".guardrail" / "guardrails"
        assert guardrails_config.agents_path == Path.home() / ".guardrail" / "guardrails" / "agents"

    def test_custom_paths(self):
        """Test custom guardrails paths"""
        guardrails_config = GuardrailsConfig(
            base_path="/custom/guardrails",
            agents_path="/custom/agents"
        )
        assert guardrails_config.base_path == Path("/custom/guardrails")
        assert guardrails_config.agents_path == Path("/custom/agents")


class TestTeamConfig:
    """Test team configuration"""

    def test_team_disabled(self):
        """Test team sync disabled"""
        team_config = TeamConfig(enabled=False)
        assert team_config.enabled is False
        assert team_config.sync_repo == ""

    def test_team_enabled(self):
        """Test team sync enabled"""
        team_config = TeamConfig(
            enabled=True,
            sync_repo="git@github.com:org/guardrails.git",
            sync_interval_hours=6,
            branch="develop"
        )
        assert team_config.enabled is True
        assert team_config.sync_repo == "git@github.com:org/guardrails.git"
        assert team_config.sync_interval_hours == 6
        assert team_config.branch == "develop"


class TestConfig:
    """Test main configuration"""

    def test_default_config(self):
        """Test default configuration"""
        config = Config()
        assert config.version == "1.0"
        assert config.mode == "standard"
        assert config.default_agent == "auto"
        assert config.strict is False

    def test_strict_mode(self):
        """Test strict mode configuration"""
        config = Config(mode="strict", strict=True)
        assert config.mode == "strict"
        assert config.strict is True

    def test_tool_configuration(self):
        """Test tool configuration"""
        config = Config(
            tools={
                "claude": ToolConfig(cli_path="claude", enabled=True),
                "gemini": ToolConfig(cli_path="gemini", enabled=False)
            }
        )
        assert "claude" in config.tools
        assert "gemini" in config.tools
        assert config.tools["claude"].enabled is True
        assert config.tools["gemini"].enabled is False

    def test_guardrails_configuration(self):
        """Test guardrails configuration"""
        config = Config(
            default_agent="architect",
            guardrails=GuardrailsConfig(
                base_path="/custom/guardrails"
            )
        )
        assert config.default_agent == "architect"
        assert config.guardrails.base_path == Path("/custom/guardrails")

    def test_team_sync(self):
        """Test team sync configuration"""
        config = Config(
            team=TeamConfig(
                enabled=True,
                sync_repo="git@github.com:org/guardrails.git"
            )
        )
        assert config.team.enabled is True
        assert config.team.sync_repo == "git@github.com:org/guardrails.git"

    def test_database_config(self):
        """Test database configuration"""
        config = Config(
            database=DatabaseConfig(path=":memory:")
        )
        assert config.database.path == Path(":memory:")

    def test_logging_config(self):
        """Test logging configuration"""
        config = Config(
            logging=LoggingConfig(level="DEBUG", file="/tmp/guardrail.log")
        )
        assert config.logging.level == "DEBUG"
        assert config.logging.file == Path("/tmp/guardrail.log")

    def test_load_from_file(self, tmp_path):
        """Test loading configuration from file"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
version: "1.0"
mode: strict
default_agent: architect
strict: true

database:
  path: /tmp/test.db

logging:
  level: DEBUG
  file: /tmp/guardrail.log

tools:
  claude:
    cli_path: claude
    enabled: true
    timeout: 120
""")

        config = Config.from_file(str(config_file))
        assert config.mode == "strict"
        assert config.default_agent == "architect"
        assert config.strict is True
        assert config.database.path == Path("/tmp/test.db")
        assert config.logging.level == "DEBUG"
