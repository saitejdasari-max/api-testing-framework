"""
utils/logger.py
───────────────
Structured, coloured logger shared across the entire framework.
Call `get_logger(__name__)` in any module to get a named logger.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import colorlog

from configs.config_manager import get_config

_INITIALIZED: bool = False


def _initialize_logging() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return

    cfg = get_config()
    log_level = getattr(logging, cfg.logging.level, logging.DEBUG)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # ── Console handler (colour) ────────────────────────────────────────────
    console_fmt = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)-8s] %(name)s — %(message)s%(reset)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_fmt)
    root_logger.addHandler(console_handler)

    # ── File handler (plain) ────────────────────────────────────────────────
    if cfg.logging.to_file:
        log_dir: Path = cfg.logging.log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        file_path = log_dir / "test_run.log"

        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(file_fmt)
        root_logger.addHandler(file_handler)

    # Silence overly chatty third-party libraries
    for noisy in ("urllib3", "requests", "charset_normalizer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, initialising logging on first call."""
    _initialize_logging()
    return logging.getLogger(name)
