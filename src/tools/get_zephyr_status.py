#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Description: Get Zephyr project Git status information
文件描述: 获取Zephyr项目的Git状态信息
"""

from typing import Dict, Any
import os
import subprocess
from src.utils.common_tools import check_tools
from src.utils.logging_utils import get_logger


def _is_git_repo(path: str) -> bool:
    try:
        process = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
        )
        return process.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _resolve_git_dir(project_dir: str) -> tuple[str | None, list[str]]:
    """Return (git_dir, tried_dirs).

    Zephyr "west" workspaces often are not Git repos at the workspace root.
    Common Git repos are:
    - <workspace>/zephyr
    - <workspace>/.west/manifest
    """

    tried: list[str] = []
    candidates = [
        project_dir,
        os.path.join(project_dir, "zephyr"),
        os.path.join(project_dir, ".west", "manifest"),
    ]

    for candidate in candidates:
        tried.append(candidate)
        if os.path.isdir(candidate) and _is_git_repo(candidate):
            return candidate, tried

    return None, tried


def get_zephyr_status(project_dir: str) -> Dict[str, Any]:
    """
    Function Description: Get Git status information of Zephyr project
    功能描述: 获取Zephyr项目的Git状态信息

    Parameters:
    参数说明:
    - project_dir (str): Required. Zephyr project directory
    - project_dir (str): 必须。Zephyr项目目录

    Returns:
    返回值:
    - Dict[str, Any]: Contains status, current branch, commit information, etc.
    - Dict[str, Any]: 包含状态、当前分支、提交信息等

    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    logger = get_logger(__name__)

    # Check if git tool is installed
    # 检查git工具是否安装
    logger.info("Checking git tool installation...")
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        logger.error("git tool not installed")
        return {"status": "error", "log": "", "error": "git工具未安装"}

    # Check if project directory exists
    # 检查项目目录是否存在
    if not os.path.exists(project_dir):
        logger.error("Project directory does not exist: %s", project_dir)
        return {"status": "error", "log": "", "error": f"项目目录不存在: {project_dir}"}

    # Resolve which directory to treat as the Git repo.
    # For west workspaces, the root may not be a Git repo.
    git_dir, tried_dirs = _resolve_git_dir(project_dir)
    if not git_dir:
        logger.error(
            "Not a git repo (including common west locations). project_dir=%s tried=%s",
            project_dir,
            tried_dirs,
        )
        return {
            "status": "error",
            "log": "",
            "error": "指定目录不是Git仓库（也未找到west常见Git目录）: "
            + project_dir
            + "。已尝试: "
            + ", ".join(tried_dirs),
        }

    # Get current branch
    # 获取当前分支
    try:
        cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        process = subprocess.run(
            cmd,
            cwd=git_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        current_branch = process.stdout.strip()
    except (OSError, subprocess.SubprocessError) as e:
        logger.exception("Failed to get current branch")
        return {"status": "error", "log": "", "error": f"获取当前分支失败: {str(e)}"}

    # Get recent commit information (latest 5)
    # 获取最近的提交信息（最近5条）
    try:
        # Use ASCII unit/record separators to make parsing robust.
        # Each record: hash<US>author<US>email<US>date<US>subject<RS>
        cmd = [
            "git",
            "log",
            "-5",
            "--date=iso-strict",
            "--pretty=format:%H%x1f%an%x1f%ae%x1f%ad%x1f%s%x1e",
        ]
        process = subprocess.run(
            cmd,
            cwd=git_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        recent_commits: list[dict[str, str]] = []
        raw = process.stdout or ""
        for record in raw.split("\x1e"):
            record = record.strip()
            if not record:
                continue
            parts = record.split("\x1f")
            if len(parts) < 5:
                continue
            recent_commits.append(
                {
                    "commit_hash": parts[0],
                    "author_name": parts[1],
                    "author_email": parts[2],
                    "commit_date": parts[3],
                    "commit_message": parts[4],
                }
            )

        # Backward-compatible top-level fields reflect the latest commit.
        if recent_commits:
            commit_hash = recent_commits[0].get("commit_hash", "")
            author_name = recent_commits[0].get("author_name", "")
            author_email = recent_commits[0].get("author_email", "")
            commit_date = recent_commits[0].get("commit_date", "")
            commit_message = recent_commits[0].get("commit_message", "")
        else:
            commit_hash = author_name = author_email = commit_date = commit_message = ""
    except (OSError, subprocess.SubprocessError) as e:
        logger.exception("Failed to get recent commits")
        return {"status": "error", "log": "", "error": f"获取提交信息失败: {str(e)}"}

    # Get Git status
    # 获取Git状态
    try:
        cmd = ["git", "status"]
        process = subprocess.run(
            cmd,
            cwd=git_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        git_status = process.stdout.strip()
    except (OSError, subprocess.SubprocessError) as e:
        logger.exception("Failed to get git status")
        return {"status": "error", "log": "", "error": f"获取Git状态失败: {str(e)}"}

    return {
        "status": "success",
        "current_branch": current_branch,
        "commit_hash": commit_hash,
        "author_name": author_name,
        "author_email": author_email,
        "commit_date": commit_date,
        "commit_message": commit_message,
        "recent_commits": recent_commits,
        "git_status": git_status,
    }
