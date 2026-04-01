#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function Description: Test Git connection with provided credentials
功能描述: 使用提供的凭据测试Git连接
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse

from src.utils.common_tools import check_tools
from src.utils.input_validation import (
    ValidationError,
    validate_existing_directory,
    validate_non_empty_text,
    validate_repo_url,
)


GIT_AUTH_HOSTS = {"github.com", "api.github.com"}


def _create_askpass_script(username: str, password: str) -> tuple[str, dict[str, str]]:
    env = os.environ.copy()
    env["ZEPHYR_MCP_GIT_USERNAME"] = username
    env["ZEPHYR_MCP_GIT_PASSWORD"] = password
    env["GIT_TERMINAL_PROMPT"] = "0"

    suffix = ".bat" if os.name == "nt" else ".sh"
    fd, script_path = tempfile.mkstemp(prefix="zephyr_mcp_git_askpass_", suffix=suffix)
    os.close(fd)

    if os.name == "nt":
        script = (
            "@echo off\n"
            "set prompt=%~1\n"
            "echo %prompt% | findstr /I \"username\" >nul && (\n"
            "  echo %ZEPHYR_MCP_GIT_USERNAME%\n"
            ") || (\n"
            "  echo %ZEPHYR_MCP_GIT_PASSWORD%\n"
            ")\n"
        )
    else:
        script = (
            "#!/bin/sh\n"
            "case \"$1\" in\n"
            "  *Username*|*username*) printf '%s\\n' \"$ZEPHYR_MCP_GIT_USERNAME\" ;;\n"
            "  *) printf '%s\\n' \"$ZEPHYR_MCP_GIT_PASSWORD\" ;;\n"
            "esac\n"
        )

    Path(script_path).write_text(script, encoding="utf-8")
    if os.name != "nt":
        os.chmod(script_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    env["GIT_ASKPASS"] = script_path
    env["SSH_ASKPASS"] = script_path
    return script_path, env



def test_git_connection(
    repo_url: str,
    username: str | None = None,
    password: str | None = None,
    project_dir: str | None = None,
) -> Dict[str, Any]:
    """
    Function Description: Test Git connection with provided credentials
    功能描述: 使用提供的凭据测试Git连接
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}

    askpass_script: str | None = None
    try:
        repo_url = validate_repo_url(repo_url, "repo_url")
        if project_dir is not None:
            project_dir = validate_existing_directory(project_dir, "project_dir")
        if username is not None:
            username = validate_non_empty_text(username, "username", max_length=256)
        if password is not None:
            password = validate_non_empty_text(password, "password", max_length=512)
    except ValidationError as exc:
        return {"status": "error", "log": "", "error": str(exc), "connection_test_passed": False}

    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"

    if username or password:
        if not (username and password):
            return {
                "status": "error",
                "log": "",
                "error": "username 和 password 必须同时提供",
                "connection_test_passed": False,
            }

        parsed = urlparse(repo_url)
        if parsed.scheme in {"http", "https"} and parsed.hostname not in GIT_AUTH_HOSTS:
            return {
                "status": "error",
                "log": "",
                "error": "出于安全考虑，仅支持为 GitHub HTTPS 地址提供显式凭据测试",
                "connection_test_passed": False,
            }

        askpass_script, env = _create_askpass_script(username, password)

    cwd = project_dir or None
    cmd = ["git", "ls-remote", repo_url, "HEAD"]

    try:
        process = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if process.returncode == 0:
            return {
                "status": "success",
                "log": f"成功连接到Git仓库: {repo_url}",
                "error": "",
                "connection_test_passed": True,
                "output_sample": process.stdout[:200] if process.stdout else "",
            }

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
    finally:
        if askpass_script:
            try:
                os.remove(askpass_script)
            except OSError:
                pass
