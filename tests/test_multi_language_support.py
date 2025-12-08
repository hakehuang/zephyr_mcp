#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多语言支持测试文件
测试语言资源和翻译功能是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # 导入语言资源模块
    from src.utils.language_resources import (
        get_text,
        set_language,
        get_current_language,
        get_available_languages,
        LanguageManager
    )
    
    print("[OK] 成功导入语言资源模块")
except ImportError as e:
    print(f"[ERROR] 导入语言资源模块失败: {e}")
    sys.exit(1)

def test_available_languages():
    """测试可用语言列表"""
    print("\n=== 测试可用语言列表 ===")
    try:
        available_langs = get_available_languages()
        print(f"可用语言: {available_langs}")
        assert 'zh' in available_langs, "中文语言包缺失"
        assert 'en' in available_langs, "英文语言包缺失"
        print("[PASS] 可用语言测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] 可用语言测试失败: {e}")
        return False

def test_language_switching():
    """测试语言切换功能"""
    print("\n=== 测试语言切换功能 ===")
    try:
        # 测试默认语言
        default_lang = get_current_language()
        print(f"默认语言: {default_lang}")
        
        # 切换到英文
        set_language('en')
        en_lang = get_current_language()
        print(f"切换到英文: {en_lang}")
        assert en_lang == 'en', "未能切换到英文"
        
        # 切换到中文
        set_language('zh')
        zh_lang = get_current_language()
        print(f"切换到中文: {zh_lang}")
        assert zh_lang == 'zh', "未能切换到中文"
        
        print("[PASS] 语言切换测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] 语言切换测试失败: {e}")
        return False

def test_translation_retrieval():
    """测试翻译文本检索"""
    print("\n=== 测试翻译文本检索 ===")
    try:
        # 测试中文翻译
        set_language('zh')
        zh_text = get_text('server_started')
        print(f"中文: {zh_text}")
        assert zh_text == "JSON API服务器已启动: http://{}", "中文翻译错误"
        
        # 测试英文翻译
        set_language('en')
        en_text = get_text('server_started')
        print(f"英文: {en_text}")
        assert en_text == "JSON API server started: http://{}", "英文翻译错误"
        
        # 测试带参数的翻译
        test_param = "test_tool"
        zh_param_text = get_text('tool_register_error', test_param, "error_message")
        en_param_text = get_text('tool_register_error', test_param, "error_message")
        print(f"带参数中文: {zh_param_text}")
        print(f"带参数英文: {en_param_text}")
        assert test_param in zh_param_text, "中文参数替换失败"
        assert test_param in en_param_text, "英文参数替换失败"
        
        print("[PASS] 翻译文本检索测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] 翻译文本检索测试失败: {e}")
        return False

def test_language_manager_initialization():
    """测试语言管理器初始化"""
    print("\n=== 测试语言管理器初始化 ===")
    try:
        # 测试默认初始化
        manager = LanguageManager()
        print(f"默认管理器语言: {manager.get_language()}")
        
        # 测试指定语言初始化
        manager_en = LanguageManager('en')
        print(f"英文管理器语言: {manager_en.get_language()}")
        assert manager_en.get_language() == 'en', "语言管理器初始化失败"
        
        print("[PASS] 语言管理器初始化测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] 语言管理器初始化测试失败: {e}")
        return False

def test_missing_translation():
    """测试缺失翻译的处理"""
    print("\n=== 测试缺失翻译的处理 ===")
    try:
        # 测试不存在的键
        missing_key = "non_existent_key_12345"
        result = get_text(missing_key)
        print(f"缺失键 '{missing_key}' 的返回值: {result}")
        assert result == missing_key, "缺失翻译处理不正确"
        
        print("[PASS] 缺失翻译处理测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] 缺失翻译处理测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("[LANGUAGE] Zephyr MCP 多语言支持测试")
    print("=" * 50)
    
    tests = [
        test_available_languages,
        test_language_switching,
        test_translation_retrieval,
        test_language_manager_initialization,
        test_missing_translation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 测试通过")
    print("=" * 50)
    
    if passed == total:
        print("[SUCCESS] 所有测试通过！")
        return True
    else:
        print(f"[WARN] 有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
