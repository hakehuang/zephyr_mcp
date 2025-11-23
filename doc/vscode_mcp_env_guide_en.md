# VS Code MCP Environment Variable Configuration Guide

## Current Configuration Analysis

Looking at your `.vscode/mcp.json` file, the current environment variable configuration is as follows:

```json
"env": {
    "mcp_name": "ZephyrMcpServer"
}
```

## How to Add Git Authentication Environment Variables

### Method 1: Direct Addition in mcp.json

Modify the `.vscode/mcp.json` file to add Git authentication variables in the `env` section:

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
                    // ... other configurations remain unchanged
                }
            }
        }
    }
}
```

### Method 2: Using More Secure Methods

#### Option A: Using Environment Variables in VS Code Settings

1. Open VS Code settings (Ctrl+,)
2. Search for `terminal.integrated.env.windows`
3. Add user settings:

```json
{
    "terminal.integrated.env.windows": {
        "GIT_USERNAME": "your_git_username",
        "GIT_PASSWORD": "your_git_token_or_password"
    }
}
```

#### Option B: Using System Environment Variables

Set user-level environment variables in Windows system:

```powershell
# Set user environment variables
[Environment]::SetEnvironmentVariable('GIT_USERNAME', 'your_git_username', 'User')
[Environment]::SetEnvironmentVariable('GIT_PASSWORD', 'your_git_token', 'User')
```

#### Option C: Using .env File (Recommended)

1. Create a `.env` file in the project root directory:

```env
# .env file
GIT_USERNAME=your_git_username
GIT_PASSWORD=your_git_token_or_password
MCP_NAME=ZephyrMcpServer
```

2. Modify MCP server code to load the .env file (add at the beginning of mcp_server.py):

```python
import os
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
```

## Configuration Priority

Environment variable priority (from highest to lowest):

1. **Direct parameter passing**: username/token parameters directly provided when calling functions
2. **env settings in mcp.json**: Environment variables set in VS Code MCP configuration
3. **VS Code terminal environment variables**: Environment variables configured in VS Code settings
4. **System environment variables**: Operating system-level environment variables
5. **Default values**: If none of the above are set, use the default value "None"

## Security Best Practices

### 1. Do Not Hardcode Credentials in Code

```json
// ❌ Incorrect approach
"env": {
    "GIT_USERNAME": "my_real_username",
    "GIT_PASSWORD": "my_real_password123"
}
```

### 2. Use Placeholders and Documentation

```json
// ✅ Correct approach
"env": {
    "mcp_name": "ZephyrMcpServer",
    "GIT_USERNAME": "${GIT_USERNAME}",
    "GIT_PASSWORD": "${GIT_PASSWORD}"
}
```

### 3. Use VS Code's Variable Substitution

VS Code supports several predefined variables:

- `${env:GIT_USERNAME}` - Reference system environment variables
- `${workspaceFolder}` - Workspace folder path
- `${userHome}` - User home directory

### 4. Create Configuration Templates

Create an `mcp.json.template` file:

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

Then copy it to `mcp.json` and fill in actual values before use.

## Verifying Configuration

### Method 1: Using MCP Tools for Verification

```python
# Verify if environment variables are set correctly
import os
print(f"GIT_USERNAME: {os.environ.get('GIT_USERNAME', 'Not set')}")
print(f"GIT_PASSWORD: {'Set' if os.environ.get('GIT_PASSWORD') else 'Not set'}")
```

### Method 2: Testing with west_init

```python
# Test west_init function
result = west_init(
    repo_url="https://github.com/zephyrproject-rtos/zephyr",
    branch="main", 
    project_dir="test-project",
    auth_method="env"  # Use environment variable authentication
)
print(result)
```

## Common Issues

### Q1: Environment Variables Not Taking Effect
**Solution:**
1. Restart VS Code
2. Check if environment variable names are correct (case-sensitive)
3. Verify that the MCP server correctly reads the environment variables

### Q2: Security Warnings
**Solution:**
1. Use Personal Access Tokens (PAT) instead of passwords
2. Regularly rotate tokens
3. Use system environment variables instead of hardcoding in files

### Q3: Multi-user Shared Configuration
**Solution:**
1. Use system environment variables
2. Create user-specific configuration files
3. Use `.env` files and add to `.gitignore`

## Recommended Configuration

**Most secure configuration method:**

1. **Do not** store real credentials in `mcp.json`
2. Use system environment variables
3. Document the required environment variables

**Final recommended mcp.json:**

```json
{
    "name": "Zephyr MCP Server",
    "description": "Model Context Protocol server for Zephyr RTOS development workflows",
    "env": {
        "mcp_name": "ZephyrMcpServer"
    }
}
```

**What users need to do:**

Set environment variables at the system level:

```powershell
# Windows
[Environment]::SetEnvironmentVariable('GIT_USERNAME', 'your_username', 'User')
[Environment]::SetEnvironmentVariable('GIT_PASSWORD', 'your_token', 'User')

# Linux/Mac
export GIT_USERNAME="your_username"
export GIT_PASSWORD="your_token"
```