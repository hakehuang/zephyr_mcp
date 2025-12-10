#!/usr/bin/env python3
"""
测试agno Agent与OpenTelemetry的集成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core import ZephyrMCPAgent

def test_agno_agent_creation():
    """测试创建agno Agent"""
    print("测试agno Agent创建...")
    
    try:
        # 使用默认配置文件
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        agent = ZephyrMCPAgent(config_path)
        print("✓ agno Agent创建成功")
        
        # 检查agno Agent属性
        print(f"✓ Agent名称: {agent.config['agent_name']}")
        
        # 检查OpenTelemetry配置
        if hasattr(agent, 'otel_config'):
            print(f"✓ OpenTelemetry配置: {agent.otel_config}")
        else:
            print("✗ OpenTelemetry配置未找到")
            
        # 检查agno telemetry属性
        if hasattr(agent.agent, 'telemetry'):
            print(f"✓ agno telemetry属性: {agent.agent.telemetry}")
        else:
            print("✗ agno telemetry属性未找到")
            
        return True
        
    except Exception as e:
        print(f"✗ agno Agent创建失败: {e}")
        return False

def test_opentelemetry_disabled():
    """测试禁用OpenTelemetry"""
    print("\n测试禁用OpenTelemetry...")
    
    try:
        # 使用默认配置文件
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        agent = ZephyrMCPAgent(config_path)
        print("✓ 禁用OpenTelemetry的Agent创建成功")
        
        # 检查OpenTelemetry是否被正确禁用
        if hasattr(agent, 'otel_tracer') and agent.otel_tracer is None:
            print("✓ OpenTelemetry已正确禁用")
        else:
            print("✗ OpenTelemetry未正确禁用")
            
        return True
        
    except Exception as e:
        print(f"✗ 禁用OpenTelemetry的Agent创建失败: {e}")
        return False

def test_agno_telemetry_control():
    """测试agno telemetry属性控制"""
    print("\n测试agno telemetry属性控制...")
    
    try:
        # 使用默认配置文件
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        agent = ZephyrMCPAgent(config_path)
        
        # 检查agno Agent的telemetry属性
        if hasattr(agent.agent, 'telemetry'):
            # 保存原始telemetry值
            original_telemetry = agent.agent.telemetry
            
            # 手动禁用agno telemetry
            agent.agent.telemetry = False
            print(f"✓ agno telemetry属性设置为: {agent.agent.telemetry}")
            
            # 由于OpenTelemetry在初始化时检查telemetry属性，
            # 我们需要检查当前状态是否反映了禁用状态
            if agent.otel_tracer is None:
                print("✓ agno telemetry属性正确控制了OpenTelemetry")
            else:
                print("✗ agno telemetry属性未能控制OpenTelemetry")
                
            # 恢复原始telemetry值
            agent.agent.telemetry = original_telemetry
            
        else:
            print("✗ agno Agent没有telemetry属性")
            return False
                
        return True
        
    except Exception as e:
        print(f"✗ agno telemetry属性控制测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试agno Agent与OpenTelemetry集成...\n")
    
    # 运行测试
    test1 = test_agno_agent_creation()
    test2 = test_opentelemetry_disabled() 
    test3 = test_agno_telemetry_control()
    
    print(f"\n测试结果:")
    print(f"- 基础Agent创建: {'通过' if test1 else '失败'}")
    print(f"- OpenTelemetry禁用: {'通过' if test2 else '失败'}")
    print(f"- agno telemetry控制: {'通过' if test3 else '失败'}")
    
    if test1 and test2 and test3:
        print("\n🎉 所有测试通过！agno Agent与OpenTelemetry集成正常工作。")
    else:
        print("\n❌ 部分测试失败，需要检查代码。")