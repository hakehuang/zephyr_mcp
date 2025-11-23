# MCP Environment Variable Configuration Examples

## Example 1: Basic Configuration (Secure)

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

## Example 2: Using Placeholders (Recommended)

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

## Example 3: Development Environment Configuration

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

## Example 4: Production Environment Configuration

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

## Environment Variable Setup Scripts

### Windows PowerShell Setup Script

```powershell
# set_env.ps1
Write-Host "Setting up Zephyr MCP environment variables..."

# Temporary settings (current session)
$env:GIT_USERNAME = Read-Host "Please enter Git username"
$env:GIT_PASSWORD = Read-Host "Please enter Git token/password" -AsSecureString

# Permanent settings (user level)
[Environment]::SetEnvironmentVariable('GIT_USERNAME', $env:GIT_USERNAME, 'User')
[Environment]::SetEnvironmentVariable('GIT_PASSWORD', [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($env:GIT_PASSWORD)), 'User')

Write-Host "Environment variables setup complete!"
```

### Linux/Mac Setup Script

```bash
#!/bin/bash
# set_env.sh

echo "Setting up Zephyr MCP environment variables..."

read -p "Please enter Git username: " GIT_USERNAME
read -sp "Please enter Git token/password: " GIT_PASSWORD
echo

# Temporary settings
export GIT_USERNAME="$GIT_USERNAME"
export GIT_PASSWORD="$GIT_PASSWORD"

# Permanent settings (add to ~/.bashrc or ~/.zshrc)
echo "export GIT_USERNAME=\"$GIT_USERNAME\"" >> ~/.bashrc
echo "export GIT_PASSWORD=\"$GIT_PASSWORD\"" >> ~/.bashrc

echo "Environment variables setup complete!"
```

## Verification Script

```python
# verify_env.py
import os
import json

def verify_environment():
    """Verify environment variable configuration"""
    
    print("=== MCP Environment Variable Verification ===")
    
    # Check basic environment variables
    mcp_name = os.environ.get('mcp_name', 'Not set')
    git_username = os.environ.get('GIT_USERNAME', 'Not set')
    git_password = 'Set' if os.environ.get('GIT_PASSWORD') else 'Not set'
    
    print(f"mcp_name: {mcp_name}")
    print(f"GIT_USERNAME: {git_username}")
    print(f"GIT_PASSWORD: {git_password}")
    
    # Check MCP configuration file
    try:
        with open('.vscode/mcp.json', 'r') as f:
            config = json.load(f)
            env_config = config.get('mcp', {}).get('servers', {}).get('zephyr-mcp', {}).get('env', {})
            
            print(f"\n=== MCP Configuration File ===")
            print(f"Environment variables in configuration file: {env_config}")
            
            # Check if secure method is used
            if '${env:' in str(env_config):
                print("✅ Secure variable reference method is used")
            else:
                print("⚠️  Environment variable values are set directly, consider using variable references")
                
    except FileNotFoundError:
        print("❌ .vscode/mcp.json configuration file not found")
    except json.JSONDecodeError:
        print("❌ MCP configuration file has invalid format")
    
    # Test west initialization
    print(f"\n=== West Initialization Test ===")
    try:
        from src.mcp_server import west_init
        
        # Test parameter validation
        result = west_init(
            repo_url="https://github.com/zephyrproject-rtos/zephyr",
            branch="main",
            project_dir="test-env-project",
            auth_method="env"
        )
        
        print(f"west_init result: {result}")
        
    except Exception as e:
        print(f"west_init test failed: {e}")

if __name__ == "__main__":
    verify_environment()
```

## Best Practices Summary

1. **Security First**: Do not store real credentials in configuration files
2. **Use Variable References**: Use `${env:VARIABLE_NAME}` syntax
3. **Layered Configuration**: Create different configurations for different environments (development, testing, production)
4. **Documentation**: Record the environment variables that need to be set
5. **Validate Configuration**: Provide validation scripts to check if configuration is correct
6. **Version Control**: Exclude sensitive information from version control

## Quick Start Steps

1. **Choose Configuration Template**: Select a suitable configuration from the examples above
2. **Set System Environment Variables**:
   ```powershell
   # Windows
   [Environment]::SetEnvironmentVariable('GIT_USERNAME', 'your_username', 'User')
   [Environment]::SetEnvironmentVariable('GIT_PASSWORD', 'your_token', 'User')
   ```
3. **Validate Configuration**: Run the verification script to ensure everything works correctly
4. **Restart VS Code**: Ensure environment variables take effect

After this configuration, your MCP server can securely use environment variables for Git authentication!