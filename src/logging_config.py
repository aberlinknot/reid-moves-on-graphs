"""Structured logging configuration for the project.

Provides:
- JSON output to files (JSONL format, one record per line)
- Pretty console output with colors and levels
- Unified logging across all modules
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert a LogRecord to JSON string."""
        log_data = {
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields if present
        if hasattr(record, "event"):
            log_data["event"] = record.event
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        if hasattr(record, 'extra_fields') and record.extra_fields:
            # Keep custom fields namespaced to avoid overwriting reserved keys.
            log_data['extra_fields'] = record.extra_fields

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Format log records for pretty console output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format record with colors and structure."""
        level = record.levelname
        color = self.COLORS.get(level, "")
        timestamp = self.formatTime(record, "%H:%M:%S")
        logger_name = record.name.split(".")[-1]  # Last component only

        # Build base message
        message = f"{color}[{timestamp}] [{level:8}] {logger_name}{self.RESET}"

        # Add structured fields if present
        if hasattr(record, "event"):
            message += f" | event={record.event}"
        if hasattr(record, "run_id"):
            message += f" | run_id={record.run_id}"

        # Add main message
        message += f"\n  {record.getMessage()}"

        # Add exception if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def setup_logging(
    name: str,
    log_file: Path | None = None,
    level: int = logging.INFO,
    console: bool = True,
    verbose: bool = False,
) -> logging.Logger:
    """Configure and return a logger.

    Parameters
    ----------
    name : str
        Logger name (typically __name__).
    log_file : Path | None, optional
        Path to write JSONL logs. If None, only console output.
    level : int, optional
        Logging level (default: logging.INFO).
    console : bool, optional
        Whether to output to console (default: True).
    verbose : bool, optional
        If True, use DEBUG level (overrides level parameter).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Use DEBUG if verbose flag is set
    if verbose:
        level = logging.DEBUG

    logger.setLevel(level)
    logger.handlers.clear()

    # Console handler (pretty output)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(ConsoleFormatter())
        logger.addHandler(console_handler)

    # File handler (JSON output)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    event: str | None = None,
    run_id: str | None = None,
    extra_fields: dict[str, object] | None = None,
) -> None:
    """Log a structured event with metadata.

    Parameters
    ----------
    logger : logging.Logger
        Logger instance.
    level : int
        Log level (logging.INFO, logging.WARNING, etc.).
    message : str
        Main message text.
    event : str | None, optional
        Event type/category.
    run_id : str | None, optional
        Run identifier for correlation.
    extra_fields : dict[str, object] | None, optional
        Additional fields to include in JSON log.
    """
    record = logger.makeRecord(
        logger.name,
        level,
        "(unknown file)",
        0,
        message,
        (),
        None,
    )
    if event:
        record.event = event
    if run_id:
        record.run_id = run_id
    if extra_fields:
        record.extra_fields = extra_fields

    logger.handle(record)
