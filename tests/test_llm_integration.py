#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM集成功能测试脚本
用于验证LLM模块的导入和基本功能
"""
import sys
import os
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_llm_import():
    """
    测试LLM模块的导入
    """
    logger.info("测试LLM模块导入...")
    try:
        # 尝试导入LLM集成模块
        from src.utils.llm_integration import LLMIntegration
        from src.tools.llm_tools import init_llm, get_llm, get_llm_status, get_registered_tools
        logger.info("[OK] LLM模块导入成功")
        return True
    except ImportError as e:
        logger.error(f"[ERROR] LLM模块导入失败: {str(e)}")
        return False

def test_llm_initialization():
    """
    测试LLM集成的初始化
    """
    logger.info("测试LLM集成初始化...")
    try:
        from src.utils.llm_integration import LLMIntegration
        
        # 加载配置文件
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 初始化LLM集成
        llm_config = config.get('llm', {})
        llm = LLMIntegration(llm_config)
        
        # 验证配置加载
        logger.info(f"[OK] LLM集成初始化成功")
        logger.info(f"  - 配置内容: {json.dumps(llm_config, indent=2, ensure_ascii=False)}")
        
        # 获取状态信息
        status = llm.get_status()
        logger.info(f"  - 状态信息: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        return True
    except Exception as e:
        logger.error(f"[ERROR] LLM集成初始化失败: {str(e)}")
        return False

def test_llm_tools_registration():
    """
    测试LLM工具的注册信息
    """
    logger.info("测试LLM工具注册信息...")
    try:
        from src.tools.llm_tools import get_registered_tools
        
        tools = get_registered_tools()
        logger.info(f"[OK] 获取LLM工具列表成功")
        logger.info(f"  - 可用工具数量: {len(tools)}")
        
        for tool_name, tool_info in tools.items():
            logger.info(f"  - 工具: {tool_name}")
            logger.info(f"    描述: {tool_info['description']}")
            logger.info(f"    参数数量: {len(tool_info.get('params', []))}")
        
        return True
    except Exception as e:
        logger.error(f"[ERROR] 获取LLM工具列表失败: {str(e)}")
        return False

def test_agent_integration():
    """
    测试与agent的集成
    """
    logger.info("测试与agent的集成...")
    try:
        # 检查agent.py是否包含LLM相关代码
        with open('agent.py', 'r', encoding='utf-8') as f:
            agent_content = f.read()
        
        # 检查关键字
        keywords = [
            'from src.utils.llm_integration import LLMIntegration',
            'from src.tools.llm_tools import',
            'ai_assistant',
            'llm_integration',
            'register_llm_tools'
        ]
        
        found_keywords = 0
        for keyword in keywords:
            if keyword in agent_content:
                found_keywords += 1
                logger.info(f"  [OK] 找到关键字: {keyword}")
            else:
                logger.warning(f"  [WARN] 未找到关键字: {keyword}")
        
        if found_keywords >= 3:  # 至少找到3个关键字才算基本成功
            logger.info(f"[OK] Agent集成检查通过 (找到{found_keywords}/{len(keywords)}个关键字)")
            return True
        else:
            logger.warning(f"[WARN] Agent集成可能不完整 (仅找到{found_keywords}/{len(keywords)}个关键字)")
            return False
    except Exception as e:
        logger.error(f"[ERROR] Agent集成检查失败: {str(e)}")
        return False

def print_usage_instructions():
    """
    打印使用说明
    """
    print("\n=== LLM集成使用说明 ===")
    print("1. 设置环境变量:")
    print("   - OpenAI API: 设置 OPENAI_API_KEY 环境变量")
    print("   - Anthropic API: 设置 ANTHROPIC_API_KEY 环境变量")
    print("\n2. 启动Agent:")
    print("   python agent.py")
    print("\n3. 使用AI助手功能:")
    print("   - 发送POST请求到 /api/ai_assistant 端点")
    print("   - 支持的工具: generate_text, analyze_code, explain_error, llm_chat, get_llm_status")
    print("\n4. 示例请求:")
    print("   {")
    print("     'tool': 'generate_text',")
    print("     'params': {")
    print("       'prompt': 'Hello, how can I help you today?',")
    print("       'model': 'gpt-4-turbo',")
    print("       'max_tokens': 500,")
    print("       'temperature': 0.7")
    print("     }")
    print("   }")

def main():
    """
    主测试函数
    """
    print("\n=== LLM集成功能测试 ===\n")
    
    # 运行所有测试
    tests = [
        ('模块导入测试', test_llm_import),
        ('LLM初始化测试', test_llm_initialization),
        ('工具注册测试', test_llm_tools_registration),
        ('Agent集成测试', test_agent_integration)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        if test_func():
            passed_tests += 1
    
    # 打印测试结果摘要
    print("\n=== 测试结果摘要 ===")
    print(f"通过测试: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("[OK] 所有测试通过! LLM集成配置成功。")
    else:
        print(f"[WARN] 有{total_tests - passed_tests}个测试未通过，请检查配置。")
    
    # 打印使用说明
    print_usage_instructions()
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)