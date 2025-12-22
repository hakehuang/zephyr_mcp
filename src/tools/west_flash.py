#!/bin/env python3
# coding=utf-8
"""
Function Description: west flash tool for flashing firmware using west command
功能描述: 使用 west 命令烧录固件的 west flash 工具
"""

from typing import Dict, Any, Optional
import os
import subprocess
from src.utils.common_tools import check_tools


def west_flash(
    build_dir: str,
    board: Optional[str] = None,
    runner: Optional[str] = None,
    probe_id: Optional[str] = None,
    flash_extra_args: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Function Description: Execute west flash command to flash firmware
    功能描述: 执行west flash命令烧录固件

    Parameters:
    参数说明:
    - build_dir (str): Required. Build output directory
    - build_dir (str): 必须。构建输出目录
    - board (Optional[str]): Optional. Target hardware board model
    - board (Optional[str]): 可选。目标硬件板型号
    - runner (Optional[str]): Optional. Flasher type (e.g., jlink, pyocd, openocd, etc.)
    - runner (Optional[str]): 可选。烧录器类型（如jlink, pyocd, openocd等）
    - probe_id (Optional[str]): Optional. Flasher ID/serial number
    - probe_id (Optional[str]): 可选。烧录器ID/序列号
    - flash_extra_args (Optional[str]): Optional. Additional flash parameters
    - flash_extra_args (Optional[str]): 可选。额外的flash参数

    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息

    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    # 检查west工具是否安装
    tools_status = check_tools(["west"])
    if not tools_status.get("west", False):
        return {"status": "error", "log": "", "error": "west工具未安装"}

    # 检查构建目录是否存在
    if not os.path.exists(build_dir):
        return {"status": "error", "log": "", "error": f"构建目录不存在: {build_dir}"}

    try:
        # 构建west flash命令
        cmd = ["west", "flash"]

        # 添加可选参数
        if board:
            cmd.extend(["--board", board])
        if runner:
            cmd.extend(["--runner", runner])
        if probe_id:
            cmd.extend(["--probe-id", probe_id])
        if flash_extra_args:
            # 将额外参数作为字符串解析并添加
            extra_args = flash_extra_args.split()
            cmd.extend(extra_args)

        # 执行命令
        process = subprocess.run(cmd, cwd=build_dir, capture_output=True, text=True)

        if process.returncode == 0:
            return {"status": "success", "log": process.stdout, "error": ""}
        else:
            return {"status": "error", "log": process.stdout, "error": process.stderr}
    except Exception as e:
        return {"status": "error", "log": "", "error": f"执行west flash失败: {str(e)}"}
