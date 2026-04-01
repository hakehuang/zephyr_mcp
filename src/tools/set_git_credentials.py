#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function Description: Set Git credentials for authentication
功能描述: 设置Git认证凭据
"""

from __future__ import annotations

import os
import subprocess
from typing import Dict, Any

from src.utils.common_tools import check_tools, is_git_repository, run_command
from src.utils.input_validation import (
    ValidationError,
    validate_existing_directory,
    validate_non_empty_text,
)


GIT_CREDENTIAL_HOST = "github.com"



def set_git_credentials(username: str, password: str, project_dir: str = None) -> Dict[str, Any]:
    """
    Function Description: Set Git credentials for authentication
    功能描述: 设置Git认证凭据
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}

    try:
        username = validate_non_empty_text(username, "username", max_length=256)
        password = validate_non_empty_text(password, "password", max_length=512)
        if project_dir is not None:
            project_dir = validate_existing_directory(project_dir, "project_dir")
            if not is_git_repository(project_dir):
                return {
                    "status": "error",
                    "log": "",
                    "error": f"指定目录不是Git仓库: {project_dir}",
                }
    except ValidationError as exc:
        return {"status": "error", "log": "", "error": str(exc)}

    config_scope = "--local" if project_dir is not None else "--global"
    cwd = project_dir if project_dir is not None else None
    helper_candidates = (
        ["manager-core", "manager", "wincred"]
        if os.name == "nt"
        else ["cache", "store"]
    )

    last_error = ""
    selected_helper = None
    for helper in helper_candidates:
        result = run_command(
            ["git", "config", config_scope, "credential.helper", helper],
            cwd=cwd,
        )
        if result["status"] == "success":
            selected_helper = helper
            break
        last_error = result.get("stderr", "") or result.get("stdout", "")

    if selected_helper is None:
        return {
            "status": "error",
            "log": "",
            "error": f"配置凭据助手失败: {last_error or 'unknown error'}",
        }

    approve_input = (
        "protocol=https\n"
        f"host={GIT_CREDENTIAL_HOST}\n"
        f"username={username}\n"
        f"password={password}\n\n"
    )

    try:
        process = subprocess.run(
            ["git", "credential", "approve"],
            cwd=cwd,
            input=approve_input,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"写入Git凭据时发生错误: {str(e)}",
        }

    if process.returncode != 0:
        return {
            "status": "error",
            "log": "",
            "error": f"写入Git凭据失败: {process.stderr.strip() or process.stdout.strip()}",
        }

    scope_text = "项目本地" if project_dir is not None else "全局"
    return {
        "status": "success",
        "log": (
            f"已成功设置{scope_text}Git凭据（credential.helper={selected_helper}, host={GIT_CREDENTIAL_HOST}）"
        ),
        "error": "",
    }
