#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internal helper functions for Git and West operations
Git和West操作的内部辅助函数
"""

from typing import Dict, Any, Optional
import os

from src.utils.common_tools import run_command, format_error_message, is_git_repository


def _git_checkout_internal(project_dir: str, ref: str) -> Dict[str, Any]:
    """
    Internal function: Execute Git checkout operation
    内部函数：执行Git checkout操作

    Args:
        project_dir (str): Project directory path
        project_dir (str): 项目目录路径
        ref (str): Git reference (branch, tag or commit SHA)
        ref (str): Git引用（分支、标签或提交SHA）

    Returns:
        Dict[str, Any]: Dictionary containing execution status, logs and error information
        Dict[str, Any]: 包含执行状态、日志和错误信息的字典
    """
    # Check if it's a Git repository
    # Check if it's a Git repository
    # 检查是否是Git仓库
    if not is_git_repository(project_dir):
        return {"status": "error", "log": [], "error": "指定目录不是有效的Git仓库"}

    # Check if directory exists
    # Check if directory exists
    # 检查目录是否存在
    if not os.path.isdir(project_dir):
        return {"status": "error", "log": [], "error": f"目录不存在: {project_dir}"}

    log = []

    # Get current status for potential recovery
    # Get current status for potential recovery
    # 获取当前状态，以便在失败时恢复
    get_status_result = run_command(["git", "status", "--porcelain"], cwd=project_dir)
    if get_status_result["status"] != "success":
        return {
            "status": "error",
            "log": log + [f"获取Git状态失败: {get_status_result['stderr']}"],
            "error": "无法获取当前Git状态",
        }

    has_uncommitted_changes = len(get_status_result["stdout"].strip()) > 0
    if has_uncommitted_changes:
        log.append("警告: 当前有未提交的更改，切换分支可能会导致冲突")

    # Try to checkout
    # Try to checkout
    # 尝试checkout
    log.append(f"正在切换到: {ref}")
    checkout_result = run_command(["git", "checkout", ref], cwd=project_dir)

    if checkout_result["status"] != "success":
        error_msg = format_error_message("Git checkout", checkout_result["stderr"])
        return {"status": "error", "log": log + [error_msg], "error": error_msg}

    log.append("Git checkout 成功完成")
    return {"status": "success", "log": log, "error": None}


def _west_update_internal(project_dir: str) -> Dict[str, Any]:
    """
    Internal function: Execute west update operation
    内部函数：执行west update操作

    Args:
        project_dir (str): Project directory path
        project_dir (str): 项目目录路径

    Returns:
        Dict[str, Any]: Dictionary containing execution status, logs and error information
        Dict[str, Any]: 包含执行状态、日志和错误信息的字典
    """
    # 检查目录是否存在
    if not os.path.isdir(project_dir):
        return {"status": "error", "log": [], "error": f"目录不存在: {project_dir}"}

    log = []

    # Check if west tool is available
    # Check if west tool is available
    # 检查west工具是否可用
    log.append("检查west工具是否可用...")
    west_check_result = run_command(["west", "--version"], cwd=project_dir)
    if west_check_result["status"] != "success":
        return {
            "status": "error",
            "log": log + ["错误: 找不到west工具或无法执行"],
            "error": "west工具不可用",
        }

    # Execute west update
    # 执行west update
    log.append("开始执行west update...")
    update_result = run_command(["west", "update"], cwd=project_dir)

    if update_result["status"] != "success":
        error_msg = format_error_message("west update", update_result["stderr"])
        return {"status": "error", "log": log + [error_msg], "error": error_msg}

    log.append("west update 成功完成")
    return {"status": "success", "log": log, "error": None}


def _switch_zephyr_version_internal(project_dir: str, ref: str) -> Dict[str, Any]:
    """
    Internal function: Switch Zephyr version and execute west update
    内部函数：切换Zephyr版本并执行west update

    Args:
        project_dir (str): Project directory path
        project_dir (str): 项目目录路径
        ref (str): Git reference (SHA, tag or branch name)
        ref (str): Git引用（SHA、标签或分支名称）

    Returns:
        Dict[str, Any]: Dictionary containing execution status, logs and error information
        Dict[str, Any]: 包含执行状态、日志和错误信息的字典
    """
    log = []

    # Execute Git checkout
    # Execute Git checkout
    # 执行Git checkout
    log.append(f"切换Zephyr版本到: {ref}")
    checkout_result = _git_checkout_internal(project_dir, ref)

    if checkout_result["status"] != "success":
        return {
            "status": "error",
            "log": log + checkout_result["log"],
            "error": checkout_result["error"],
        }

    log.extend(checkout_result["log"])

    # 执行west update
    update_result = _west_update_internal(project_dir)

    if update_result["status"] != "success":
        return {
            "status": "error",
            "log": log + update_result["log"],
            "error": update_result["error"],
        }

    log.extend(update_result["log"])
    log.append(f"Zephyr版本成功切换到: {ref}")

    return {"status": "success", "log": log, "error": None}


def _fetch_branch_or_pr_internal(
    project_dir: str,
    branch_name: Optional[str],
    pr_number: Optional[int],
    remote_name: str,
) -> Dict[str, Any]:
    """
    Internal function: Fetch branch or pull request and checkout
    内部函数：获取分支或拉取请求并检出

    Args:
        project_dir (str): Project directory path
        project_dir (str): 项目目录路径
        branch_name (Optional[str]): Branch name
        branch_name (Optional[str]): 分支名称
        pr_number (Optional[int]): Pull request number
        pr_number (Optional[int]): 拉取请求编号
        remote_name (str): Remote repository name
        remote_name (str): 远程仓库名称

    Returns:
        Dict[str, Any]: Dictionary containing execution status, logs and error information
        Dict[str, Any]: 包含执行状态、日志和错误信息的字典
    """
    # 检查是否是Git仓库
    if not is_git_repository(project_dir):
        return {"status": "error", "log": [], "error": "指定目录不是有效的Git仓库"}

    log = []

    # Get remote URL
    # Get remote URL
    # 获取远程URL
    remote_cmd = ["git", "remote", "get-url", remote_name]
    remote_result = run_command(remote_cmd, cwd=project_dir)

    if remote_result["status"] != "success":
        return {
            "status": "error",
            "log": log + [f"无法获取远程仓库URL: {remote_result['stderr']}"],
            "error": f"远程仓库 {remote_name} 不存在或无法访问",
        }

    remote_url = remote_result["stdout"].strip()
    log.append(f"使用远程仓库: {remote_name} ({remote_url})")

    # Determine whether to fetch branch or PR
    # 确定是获取分支还是PR
    if pr_number is not None:
        # Fetch PR
        # 获取PR
        pr_ref = f"refs/pull/{pr_number}/head"
        local_branch = f"pr-{pr_number}"
        log.append(f"正在获取PR #{pr_number} 到本地分支 {local_branch}")

        # First try to fetch PR directly
        # 首先尝试直接fetch PR
        fetch_cmd = ["git", "fetch", remote_name, f"{pr_ref}:{local_branch}"]
        fetch_result = run_command(fetch_cmd, cwd=project_dir)

        if fetch_result["status"] != "success":
            error_msg = format_error_message("获取PR", fetch_result["stderr"])
            return {"status": "error", "log": log + [error_msg], "error": error_msg}

        # Checkout PR branch
        # 检出PR分支
        checkout_cmd = ["git", "checkout", local_branch]
        checkout_result = run_command(checkout_cmd, cwd=project_dir)

        if checkout_result["status"] != "success":
            error_msg = format_error_message("检出PR分支", checkout_result["stderr"])
            return {"status": "error", "log": log + [error_msg], "error": error_msg}

        log.append(f"成功获取并检出PR #{pr_number} 到分支 {local_branch}")

    elif branch_name is not None:
        # Fetch branch
        # 获取分支
        log.append(f"正在获取分支 {branch_name} 从远程 {remote_name}")

        # First fetch branch
        # 首先fetch分支
        fetch_cmd = ["git", "fetch", remote_name, branch_name]
        fetch_result = run_command(fetch_cmd, cwd=project_dir)

        if fetch_result["status"] != "success":
            error_msg = format_error_message("获取分支", fetch_result["stderr"])
            return {"status": "error", "log": log + [error_msg], "error": error_msg}

        # Checkout branch
        # 检出分支
        checkout_cmd = ["git", "checkout", branch_name]
        checkout_result = run_command(checkout_cmd, cwd=project_dir)

        if checkout_result["status"] != "success":
            # If direct checkout fails, try to create local branch tracking remote branch
            # 如果直接检出失败，尝试创建本地分支跟踪远程分支
            track_cmd = [
                "git",
                "checkout",
                "-b",
                branch_name,
                f"{remote_name}/{branch_name}",
            ]
            track_result = run_command(track_cmd, cwd=project_dir)

            if track_result["status"] != "success":
                error_msg = format_error_message("检出分支", track_result["stderr"])
                return {
                    "status": "error",
                    "log": log + ["直接检出失败，尝试创建跟踪分支...", error_msg],
                    "error": error_msg,
                }

        log.append(f"成功获取并检出分支 {branch_name}")

    else:
        return {"status": "error", "log": log, "error": "必须提供分支名称或PR编号"}

    return {"status": "success", "log": log, "error": None}


def _git_rebase_internal(
    project_dir: str,
    source_branch: str,
    onto_branch: Optional[str],
    interactive: bool,
    force: bool,
) -> Dict[str, Any]:
    """
    Internal function: Execute Git rebase operation
    内部函数：执行Git rebase操作

    Args:
        project_dir (str): Project directory path
        project_dir (str): 项目目录路径
        source_branch (str): Source branch to rebase from
        source_branch (str): 要从中rebase的源分支
        onto_branch (Optional[str]): Target branch to rebase onto
        onto_branch (Optional[str]): 要rebase到的目标分支
        interactive (bool): Whether to perform interactive rebase
        interactive (bool): 是否执行交互式rebase
        force (bool): Whether to force rebase without confirmation
        force (bool): 是否强制rebase而不进行确认

    Returns:
        Dict[str, Any]: Dictionary containing execution status, logs and error information
        Dict[str, Any]: 包含执行状态、日志和错误信息的字典
    """
    # 检查是否是Git仓库
    if not is_git_repository(project_dir):
        return {"status": "error", "log": [], "error": "指定目录不是有效的Git仓库"}

    log = []

    # Build rebase command
    # Build rebase command
    # 构建rebase命令
    rebase_cmd = ["git", "rebase"]

    if interactive:
        rebase_cmd.append("-i")

    # Determine rebase target
    # Determine rebase target
    # 确定rebase目标
    if onto_branch is None:
        # Directly rebase to source_branch
        # 直接rebase到source_branch
        rebase_cmd.append(source_branch)
        log.append(f"正在执行rebase操作: 当前分支 -> {source_branch}")
    else:
        # Rebase source_branch commits from current branch onto onto_branch
        # rebase当前分支的source_branch提交到onto_branch
        rebase_cmd.extend(["--onto", onto_branch, source_branch])
        log.append(f"正在执行rebase操作: {source_branch} -> {onto_branch}")

    # Execute rebase command
    # Execute rebase command
    # 执行rebase命令
    rebase_result = run_command(rebase_cmd, cwd=project_dir)

    if rebase_result["status"] != "success":
        # Check if it's a conflict error
        # 检查是否是冲突错误
        if (
            "CONFLICT" in rebase_result["stderr"]
            or "CONFLICT" in rebase_result["stdout"]
        ):
            error_msg = "rebase过程中遇到冲突，请手动解决后继续"
            log.append("rebase遇到冲突，请执行以下步骤解决:")
            log.append("1. 解决冲突文件中的冲突")
            log.append("2. 执行 'git add' 添加解决后的文件")
            log.append("3. 执行 'git rebase --continue' 继续rebase")
            log.append("   或者执行 'git rebase --abort' 取消rebase")
        else:
            error_msg = format_error_message("Git rebase", rebase_result["stderr"])

        return {"status": "error", "log": log + [error_msg], "error": error_msg}

    log.append("Git rebase 成功完成")
    return {"status": "success", "log": log, "error": None}
