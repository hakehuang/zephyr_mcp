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


def activate_venv():
    """Activate virtual environment if not already active
    如果虚拟环境未激活，则激活它"""

    # Check if already in virtual environment
    # 检查是否已在虚拟环境中
    if is_venv_active():
        print("[Venv] Virtual environment is already active")
        print("[Venv] 虚拟环境已激活")
        print(f"[Venv] Python executable: {get_current_python_path()}")
        print(f"[Venv] Python 可执行文件: {get_current_python_path()}")
        return True

    # Detect virtual environment
    # 检测虚拟环境
    venv_path = detect_venv_path()
    if not venv_path:
        print("[Venv] No virtual environment found in project directory")
        print("[Venv] 在项目目录中未找到虚拟环境")
        return False

    print(f"[Venv] Found virtual environment: {venv_path}")
    print(f"[Venv] 找到虚拟环境: {venv_path}")

    # Get virtual environment Python path
    # 获取虚拟环境Python路径
    venv_python = get_venv_python_path(venv_path)
    if not venv_python:
        print("[Venv] Could not find Python executable in virtual environment")
        print("[Venv] 在虚拟环境中找不到Python可执行文件")
        return False

    # Check if we're already using the virtual environment Python
    # 检查是否已经在使用虚拟环境的Python
    current_python = get_current_python_path()
    if str(venv_python).lower() == current_python.lower():
        print("[Venv] Already using virtual environment Python")
        print("[Venv] 已经在使用虚拟环境的Python")
        return True

    # Restart with virtual environment Python
    # 使用虚拟环境Python重新启动
    print(f"[Venv] Restarting with virtual environment Python: {venv_python}")
    print(f"[Venv] 使用虚拟环境Python重新启动: {venv_python}")

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
        print(f"[Venv] Failed to restart with virtual environment: {e}")
        print(f"[Venv] 使用虚拟环境重新启动失败: {e}")
        return False
    except Exception as e:
        print(f"[Venv] Unexpected error during restart: {e}")
        print(f"[Venv] 重新启动过程中出现意外错误: {e}")
        return False


def ensure_venv_activated():
    """Ensure virtual environment is activated, restart if necessary
    确保虚拟环境已激活，必要时重新启动"""

    # If already in virtual environment, nothing to do
    # 如果已在虚拟环境中，无需操作
    if is_venv_active():
        return True

    # Try to activate virtual environment
    # 尝试激活虚拟环境
    return activate_venv()


def check_venv_dependencies():
    """Check if required dependencies are installed in virtual environment
    检查虚拟环境中是否安装了必需的依赖"""

    if not is_venv_active():
        print("[Venv] Cannot check dependencies: virtual environment not active")
        print("[Venv] 无法检查依赖: 虚拟环境未激活")
        return False

    required_packages = [
        "requests",
        "python-dotenv",
        "openai",
        "anthropic",
        "opentelemetry-sdk",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"[Venv] Missing required packages: {', '.join(missing_packages)}")
        print(f"[Venv] 缺少必需的包: {', '.join(missing_packages)}")
        return False

    print("[Venv] All required dependencies are available")
    print("[Venv] 所有必需的依赖都可用")
    return True


if __name__ == "__main__":
    # Test the virtual environment manager
    # 测试虚拟环境管理器
    print("=== Virtual Environment Manager Test ===")
    print("=== 虚拟环境管理器测试 ===")

    venv_path = detect_venv_path()
    print(f"Detected venv path: {venv_path}")
    print(f"检测到的venv路径: {venv_path}")

    is_active = is_venv_active()
    print(f"Venv active: {is_active}")
    print(f"虚拟环境激活状态: {is_active}")

    current_python = get_current_python_path()
    print(f"Current Python: {current_python}")
    print(f"当前Python: {current_python}")

    if venv_path:
        venv_python = get_venv_python_path(venv_path)
        print(f"Venv Python: {venv_python}")
        print(f"虚拟环境Python: {venv_python}")

    print("Test completed successfully")
    print("测试成功完成")
