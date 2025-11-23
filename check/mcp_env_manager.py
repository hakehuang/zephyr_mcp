#!/usr/bin/env python3
"""
Zephyr MCP 环境变量配置工具
用于管理和验证 MCP 环境变量设置
"""

import os
import json
import platform
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

class MCPEnvManager:
    """MCP 环境变量管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.vscode_dir = self.project_root / '.vscode'
        self.mcp_config_file = self.vscode_dir / 'mcp.json'
        self.env_file = self.project_root / '.env'
        
    def check_current_config(self) -> Dict:
        """检查当前 MCP 配置"""
        if not self.mcp_config_file.exists():
            return {"error": "MCP 配置文件不存在"}
        
        try:
            with open(self.mcp_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 提取环境变量配置
            mcp_server = config.get('mcp', {}).get('servers', {}).get('zephyr-mcp', {})
            env_config = mcp_server.get('env', {})
            
            return {
                "config": config,
                "env_config": env_config,
                "has_hardcoded_creds": self._has_hardcoded_credentials(env_config),
                "uses_env_vars": self._uses_env_references(env_config)
            }
        except Exception as e:
            return {"error": f"读取配置文件失败: {e}"}
    
    def _has_hardcoded_credentials(self, env_config: Dict) -> bool:
        """检查是否有硬编码的凭据"""
        git_username = env_config.get('GIT_USERNAME', '')
        git_password = env_config.get('GIT_PASSWORD', '')
        
        # 如果有值且不是变量引用格式，则认为是硬编码
        return (git_username and not git_username.startswith('${')) or \
               (git_password and not git_password.startswith('${'))
    
    def _uses_env_references(self, env_config: Dict) -> bool:
        """
        Check if environment variable references are used
        检查是否使用了环境变量引用
        """
        git_username = env_config.get('GIT_USERNAME', '')
        git_password = env_config.get('GIT_PASSWORD', '')
        
        return (git_username and '${env:' in git_username) or \
               (git_password and '${env:' in git_password)
    
    def get_system_env_vars(self) -> Dict:
        """
        Get system environment variables
        获取系统环境变量
        """
        return {
            'GIT_USERNAME': os.environ.get('GIT_USERNAME', '未设置'),
            'GIT_PASSWORD': '已设置' if os.environ.get('GIT_PASSWORD') else '未设置',
            'mcp_name': os.environ.get('mcp_name', '未设置')
        }
    
    def create_secure_config(self) -> bool:
        """创建安全的配置文件"""
        try:
            # 读取当前配置
            with open(self.mcp_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新环境变量配置
            mcp_server = config.get('mcp', {}).get('servers', {}).get('zephyr-mcp', {})
            if 'env' not in mcp_server:
                mcp_server['env'] = {}
            
            # 设置安全的配置
            mcp_server['env'].update({
                'mcp_name': 'ZephyrMcpServer',
                'GIT_USERNAME': '${env:GIT_USERNAME}',
                'GIT_PASSWORD': '${env:GIT_PASSWORD}'
            })
            
            # 备份原文件
            backup_file = self.mcp_config_file.with_suffix('.json.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # 写入新配置
            with open(self.mcp_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            print(f"✅ 已创建安全配置文件")
            print(f"📁 备份文件: {backup_file}")
            return True
            
        except Exception as e:
            print(f"❌ 创建安全配置失败: {e}")
            return False
    
    def create_env_file_template(self) -> bool:
        """创建环境变量模板文件"""
        env_template = """# Zephyr MCP 环境变量配置
# 请将 YOUR_GIT_USERNAME 和 YOUR_GIT_TOKEN 替换为实际值

# Git 认证信息
GIT_USERNAME=YOUR_GIT_USERNAME
GIT_PASSWORD=YOUR_GIT_TOKEN

# MCP 服务器名称
MCP_NAME=ZephyrMcpServer

# 调试选项（可选）
# DEBUG=true
# LOG_LEVEL=INFO
"""
        
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write(env_template)
            
            print(f"✅ 已创建环境变量模板文件: {self.env_file}")
            return True
        except Exception as e:
            print(f"❌ 创建环境变量模板失败: {e}")
            return False
    
    def set_system_env_vars(self, username: str, password: str) -> bool:
        """设置系统环境变量"""
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows 系统
                subprocess.run([
                    'powershell', '-Command',
                    f'[Environment]::SetEnvironmentVariable("GIT_USERNAME", "{username}", "User")'
                ], check=True)
                
                subprocess.run([
                    'powershell', '-Command', 
                    f'[Environment]::SetEnvironmentVariable("GIT_PASSWORD", "{password}", "User")'
                ], check=True)
                
                print("✅ Windows 系统环境变量设置完成")
                print("💡 请重启 VS Code 使环境变量生效")
                
            else:
                # Linux/Mac 系统
                home = Path.home()
                shell_rc = home / '.bashrc'
                
                if not shell_rc.exists():
                    shell_rc = home / '.zshrc'
                
                with open(shell_rc, 'a') as f:
                    f.write(f'\n# Zephyr MCP 环境变量\n')
                    f.write(f'export GIT_USERNAME="{username}"\n')
                    f.write(f'export GIT_PASSWORD="{password}"\n')
                
                print(f"✅ {system} 系统环境变量已添加到 {shell_rc}")
                print("💡 请运行 'source ~/.bashrc' 或重启终端使环境变量生效")
            
            return True
            
        except Exception as e:
            print(f"❌ 设置系统环境变量失败: {e}")
            return False
    
    def validate_setup(self) -> Tuple[bool, str]:
        """验证环境变量设置"""
        # 检查系统环境变量
        sys_env = self.get_system_env_vars()
        
        # 检查配置文件
        config_check = self.check_current_config()
        
        if "error" in config_check:
            return False, config_check["error"]
        
        # 检查是否有硬编码凭据
        if config_check.get("has_hardcoded_creds", False):
            return False, "配置文件包含硬编码凭据，请使用安全配置"
        
        # 检查系统环境变量
        if sys_env['GIT_USERNAME'] == '未设置':
            return False, "系统环境变量 GIT_USERNAME 未设置"
        
        if sys_env['GIT_PASSWORD'] == '未设置':
            return False, "系统环境变量 GIT_PASSWORD 未设置"
        
        return True, "环境变量配置正确"
    
    def print_status(self):
        """打印当前状态"""
        print("=" * 50)
        print("Zephyr MCP 环境变量状态检查")
        print("=" * 50)
        
        # 系统环境变量
        print("\n🔧 系统环境变量:")
        sys_env = self.get_system_env_vars()
        for key, value in sys_env.items():
            status = "✅" if value != "未设置" else "❌"
            print(f"  {status} {key}: {value}")
        
        # 配置文件检查
        print("\n📄 配置文件检查:")
        config_check = self.check_current_config()
        
        if "error" in config_check:
            print(f"❌ {config_check['error']}")
        else:
            env_config = config_check.get("env_config", {})
            print(f"✅ 找到配置文件: {self.mcp_config_file}")
            print(f"📝 环境变量配置: {env_config}")
            
            if config_check.get("has_hardcoded_creds", False):
                print("⚠️  警告: 配置文件包含硬编码凭据")
            
            if config_check.get("uses_env_vars", False):
                print("✅ 使用了环境变量引用")
        
        # 验证结果
        is_valid, message = self.validate_setup()
        print(f"\n🔍 验证结果: {'✅' if is_valid else '❌'} {message}")
        
        print("\n" + "=" * 50)

def main():
    """主函数"""
    manager = MCPEnvManager()
    
    while True:
        print("\nZephyr MCP 环境变量管理工具")
        print("1. 查看当前状态")
        print("2. 创建安全配置")
        print("3. 创建环境变量模板")
        print("4. 设置系统环境变量")
        print("5. 验证配置")
        print("6. 退出")
        
        choice = input("\n请选择操作 (1-6): ").strip()
        
        if choice == '1':
            manager.print_status()
        
        elif choice == '2':
            if manager.create_secure_config():
                print("✅ 安全配置创建完成！")
        
        elif choice == '3':
            if manager.create_env_file_template():
                print("✅ 环境变量模板创建完成！")
                print("💡 请编辑 .env 文件并填入实际值")
        
        elif choice == '4':
            username = input("请输入 Git 用户名: ").strip()
            password = input("请输入 Git 令牌/密码: ").strip()
            
            if username and password:
                if manager.set_system_env_vars(username, password):
                    print("✅ 系统环境变量设置完成！")
            else:
                print("❌ 用户名和密码不能为空")
        
        elif choice == '5':
            is_valid, message = manager.validate_setup()
            print(f"\n🔍 验证结果: {'✅' if is_valid else '❌'} {message}")
        
        elif choice == '6':
            print("👋 再见！")
            break
        
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main()