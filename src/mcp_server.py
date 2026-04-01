# mcp_server.py - Zephyr MCP Server
# mcp_server.py - Zephyr MCP 服务器
import os
import io
import sys
from pathlib import Path
import asyncio
import contextlib
import functools
import inspect
import time
from typing import Any

# Allow running as a script: `python src/mcp_server.py`
# When run this way, the repo root isn't automatically on sys.path.
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.utils.logging_utils import (  # noqa: E402  # pylint: disable=wrong-import-position
    get_logger,
    capture_debug_logs,
    print_to_logger,
    StdioLoggerWriter,
    redirect_stdio_to_logger,
)

logger = get_logger(__name__)

os.environ['PYTHONUNBUFFERED'] = '1'

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import virtual environment manager
# 导入虚拟环境管理器
try:
    from src.utils.venv_manager import (
        ensure_venv_activated,
        check_venv_dependencies,
        is_venv_active,
    )

    VENV_MANAGER_AVAILABLE = True
except ImportError:
    VENV_MANAGER_AVAILABLE = False
    logger.warning("Warning: venv_manager module not available")
    logger.warning("警告: venv_manager 模块不可用")


def _ensure_venv_ready_for_tool() -> tuple[bool, str, str]:
    """Return (ok, error_en, error_zh). Never restarts the process."""

    if not VENV_MANAGER_AVAILABLE:
        return True, "", ""

    if not is_venv_active():
        # Never restart inside a running stdio server.
        ensure_venv_activated(allow_restart=False)
        return (
            False,
            "Virtual environment is not active. Start the server using the venv Python (.venv) before calling tools.",
            "虚拟环境未激活。请先使用虚拟环境(.venv)的Python启动服务器，然后再调用工具。",
        )

    if not bool(check_venv_dependencies()):
        return (
            False,
            "Missing required Python packages in the active venv. Install dependencies (e.g. pip install -r requirements.txt).",
            "当前虚拟环境缺少必需的Python包。请安装依赖（例如：pip install -r requirements.txt）。",
        )

    return True, "", ""


def _wrap_tool_with_venv_step(func):
    """Wrap a tool so venv check is mandatory and stdout is redirected to stderr."""

    def _mask_param(param_name: str, value: Any) -> Any:
        name = (param_name or "").lower()
        if any(
            s in name
            for s in (
                "password",
                "passwd",
                "token",
                "secret",
                "apikey",
                "api_key",
                "pat",
                "private_key",
            )
        ):
            return "<redacted>"
        return value

    sig = inspect.signature(func)
    for p in sig.parameters.values():
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            raise TypeError("Functions with *args/**kwargs are not supported as tools")

    strict_stdio = os.getenv("ZEPHYR_MCP_STRICT_STDIO", "1") != "0"
    wrapped_name = getattr(func, "__name__", "wrapped_tool")

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        debug = []
        process_feedback = []

        def _pf(level, message, **extra):
            event = {
                "ts": time.time(),
                "level": str(level),
                "message": str(message),
                "tool": wrapped_name,
            }
            if extra:
                event.update(extra)
            process_feedback.append(event)

        masked_params = {
            name: _mask_param(name, value)
            for name, value in bound.arguments.items()
        }

        debug.append(f"INFO mcp_server: Invoking tool {wrapped_name}")
        debug.append("INFO mcp_server: Params: " + repr(masked_params))
        debug.append("INFO mcp_server: Strict stdio=" + str(strict_stdio))
        _pf("info", "Invoking tool")
        started = time.time()

        with capture_debug_logs(debug):
            tool_logger = get_logger("tools." + wrapped_name)
            old_print = __import__("builtins").print

            def _tool_print(*print_args, **print_kwargs):
                return print_to_logger(tool_logger, *print_args, **print_kwargs)

            __import__("builtins").print = _tool_print
            try:
                with redirect_stdio_to_logger(tool_logger, strict=strict_stdio):
                    ok, err_en, err_zh = _ensure_venv_ready_for_tool()
                    if not ok:
                        debug.append("ERROR mcp_server: " + err_en)
                        _pf("error", err_en, chinese_error=err_zh)
                        return {
                            "status": "error",
                            "success": False,
                            "error": err_en,
                            "chinese_error": err_zh,
                            "debug": debug,
                            "process_feedback": process_feedback,
                        }
                    try:
                        _pf("info", "Tool execution started")
                        result = func(*bound.args, **bound.kwargs)
                        _pf("info", "Tool execution finished")
                    except Exception as e:
                        debug.append("ERROR mcp_server: Tool raised exception: " + str(e))
                        _pf("error", str(e), exception_type=type(e).__name__)
                        return {
                            "status": "error",
                            "success": False,
                            "error": str(e),
                            "exception_type": type(e).__name__,
                            "debug": debug,
                            "process_feedback": process_feedback,
                        }
            finally:
                __import__("builtins").print = old_print

        debug.append(
            "INFO mcp_server: Finished in " + str(round(time.time() - started, 3)) + "s"
        )
        _pf("info", "Finished", duration_s=round(time.time() - started, 3))
        if isinstance(result, dict):
            existing = result.get("debug")
            if isinstance(existing, list):
                merged = []
                seen = set()
                for item in existing + debug:
                    key = str(item)
                    if key in seen:
                        continue
                    seen.add(key)
                    merged.append(item)
                result["debug"] = merged
            else:
                result["debug"] = debug

            existing_pf = result.get("process_feedback")
            if isinstance(existing_pf, list):
                result["process_feedback"] = existing_pf + process_feedback
            else:
                result["process_feedback"] = process_feedback
            return result

        return {
            "status": "success",
            "success": True,
            "result": result,
            "debug": debug,
            "process_feedback": process_feedback,
        }

    wrapped.__signature__ = sig
    return wrapped

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
                logger.warning(
                    "Mock MCP Server '%s' is running with %s tools",
                    self.name,
                    len(self.tools),
                )

        # Use mock class
        # 使用模拟类
        FastMCP = MockMCP
        logger.warning(
            "Warning: fastmcp or mcp package not found, using mock MCP class"
        )
        logger.warning("警告: 未找到 fastmcp 或 mcp 包，使用模拟的 MCP 类")

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
        tools_method = getattr(server, "get_tools", None)
        if not callable(tools_method):
            return set()
        try:
            if asyncio.iscoroutinefunction(tools_method):
                try:
                    tools = asyncio.run(tools_method())
                except RuntimeError:
                    # If we're already in an event loop, skip pre-check.
                    return set()
            else:
                tools = tools_method()
        except Exception:  # noqa: BLE001
            return set()

        if isinstance(tools, dict):
            return set(tools.keys())
        if isinstance(tools, (list, tuple, set)):
            return set(str(x) for x in tools)
        return set()

    if name in _get_registered_tool_names():
        return

    func = _wrap_tool_with_venv_step(func)

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
    from src.tools.trigger_remote_test import trigger_remote_test
    from src.tools.nxp_downstream_setup import nxp_downstream_setup
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
    from tools.trigger_remote_test import trigger_remote_test
    from tools.nxp_downstream_setup import nxp_downstream_setup

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
        "trigger_remote_test": trigger_remote_test,
        "nxp_downstream_setup": nxp_downstream_setup,
    }

    for tool_name, tool_func in tools_to_register.items():
        _register_tool(server, tool_name, tool_func)

    # Register LLM tools (multiple tool functions)
    try:
        try:
            from src.tools.llm_tools import register_llm_tools  # type: ignore
        except ImportError:
            from tools.llm_tools import register_llm_tools  # type: ignore
        register_llm_tools(server)
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Error registering LLM tools")


# Register tools on import so stdio transport works reliably.
try:
    register_all_tools(mcp)
except Exception as e:
    logger.exception("Error registering tools at import time: %s", str(e))
    logger.error("导入时注册工具失败: %s", str(e))


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
        "trigger_remote_test",
        "nxp_downstream_setup",
        "llm_tools",
        "get_llm_status",
        "generate_text",
        "analyze_code",
        "explain_error",
        "llm_chat",
        "generate_tool_documentation",
    ]

    try:
        server_tools_method = server.get_tools
        if asyncio.iscoroutinefunction(server_tools_method):
            registered_tools = asyncio.run(server_tools_method())
        else:
            registered_tools = server_tools_method()

        # FastMCP may return a dict of tool_name -> tool metadata.
        if isinstance(registered_tools, dict):
            registered_tool_names = set(registered_tools.keys())
        elif isinstance(registered_tools, (list, tuple, set)):
            registered_tool_names = set(str(x) for x in registered_tools)
        else:
            registered_tool_names = set()

        for tool in required_tools:
            logger.info("  - %s", tool)
            if tool not in registered_tool_names:
                logger.warning("Warning: Tool %s not registered", tool)
                logger.warning("警告: 工具 %s 未注册", tool)

        logger.info("Registered %s tools", len(registered_tool_names))
        logger.info("已注册 %s 个工具", len(registered_tool_names))
    except Exception as e:  # noqa: BLE001
        logger.exception("Error checking tool registration status: %s", str(e))
        logger.error("检查工具注册状态时出错: %s", str(e))


# Ensure all tools are registered before running the server
# 运行服务器前确保所有工具都已注册
if __name__ == "__main__":
    # Ensure virtual environment is activated before proceeding
    # 确保虚拟环境已激活后再继续
    if VENV_MANAGER_AVAILABLE:
        logger.info("[Venv] Checking virtual environment status...")
        logger.info("[Venv] 检查虚拟环境状态...")

        # Try to activate virtual environment
        # 尝试激活虚拟环境
        if ensure_venv_activated():
            # Check dependencies after potential restart
            # 在可能的重新启动后检查依赖
            check_venv_dependencies()
        else:
            logger.warning(
                "[Venv] Virtual environment activation failed, continuing with current environment"
            )
            logger.warning("[Venv] 虚拟环境激活失败，继续使用当前环境")
    else:
        logger.warning(
            "[Venv] Virtual environment manager not available, continuing with current environment"
        )
        logger.warning("[Venv] 虚拟环境管理器不可用，继续使用当前环境")

    # Tools are registered at import time; only register again if tool list is empty.
    try:
        mcp_tools_method = getattr(mcp, "get_tools", None)
        if callable(mcp_tools_method):
            existing = (
                asyncio.run(mcp_tools_method())
                if asyncio.iscoroutinefunction(mcp_tools_method)
                else mcp_tools_method()
            )
        else:
            existing = None

        existing_names = set(existing.keys()) if isinstance(existing, dict) else set(existing or [])
        if not existing_names:
            register_all_tools(mcp)
    except Exception as e:  # noqa: BLE001
        logger.exception("Error ensuring tools are registered: %s", str(e))
        logger.error("确保工具注册时出错: %s", str(e))

    # Ensure all tools are properly registered
    # 确保所有工具都已正确注册
    __ensure_tools_are_registered(mcp)
    # Run the server
    # 运行服务器
    logger.info("[Starting] Starting MCP server %s...", mcp_name)
    logger.info("[启动] 正在启动 MCP 服务器 %s...", mcp_name)
    try:
        mcp.run()
    except Exception as e:  # noqa: BLE001
        logger.exception("Server runtime error: %s", str(e))
        logger.error("服务器运行时出错: %s", str(e))
