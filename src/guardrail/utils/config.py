"""Configuration management for guardrail.dev"""

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class ToolConfig(BaseModel):
    """AI tool configuration"""

    cli_path: str
    enabled: bool = True
    timeout: int = 120  # 2 minutes - guardrails add significant context


class GuardrailsConfig(BaseModel):
    """Guardrails configuration"""

    base_path: str = "~/.guardrail/guardrails"
    files: List[str] = Field(
        default_factory=lambda: ["BPSBS.md", "AI_Guardrails.md", "UX_UI_Guardrails.md"]
    )
    agents_path: str = "~/.guardrail/guardrails/agents"

    @field_validator("base_path", "agents_path")
    @classmethod
    def expand_path(cls, v: str) -> str:
        return str(Path(v).expanduser().resolve())


class DatabaseConfig(BaseModel):
    """Database configuration"""

    path: str = "~/.guardrail/data/guardrail.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24

    @field_validator("path")
    @classmethod
    def expand_path(cls, v: str) -> str:
        return str(Path(v).expanduser().resolve())


class LoggingConfig(BaseModel):
    """Logging configuration"""

    level: str = "INFO"
    file: str = "~/.guardrail/logs/guardrail.log"
    max_size_mb: int = 100
    backup_count: int = 5

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v_upper

    @field_validator("file")
    @classmethod
    def expand_path(cls, v: str) -> str:
        return str(Path(v).expanduser().resolve())


class FeaturesConfig(BaseModel):
    """Feature flags configuration"""

    background_analysis: bool = True
    failure_prediction: bool = False  # Phase 2
    prompt_optimization: bool = False  # Phase 2
    team_sync: bool = False  # Phase 2

    # Background workers (Phase 3)
    analysis_worker: bool = True
    metrics_worker: bool = True
    markdown_export: bool = True
    cleanup_worker: bool = True

    # Version 2 features
    v2_adaptive_learning: bool = True  # Enable adaptive guardrail learning
    v2_task_classification: bool = True  # Enable task type classification
    v2_auto_save_files: bool = True  # Enable automatic file saving
    v2_conversation_history: bool = True  # Enable conversation tracking
    v2_dynamic_guardrails: bool = True  # Load learned guardrails from DB


class TeamConfig(BaseModel):
    """Team synchronization configuration"""

    enabled: bool = False
    sync_repo: str = ""
    sync_interval_hours: int = 1
    branch: str = "main"


class Config(BaseModel):
    """Main configuration model"""

    version: str = "2.0"
    mode: str = "standard"
    default_agent: str = "auto"

    tools: Dict[str, ToolConfig] = Field(
        default_factory=lambda: {
            "claude": ToolConfig(cli_path="claude", enabled=True, timeout=120),
            "gemini": ToolConfig(cli_path="gemini", enabled=True, timeout=120),
            "codex": ToolConfig(cli_path="codex", enabled=True, timeout=120),
        }
    )

    guardrails: GuardrailsConfig = Field(default_factory=GuardrailsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    team: TeamConfig = Field(default_factory=TeamConfig)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        valid_modes = ["standard", "strict"]
        if v not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")
        return v

    class Config:
        extra = "allow"


class Settings(BaseSettings):
    """Environment-based settings with fallback to config file"""

    # Operating Mode
    guardrail_mode: str = "standard"

    # Logging
    guardrail_log_level: str = "INFO"
    guardrail_log_file: str = "~/.guardrail/logs/guardrail.log"
    guardrail_log_max_size_mb: int = 100
    guardrail_log_backup_count: int = 5

    # Database
    guardrail_db_path: str = "~/.guardrail/data/guardrail.db"
    guardrail_db_backup_enabled: bool = True
    guardrail_db_backup_interval_hours: int = 24

    # AI Tool Paths
    guardrail_claude_path: str = "claude"
    guardrail_gemini_path: str = "gemini"
    guardrail_codex_path: str = "codex"

    # Guardrails
    guardrail_base_path: str = "~/.guardrail/guardrails"
    guardrail_agents_path: str = "~/.guardrail/guardrails/agents"

    # Features
    guardrail_background_analysis: bool = True
    guardrail_failure_prediction: bool = False
    guardrail_prompt_optimization: bool = False
    guardrail_team_sync: bool = False

    # Team
    guardrail_team_enabled: bool = False
    guardrail_team_sync_repo: str = ""
    guardrail_team_sync_interval_hours: int = 1
    guardrail_team_branch: str = "main"

    # Performance
    guardrail_timeout_seconds: int = 120  # 2 minutes for AI tools with guardrails
    guardrail_max_retries: int = 3
    guardrail_cache_size_mb: int = 100

    # Development
    guardrail_debug: bool = False
    guardrail_verbose: bool = False
    guardrail_dry_run: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class ConfigManager:
    """Configuration manager for guardrail.dev"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = (
            Path(config_path).expanduser()
            if config_path
            else Path.home() / ".guardrail" / "config.yaml"
        )
        self.settings = Settings()
        self.config: Optional[Config] = None

    def load(self) -> Config:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                config_data = yaml.safe_load(f)
                self.config = Config(**config_data)
        else:
            self.config = self._create_default_config()
            self.save()

        # Override with environment variables
        self._apply_env_overrides()
        return self.config

    def _create_default_config(self) -> Config:
        """Create default configuration"""
        return Config(
            version="2.0",
            mode=self.settings.guardrail_mode,
            default_agent="auto",
            tools={
                "claude": ToolConfig(
                    cli_path=self.settings.guardrail_claude_path,
                    enabled=True,
                    timeout=self.settings.guardrail_timeout_seconds,
                ),
                "gemini": ToolConfig(
                    cli_path=self.settings.guardrail_gemini_path,
                    enabled=True,
                    timeout=self.settings.guardrail_timeout_seconds,
                ),
                "codex": ToolConfig(
                    cli_path=self.settings.guardrail_codex_path,
                    enabled=True,
                    timeout=self.settings.guardrail_timeout_seconds,
                ),
            },
            guardrails=GuardrailsConfig(
                base_path=self.settings.guardrail_base_path,
                agents_path=self.settings.guardrail_agents_path,
            ),
            database=DatabaseConfig(
                path=self.settings.guardrail_db_path,
                backup_enabled=self.settings.guardrail_db_backup_enabled,
                backup_interval_hours=self.settings.guardrail_db_backup_interval_hours,
            ),
            logging=LoggingConfig(
                level=self.settings.guardrail_log_level,
                file=self.settings.guardrail_log_file,
                max_size_mb=self.settings.guardrail_log_max_size_mb,
                backup_count=self.settings.guardrail_log_backup_count,
            ),
            features=FeaturesConfig(
                background_analysis=self.settings.guardrail_background_analysis,
                failure_prediction=self.settings.guardrail_failure_prediction,
                prompt_optimization=self.settings.guardrail_prompt_optimization,
                team_sync=self.settings.guardrail_team_sync,
            ),
            team=TeamConfig(
                enabled=self.settings.guardrail_team_enabled,
                sync_repo=self.settings.guardrail_team_sync_repo,
                sync_interval_hours=self.settings.guardrail_team_sync_interval_hours,
                branch=self.settings.guardrail_team_branch,
            ),
        )

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to config"""
        if not self.config:
            return

        # Mode override
        if os.getenv("GUARDRAIL_MODE"):
            self.config.mode = self.settings.guardrail_mode

        # Tool paths
        if os.getenv("GUARDRAIL_CLAUDE_PATH"):
            self.config.tools["claude"].cli_path = self.settings.guardrail_claude_path
        if os.getenv("GUARDRAIL_GEMINI_PATH"):
            self.config.tools["gemini"].cli_path = self.settings.guardrail_gemini_path
        if os.getenv("GUARDRAIL_CODEX_PATH"):
            self.config.tools["codex"].cli_path = self.settings.guardrail_codex_path

        # Logging
        if os.getenv("GUARDRAIL_LOG_LEVEL"):
            self.config.logging.level = self.settings.guardrail_log_level

        # Features
        if os.getenv("GUARDRAIL_BACKGROUND_ANALYSIS"):
            self.config.features.background_analysis = (
                self.settings.guardrail_background_analysis
            )

    def save(self) -> None:
        """Save configuration to file"""
        if not self.config:
            raise ValueError("No configuration to save")

        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        config_dict = self.config.model_dump()
        with open(self.config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    def get(self, key: str, default: any = None) -> any:
        """Get configuration value by key"""
        if not self.config:
            self.load()

        keys = key.split(".")
        value = self.config
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: any) -> None:
        """Set configuration value by key"""
        if not self.config:
            self.load()

        keys = key.split(".")
        obj = self.config
        for k in keys[:-1]:
            if hasattr(obj, k):
                obj = getattr(obj, k)
            elif isinstance(obj, dict):
                obj = obj[k]

        if hasattr(obj, keys[-1]):
            setattr(obj, keys[-1], value)
        elif isinstance(obj, dict):
            obj[keys[-1]] = value

        self.save()

    def init_directories(self) -> None:
        """Initialize required directories"""
        if not self.config:
            self.load()

        # Create guardrails directory
        Path(self.config.guardrails.base_path).mkdir(parents=True, exist_ok=True)
        Path(self.config.guardrails.agents_path).mkdir(parents=True, exist_ok=True)

        # Create database directory
        Path(self.config.database.path).parent.mkdir(parents=True, exist_ok=True)

        # Create logs directory
        Path(self.config.logging.file).parent.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.load()
    return _config_manager.config


def reload_config() -> Config:
    """Reload configuration from file"""
    global _config_manager
    _config_manager = ConfigManager()
    return _config_manager.load()
