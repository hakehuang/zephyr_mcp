#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Description: Git rebase tool for Zephyr project
文件描述: Zephyr项目的Git rebase工具
"""

import os
import subprocess
from typing import Dict, Any, Optional, List

from src.utils.common_tools import check_tools
from src.utils.internal_helpers import _git_rebase_internal


def _run_git_cmd(project_dir: str, args: List[str]) -> subprocess.CompletedProcess:
    """Run a git command in `project_dir` and return the CompletedProcess."""
    return subprocess.run(["git", *args], cwd=project_dir, capture_output=True, text=True)


def _error(msg: str) -> Dict[str, Any]:
    return {"status": "error", "log": "", "error": msg}


def _check_git_installed() -> Optional[Dict[str, Any]]:
    """Return an error response dict if git is not available, else None."""
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return _error("git工具未安装")
    return None


def _check_project_dir_exists(project_dir: str) -> Optional[Dict[str, Any]]:
    """Return an error response dict if directory does not exist, else None."""
    if not os.path.exists(project_dir):
        return _error(f"项目目录不存在: {project_dir}")
    return None


def _check_is_git_repo(project_dir: str) -> Optional[Dict[str, Any]]:
    """Return an error response dict if directory is not a git repo, else None."""
    try:
        process = _run_git_cmd(project_dir, ["rev-parse", "--is-inside-work-tree"])
        if process.returncode != 0:
            return _error(f"指定目录不是Git仓库: {project_dir}")
    except Exception as e:
        return _error(f"检查Git仓库失败: {str(e)}")
    return None


def _get_current_branch(project_dir: str) -> Dict[str, Any]:
    """Return {status, branch, error}."""
    try:
        process = _run_git_cmd(project_dir, ["rev-parse", "--abbrev-ref", "HEAD"])
        if process.returncode != 0:
            return {
                "status": "error",
                "branch": None,
                "error": process.stderr.strip() or process.stdout.strip(),
            }
        return {"status": "success", "branch": process.stdout.strip(), "error": None}
    except Exception as e:
        return {"status": "error", "branch": None, "error": str(e)}


def _verify_git_ref_exists(project_dir: str, ref: str) -> Optional[Dict[str, Any]]:
    """Verify a git ref exists.

    Accepts branches, tags, and commit SHAs.
    """
    # `rev-parse --verify <name>^{commit}` accepts:
    # - branch names
    # - tags
    # - full/short commit SHAs
    # We also try common remote/refs prefixes for convenience.
    candidates = [
        ref,
        f"{ref}^{{commit}}",
        f"refs/heads/{ref}",
        f"refs/heads/{ref}^{{commit}}",
        f"refs/tags/{ref}",
        f"refs/tags/{ref}^{{commit}}",
        f"origin/{ref}",
        f"origin/{ref}^{{commit}}",
        f"refs/remotes/origin/{ref}",
        f"refs/remotes/origin/{ref}^{{commit}}",
    ]

    for cand in candidates:
        try:
            process = _run_git_cmd(project_dir, ["rev-parse", "--verify", "--quiet", cand])
            if process.returncode == 0:
                return None
        except Exception:
            continue

    return _error(f"Git引用不存在(分支/标签/SHA): {ref}")


def git_rebase(
    project_dir: str,
    source_branch: str,
    onto_branch: Optional[str] = None,
    interactive: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Function Description: Execute Git rebase operation
    功能描述: 执行Git rebase操作

    Parameters:
    参数说明:
    - project_dir (str): Required. Project directory
    - project_dir (str): 必须。项目目录
    - source_branch (str): Required. Git reference to rebase onto (branch/tag/SHA)
    - source_branch (str): 必须。要rebase到的Git引用（分支/标签/SHA）
    - onto_branch (Optional[str]): Optional. "--onto" target (branch/tag/SHA). If None, rebases current branch onto source_branch
    - onto_branch (Optional[str]): 可选。"--onto" 目标（分支/标签/SHA）。如果为None，则将当前分支rebase到source_branch上
    - interactive (bool): Optional. Whether to perform interactive rebase. Default: False
    - interactive (bool): 可选。是否执行交互式rebase。默认：False
    - force (bool): Optional. Whether to force rebase without confirmation. Default: False
    - force (bool): 可选。是否强制rebase而不进行确认。默认：False

    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息

    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    err = _check_git_installed()
    if err:
        return err

    err = _check_project_dir_exists(project_dir)
    if err:
        return err

    err = _check_is_git_repo(project_dir)
    if err:
        return err

    # Get current branch (kept for parity/diagnostics)
    # 获取当前分支（用于诊断/保持旧行为一致）
    current_branch_result = _get_current_branch(project_dir)
    if current_branch_result["status"] != "success":
        return _error(f"获取当前分支失败: {current_branch_result['error']}")
    _ = current_branch_result["branch"]

    # Validate refs (branch/tag/SHA)
    err = _verify_git_ref_exists(project_dir, source_branch)
    if err:
        return err

    if onto_branch:
        err = _verify_git_ref_exists(project_dir, onto_branch)
        if err:
            return err

    # Call internal function to execute rebase
    # 调用内部函数执行rebase
    return _git_rebase_internal(
        project_dir, source_branch, onto_branch, interactive, force
    )
