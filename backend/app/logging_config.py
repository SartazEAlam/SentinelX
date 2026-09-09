"""Structured logging configuration for SentinelX backend."""

import logging
import sys
from datetime import UTC, datetime


class SensitiveFieldFilter(logging.Filter):
    """Filter that redacts sensitive information from log records.

    Prevents accidental logging of passwords, tokens, secrets, and
    sensitive file contents.
    """

    SENSITIVE_PATTERNS: frozenset[str] = frozenset({
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "jwt",
        "authorization",
        "credential",
    })

    def filter(self, record: logging.LogRecord) -> bool:
        """Allow the record but redact any sensitive content."""
        raw_text = str(record.msg).lower()
        args_text = ""
        if record.args:
            try:
                args_text = str(record.getMessage()).lower()
            except Exception:
                args_text = str(record.args).lower()

        combined = f"{raw_text} {args_text}"
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in combined:
                record.msg = f"[REDACTED - message contained '{pattern}']"
                record.args = None
                break
        return True


class StructuredFormatter(logging.Formatter):
    """Formatter that produces structured, contextual log lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record with timestamp, level, module, and message."""
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        level = record.levelname.ljust(8)
        module = record.name
        message = super().format(record)
        return f"{timestamp} | {level} | {module} | {message}"


def setup_logging(level: str = "INFO") -> None:
    """Configure application-wide structured logging.

    Args:
        level: The log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicate output
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(StructuredFormatter())
    console_handler.addFilter(SensitiveFieldFilter())

    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if level.upper() == "DEBUG" else logging.WARNING
    )

    logging.getLogger(__name__).info(
        "Logging initialized - level=%s", level.upper()
    )
