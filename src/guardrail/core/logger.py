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

    # Build processor chain
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
    ]

    # Add appropriate renderer
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog.stdlib.logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    # Also configure file logging if specified
    if log_file:
        import logging
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.logging.max_size_mb * 1024 * 1024,
            backupCount=config.logging.backup_count,
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))

        # JSON format for file logs
        file_formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=processors,
        )
        file_handler.setFormatter(file_formatter)

        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        root_logger.setLevel(getattr(logging, log_level.upper()))


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)
