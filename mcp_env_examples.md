# MCP 环境变量配置示例文件

## 示例 1：基础配置（安全）

```json
{
    "name": "Zephyr MCP Server",
    "description": "Model Context Protocol server for Zephyr RTOS development workflows",
    "version": "1.0.0",
    "mcp": {
        "servers": {
            "zephyr-mcp": {
                "command": "python",
                "args": ["${workspaceFolder}/src/mcp_server.py"],
                "env": {
                    "mcp_name": "ZephyrMcpServer"
                },
                "capabilities": {
                    "tools": [
                        {
                            "name": "west_init",
                            "description": "Initialize a Zephyr project using west tool",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "repo_url": {
                                        "type": "string",
                                        "description": "Repository URL"
                                    },
                                    "branch": {
                                        "type": "string",
                                        "description": "Branch name"
                                    },
                                    "project_dir": {
                                        "type": "string",
                                        "description": "Project directory"
                                    },
                                    "auth_method": {
                                        "type": "string",
                                        "description": "Authentication method"
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
}
```

## 示例 2：使用占位符（推荐）

```json
{
    "name": "Zephyr MCP Server",
    "env": {
        "mcp_name": "ZephyrMcpServer",
        "GIT_USERNAME": "${env:GIT_USERNAME}",
        "GIT_PASSWORD": "${env:GIT_PASSWORD}"
    }
}
```

## 示例 3：开发环境配置

```json
{
    "name": "Zephyr MCP Server (Dev)",
    "env": {
        "mcp_name": "ZephyrMcpServer",
        "GIT_USERNAME": "dev_user",
        "GIT_PASSWORD": "dev_token",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG"
    }
}
```

## 示例 4：生产环境配置

```json
{
    "name": "Zephyr MCP Server (Prod)",
    "env": {
        "mcp_name": "ZephyrMcpServer",
        "GIT_USERNAME": "${env:GIT_USERNAME}",
        "GIT_PASSWORD": "${env:GIT_PASSWORD}",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO"
    }
}
```

## 环境变量设置脚本

### Windows PowerShell 设置脚本

```powershell
# set_env.ps1
Write-Host "设置 Zephyr MCP 环境变量..."

# 临时设置（当前会话）
$env:GIT_USERNAME = Read-Host "请输入 Git 用户名"
$env:GIT_PASSWORD = Read-Host "请输入 Git 令牌/密码" -AsSecureString

# 永久设置（用户级别）
[Environment]::SetEnvironmentVariable('GIT_USERNAME', $env:GIT_USERNAME, 'User')
[Environment]::SetEnvironmentVariable('GIT_PASSWORD', [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($env:GIT_PASSWORD)), 'User')

Write-Host "环境变量设置完成！"
```

### Linux/Mac 设置脚本

```bash
#!/bin/bash
# set_env.sh

echo "设置 Zephyr MCP 环境变量..."

read -p "请输入 Git 用户名: " GIT_USERNAME
read -sp "请输入 Git 令牌/密码: " GIT_PASSWORD
echo

# 临时设置
export GIT_USERNAME="$GIT_USERNAME"
export GIT_PASSWORD="$GIT_PASSWORD"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo "export GIT_USERNAME=\"$GIT_USERNAME\"" >> ~/.bashrc
echo "export GIT_PASSWORD=\"$GIT_PASSWORD\"" >> ~/.bashrc

echo "环境变量设置完成！"
```

## 验证脚本

```python
# verify_env.py
import os
import json

def verify_environment():
    """验证环境变量配置"""
    
    print("=== MCP 环境变量验证 ===")
    
    # 检查基本环境变量
    mcp_name = os.environ.get('mcp_name', '未设置')
    git_username = os.environ.get('GIT_USERNAME', '未设置')
    git_password = '已设置' if os.environ.get('GIT_PASSWORD') else '未设置'
    
    print(f"mcp_name: {mcp_name}")
    print(f"GIT_USERNAME: {git_username}")
    print(f"GIT_PASSWORD: {git_password}")
    
    # 检查 MCP 配置文件
    try:
        with open('.vscode/mcp.json', 'r') as f:
            config = json.load(f)
            env_config = config.get('mcp', {}).get('servers', {}).get('zephyr-mcp', {}).get('env', {})
            
            print(f"\n=== MCP 配置文件 ===")
            print(f"配置文件中的环境变量: {env_config}")
            
            # 检查是否使用了安全的方式
            if '${env:' in str(env_config):
                print("✅ 使用了安全的变量引用方式")
            else:
                print("⚠️  直接设置了环境变量值，考虑使用变量引用")
                
    except FileNotFoundError:
        print("❌ 未找到 .vscode/mcp.json 配置文件")
    except json.JSONDecodeError:
        print("❌ MCP 配置文件格式错误")
    
    # 测试 west 初始化
    print(f"\n=== west 初始化测试 ===")
    try:
        from src.mcp_server import west_init
        
        # 测试参数验证
        result = west_init(
            repo_url="https://github.com/zephyrproject-rtos/zephyr",
            branch="main",
            project_dir="test-env-project",
            auth_method="env"
        )
        
        print(f"west_init 结果: {result}")
        
    except Exception as e:
        print(f"west_init 测试失败: {e}")

if __name__ == "__main__":
    verify_environment()
```

## 最佳实践总结

1. **安全性优先**：不要在配置文件中存储真实凭据
2. **使用变量引用**：使用 `${env:VARIABLE_NAME}` 语法
3. **分层配置**：为不同环境（开发、测试、生产）创建不同配置
4. **文档化**：记录需要设置的环境变量
5. **验证配置**：提供验证脚本来检查配置是否正确
6. **版本控制**：将敏感信息排除在版本控制之外

## 快速开始步骤

1. **选择配置模板**：从上面的示例中选择适合的配置
2. **设置系统环境变量**：
   ```powershell
   # Windows
   [Environment]::SetEnvironmentVariable('GIT_USERNAME', 'your_username', 'User')
   [Environment]::SetEnvironmentVariable('GIT_PASSWORD', 'your_token', 'User')
   ```
3. **验证配置**：运行验证脚本确保一切正常
4. **重启 VS Code**：确保环境变量生效

这样配置后，您的 MCP 服务器就可以安全地使用环境变量进行 Git 认证了！