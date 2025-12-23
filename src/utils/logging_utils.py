#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared logging helpers.

Goal: avoid `print()` in runtime code and consistently log to the repo `logs/` folder.

This module intentionally keeps configuration minimal and avoids changing global logging
configuration (no logging.basicConfig()).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any


def _get_repo_root() -> Path:
    # This file is located at: <repo>/src/utils/logging_utils.py
    return Path(__file__).resolve().parents[2]


def get_logger(name: str, *, level: int = logging.INFO, log_file: str | None = None) -> logging.Logger:
    """Return a logger configured with a UTF-8 file handler under `logs/`.

    The handler is added only once per (logger, log_file) pair.
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    logs_dir = _get_repo_root() / "logs"
    log_filename = log_file or f"{name.replace('.', '_')}.log"
    log_path = str((logs_dir / log_filename).resolve())

    already_has_same_file_handler = any(
        isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == log_path
        for h in logger.handlers
    )

    if not already_has_same_file_handler:
        os.makedirs(str(logs_dir), exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    # Avoid double-logging if root logging is configured elsewhere.
    logger.propagate = False
    return logger


def print_to_logger(
    logger: logging.Logger,
    *args: Any,
    sep: str = " ",
    end: str = "\n",
    file: Any | None = None,
    flush: bool = False,
) -> None:
    """A drop-in replacement for `print()` that logs to a file.

    - Defaults to INFO
    - If `file` is stderr-like, uses ERROR level
    """

    _ = flush  # not applicable for file logging
    message = sep.join("" if a is None else str(a) for a in args)
    if end and end != "\n":
        message = f"{message}{end}"

    # Keep log lines tidy (logging already appends newline in handlers).
    message = message.rstrip("\n")

    is_stderr = False
    try:
        import sys

        is_stderr = file is sys.stderr
    except Exception:
        is_stderr = False

    if is_stderr:
        logger.error(message)
    else:
        logger.info(message)
