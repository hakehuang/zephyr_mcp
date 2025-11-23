#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试trace_id功能的脚本
"""

import json
import requests
import uuid
import time
import sys
import os

BASE_URL = "http://localhost:8000"


def test_trace_id_functionality():
    """测试所有端点的trace_id功能"""
    print("开始测试trace_id功能...")
    print("=" * 50)
    
    # 测试场景1：发送带有X-Trace-ID头的请求
    custom_trace_id = str(uuid.uuid4())
    print(f"\n测试场景1：使用自定义trace_id: {custom_trace_id}")
    
    # 测试健康检查端点
    headers = {"X-Trace-ID": custom_trace_id}
    response = requests.get(f"{BASE_URL}/health", headers=headers)
    print(f"/health 响应状态码: {response.status_code}")
    health_data = response.json()
    print(f"/health 响应中的trace_id: {health_data.get('trace_id')}")
    print(f"响应头中的X-Trace-ID: {response.headers.get('X-Trace-ID')}")
    assert health_data.get('trace_id') == custom_trace_id, "自定义trace_id不匹配"
    
    # 测试工具列表端点
    response = requests.get(f"{BASE_URL}/api/tools", headers=headers)
    print(f"\n/api/tools 响应状态码: {response.status_code}")
    tools_data = response.json()
    print(f"/api/tools 响应中的trace_id: {tools_data.get('trace_id')}")
    assert tools_data.get('trace_id') == custom_trace_id, "自定义trace_id不匹配"
    
    # 测试场景2：不发送X-Trace-ID头，应该自动生成
    print("\n" + "=" * 50)
    print("测试场景2：自动生成trace_id")
    
    # 测试健康检查端点
    response = requests.get(f"{BASE_URL}/health")
    print(f"/health 响应状态码: {response.status_code}")
    health_data = response.json()
    auto_trace_id = health_data.get('trace_id')
    print(f"自动生成的trace_id: {auto_trace_id}")
    assert auto_trace_id is not None, "自动生成的trace_id不应为None"
    assert len(auto_trace_id) == 36, "自动生成的trace_id格式不正确"
    
    # 测试场景3：测试404端点，确认错误响应也包含trace_id
    print("\n" + "=" * 50)
    print("测试场景3：错误响应中的trace_id")
    
    custom_trace_id = str(uuid.uuid4())
    headers = {"X-Trace-ID": custom_trace_id}
    response = requests.get(f"{BASE_URL}/nonexistent", headers=headers)
    print(f"/nonexistent 响应状态码: {response.status_code}")
    try:
        error_data = response.json()
        print(f"错误响应中的trace_id: {error_data.get('trace_id')}")
        assert error_data.get('trace_id') == custom_trace_id, "错误响应中的trace_id不匹配"
    except json.JSONDecodeError:
        print("警告: 错误响应不是有效的JSON格式")
    
    # 测试场景4：如果LLM启用，测试AI助手端点
    print("\n" + "=" * 50)
    print("测试场景4：AI助手端点的trace_id (如果LLM已启用)")
    
    custom_trace_id = str(uuid.uuid4())
    headers = {"X-Trace-ID": custom_trace_id, "Content-Type": "application/json"}
    payload = {
        "messages": [
            {"role": "user", "content": "hello"}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/ai_assistant", 
                               headers=headers, 
                               data=json.dumps(payload))
        print(f"/api/ai_assistant 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            ai_data = response.json()
            print(f"AI助手响应中的trace_id: {ai_data.get('trace_id')}")
            assert ai_data.get('trace_id') == custom_trace_id, "AI助手响应中的trace_id不匹配"
        elif response.status_code == 500:
            print("注意: AI助手返回500错误，可能是LLM未配置或未启用")
        else:
            print(f"注意: AI助手返回非预期状态码: {response.status_code}")
    except Exception as e:
        print(f"测试AI助手端点时出错: {str(e)}")
    
    print("\n" + "=" * 50)
    print("trace_id功能测试完成！")
    print("请检查服务器日志，确认日志中包含正确的trace_id")


if __name__ == "__main__":
    print("Zephyr MCP Agent trace_id功能测试脚本")
    print(f"测试目标服务器: {BASE_URL}")
    print("\n注意: 请确保服务器正在运行，否则测试将失败")
    print("建议先启动服务器: python agent.py")
    
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
        print(f"使用自定义服务器地址: {BASE_URL}")
    
    try:
        # 先检查服务器是否可访问
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"服务器健康检查: {'成功' if response.status_code == 200 else '失败'}")
        
        # 运行测试
        test_trace_id_functionality()
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器，请确保服务器正在运行")
        print("使用方法:")
        print(f"1. 启动服务器: python agent.py")
        print(f"2. 运行测试: python {os.path.basename(__file__)}")
        sys.exit(1)
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)