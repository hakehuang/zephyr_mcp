#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function Description: Run west update command in Zephyr project directory
功能描述: 在Zephyr项目目录中运行west update命令
"""

from typing import Dict, Any
import os

from src.utils.common_tools import check_tools
from src.utils.internal_helpers import _west_update_internal
from src.utils.logging_utils import get_logger


logger = get_logger(__name__)


def west_update(project_dir: str) -> Dict[str, Any]:
    """
    Function Description: Run west update command in Zephyr project directory
    功能描述: 在Zephyr项目目录中运行west update命令

    Parameters:
    参数说明:
    - project_dir (str): Required. Zephyr project directory
    - project_dir (str): 必须。Zephyr项目目录

    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息

    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    logger.info("[west_update] start project_dir=%s", project_dir)

    # 检查west工具是否安装
    tools_status = check_tools(["west"])
    if not tools_status.get("west", False):
        logger.error("[west_update] west not installed (check_tools=%s)", tools_status)
        return {"status": "error", "log": "", "error": "west工具未安装"}

    # 检查项目目录是否存在
    if not os.path.exists(project_dir):
        logger.error("[west_update] project dir does not exist: %s", project_dir)
        return {"status": "error", "log": "", "error": f"项目目录不存在: {project_dir}"}

    # 检查是否存在west.yml文件
    west_yml_path = os.path.join(project_dir, "west.yml")
    if not os.path.exists(west_yml_path):
        logger.error("[west_update] west.yml missing: %s", west_yml_path)
        return {
            "status": "error",
            "log": "",
            "error": f"west.yml文件不存在，请确认是Zephyr项目: {project_dir}",
        }

    # 调用内部函数执行update
    result = _west_update_internal(project_dir)

    logger.info(
        "[west_update] finished status=%s",
        result.get("status") if isinstance(result, dict) else type(result).__name__,
    )
    return result
