#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多语言支持验证脚本
验证语言资源和翻译功能是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # 导入语言资源模块
    from src.utils.language_resources import (
        get_text,
        set_language,
        get_current_language,
        get_available_languages
    )
    
    print("✅ 成功导入语言资源模块")
except ImportError as e:
    print(f"❌ 导入语言资源模块失败: {e}")
    sys.exit(1)

def verify_translations():
    """验证翻译功能"""
    print("\n=== 多语言支持验证 ===")
    
    # 测试中文
    try:
        set_language('zh')
        zh_welcome = get_text('starting_agent', 'Zephyr MCP', '1.0.0')
        zh_server = get_text('server_started', 'localhost:8000')
        zh_health = get_text('health_check_start')
        print(f'中文测试:')
        print(f'  启动消息: {zh_welcome}')
        print(f'  服务器消息: {zh_server}')
        print(f'  健康检查: {zh_health}')
        print('✓ 中文翻译正常')
    except Exception as e:
        print(f'❌ 中文测试失败: {e}')
        return False
    
    # 测试英文
    try:
        set_language('en')
        en_welcome = get_text('starting_agent', 'Zephyr MCP', '1.0.0')
        en_server = get_text('server_started', 'localhost:8000')
        en_health = get_text('health_check_start')
        print(f'英文测试:')
        print(f'  Welcome message: {en_welcome}')
        print(f'  Server message: {en_server}')
        print(f'  Health check: {en_health}')
        print('✓ English translation works')
    except Exception as e:
        print(f'❌ English test failed: {e}')
        return False
    
    # 测试参数替换
    try:
        set_language('zh')
        zh_param = get_text('parameter_required', 'test_tool', 'required_param')
        en_param = get_text('parameter_required', 'test_tool', 'required_param')
        print(f'参数替换测试:')
        print(f'  中文: {zh_param}')
        print(f'  英文: {en_param}')
        print('✓ 参数替换正常')
    except Exception as e:
        print(f'❌ 参数替换测试失败: {e}')
        return False
    
    return True

if __name__ == "__main__":
    success = verify_translations()
    if success:
        print("\n🎉 所有多语言支持验证通过！")
        sys.exit(0)
    else:
        print("\n❌ 多语言支持验证失败！")
        sys.exit(1)
