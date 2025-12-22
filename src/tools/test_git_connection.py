#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function Description: Test Git connection with provided credentials
功能描述: 使用提供的凭据测试Git连接
"""

import os
import subprocess
from typing import Dict, Any
from src.utils.common_tools import check_tools


def test_git_connection(
    repo_url: str,
    username: str | None = None,
    password: str | None = None,
    project_dir: str | None = None,
) -> Dict[str, Any]:
    """
    Function Description: Test Git connection with provided credentials
    功能描述: 使用提供的凭据测试Git连接

    Parameters:
    参数说明:
    - repo_url (str): Required. Git repository URL to test
    - repo_url (str): 必须。要测试的Git仓库地址
    - username (Optional[str]): Optional. Git username for authentication
    - username (Optional[str]): 可选。Git认证用户名
    - password (Optional[str]): Optional. Git password for authentication
    - password (Optional[str]): 可选。Git认证密码
    - project_dir (Optional[str]): Optional. Project directory for testing
    - project_dir (Optional[str]): 可选。项目目录，用于测试

    Returns:
    返回值:
    - Dict[str, Any]: Contains status, connection test results and error information
    - Dict[str, Any]: 包含状态、连接测试结果和错误信息

    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    # 检查git工具是否安装
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}

    # 检查项目目录（如果指定了）
    if project_dir is not None and not os.path.exists(project_dir):
        return {"status": "error", "log": "", "error": f"项目目录不存在: {project_dir}"}

    # 准备命令
    cmd = ["git", "ls-remote", repo_url, "HEAD"]
    cwd = project_dir if project_dir is not None else None

    # 准备环境变量
    env = os.environ.copy()

    # 如果提供了凭据，构建带有凭据的URL
    # 注意：这只是一个简单的测试方法，在实际生产环境中应使用更安全的凭据处理方式
    test_url = repo_url
    if username and password:
        # 解析URL以添加凭据
        try:
            from urllib.parse import urlparse, urlunparse

            parsed = urlparse(repo_url)
            netloc = f"{username}:{password}@{parsed.netloc}"
            test_url = urlunparse(
                (
                    parsed.scheme,
                    netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
            cmd[2] = test_url  # 更新命令中的URL
        except ImportError:
            # 如果urllib.parse不可用（Python 2.x），则使用简单方法
            if "://" in repo_url:
                scheme, rest = repo_url.split("://", 1)
                test_url = f"{scheme}://{username}:{password}@{rest}"
                cmd[2] = test_url

    try:
        # 执行git ls-remote命令
        process = subprocess.run(
            cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=30
        )  # 设置超时以防止无限等待

        if process.returncode == 0:
            # 成功连接
            return {
                "status": "success",
                "log": f"成功连接到Git仓库: {repo_url}",
                "error": "",
                "connection_test_passed": True,
                "output_sample": process.stdout[:200] if process.stdout else "",
            }
        else:
            # 连接失败
            error_msg = process.stderr.strip() if process.stderr else "未知错误"
            return {
                "status": "error",
                "log": "",
                "error": f"连接Git仓库失败: {error_msg}",
                "connection_test_passed": False,
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "log": "",
            "error": "连接超时，请检查网络连接和仓库地址",
            "connection_test_passed": False,
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"测试Git连接时发生错误: {str(e)}",
            "connection_test_passed": False,
        }
