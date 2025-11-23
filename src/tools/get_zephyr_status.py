from typing import Dict, Any
import os
import subprocess
from ..utils.common_tools import check_tools

# Try to import mcp or fastmcp
# 尝试导入mcp或fastmcp
mcp = None
try:
    from mcp import FastMCP
    mcp = FastMCP()
except ImportError:
    try:
        from fastmcp import FastMCP
        mcp = FastMCP()
    except ImportError:
        # In test environments, if mcp cannot be imported, create a simple mock object
        # 在测试环境中，如果无法导入mcp，创建一个简单的模拟对象
        class MockMCP:
            def tool(self):
                def decorator(func):
                    return func
                return decorator
        mcp = MockMCP()

@mcp.tool()
def get_zephyr_status(project_dir: str) -> Dict[str, Any]:
    """
    Function Description: Get Git status information of Zephyr project
    功能描述: 获取Zephyr项目的Git状态信息
    
    Parameters:
    参数说明:
    - project_dir (str): Required. Zephyr project directory
    - project_dir (str): 必须。Zephyr项目目录
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains status, current branch, commit information, etc.
    - Dict[str, Any]: 包含状态、当前分支、提交信息等
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    # Check if git tool is installed
    # 检查git工具是否安装
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    # Check if project directory exists
    # 检查项目目录是否存在
    if not os.path.exists(project_dir):
        return {"status": "error", "log": "", "error": f"项目目录不存在: {project_dir}"}
    
    # Check if it's a Git repository
    # 检查是否是Git仓库
    try:
        cmd = ["git", "rev-parse", "--is-inside-work-tree"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        if process.returncode != 0:
            return {"status": "error", "log": "", "error": f"指定目录不是Git仓库: {project_dir}"}
    except Exception as e:
        return {"status": "error", "log": "", "error": f"检查Git仓库失败: {str(e)}"}
    
    # Get current branch
    # 获取当前分支
    try:
        cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        current_branch = process.stdout.strip()
    except Exception as e:
        return {"status": "error", "log": "", "error": f"获取当前分支失败: {str(e)}"}
    
    # Get recent commit information
    # 获取最近的提交信息
    try:
        cmd = ["git", "log", "-1", "--pretty=format:%H%n%an%n%ae%n%ad%n%s"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        commit_info = process.stdout.strip().split('\n')
        
        if len(commit_info) >= 5:
            commit_hash, author_name, author_email, commit_date, commit_message = commit_info[0], commit_info[1], commit_info[2], commit_info[3], commit_info[4]
        else:
            commit_hash, author_name, author_email, commit_date, commit_message = "", "", "", "", ""
    except Exception as e:
        return {"status": "error", "log": "", "error": f"获取提交信息失败: {str(e)}"}
    
    # Get Git status
    # 获取Git状态
    try:
        cmd = ["git", "status"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        git_status = process.stdout.strip()
    except Exception as e:
        return {"status": "error", "log": "", "error": f"获取Git状态失败: {str(e)}"}
    
    return {
        "status": "success",
        "current_branch": current_branch,
        "commit_hash": commit_hash,
        "author_name": author_name,
        "author_email": author_email,
        "commit_date": commit_date,
        "commit_message": commit_message,
        "git_status": git_status
    }