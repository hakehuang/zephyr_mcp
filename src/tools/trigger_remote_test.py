#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trigger Remote Test Tool

This tool does not directly execute a remote pipeline.
Instead, it generates a ready-to-edit request prompt for a remote CI system
(e.g., Jenkins / Bitbucket / custom API) and asks the user to update the
content before submitting.

The output is intentionally provided in the exact text format requested by
the user so it can be pasted into another system or used as an instruction
payload.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.utils.logging_utils import get_logger


logger = get_logger(__name__)


def _quote_value(value: Any) -> str:
    """Render parameter values in the legacy single-/double-quote style."""
    value_str = "" if value is None else str(value)
    if '"' in value_str and "'" not in value_str:
        return f"'{value_str}'"
    return f'"{value_str}"'


def _render_prompt(job_full_name: str, parameters: Dict[str, Any]) -> str:
    """Render the exact trigger_build text block using the provided values."""
    items = list(parameters.items())
    lines = [
        "trigger_build",
        "{",
        f'\t"jobFullName": "{job_full_name}"',
        '"parameters"  = {',
    ]

    for index, (key, value) in enumerate(items):
        suffix = "," if index < len(items) - 1 else ""
        lines.append(f"\t'{key}': {_quote_value(value)}{suffix}")

    lines.extend(["}", "}"])
    return "\n".join(lines)


def trigger_remote_test(
    jobFullName: str = "zephyr_test_pipe_quick",
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a remote test trigger prompt template.

    Function Description:
    - Generates a prompt in the requested `trigger_build { ... }` format.
    - Returns both the rendered prompt text and a structured representation.

    Parameters:
    - jobFullName (str): Remote job full name. Default: "zephyr_test_pipe_quick".
    - parameters (Optional[Dict[str, Any]]): Optional parameter overrides.
      These values are applied to both the structured request and the prompt.

    Returns:
    - Dict[str, Any]:
        - status: "success"
        - prompt: The rendered text to paste/submit
        - request: A machine-readable request object (jobFullName + parameters)
        - instructions: Short instructions asking user to verify content
    """

    logger.info("[trigger_remote_test] Generating remote test trigger prompt")

    default_parameters: Dict[str, Any] = {
        "TEST_TARGET_SERIES": "mimxrt1170_evk@A/mimxrt1176/cm4",
        "TEST_NOTIFIER": "hake.huang@nxp.com",
        "TEST_TWISTER_ADDITIONAL_PARAM": "",
        "TEST_TWISTER_SYSBUILD": "",
        "TEST_HWV2": "Y",
        "TEST_TARGET_BRANCH": "main",
        "TEST_TARGET_REPO": "https://github.com/zephyrproject-rtos/zephyr.git",
        "TEST_TARGET_COMMIT_HASH": "",
        "TEST_TARGET_PULL_ID": "100434",
        "TEST_TARGET_TEST_FOLDER": "tests/kernel/common",
        "TEST_TOOLCHAIN": "zephyr",
        "TEST_TOOLCHAIN_KEYS": "",
        "token": "BITBUCKET_BUILD_RUN_PLAN_PLATFORM_QUICK",
    }

    if parameters:
        for key, value in parameters.items():
            default_parameters[str(key)] = value

    return {
        "status": "success",
        "prompt": _render_prompt(jobFullName, default_parameters),
        "request": {
            "jobFullName": jobFullName,
            "parameters": default_parameters,
        },
        "instructions": [
            "Verify TEST_TARGET_SERIES / TEST_TARGET_PULL_ID / TEST_TARGET_COMMIT_HASH / TEST_TARGET_TEST_FOLDER before submitting.",
            "Use TEST_TARGET_SERIES for the platform name; keep TEST_TWISTER_ADDITIONAL_PARAM empty unless extra twister args are truly needed.",
        ],
    }
