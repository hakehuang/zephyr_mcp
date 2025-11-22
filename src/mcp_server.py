# mcp_server.py - Zephyr MCP Server
# Zephyr MCP 服务器
import os
import subprocess
import re
from typing import List, Union, Optional, Dict, Any
try:
    from fastmcp import FastMCP  # fastmcp 是第三方 MCP 实现，忽略拼写检查
except ImportError:
    # 如果 fastmcp 未安装，尝试使用 mcp 包
    try:
        from mcp import FastMCP
    except ImportError:
        raise ImportError("无法解析导入“fastmcp”或“mcp”，请确保已安装 fastmcp 或 mcp 包")

mcp_name = os.getenv("mcp_name", "ZephyrMcpServer")
mcp = FastMCP(mcp_name)

def check_tools(tools: List[str]) -> Dict[str, bool]:
    """
    Function Description: Check if required tools exist in the system
    功能描述: 检查必需的工具是否存在于系统中
    
    Parameters:
    参数说明:
    - tools (List[str]): Required. List of tool names to check
    - tools (List[str]): 必须。需要检测的工具名称列表
    
    Returns:
    返回值:
    - Dict[str, bool]: Check result for each tool, key is tool name, value is existence
    - Dict[str, bool]: 每个工具的检查结果，键为工具名，值为是否存在
    
    Exception Handling:
    异常处理:
    - Does not throw exceptions, only returns check results
    - 不抛出异常，仅返回检测结果
    """
    result = {}
    for tool in tools:
        try:
            subprocess.run([tool, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            result[tool] = True
        except (subprocess.SubprocessError, FileNotFoundError):
            result[tool] = False
    return result

def _west_init_core(repo_url: str, branch: str, project_dir: str, 
                   username: str, token: str,
                   auth_method: str = "env") -> Dict[str, Any]:
    """
    Core implementation of west init functionality
    This is the internal implementation that both west_init and west_init_interactive can call
    """
    tools_status = check_tools(["west", "git"])
    if not tools_status.get("west", False):
        return {"status": "error", "log": "", "error": "west工具未安装"}
    
    # 准备认证的仓库URL
    authenticated_url = repo_url
    env = os.environ.copy()
    
    if username and token:
        if auth_method == "embedded":
            # 嵌入式认证：将凭据嵌入URL中
            if "://" in repo_url:
                protocol, rest = repo_url.split("://", 1)
                authenticated_url = f"{protocol}://{username}:{token}@{rest}"
        elif auth_method == "env":
            # 环境变量认证
            env["GIT_USERNAME"] = username
            env["GIT_PASSWORD"] = token
            env["GIT_TERMINAL_PROMPT"] = "0"
        elif auth_method == "config":
            # 配置认证：预先设置Git配置
            try:
                # 设置全局用户名
                username_cmd = ["git", "config", "--global", "user.name", username]
                subprocess.run(username_cmd, capture_output=True, text=True, check=True)
                
                # 设置凭据缓存
                credential_cmd = ["git", "config", "--global", "credential.helper", "cache"]
                subprocess.run(credential_cmd, capture_output=True, text=True, check=True)
                
                # 设置凭据缓存时间
                cache_timeout_cmd = ["git", "config", "--global", "credential.helper", "cache --timeout=3600"]
                subprocess.run(cache_timeout_cmd, capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as e:
                return {
                    "status": "error",
                    "log": "",
                    "error": f"Git配置失败: {e.stderr}"
                }
    
    cmd = ["west", "init", "-m", authenticated_url, "--mr", branch]
    
    try:
        # 测试Git连接（如果提供了凭据）
        if username and token:
            test_cmd = ["git", "ls-remote", authenticated_url, "HEAD"]
            test_env = env.copy()
            test_env["GIT_TERMINAL_PROMPT"] = "0"
            
            test_process = subprocess.run(test_cmd, capture_output=True, text=True, env=test_env)
            if test_process.returncode != 0:
                return {
                    "status": "error",
                    "log": test_process.stderr,
                    "error": f"Git连接测试失败: {test_process.stderr}"
                }
        
        # 执行命令前询问用户确认
        # 直接在函数内部定义一个简单的confirm_execution辅助函数
        def confirm_execution(message):
            """获取用户确认"""
            try:
                confirm = input(f"{message} (y/N): ").strip().lower()
                return confirm in ['y', 'yes']
            except (KeyboardInterrupt, EOFError):
                return False
                
        cmd_str = " ".join(cmd)
        if not confirm_execution(f"即将执行命令: {cmd_str}"):
            return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
        
        # 执行west init
        process = subprocess.run(cmd, capture_output=True, text=True, env=env, check=True)
        
        # 如果使用配置认证，设置项目特定的配置
        if username and token and auth_method == "config":
            try:
                # 设置项目特定的用户名
                local_username_cmd = ["git", "config", "--local", "user.name", username]
                subprocess.run(local_username_cmd, cwd=project_dir, capture_output=True, text=True, check=True)
                
                # 设置项目特定的邮箱
                local_email_cmd = ["git", "config", "--local", "user.email", f"{username}@example.com"]
                subprocess.run(local_email_cmd, cwd=project_dir, capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError:
                # 忽略项目配置错误，因为west init可能已经成功
                pass
        
        return {
            "status": "success",
            "log": process.stdout,
            "auth_method": auth_method,
            "authenticated_url": authenticated_url if username and token else repo_url,
            "error": ""
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "log": e.stdout + e.stderr,
            "auth_method": auth_method,
            "authenticated_url": authenticated_url if username and token else repo_url,
            "error": f"初始化失败: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "auth_method": auth_method,
            "authenticated_url": authenticated_url if username and token else repo_url,
            "error": f"未知错误: {str(e)}"
        }


def west_init_interactive(repo_url: Optional[str], branch: Optional[str], 
                         project_dir: Optional[str], username: Optional[str] = None, 
                         token: Optional[str] = None, auth_method: Optional[str] = None,
                         require_confirmation: bool = True, auto_prompt: bool = True) -> Dict[str, Any]:
    """
    Function Description: Interactive west init with user prompting for missing parameters and confirmation
    功能描述: 交互式west init，提示用户输入缺失参数并要求确认
    
    Parameters:
    参数说明:
    - repo_url (Optional[str]): Git repository URL. If None and auto_prompt=True, will prompt user
    - repo_url (Optional[str]): Git仓库地址。如果为None且auto_prompt=True，将提示用户输入
    - branch (Optional[str]): Git branch name. If None and auto_prompt=True, will prompt user  
    - branch (Optional[str]): Git分支名称。如果为None且auto_prompt=True，将提示用户输入
    - project_dir (Optional[str]): Local project directory. If None and auto_prompt=True, will prompt user
    - project_dir (Optional[str]): 本地项目目录。如果为None且auto_prompt=True，将提示用户输入
    - username (Optional[str]): Git username for authentication
    - username (Optional[str]): Git认证用户名
    - token (Optional[str]): Git token or password for authentication
    - token (Optional[str]): Git令牌或认证密码
    - auth_method (Optional[str]): Authentication method: "embedded", "env", or "config". Default: "embedded"
    - auth_method (Optional[str]): 认证方法："embedded"（嵌入式）、"env"（环境变量）、"config"（配置）。默认："embedded"
    - require_confirmation (bool): Whether to require user confirmation before execution. Default: True
    - require_confirmation (bool): 是否在执行前要求用户确认。默认：True
    - auto_prompt (bool): Whether to automatically prompt for missing parameters. Default: True
    - auto_prompt (bool): 是否自动提示缺失参数。默认：True
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log, confirmation result, and error information
    - Dict[str, Any]: 包含状态、日志、确认结果和错误信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    import sys
    
    def prompt_user(prompt_text: str, default_value: Optional[str] = None, is_password: bool = False):
        """Helper function to prompt user for input"""
        try:
            if default_value:
                prompt_text = f"{prompt_text} (default: {default_value})"
            
            if is_password:
                import getpass
                user_input = getpass.getpass(f"{prompt_text}: ")
            else:
                user_input = input(f"{prompt_text}: ")
            
            # Return default if user enters empty string
            return user_input.strip() if user_input.strip() else default_value
        except (KeyboardInterrupt, EOFError):
            return None
    
    def validate_parameters():
        """Validate and collect all required parameters"""
        nonlocal repo_url, branch, project_dir
        
        # Check for missing required parameters
        missing_params = []
        if not repo_url:
            missing_params.append("repo_url")
        if not branch:
            missing_params.append("branch")  
        if not project_dir:
            missing_params.append("project_dir")
        
        if missing_params and auto_prompt:
            print(f"\n⚠️  检测到缺失必需参数: {', '.join(missing_params)}")
            print("请提供以下信息:\n")
            
            # Prompt for missing parameters
            if not repo_url:
                repo_url = prompt_user("Git仓库地址 (例如: https://github.com/zephyrproject-rtos/zephyr)")
                if not repo_url:
                    return False, "用户取消了repo_url输入"
            
            if not branch:
                branch = prompt_user("Git分支名称", "main")
                if not branch:
                    return False, "用户取消了branch输入"
            
            if not project_dir:
                project_dir = prompt_user("本地项目目录 (例如: c:/temp/zephyr-project)")
                if not project_dir:
                    return False, "用户取消了project_dir输入"
            
            print()  # Add spacing
        
        return True, None
    
    def confirm_execution():
        """Show confirmation dialog to user"""
        nonlocal repo_url, branch, project_dir
        if not require_confirmation:
            return True
            
        print("\n" + "="*60)
        print("🚀 准备执行 west init 命令，配置如下:")
        print("="*60)
        print(f"📦 Git仓库: {repo_url}")
        print(f"🌿 分支: {branch}")
        print(f"📁 项目目录: {project_dir}")
        
        if username:
            print(f"👤 用户名: {username}")
            print(f"🔐 认证方式: {auth_method}")
        else:
            print("🔓 认证: 无")
        
        print("="*60)
        
        try:
            confirm = input("\n是否继续执行? [Y/n]: ").strip().lower()
            return confirm in ['', 'y', 'yes']
        except (KeyboardInterrupt, EOFError):
            return False
    
    # Step 1: Validate parameters and prompt for missing ones
    valid, error_msg = validate_parameters()
    if not valid:
        return {
            "status": "cancelled",
            "log": "",
            "confirmation": False,
            "error": error_msg or "参数验证失败"
        }
    
    # Step 2: Show confirmation dialog
    if not confirm_execution():
        return {
            "status": "cancelled", 
            "log": "",
            "confirmation": False,
            "error": "用户取消了操作"
        }
    
    # Step 3: Execute the core west_init logic
    print("\n🔄 正在执行 west init...")
    
    # Call the core implementation with collected parameters
    # 在调用核心实现前确保所有必需参数已提供
    if repo_url is None or branch is None or project_dir is None:
        return {
            "status": "error",
            "log": "",
            "error": "缺少必需的参数：repo_url、branch 或 project_dir 不能为空"
        }
    
    # 确保 username 有默认值，符合 _west_init_core 的要求
    if username is None:
        username = os.environ.get("ZEPHYR_MCP_GIT_USERNAME", "None")
    if auth_method is None:
        auth_method = "env"
    if token is None:
        token = os.environ.get("ZEPHYR_MCP_GIT_PASSWORD", "None")
    
    result = _west_init_core(repo_url=repo_url, branch=branch, project_dir=project_dir,
                            username=username, token=token, auth_method=auth_method)
    
    # Add confirmation status to result
    result["confirmation"] = True
    result["interactive_mode"] = True
    
    return result


@mcp.tool()
def validate_west_init_params(repo_url: Optional[str] = None, branch: Optional[str] = None, 
                             project_dir: Optional[str] = None, auth_method: str = "embedded") -> Dict[str, Any]:
    """
    Function Description: Validate west init parameters and provide helpful suggestions
    功能描述: 验证west init参数并提供有用的建议
    
    Parameters:
    参数说明:
    - repo_url (Optional[str]): Git repository URL to validate
    - repo_url (Optional[str]): Git仓库地址用于验证
    - branch (Optional[str]): Git branch name to validate
    - branch (Optional[str]): Git分支名称用于验证
    - project_dir (Optional[str]): Local project directory to validate
    - project_dir (Optional[str]): 本地项目目录用于验证
    - auth_method (str): Authentication method to validate
    - auth_method (str): 认证方法用于验证
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains validation status, suggestions, and error information
    - Dict[str, Any]: 包含验证状态、建议和错误信息
    
    Exception Handling:
    异常处理:
    - Does not throw exceptions, only returns validation results
    - 不抛出异常，仅返回验证结果
    """
    validation_result = {
        "status": "valid",
        "missing_params": [],
        "warnings": [],
        "suggestions": [],
        "validation_details": {}
    }
    
    # Check missing parameters
    if not repo_url:
        validation_result["missing_params"].append("repo_url")
        validation_result["suggestions"].append("repo_url: 使用 Zephyr 官方仓库 https://github.com/zephyrproject-rtos/zephyr")
    else:
        # Validate repo_url format
        if not (repo_url.startswith("http://") or repo_url.startswith("https://") or repo_url.startswith("git@")):
            validation_result["warnings"].append("repo_url 格式可能不正确，建议使用 http://, https:// 或 git@ 开头")
        
        # Check if it's a known Zephyr mirror
        if "zephyrproject-rtos" in repo_url:
            validation_result["validation_details"]["repo_url"] = "检测到官方 Zephyr 仓库"
        elif "github.com" in repo_url and "zephyr" in repo_url:
            validation_result["validation_details"]["repo_url"] = "检测到 GitHub 上的 Zephyr 仓库"
    
    if not branch:
        validation_result["missing_params"].append("branch")
        validation_result["suggestions"].append("branch: 常用分支有 'main', 'master', 'v3.5-branch' 等")
    else:
        # Validate branch name
        if branch in ["main", "master"]:
            validation_result["validation_details"]["branch"] = "使用标准主分支"
        elif branch.startswith("v") and "-branch" in branch:
            validation_result["validation_details"]["branch"] = "使用版本分支"
    
    if not project_dir:
        validation_result["missing_params"].append("project_dir")
        validation_result["suggestions"].append("project_dir: 建议使用空目录，例如: c:/temp/zephyr-project")
    else:
        # Validate project directory
        import os
        if os.path.exists(project_dir):
            if os.listdir(project_dir):  # Directory exists and is not empty
                validation_result["warnings"].append(f"目录 {project_dir} 已存在且不为空，可能导致冲突")
            else:
                validation_result["validation_details"]["project_dir"] = "目录存在且为空"
        else:
            validation_result["validation_details"]["project_dir"] = "目录不存在，将被创建"
    
    # Validate auth_method
    valid_auth_methods = ["embedded", "env", "config"]
    if auth_method not in valid_auth_methods:
        validation_result["warnings"].append(f"auth_method '{auth_method}' 不是有效值，使用默认值 'embedded'")
        validation_result["suggestions"].append(f"有效认证方式: {', '.join(valid_auth_methods)}")
    
    # Set overall status
    if validation_result["missing_params"]:
        validation_result["status"] = "missing_params"
    elif validation_result["warnings"]:
        validation_result["status"] = "warnings"
    else:
        validation_result["status"] = "valid"
    
    return validation_result

@mcp.tool()
def west_flash(build_dir: str, board: Optional[str] = None, runner: Optional[str] = None, 
                probe_id: Optional[str] = None, flash_extra_args: Optional[str] = None) -> Dict[str, Any]:
    """
    Function Description: Execute west flash command to flash firmware
    功能描述: 执行west flash命令烧录固件
    
    Parameters:
    参数说明:
    - build_dir (str): Required. Build output directory
    - build_dir (str): 必须。构建输出目录
    - board (Optional[str]): Optional. Target hardware board model
    - board (Optional[str]): 可选。目标硬件板型号
    - runner (Optional[str]): Optional. Flasher type (e.g., jlink, pyocd, openocd, etc.)
    - runner (Optional[str]): 可选。烧录器类型（如jlink, pyocd, openocd等）
    - probe_id (Optional[str]): Optional. Flasher ID/serial number
    - probe_id (Optional[str]): 可选。烧录器ID/序列号
    - flash_extra_args (Optional[str]): Optional. Additional flash parameters
    - flash_extra_args (Optional[str]): 可选。额外的flash参数
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    tools_status = check_tools(["west"])
    if not tools_status.get("west", False):
        return {"status": "error", "log": "", "error": "west工具未安装"}
    
    cmd = ["west", "flash", "-d", build_dir]
    if board:
        cmd.extend(["--board", board])
    if runner:
        cmd.extend(["--runner", runner])
    if probe_id:
        cmd.extend(["--", "--id", probe_id])
    if flash_extra_args:
        cmd.extend(flash_extra_args.split())
    
    # 执行命令前询问用户确认
    def confirm_execution(message):
        """获取用户确认"""
        try:
            confirm = input(f"{message} (y/N): ").strip().lower()
            return confirm in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            return False
    
    cmd_str = " ".join(cmd)
    if not confirm_execution(f"即将执行命令: {cmd_str}"):
        return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {
            "status": "success",
            "log": process.stdout,
            "error": ""
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "log": e.stdout + e.stderr,
            "error": f"烧录失败: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"未知错误: {str(e)}"
        }

@mcp.tool()
def run_twister(platform: Optional[str] = None, tests: Optional[Union[List[str], str]] = None, 
                test_cases: Optional[Union[List[str], str]] = None, enable_slow: bool = False, 
                build_only: bool = False, extra_args: Optional[str] = None, 
                project_dir: str = ".") -> Dict[str, Any]:
    """
    Function Description: Execute twister test or build command and return structured results
    功能描述: 执行twister测试或编译命令并返回结构化结果
    
    Parameters:
    参数说明:
    - platform (Optional[str]): Optional. Target hardware platform
    - platform (Optional[str]): 可选。目标硬件平台
    - tests (Optional[Union[List[str], str]]): Optional. Test path or suite name (using -T parameter)
    - tests (Optional[Union[List[str], str]]): 可选。测试路径或套件名称（使用-T参数）
    - test_cases (Optional[Union[List[str], str]]): Optional. Test case name (using -s parameter)
    - test_cases (Optional[Union[List[str], str]]): 可选。测试用例名称（使用-s参数）
    - enable_slow (bool): Optional. Whether to enable slow tests, default is False
    - enable_slow (bool): 可选。是否启用慢测试，默认为False
    - build_only (bool): Optional. Whether to build only, default is False
    - build_only (bool): 可选。是否仅编译，默认为False
    - extra_args (Optional[str]): Optional. Additional twister parameters
    - extra_args (Optional[str]): 可选。额外的twister参数
    - project_dir (str): Required. Zephyr project root directory
    - project_dir (str): 必须。Zephyr项目根目录
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log, statistics and error information
    - Dict[str, Any]: 包含状态、日志、统计信息和错误信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    tools_status = check_tools(["twister", "west"])
    if not tools_status.get("twister", False):
        return {"status": "error", "log": "", "summary": {}, "error": "twister工具未安装"}
    
    cmd = ["twister"]
    if platform:
        cmd.extend(["-p", platform])
    if tests:
        if isinstance(tests, list):
            for test in tests:
                cmd.extend(["-T", test])
        else:
            cmd.extend(["-T", tests])
    if test_cases:
        if isinstance(test_cases, list):
            for test_case in test_cases:
                cmd.extend(["-s", test_case])
        else:
            cmd.extend(["-s", test_cases])
    if enable_slow:
        cmd.append("--enable-slow")
    if build_only:
        cmd.append("--build-only")
    if extra_args:
        cmd.extend(extra_args.split())
    cmd.extend(["-T", project_dir])
    
    # 执行命令前询问用户确认
    def confirm_execution(message):
        """获取用户确认"""
        try:
            confirm = input(f"{message} (y/N): ").strip().lower()
            return confirm in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            return False
    
    cmd_str = " ".join(cmd)
    if not confirm_execution(f"即将执行命令: {cmd_str}"):
        return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        log = process.stdout + process.stderr
        
        summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        failed_tests = []
        
        total_match = re.search(r"(\d+)\stests\sselected", log)
        if total_match:
            summary["total"] = int(total_match.group(1))
        
        passed_match = re.search(r"(\d+)\spassed", log)
        if passed_match:
            summary["passed"] = int(passed_match.group(1))
        
        failed_match = re.search(r"(\d+)\sfailed", log)
        if failed_match:
            summary["failed"] = int(failed_match.group(1))
        
        skipped_match = re.search(r"(\d+)\sskipped", log)
        if skipped_match:
            summary["skipped"] = int(skipped_match.group(1))
        
        failed_tests_match = re.findall(r"(\w+\.py::\w+\s*\(\)\s*FAILED)", log)
        if failed_tests_match:
            failed_tests = failed_tests_match
        
        return {
            "status": "success",
            "log": log,
            "summary": summary,
            "failed_tests": failed_tests,
            "error": ""
        }
    except subprocess.CalledProcessError as e:
        log = e.stdout + e.stderr
        return {
            "status": "error",
            "log": log,
            "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
            "failed_tests": [],
            "error": f"执行失败: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
            "failed_tests": [],
            "error": f"未知错误: {str(e)}"
        }

# 内部函数：Git checkout操作
# Internal function: Git checkout operation
def _git_checkout_internal(project_dir: str, ref: str) -> Dict[str, Any]:
    """
    Internal function for Git checkout operation
    内部函数：Git checkout操作
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    cmd = ["git", "checkout", ref]
    try:
        # 执行命令前询问用户确认
        def confirm_execution(message):
            """获取用户确认"""
            try:
                confirm = input(f"{message} (y/N): ").strip().lower()
                return confirm in ['y', 'yes']
            except (KeyboardInterrupt, EOFError):
                return False
        
        cmd_str = " ".join(cmd)
        if not confirm_execution(f"即将执行命令: {cmd_str}"):
            return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
            
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True, check=True)
        return {
            "status": "success",
            "log": process.stdout,
            "error": ""
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "log": e.stdout + e.stderr,
            "error": f"Git checkout失败: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"未知错误: {str(e)}"
        }

# 内部函数：West update操作
# Internal function: West update operation
def _west_update_internal(project_dir: str) -> Dict[str, Any]:
    """
    Internal function for west update operation
    内部函数：West update操作
    """
    tools_status = check_tools(["west"])
    if not tools_status.get("west", False):
        return {"status": "error", "log": "", "error": "west工具未安装"}
    
    cmd = ["west", "update"]
    
    # 执行命令前询问用户确认
    def confirm_execution(message):
        """获取用户确认"""
        try:
            confirm = input(f"{message} (y/N): ").strip().lower()
            return confirm in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            return False
    
    cmd_str = " ".join(cmd)
    if not confirm_execution(f"即将执行命令: {cmd_str}"):
        return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
    
    try:
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True, check=True)
        return {
            "status": "success",
            "log": process.stdout,
            "error": ""
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "log": e.stdout + e.stderr,
            "error": f"west update失败: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"未知错误: {str(e)}"
        }

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
    return _git_checkout_internal(project_dir, ref)

@mcp.tool()
def west_update(project_dir: str) -> Dict[str, Any]:
    """
    Function Description: Run west update command in Zephyr project directory
    功能描述: 在Zephyr项目目录中运行west update命令
    
    Parameters:
    参数说明:
    - project_dir (str): Required. Zephyr project directory
    - project_dir (str): 必须。Zephyr项目目录
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    return _west_update_internal(project_dir)

def _switch_zephyr_version_internal(project_dir: str, ref: str) -> Dict[str, Any]:
    """
    Internal function for switching Zephyr version and running west update
    内部函数：切换Zephyr版本并运行west update
    """
    # 执行命令前询问用户确认
    def confirm_execution(message):
        """获取用户确认"""
        try:
            confirm = input(f"{message} (y/N): ").strip().lower()
            return confirm in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            return False
    
    # 确认切换Zephyr版本
    if not confirm_execution(f"即将切换Zephyr版本到 {ref} 并执行west update，是否继续?"):
        return {"status": "canceled", "log": "用户取消了版本切换操作", "error": "用户取消"}
    
    # 首先切换到指定的引用
    checkout_result = _git_checkout_internal(project_dir=project_dir, ref=ref)
    if checkout_result["status"] == "error":
        return checkout_result
    
    # 然后运行west update
    update_result = _west_update_internal(project_dir=project_dir)
    if update_result["status"] == "error":
        return update_result
    
    # 合并结果
    return {
        "status": "success",
        "log": f"Git checkout: {checkout_result['log']}\nWest update: {update_result['log']}",
        "error": ""
    }

@mcp.tool()
def switch_zephyr_version(project_dir: str, ref: str) -> Dict[str, Any]:
    """
    Function Description: Switch to specified Zephyr version (SHA or tag) and run west update
    功能描述: 切换到指定的Zephyr版本（SHA号或tag）并运行west update
    
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
    return _switch_zephyr_version_internal(project_dir, ref)

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
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    try:
        # 获取当前分支
        branch_cmd = ["git", "branch", "--show-current"]
        branch_process = subprocess.run(branch_cmd, cwd=project_dir, capture_output=True, text=True, check=True)
        current_branch = branch_process.stdout.strip()
        
        # 获取当前提交信息
        commit_cmd = ["git", "log", "-1", "--oneline"]
        commit_process = subprocess.run(commit_cmd, cwd=project_dir, capture_output=True, text=True, check=True)
        current_commit = commit_process.stdout.strip()
        
        # 获取状态
        status_cmd = ["git", "status", "--porcelain"]
        status_process = subprocess.run(status_cmd, cwd=project_dir, capture_output=True, text=True, check=True)
        status_output = status_process.stdout.strip()
        
        return {
            "status": "success",
            "current_branch": current_branch,
            "current_commit": current_commit,
            "git_status": status_output,
            "has_changes": bool(status_output),
            "error": ""
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "current_branch": "",
            "current_commit": "",
            "git_status": "",
            "has_changes": False,
            "error": f"获取Git状态失败: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "current_branch": "",
            "current_commit": "",
            "git_status": "",
            "has_changes": False,
            "error": f"未知错误: {str(e)}"
        }

@mcp.tool()
def git_redirect_zephyr_mirror(enable: bool = True, mirror_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Function Description: Configure Git global redirect to redirect GitHub Zephyr repository to specified mirror
    功能描述: 配置Git全局重定向，将GitHub的Zephyr仓库地址重定向到指定的镜像源
    
    Parameters:
    参数说明:
    - enable (bool): Optional. Whether to enable redirect, default is True (enabled)
    - enable (bool): 可选。是否启用重定向，默认为True（启用）
    - mirror_url (Optional[str]): Optional. Mirror URL, defaults to domestic mirror
    - mirror_url (Optional[str]): 可选。镜像源地址，默认为国内镜像源
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    original_url = "https://github.com/zephyrproject-rtos/"
    # 设置默认镜像源，如果用户未提供则使用默认值
    if mirror_url is None:
        mirror_url = "https://www.zephyrrtos.cn:3000/zephyrrtos_china/"
    
    try:
        # 执行命令前询问用户确认
        def confirm_execution(message):
            """获取用户确认"""
            try:
                confirm = input(f"{message} (y/N): ").strip().lower()
                return confirm in ['y', 'yes']
            except (KeyboardInterrupt, EOFError):
                return False
        
        if enable:
            # 启用重定向
            cmd = ["git", "config", "--global", f"url.{mirror_url}.insteadOf", original_url]
            # 执行命令前确认
            cmd_str = " ".join(cmd)
            if not confirm_execution(f"即将执行命令: {cmd_str}"):
                return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
            process = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # 验证配置是否生效
            verify_cmd = ["git", "config", "--global", "--get", f"url.{mirror_url}.insteadOf"]
            verify_process = subprocess.run(verify_cmd, capture_output=True, text=True)
            
            return {
                "status": "success",
                "log": f"已启用Git重定向: {original_url} -> {mirror_url}\n验证结果: {verify_process.stdout.strip()}",
                "error": ""
            }
        else:
            # 禁用重定向
            cmd = ["git", "config", "--global", "--unset", f"url.{mirror_url}.insteadOf"]
            # 执行命令前确认
            cmd_str = " ".join(cmd)
            if not confirm_execution(f"即将执行命令: {cmd_str}"):
                return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            return {
                "status": "success",
                "log": f"已禁用Git重定向: {original_url} -> {mirror_url}",
                "error": ""
            }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "log": e.stdout + e.stderr,
            "error": f"Git重定向配置失败: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"未知错误: {str(e)}"
        }

@mcp.tool()
def get_git_redirect_status() -> Dict[str, Any]:
    """
    Function Description: Get current Git redirect configuration status
    功能描述: 获取当前Git重定向配置状态
    
    Parameters:
    参数说明:
    - No parameters
    - 无参数
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains redirect configuration status information
    - Dict[str, Any]: 包含重定向配置状态信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    try:
        # 获取所有URL重定向配置
        cmd = ["git", "config", "--global", "--get-regexp", "url\\..*\\.insteadOf"]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        redirects = {}
        if process.returncode == 0:
            lines = process.stdout.strip().split('\n')
            for line in lines:
                if line:
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        redirects[parts[0]] = parts[1]
        
        # 检查特定的Zephyr重定向
        zephyr_redirect = None
        check_cmd = ["git", "config", "--global", "--get", "url.https://www.zephyrrtos.cn:3000/zephyrrtos_china/.insteadOf"]
        check_process = subprocess.run(check_cmd, capture_output=True, text=True)
        if check_process.returncode == 0:
            zephyr_redirect = check_process.stdout.strip()
        
        return {
            "status": "success",
            "all_redirects": redirects,
            "zephyr_redirect_enabled": zephyr_redirect is not None,
            "zephyr_redirect_value": zephyr_redirect,
            "error": ""
        }
    except Exception as e:
        return {
            "status": "error",
            "all_redirects": {},
            "zephyr_redirect_enabled": False,
            "zephyr_redirect_value": None,
            "error": f"获取Git重定向状态失败: {str(e)}"
        }

@mcp.tool()
def set_git_credentials(username: str, password: str, project_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Function Description: Set Git credentials for authentication
    功能描述: 设置Git认证凭据
    
    Parameters:
    参数说明:
    - username (str): Required. Git username or access token
    - username (str): 必须。Git用户名或访问令牌
    - password (str): Required. Git password or personal access token
    - password (str): 必须。Git密码或个人访问令牌
    - project_dir (Optional[str]): Optional. Project directory for local configuration
    - project_dir (Optional[str]): 可选。项目目录，用于本地配置
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    try:
        # 执行命令前询问用户确认
        def confirm_execution(message):
            """获取用户确认"""
            try:
                confirm = input(f"{message} (y/N): ").strip().lower()
                return confirm in ['y', 'yes']
            except (KeyboardInterrupt, EOFError):
                return False
        
        # 确认设置Git凭据
        if not confirm_execution(f"即将设置Git凭据，用户名: {username}，是否继续?"):
            return {"status": "canceled", "log": "用户取消了Git凭据设置", "error": "用户取消"}
        
        # 设置全局用户名
        username_cmd = ["git", "config", "--global", "user.name", username]
        # 执行命令前确认
        cmd_str = " ".join(username_cmd)
        if not confirm_execution(f"即将执行命令: {cmd_str}"):
            return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
        username_process = subprocess.run(username_cmd, capture_output=True, text=True, check=True)
        
        # 设置全局邮箱（使用用户名作为邮箱前缀）
        email_cmd = ["git", "config", "--global", "user.email", f"{username}@example.com"]
        # 执行命令前确认
        cmd_str = " ".join(email_cmd)
        if not confirm_execution(f"即将执行命令: {cmd_str}"):
            return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
        email_process = subprocess.run(email_cmd, capture_output=True, text=True, check=True)
        
        # 设置项目特定的凭据（如果提供了项目目录）
        if project_dir:
            # 设置项目特定的用户名
            local_username_cmd = ["git", "config", "--local", "user.name", username]
            # 执行命令前确认
            cmd_str = " ".join(local_username_cmd)
            if not confirm_execution(f"即将执行命令: {cmd_str} (项目目录: {project_dir})"):
                return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
            subprocess.run(local_username_cmd, cwd=project_dir, capture_output=True, text=True, check=True)
            
            # 设置项目特定的邮箱
            local_email_cmd = ["git", "config", "--local", "user.email", f"{username}@example.com"]
            # 执行命令前确认
            cmd_str = " ".join(local_email_cmd)
            if not confirm_execution(f"即将执行命令: {cmd_str} (项目目录: {project_dir})"):
                return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
            subprocess.run(local_email_cmd, cwd=project_dir, capture_output=True, text=True, check=True)
        
        # 配置凭据存储（使用缓存方式）
        credential_cmd = ["git", "config", "--global", "credential.helper", "cache"]
        # 执行命令前确认
        cmd_str = " ".join(credential_cmd)
        if not confirm_execution(f"即将执行命令: {cmd_str}"):
            return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
        subprocess.run(credential_cmd, capture_output=True, text=True, check=True)
        
        # 设置凭据缓存时间（1小时）
        cache_timeout_cmd = ["git", "config", "--global", "credential.helper", "cache --timeout=3600"]
        # 执行命令前确认
        cmd_str = " ".join(cache_timeout_cmd)
        if not confirm_execution(f"即将执行命令: {cmd_str}"):
            return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
        subprocess.run(cache_timeout_cmd, capture_output=True, text=True, check=True)
        
        return {
            "status": "success",
            "log": f"Git凭据设置成功。用户名: {username}, 项目目录: {project_dir or '全局设置'}",
            "error": ""
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "log": e.stdout + e.stderr,
            "error": f"Git凭据设置失败: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"未知错误: {str(e)}"
        }

@mcp.tool()
def test_git_connection(repo_url: str, username: Optional[str] = None, 
                       password: Optional[str] = None, project_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Function Description: Test Git connection with provided credentials
    功能描述: 使用提供的凭据测试Git连接
    
    Parameters:
    参数说明:
    - repo_url (str): Required. Git repository URL to test
    - repo_url (str): 必须。要测试的Git仓库地址
    - username (Optional[str]): Optional. Git username for authentication
    - username (Optional[str]): 可选。Git认证用户名
    - password (Optional[str]): Optional. Git password for authentication
    - password (Optional[str]): 可选。Git认证密码
    - project_dir (Optional[str]): Optional. Project directory for testing
    - project_dir (Optional[str]): 可选。项目目录，用于测试
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains status, connection test results and error information
    - Dict[str, Any]: 包含状态、连接测试结果和错误信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    try:
        # 如果提供了用户名和密码，构建认证URL
        test_url = repo_url
        if username and password:
            # 将用户名和密码嵌入到URL中（仅用于测试）
            if "://" in repo_url:
                protocol, rest = repo_url.split("://", 1)
                test_url = f"{protocol}://{username}:{password}@{rest}"
        
        # 使用ls-remote命令测试连接
        cmd = ["git", "ls-remote", test_url, "HEAD"]
        
        # 设置环境变量（避免交互式认证）
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        
        process = subprocess.run(cmd, capture_output=True, text=True, env=env, 
                                cwd=project_dir if project_dir else None)
        
        if process.returncode == 0:
            return {
                "status": "success",
                "log": f"Git连接测试成功。仓库: {repo_url}",
                "connection_status": "success",
                "output": process.stdout.strip(),
                "error": ""
            }
        else:
            return {
                "status": "error",
                "log": f"Git连接测试失败。仓库: {repo_url}",
                "connection_status": "failed",
                "output": process.stderr.strip(),
                "error": f"连接测试失败: {process.stderr}"
            }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "connection_status": "failed",
            "output": "",
            "error": f"连接测试异常: {str(e)}"
        }

@mcp.tool()
def get_git_config_status(project_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Function Description: Get current Git configuration status
    功能描述: 获取当前Git配置状态
    
    Parameters:
    参数说明:
    - project_dir (Optional[str]): Optional. Project directory to check local configuration
    - project_dir (Optional[str]): 可选。项目目录，用于检查本地配置
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains Git configuration information
    - Dict[str, Any]: 包含Git配置信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    try:
        config_items = {}
        
        # 获取全局配置
        global_cmd = ["git", "config", "--global", "--list"]
        global_process = subprocess.run(global_cmd, capture_output=True, text=True)
        
        if global_process.returncode == 0:
            for line in global_process.stdout.strip().split('\n'):
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    config_items[f"global.{key}"] = value
        
        # 获取本地配置（如果提供了项目目录）
        if project_dir:
            local_cmd = ["git", "config", "--local", "--list"]
            local_process = subprocess.run(local_cmd, cwd=project_dir, capture_output=True, text=True)
            
            if local_process.returncode == 0:
                for line in local_process.stdout.strip().split('\n'):
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        config_items[f"local.{key}"] = value
        
        return {
            "status": "success",
            "config_items": config_items,
            "global_config_count": len([k for k in config_items.keys() if k.startswith("global.")]),
            "local_config_count": len([k for k in config_items.keys() if k.startswith("local.")]),
            "error": ""
        }
    except Exception as e:
        return {
            "status": "error",
            "config_items": {},
            "global_config_count": 0,
            "local_config_count": 0,
            "error": f"获取Git配置状态失败: {str(e)}"
        }

# 内部函数：获取分支或拉取请求
# Internal function: Fetch branch or pull request
def _fetch_branch_or_pr_internal(project_dir: str, branch_name: Optional[str] = None, 
                               pr_number: Optional[int] = None, remote_name: str = "origin") -> Dict[str, Any]:
    """
    Internal function for fetching branch or pull request
    内部函数：获取分支或拉取请求
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    # 验证参数
    if branch_name is None and pr_number is None:
        return {"status": "error", "log": "", "error": "必须提供branch_name或pr_number参数"}
    
    if branch_name is not None and pr_number is not None:
        return {"status": "error", "log": "", "error": "branch_name和pr_number参数不能同时提供"}
    
    try:
        # 执行命令前询问用户确认
        def confirm_execution(message):
            """获取用户确认"""
            try:
                confirm = input(f"{message} (y/N): ").strip().lower()
                return confirm in ['y', 'yes']
            except (KeyboardInterrupt, EOFError):
                return False
        
        if branch_name is not None:
            # 获取指定分支
            cmd = ["git", "fetch", remote_name, branch_name]
            cmd_str = " ".join(cmd)
            if not confirm_execution(f"即将执行命令: {cmd_str}"):
                return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
            
            process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True, check=True)
            
            # 检出获取的分支
            checkout_cmd = ["git", "checkout", branch_name]
            checkout_cmd_str = " ".join(checkout_cmd)
            if not confirm_execution(f"即将执行命令: {checkout_cmd_str}"):
                return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
            
            checkout_process = subprocess.run(checkout_cmd, cwd=project_dir, capture_output=True, text=True, check=True)
            
            return {
                "status": "success",
                "log": f"Git fetch分支: {process.stdout}\nGit checkout: {checkout_process.stdout}",
                "action": "fetch_branch",
                "branch_name": branch_name,
                "remote_name": remote_name,
                "error": ""
            }
        else:
            # 获取指定PR
            # 使用GitHub PR获取方式: refs/pull/{PR_NUMBER}/head:{LOCAL_BRANCH_NAME}
            local_branch_name = f"pr-{pr_number}"
            cmd = ["git", "fetch", remote_name, f"refs/pull/{pr_number}/head:{local_branch_name}"]
            cmd_str = " ".join(cmd)
            if not confirm_execution(f"即将执行命令: {cmd_str}"):
                return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
            
            process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True, check=True)
            
            # 检出获取的PR分支
            checkout_cmd = ["git", "checkout", local_branch_name]
            checkout_cmd_str = " ".join(checkout_cmd)
            if not confirm_execution(f"即将执行命令: {checkout_cmd_str}"):
                return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
            
            checkout_process = subprocess.run(checkout_cmd, cwd=project_dir, capture_output=True, text=True, check=True)
            
            return {
                "status": "success",
                "log": f"Git fetch PR: {process.stdout}\nGit checkout: {checkout_process.stdout}",
                "action": "fetch_pr",
                "pr_number": pr_number,
                "local_branch_name": local_branch_name,
                "remote_name": remote_name,
                "error": ""
            }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "log": e.stdout + e.stderr,
            "error": f"Git操作失败: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"未知错误: {str(e)}"
        }

@mcp.tool()
def fetch_branch_or_pr(project_dir: str, branch_name: Optional[str] = None, 
                      pr_number: Optional[int] = None, remote_name: str = "origin") -> Dict[str, Any]:
    """
    Function Description: Fetch a branch or pull request from a Git repository and checkout
    功能描述: 从Git仓库获取分支或拉取请求并检出
    
    Parameters:
    参数说明:
    - project_dir (str): Required. Project directory
    - project_dir (str): 必须。项目目录
    - branch_name (Optional[str]): Optional. Branch name to fetch
    - branch_name (Optional[str]): 可选。要获取的分支名称
    - pr_number (Optional[int]): Optional. Pull request number to fetch
    - pr_number (Optional[int]): 可选。要获取的拉取请求编号
    - remote_name (str): Optional. Remote name, default is "origin"
    - remote_name (str): 可选。远程仓库名称，默认为"origin"
    
    Returns:
    返回值:
    - Dict[str, Any]: Contains status, log and error information
    - Dict[str, Any]: 包含状态、日志和错误信息
    
    Exception Handling:
    异常处理:
    - Tool detection failure or command execution exception will be reflected in the returned error information
    - 工具检测失败或命令执行异常会体现在返回的错误信息中
    """
    return _fetch_branch_or_pr_internal(project_dir, branch_name, pr_number, remote_name)

# 内部函数：执行Git rebase操作
# Internal function: Execute Git rebase operation
def _git_rebase_internal(project_dir: str, source_branch: str, onto_branch: Optional[str] = None,
                        interactive: bool = False, force: bool = False) -> Dict[str, Any]:
    """
    Internal function for executing Git rebase operation
    内部函数：执行Git rebase操作
    """
    tools_status = check_tools(["git"])
    if not tools_status.get("git", False):
        return {"status": "error", "log": "", "error": "git工具未安装"}
    
    # 验证参数
    if not source_branch:
        return {"status": "error", "log": "", "error": "必须提供source_branch参数"}
    
    try:
        # 执行命令前询问用户确认
        def confirm_execution(message):
            """获取用户确认"""
            try:
                confirm = input(f"{message} (y/N): ").strip().lower()
                return confirm in ['y', 'yes']
            except (KeyboardInterrupt, EOFError):
                return False
        
        # 构建rebase命令
        cmd = ["git", "rebase"]
        if interactive:
            cmd.append("-i")
        if force:
            cmd.append("-f")
        
        if onto_branch:
            # 执行 git rebase [options] --onto <onto_branch> <source_branch>
            cmd.extend(["--onto", onto_branch, source_branch])
        else:
            # 执行 git rebase [options] <source_branch>
            cmd.append(source_branch)
        
        cmd_str = " ".join(cmd)
        if not force and not confirm_execution(f"即将执行命令: {cmd_str}"):
            return {"status": "canceled", "log": "用户取消了命令执行", "error": "用户取消"}
        
        # 执行rebase命令
        process = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        
        if process.returncode == 0:
            return {
                "status": "success",
                "log": process.stdout,
                "action": "git_rebase",
                "source_branch": source_branch,
                "onto_branch": onto_branch,
                "interactive": interactive,
                "force": force,
                "error": ""
            }
        else:
            # 检查是否存在冲突
            has_conflicts = "CONFLICT" in process.stderr or "CONFLICT" in process.stdout
            if has_conflicts:
                return {
                    "status": "conflict",
                    "log": process.stdout + process.stderr,
                    "action": "git_rebase",
                    "source_branch": source_branch,
                    "onto_branch": onto_branch,
                    "interactive": interactive,
                    "force": force,
                    "error": "Rebase过程中遇到冲突，请手动解决",
                    "conflict_resolution_hint": "使用 'git rebase --continue' 继续，'git rebase --abort' 取消，或 'git rebase --skip' 跳过当前提交"
                }
            else:
                return {
                    "status": "error",
                    "log": process.stdout + process.stderr,
                    "error": f"Git rebase失败: {process.stderr}"
                }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "log": e.stdout + e.stderr,
            "error": f"Git rebase失败: {e.stderr}"
        }
    except Exception as e:
        return {
            "status": "error",
            "log": "",
            "error": f"未知错误: {str(e)}"
        }

@mcp.tool()
def git_rebase(project_dir: str, source_branch: str, onto_branch: Optional[str] = None,
              interactive: bool = False, force: bool = False) -> Dict[str, Any]:
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
    return _git_rebase_internal(project_dir, source_branch, onto_branch, interactive, force)

if __name__ == "__main__":
    mcp.run()