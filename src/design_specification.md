# Zephyr MCP 系统设计说明规格书

## 1. 系统概述

Zephyr MCP（Modular Control Plane）是一个灵活、可扩展的模块化控制平面系统，专为管理和执行各种工具而设计。该系统提供了统一的接口来注册、发现、执行和监控工具，支持工具健康检查、文档生成和LLM集成等功能。

### 1.1 核心功能

- 动态工具注册和发现机制
- 统一的HTTP API接口
- 工具参数验证和错误处理
- 工具健康检查和状态监控
- 自动生成工具文档
- LLM集成支持
- 完整的日志记录和追踪

### 1.2 系统架构

```
┌─────────────────┐      ┌───────────────────┐      ┌───────────────────────┐
│  HTTP客户端     │      │  ZephyrMCPAgent   │      │       工具实现        │
│                 │──────▶                  │──────▶                      │
│  (API调用)      │◀─────│  代理和服务器     │◀─────│   (各功能模块)        │
└─────────────────┘      └─────────┬─────────┘      └───────────────────────┘
                                   │
                         ┌─────────┴─────────┐
                         │                   │
               ┌─────────▼─────────┐ ┌───────▼─────────────┐
               │ ToolRegistry      │ │    ToolWrapper      │
               │ 工具注册表         │ │    工具包装器       │
               └───────────────────┘ └─────────────────────┘
```

## 2. 核心组件设计

### 2.1 ZephyrMCPAgent 代理类

ZephyrMCPAgent是整个系统的核心组件，负责初始化配置、注册工具、启动HTTP服务器和管理LLM集成。

**设计思路**：
- 采用模块化设计，将工具注册、服务器启动和LLM集成等功能解耦
- 提供统一的接口来管理系统的生命周期
- 支持多种操作模式（正常启动、健康检查、文档生成、测试模式等）

**核心功能**：
- 配置加载和初始化
- 工具注册和验证
- HTTP服务器启动和管理
- LLM集成初始化
- 健康状态检查
- 工具文档生成

**代码结构**：
```python
class ZephyrMCPAgent:
    def __init__(self, config_path):
        # 初始化配置、日志和工具注册表
        
    def load_config(self, config_path):
        # 加载配置文件
        
    def register_tools(self):
        # 注册工具到工具注册表
        
    def start(self):
        # 启动HTTP服务器和LLM集成
        
    def perform_health_check(self):
        # 执行健康检查
        
    def _generate_tool_documentation(self, output_file):
        # 生成工具文档
```

### 2.2 ToolRegistry 工具注册表

ToolRegistry负责工具的发现、注册、分类和健康检查，是系统的核心管理组件。

**设计思路**：
- 实现自动发现机制，支持从指定目录加载工具模块
- 提供统一的工具注册接口，支持单个工具注册和批量注册
- 维护工具的元数据，包括描述、参数和返回值信息
- 实现工具分类和过滤功能，方便用户查找和使用工具
- 提供工具健康检查功能，确保工具的可用性和正确性

**核心功能**：
- 工具发现和加载（discover_tools）
- 工具注册（register_tool, register_all_tools）
- 工具信息获取（get_registered_tools, get_tool_by_name）
- 工具分类（categorize_tools）
- 工具过滤和搜索（filter_tools）
- 工具健康检查（get_tool_health）
- 文档生成（generate_tool_documentation）

**代码结构**：
```python
class ToolRegistry:
    def __init__(self):
        # 初始化工具注册表
        
    def discover_tools(self, directory):
        # 发现指定目录中的工具
        
    def register_tool(self, tool_function):
        # 注册单个工具
        
    def register_all_tools(self, tool_functions):
        # 批量注册工具
        
    def get_registered_tools(self):
        # 获取所有已注册的工具
        
    def get_tool_by_name(self, tool_name):
        # 根据名称获取工具
        
    def categorize_tools(self):
        # 对工具进行分类
        
    def filter_tools(self, search_term):
        # 根据搜索词过滤工具
        
    def get_tool_health(self):
        # 获取工具健康状态
        
    def generate_tool_documentation(self, output_file, format="markdown"):
        # 生成工具文档
```

### 2.3 ToolWrapper 工具包装器

ToolWrapper负责包装工具函数，提取工具的元数据（如参数描述、返回值类型等），并提供工具验证功能。

**设计思路**：
- 自动从工具函数的文档字符串中提取参数描述、返回值和异常处理信息
- 提供工具验证机制，确保工具符合系统的要求
- 支持将工具转换为标准格式，便于在不同组件间传递

**核心功能**：
- 工具包装（wrap_tool）
- 参数信息提取（_extract_parameters）
- 文档字符串解析（_parse_param_descriptions）
- 返回值信息提取（_extract_returns）
- 工具验证（validate_tool, is_valid_tool）
- 工具描述对象创建（create_agno_tool）

**代码结构**：
```python
class ToolWrapper:
    @staticmethod
    def wrap_tool(tool_function):
        # 包装工具函数，提取元数据
        
    @staticmethod
    def _extract_parameters(tool_function):
        # 提取工具参数信息
        
    @staticmethod
    def _parse_param_descriptions(docstring):
        # 解析文档字符串中的参数描述
        
    @staticmethod
    def _extract_returns(docstring):
        # 提取返回值信息
        
    @staticmethod
    def validate_tool(tool_function):
        # 验证工具是否符合要求
        
    @staticmethod
    def is_valid_tool(tool_function):
        # 检查工具是否有效

# 工具装饰器
def create_tool_wrapper(tool_function):
    # 创建工具包装器装饰器
```

### 2.4 JSONToolHandler HTTP处理器

JSONToolHandler是HTTP服务器的核心组件，负责处理工具调用请求、参数验证、错误处理和响应构造。

**设计思路**：
- 实现RESTful API接口，支持工具调用、工具信息查询和文档获取
- 提供参数验证机制，确保工具调用的安全性和正确性
- 实现错误处理机制，返回标准的错误响应
- 支持追踪ID生成，便于问题排查和日志记录

**核心功能**：
- 处理工具调用请求（do_POST）
- 处理工具信息查询请求（do_GET）
- 参数验证（_validate_request_params）
- 请求解析和处理（_ai_assistant_request）
- 错误处理和响应构造

**代码结构**：
```python
class JSONToolHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 处理POST请求，执行工具调用
        
    def do_GET(self):
        # 处理GET请求，提供工具信息和文档
        
    def _validate_request_params(self, tool_name, params):
        # 验证请求参数
        
    def _ai_assistant_request(self, request_data):
        # 处理AI助手请求
        
    def log_message(self, format, *args):
        # 自定义日志记录格式
```

## 3. 系统工作流程

### 3.1 系统启动流程

1. 解析命令行参数
2. 初始化ZephyrMCPAgent
3. 加载配置文件
4. 注册工具到工具注册表
5. 初始化LLM集成（如果启用）
6. 执行健康检查
7. 启动HTTP服务器

### 3.2 工具调用流程

1. 客户端发送HTTP请求到服务器
2. JSONToolHandler接收并解析请求
3. 生成追踪ID（trace_id）
4. 验证请求参数
5. 调用相应的工具函数
6. 捕获并处理异常
7. 构造响应（成功或失败）
8. 返回JSON格式的响应

### 3.3 工具注册流程

1. 扫描指定目录下的工具模块
2. 加载工具模块
3. 提取工具函数
4. 验证工具函数
5. 提取工具元数据
6. 注册到工具注册表

## 4. API接口设计

Zephyr MCP提供了以下RESTful API接口：

### 4.1 /api/tools

**方法**: GET
**功能**: 获取所有可用工具的列表
**响应格式**: JSON数组，包含工具名称和描述

### 4.2 /api/tool/info

**方法**: GET
**功能**: 获取指定工具的详细信息
**参数**: tool_name - 工具名称
**响应格式**: JSON对象，包含工具的详细信息（描述、参数、返回值等）

### 4.3 /api/tool

**方法**: POST
**功能**: 执行工具调用
**请求体**: JSON对象，包含tool_name和params字段
**响应格式**: JSON对象，包含执行结果或错误信息

### 4.4 /api/ai_assistant

**方法**: POST
**功能**: 处理AI助手请求
**请求体**: JSON对象，包含AI助手所需的信息
**响应格式**: JSON对象，包含AI助手的响应或错误信息

### 4.5 /api/docs

**方法**: GET
**功能**: 获取API文档
**响应格式**: HTML格式的API文档

## 5. 配置设计

Zephyr MCP支持通过JSON配置文件进行配置，主要配置项包括：

### 5.1 基本配置

- `port`: HTTP服务器端口
- `host`: HTTP服务器主机
- `log_level`: 日志级别

### 5.2 工具配置

- `tools_directory`: 工具模块目录
- `tools_pattern`: 工具模块匹配模式

### 5.3 LLM配置

- `enabled`: 是否启用LLM集成
- `providers`: LLM提供商配置
  - `openai`: OpenAI配置
    - `api_key`: OpenAI API密钥
  - `anthropic`: Anthropic配置
    - `api_key`: Anthropic API密钥
  - `deepseek`: DeepSeek配置
    - `api_key`: DeepSeek API密钥

## 6. 错误处理设计

Zephyr MCP实现了全面的错误处理机制，包括：

### 6.1 错误类型

- 参数错误：请求参数不合法或缺失
- 工具错误：工具执行失败
- 系统错误：系统内部错误
- 权限错误：访问权限不足

### 6.2 错误响应格式

所有错误响应都采用统一的JSON格式：

```json
{
  "error": {
    "code": "错误代码",
    "message": "错误消息",
    "details": "错误详情"
  },
  "trace_id": "追踪ID"
}
```

## 7. 日志和监控设计

### 7.1 日志设计

- 支持多级别日志（DEBUG, INFO, WARNING, ERROR）
- 日志包含时间戳、级别、消息和追踪ID
- 支持自定义日志格式

### 7.2 监控设计

- 工具健康检查机制
- 工具状态统计（健康、警告、错误）
- LLM集成状态监控

## 8. 扩展性设计

Zephyr MCP采用了以下扩展性设计：

### 8.1 模块化架构

- 核心组件解耦，便于扩展和维护
- 工具注册机制支持动态添加新工具

### 8.2 插件化设计

- 支持通过插件机制扩展功能
- 工具模块可以独立开发和部署

### 8.3 集成支持

- 支持LLM集成扩展
- 提供标准接口便于与其他系统集成

## 9. 安全性设计

### 9.1 参数验证

- 严格的参数类型和范围验证
- 防止注入攻击

### 9.2 错误信息保护

- 避免暴露敏感信息
- 提供友好的错误提示

### 9.3 访问控制（预留）

- 预留访问控制接口，可扩展实现认证和授权

## 10. 部署和运维

### 10.1 部署方式

- 支持本地部署和容器化部署
- 提供命令行参数控制不同的运行模式

### 10.2 运维工具

- 健康检查命令
- 工具文档生成
- 工具列表和搜索功能

## 11. 测试和验证

### 11.1 测试模式

- 提供测试模式，验证工具注册但不启动服务
- 支持工具健康状态检查

### 11.2 验证机制

- 工具参数验证
- 工具函数签名检查
- 文档完整性验证

## 12. 总结

Zephyr MCP是一个设计精良、功能全面的模块化控制平面系统，具有以下优势：

1. **灵活的模块化设计**：核心组件解耦，便于扩展和维护
2. **统一的工具管理**：提供统一的接口来注册、发现、执行和监控工具
3. **完整的API接口**：RESTful API设计，便于与其他系统集成
4. **强大的错误处理**：全面的错误处理机制，提供友好的错误提示
5. **丰富的运维工具**：支持健康检查、文档生成等运维功能
6. **LLM集成支持**：内置LLM集成功能，增强系统智能性

Zephyr MCP适用于需要统一管理和执行多种工具的场景，如DevOps工具链、自动化测试平台、集成开发环境等。