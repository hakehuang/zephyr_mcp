#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared logging helpers.

Goal: avoid `print()` in runtime code and consistently log to the repo `logs/` folder.

This module intentionally keeps configuration minimal and avoids changing global logging
configuration (no logging.basicConfig()).
"""

from __future__ import annotations

import io
from contextvars import ContextVar
from contextlib import contextmanager
import logging
import os
from pathlib import Path
from typing import Any


_DEBUG_BUFFER: ContextVar[list[str] | None] = ContextVar("zephyr_mcp_debug_buffer", default=None)


class _TruncatingListWriter(io.TextIOBase):
    def __init__(
        self,
        buffer: list[str],
        prefix: str,
        *,
        max_chars: int = 20000,
    ) -> None:
        self._buffer = buffer
        self._prefix = prefix
        self._max_chars = max_chars
        self._total_chars = 0
        self._truncated = False

    def write(self, s: str) -> int:  # type: ignore[override]
        if not s:
            return 0
        if self._truncated:
            return len(s)

        # Split into lines but keep ordering. Avoid emitting empty trailing line.
        lines = s.splitlines()
        if s.endswith("\n"):
            lines.append("")

        for line in lines:
            if line == "":
                continue
            entry = f"{self._prefix}{line}"
            remaining = self._max_chars - self._total_chars
            if remaining <= 0:
                self._buffer.append(f"{self._prefix}<truncated>")
                self._truncated = True
                break

            if len(entry) > remaining:
                self._buffer.append(entry[:remaining])
                self._buffer.append(f"{self._prefix}<truncated>")
                self._total_chars += remaining
                self._truncated = True
                break

            self._buffer.append(entry)
            self._total_chars += len(entry)

        return len(s)


class _BytesToTextWriter(io.RawIOBase):
    """A minimal bytes writer that forwards to a text writer.

    Some libraries (notably pip/setuptools) write to `sys.stdout.buffer`.
    When we replace `sys.stdout` with a custom `io.TextIOBase`, those callers may
    still expect a `.buffer` attribute.
    """

    def __init__(self, text_writer: "StdioLoggerWriter", *, encoding: str = "utf-8", errors: str = "replace"):
        self._text_writer = text_writer
        self._encoding = encoding
        self._errors = errors

    def writable(self) -> bool:  # type: ignore[override]
        return True

    def write(self, b: bytes | bytearray | memoryview) -> int:  # type: ignore[override]
        text = bytes(b).decode(self._encoding, errors=self._errors)
        return self._text_writer.write(text)

    def flush(self) -> None:  # type: ignore[override]
        self._text_writer.flush()


class StdioLoggerWriter(io.TextIOBase):
    """A file-like object that logs writes and can optionally raise.

    Used to enforce: tools should not write to stdout/stderr; they should log instead.

    Note: `io.TextIOBase` exposes read-only `encoding`/`errors` attributes (implemented as
    C-level descriptors). Setting them directly raises:
    `attribute 'encoding' of '_io._TextIOBase' objects is not writable`.

    To stay compatible with callers that expect `sys.stdout.encoding`, `sys.stdout.errors`,
    and `sys.stdout.buffer`, we provide them as properties.
    """

    def __init__(
        self,
        logger: logging.Logger,
        *,
        level: int,
        prefix: str,
        strict: bool,
        encoding: str = "utf-8",
        errors: str = "replace",
    ) -> None:
        self._logger = logger
        self._level = level
        self._prefix = prefix
        self._strict = strict
        self._raised = False

        self._encoding = encoding
        self._errors = errors
        self._buffer = _BytesToTextWriter(self, encoding=encoding, errors=errors)

    @property
    def encoding(self) -> str:  # type: ignore[override]
        return self._encoding

    @property
    def errors(self) -> str:  # type: ignore[override]
        return self._errors

    @property
    def buffer(self) -> _BytesToTextWriter:  # type: ignore[override]
        return self._buffer

    def flush(self) -> None:  # type: ignore[override]
        return

    def isatty(self) -> bool:  # type: ignore[override]
        return False

    def write(self, s: str) -> int:  # type: ignore[override]
        if not s:
            return 0

        # Keep behavior similar to print(): log line by line.
        for line in s.splitlines():
            if not line:
                continue
            msg = f"{self._prefix}{line}"
            try:
                self._logger.log(self._level, msg)
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        if self._strict and not self._raised and s.strip():
            self._raised = True
            raise RuntimeError(
                "Tool attempted to write to stdout/stderr. Use the provided logger instead of print()/stdout writes."
            )

        return len(s)


@contextmanager
def redirect_stdio_to_logger(
    logger: logging.Logger,
    *,
    strict: bool,
    stdout_level: int = logging.INFO,
    stderr_level: int = logging.ERROR,
    stdout_prefix: str = "STDOUT: ",
    stderr_prefix: str = "STDERR: ",
):
    """Temporarily redirect `sys.stdout`/`sys.stderr` to the provided `logger`.

    This ensures accidental writes to stdout/stderr do not leak to transports (e.g. MCP stdio),
    while still recording the messages to the repo log files and (when debug capture is enabled)
    returning them to callers.
    """

    import sys

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StdioLoggerWriter(
        logger,
        level=stdout_level,
        prefix=stdout_prefix,
        strict=strict,
    )
    sys.stderr = StdioLoggerWriter(
        logger,
        level=stderr_level,
        prefix=stderr_prefix,
        strict=strict,
    )
    try:
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


@contextmanager
def capture_stdio(
    buffer: list[str],
    *,
    max_chars: int = 20000,
):
    """Capture prints/writes to stdout/stderr into `buffer`.

    This is used by MCP/HTTP wrappers to ensure any `print()` output is returned to callers
    via the `debug` field, and does not leak to the MCP stdio transport.
    """

    import contextlib

    stdout_writer = _TruncatingListWriter(buffer, "STDOUT: ", max_chars=max_chars)
    stderr_writer = _TruncatingListWriter(buffer, "STDERR: ", max_chars=max_chars)
    with contextlib.redirect_stdout(stdout_writer), contextlib.redirect_stderr(stderr_writer):
        yield buffer


class _ContextDebugHandler(logging.Handler):
    """A logging handler that appends formatted records to a context-local list."""

    def emit(self, record: logging.LogRecord) -> None:
        buffer = _DEBUG_BUFFER.get()
        if buffer is None:
            return
        try:
            buffer.append(self.format(record))
        except Exception:  # pylint: disable=broad-exception-caught
            # Never break execution due to debug capture issues.
            return


@contextmanager
def capture_debug_logs(buffer: list[str]):
    """Capture logs produced during this context into `buffer`.

    This is used by the MCP/HTTP runtime wrappers to expose debug info to callers.
    """

    token = _DEBUG_BUFFER.set(buffer)
    try:
        yield buffer
    finally:
        _DEBUG_BUFFER.reset(token)


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

    # Add a context debug handler (only once per logger) so callers can opt-in to receiving
    # log lines in tool results without changing each tool implementation.
    if not any(isinstance(h, _ContextDebugHandler) for h in logger.handlers):
        debug_handler = _ContextDebugHandler()
        debug_handler.setLevel(level)
        debug_handler.setFormatter(
            logging.Formatter(
                fmt="%(levelname)s %(name)s: %(message)s",
            )
        )
        logger.addHandler(debug_handler)

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
    except Exception:  # pylint: disable=broad-exception-caught
        is_stderr = False

    if is_stderr:
        logger.error(message)
    else:
        logger.info(message)
