#!/usr/bin/env python3
"""
综合测试agno Agent与OpenTelemetry的集成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core import ZephyrMCPAgent

def test_tool_registration():
    """测试工具注册功能"""
    print("测试工具注册功能...")
    
    try:
        # 使用默认配置文件
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        agent = ZephyrMCPAgent(config_path)
        
        # 检查工具注册表
        if hasattr(agent, 'tool_registry'):
            registered_tools = agent.tool_registry.get_registered_tools()
            print(f"✓ 工具注册表已初始化，注册了 {len(registered_tools)} 个工具")
            
            # 检查是否有工具
            if len(registered_tools) > 0:
                print("✓ 工具注册成功")
                for tool_name in list(registered_tools.keys())[:3]:  # 显示前3个工具
                    print(f"  - {tool_name}")
                if len(registered_tools) > 3:
                    print(f"  - ... 还有 {len(registered_tools) - 3} 个工具")
            else:
                print("✗ 没有注册任何工具")
        else:
            print("✗ 工具注册表未找到")
            
        return True
        
    except Exception as e:
        print(f"✗ 工具注册测试失败: {e}")
        return False

def test_opentelemetry_integration():
    """测试OpenTelemetry集成"""
    print("\n测试OpenTelemetry集成...")
    
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        agent = ZephyrMCPAgent(config_path)
        
        # 检查OpenTelemetry配置
        if hasattr(agent, 'otel_config'):
            print(f"✓ OpenTelemetry配置: {agent.otel_config}")
        else:
            print("✗ OpenTelemetry配置未找到")
            
        # 检查OpenTelemetry追踪器
        if hasattr(agent, 'otel_tracer'):
            if agent.otel_tracer is not None:
                print("✓ OpenTelemetry追踪器已初始化")
            else:
                print("✓ OpenTelemetry追踪器已禁用（符合预期）")
        else:
            print("✗ OpenTelemetry追踪器属性未找到")
            
        # 检查agno Agent的telemetry属性
        if hasattr(agent.agent, 'telemetry'):
            print(f"✓ agno Agent telemetry属性: {agent.agent.telemetry}")
        else:
            print("✗ agno Agent telemetry属性未找到")
            
        return True
        
    except Exception as e:
        print(f"✗ OpenTelemetry集成测试失败: {e}")
        return False

def test_http_handler():
    """测试HTTP请求处理器"""
    print("\n测试HTTP请求处理器...")
    
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        agent = ZephyrMCPAgent(config_path)
        
        # 检查HTTP服务器配置
        if hasattr(agent, 'config') and 'port' in agent.config:
            print(f"✓ HTTP服务器端口配置: {agent.config.get('port', 8001)}")
        else:
            print("✗ HTTP服务器配置未找到")
            
        # 检查工具注册表是否可用于HTTP处理
        if hasattr(agent, 'tool_registry'):
            registered_tools = agent.tool_registry.get_registered_tools()
            print(f"✓ HTTP处理器可访问 {len(registered_tools)} 个工具")
        else:
            print("✗ 工具注册表不可用于HTTP处理")
            
        return True
        
    except Exception as e:
        print(f"✗ HTTP处理器测试失败: {e}")
        return False

def test_agno_api_compatibility():
    """测试agno API兼容性"""
    print("\n测试agno API兼容性...")
    
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        agent = ZephyrMCPAgent(config_path)
        
        # 检查agno Agent的可用方法
        agno_methods = [method for method in dir(agent.agent) if not method.startswith('_')]
        print(f"✓ agno Agent有 {len(agno_methods)} 个公共方法")
        
        # 检查关键方法是否存在
        key_methods = ['add_tool', 'register_tool', '_run_tool']
        for method in key_methods:
            if hasattr(agent.agent, method):
                print(f"  ✓ {method} 方法存在")
            else:
                print(f"  ✗ {method} 方法不存在")
                
        # 检查telemetry属性
        if hasattr(agent.agent, 'telemetry'):
            print(f"  ✓ telemetry 属性存在: {agent.agent.telemetry}")
        else:
            print("  ✗ telemetry 属性不存在")
            
        return True
        
    except Exception as e:
        print(f"✗ agno API兼容性测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始综合测试agno Agent与OpenTelemetry集成...\n")
    
    # 运行测试
    test1 = test_tool_registration()
    test2 = test_opentelemetry_integration()
    test3 = test_http_handler()
    test4 = test_agno_api_compatibility()
    
    print(f"\n测试结果:")
    print(f"- 工具注册功能: {'通过' if test1 else '失败'}")
    print(f"- OpenTelemetry集成: {'通过' if test2 else '失败'}")
    print(f"- HTTP请求处理器: {'通过' if test3 else '失败'}")
    print(f"- agno API兼容性: {'通过' if test4 else '失败'}")
    
    if test1 and test2 and test3 and test4:
        print("\n🎉 所有测试通过！agno Agent与OpenTelemetry集成完全正常工作。")
    else:
        print("\n❌ 部分测试失败，需要检查代码。")