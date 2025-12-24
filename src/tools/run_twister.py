#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Description: Twister test tool for Zephyr project
文件描述: Zephyr项目的Twister测试工具
"""


import os
import re
import subprocess
from typing import Dict, Any, Optional, Union, List
from src.utils.common_tools import check_tools
from src.utils.logging_utils import get_logger, print_to_logger


def run_twister(
    platform: Optional[str] = None,
    tests: Optional[Union[List[str], str]] = None,
    test_cases: Optional[Union[List[str], str]] = None,
    enable_slow: bool = False,
    build_only: bool = False,
    extra_args: Optional[str] = None,
    project_dir: str = ".",
) -> Dict[str, Any]:
    """
    Function Description: Execute twister test or build command and return structured results
    功能描述: 执行twister测试或编译命令并返回结构化结果

    Parameters:
    参数说明:
    - platform (Optional[str]): Optional. Target hardware platform
    - platform (Optional[str]): 可选。目标硬件平台
    - tests (Optional[Union[List[str], str]]): Optional. Test path or suite name (using -T parameter)
    - tests (Optional[Union[List[str], str]]): 可选。测试路径或套件名称（使用-T参数）
    - test_cases (Optional[Union[List[str], str]]): Optional. Test case name (using -s parameter)
    - test_cases (Optional[Union[List[str], str]]): 可选。测试用例名称（使用-s参数）
    - enable_slow (bool): Optional. Whether to enable slow tests, default is False
    - enable_slow (bool): 可选。是否启用慢测试，默认为False
    - build_only (bool): Optional. Whether to build only, default is False
    - build_only (bool): 可选。是否仅编译，默认为False
    - extra_args (Optional[str]): Optional. Additional twister parameters
    - extra_args (Optional[str]): 可选。额外的twister参数
    - project_dir (str): Required. Zephyr project root directory
    - project_dir (str): 必须。Zephyr项目根目录

    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log, statistics and error information
    - Dict[str, Any]: 包含状态、日志、统计信息和错误信息

    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """

    logger = get_logger("run_twister")
    debug: List[str] = []

    def _dbg(message: str) -> None:
        debug.append(message)
        print_to_logger(logger, message)

    _dbg(
        "[run_twister] Start twister execution with params: "
        f"platform={platform}, tests={tests}, test_cases={test_cases}, "
        f"enable_slow={enable_slow}, build_only={build_only}, "
        f"extra_args={extra_args}, project_dir={project_dir}"
    )

    # 检查twister工具是否可用
    # 尝试找到twister脚本的位置（通常在zephyr/scripts目录下）
    twister_path = os.path.join(project_dir, "scripts", "twister")
    _dbg(f"[run_twister] Checking twister path: {twister_path}")
    if not os.path.exists(twister_path):
        _dbg(f"[run_twister] twister not found at {twister_path}, checking system PATH...")
        tools_status = check_tools(["twister"])
        _dbg(f"[run_twister] check_tools result: {tools_status}")
        if not tools_status.get("twister", False):
            _dbg("[run_twister] twister tool not found in system PATH.")
            return {
                "status": "error",
                "log": "",
                "debug": debug,
                "error": "twister工具未找到，请确保正确设置了Zephyr环境",
            }
        twister_path = "twister"
    else:
        _dbg(f"[run_twister] twister found at {twister_path}")


    # 检查项目目录是否存在
    if not os.path.exists(project_dir):
        _dbg(f"[run_twister] 项目目录不存在: {project_dir}")
        return {
            "status": "error",
            "log": "",
            "debug": debug,
            "error": f"项目目录不存在: {project_dir}",
        }


    try:
        # 构建twister命令
        cmd = [twister_path]
        _dbg(f"[run_twister] Initial command: {cmd}")

        # 添加平台参数
        if platform:
            cmd.extend(["-p", platform])
            _dbg(f"[run_twister] Added platform: {platform}")

        # 添加测试路径参数
        if tests:
            if isinstance(tests, list):
                for test in tests:
                    cmd.extend(["-T", test])
                    _dbg(f"[run_twister] Added test path: {test}")
            else:
                cmd.extend(["-T", tests])
                _dbg(f"[run_twister] Added test path: {tests}")

        # 添加测试用例参数
        if test_cases:
            if isinstance(test_cases, list):
                for test_case in test_cases:
                    cmd.extend(["-s", test_case])
                    _dbg(f"[run_twister] Added test case: {test_case}")
            else:
                cmd.extend(["-s", test_cases])
                _dbg(f"[run_twister] Added test case: {test_cases}")

        # 添加其他可选参数
        if enable_slow:
            cmd.append("--enable-slow")
            _dbg("[run_twister] Enabled slow tests")
        if build_only:
            cmd.append("--build-only")
            _dbg("[run_twister] Build only mode enabled")

        # 添加额外参数
        if extra_args:
            # 将额外参数作为字符串解析并添加
            extra_args_list = extra_args.split()
            cmd.extend(extra_args_list)
            _dbg(f"[run_twister] Added extra args: {extra_args_list}")

        _dbg(f"[run_twister] Final command: {' '.join(cmd)} (cwd={project_dir})")

        # 执行命令
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True, check=False)
        _dbg(f"[run_twister] Command executed. Return code: {process.returncode}")

        # 解析输出，提取统计信息
        stdout = process.stdout
        stderr = process.stderr
        _dbg(f"[run_twister] STDOUT:\n{stdout}")
        _dbg(f"[run_twister] STDERR:\n{stderr}")

        # 尝试从输出中提取测试统计信息
        stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "error": 0,
            "timeout": 0,
        }

        # 简单的统计提取逻辑
        if "Total tests selected" in stdout:
            match = re.search(r"Total tests selected: (\d+)", stdout)
            if match:
                stats["total"] = int(match.group(1))
                _dbg(f"[run_twister] Total tests selected: {stats['total']}")

        # 提取各种结果的数量
        for key in ["passed", "failed", "skipped", "error", "timeout"]:
            match = re.search(rf"\b{key}: (\d+)", stdout, re.IGNORECASE)
            if match:
                stats[key] = int(match.group(1))
                _dbg(f"[run_twister] {key}: {stats[key]}")

        if process.returncode == 0:
            _dbg("[run_twister] Twister run successful.")
            return {
                "status": "success",
                "log": stdout,
                "statistics": stats,
                "debug": debug,
                "error": "",
            }
        else:
            _dbg(f"[run_twister] Twister run failed with return code {process.returncode}.")
            return {
                "status": "error",
                "log": stdout,
                "statistics": stats,
                "debug": debug,
                "error": stderr,
            }
    except Exception as e:  # pylint: disable=broad-exception-caught
        _dbg(f"[run_twister] Exception occurred: {str(e)}")
        return {
            "status": "error",
            "log": "",
            "statistics": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "error": 0,
                "timeout": 0,
            },
            "debug": debug,
            "error": f"执行twister失败: {str(e)}",
        }
