#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Description: Git redirect tool for Zephyr project mirror
文件描述: Zephyr项目镜像的Git重定向工具
"""

import io
import sys
import subprocess
from typing import Dict, Any

from src.utils.common_tools import check_tools

# Reconfigure stdout with new encoding
sys.stdout.reconfigure(encoding='utf-8')


def git_redirect_zephyr_mirror(
    enable: bool = True, mirror_url: str = None
) -> Dict[str, Any]:
    """
    Function Description: Configure Git global redirect to redirect GitHub Zephyr repository to specified mirror
    功能描述: 配置Git全局重定向，将GitHub的Zephyr仓库地址重定向到指定的镜像源

    Parameters:
    参数说明:
    - enable (bool): Optional. Whether to enable redirect, default is True (enabled)
    - enable (bool): 可选。是否启用重定向，默认为True（启用）
    - mirror_url (Optional[str]): Optional. Mirror URL, defaults to domestic mirror
    - mirror_url (Optional[str]): 可选。镜像源地址，默认为国内镜像源

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

    # If no mirror URL is specified, use the default domestic mirror
    # 如果未指定镜像源，使用默认的国内镜像源
    if mirror_url is None:
        mirror_url = (
            "https://mirror.tuna.tsinghua.edu.cn/git/zephyrproject-rtos/zephyr.git"
        )

    try:
        if enable:
            # Set up redirect
            # 设置重定向
            cmd = [
                "git",
                "config",
                "--global",
                "url." + mirror_url + ".insteadOf",
                "https://github.com/zephyrproject-rtos/zephyr.git",
            ]
            process = subprocess.run(cmd, capture_output=True, text=True)

            if process.returncode == 0:
                return {
                    "status": "success",
                    "log": f"已成功启用GitHub Zephyr仓库重定向到: {mirror_url}",
                    "error": "",
                }
            else:
                return {
                    "status": "error",
                    "log": "",
                    "error": f"启用重定向失败: {process.stderr}",
                }
        else:
            # Remove redirect
            # 移除重定向
            cmd = [
                "git",
                "config",
                "--global",
                "--unset",
                "url." + mirror_url + ".insteadOf",
            ]
            process = subprocess.run(cmd, capture_output=True, text=True)

            # If it fails, it might be because the configuration doesn't exist, which is normal
            # 如果失败，可能是因为配置不存在，这是正常的
            if process.returncode != 0 and "No such key" in process.stderr:
                return {
                    "status": "success",
                    "log": "重定向配置不存在，无需移除",
                    "error": "",
                }
            elif process.returncode == 0:
                return {
                    "status": "success",
                    "log": f"已成功移除GitHub Zephyr仓库重定向: {mirror_url}",
                    "error": "",
                }
            else:
                return {
                    "status": "error",
                    "log": "",
                    "error": f"移除重定向失败: {process.stderr}",
                }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"配置Git重定向时发生错误: {str(e)}",
        }
