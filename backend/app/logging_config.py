"""
Structured logging configuration for AURA.
Writes JSON-lines logs to file + coloured output to console.
Never logs passwords, API keys, tokens, or file contents.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import structlog
from structlog.types import EventDict, WrappedLogger


# ── Sensitive key scrubber ────────────────────────────────────────────────────

_SENSITIVE_KEYS = frozenset({
    "api_key", "secret_key", "password", "token", "auth",
    "authorization", "credential", "secret", "private_key",
})


def _scrub_sensitive(
    logger: WrappedLogger,
    method: str,
    event_dict: EventDict,
) -> EventDict:
    """Remove sensitive values before they reach any sink."""
    for key in list(event_dict.keys()):
        if any(s in key.lower() for s in _SENSITIVE_KEYS):
            event_dict[key] = "***REDACTED***"
    return event_dict


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup_logging(log_level: str = "INFO", log_dir: Path | None = None) -> None:
    """Configure structlog + stdlib logging."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _scrub_sensitive,
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Console renderer — disable colors if colorama not available on Windows
    try:
        import colorama  # noqa: F401
        _use_colors = True
    except ImportError:
        _use_colors = False

    console_renderer = structlog.dev.ConsoleRenderer(
        colors=_use_colors,
        exception_formatter=structlog.dev.plain_traceback,
    )

    # File renderer (JSON lines)
    file_renderer = structlog.processors.JSONRenderer()

    handlers: list[logging.Handler] = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, console_renderer],
            foreign_pre_chain=shared_processors,
        )
    )
    handlers.append(console_handler)

    # File handler (if log_dir provided)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        log_file = log_dir / f"aura_{today}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, file_renderer],
                foreign_pre_chain=shared_processors,
            )
        )
        handlers.append(file_handler)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers = []
    for h in handlers:
        root_logger.addHandler(h)

    # Quiet noisy third-party loggers
    for name in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)
