#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common utility functions for the project
通用工具函数
"""

from typing import Dict, Any, Optional
import subprocess
import os
import time
import random

from src.utils.venv_manager import activate_venv


def check_tools(tools: list) -> Dict[str, bool]:
    """
    Check if specified tools are installed in the system
    检查系统中是否安装了指定的工具

    Args:
        tools (list): List of tool names to check
        tools (list): 需要检查的工具名称列表

    Returns:
        Dict[str, bool]: Dictionary containing installation status of each tool
        Dict[str, bool]: 包含每个工具安装状态的字典
    """
    result = {}
    activate_venv(True)
    for tool in tools:
        # Use 'where' on Windows, 'which' on other systems
        # 在Windows上使用where，在其他系统上使用which
        cmd = "where" if os.name == "nt" else "which"
        try:
            process = subprocess.run([cmd, tool], capture_output=True, text=True)
            result[tool] = process.returncode == 0
        except Exception:
            result[tool] = False
    return result


def is_git_repository(project_dir: str) -> bool:
    """
    Check if the specified directory is a Git repository
    检查指定目录是否是Git仓库

    Args:
        project_dir (str): Project directory path
        project_dir (str): 项目目录路径

    Returns:
        bool: Return True if it's a Git repository, False otherwise
        bool: 如果是Git仓库返回True，否则返回False
    """
    try:
        cmd = ["git", "rev-parse", "--is-inside-work-tree"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        return process.returncode == 0
    except Exception:
        return False


def get_current_branch(project_dir: str) -> Optional[str]:
    """
    Get the current Git branch name
    获取当前Git分支名称

    Args:
        project_dir (str): Project directory path
        project_dir (str): 项目目录路径

    Returns:
        Optional[str]: Current branch name, None if cannot be retrieved
        Optional[str]: 当前分支名称，如果无法获取返回None
    """
    try:
        cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        return process.stdout.strip() if process.returncode == 0 else None
    except Exception:
        return None


def is_branch_exists(
    project_dir: str, branch_name: str, remote: str = "origin"
) -> bool:
    """
    Check if a branch exists (locally or remotely)
    检查分支是否存在（本地或远程）

    Args:
        project_dir (str): Project directory path
        project_dir (str): 项目目录路径
        branch_name (str): Branch name
        branch_name (str): 分支名称
        remote (str): Remote repository name, default is "origin"
        remote (str): 远程仓库名称，默认为"origin"

    Returns:
        bool: Return True if branch exists, False otherwise
        bool: 如果分支存在返回True，否则返回False
    """
    try:
        # Check local branch
        # 检查本地分支
        local_cmd = ["git", "show-ref", "--verify", f"refs/heads/{branch_name}"]
        local_process = subprocess.run(
            local_cmd, cwd=project_dir, capture_output=True, text=True
        )
        if local_process.returncode == 0:
            return True

        # Check remote branch
        # 检查远程分支
        remote_cmd = [
            "git",
            "show-ref",
            "--verify",
            f"refs/remotes/{remote}/{branch_name}",
        ]
        remote_process = subprocess.run(
            remote_cmd, cwd=project_dir, capture_output=True, text=True
        )
        return remote_process.returncode == 0
    except Exception:
        return False


def run_command(
    cmd: list,
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    env: Optional[Dict[str, str]] = None,
    retries: int = 0,
    retry_backoff_seconds: float = 1.0,
) -> Dict[str, Any]:
    """
    Execute command and return results
    执行命令并返回结果

    Args:
        cmd (list): Command and its arguments list
        cmd (list): 命令及其参数列表
        cwd (Optional[str]): Working directory
        cwd (Optional[str]): 工作目录
        timeout (Optional[int]): Timeout in seconds
        timeout (Optional[int]): 超时时间（秒）

    Returns:
        Dict[str, Any]: Dictionary containing execution status, output and error information
        Dict[str, Any]: 包含执行状态、输出和错误信息的字典
    """
    def _is_transient_network_error(stdout: str, stderr: str) -> bool:
        combined = f"{stdout}\n{stderr}".lower()
        patterns = [
            # Git / curl
            "could not resolve host",
            "failed to connect",
            "connection timed out",
            "connection reset",
            "connection was reset",
            "recv failure",
            "send failure",
            "http2",
            "http/2",
            "rpc failed",
            "gnutls_recv_error",
            "schannel",
            "ssl_connect",
            "tls",
            "remote end hung up unexpectedly",
            "the remote end hung up",
            "fatal: unable to access",
            "fatal: unable to look up",
            "http 5",
            "503",
            "502",
            "504",
            # Pip
            "read timed out",
            "temporary failure in name resolution",
            "name or service not known",
            "max retries exceeded",
            "chunked encoding error",
            "connection aborted",
        ]
        return any(p in combined for p in patterns)

    try:
        attempts = max(1, int(retries) + 1)
        last_process: Optional[subprocess.CompletedProcess] = None

        for attempt in range(attempts):
            last_process = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if last_process.returncode == 0:
                return {
                    "status": "success",
                    "returncode": 0,
                    "stdout": last_process.stdout,
                    "stderr": last_process.stderr,
                    "attempts": attempt + 1,
                }

            # Retry only for likely transient network problems.
            can_retry = (
                attempt < attempts - 1
                and _is_transient_network_error(last_process.stdout, last_process.stderr)
            )
            if not can_retry:
                break

            # Exponential backoff with small jitter.
            sleep_seconds = (retry_backoff_seconds * (2**attempt)) + random.uniform(
                0.0, 0.5
            )
            time.sleep(sleep_seconds)

        return {
            "status": "success" if last_process and last_process.returncode == 0 else "error",
            "returncode": -1 if last_process is None else last_process.returncode,
            "stdout": "" if last_process is None else last_process.stdout,
            "stderr": "" if last_process is None else last_process.stderr,
            "attempts": attempts,
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out",
        }
    except Exception as e:
        return {"status": "error", "returncode": -1, "stdout": "", "stderr": str(e)}


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure directory exists, create if it doesn't
    确保目录存在，如果不存在则创建

    Args:
        directory_path (str): Directory path
        directory_path (str): 目录路径

    Returns:
        bool: Return True if directory exists or created successfully, False otherwise
        bool: 如果目录存在或创建成功返回True，否则返回False
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception:
        return False


def format_error_message(operation: str, error: str) -> str:
    """
    Format error message
    格式化错误消息

    Args:
        operation (str): Operation name
        operation (str): 操作名称
        error (str): Error message
        error (str): 错误信息

    Returns:
        str: Formatted error message
        str: 格式化后的错误消息
    """
    return f"{operation}失败: {error}"


def parse_git_config(config_output: str) -> Dict[str, str]:
    """
    Parse Git config output
    解析Git配置输出

    Args:
        config_output (str): Output of Git config command
        config_output (str): Git配置命令的输出

    Returns:
        Dict[str, str]: Configuration items dictionary
        Dict[str, str]: 配置项字典
    """
    config_dict = {}
    config_lines = config_output.strip().split("\n") if config_output.strip() else []

    for line in config_lines:
        if "=" in line:
            key, value = line.split("=", 1)
            config_dict[key.strip()] = value.strip()

    return config_dict
