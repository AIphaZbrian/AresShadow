"""
ARES STRUCTURE ENGINE v1.0 — Logging Utility
"""

import logging
import os
import sys

def get_logger(name: str = "ares") -> logging.Logger:
    """Return a configured logger instance."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter(
            "[%(asctime)s] %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level, logging.INFO))
    return logger
