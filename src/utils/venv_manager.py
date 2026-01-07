#!usr/bin/env python3
# -*- coding: utf-8 -*-
"""
venv_manager.py - Virtual Environment Manager
venv_manager.py - 虚拟环境管理器
"""

import sys
import subprocess
import platform
from pathlib import Path

from src.utils.logging_utils import get_logger, print_to_logger

logger = get_logger(__name__)


def _eprint(*args, **kwargs):
    """Print to stderr (avoid corrupting stdio JSON-RPC)."""
    kwargs.setdefault("file", sys.stderr)
    print_to_logger(logger, *args, **kwargs)


def detect_venv_path():
    """Detect virtual environment path
    检测虚拟环境路径"""
    project_root = Path(__file__).parent.parent.parent

    # Common virtual environment directories
    # 常见的虚拟环境目录
    possible_venv_dirs = [
        project_root / ".venv",
        project_root / "venv",
        project_root / "env",
        project_root / "virtualenv",
    ]

    for venv_dir in possible_venv_dirs:
        if venv_dir.exists():
            return venv_dir

    return None


def get_venv_activation_command(venv_path):
    """Get virtual environment activation command based on platform
    根据平台获取虚拟环境激活命令"""
    system = platform.system().lower()

    if system == "windows":
        # Windows activation
        # Windows 激活
        activate_script = venv_path / "Scripts" / "activate.bat"
        if activate_script.exists():
            return f"call {activate_script}"
    elif system in ["linux", "darwin"]:  # darwin is macOS
        # Linux/macOS activation
        # Linux/macOS 激活
        activate_script = venv_path / "bin" / "activate"
        if activate_script.exists():
            return f"source {activate_script}"

    return None


def is_venv_active():
    """Check if virtual environment is currently active
    检查虚拟环境是否已激活"""
    # Check if we're running in a virtual environment
    # 检查是否在虚拟环境中运行
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def get_current_python_path():
    """Get current Python executable path
    获取当前Python可执行文件路径"""
    return sys.executable


def get_venv_python_path(venv_path):
    """Get Python executable path in virtual environment
    获取虚拟环境中的Python可执行文件路径"""
    system = platform.system().lower()

    if system == "windows":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"

    return python_exe if python_exe.exists() else None


def activate_venv(allow_restart: bool = True):
    """Activate virtual environment if not already active
    如果虚拟环境未激活，则激活它"""

    # Check if already in virtual environment
    # 检查是否已在虚拟环境中
    if is_venv_active():
        _eprint("[Venv] Virtual environment is already active")
        _eprint("[Venv] 虚拟环境已激活")
        _eprint(f"[Venv] Python executable: {get_current_python_path()}")
        _eprint(f"[Venv] Python 可执行文件: {get_current_python_path()}")
        return True

    # Detect virtual environment
    # 检测虚拟环境
    venv_path = detect_venv_path()
    if not venv_path:
        _eprint("[Venv] No virtual environment found in project directory")
        _eprint("[Venv] 在项目目录中未找到虚拟环境")
        return False

    _eprint(f"[Venv] Found virtual environment: {venv_path}")
    _eprint(f"[Venv] 找到虚拟环境: {venv_path}")

    # Get virtual environment Python path
    # 获取虚拟环境Python路径
    venv_python = get_venv_python_path(venv_path)
    if not venv_python:
        _eprint("[Venv] Could not find Python executable in virtual environment")
        _eprint("[Venv] 在虚拟环境中找不到Python可执行文件")
        return False

    # Check if we're already using the virtual environment Python
    # 检查是否已经在使用虚拟环境的Python
    current_python = get_current_python_path()
    if str(venv_python).lower() == current_python.lower():
        _eprint("[Venv] Already using virtual environment Python")
        _eprint("[Venv] 已经在使用虚拟环境的Python")
        return True

    if not allow_restart:
        _eprint("[Venv] Virtual environment not active and restart is disabled")
        _eprint("[Venv] 虚拟环境未激活且已禁用重新启动")
        _eprint(f"[Venv] Current Python: {current_python}")
        _eprint(f"[Venv] Expected venv Python: {venv_python}")
        return False

    # Restart with virtual environment Python
    # 使用虚拟环境Python重新启动
    _eprint(f"[Venv] Restarting with virtual environment Python: {venv_python}")
    _eprint(f"[Venv] 使用虚拟环境Python重新启动: {venv_python}")

    # Get current script and arguments
    # 获取当前脚本和参数
    script_path = sys.argv[0]
    script_args = sys.argv[1:]

    # Build command to restart with virtual environment Python
    # 构建使用虚拟环境Python重新启动的命令
    command = [str(venv_python), script_path] + script_args

    try:
        # Execute the command
        # 执行命令
        result = subprocess.run(command, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        _eprint(f"[Venv] Failed to restart with virtual environment: {e}")
        _eprint(f"[Venv] 使用虚拟环境重新启动失败: {e}")
        return False
    except Exception as e:
        _eprint(f"[Venv] Unexpected error during restart: {e}")
        _eprint(f"[Venv] 重新启动过程中出现意外错误: {e}")
        return False


def ensure_venv_activated(allow_restart: bool = True):
    """Ensure virtual environment is activated, restart if necessary
    确保虚拟环境已激活，必要时重新启动"""

    # If already in virtual environment, nothing to do
    # 如果已在虚拟环境中，无需操作
    if is_venv_active():
        return True

    # Try to activate virtual environment
    # 尝试激活虚拟环境
    return activate_venv(allow_restart=allow_restart)


def check_venv_dependencies():
    """Check if required dependencies are installed in virtual environment
    检查虚拟环境中是否安装了必需的依赖

    Note:
        Some pip package names differ from their importable module names.
        For example:
        - python-dotenv -> import dotenv
        - opentelemetry-sdk -> import opentelemetry.sdk

    Note: import names are not always the same as pip distribution names
    (e.g. "python-dotenv" is imported as "dotenv").

    检查虚拟环境中是否安装了必需的依赖。

    注意：import 名称不一定与 pip 包名一致（例如："python-dotenv" 的 import 名为 "dotenv"）。
    """

    if not is_venv_active():
        _eprint("[Venv] Cannot check dependencies: virtual environment not active")
        _eprint("[Venv] 无法检查依赖: 虚拟环境未激活")
        return False

    import importlib

    # Map pip package name -> Python import module
    required = {
        "requests": "requests",
        "python-dotenv": "dotenv",
        "openai": "openai",
        "anthropic": "anthropic",
        "opentelemetry-sdk": "opentelemetry.sdk",
    }

    missing_packages: list[str] = []

    for package_name, module_name in required.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        _eprint(f"[Venv] Missing required packages: {', '.join(missing_packages)}")
        _eprint(f"[Venv] 缺少必需的包: {', '.join(missing_packages)}")
        return False

    _eprint("[Venv] All required dependencies are available")
    _eprint("[Venv] 所有必需的依赖都可用")
    return True


if __name__ == "__main__":
    # Test the virtual environment manager
    # 测试虚拟环境管理器
    _eprint("=== Virtual Environment Manager Test ===")
    _eprint("=== 虚拟环境管理器测试 ===")

    venv_path = detect_venv_path()
    _eprint(f"Detected venv path: {venv_path}")
    _eprint(f"检测到的venv路径: {venv_path}")

    is_active = is_venv_active()
    _eprint(f"Venv active: {is_active}")
    _eprint(f"虚拟环境激活状态: {is_active}")

    current_python = get_current_python_path()
    _eprint(f"Current Python: {current_python}")
    _eprint(f"当前Python: {current_python}")

    if venv_path:
        venv_python = get_venv_python_path(venv_path)
        _eprint(f"Venv Python: {venv_python}")
        _eprint(f"虚拟环境Python: {venv_python}")

    _eprint("Test completed successfully")
    _eprint("测试成功完成")
