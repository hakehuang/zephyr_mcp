#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 测试/health端点是否存在
import urllib.request
import json

def test_health_endpoint():
    try:
        response = urllib.request.urlopen('http://localhost:8001/health', timeout=2)
        print(f"状态码: {response.status}")
        content = response.read().decode('utf-8')
        print(f"响应内容: {content}")
        try:
            data = json.loads(content)
            print(f"JSON数据: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError:
            print("响应不是JSON格式")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    test_health_endpoint()
