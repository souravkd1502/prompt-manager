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
        force=True,  # Force reconfiguration even if logging was already configured
    )

    
    # Log that logging has been initialized
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized successfully")
