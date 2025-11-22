from typing import Dict, Any, Optional
import subprocess
import os
import sys


def check_tools(tools: list) -> Dict[str, bool]:
    """
    检查系统中是否安装了指定的工具
    
    Args:
        tools (list): 需要检查的工具名称列表
    
    Returns:
        Dict[str, bool]: 包含每个工具安装状态的字典
    """
    result = {}
    for tool in tools:
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
    检查指定目录是否是Git仓库
    
    Args:
        project_dir (str): 项目目录路径
    
    Returns:
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
    获取当前Git分支名称
    
    Args:
        project_dir (str): 项目目录路径
    
    Returns:
        Optional[str]: 当前分支名称，如果无法获取返回None
    """
    try:
        cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        return process.stdout.strip() if process.returncode == 0 else None
    except Exception:
        return None


def is_branch_exists(project_dir: str, branch_name: str, remote: str = "origin") -> bool:
    """
    检查分支是否存在（本地或远程）
    
    Args:
        project_dir (str): 项目目录路径
        branch_name (str): 分支名称
        remote (str): 远程仓库名称，默认为"origin"
    
    Returns:
        bool: 如果分支存在返回True，否则返回False
    """
    try:
        # 检查本地分支
        local_cmd = ["git", "show-ref", "--verify", f"refs/heads/{branch_name}"]
        local_process = subprocess.run(local_cmd, cwd=project_dir, capture_output=True, text=True)
        if local_process.returncode == 0:
            return True
        
        # 检查远程分支
        remote_cmd = ["git", "show-ref", "--verify", f"refs/remotes/{remote}/{branch_name}"]
        remote_process = subprocess.run(remote_cmd, cwd=project_dir, capture_output=True, text=True)
        return remote_process.returncode == 0
    except Exception:
        return False


def run_command(cmd: list, cwd: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    执行命令并返回结果
    
    Args:
        cmd (list): 命令及其参数列表
        cwd (Optional[str]): 工作目录
        timeout (Optional[int]): 超时时间（秒）
    
    Returns:
        Dict[str, Any]: 包含执行状态、输出和错误信息的字典
    """
    try:
        process = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return {
            "status": "success" if process.returncode == 0 else "error",
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out"
        }
    except Exception as e:
        return {
            "status": "error",
            "returncode": -1,
            "stdout": "",
            "stderr": str(e)
        }


def ensure_directory_exists(directory_path: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory_path (str): 目录路径
    
    Returns:
        bool: 如果目录存在或创建成功返回True，否则返回False
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception:
        return False


def format_error_message(operation: str, error: str) -> str:
    """
    格式化错误消息
    
    Args:
        operation (str): 操作名称
        error (str): 错误信息
    
    Returns:
        str: 格式化后的错误消息
    """
    return f"{operation}失败: {error}"


def parse_git_config(config_output: str) -> Dict[str, str]:
    """
    解析Git配置输出
    
    Args:
        config_output (str): Git配置命令的输出
    
    Returns:
        Dict[str, str]: 配置项字典
    """
    config_dict = {}
    config_lines = config_output.strip().split('\n') if config_output.strip() else []
    
    for line in config_lines:
        if '=' in line:
            key, value = line.split('=', 1)
            config_dict[key.strip()] = value.strip()
    
    return config_dict