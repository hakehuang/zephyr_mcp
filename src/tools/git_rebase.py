from typing import Dict, Any, Optional
import os

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
        # 在测试环境中，如果无法导入mcp，创建一个简单的模拟对象
        class MockMCP:
            def tool(self):
                def decorator(func):
                    return func
                return decorator
        mcp = MockMCP()

from ..utils.common_tools import check_tools, run_command, is_git_repository
from ..utils.internal_helpers import _git_rebase_internal

@mcp.tool()
def git_rebase(project_dir: str, source_branch: str, onto_branch: Optional[str] = None, interactive: bool = False, force: bool = False) -> Dict[str, Any]:
    """
    Function Description: Execute Git rebase operation
    功能描述: 执行Git rebase操作
    
    Parameters:
    参数说明:
    - project_dir (str): Required. Project directory
    - project_dir (str): 必须。项目目录
    - source_branch (str): Required. Source branch to rebase from
    - source_branch (str): 必须。要从中rebase的源分支
    - onto_branch (Optional[str]): Optional. Target branch to rebase onto. If None, rebases current branch onto source_branch
    - onto_branch (Optional[str]): 可选。要rebase到的目标分支。如果为None，则将当前分支rebase到source_branch上
    - interactive (bool): Optional. Whether to perform interactive rebase. Default: False
    - interactive (bool): 可选。是否执行交互式rebase。默认：False
    - force (bool): Optional. Whether to force rebase without confirmation. Default: False
    - force (bool): 可选。是否强制rebase而不进行确认。默认：False
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    # 检查git工具是否安装
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    # 检查项目目录是否存在
    if not os.path.exists(project_dir):
        return {"status": "error", "log": "", "error": f"项目目录不存在: {project_dir}"}
    
    # 检查是否是Git仓库
    try:
        cmd = ["git", "rev-parse", "--is-inside-work-tree"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        if process.returncode != 0:
            return {"status": "error", "log": "", "error": f"指定目录不是Git仓库: {project_dir}"}
    except Exception as e:
        return {"status": "error", "log": "", "error": f"检查Git仓库失败: {str(e)}"}
    
    # 获取当前分支
    try:
        cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        current_branch = process.stdout.strip()
    except Exception as e:
        return {"status": "error", "log": "", "error": f"获取当前分支失败: {str(e)}"}
    
    # 检查源分支是否存在
    try:
        cmd = ["git", "show-ref", "--verify", f"refs/heads/{source_branch}"]
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        if process.returncode != 0:
            # 检查远程分支
            cmd = ["git", "show-ref", "--verify", f"refs/remotes/origin/{source_branch}"]
            process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
            if process.returncode != 0:
                return {"status": "error", "log": "", "error": f"源分支不存在: {source_branch}"}
    except Exception as e:
        return {"status": "error", "log": "", "error": f"检查源分支失败: {str(e)}"}
    
    # 如果指定了onto_branch，检查它是否存在
    if onto_branch:
        try:
            cmd = ["git", "show-ref", "--verify", f"refs/heads/{onto_branch}"]
            process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
            if process.returncode != 0:
                # 检查远程分支
                cmd = ["git", "show-ref", "--verify", f"refs/remotes/origin/{onto_branch}"]
                process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
                if process.returncode != 0:
                    return {"status": "error", "log": "", "error": f"目标分支不存在: {onto_branch}"}
        except Exception as e:
            return {"status": "error", "log": "", "error": f"检查目标分支失败: {str(e)}"}
    
    # 调用内部函数执行rebase
    return _git_rebase_internal(project_dir, source_branch, onto_branch, interactive, force)