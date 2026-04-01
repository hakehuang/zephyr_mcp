#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Description: Git redirect tool for Zephyr project mirror
文件描述: Zephyr项目镜像的Git重定向工具
"""

from typing import Dict, Any

from src.utils.common_tools import check_tools, run_command
from src.utils.input_validation import ValidationError, validate_repo_url

DEFAULT_MIRROR_URL = (
    "https://mirror.tuna.tsinghua.edu.cn/git/zephyrproject-rtos/zephyr.git"
)
DEFAULT_ORIGINAL_URL = "https://github.com/zephyrproject-rtos/zephyr.git"



def git_redirect_zephyr_mirror(
    enable: bool = True, mirror_url: str = None
) -> Dict[str, Any]:
    """
    Function Description: Configure Git global redirect to redirect GitHub Zephyr repository to specified mirror
    功能描述: 配置Git全局重定向，将GitHub的Zephyr仓库地址重定向到指定的镜像源
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}

    try:
        mirror_url = validate_repo_url(mirror_url or DEFAULT_MIRROR_URL, "mirror_url")
    except ValidationError as exc:
        return {"status": "error", "log": "", "error": str(exc)}

    if enable:
        cmd = [
            "git",
            "config",
            "--global",
            f"url.{mirror_url}.insteadOf",
            DEFAULT_ORIGINAL_URL,
        ]
        result = run_command(cmd)
        if result["status"] == "success":
            return {
                "status": "success",
                "log": f"已成功启用GitHub Zephyr仓库重定向到: {mirror_url}",
                "error": "",
            }
        return {
            "status": "error",
            "log": "",
            "error": f"启用重定向失败: {result['stderr']}",
        }

    cmd = ["git", "config", "--global", "--unset", f"url.{mirror_url}.insteadOf"]
    result = run_command(cmd)
    stderr = result.get("stderr", "") or ""
    if result["status"] == "success" or "No such key" in stderr:
        return {
            "status": "success",
            "log": (
                "重定向配置不存在，无需移除"
                if "No such key" in stderr and result["status"] != "success"
                else f"已成功移除GitHub Zephyr仓库重定向: {mirror_url}"
            ),
            "error": "",
        }

    return {
        "status": "error",
        "log": "",
        "error": f"移除重定向失败: {stderr}",
    }
