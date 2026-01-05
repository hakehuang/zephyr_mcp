#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" 
Function Description: NXP downstream workspace setup helper
功能描述: NXP downstream 工作区初始化辅助工具

This tool automates the following workflow (as requested):
1) git config --global url.ssh://git@bitbucket.sw.nxp.com/mcucore/bifrost.git.insteadOf https://github.com/nxp-zephyr/bifrost
2) west init -m ssh://git@bitbucket.sw.nxp.com/mcucore/nxp-zsdk.git
3) west update bifrost
4) python bifrost/scripts/init_env.py
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict

from src.utils.common_tools import check_tools, format_error_message, run_command
from src.utils.logging_utils import get_logger, print_to_logger


logger = get_logger(__name__)


DEFAULT_BIFROST_FROM_URL = "https://github.com/nxp-zephyr/bifrost"
DEFAULT_BIFROST_TO_URL = "ssh://git@bitbucket.sw.nxp.com/mcucore/bifrost.git"
DEFAULT_MANIFEST_URL = "ssh://git@bitbucket.sw.nxp.com/mcucore/nxp-zsdk.git"


def nxp_downstream_setup(
    project_dir: str,
    manifest_url: str = DEFAULT_MANIFEST_URL,
    bifrost_from_url: str = DEFAULT_BIFROST_FROM_URL,
    bifrost_to_url: str = DEFAULT_BIFROST_TO_URL,
    force_west_init: bool = False,
    run_init_env: bool = True,
) -> Dict[str, Any]:
    """
    Function Description: NXP downstream workspace setup helper
    功能描述: NXP downstream 工作区初始化辅助工具

    Parameters:
    参数说明:
    - project_dir (str): Required. Directory to init/update the west workspace
    - project_dir (str): 必须。用于初始化/更新west工作区的目录
    - manifest_url (str): Optional. West manifest repository URL (used by west init -m)
    - manifest_url (str): 可选。West manifest仓库地址（用于 west init -m）
    - bifrost_from_url (str): Optional. The HTTPS URL to redirect from
    - bifrost_from_url (str): 可选。需要被重定向的HTTPS地址
    - bifrost_to_url (str): Optional. The SSH URL to redirect to
    - bifrost_to_url (str): 可选。要重定向到的SSH地址
    - force_west_init (bool): Optional. If True, runs west init even if .west exists
    - force_west_init (bool): 可选。如果为True，即使存在.west也会执行west init
    - run_init_env (bool): Optional. If True, runs bifrost/scripts/init_env.py after west update
    - run_init_env (bool): 可选。如果为True，在west update后执行bifrost/scripts/init_env.py

    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息
    """

    logger.info(
        "[nxp_downstream_setup] start project_dir=%s manifest_url=%s force_west_init=%s run_init_env=%s",
        project_dir,
        manifest_url,
        force_west_init,
        run_init_env,
    )

    log: list[str] = []

    def _dbg(message: str) -> None:
        log.append(message)
        print_to_logger(logger, message)

    if not project_dir:
        return {"status": "error", "log": log, "error": "project_dir is required"}

    # Ensure tools exist.
    tools_status = check_tools(["git", "west"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": log, "error": "git工具未安装"}
    if not tools_status.get("west", False):
        return {"status": "error", "log": log, "error": "west工具未安装"}

    project_dir = os.path.abspath(project_dir)
    os.makedirs(project_dir, exist_ok=True)
    logger.info(f"Using workspace directory: {project_dir}")

    # 1) Configure global git URL rewrite for bifrost.
    _dbg("Configuring git url.insteadOf for bifrost...")
    git_cfg_key = f"url.{bifrost_to_url}.insteadOf"
    cfg_result = run_command(
        ["git", "config", "--global", git_cfg_key, bifrost_from_url],
        cwd=project_dir,
    )
    if cfg_result.get("status") != "success":
        error_msg = format_error_message("git config", cfg_result.get("stderr", ""))
        return {"status": "error", "log": log + [error_msg], "error": error_msg}
    _dbg(f"Git redirect set: {bifrost_from_url} -> {bifrost_to_url}")

    # 2) west init
    west_dir = os.path.join(project_dir, ".west")
    if os.path.isdir(west_dir) and not force_west_init:
        _dbg(".west already exists; skipping west init (force_west_init=False)")
    else:
        _dbg(f"Running west init -m {manifest_url} ...")
        init_result = run_command(
            ["west", "init", "-m", manifest_url],
            cwd=project_dir,
            retries=3,
            retry_backoff_seconds=2.0,
        )
        if init_result.get("status") != "success":
            error_msg = format_error_message("west init", init_result.get("stderr", ""))
            return {"status": "error", "log": log + [error_msg], "error": error_msg}
        _dbg("west init completed")

    # 3) west update bifrost
    _dbg("Running west update bifrost ...")
    update_result = run_command(
        ["west", "update", "bifrost"],
        cwd=project_dir,
        retries=3,
        retry_backoff_seconds=2.0,
    )
    if update_result.get("status") != "success":
        error_msg = format_error_message("west update bifrost", update_result.get("stderr", ""))
        return {"status": "error", "log": log + [error_msg], "error": error_msg}
    _dbg("west update bifrost completed")

    # 4) python bifrost/scripts/init_env.py
    if run_init_env:
        script_path = os.path.join(project_dir, "bifrost", "scripts", "init_env.py")
        if not os.path.isfile(script_path):
            error_msg = f"init_env.py not found: {script_path}"
            return {"status": "error", "log": log + [error_msg], "error": error_msg}

        _dbg("Running bifrost/scripts/init_env.py ...")
        py_result = run_command(
            [sys.executable, script_path],
            cwd=project_dir,
            retries=0,
        )
        if py_result.get("status") != "success":
            error_msg = format_error_message("init_env.py", py_result.get("stderr", ""))
            return {"status": "error", "log": log + [error_msg], "error": error_msg}
        _dbg("init_env.py completed")

    return {"status": "success", "log": log, "error": None}
