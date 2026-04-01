# -*- coding: utf-8 -*-
"""Fetch Branch or Pull Request from Git Repository
从Git仓库获取分支或拉取请求 """

from typing import Dict, Any, Optional

from src.utils.common_tools import check_tools, is_git_repository
from src.utils.input_validation import (
    ValidationError,
    validate_existing_directory,
    validate_git_remote_name,
    validate_non_empty_text,
    validate_positive_int,
)
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
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}

    try:
        project_dir = validate_existing_directory(project_dir, "project_dir")
        remote_name = validate_git_remote_name(remote_name, "remote_name")
        if branch_name is not None:
            branch_name = validate_non_empty_text(
                branch_name,
                "branch_name",
                max_length=256,
            )
        if pr_number is not None:
            pr_number = validate_positive_int(pr_number, "pr_number")
    except ValidationError as exc:
        return {"status": "error", "log": "", "error": str(exc)}

    if branch_name is None and pr_number is None:
        return {
            "status": "error",
            "log": "",
            "error": "必须提供branch_name或pr_number参数",
        }

    if not is_git_repository(project_dir):
        return {
            "status": "error",
            "log": "",
            "error": f"指定目录不是Git仓库: {project_dir}",
        }

    return _fetch_branch_or_pr_internal(project_dir, branch_name, pr_number, remote_name)
