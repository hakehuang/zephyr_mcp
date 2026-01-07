# Zephyr MCP Agent

一个基于Agno框架的模块化Zephyr RTOS开发工作流MCP（Model Context Protocol）Agent。该Agent提供了一套完整的Zephyr项目管理工具，包括项目初始化、固件烧录、测试、版本管理和Git操作等功能。

A modular Zephyr RTOS development workflow MCP (Model Context Protocol) Agent based on the Agno framework. This Agent provides a comprehensive set of tools for Zephyr project management, including project initialization, firmware flashing, testing, version management, and Git operations.

---

## 🚀 新特性 / New Features

### 模块化架构 / Modular Architecture
- **模块化设计** - 将大型单体文件拆分为专注的模块，提高可维护性
- **职责分离** - 每个模块负责特定功能，便于团队协作开发
- **易于扩展** - 新增功能只需在相应模块中添加

- **Modular Design** - Split large monolithic files into focused modules for better maintainability
- **Separation of Concerns** - Each module handles specific functionality for team collaboration
- **Easy to Extend** - Add new features by extending corresponding modules

### Agno框架集成 / Agno Framework Integration
- **Agno API兼容** - 使用Agno v2.3.2的现代Agent框架
- **工具注册优化** - 使用`agent.add_tool()`方法注册工具
- **Telemetry支持** - 与Agno的telemetry标志兼容

- **Agno API Compatible** - Uses modern Agno v2.3.2 Agent framework
- **Optimized Tool Registration** - Register tools using `agent.add_tool()` method
- **Telemetry Support** - Compatible with Agno's telemetry flag

### OpenTelemetry分布式追踪 / OpenTelemetry Distributed Tracing
- **可配置追踪** - 支持控制台和OTLP导出器
- **HTTP请求追踪** - 自动追踪API请求和工具调用
- **优雅降级** - 当OpenTelemetry依赖未安装时自动禁用

- **Configurable Tracing** - Supports console and OTLP exporters
- **HTTP Request Tracing** - Automatically traces API requests and tool calls
- **Graceful Degradation** - Automatically disables when OpenTelemetry dependencies are not installed

### 多语言支持 / Multi-language Support
- **国际化** - 支持中文和英文界面
- **自动检测** - 根据HTTP请求头自动检测语言
- **动态切换** - 运行时动态切换语言

- **Internationalization** - Supports Chinese and English interfaces
- **Auto-detection** - Automatically detects language from HTTP request headers
- **Dynamic Switching** - Switch languages at runtime

---

## 📁 项目结构 / Project Structure

```
zephyr_mcp/
├── main.py                      # 主入口文件 / Main entry point
├── agent_core.py                # Agent核心类 / Agent core class
├── opentelemetry_integration.py # OpenTelemetry集成模块 / OpenTelemetry integration module
├── http_server.py               # HTTP服务器实现 / HTTP server implementation
├── config_manager.py            # 配置管理模块 / Configuration management module
├── language_manager.py          # 语言管理模块 / Language management module
├── config.json                  # 配置文件（自动生成） / Configuration file (auto-generated)
└── src/                         # 源代码目录 / Source code directory
    ├── tools/                   # 工具模块 / Tools module
    └── utils/                   # 工具类 / Utility classes
```

---

## 🔧 核心功能 / Core Features

### Zephyr操作 / Zephyr Operations
- **项目初始化** - 支持认证的Zephyr项目初始化
- **固件烧录** - 使用各种烧录器烧录固件到目标板
- **测试框架** - 运行Twister测试并返回结构化结果
- **版本管理** - 切换Zephyr版本和管理更新

- **Project Initialization** - Initialize Zephyr projects with authentication support
- **Firmware Flashing** - Flash firmware to target boards with various flashers
- **Testing Framework** - Run Twister tests with comprehensive result reporting
- **Version Management** - Switch between Zephyr versions and manage updates

### 认证支持 / Authentication Support
- **多种认证方法** - 嵌入式、环境变量和Git配置认证
- **安全凭据处理** - 支持用户名/令牌认证
- **连接测试** - Git连接预验证

- **Multiple Authentication Methods** - Embedded, environment variable, and Git config authentication
- **Secure Credential Handling** - Support for username/token authentication
- **Connection Testing** - Pre-flight Git connection validation

### Git操作 / Git Operations
- **分支管理** - 检出特定Git引用（SHA、标签、分支）
- **镜像管理** - 重定向到Zephyr Git镜像
- **配置管理** - 设置和获取Git配置状态

- **Branch Management** - Checkout specific Git references (SHA, tag, branch)
- **Mirror Management** - Redirect to Zephyr Git mirrors
- **Configuration Management** - Set and retrieve Git configuration status

---

## 🚀 快速开始 / Quick Start

### 虚拟环境自动激活 / Virtual Environment Auto-activation

项目现在支持自动虚拟环境检测和激活功能，确保MCP服务器始终在正确的环境中运行。

The project now supports automatic virtual environment detection and activation, ensuring the MCP server always runs in the correct environment.

#### 启动方式 / Startup Methods

**方式1: 使用启动器（推荐） / Method 1: Using Launcher (Recommended)**
```bash
# 从项目根目录启动 / Start from project root
python start_mcp_server.py
```

**方式2: 直接运行MCP服务器 / Method 2: Direct MCP Server Execution**
```bash
# MCP服务器会自动检测并激活虚拟环境
# MCP server will automatically detect and activate virtual environment
python src/mcp_server.py
```

#### 虚拟环境管理 / Virtual Environment Management

- **自动检测** - 自动查找项目根目录下的`.venv`、`venv`等虚拟环境目录
- **跨平台支持** - 支持Windows、Linux和macOS的虚拟环境激活
- **依赖检查** - 启动时自动检查必需的Python包是否已安装
- **优雅降级** - 如果虚拟环境不可用，会继续使用当前环境

- **Auto-detection** - Automatically finds virtual environment directories like `.venv`, `venv` in project root
- **Cross-platform Support** - Supports virtual environment activation on Windows, Linux, and macOS
- **Dependency Checking** - Automatically checks if required Python packages are installed at startup
- **Graceful Degradation** - Continues with current environment if virtual environment is unavailable

### 环境设置 / Environment Setup

### 安装要求 / Prerequisites

- Python 3.8+
- Zephyr开发环境（包含west、git、twister）
- Zephyr development environment (with west, git, twister)

### 安装步骤 / Installation Steps

1. 克隆仓库：
```bash
git clone https://github.com/your-username/zephyr_mcp.git
cd zephyr_mcp
```

2. 安装依赖：
```bash
pip install agno==2.3.2
```

3. 启动Agent：
```bash
python main.py
```

### 创建示例配置 / Create Sample Configuration

```bash
python main.py --create-config
```

---

## ⚙️ 配置说明 / Configuration

### 配置文件结构 / Configuration File Structure

```json
{
  "agent_name": "Zephyr MCP Agent",
  "version": "1.0.0",
  "description": "Zephyr MCP Agent for Zephyr RTOS development",
  "tools_directory": "./src/tools",
  "utils_directory": "./src/utils",
  "log_level": "INFO",
  "port": 8001,
  "host": "localhost",
  "language": {
    "default": "zh",
    "available": ["zh", "en"],
    "auto_detect": true
  },
  "opentelemetry": {
    "enabled": false,
    "service_name": "zephyr_mcp_agent",
    "exporter": "console",
    "otlp_endpoint": "http://localhost:4318/v1/traces",
    "sampler": "always_on",
    "headers": {},
    "api_key": "",
    "project_name": "zephyr_mcp_agent"
  },
  "llm": {
    "enabled": false,
    "providers": {
      "openai": {
        "api_key": "your_openai_api_key_here",
        "model": "gpt-3.5-turbo"
      }
    }
  }
}
```

### 分布式追踪配置 / Distributed Tracing Configuration

#### 基本配置 / Basic Configuration

```json
{
  "opentelemetry": {
    "enabled": false,
    "service_name": "zephyr_mcp_agent",
    "exporter": "console",
    "otlp_endpoint": "http://localhost:4318/v1/traces",
    "sampler": "always_on",
    "headers": {},
    "api_key": "",
    "project_name": "zephyr_mcp_agent"
  }
}
```

#### LangSmith 集成配置 / LangSmith Integration Configuration

```json
{
  "opentelemetry": {
    "enabled": true,
    "service_name": "zephyr_mcp_agent",
    "exporter": "otlp",
    "otlp_endpoint": "https://api.smith.langchain.com/otel/v1/traces",
    "sampler": "always_on",
    "headers": {
      "x-api-key": "lsv2_pt_your_api_key_here",
      "Langsmith-Project": "your_project_name"
    },
    "api_key": "lsv2_pt_your_api_key_here",
    "project_name": "your_project_name"
  }
}
```

#### 支持的导出器 / Supported Exporters

- **console**: 输出到控制台 / Output to console
- **otlp**: 使用 OTLP 协议导出到远程服务 / Export to remote service using OTLP protocol

#### Agno Instrumentor 集成 / Agno Instrumentor Integration

项目现在支持使用 Agno Instrumentor 进行自动埋点。当 `openinference.instrumentation.agno` 包可用时，系统会自动启用 Agno 的自动埋点功能。

The project now supports automatic instrumentation using Agno Instrumentor. When the `openinference.instrumentation.agno` package is available, the system will automatically enable Agno's automatic instrumentation.

### 命令行参数 / Command Line Arguments

```bash
# 基本使用 / Basic usage
python main.py

# 指定配置文件 / Specify config file
python main.py --config custom_config.json

# 创建示例配置文件 / Create sample config
python main.py --create-config

# 覆盖配置参数 / Override config parameters
python main.py --port 8080 --host 0.0.0.0 --language en --log-level DEBUG
```

---

## 🌐 API接口 / API Endpoints

启动服务后，可以通过以下API端点与Agent交互：
After starting the service, you can interact with the Agent through the following API endpoints:

### 工具调用 / Tool Execution
```bash
POST http://localhost:8001/api/tool
Content-Type: application/json
X-Trace-ID: your-trace-id

{
  "tool": "tool_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

### 获取工具列表 / Get Tool List
```bash
GET http://localhost:8001/api/tools
```

### 获取工具信息 / Get Tool Information
```bash
GET http://localhost:8001/api/tool/info?name=tool_name
```

### API文档 / API Documentation
```bash
GET http://localhost:8001/api/docs
```

---

## 🔧 可用工具 / Available Tools

### Zephyr项目管理工具 / Zephyr Project Management Tools

#### `setup_zephyr_environment` - 设置Zephyr开发环境 / Set up Zephyr Development Environment
根据west.yml文件设置完整的Zephyr RTOS开发环境。
Set up a complete Zephyr RTOS development environment according to west.yml file.

**参数 / Parameters：**
- `west_yml_url` (str): west.yml文件的URL / URL of west.yml file
- `project_dir` (str): 项目目录路径 / Project directory path
- `manifest_rev` (Optional[str]): manifest修订版本 / Manifest revision

#### `west_flash` - 烧录固件 / Flash Firmware
执行west flash命令将固件烧录到目标板。
Execute west flash command to flash firmware to target board.

**参数 / Parameters：**
- `build_dir` (str): 构建输出目录 / Build output directory
- `board` (Optional[str]): 目标硬件板型号 / Target hardware board model
- `runner` (Optional[str]): 烧录器类型 / Flasher type

#### `run_twister` - 运行Twister测试 / Run Twister Tests
执行twister测试或构建命令并返回结构化结果。
Execute twister test or build command and return structured results.

**参数 / Parameters：**
- `platform` (Optional[str]): 目标硬件平台 / Target hardware platform
- `tests` (Optional[List[str]]): 测试路径或套件名称 / Test path or suite name
- `project_dir` (str): Zephyr项目根目录 / Zephyr project root directory

### Git操作工具 / Git Operation Tools

#### `git_checkout` - 切换Git引用 / Switch Git Reference
在Zephyr项目目录中切换到指定的Git引用（SHA、标签或分支）。
Switch to specified Git reference (SHA, tag or branch) in Zephyr project directory.

**参数 / Parameters：**
- `project_dir` (str): Zephyr项目目录 / Zephyr project directory
- `ref` (str): Git引用 / Git reference

#### `west_update` - 更新Zephyr项目 / Update Zephyr Project
在Zephyr项目目录中运行west update命令。
Run west update command in Zephyr project directory.

**参数 / Parameters：**
- `project_dir` (str): Zephyr项目目录 / Zephyr project directory

#### `switch_zephyr_version` - 切换Zephyr版本 / Switch Zephyr Version
切换到指定的Zephyr版本（SHA或标签）并运行west update。
Switch to specified Zephyr version (SHA or tag) and run west update.

**参数 / Parameters：**
- `project_dir` (str): Zephyr项目目录 / Zephyr project directory
- `ref` (str): Git引用 / Git reference

#### `get_zephyr_status` - 获取项目状态 / Get Project Status
获取Zephyr项目的Git状态信息。
Get Git status information of Zephyr project.

**参数 / Parameters：**
- `project_dir` (str): Zephyr项目目录 / Zephyr project directory

### Git认证和配置工具 / Git Authentication and Configuration Tools

#### `git_redirect_zephyr_mirror` - 重定向到Git镜像 / Redirect to Git Mirror
将Zephyr Git仓库重定向到镜像地址。
Redirect Zephyr Git repository to mirror address.

**参数 / Parameters：**
- `project_dir` (str): Zephyr项目目录 / Zephyr project directory
- `mirror_url` (str): 镜像仓库URL / Mirror repository URL

#### `get_git_redirect_status` - 获取重定向状态 / Get Redirect Status
获取Git远程重定向状态。
Get Git remote redirect status.

**参数 / Parameters：**
- `project_dir` (str): Zephyr项目目录 / Zephyr project directory

#### `set_git_credentials` - 设置Git凭据 / Set Git Credentials
设置Git认证凭据（全局或项目特定）。
Set Git authentication credentials (global or project-specific).

**参数 / Parameters：**
- `username` (str): Git用户名 / Git username
- `password` (str): Git密码/令牌 / Git password/token
- `project_dir` (Optional[str]): 项目目录（用于本地配置） / Project directory (for local config)

#### `test_git_connection` - 测试Git连接 / Test Git Connection
使用认证测试Git仓库连接。
Test Git repository connection with authentication.

**参数 / Parameters：**
- `repo_url` (str): Git仓库URL / Git repository URL
- `username` (Optional[str]): Git用户名 / Git username
- `password` (Optional[str]): Git密码/令牌 / Git password/token

#### `get_git_config_status` - 获取Git配置状态 / Get Git Configuration Status
获取Git配置状态（全局或项目特定）。
Get Git configuration status (global or project-specific).

**参数 / Parameters：**
- `project_dir` (Optional[str]): 项目目录（用于本地配置） / Project directory (for local config)

### 高级Git操作 / Advanced Git Operations

#### `fetch_branch_or_pr` - 获取分支或Pull Request / Fetch Branch or Pull Request
从远程仓库获取分支或Pull Request。
Fetch a branch or pull request from a remote repository.

#### `git_rebase` - 执行Git rebase操作 / Execute Git Rebase Operation
在Zephyr项目目录中执行Git rebase操作。
Execute Git rebase operation in Zephyr project directory.

> Note: `source_branch`/`onto_branch` accept any Git reference (branch, tag, or commit SHA).

---

## 🔍 模块说明 / Module Documentation

### agent_core.py
Agent核心类，包含主要的`ZephyrMCPAgent`类，负责：
Agent core class containing the main `ZephyrMCPAgent` class, responsible for:
- Agent初始化和配置加载 / Agent initialization and configuration loading
- 工具注册和管理 / Tool registration and management
- 语言管理 / Language management
- 与Agno框架的集成 / Integration with Agno framework

### opentelemetry_integration.py
OpenTelemetry集成模块，提供：
OpenTelemetry integration module, providing:
- 分布式追踪初始化 / Distributed tracing initialization
- Span创建和管理 / Span creation and management
- 多种导出器支持（控制台、OTLP） / Multiple exporter support (console, OTLP)
- HTTP请求自动追踪 / HTTP request automatic tracing

### http_server.py
HTTP服务器模块，实现：
HTTP server module, implementing:
- JSON API服务器 / JSON API server
- 工具调用请求处理 / Tool execution request handling
- 错误处理和追踪ID管理 / Error handling and trace ID management
- 多语言请求头检测 / Multi-language request header detection

### config_manager.py
配置管理模块，负责：
Configuration management module, responsible for:
- 配置文件加载和验证 / Configuration file loading and validation
- 默认配置生成 / Default configuration generation
- 配置参数覆盖 / Configuration parameter overriding

### language_manager.py
语言管理模块，提供：
Language management module, providing:
- 多语言资源管理 / Multi-language resource management
- 语言切换功能 / Language switching functionality
- 请求头语言检测 / Request header language detection

---

## 🛠️ 开发指南 / Development Guide

### 添加新工具 / Adding New Tools

1. 在`src/tools/`目录中创建新的工具模块
2. 定义工具函数并使用适当的装饰器
3. 在工具注册表中注册新工具
4. 更新相关文档

1. Create new tool module in `src/tools/` directory
2. Define tool function with appropriate decorators
3. Register new tool in tool registry
4. Update relevant documentation

### 模块开发 / Module Development

每个模块应该：
Each module should:
- 职责单一，功能专注 / Have single responsibility and focused functionality
- 提供清晰的接口和文档 / Provide clear interfaces and documentation
- 包含适当的错误处理 / Include proper error handling
- 遵循项目的代码风格 / Follow project code style

### 测试 / Testing

```bash
# 测试模块导入 / Test module imports
python -c "from agent_core import ZephyrMCPAgent; print('导入成功 / Import successful')"

# 测试配置加载 / Test configuration loading
python -c "from config_manager import load_config; config = load_config('config.json'); print('配置加载成功 / Config loaded successfully')"

# 测试Agent启动 / Test Agent startup
python main.py --help
```

---

## 🔄 重构优势 / Refactoring Benefits

### 代码质量提升 / Code Quality Improvement
- **可读性** - 模块化设计使代码更易于理解和维护
- **可测试性** - 可以单独测试每个模块
- **可维护性** - 修改一个模块不会影响其他功能

- **Readability** - Modular design makes code easier to understand and maintain
- **Testability** - Each module can be tested independently
- **Maintainability** - Modifying one module doesn't affect other functionality

### 开发效率提升 / Development Efficiency Improvement
- **并行开发** - 多个开发者可以同时开发不同模块
- **快速定位** - 问题定位更快速，职责更明确
- **扩展便捷** - 新增功能只需在相应模块中添加

- **Parallel Development** - Multiple developers can work on different modules simultaneously
- **Quick Troubleshooting** - Faster problem identification with clear responsibilities
- **Easy Extension** - Add new features by extending corresponding modules

### 架构现代化 / Architecture Modernization
- **Agno框架** - 使用现代Agent框架，提供更好的工具管理
- **OpenTelemetry** - 集成分布式追踪，便于监控和调试
- **模块化设计** - 符合现代软件工程最佳实践

- **Agno Framework** - Uses modern Agent framework for better tool management
- **OpenTelemetry** - Integrated distributed tracing for monitoring and debugging
- **Modular Design** - Follows modern software engineering best practices

---

## 🐛 故障排除 / Troubleshooting

### 常见问题 / Common Issues

1. **OpenTelemetry依赖未安装** / **OpenTelemetry Dependencies Not Installed**
   ```
   警告: OpenTelemetry 依赖未安装，将禁用分布式追踪功能
   Warning: OpenTelemetry dependencies not installed, distributed tracing will be disabled
   ```
   解决方案：安装OpenTelemetry依赖或保持禁用状态
   Solution: Install OpenTelemetry dependencies or keep disabled

2. **工具注册警告** / **Tool Registration Warnings**
   ```
   警告: 注册工具 tool_name 时出错: validation error
   Warning: Error registering tool tool_name: validation error
   ```
   解决方案：检查工具参数定义是否正确
   Solution: Check if tool parameter definitions are correct

3. **端口冲突** / **Port Conflict**
   ```
   错误: 端口 8001 已被占用
   Error: Port 8001 is already in use
   ```
   解决方案：使用`--port`参数指定其他端口
   Solution: Use `--port` parameter to specify different port

### 日志级别 / Log Levels

使用`--log-level`参数控制日志详细程度：
Use `--log-level` parameter to control log verbosity:
- `DEBUG` - 详细调试信息 / Detailed debug information
- `INFO` - 常规运行信息（默认） / Regular runtime information (default)
- `WARNING` - 警告信息 / Warning information
- `ERROR` - 错误信息 / Error information

---

## 📄 许可证 / License

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 贡献 / Contributing

欢迎贡献代码！请：
Contributions are welcome! Please:
1. Fork仓库 / Fork the repository
2. 创建功能分支 / Create a feature branch
3. 为新功能添加测试 / Add tests for new functionality
4. 更新文档 / Update documentation
5. 提交Pull Request / Submit a Pull Request

## 📞 支持 / Support

如有问题和疑问：
For issues and questions:
- 在GitHub上创建Issue / Create an issue on GitHub
- 查看现有文档 / Check existing documentation
- 检查工具提供的错误消息和建议 / Review error messages and suggestions provided by tools
