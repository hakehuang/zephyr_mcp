#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Get Git Configuration Status
获取Git配置状态 """

from typing import Dict, Any

from src.utils.common_tools import check_tools, parse_git_config, is_git_repository
from src.utils.input_validation import ValidationError, validate_existing_directory



def get_git_config_status(project_dir: str = None) -> Dict[str, Any]:
    """
    Function Description: Get current Git configuration status
    功能描述: 获取当前Git配置状态
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}

    try:
        if project_dir is not None:
            project_dir = validate_existing_directory(project_dir, "project_dir")
            if not is_git_repository(project_dir):
                return {
                    "status": "error",
                    "log": "",
                    "error": f"指定目录不是Git仓库: {project_dir}",
                }

            scope = "--local"
            cwd = project_dir
            config_type = "local"
        else:
            scope = "--global"
            cwd = None
            config_type = "global"
    except ValidationError as exc:
        return {"status": "error", "log": "", "error": str(exc)}

    from src.utils.common_tools import run_command

    result = run_command(["git", "config", scope, "--list"], cwd=cwd)
    if result["status"] != "success":
        return {
            "status": "error",
            "log": "",
            "error": f"获取Git配置失败: {result['stderr']}",
        }

    config_dict = parse_git_config(result["stdout"])
    user_name = config_dict.get("user.name", "未设置")
    user_email = config_dict.get("user.email", "未设置")
    credential_helper = config_dict.get("credential.helper", "未设置")

    redirect_configs = []
    for key, value in config_dict.items():
        if key.startswith("url.") and key.endswith(".insteadof"):
            mirror_url = key[4:].rsplit(".insteadof", 1)[0]
            redirect_configs.append(
                {"mirror_url": mirror_url, "original_url": value}
            )

    return {
        "status": "success",
        "config_type": config_type,
        "user_name": user_name,
        "user_email": user_email,
        "credential_helper": credential_helper,
        "redirect_configs": redirect_configs,
        "all_config": config_dict,
    }
