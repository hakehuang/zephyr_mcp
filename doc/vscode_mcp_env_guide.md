# VS Code MCP 环境变量配置指南

## 当前配置分析

查看您的 `.vscode/mcp.json` 文件，目前的环境变量配置如下：

```json
"env": {
    "mcp_name": "ZephyrMcpServer"
}
```

## 如何添加 Git 认证环境变量

### 方法 1：直接在 mcp.json 中添加

修改 `.vscode/mcp.json` 文件，在 `env` 部分添加 Git 认证变量：

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
                    "mcp_name": "ZephyrMcpServer",
                    "GIT_USERNAME": "your_git_username",
                    "GIT_PASSWORD": "your_git_token_or_password"
                },
                "capabilities": {
                    // ... 其他配置保持不变
                }
            }
        }
    }
}
```

### 方法 2：使用更安全的方式

#### 选项 A：使用 VS Code 设置中的环境变量

1. 打开 VS Code 设置 (Ctrl+,)
2. 搜索 `terminal.integrated.env.windows`
3. 添加用户设置：

```json
{
    "terminal.integrated.env.windows": {
        "GIT_USERNAME": "your_git_username",
        "GIT_PASSWORD": "your_git_token_or_password"
    }
}
```

#### 选项 B：使用系统环境变量

在 Windows 系统中设置用户级别的环境变量：

```powershell
# 设置用户环境变量
[Environment]::SetEnvironmentVariable('GIT_USERNAME', 'your_git_username', 'User')
[Environment]::SetEnvironmentVariable('GIT_PASSWORD', 'your_git_token', 'User')
```

#### 选项 C：使用 .env 文件（推荐）

1. 在项目根目录创建 `.env` 文件：

```env
# .env 文件
GIT_USERNAME=your_git_username
GIT_PASSWORD=your_git_token_or_password
MCP_NAME=ZephyrMcpServer
```

2. 修改 MCP 服务器代码以加载 .env 文件（在 mcp_server.py 开头添加）：

```python
import os
from pathlib import Path

# 加载 .env 文件
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
```

## 配置优先级

环境变量的优先级（从高到低）：

1. **直接参数传递**：调用函数时直接提供的 username/token 参数
2. **mcp.json 中的 env 设置**：在 VS Code MCP 配置中设置的环境变量
3. **VS Code 终端环境变量**：在 VS Code 设置中配置的环境变量
4. **系统环境变量**：操作系统级别的环境变量
5. **默认值**：如果以上都没有设置，使用默认值 `"None"`

## 安全最佳实践

### 1. 不要在代码中硬编码凭据

```json
// ❌ 错误做法
"env": {
    "GIT_USERNAME": "my_real_username",
    "GIT_PASSWORD": "my_real_password123"
}
```

### 2. 使用占位符和文档说明

```json
// ✅ 正确做法
"env": {
    "mcp_name": "ZephyrMcpServer",
    "GIT_USERNAME": "${GIT_USERNAME}",
    "GIT_PASSWORD": "${GIT_PASSWORD}"
}
```

### 3. 使用 VS Code 的变量替换

VS Code 支持一些预定义变量：

- `${env:GIT_USERNAME}` - 引用系统环境变量
- `${workspaceFolder}` - 工作区文件夹路径
- `${userHome}` - 用户主目录

### 4. 创建配置模板

创建 `mcp.json.template` 文件：

```json
{
    "name": "Zephyr MCP Server",
    "env": {
        "mcp_name": "ZephyrMcpServer",
        "GIT_USERNAME": "YOUR_GIT_USERNAME_HERE",
        "GIT_PASSWORD": "YOUR_GIT_TOKEN_HERE"
    }
}
```

然后在使用前复制为 `mcp.json` 并填入实际值。

## 验证配置

### 方法 1：使用 MCP 工具验证

```python
# 验证环境变量是否设置正确
import os
print(f"GIT_USERNAME: {os.environ.get('GIT_USERNAME', '未设置')}")
print(f"GIT_PASSWORD: {'已设置' if os.environ.get('GIT_PASSWORD') else '未设置'}")
```

### 方法 2：使用 west_init 测试

```python
# 测试 west_init 函数
result = west_init(
    repo_url="https://github.com/zephyrproject-rtos/zephyr",
    branch="main", 
    project_dir="test-project",
    auth_method="env"  # 使用环境变量认证
)
print(result)
```

## 常见问题

### Q1: 环境变量不生效
**解决方案：**
1. 重启 VS Code
2. 检查环境变量名称是否正确（区分大小写）
3. 验证 MCP 服务器是否正确读取了环境变量

### Q2: 安全警告
**解决方案：**
1. 使用个人访问令牌（PAT）而不是密码
2. 定期更换令牌
3. 使用系统环境变量而不是硬编码在文件中

### Q3: 多用户共享配置
**解决方案：**
1. 使用系统环境变量
2. 创建用户特定的配置文件
3. 使用 `.env` 文件并添加到 `.gitignore`

## 推荐配置

**最安全的配置方式：**

1. **不要**在 `mcp.json` 中存储真实凭据
2. 使用系统环境变量
3. 在文档中说明需要设置的环境变量

**最终推荐的 mcp.json：**

```json
{
    "name": "Zephyr MCP Server",
    "description": "Model Context Protocol server for Zephyr RTOS development workflows",
    "env": {
        "mcp_name": "ZephyrMcpServer"
    }
}
```

**用户需要做的：**

在系统级别设置环境变量：

```powershell
# Windows
[Environment]::SetEnvironmentVariable('GIT_USERNAME', 'your_username', 'User')
[Environment]::SetEnvironmentVariable('GIT_PASSWORD', 'your_token', 'User')

# Linux/Mac
export GIT_USERNAME="your_username"
export GIT_PASSWORD="your_token"
```