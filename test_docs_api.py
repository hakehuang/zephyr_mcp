import requests
import json

# 测试API文档端点
def test_api_docs():
    url = "http://localhost:8000/api/docs"
    print(f"发送请求到: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"响应状态码: {response.status_code}")
        
        # 尝试解析JSON响应
        try:
            json_response = response.json()
            print("\nAPI文档响应:")
            print(json.dumps(json_response, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print("警告: 响应不是有效的JSON格式")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.Timeout:
        print("错误: 请求超时")
    except requests.exceptions.RequestException as e:
        print(f"错误: 请求失败 - {str(e)}")

if __name__ == "__main__":
    print("=== 测试API文档端点 ===")
    test_api_docs()