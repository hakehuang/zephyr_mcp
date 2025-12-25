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


_DEFAULT_PROMPT = """trigger_build
{
	\"jobFullName\": \"zephyr_test_pipe_quick\"
\"parameters\"  = {'TEST_TARGET_SERIES': \"mimxrt1170_evk@A/mimxrt1176/cm4\",
	'TEST_NOTIFIER': \"hake.huang@nxp.com\",
	'TEST_TWISTER_ADDITIONAL_PARAM': \"\",
	'TEST_TWISTER_SYSBUILD': \"\",
	'TEST_HWV2' : 'Y',
	'TEST_TARGET_BRANCH': \"main\",
	'TEST_TARGET_REPO': \" https://github.com/zephyrproject-rtos/zephyr.git\",
	'TEST_TARGET_COMMIT_HASH': \"\",
	'TEST_TARGET_PULL_ID': '100434',
	'TEST_TARGET_TEST_FOLDER': 'tests/kernel/common',
	'TEST_TOOLCHAIN': \"zephyr\",
	'TEST_TOOLCHAIN_KEYS': '',
'token': 'BITBUCKET_BUILD_RUN_PLAN_PLATFORM_QUICK'}
}
"""


def trigger_remote_test(
    jobFullName: str = "zephyr_test_pipe_quick",
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a remote test trigger prompt template.

    Function Description:
    - Generates a prompt in the requested `trigger_build { ... }` format.
    - Returns both the raw prompt text and a structured representation.

    Parameters:
    - jobFullName (str): Remote job full name. Default: "zephyr_test_pipe_quick".
    - parameters (Optional[Dict[str, Any]]): Optional parameter overrides (structured output only).
      Note: The `prompt` field is a fixed template string so users can edit it manually.

    Returns:
    - Dict[str, Any]:
        - status: "success"
        - prompt: The template text to paste/edit
        - request: A machine-readable request object (jobFullName + parameters)
        - instructions: Short instructions asking user to update content
    """

    logger.info("[trigger_remote_test] Generating remote test trigger prompt")

    default_parameters: Dict[str, Any] = {
        "TEST_TARGET_SERIES": "mimxrt1170_evk@A/mimxrt1176/cm4",
        "TEST_NOTIFIER": "hake.huang@nxp.com",
        "TEST_TWISTER_ADDITIONAL_PARAM": "",
        "TEST_TWISTER_SYSBUILD": "",
        "TEST_HWV2": "Y",
        "TEST_TARGET_BRANCH": "main",
        # Keep the exact user-provided leading space in the prompt template;
        # for the structured request we normalize it.
        "TEST_TARGET_REPO": "https://github.com/zephyrproject-rtos/zephyr.git",
        "TEST_TARGET_COMMIT_HASH": "",
        # Keep the exact user-provided trailing space in the prompt template;
        # for the structured request we normalize it.
        "TEST_TARGET_PULL_ID": "100434",
        "TEST_TARGET_TEST_FOLDER": "tests/kernel/common",
        "TEST_TOOLCHAIN": "zephyr",
        "TEST_TOOLCHAIN_KEYS": "",
        "token": "BITBUCKET_BUILD_RUN_PLAN_PLATFORM_QUICK",
    }

    if parameters:
        for k, v in parameters.items():
            default_parameters[str(k)] = v

    return {
        "status": "success",
        "prompt": _DEFAULT_PROMPT.replace("zephyr_test_pipe_quick", jobFullName, 1)
        if jobFullName != "zephyr_test_pipe_quick"
        else _DEFAULT_PROMPT,
        "request": {
            "jobFullName": jobFullName,
            "parameters": default_parameters,
        },
        "instructions": [
            "Update the fields inside the prompt before submitting.",
            "Common fields to update: TEST_TARGET_PULL_ID / TEST_TARGET_COMMIT_HASH / TEST_TARGET_TEST_FOLDER / TEST_NOTIFIER.",
            "Note: the provided template includes a leading space in TEST_TARGET_REPO and a trailing space in TEST_TARGET_PULL_ID; remove them if they are not intended.",
        ],
    }
