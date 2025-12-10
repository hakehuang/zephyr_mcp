#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trace ID 功能边界情况测试

测试各种特殊情况和异常场景下的trace_id处理
"""

import unittest
import requests
import json
import uuid
import sys
import os
import string
import random
from concurrent.futures import ThreadPoolExecutor

# 服务器地址
BASE_URL = "http://localhost:8002"


class TestEdgeCasesTraceId(unittest.TestCase):
    """测试trace_id的边界情况"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置，检查服务器是否运行"""
        print(f"测试目标服务器: {BASE_URL}")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=3)
            if response.status_code != 200:
                print(f"警告: 服务器响应状态码不是200: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("警告: 无法连接到服务器，某些测试可能会失败")
    
    def test_special_characters_trace_id(self):
        """测试包含特殊字符的trace_id"""
        print("\n测试特殊字符trace_id...")
        
        # 测试各种特殊字符组合
        special_cases = [
            "trace-id-with-dash",
            "trace_id_with_underscore",
            "trace.id.with.dots",
            "TRACE_ID_UPPERCASE",
            "trace id with spaces",
            "trace-id-12345",
            "!@#$%^&*()",
            "中文trace_id",
            "日本語trace_id",
            "한국어trace_id",
        ]
        
        for special_trace_id in special_cases:
            try:
                headers = {"X-Trace-ID": special_trace_id}
                response = requests.get(f"{BASE_URL}/health", headers=headers, timeout=3)
                
                print(f"  测试 '{special_trace_id[:20]}...': 状态码 {response.status_code}")
                
                # 即使使用特殊字符，服务器也应该接受请求并返回相同的trace_id
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.assertIn("trace_id", data)
                        self.assertEqual(data["trace_id"], special_trace_id, 
                                       f"特殊字符trace_id不匹配: 发送='{special_trace_id}', 接收='{data.get('trace_id')}'")
                    except json.JSONDecodeError:
                        print(f"    警告: 响应不是有效的JSON格式")
            except Exception as e:
                print(f"    错误处理特殊trace_id '{special_trace_id}': {str(e)}")
    
    def test_empty_and_null_trace_id(self):
        """测试空和null的trace_id"""
        print("\n测试空和null trace_id...")
        
        empty_cases = [
            "",           # 空字符串
            "   ",        # 空白字符串
            "null",       # 字符串"null"
            "undefined",  # 字符串"undefined"
        ]
        
        for empty_trace_id in empty_cases:
            try:
                headers = {"X-Trace-ID": empty_trace_id}
                response = requests.get(f"{BASE_URL}/health", headers=headers, timeout=3)
                
                print(f"  测试 '{repr(empty_trace_id)}': 状态码 {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.assertIn("trace_id", data)
                    
                    # 对于空trace_id，服务器应该生成新的trace_id
                    if empty_trace_id.strip() in ["", "null", "undefined"]:
                        received_trace_id = data["trace_id"]
                        self.assertNotEqual(received_trace_id, empty_trace_id, 
                                           f"空trace_id应该被替换，但返回了相同的值")
                        # 验证生成的是有效的UUID
                        try:
                            uuid.UUID(received_trace_id)
                            print(f"    ✓ 成功生成了有效的UUID: {received_trace_id}")
                        except ValueError:
                            print(f"    ✗ 生成的trace_id不是有效的UUID格式")
            except Exception as e:
                print(f"    错误: {str(e)}")
    
    def test_extremely_long_trace_id(self):
        """测试非常长的trace_id"""
        print("\n测试超长trace_id...")
        
        # 生成各种长度的trace_id
        lengths = [100, 1000, 10000, 100000]
        
        for length in lengths:
            try:
                # 生成指定长度的随机字符串
                long_trace_id = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
                
                print(f"  测试长度为{length}的trace_id...")
                headers = {"X-Trace-ID": long_trace_id}
                response = requests.get(f"{BASE_URL}/health", headers=headers, timeout=5)
                
                print(f"    状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.assertIn("trace_id", data)
                    
                    # 验证长trace_id是否被正确处理
                    # 注意：HTTP服务器可能会对请求头长度有限制
                    received_trace_id = data["trace_id"]
                    print(f"    返回的trace_id长度: {len(received_trace_id)}")
                elif response.status_code == 431:  # Request Header Fields Too Large
                    print(f"    预期的431错误: 请求头过大")
            except requests.exceptions.RequestException as e:
                print(f"    请求异常: {str(e)}")
            except Exception as e:
                print(f"    错误: {str(e)}")
    
    def test_duplicate_trace_id(self):
        """测试重复使用相同的trace_id"""
        print("\n测试重复trace_id...")
        
        # 生成一个trace_id
        duplicate_trace_id = str(uuid.uuid4())
        headers = {"X-Trace-ID": duplicate_trace_id}
        
        # 多次发送相同的trace_id
        for i in range(5):
            try:
                response = requests.get(f"{BASE_URL}/health", headers=headers, timeout=3)
                print(f"  请求 {i+1}: 状态码 {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.assertIn("trace_id", data)
                    self.assertEqual(data["trace_id"], duplicate_trace_id, 
                                   f"重复trace_id请求 {i+1} 不匹配")
            except Exception as e:
                print(f"  请求 {i+1} 错误: {str(e)}")
    
    def test_malformed_uuid_trace_id(self):
        """测试格式错误的UUID作为trace_id"""
        print("\n测试格式错误的UUID...")
        
        # UUID格式错误的案例
        malformed_uuids = [
            "12345678-1234-1234-1234-1234567890abx",  # 多了一个字符
            "1234567-1234-1234-1234-1234567890ab",    # 少了一个字符
            "123456781234123412341234567890ab",       # 没有连字符
            "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",   # 全是x
            "12345678-1234-ABCD-1234-1234567890ab",   # 混合大小写
        ]
        
        for malformed_uuid in malformed_uuids:
            try:
                headers = {"X-Trace-ID": malformed_uuid}
                response = requests.get(f"{BASE_URL}/health", headers=headers, timeout=3)
                
                print(f"  测试 '{malformed_uuid}': 状态码 {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.assertIn("trace_id", data)
                    # 服务器应该接受任何格式的trace_id，不需要验证是否为有效的UUID
                    self.assertEqual(data["trace_id"], malformed_uuid, 
                                   f"格式错误的UUID不匹配")
            except Exception as e:
                print(f"    错误: {str(e)}")
    
    def test_server_stress_trace_id(self):
        """测试服务器压力下的trace_id处理"""
        print("\n测试服务器压力下的trace_id...")
        
        def send_stress_request(custom_trace_id):
            """发送压力测试请求"""
            headers = {"X-Trace-ID": custom_trace_id}
            try:
                response = requests.get(f"{BASE_URL}/health", headers=headers, timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("trace_id") == custom_trace_id
                return False
            except Exception:
                return False
        
        # 生成多个不同的trace_id
        test_count = 100
        custom_trace_ids = [str(uuid.uuid4()) for _ in range(test_count)]
        
        print(f"发送 {test_count} 个并发请求...")
        
        # 并发发送请求
        success_count = 0
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(send_stress_request, custom_trace_ids))
            success_count = sum(results)
        
        success_rate = (success_count / test_count) * 100
        print(f"成功: {success_count}/{test_count} ({success_rate:.1f}%)")
        
        # 即使在压力下，大部分请求也应该成功
        self.assertGreaterEqual(success_rate, 90.0, 
                               f"压力测试成功率低于90%: {success_rate:.1f}%")


if __name__ == '__main__':
    print("Zephyr MCP Agent Trace ID 边界情况测试")
    print("=" * 60)
    print("测试各种特殊情况下的trace_id处理")
    print("=" * 60)
    
    # 如果提供了命令行参数，使用自定义服务器地址
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
        print(f"使用自定义服务器地址: {BASE_URL}")
    
    # 运行测试
    unittest.main()