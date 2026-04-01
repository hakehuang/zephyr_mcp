#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Description: Git checkout tool for Zephyr project
文件描述: Zephyr项目的Git checkout工具
"""

from typing import Dict, Any
from src.utils.common_tools import check_tools, is_git_repository
from src.utils.input_validation import (
    ValidationError,
    validate_existing_directory,
    validate_git_ref,
)
from src.utils.internal_helpers import _git_checkout_internal


def git_checkout(project_dir: str, ref: str) -> Dict[str, Any]:
    """
    Function Description: Switch to specified Git reference (SHA, tag or branch) in Zephyr project directory
    功能描述: 在Zephyr项目目录中切换到指定的Git引用（SHA号、tag或分支）

    Parameters:
    参数说明:
    - project_dir (str): Required. Zephyr project directory
    - project_dir (str): 必须。Zephyr项目目录
    - ref (str): Required. Git reference (SHA, tag or branch name)
    - ref (str): 必须。Git引用（SHA号、tag或分支名称）

    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息

    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    # Check if git tool is installed
    # 检查git工具是否安装
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}

    try:
        project_dir = validate_existing_directory(project_dir, "project_dir")
        ref = validate_git_ref(ref, "ref")
    except ValidationError as exc:
        return {"status": "error", "log": "", "error": str(exc)}

    # Check if it's a Git repository
    # 检查是否是Git仓库
    if not is_git_repository(project_dir):
        return {
            "status": "error",
            "log": "",
            "error": f"指定目录不是Git仓库: {project_dir}",
        }

    # Call internal function to execute checkout
    # 调用内部函数执行checkout
    return _git_checkout_internal(project_dir, ref)
