# mcp_server.py - Zephyr MCP Server
# mcp_server.py - Zephyr MCP 服务器
import os
import io
import sys
import asyncio

os.environ['PYTHONUNBUFFERED'] = '1'

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import virtual environment manager
# 导入虚拟环境管理器
try:
    from src.utils.venv_manager import ensure_venv_activated, check_venv_dependencies

    VENV_MANAGER_AVAILABLE = True
except ImportError:
    VENV_MANAGER_AVAILABLE = False
    print("Warning: venv_manager module not available", file=sys.stderr)
    print("警告: venv_manager 模块不可用", file=sys.stderr)

# Import MCP related libraries
# 导入 MCP 相关库
try:
    # Try to import FastMCP from fastmcp
    # 尝试从 fastmcp 导入 FastMCP
    from fastmcp import (
        FastMCP,
    )  # fastmcp is a third-party MCP implementation, ignore spelling check
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

            def add_tool(self, name, func):
                self.tools[name] = func

            def get_tools(self):
                return list(self.tools.keys())

            def run(self):
                print(
                    f"Mock MCP Server '{self.name}' is running with {len(self.tools)} tools",
                    file=sys.stderr,
                )

        # Use mock class
        # 使用模拟类
        FastMCP = MockMCP
        print(
            "Warning: fastmcp or mcp package not found, using mock MCP class",
            file=sys.stderr,
        )
        print("警告: 未找到 fastmcp 或 mcp 包，使用模拟的 MCP 类", file=sys.stderr)

# Create MCP server instance
# 创建 MCP 服务器实例
mcp_name = os.getenv("mcp_name", "ZephyrMcpServer")
mcp = FastMCP(mcp_name)


def _register_tool(server, name: str, func) -> None:
    """Register a callable as an MCP tool across different MCP implementations.

    - fastmcp.FastMCP: register via server.tool(func, name=...)
    - MockMCP / simple MCPs: register via server.add_tool(name, func)
    """

    def _get_registered_tool_names() -> set[str]:
        get_tools_method = getattr(server, "get_tools", None)
        if not callable(get_tools_method):
            return set()
        try:
            if asyncio.iscoroutinefunction(get_tools_method):
                try:
                    tools = asyncio.run(get_tools_method())
                except RuntimeError:
                    # If we're already in an event loop, skip pre-check.
                    return set()
            else:
                tools = get_tools_method()
        except Exception:
            return set()

        if isinstance(tools, dict):
            return set(tools.keys())
        if isinstance(tools, (list, tuple, set)):
            return set(str(x) for x in tools)
        return set()

    if name in _get_registered_tool_names():
        return

    tool_attr = getattr(server, "tool", None)
    if callable(tool_attr):
        tool_attr(func, name=name)
        return

    add_tool_attr = getattr(server, "add_tool", None)
    if callable(add_tool_attr):
        add_tool_attr(name, func)
        return

    raise TypeError("MCP server does not support tool registration")

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
    from src.tools.llm_tools import llm_tools, register_llm_tools
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
    from tools.set_git_credentials import set_git_credentials
    from tools.test_git_connection import test_git_connection
    from tools.get_git_config_status import get_git_config_status
    from tools.fetch_branch_or_pr import fetch_branch_or_pr
    from tools.git_rebase import git_rebase
    from tools.setup_zephyr_environment import setup_zephyr_environment
    from tools.llm_tools import llm_tools, register_llm_tools


def register_all_tools(server) -> None:
    """Register all tools on the given MCP server instance.

    Important: with stdio transport, the server is typically started by importing
    this module (not executing it as __main__), so registration must be import-safe.
    """

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
    }

    for tool_name, tool_func in tools_to_register.items():
        _register_tool(server, tool_name, tool_func)

    # Register LLM tools (multiple tool functions)
    register_llm_tools(server)


# Register tools on import so stdio transport works reliably.
try:
    register_all_tools(mcp)
except Exception as e:
    print(f"Error registering tools at import time: {str(e)}", file=sys.stderr)
    print(f"导入时注册工具失败: {str(e)}", file=sys.stderr)


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
        "llm_tools",
        "get_llm_status",
        "generate_text",
        "analyze_code",
        "explain_error",
        "llm_chat",
        "generate_tool_documentation",
    ]

    try:
        get_tools_method = server.get_tools
        if asyncio.iscoroutinefunction(get_tools_method):
            registered_tools = asyncio.run(get_tools_method())
        else:
            registered_tools = get_tools_method()

        # FastMCP may return a dict of tool_name -> tool metadata.
        if isinstance(registered_tools, dict):
            registered_tool_names = set(registered_tools.keys())
        elif isinstance(registered_tools, (list, tuple, set)):
            registered_tool_names = set(str(x) for x in registered_tools)
        else:
            registered_tool_names = set()

        for tool in required_tools:
            print(f"  - {tool}", file=sys.stderr)
            if tool not in registered_tool_names:
                print(f"Warning: Tool {tool} not registered", file=sys.stderr)
                print(f"警告: 工具 {tool} 未注册", file=sys.stderr)

        print(f"Registered {len(registered_tool_names)} tools", file=sys.stderr)
        print(f"已注册 {len(registered_tool_names)} 个工具", file=sys.stderr)
    except Exception as e:
        print(f"Error checking tool registration status: {str(e)}", file=sys.stderr)
        print(f"检查工具注册状态时出错: {str(e)}", file=sys.stderr)


# Ensure all tools are registered before running the server
# 运行服务器前确保所有工具都已注册
if __name__ == "__main__":
    # Ensure virtual environment is activated before proceeding
    # 确保虚拟环境已激活后再继续
    if VENV_MANAGER_AVAILABLE:
        print("[Venv] Checking virtual environment status...", file=sys.stderr)
        print("[Venv] 检查虚拟环境状态...", file=sys.stderr)

        # Try to activate virtual environment
        # 尝试激活虚拟环境
        if ensure_venv_activated():
            # Check dependencies after potential restart
            # 在可能的重新启动后检查依赖
            check_venv_dependencies()
        else:
            print(
                "[Venv] Virtual environment activation failed, continuing with current environment"
            , file=sys.stderr)
            print("[Venv] 虚拟环境激活失败，继续使用当前环境", file=sys.stderr)
    else:
        print(
            "[Venv] Virtual environment manager not available, continuing with current environment"
        , file=sys.stderr)
        print("[Venv] 虚拟环境管理器不可用，继续使用当前环境", file=sys.stderr)

    # Tools are registered at import time; only register again if tool list is empty.
    try:
        get_tools_method = getattr(mcp, "get_tools", None)
        if callable(get_tools_method):
            existing = (
                asyncio.run(get_tools_method())
                if asyncio.iscoroutinefunction(get_tools_method)
                else get_tools_method()
            )
        else:
            existing = None

        existing_names = set(existing.keys()) if isinstance(existing, dict) else set(existing or [])
        if not existing_names:
            register_all_tools(mcp)
    except Exception as e:
        print(f"Error ensuring tools are registered: {str(e)}", file=sys.stderr)
        print(f"确保工具注册时出错: {str(e)}", file=sys.stderr)

    # Ensure all tools are properly registered
    # 确保所有工具都已正确注册
    __ensure_tools_are_registered(mcp)
    # Run the server
    # 运行服务器
    print(f"\n[Starting] Starting MCP server {mcp_name}...", file=sys.stderr)
    print(f"\n[启动] 正在启动 MCP 服务器 {mcp_name}...", file=sys.stderr)
    import traceback
    try:
        mcp.run()
    except Exception as e:
        print(f"Server runtime error: {str(e)}", file=sys.stderr)
        print(f"服务器运行时出错: {str(e)}", file=sys.stderr)
        traceback.print_exc()
