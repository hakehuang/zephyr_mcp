#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重构后的代码是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试所有工具的导入是否正常"""
    print("测试工具导入...")
    success = True
    
    # 测试工具函数导入（逐个导入，提高错误定位精确度）
    tool_imports = [
        ('src.tools.validate_west_init_params', 'validate_west_init_params'),
        ('src.tools.west_flash', 'west_flash'),
        ('src.tools.run_twister', 'run_twister'),
        ('src.tools.git_checkout', 'git_checkout'),
        ('src.tools.west_update', 'west_update'),
        ('src.tools.switch_zephyr_version', 'switch_zephyr_version'),
        ('src.tools.get_zephyr_status', 'get_zephyr_status'),
        ('src.tools.git_redirect_zephyr_mirror', 'git_redirect_zephyr_mirror'),
        ('src.tools.get_git_redirect_status', 'get_git_redirect_status'),
        ('src.tools.set_git_credentials', 'set_git_credentials'),
        ('src.tools.test_git_connection', 'test_git_connection'),
        ('src.tools.get_git_config_status', 'get_git_config_status'),
        ('src.tools.fetch_branch_or_pr', 'fetch_branch_or_pr'),
        ('src.tools.git_rebase', 'git_rebase')
    ]
    
    print("\n测试工具函数导入:")
    imported_tools = []
    for module, name in tool_imports:
        try:
            __import__(module)
            module_obj = sys.modules[module]
            getattr(module_obj, name)
            imported_tools.append(name)
            # 避免打印过多信息，只显示成功数量
        except ImportError as e:
            print(f"✗ {module} 导入失败: {e}")
            success = False
        except AttributeError as e:
            print(f"✗ {module} 中找不到 {name}: {e}")
            success = False
    
    print(f"✓ 成功导入 {len(imported_tools)}/{len(tool_imports)} 个工具函数")
    
    # 测试共享工具函数导入（关键函数）
    try:
        from src.utils.common_tools import check_tools, run_command, format_error_message
        print("✓ 成功导入关键共享工具函数")
    except ImportError as e:
        print(f"✗ 导入关键共享工具函数失败: {e}")
        success = False
    
    # 内部辅助函数导入不是必须的，即使失败也继续测试
    try:
        from src.utils.internal_helpers import _git_checkout_internal
        print("✓ 成功导入示例内部辅助函数")
    except ImportError as e:
        print(f"⚠️  导入内部辅助函数失败: {e} (可选，继续测试)")
    
    return success

def test_common_tools():
    """测试共享工具函数的基本功能"""
    print("\n测试共享工具函数...")
    
    try:
        from src.utils.common_tools import check_tools, format_error_message
        
        # 测试check_tools函数 - 使用Python作为必选工具，git作为可选工具
        tools_status = check_tools(["python"])
        print(f"工具检查结果 (Python): {tools_status}")
        
        # 测试format_error_message函数
        error_msg = format_error_message("测试错误", "这是一个测试错误消息")
        print(f"格式化的错误消息: {error_msg}")
        
        return True
    except Exception as e:
        print(f"⚠️  共享工具函数测试遇到问题: {e} (继续测试)")
        return False

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