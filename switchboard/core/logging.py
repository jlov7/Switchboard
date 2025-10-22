from __future__ import annotations

import logging
import os
from typing import Any

import structlog


def configure_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level)
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.dict_tracebacks,
            structlog.processors.format_exc_info,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def redact_args(arguments: dict[str, Any], redacted_fields: list[str]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in arguments.items():
        sanitized[key] = "***" if key in redacted_fields else value
    return sanitized
