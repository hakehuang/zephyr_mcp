#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Get Git Redirect Configuration Status
获取Git重定向配置状态"""

from typing import Dict, Any

from src.utils.common_tools import check_tools, parse_git_config, run_command



def get_git_redirect_status() -> Dict[str, Any]:
    """
    Function Description: Get current Git redirect configuration status
    功能描述: 获取当前Git重定向配置状态
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}

    result = run_command(["git", "config", "--global", "--list"])
    if result["status"] != "success":
        return {
            "status": "error",
            "log": "",
            "error": f"获取Git配置失败: {result['stderr']}",
        }

    config_dict = parse_git_config(result["stdout"])
    zephyr_redirects = []
    for key, value in config_dict.items():
        if key.startswith("url.") and key.endswith(".insteadof"):
            if "zephyr" in key.lower() or "zephyr" in value.lower():
                mirror_url = key[4:].rsplit(".insteadof", 1)[0]
                zephyr_redirects.append(
                    {"mirror_url": mirror_url, "original_url": value}
                )

    return {
        "status": "success",
        "has_redirects": bool(zephyr_redirects),
        "zephyr_redirects": zephyr_redirects,
        "all_config": config_dict,
    }
