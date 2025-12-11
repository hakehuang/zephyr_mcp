#!/usr/bin/env python3
"""
测试agent_core.py的双语支持功能 / Test bilingual support functionality in agent_core.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core import ZephyrMCPAgent

def test_language_switching():
    """测试语言切换功能"""
    print("=== 测试语言切换功能 ===")
    
    try:
        # 创建agent实例
        agent = ZephyrMCPAgent("config.json")
        
        # 测试获取语言信息
        language_info = agent.get_language_info()
        print(f"✓ 当前语言: {language_info['current']} ({language_info['name']})")
        
        # 测试获取可用语言
        available_languages = agent.get_available_languages()
        print(f"✓ 可用语言: {available_languages}")
        
        # 测试切换到英文
        if agent.switch_language("en"):
            print("✓ 成功切换到英文")
            print(f"✓ 当前语言: {agent.get_language_info()['current']}")
        else:
            print("✗ 切换到英文失败")
            return False
        
        # 测试切换回中文
        if agent.switch_language("zh"):
            print("✓ 成功切换回中文")
            print(f"✓ 当前语言: {agent.get_language_info()['current']}")
        else:
            print("✗ 切换回中文失败")
            return False
        
        # 测试无效语言
        if not agent.switch_language("fr"):
            print("✓ 正确处理无效语言")
        else:
            print("✗ 未正确处理无效语言")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ 语言切换测试失败: {e}")
        return False

def test_bilingual_text():
    """测试双语文本功能"""
    print("\n=== 测试双语文本功能 ===")
    
    try:
        # 创建agent实例
        agent = ZephyrMCPAgent("config.json")
        
        # 测试获取双语文本
        bilingual_text = agent.get_bilingual_text("starting_agent", "Test Agent", "1.0.0")
        print("✓ 双语文本获取成功:")
        print(f"  中文: {bilingual_text['zh']}")
        print(f"  英文: {bilingual_text['en']}")
        
        # 测试多个文本
        test_keys = ["registering_tools", "tools_registered", "available_tools"]
        for key in test_keys:
            bilingual_text = agent.get_bilingual_text(key)
            print(f"✓ {key}: {bilingual_text['zh']} / {bilingual_text['en']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 双语文本测试失败: {e}")
        return False

def test_language_display():
    """测试语言信息显示"""
    print("\n=== 测试语言信息显示 ===")
    
    try:
        # 创建agent实例
        agent = ZephyrMCPAgent("config.json")
        
        # 测试显示语言信息
        print("✓ 显示语言信息:")
        agent.display_language_info()
        
        # 测试切换到英文后显示
        agent.switch_language("en")
        print("\n✓ 切换到英文后显示语言信息:")
        agent.display_language_info()
        
        return True
        
    except Exception as e:
        print(f"✗ 语言信息显示测试失败: {e}")
        return False

def test_bilingual_documentation():
    """测试双语文档生成"""
    print("\n=== 测试双语文档生成 ===")
    
    try:
        # 创建agent实例
        agent = ZephyrMCPAgent("config.json")
        
        # 注册工具
        agent.register_tools()
        
        # 测试生成双语文档
        if agent.generate_bilingual_documentation("./test_bilingual_docs.md"):
            print("✓ 双语文档生成成功")
            
            # 检查文件是否存在
            if os.path.exists("./test_bilingual_docs.md"):
                print("✓ 双语文档文件已创建")
                
                # 读取文件内容检查
                with open("./test_bilingual_docs.md", 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "工具文档 / Tool Documentation" in content:
                        print("✓ 双语文档内容正确")
                    else:
                        print("✗ 双语文档内容不正确")
                        return False
            else:
                print("✗ 双语文档文件未创建")
                return False
        else:
            print("✗ 双语文档生成失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ 双语文档生成测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试agent_core.py的双语支持功能...\n")
    
    # 运行测试
    test1 = test_language_switching()
    test2 = test_bilingual_text()
    test3 = test_language_display()
    test4 = test_bilingual_documentation()
    
    print(f"\n=== 测试结果 ===")
    print(f"- 语言切换功能: {'通过' if test1 else '失败'}")
    print(f"- 双语文本功能: {'通过' if test2 else '失败'}")
    print(f"- 语言信息显示: {'通过' if test3 else '失败'}")
    print(f"- 双语文档生成: {'通过' if test4 else '失败'}")
    
    if test1 and test2 and test3 and test4:
        print("\n🎉 所有双语支持功能测试通过！")
    else:
        print("\n❌ 部分双语支持功能测试失败，需要检查代码。")
    
    # 清理测试文件
    if os.path.exists("./test_bilingual_docs.md"):
        os.remove("./test_bilingual_docs.md")
        print("✓ 清理测试文件完成")