#!/usr/bin/env python3
"""
MCP 环境变量获取指南
展示 zephyr_mcp 如何从环境变量获取认证信息
"""

import os

def show_env_variables():
    """显示当前环境变量设置"""
    print("=== MCP 环境变量配置指南 ===\n")
    
    # 检查当前环境变量
    git_username = os.environ.get("GIT_USERNAME", "未设置")
    git_password = os.environ.get("GIT_PASSWORD", "未设置")
    
    print("1. 当前环境变量状态:")
    print(f"   GIT_USERNAME: {git_username}")
    print(f"   GIT_PASSWORD: {'*' * len(git_password) if git_password != '未设置' else '未设置'}")
    
    print("\n2. 环境变量获取逻辑:")
    print("   在 west_init_interactive 函数中:")
    print("   - 当 username 参数为 None 时")
    print("   - 系统会自动从环境变量获取:")
    print("     username = os.environ.get('GIT_USERNAME', 'None')")
    print("     token = os.environ.get('GIT_PASSWORD', 'None')")
    
    print("\n3. 认证方法 (auth_method):")
    print("   - embedded: 将凭据嵌入URL中")
    print("   - env: 使用环境变量认证")
    print("   - config: 使用Git配置认证")
    
    print("\n4. 设置环境变量方法:")
    print("\n   Windows PowerShell:")
    print("   # 临时设置（当前会话有效）")
    print("   $env:GIT_USERNAME = 'your_username'")
    print("   $env:GIT_PASSWORD = 'your_token'")
    
    print("\n   # 永久设置（用户级别）")
    print("   [Environment]::SetEnvironmentVariable('GIT_USERNAME', 'your_username', 'User')")
    print("   [Environment]::SetEnvironmentVariable('GIT_PASSWORD', 'your_token', 'User')")
    
    print("\n   Windows CMD:")
    print("   # 临时设置")
    print("   set GIT_USERNAME=your_username")
    print("   set GIT_PASSWORD=your_token")
    
    print("\n   Linux/Mac:")
    print("   # 临时设置")
    print("   export GIT_USERNAME='your_username'")
    print("   export GIT_PASSWORD='your_token'")
    
    print("\n   # 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）")
    print("   echo 'export GIT_USERNAME=\"your_username\"' >> ~/.bashrc")
    print("   echo 'export GIT_PASSWORD=\"your_token\"' >> ~/.bashrc")
    print("   source ~/.bashrc")
    
    print("\n5. 使用示例:")
    print("   # 在 Python 中设置")
    print("   os.environ['GIT_USERNAME'] = 'your_username'")
    print("   os.environ['GIT_PASSWORD'] = 'your_token'")
    
    print("\n6. 验证设置:")
    print("   # 检查是否设置成功")
    print("   python -c \"import os; print(os.environ.get('GIT_USERNAME'))\"")
    
    print("\n=== 指南完成 ===")

def demo_env_usage():
    """演示环境变量的使用"""
    print("\n=== 环境变量使用演示 ===\n")
    
    # 模拟 west_init_interactive 中的逻辑
    def simulate_west_init(username=None, token=None):
        print(f"输入参数 - username: {username}, token: {'*' * len(token) if token else None}")
        
        # 如果参数为 None，从环境变量获取
        if username is None:
            username = os.environ.get("GIT_USERNAME", "None")
            print(f"从环境变量获取 username: {username}")
        
        if token is None:
            token = os.environ.get("GIT_PASSWORD", "None")
            print(f"从环境变量获取 token: {'*' * len(token) if token != 'None' else 'None'}")
        
        return username, token
    
    print("场景1: 直接提供参数")
    sim_username, sim_token = simulate_west_init("direct_user", "direct_token")
    
    print("\n场景2: 使用环境变量")
    # 临时设置环境变量用于演示
    os.environ["GIT_USERNAME"] = "env_user"
    os.environ["GIT_PASSWORD"] = "env_token"
    sim_username, sim_token = simulate_west_init()
    
    print("\n场景3: 混合使用")
    sim_username, sim_token = simulate_west_init(username="partial_user")

if __name__ == "__main__":
    show_env_variables()
    demo_env_usage()