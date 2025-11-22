from typing import Dict, Any
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

from ..utils.common_tools import check_tools, format_error_message
from ..utils.internal_helpers import _git_checkout_internal

@mcp.tool()
def git_checkout(project_dir: str, ref: str) -> Dict[str, Any]:
    """
    Function Description: Switch to specified Git reference (SHA, tag or branch) in Zephyr project directory
    功能描述: 在Zephyr项目目录中切换到指定的Git引用（SHA号、tag或分支）
    
    Parameters:
    参数说明:
    - project_dir (str): Required. Zephyr project directory
    - project_dir (str): 必须。Zephyr项目目录
    - ref (str): Required. Git reference (SHA, tag or branch name)
    - ref (str): 必须。Git引用（SHA号、tag或分支名称）
    
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
    
    # 调用内部函数执行checkout
    return _git_checkout_internal(project_dir, ref)