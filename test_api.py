import requests
import json

# 测试工具调用API
def test_tool_call():
    url = "http://localhost:8000/api/tool"
    headers = {"Content-Type": "application/json"}
    data = {
        "tool": "test_git_connection",
        "params": {
            "repo_url": "https://github.com/zephyrproject-rtos/zephyr"
        }
    }
    
    print(f"发送请求到: {url}")
    print(f"请求数据: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # 尝试解析JSON响应
        try:
            json_response = response.json()
            print(f"JSON响应: {json.dumps(json_response, indent=2)}")
        except json.JSONDecodeError:
            print("警告: 响应不是有效的JSON格式")
            
    except requests.exceptions.Timeout:
        print("错误: 请求超时")
    except requests.exceptions.RequestException as e:
        print(f"错误: 请求失败 - {str(e)}")

# 测试工具信息API
def test_tool_info():
    url = "http://localhost:8000/api/tool/info?name=test_git_connection"
    print(f"\n发送请求到: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"错误: 请求失败 - {str(e)}")

if __name__ == "__main__":
    print("=== 测试工具信息API ===")
    test_tool_info()
    
    print("\n=== 测试工具调用API ===")
    test_tool_call()