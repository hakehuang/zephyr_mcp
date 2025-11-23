#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重构后的代码是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """测试所有工具的导入是否正常"""
    print("测试工具导入...")
    
    # 测试从工具模块导入
    try:
        from src.tools.validate_west_init_params import validate_west_init_params
        from src.tools.west_flash import west_flash
        from src.tools.run_twister import run_twister
        from src.tools.git_checkout import git_checkout
        from src.tools.west_update import west_update
        from src.tools.switch_zephyr_version import switch_zephyr_version
        from src.tools.get_zephyr_status import get_zephyr_status
        from src.tools.git_redirect_zephyr_mirror import git_redirect_zephyr_mirror
        from src.tools.get_git_redirect_status import get_git_redirect_status
        from src.tools.set_git_credentials import set_git_credentials
        from src.tools.test_git_connection import test_git_connection
        from src.tools.get_git_config_status import get_git_config_status
        from src.tools.fetch_branch_or_pr import fetch_branch_or_pr
        from src.tools.git_rebase import git_rebase
        print("✓ 成功从工具模块导入所有工具")
    except ImportError as e:
        print(f"✗ 从工具模块导入失败: {e}")
        return False
    
    # 测试共享工具函数导入
    try:
        from src.utils.common_tools import (
            check_tools,
            run_command,
            format_error_message,
            is_git_repository,
            get_current_branch,
            parse_git_config
        )
        print("✓ 成功导入共享工具函数")
    except ImportError as e:
        print(f"✗ 导入共享工具函数失败: {e}")
        return False
    
    # 测试内部辅助函数导入
    try:
        from src.utils.internal_helpers import (
            _git_checkout_internal,
            _west_update_internal,
            _switch_zephyr_version_internal,
            _fetch_branch_or_pr_internal,
            _git_rebase_internal
        )
        print("✓ 成功导入内部辅助函数")
    except ImportError as e:
        print(f"✗ 导入内部辅助函数失败: {e}")
        return False
    
    return True

def test_common_tools():
    """测试共享工具函数的基本功能"""
    print("\n测试共享工具函数...")
    
    from src.utils.common_tools import check_tools, format_error_message
    
    # 测试check_tools函数
    tools_status = check_tools(["python", "git"])
    print(f"工具检查结果: {tools_status}")
    
    # 测试format_error_message函数
    error_msg = format_error_message("测试错误", "这是一个测试错误消息")
    print(f"格式化的错误消息: {error_msg}")
    
    return True

def main():
    """主测试函数"""
    print("开始测试重构后的代码...\n")
    
    success = True
    
    # 测试导入
    if not test_imports():
        success = False
    
    # 测试共享工具函数
    if not test_common_tools():
        success = False
    
    print("\n测试完成!")
    if success:
        print("✓ 所有测试通过")
        return 0
    else:
        print("✗ 测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())