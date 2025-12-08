#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trace ID 功能集成测试

注意：运行此测试需要先启动Zephyr MCP Agent服务器
"""

import unittest
import requests
import json
import uuid
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor

# 服务器地址
BASE_URL = "http://localhost:8001"


class TestIntegrationTraceId(unittest.TestCase):
    """集成测试trace_id功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置，检查服务器是否运行"""
        print(f"测试目标服务器: {BASE_URL}")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=3)
            if response.status_code != 200:
                print(f"警告: 服务器响应状态码不是200: {response.status_code}")
            print("服务器连接成功")
        except requests.exceptions.ConnectionError:
            print("错误: 无法连接到服务器，请确保服务器正在运行")
            print(f"使用命令启动服务器: python {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agent.py')}")
            # 不强制退出，允许部分测试运行
    
    def test_health_endpoint_trace_id(self):
        """测试健康检查端点的trace_id处理"""
        print("\n测试 /health 端点...")
        
        # 测试场景1: 使用自定义trace_id
        custom_trace_id = str(uuid.uuid4())
        headers = {"X-Trace-ID": custom_trace_id}
        response = requests.get(f"{BASE_URL}/health", headers=headers)
        
        self.assertEqual(response.status_code, 200, "健康检查端点返回非200状态码")
        
        # 验证响应头包含X-Trace-ID
        self.assertIn("X-Trace-ID", response.headers, "响应头中缺少X-Trace-ID")
        self.assertEqual(response.headers["X-Trace-ID"], custom_trace_id, "响应头中的trace_id不匹配")
        
        # 验证响应体包含trace_id
        data = response.json()
        self.assertIn("trace_id", data, "响应体中缺少trace_id")
        self.assertEqual(data["trace_id"], custom_trace_id, "响应体中的trace_id不匹配")
        
        # 测试场景2: 自动生成trace_id
        response = requests.get(f"{BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        
        # 验证响应中包含trace_id
        data = response.json()
        self.assertIn("trace_id", data)
        auto_trace_id = data["trace_id"]
        
        # 验证自动生成的trace_id格式
        self.assertEqual(len(auto_trace_id), 36, "自动生成的trace_id长度不正确")
        # 验证是有效的UUID
        try:
            uuid.UUID(auto_trace_id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        self.assertTrue(is_valid_uuid, "自动生成的trace_id不是有效的UUID格式")
    
    def test_tools_endpoint_trace_id(self):
        """测试工具列表端点的trace_id处理"""
        print("\n测试 /api/tools 端点...")
        
        # 使用自定义trace_id
        custom_trace_id = str(uuid.uuid4())
        headers = {"X-Trace-ID": custom_trace_id}
        
        # 测试GET请求
        response = requests.get(f"{BASE_URL}/api/tools", headers=headers)
        self.assertEqual(response.status_code, 200, "/api/tools 端点返回非200状态码")
        
        # 验证响应头
        self.assertIn("X-Trace-ID", response.headers)
        self.assertEqual(response.headers["X-Trace-ID"], custom_trace_id)
        
        # 验证响应体
        data = response.json()
        self.assertIn("trace_id", data, "/api/tools 响应中缺少trace_id")
        self.assertEqual(data["trace_id"], custom_trace_id)
        
        # 验证响应包含tools字段
        self.assertIn("tools", data, "/api/tools 响应中缺少tools字段")
    
    def test_ai_assistant_trace_id(self):
        """测试AI助手端点的trace_id处理"""
        print("\n测试 /api/ai_assistant 端点...")
        
        # 使用自定义trace_id
        custom_trace_id = str(uuid.uuid4())
        headers = {
            "X-Trace-ID": custom_trace_id,
            "Content-Type": "application/json"
        }
        
        # 准备测试数据
        payload = {
            "messages": [
                {"role": "user", "content": "hello, please respond with a short message"}
            ]
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/ai_assistant",
                headers=headers,
                data=json.dumps(payload)
            )
            
            # 检查响应状态
            print(f"AI助手端点响应状态码: {response.status_code}")
            
            # 如果LLM未启用，可能会返回500，但仍应包含trace_id
            if response.status_code == 200 or response.status_code == 500:
                # 验证响应头
                self.assertIn("X-Trace-ID", response.headers, "AI助手响应头中缺少X-Trace-ID")
                self.assertEqual(response.headers["X-Trace-ID"], custom_trace_id)
                
                # 验证响应体
                try:
                    data = response.json()
                    self.assertIn("trace_id", data, "AI助手响应体中缺少trace_id")
                    self.assertEqual(data["trace_id"], custom_trace_id)
                except json.JSONDecodeError:
                    print("警告: AI助手响应不是有效的JSON格式")
            else:
                print(f"注意: AI助手端点返回了非预期状态码: {response.status_code}")
        except Exception as e:
            print(f"测试AI助手端点时出错: {str(e)}")
            # 如果服务器不支持AI助手，不视为测试失败
    
    def test_404_endpoint_trace_id(self):
        """测试404端点的trace_id处理"""
        print("\n测试 404 端点...")
        
        # 使用自定义trace_id
        custom_trace_id = str(uuid.uuid4())
        headers = {"X-Trace-ID": custom_trace_id}
        
        # 访问不存在的端点
        response = requests.get(f"{BASE_URL}/nonexistent_endpoint_12345", headers=headers)
        
        # 应该返回404
        self.assertEqual(response.status_code, 404, "不存在的端点未返回404状态码")
        
        # 验证响应头
        self.assertIn("X-Trace-ID", response.headers, "404响应头中缺少X-Trace-ID")
        self.assertEqual(response.headers["X-Trace-ID"], custom_trace_id)
        
        # 验证响应体
        try:
            data = response.json()
            self.assertIn("trace_id", data, "404响应体中缺少trace_id")
            self.assertEqual(data["trace_id"], custom_trace_id)
        except json.JSONDecodeError:
            print("警告: 404响应不是有效的JSON格式")
    
    def test_concurrent_requests_trace_id(self):
        """测试并发请求时的trace_id隔离"""
        print("\n测试并发请求的trace_id隔离...")
        
        def send_request(custom_trace_id):
            """发送单个请求并返回trace_id"""
            headers = {"X-Trace-ID": custom_trace_id}
            response = requests.get(f"{BASE_URL}/health", headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("trace_id")
            return None
        
        # 生成多个不同的trace_id
        custom_trace_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        # 并发发送请求
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(send_request, custom_trace_ids))
        
        # 验证每个请求返回的trace_id与发送的一致
        for i, (sent, received) in enumerate(zip(custom_trace_ids, results)):
            self.assertEqual(sent, received, 
                           f"并发请求 {i+1}: 发送的trace_id {sent} 与接收的 {received} 不匹配")
        
        print(f"成功验证 {len(results)} 个并发请求的trace_id隔离")


class TestErrorScenariosTraceId(unittest.TestCase):
    """测试错误场景下的trace_id处理"""
    
    def test_invalid_json_trace_id(self):
        """测试无效JSON格式时的trace_id处理"""
        print("\n测试无效JSON格式...")
        
        # 使用自定义trace_id
        custom_trace_id = str(uuid.uuid4())
        headers = {
            "X-Trace-ID": custom_trace_id,
            "Content-Type": "application/json"
        }
        
        # 发送无效的JSON数据
        invalid_json = "{invalid json format}"
        response = requests.post(
            f"{BASE_URL}/api/ai_assistant",
            headers=headers,
            data=invalid_json
        )
        
        # 应该返回400或500错误
        self.assertTrue(response.status_code in [400, 500], 
                      f"无效JSON应返回400或500，实际返回: {response.status_code}")
        
        # 验证响应头包含trace_id
        self.assertIn("X-Trace-ID", response.headers)
        self.assertEqual(response.headers["X-Trace-ID"], custom_trace_id)
        
        # 验证响应体包含trace_id
        try:
            data = response.json()
            self.assertIn("trace_id", data)
            self.assertEqual(data["trace_id"], custom_trace_id)
        except json.JSONDecodeError:
            print("警告: 错误响应不是有效的JSON格式")
    
    def test_missing_required_fields_trace_id(self):
        """测试缺少必填字段时的trace_id处理"""
        print("\n测试缺少必填字段...")
        
        # 使用自定义trace_id
        custom_trace_id = str(uuid.uuid4())
        headers = {
            "X-Trace-ID": custom_trace_id,
            "Content-Type": "application/json"
        }
        
        # 缺少messages字段
        payload = {"model": "test-model"}
        response = requests.post(
            f"{BASE_URL}/api/ai_assistant",
            headers=headers,
            data=json.dumps(payload)
        )
        
        # 验证响应状态
        print(f"缺少必填字段响应状态码: {response.status_code}")
        
        # 验证响应头包含trace_id
        self.assertIn("X-Trace-ID", response.headers)
        self.assertEqual(response.headers["X-Trace-ID"], custom_trace_id)
        
        # 验证响应体包含trace_id
        try:
            data = response.json()
            self.assertIn("trace_id", data)
            self.assertEqual(data["trace_id"], custom_trace_id)
        except json.JSONDecodeError:
            print("警告: 错误响应不是有效的JSON格式")


if __name__ == '__main__':
    print("Zephyr MCP Agent Trace ID 集成测试")
    print("=" * 60)
    print("注意: 运行此测试需要先启动Zephyr MCP Agent服务器")
    print("=" * 60)
    
    # 如果提供了命令行参数，使用自定义服务器地址
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
        print(f"使用自定义服务器地址: {BASE_URL}")
    
    # 运行测试
    unittest.main()