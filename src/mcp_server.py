# mcp_server.py - Zephyr MCP Server
# mcp_server.py - Zephyr MCP 服务器
import os
import sys

# Import MCP related libraries
# 导入 MCP 相关库
try:
    # Try to import FastMCP from fastmcp
    # 尝试从 fastmcp 导入 FastMCP
    from fastmcp import FastMCP  # fastmcp is a third-party MCP implementation, ignore spelling check
    # fastmcp 是第三方 MCP 实现，忽略拼写检查
except ImportError:
    # If fastmcp is not installed, try to use mcp package
    # 如果 fastmcp 未安装，尝试使用 mcp 包
    try:
        from mcp import FastMCP
    except ImportError:
        # If both imports fail, create a mock MCP class for development and testing
        # 如果都导入失败，创建一个模拟的 MCP 类用于开发和测试
        class MockMCP:
            def __init__(self, name):
                self.name = name
                self.tools = {}
            
            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator
            
            def register_tool(self, name, func):
                self.tools[name] = func
            
            def get_registered_tools(self):
                return list(self.tools.keys())
            
            def run(self):
                print(f"Mock MCP Server '{self.name}' is running with {len(self.tools)} tools")
        
        # Use mock class
        # 使用模拟类
        FastMCP = MockMCP
        print("Warning: fastmcp or mcp package not found, using mock MCP class")
        print("警告: 未找到 fastmcp 或 mcp 包，使用模拟的 MCP 类")

# Create MCP server instance
# 创建 MCP 服务器实例
mcp_name = os.getenv("mcp_name", "ZephyrMcpServer")
mcp = FastMCP(mcp_name)

# Import all tool modules
# 导入所有工具模块
# Use relative path import to adapt to different runtime environments
# 使用相对路径导入，适应不同的运行环境


# Add project root directory to Python path to ensure tool modules can be imported
# 将项目根目录添加到Python路径，确保可以导入工具模块
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

try:
    from src.tools.validate_west_init_params import validate_west_init_params
    from src.tools.west_flash import west_flash
    from src.tools.west_update import west_update
    from src.tools.switch_zephyr_version import switch_zephyr_version
    from src.tools.run_twister import run_twister
    from src.tools.git_checkout import git_checkout
    from src.tools.get_zephyr_status import get_zephyr_status
    from src.tools.git_redirect_zephyr_mirror import git_redirect_zephyr_mirror
    from src.tools.get_git_redirect_status import get_git_redirect_status
    from src.tools.set_git_credentials import set_git_credentials
    from src.tools.test_git_connection import test_git_connection
    from src.tools.get_git_config_status import get_git_config_status
    from src.tools.fetch_branch_or_pr import fetch_branch_or_pr
    from src.tools.git_rebase import git_rebase
    from src.tools.setup_zephyr_environment import setup_zephyr_environment
    from src.tools.llm_tools import llm_tools
except ImportError:
    # Alternative import method, import directly from tools directory
    # 备选导入方案，直接从tools目录导入
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    from tools.validate_west_init_params import validate_west_init_params
    from tools.west_flash import west_flash
    from tools.west_update import west_update
    from tools.switch_zephyr_version import switch_zephyr_version
    from tools.run_twister import run_twister
    from tools.git_checkout import git_checkout
    from tools.get_zephyr_status import get_zephyr_status
    from tools.git_redirect_zephyr_mirror import git_redirect_zephyr_mirror
    from tools.get_git_redirect_status import get_git_redirect_status
    from tools.set_git_credentials import set_git_credentials
    from tools.test_git_connection import test_git_connection
    from tools.get_git_config_status import get_git_config_status
    from tools.fetch_branch_or_pr import fetch_branch_or_pr
    from tools.git_rebase import git_rebase
    from tools.setup_zephyr_environment import setup_zephyr_environment
    from tools.llm_tools import llm_tools

def __ensure_tools_are_registered(server):
    """Ensure all tool functions are properly registered with MCP
    确保所有工具函数都被MCP正确注册"""
    required_tools = [
        "validate_west_init_params",
        "west_flash",
        "west_update",
        "switch_zephyr_version",
        "run_twister",
        "git_checkout",
        "get_zephyr_status",
        "git_redirect_zephyr_mirror",
        "get_git_redirect_status",
        "set_git_credentials",
        "test_git_connection",
        "get_git_config_status",
        "fetch_branch_or_pr",
        "git_rebase",
        "setup_zephyr_environment",
        "llm_tools"
    ]
    
    try:
        registered_tools = server.get_registered_tools()
        for tool in required_tools:
            if tool not in registered_tools:
                print(f"Warning: Tool {tool} not registered")
                print(f"警告: 工具 {tool} 未注册")
        
        print(f"Registered {len(registered_tools)} tools")
        print(f"已注册 {len(registered_tools)} 个工具")
    except Exception as e:
        print(f"Error checking tool registration status: {str(e)}")
        print(f"检查工具注册状态时出错: {str(e)}")

# Ensure all tools are registered before running the server
# 运行服务器前确保所有工具都已注册
if __name__ == "__main__":
    # Use dictionary to register tools in batch for better code maintainability
    # 使用字典批量注册工具，提高代码可维护性
    tools_to_register = {
        "validate_west_init_params": validate_west_init_params,
        "west_flash": west_flash,
        "run_twister": run_twister,
        "git_checkout": git_checkout,
        "west_update": west_update,
        "switch_zephyr_version": switch_zephyr_version,
        "get_zephyr_status": get_zephyr_status,
        "git_redirect_zephyr_mirror": git_redirect_zephyr_mirror,
        "get_git_redirect_status": get_git_redirect_status,
        "set_git_credentials": set_git_credentials,
        "test_git_connection": test_git_connection,
        "get_git_config_status": get_git_config_status,
        "fetch_branch_or_pr": fetch_branch_or_pr,
        "git_rebase": git_rebase,
        "setup_zephyr_environment": setup_zephyr_environment,
        "llm_tools": llm_tools
    }
    
    # Register all tools in batch
    # 批量注册所有工具
    registered_count = 0
    for tool_name, tool_func in tools_to_register.items():
        try:
            mcp.register_tool(tool_name, tool_func)
            registered_count += 1
        except Exception as e:
            print(f"Error registering tool '{tool_name}': {str(e)}")
            print(f"注册工具 '{tool_name}' 时出错: {str(e)}")
    
    # Ensure all tools are properly registered
    # 确保所有工具都已正确注册
    __ensure_tools_are_registered(mcp)
    # Run the server
    # 运行服务器
    print(f"\n[Starting] Starting MCP server {mcp_name}...")
    print(f"\n[启动] 正在启动 MCP 服务器 {mcp_name}...")
    try:
        mcp.run()
    except Exception as e:
        print(f"Server runtime error: {str(e)}")
        print(f"服务器运行时出错: {str(e)}")