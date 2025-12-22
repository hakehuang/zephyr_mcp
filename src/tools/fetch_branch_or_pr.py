# -*- coding: utf-8 -*-
"""Fetch Branch or Pull Request from Git Repository
从Git仓库获取分支或拉取请求 """

import os
import subprocess

from typing import Dict, Any, Optional

from src.utils.common_tools import check_tools
from src.utils.internal_helpers import _fetch_branch_or_pr_internal


def fetch_branch_or_pr(
    project_dir: str,
    branch_name: Optional[str] = None,
    pr_number: Optional[int] = None,
    remote_name: str = "origin",
) -> Dict[str, Any]:
    """
    Function Description: Fetch a branch or pull request from a Git repository and checkout
    功能描述: 从Git仓库获取分支或拉取请求并检出

    Parameters:
    参数说明:
    - project_dir (str): Required. Project directory
    - project_dir (str): 必须。项目目录
    - branch_name (Optional[str]): Optional. Branch name to fetch
    - branch_name (Optional[str]): 可选。要获取的分支名称
    - pr_number (Optional[int]): Optional. Pull request number to fetch
    - pr_number (Optional[int]): 可选。要获取的拉取请求编号
    - remote_name (str): Optional. Remote name, default is "origin"
    - remote_name (str): 可选。远程仓库名称，默认为"origin"

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

    # Check if project directory exists
    # 检查项目目录是否存在
    if not os.path.exists(project_dir):
        return {"status": "error", "log": "", "error": f"项目目录不存在: {project_dir}"}

    # Check if it's a Git repository
    # 检查是否是Git仓库
    try:
        cmd = ["git", "rev-parse", "--is-inside-work-tree"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        if process.returncode != 0:
            return {
                "status": "error",
                "log": "",
                "error": f"指定目录不是Git仓库: {project_dir}",
            }
    except Exception as e:
        return {"status": "error", "log": "", "error": f"检查Git仓库失败: {str(e)}"}

    # Check if branch name or PR number is provided
    # 检查是否提供了分支名或PR号
    if branch_name is None and pr_number is None:
        return {
            "status": "error",
            "log": "",
            "error": "必须提供branch_name或pr_number参数",
        }

    # Call internal function to execute fetch operation
    # 调用内部函数执行获取操作
    return _fetch_branch_or_pr_internal(
        project_dir, branch_name, pr_number, remote_name
    )
