#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Get Git Redirect Configuration Status
获取Git重定向配置状态"""

import subprocess
from typing import Dict, Any
from src.utils.common_tools import check_tools

import sys
import io

# Reconfigure stdout with new encoding
sys.stdout.reconfigure(encoding='utf-8')

# Or wrap it in a new TextIOWrapper
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_git_redirect_status() -> Dict[str, Any]:
    """
    Function Description: Get current Git redirect configuration status
    功能描述: 获取当前Git重定向配置状态

    Parameters:
    参数说明:
    - No parameters
    - 无参数

    Returns:
    返回值:
    - Dict[str, Any]: Contains redirect configuration status information
    - Dict[str, Any]: 包含重定向配置状态信息

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
        # Get all git global configuration
        # 获取所有的git全局配置
        cmd = ["git", "config", "--global", "--list"]
        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode != 0:
            return {
                "status": "error",
                "log": "",
                "error": f"获取Git配置失败: {process.stderr}",
            }

        # Parse configuration
        # 解析配置
        config_output = process.stdout.strip()
        config_lines = config_output.split("\n") if config_output else []

        # Find zephyr-related redirect configurations
        # 查找与zephyr相关的重定向配置
        zephyr_redirects = []
        for line in config_lines:
            if line.startswith("url.") and ".insteadof" in line:
                parts = line.split("=")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()

                    # Check if it's a zephyr-related redirect
                    # 检查是否是zephyr相关的重定向
                    if "zephyr" in key.lower() or "zephyr" in value.lower():
                        # Extract mirror_url and original_url
                        # 提取mirror_url和original_url
                        mirror_url = key[4:].split(".insteadof")[0]
                        original_url = value

                        zephyr_redirects.append(
                            {"mirror_url": mirror_url, "original_url": original_url}
                        )

        # Check if there are any redirect configurations
        # 检查是否有任何重定向配置
        has_redirects = len(zephyr_redirects) > 0

        return {
            "status": "success",
            "has_redirects": has_redirects,
            "zephyr_redirects": zephyr_redirects,
            "all_config": config_lines,
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"获取Git重定向状态时发生错误: {str(e)}",
        }
