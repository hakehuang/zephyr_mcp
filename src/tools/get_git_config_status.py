#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Get Git Configuration Status
获取Git配置状态 """

import os
import subprocess

from typing import Dict, Any

from src.utils.common_tools import check_tools


def get_git_config_status(project_dir: str = None) -> Dict[str, Any]:
    """
    Function Description: Get current Git configuration status
    功能描述: 获取当前Git配置状态

    Parameters:
    参数说明:
    - project_dir (Optional[str]): Optional. Project directory to check local configuration
    - project_dir (Optional[str]): 可选。项目目录，用于检查本地配置

    Returns:
    返回值:
    - Dict[str, Any]: Contains Git configuration information
    - Dict[str, Any]: 包含Git配置信息

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

    # Check project directory (if specified)
    # 检查项目目录（如果指定了）
    if project_dir is not None and not os.path.exists(project_dir):
        return {"status": "error", "log": "", "error": f"项目目录不存在: {project_dir}"}

    try:
        # Determine whether to read local or global configuration
        # 确定是读取本地配置还是全局配置
        if project_dir is not None:
            # Check if it's a Git repository
            # 检查是否是Git仓库
            cmd = ["git", "rev-parse", "--is-inside-work-tree"]
            process = subprocess.run(
                cmd, cwd=project_dir, capture_output=True, text=True
            )
            if process.returncode != 0:
                return {
                    "status": "error",
                    "log": "",
                    "error": f"指定目录不是Git仓库: {project_dir}",
                }

            # Read local configuration
            # 读取本地配置
            cmd = ["git", "config", "--local", "--list"]
            cwd = project_dir
            config_type = "local"
        else:
            # Read global configuration
            # 读取全局配置
            cmd = ["git", "config", "--global", "--list"]
            cwd = None
            config_type = "global"

        # Execute command to get configuration
        # 执行命令获取配置
        process = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

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

        # Build configuration dictionary
        # 构建配置字典
        config_dict = {}
        for line in config_lines:
            if "=" in line:
                key, value = line.split("=", 1)
                config_dict[key.strip()] = value.strip()

        # Extract useful configuration information
        # 提取有用的配置信息
        user_name = config_dict.get("user.name", "未设置")
        user_email = config_dict.get("user.email", "未设置")
        credential_helper = config_dict.get("credential.helper", "未设置")

        # Find all url.*.insteadof configurations (redirect related)
        # 查找所有的url.*.insteadof配置（重定向相关）
        redirect_configs = []
        for key, value in config_dict.items():
            if key.startswith("url.") and key.endswith(".insteadof"):
                mirror_url = key[4:].rsplit(".insteadof", 1)[0]
                original_url = value
                redirect_configs.append(
                    {"mirror_url": mirror_url, "original_url": original_url}
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
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"获取Git配置状态时发生错误: {str(e)}",
        }
