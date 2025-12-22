#!/usr/bin/env python3
# start_mcp_server.py - MCP Server Launcher
# start_mcp_server.py - MCP 服务器启动器
"""
MCP Server Launcher with Virtual Environment Support
支持虚拟环境的 MCP 服务器启动器

This script ensures that the MCP server is started from the project root directory
with the virtual environment properly activated.
此脚本确保 MCP 服务器从项目根目录启动，并正确激活虚拟环境。
"""

import os
import sys
import io
import subprocess
from pathlib import Path

os.environ['PYTHONUNBUFFERED'] = '1'

def main():
    """Main entry point for the MCP server launcher
    MCP 服务器启动器的主入口点"""

    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # Get project root directory
    # 获取项目根目录
    project_root = Path(__file__).parent

    print("=== MCP Server Launcher ===")
    print("=== MCP 服务器启动器 ===")
    print(f"Project root: {project_root}")
    print(f"项目根目录: {project_root}")

    # Change to project root directory
    # 切换到项目根目录
    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}")
    print(f"工作目录: {os.getcwd()}")

    # Check if virtual environment exists
    # 检查虚拟环境是否存在
    venv_path = project_root / ".venv"
    if not venv_path.exists():
        print("[Error] Virtual environment not found at: .venv")
        print("[错误] 在 .venv 处未找到虚拟环境")
        print("[Info] Please create virtual environment first: python -m venv .venv")
        print("[信息] 请先创建虚拟环境: python -m venv .venv")
        return 1

    # Get virtual environment Python executable
    # 获取虚拟环境 Python 可执行文件
    if os.name == "nt":  # Windows
        python_exe = venv_path / "Scripts" / "python.exe"
    else:  # Linux/macOS
        python_exe = venv_path / "bin" / "python"

    if not python_exe.exists():
        print(f"[Error] Python executable not found: {python_exe}")
        print(f"[错误] 未找到 Python 可执行文件: {python_exe}")
        return 1

    print(f"Using Python: {python_exe}")
    print(f"使用 Python: {python_exe}")

    # MCP server script path
    # MCP 服务器脚本路径
    mcp_server_script = project_root / "src" / "mcp_server.py"
    if not mcp_server_script.exists():
        print(f"[Error] MCP server script not found: {mcp_server_script}")
        print(f"[错误] 未找到 MCP 服务器脚本: {mcp_server_script}")
        return 1

    # Build command to start MCP server with virtual environment Python
    # 构建使用虚拟环境 Python 启动 MCP 服务器的命令
    command = [str(python_exe), str(mcp_server_script)] + sys.argv[1:]

    print("\n[Starting] Starting MCP server with virtual environment...")
    print("\n[启动] 正在使用虚拟环境启动 MCP 服务器...")
    print(f"Command: {' '.join(command)}")
    print(f"命令: {' '.join(command)}")

    try:
        # Start the MCP server
        # 启动 MCP 服务器
        result = subprocess.run(command, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"[Error] MCP server failed with exit code {e.returncode}")
        print(f"[错误] MCP 服务器失败，退出代码 {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n[Info] MCP server stopped by user")
        print("\n[信息] MCP 服务器被用户停止")
        return 0
    except Exception as e:
        print(f"[Error] Unexpected error: {e}")
        print(f"[错误] 意外错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
