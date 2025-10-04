"""Structured logging configuration for guardrail.dev"""

import sys
from pathlib import Path
from typing import Optional

import structlog
from structlog.types import EventDict, Processor

from guardrail.utils.config import get_config


def add_app_context(logger: any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log events"""
    event_dict["app"] = "guardrail.dev"
    return event_dict


def configure_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_logs: bool = False,
) -> None:
    """Configure structured logging for the application

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        json_logs: Whether to output JSON logs (useful for production)
    """
    config = get_config()

    # Use config values if not provided
    if log_level is None:
        log_level = config.logging.level
    if log_file is None:
        log_file = config.logging.file

    # Ensure log directory exists
    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Build shared processor chain (no renderer at the end)
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    # Configure Python's logging first
    import logging
    from logging.handlers import RotatingFileHandler

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        )
    )
    root_logger.addHandler(console_handler)

    # File handler if specified (JSON format)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.logging.max_size_mb * 1024 * 1024,
            backupCount=config.logging.backup_count,
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer(),
            )
        )
        root_logger.addHandler(file_handler)

    # Configure structlog to use stdlib logging
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)
