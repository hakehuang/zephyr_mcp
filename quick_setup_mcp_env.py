#!/usr/bin/env python3
"""
快速设置 Zephyr MCP 环境变量
"""

import os
import json
import platform
import subprocess
from pathlib import Path

def quick_setup():
    """快速设置环境变量"""
    print("🚀 Zephyr MCP 环境变量快速设置")
    print("=" * 40)
    
    # 1. 检查当前状态
    print("\n📊 当前状态检查:")
    git_username = os.environ.get('GIT_USERNAME', '')
    git_password = os.environ.get('GIT_PASSWORD', '')
    
    print(f"GIT_USERNAME: {'✅ 已设置' if git_username else '❌ 未设置'}")
    print(f"GIT_PASSWORD: {'✅ 已设置' if git_password else '❌ 未设置'}")
    
    # 2. 获取用户输入
    print("\n🔧 请输入 Git 认证信息:")
    
    if not git_username:
        username = input("Git 用户名: ").strip()
    else:
        print(f"当前 GIT_USERNAME: {git_username}")
        change = input("是否修改? (y/N): ").strip().lower()
        username = input("新用户名: ").strip() if change == 'y' else git_username
    
    if not git_password:
        password = input("Git 令牌/密码: ").strip()
    else:
        print("当前 GIT_PASSWORD: 已设置")
        change = input("是否修改? (y/N): ").strip().lower()
        password = input("新令牌/密码: ").strip() if change == 'y' else git_password
    
    if not username or not password:
        print("❌ 用户名和密码不能为空")
        return False
    
    # 3. 设置系统环境变量
    print("\n⚙️  设置系统环境变量...")
    
    system = platform.system()
    
    if system == "Windows":
        try:
            # 设置用户环境变量
            subprocess.run([
                'powershell', '-Command',
                f'[Environment]::SetEnvironmentVariable("GIT_USERNAME", "{username}", "User")'
            ], check=True)
            
            subprocess.run([
                'powershell', '-Command',
                f'[Environment]::SetEnvironmentVariable("GIT_PASSWORD", "{password}", "User")'
            ], check=True)
            
            print("✅ Windows 环境变量设置完成")
            print("💡 请重启 VS Code 使设置生效")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 设置 Windows 环境变量失败: {e}")
            return False
    
    else:  # Linux/Mac
        try:
            home = Path.home()
            
            # 检测 shell 类型
            shell_rc = home / '.bashrc'
            if not shell_rc.exists():
                shell_rc = home / '.zshrc'
            
            # 添加到 shell 配置文件
            with open(shell_rc, 'a') as f:
                f.write(f'\n# Zephyr MCP 环境变量 - 添加于 {platform.system()}\n')
                f.write(f'export GIT_USERNAME="{username}"\n')
                f.write(f'export GIT_PASSWORD="{password}"\n')
            
            print(f"✅ {system} 环境变量已添加到 {shell_rc}")
            print("💡 请运行 'source ~/.bashrc' 或重启终端使设置生效")
            
        except Exception as e:
            print(f"❌ 设置 {system} 环境变量失败: {e}")
            return False
    
    # 4. 创建安全配置
    print("\n🔒 创建安全配置...")
    
    vscode_dir = Path('.vscode')
    mcp_config_file = vscode_dir / 'mcp.json'
    
    if mcp_config_file.exists():
        try:
            # 读取当前配置
            with open(mcp_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新为安全配置
            mcp_server = config.get('mcp', {}).get('servers', {}).get('zephyr-mcp', {})
            if 'env' not in mcp_server:
                mcp_server['env'] = {}
            
            mcp_server['env'].update({
                'mcp_name': 'ZephyrMcpServer',
                'GIT_USERNAME': '${env:GIT_USERNAME}',
                'GIT_PASSWORD': '${env:GIT_PASSWORD}'
            })
            
            # 备份原文件
            backup_file = mcp_config_file.with_suffix('.json.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # 写入新配置
            with open(mcp_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            print("✅ 安全配置创建完成")
            print(f"📁 备份文件: {backup_file}")
            
        except Exception as e:
            print(f"⚠️  创建安全配置时出错: {e}")
            print("您可以手动编辑 .vscode/mcp.json 文件")
    
    # 5. 验证设置
    print("\n🔍 验证设置...")
    
    # 重新加载环境变量
    if system == "Windows":
        # Windows 需要重启 VS Code 才能生效
        print("💡 Windows 系统需要重启 VS Code 来加载新环境变量")
    else:
        # Linux/Mac 可以尝试重新加载
        try:
            subprocess.run(['bash', '-c', 'source ~/.bashrc && echo $GIT_USERNAME'], 
                         capture_output=True, text=True)
        except:
            pass
    
    print("\n🎉 快速设置完成！")
    print("\n下一步:")
    print("1. 重启 VS Code")
    print("2. 验证 MCP 工具是否正常工作")
    print("3. 使用 west_init 工具测试 Git 认证")
    
    return True

def show_usage():
    """显示使用说明"""
    print("""
Zephyr MCP 环境变量快速设置脚本

使用方法:
    python quick_setup_mcp_env.py

功能:
    - 快速设置 Git 认证环境变量
    - 创建安全的 MCP 配置
    - 自动检测操作系统并应用适当设置
    - 备份现有配置文件

支持的认证方式:
    - embedded: 使用内嵌认证
    - env: 使用环境变量认证（推荐）
    - config: 使用 Git 配置认证

环境变量:
    GIT_USERNAME: Git 用户名
    GIT_PASSWORD: Git 个人访问令牌或密码
    mcp_name: MCP 服务器名称

注意事项:
    - Windows 用户需要重启 VS Code
    - Linux/Mac 用户需要重启终端或运行 source ~/.bashrc
    - 建议使用 Git 个人访问令牌而不是密码
""")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        show_usage()
    else:
        try:
            quick_setup()
        except KeyboardInterrupt:
            print("\n\n❌ 用户取消操作")
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            print("请检查错误信息并重新运行")