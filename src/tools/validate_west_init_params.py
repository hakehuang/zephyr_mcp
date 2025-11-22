#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_west_init_params - Validate west init parameters and provide helpful suggestions
"""

from typing import Dict, Any, Optional
import os
import re
import subprocess

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

from ..utils.common_tools import check_tools, ensure_directory_exists, run_command

# 内部函数：验证west init参数
def _west_init_core(repo_url: Optional[str] = None, branch: Optional[str] = None, 
                   project_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    内部函数，验证west init参数的有效性
    """
    # 验证Git仓库URL
    if repo_url:
        # 基本的Git URL格式验证
        git_url_pattern = re.compile(r'^(https?://|git@|ssh://).*\.(git)?$')
        if not git_url_pattern.match(repo_url):
            return {"status": "error", "suggestion": "仓库URL格式不正确，请提供有效的Git仓库URL"}
    
    # 验证分支名称
    if branch:
        # 分支名称不能包含某些特殊字符
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ', '\t']
        if any(char in branch for char in invalid_chars):
            return {"status": "error", "suggestion": "分支名称包含无效字符，请使用合法的分支名称"}
    
    # 验证项目目录
    if project_dir:
        # 检查目录是否已存在
        if os.path.exists(project_dir):
            # 检查目录是否为空
            if os.listdir(project_dir):
                return {"status": "warning", "suggestion": "项目目录已存在且不为空，可能会覆盖现有内容"}
    
    # 检查west工具是否安装
    tools_status = check_tools(["west"])
    if not tools_status.get("west", False):
        return {"status": "error", "suggestion": "未找到west工具，请确保已正确安装Zephyr SDK"}
    
    return {"status": "success", "suggestion": "参数验证通过"}

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
    # 验证认证方法
    valid_auth_methods = ["embedded", "http", "ssh"]
    if auth_method not in valid_auth_methods:
        return {"status": "error", "suggestion": f"无效的认证方法，支持的方法: {', '.join(valid_auth_methods)}"}
    
    # 调用内部函数进行核心验证
    return _west_init_core(repo_url, branch, project_dir)