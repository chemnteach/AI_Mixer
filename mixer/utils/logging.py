"""Structured logging for The Mixer."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class MixerLogger:
    """Enhanced logger for The Mixer with structured output."""

    def __init__(
        self,
        name: str,
        log_file: Optional[Path] = None,
        level: str = "INFO",
        max_file_size_mb: int = 100,
        backup_count: int = 5,
    ):
        """Initialize logger.

        Args:
            name: Logger name (usually module name).
            log_file: Path to log file. If None, logs to console only.
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            max_file_size_mb: Maximum size of log file before rotation.
            backup_count: Number of backup log files to keep.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Format: timestamp - name - level - message
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler (always enabled)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (if path provided)
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """Log error message.

        Args:
            message: Error message.
            exc_info: If True, include exception traceback.
        """
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False) -> None:
        """Log critical message.

        Args:
            message: Critical error message.
            exc_info: If True, include exception traceback.
        """
        self.logger.critical(message, exc_info=exc_info)

    def exception(self, message: str) -> None:
        """Log exception with traceback."""
        self.logger.exception(message)


def setup_logging(
    log_file: Optional[Path] = None,
    level: str = "INFO",
    max_file_size_mb: int = 100,
    backup_count: int = 5,
) -> None:
    """Setup root logger for The Mixer.

    Args:
        log_file: Path to log file.
        level: Logging level.
        max_file_size_mb: Maximum log file size before rotation.
        backup_count: Number of backup files to keep.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)
