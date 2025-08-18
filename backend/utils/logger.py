"""
Centralized logging setup for the Prompt Manager backend.
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger with a standard format.

    Args:
        level (int, optional): Logging level (default: logging.INFO).
    """
    # Reset existing logging handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(filename)s:%(lineno)d | %(message)s"
    )

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Reduce SQLAlchemy noise


def get_logger(name: str) -> logging.Logger:
    """
    Get a module-specific logger.

    Args:
        name (str): Logger name (usually __name__).

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)
