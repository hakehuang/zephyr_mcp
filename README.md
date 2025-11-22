# Zephyr MCP Server

A Model Context Protocol (MCP) server for Zephyr RTOS development workflows. This server provides a comprehensive set of tools for managing Zephyr projects, including project initialization, firmware flashing, testing, version management, and Git operations with authentication support.

## Features

### 🔧 Core Zephyr Operations
- **Project Initialization**: Initialize Zephyr projects with authentication support
- **Firmware Flashing**: Flash firmware to target boards with various flashers
- **Testing Framework**: Run Twister tests with comprehensive result reporting
- **Version Management**: Switch between Zephyr versions and manage updates

### 🔐 Authentication Support
- **Multiple Authentication Methods**: Embedded, environment variable, and Git config authentication
- **Secure Credential Handling**: Support for username/token authentication
- **Connection Testing**: Pre-flight Git connection validation

### 🔄 Git Operations
- **Branch Management**: Checkout specific Git references (SHA, tag, branch)
- **Mirror Management**: Redirect to Zephyr Git mirrors
- **Configuration Management**: Set and retrieve Git configuration status

## Installation

### Prerequisites

- Python 3.8+
- Zephyr development environment with:
  - `west` tool
  - `git`
  - `twister` (for testing)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/zephyr_mcp.git
cd zephyr_mcp
```

2. Install dependencies:
```bash
pip install fastmcp
```

3. Run the server:
```bash
python src/mcp_server.py
```

## Available Tools

### 1. `west_init` - Initialize Zephyr Project
Initialize a Zephyr project with authentication support.

**Parameters:**
- `repo_url` (str): Git repository URL
- `branch` (str): Git branch name
- `project_dir` (str): Local project directory
- `username` (Optional[str]): Git username for authentication
- `token` (Optional[str]): Git token or password
- `auth_method` (str): Authentication method ("embedded", "env", "config") - Default: "embedded"

**Example:**
```json
{
  "repo_url": "https://github.com/zephyrproject-rtos/zephyr.git",
  "branch": "main",
  "project_dir": "/path/to/project",
  "username": "your_username",
  "token": "your_token",
  "auth_method": "embedded"
}
```

### 2. `west_flash` - Flash Firmware
Execute west flash command to flash firmware to target board.

**Parameters:**
- `build_dir` (str): Build output directory
- `board` (Optional[str]): Target hardware board model
- `runner` (Optional[str]): Flasher type (jlink, pyocd, openocd, etc.)
- `probe_id` (Optional[str]): Flasher ID/serial number
- `flash_extra_args` (Optional[str]): Additional flash parameters

### 3. `run_twister` - Run Twister Tests
Execute twister test or build command and return structured results.

**Parameters:**
- `platform` (Optional[str]): Target hardware platform
- `tests` (Optional[Union[List[str], str]]): Test path or suite name
- `test_cases` (Optional[Union[List[str], str]]): Test case name
- `enable_slow` (bool): Enable slow tests - Default: False
- `build_only` (bool): Build only mode - Default: False
- `extra_args` (Optional[str]): Additional twister parameters
- `project_dir` (str): Zephyr project root directory

### 4. `git_checkout` - Switch Git Reference
Switch to specified Git reference (SHA, tag or branch) in Zephyr project directory.

**Parameters:**
- `project_dir` (str): Zephyr project directory
- `ref` (str): Git reference (SHA, tag or branch name)

### 5. `west_update` - Update Zephyr Project
Run west update command in Zephyr project directory.

**Parameters:**
- `project_dir` (str): Zephyr project directory

### 6. `switch_zephyr_version` - Switch Zephyr Version
Switch to specified Zephyr version (SHA or tag) and run west update.

**Parameters:**
- `project_dir` (str): Zephyr project directory
- `ref` (str): Git reference (SHA, tag or branch name)

### 7. `get_zephyr_status` - Get Project Status
Get Git status information of Zephyr project.

**Parameters:**
- `project_dir` (str): Zephyr project directory

### 8. `git_redirect_zephyr_mirror` - Redirect to Git Mirror
Redirect Zephyr Git repository to mirror address.

**Parameters:**
- `project_dir` (str): Zephyr project directory
- `mirror_url` (str): Mirror repository URL

### 9. `get_git_redirect_status` - Get Redirect Status
Get Git remote redirect status.

**Parameters:**
- `project_dir` (str): Zephyr project directory

### 10. `set_git_credentials` - Set Git Credentials
Set Git authentication credentials (global or project-specific).

**Parameters:**
- `username` (str): Git username
- `password` (str): Git password/token
- `project_dir` (Optional[str]): Project directory for local config

### 11. `test_git_connection` - Test Git Connection
Test Git repository connection with authentication.

**Parameters:**
- `repo_url` (str): Git repository URL
- `username` (Optional[str]): Git username
- `password` (Optional[str]): Git password/token
- `project_dir` (Optional[str]): Project directory for config

### 12. `get_git_config_status` - Get Git Config Status
Get Git configuration status (global or project-specific).

**Parameters:**
- `project_dir` (Optional[str]): Project directory for local config

## Authentication Methods

The server supports three authentication methods:

### 1. Embedded Authentication
Embed credentials directly in the repository URL:
```
https://username:token@github.com/zephyrproject-rtos/zephyr.git
```

### 2. Environment Variable Authentication
Set credentials via environment variables:
- `GIT_USERNAME`
- `GIT_PASSWORD`
- `GIT_TERMINAL_PROMPT=0`

### 3. Git Configuration Authentication
Configure Git credentials globally or per-project:
- Global username configuration
- Credential caching
- Project-specific settings

## Usage Examples

### Basic Project Initialization
```python
# Initialize Zephyr project
result = west_init(
    repo_url="https://github.com/zephyrproject-rtos/zephyr.git",
    branch="main",
    project_dir="/path/to/zephyr_project"
)
```

### Authentication with Private Repository
```python
# Initialize with authentication
result = west_init(
    repo_url="https://github.com/private-org/zephyr.git",
    branch="main",
    project_dir="/path/to/project",
    username="your_username",
    token="your_token",
    auth_method="embedded"
)
```

### Interactive Mode with User Prompting
```python
# Use interactive mode to prompt for missing parameters
result = west_init_interactive(
    # Leave parameters empty to prompt user
    require_confirmation=True,
    auto_prompt=True
)
```

### Parameter Validation
```python
# Validate parameters before initialization
validation = validate_west_init_params(
    repo_url="https://github.com/zephyrproject-rtos/zephyr.git",
    branch="main",
    project_dir="c:/temp/zephyr-project"
)

if validation["status"] == "valid":
    print("参数验证通过，可以安全执行")
else:
    print("发现以下问题:")
    for warning in validation["warnings"]:
        print(f"⚠️  {warning}")
    for suggestion in validation["suggestions"]:
        print(f"💡 {suggestion}")
```

### Advanced Interactive Example
```python
# Interactive initialization with validation
validation = validate_west_init_params()
if validation["status"] in ["missing_params", "warnings"]:
    print("参数验证结果:")
    print(f"状态: {validation['status']}")
    print(f"缺失参数: {validation['missing_params']}")
    print(f"警告: {validation['warnings']}")
    print(f"建议: {validation['suggestions']}")

# Then use interactive mode to fill in missing parameters
result = west_init_interactive(
    require_confirmation=True,
    auto_prompt=True
)
```

## Interactive Features

### New Interactive Tools

#### `west_init_interactive` - Interactive Project Initialization
Enhanced version of `west_init` with user-friendly features:

**Key Features:**
- **Automatic Parameter Prompting**: Prompts for missing required parameters
- **User Confirmation**: Shows configuration summary and asks for confirmation
- **Parameter Validation**: Validates inputs before execution
- **Friendly Error Messages**: Provides helpful suggestions and examples
- **Cancellation Support**: Allows users to cancel at any step

**Parameters:**
- All parameters from `west_init` are optional
- `require_confirmation` (bool): Whether to require user confirmation - Default: True
- `auto_prompt` (bool): Whether to automatically prompt for missing parameters - Default: True

**Usage Examples:**
```python
# Minimal call - will prompt for all required parameters
result = west_init_interactive()

# Partial parameters - will prompt for missing ones
result = west_init_interactive(
    repo_url="https://github.com/zephyrproject-rtos/zephyr.git",
    # branch and project_dir will be prompted
)

# Disable confirmation for automated workflows
result = west_init_interactive(
    repo_url="https://github.com/zephyrproject-rtos/zephyr.git",
    branch="main", 
    project_dir="/path/to/project",
    require_confirmation=False
)
```

#### `validate_west_init_params` - Parameter Validation
Validates west init parameters and provides helpful suggestions:

**Features:**
- **Missing Parameter Detection**: Identifies missing required parameters
- **URL Format Validation**: Checks Git repository URL format
- **Branch Name Suggestions**: Provides common branch names
- **Directory Validation**: Checks project directory status
- **Authentication Method Validation**: Validates auth method selection
- **Helpful Suggestions**: Provides specific recommendations

**Return Values:**
- `status`: "valid", "missing_params", or "warnings"
- `missing_params`: List of missing required parameters
- `warnings`: List of potential issues
- `suggestions`: List of helpful recommendations
- `validation_details`: Detailed validation information

## Error Handling

The server provides comprehensive error handling with detailed error messages:

### Common Error Scenarios

1. **Missing Tools**: Returns clear error if west/git/twister not installed
2. **Authentication Failures**: Detailed auth error messages with suggestions
3. **Connection Issues**: Git connection test failures with troubleshooting tips
4. **Permission Errors**: File system permission issues with resolution steps
5. **Invalid Parameters**: Parameter validation with helpful suggestions

### Error Response Format
```json
{
  "status": "error",
  "log": "detailed execution log",
  "error": "user-friendly error message",
  "suggestions": ["helpful suggestion 1", "suggestion 2"]
}
```

## Configuration

### Environment Variables
- `mcp_name`: MCP server name (default: "ZephyrMcpServer")
- `GIT_USERNAME`: Git username for authentication
- `GIT_PASSWORD`: Git password/token for authentication
- `GIT_TERMINAL_PROMPT`: Disable Git terminal prompts (set to "0")

### Git Mirror Configuration
Configure Git to use Zephyr mirrors for faster access:
```python
# Enable mirror redirect
git_redirect_zephyr_mirror(enable=True)

# Check redirect status
status = get_git_redirect_status()
```

## Development

### Adding New Tools
1. Define the function with proper docstring (bilingual)
2. Add `@mcp.tool()` decorator
3. Include comprehensive parameter validation
4. Add error handling with helpful messages
5. Update README documentation

### Testing
```bash
# Test basic functionality
python -m pytest tests/

# Test with real Zephyr project (requires Zephyr environment)
python src/mcp_server.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review error messages and suggestions provided by the tools
    username="your_username",
    token="your_personal_access_token",
    auth_method="embedded"
)
```

### Firmware Flashing
```python
# Flash firmware to board
result = west_flash(
    build_dir="/path/to/build",
    board="nrf52840dk_nrf52840",
    runner="jlink"
)
```

### Running Tests
```python
# Run Twister tests
result = run_twister(
    platform="nrf52840dk_nrf52840",
    tests=["samples/hello_world"],
    project_dir="/path/to/zephyr_project"
)
```

## Error Handling

All tools return structured responses with:
- `status`: "success" or "error"
- `log`: Command output logs
- `error`: Error message (if any)
- Additional tool-specific fields

## Development

### Project Structure
```
zephyr_mcp/
├── src/
│   └── mcp_server.py    # Main MCP server implementation
├── .vscode/             # VS Code configuration
├── LICENSE              # License file
└── README.md           # This file
```

### Adding New Tools

To add a new tool:

1. Define the function with `@mcp.tool()` decorator
2. Add comprehensive docstring with parameters and return values
3. Implement error handling
4. Update this README with tool documentation

Example:
```python
@mcp.tool()
def new_tool(param1: str, param2: Optional[str] = None) -> Dict[str, Any]:
    """
    Function Description: Description of the tool
    功能描述: 工具的功能描述
    
    Parameters:
    参数说明:
    - param1 (str): Required. Parameter description
    - param1 (str): 必须。参数说明
    - param2 (Optional[str]): Optional. Parameter description
    - param2 (Optional[str]): 可选。参数说明
    
    Returns:
    返回值:
    - Dict[str, Any]: Return description
    - Dict[str, Any]: 返回值说明
    
    Exception Handling:
    异常处理:
    - Exception handling description
    - 异常处理说明
    """
    # Implementation here
    pass
```

## License

This project is licensed under the terms of the LICENSE file in the root of this repository.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

For support and questions:
- Open an issue on GitHub
- Check the documentation
- Review the tool examples above