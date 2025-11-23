# Zephyr MCP System Design Specification

## 1. System Overview

Zephyr MCP (Modular Control Plane) is a flexible, scalable modular control plane system designed for managing and executing various tools. The system provides a unified interface for registering, discovering, executing, and monitoring tools, supporting features such as tool health checks, documentation generation, and LLM integration.

### 1.1 Core Features

- Dynamic tool registration and discovery mechanism
- Unified HTTP API interface
- Tool parameter validation and error handling
- Tool health check and status monitoring
- Automatic tool documentation generation
- LLM integration support
- Comprehensive logging and tracing

### 1.2 System Architecture

```
┌─────────────────┐      ┌───────────────────┐      ┌───────────────────────┐
│  HTTP Client    │      │  ZephyrMCPAgent   │      │    Tool Implementations│
│                 │──────▶                  │──────▶                      │
│  (API Calls)    │◀─────│  Agent & Server   │◀─────│   (Function Modules)   │
└─────────────────┘      └─────────┬─────────┘      └───────────────────────┘
                                   │
                         ┌─────────┴─────────┐
                         │                   │
               ┌─────────▼─────────┐ ┌───────▼─────────────┐
               │ ToolRegistry      │ │    ToolWrapper      │
               │  Tool Registry    │ │    Tool Wrapper     │
               └───────────────────┘ └─────────────────────┘
```

## 2. Core Component Design

### 2.1 ZephyrMCPAgent Class

ZephyrMCPAgent is the core component of the entire system, responsible for initializing configuration, registering tools, starting HTTP servers, and managing LLM integration.

**Design Approach**:
- Modular design that decouples tool registration, server startup, and LLM integration
- Provides a unified interface to manage the system's lifecycle
- Supports multiple operation modes (normal startup, health check, documentation generation, test mode, etc.)

**Core Features**:
- Configuration loading and initialization
- Tool registration and validation
- HTTP server startup and management
- LLM integration initialization
- Health status checking
- Tool documentation generation

**Code Structure**:
```python
class ZephyrMCPAgent:
    def __init__(self, config_path):
        # Initialize configuration, logging, and tool registry
        
    def load_config(self, config_path):
        # Load configuration file
        
    def register_tools(self):
        # Register tools to tool registry
        
    def start(self):
        # Start HTTP server and LLM integration
        
    def perform_health_check(self):
        # Perform health check
        
    def _generate_tool_documentation(self, output_file):
        # Generate tool documentation
```

### 2.2 ToolRegistry Component

ToolRegistry is responsible for tool discovery, registration, categorization, and health checking, serving as the core management component of the system.

**Design Approach**:
- Implements automatic discovery mechanism to load tool modules from specified directories
- Provides a unified tool registration interface supporting single tool registration and batch registration
- Maintains tool metadata including description, parameter, and return value information
- Implements tool categorization and filtering functionality for easy lookup and use
- Provides tool health check functionality to ensure tool availability and correctness

**Core Features**:
- Tool discovery and loading (discover_tools)
- Tool registration (register_tool, register_all_tools)
- Tool information retrieval (get_registered_tools, get_tool_by_name)
- Tool categorization (categorize_tools)
- Tool filtering and searching (filter_tools)
- Tool health checking (get_tool_health)
- Documentation generation (generate_tool_documentation)

**Code Structure**:
```python
class ToolRegistry:
    def __init__(self):
        # Initialize tool registry
        
    def discover_tools(self, directory):
        # Discover tools in the specified directory
        
    def register_tool(self, tool_function):
        # Register a single tool
        
    def register_all_tools(self, tool_functions):
        # Register multiple tools in batch
        
    def get_registered_tools(self):
        # Get all registered tools
        
    def get_tool_by_name(self, tool_name):
        # Get tool by name
        
    def categorize_tools(self):
        # Categorize tools
        
    def filter_tools(self, search_term):
        # Filter tools based on search term
        
    def get_tool_health(self):
        # Get tool health status
        
    def generate_tool_documentation(self, output_file, format="markdown"):
        # Generate tool documentation
```

### 2.3 ToolWrapper Component

ToolWrapper is responsible for wrapping tool functions, extracting tool metadata (such as parameter descriptions, return value types, etc.), and providing tool validation functionality.

**Design Approach**:
- Automatically extract parameter descriptions, return values, and exception handling information from tool function docstrings
- Provide tool validation mechanism to ensure tools meet system requirements
- Support conversion of tools to standard format for easy passing between different components

**Core Features**:
- Tool wrapping (wrap_tool)
- Parameter information extraction (_extract_parameters)
- Docstring parsing (_parse_param_descriptions)
- Return value information extraction (_extract_returns)
- Tool validation (validate_tool, is_valid_tool)
- Tool description object creation (create_agno_tool)

**Code Structure**:
```python
class ToolWrapper:
    @staticmethod
    def wrap_tool(tool_function):
        # Wrap tool function and extract metadata
        
    @staticmethod
    def _extract_parameters(tool_function):
        # Extract tool parameter information
        
    @staticmethod
    def _parse_param_descriptions(docstring):
        # Parse parameter descriptions from docstring
        
    @staticmethod
    def _extract_returns(docstring):
        # Extract return value information
        
    @staticmethod
    def validate_tool(tool_function):
        # Validate if tool meets requirements
        
    @staticmethod
    def is_valid_tool(tool_function):
        # Check if tool is valid

# Tool decorator
def create_tool_wrapper(tool_function):
    # Create tool wrapper decorator
```

### 2.4 JSONToolHandler HTTP Handler

JSONToolHandler is the core component of the HTTP server, responsible for handling tool call requests, parameter validation, error handling, and response construction.

**Design Approach**:
- Implement RESTful API interfaces supporting tool calls, tool information queries, and documentation retrieval
- Provide parameter validation mechanism to ensure security and correctness of tool calls
- Implement error handling mechanism to return standardized error responses
- Support trace ID generation for problem troubleshooting and log recording

**Core Features**:
- Handling tool call requests (do_POST)
- Handling tool information query requests (do_GET)
- Parameter validation (_validate_request_params)
- Request parsing and processing (_ai_assistant_request)
- Error handling and response construction

**Code Structure**:
```python
class JSONToolHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Handle POST requests and execute tool calls
        
    def do_GET(self):
        # Handle GET requests and provide tool information and documentation
        
    def _validate_request_params(self, tool_name, params):
        # Validate request parameters
        
    def _ai_assistant_request(self, request_data):
        # Handle AI assistant requests
        
    def log_message(self, format, *args):
        # Custom log message format
```

## 3. System Workflow

### 3.1 System Startup Flow

1. Parse command line parameters
2. Initialize ZephyrMCPAgent
3. Load configuration file
4. Register tools to tool registry
5. Initialize LLM integration (if enabled)
6. Perform health check
7. Start HTTP server

### 3.2 Tool Call Flow

1. Client sends HTTP request to server
2. JSONToolHandler receives and parses request
3. Generate trace ID
4. Validate request parameters
5. Call corresponding tool function
6. Catch and handle exceptions
7. Construct response (success or failure)
8. Return JSON format response

### 3.3 Tool Registration Flow

1. Scan tool modules in specified directory
2. Load tool modules
3. Extract tool functions
4. Validate tool functions
5. Extract tool metadata
6. Register to tool registry

## 4. API Interface Design

Zephyr MCP provides the following RESTful API interfaces:

### 4.1 /api/tools

**Method**: GET
**Function**: Get list of all available tools
**Response Format**: JSON array containing tool names and descriptions

### 4.2 /api/tool/info

**Method**: GET
**Function**: Get detailed information about a specified tool
**Parameter**: tool_name - Tool name
**Response Format**: JSON object containing detailed tool information (description, parameters, return values, etc.)

### 4.3 /api/tool

**Method**: POST
**Function**: Execute tool call
**Request Body**: JSON object containing tool_name and params fields
**Response Format**: JSON object containing execution results or error information

### 4.4 /api/ai_assistant

**Method**: POST
**Function**: Process AI assistant requests
**Request Body**: JSON object containing information needed by the AI assistant
**Response Format**: JSON object containing AI assistant response or error information

### 4.5 /api/docs

**Method**: GET
**Function**: Get API documentation
**Response Format**: HTML format API documentation

## 5. Configuration Design

Zephyr MCP supports configuration via JSON configuration files, with main configuration items including:

### 5.1 Basic Configuration

- `port`: HTTP server port
- `host`: HTTP server host
- `log_level`: Log level

### 5.2 Tool Configuration

- `tools_directory`: Tool module directory
- `tools_pattern`: Tool module matching pattern

### 5.3 LLM Configuration

- `enabled`: Whether to enable LLM integration
- `providers`: LLM provider configurations
  - `openai`: OpenAI configuration
    - `api_key`: OpenAI API key
  - `anthropic`: Anthropic configuration
    - `api_key`: Anthropic API key
  - `deepseek`: DeepSeek configuration
    - `api_key`: DeepSeek API key

## 6. Error Handling Design

Zephyr MCP implements comprehensive error handling mechanisms, including:

### 6.1 Error Types

- Parameter errors: Invalid or missing request parameters
- Tool errors: Tool execution failures
- System errors: Internal system errors
- Permission errors: Insufficient access permissions

### 6.2 Error Response Format

All error responses use a unified JSON format:

```json
{
  "error": {
    "code": "error code",
    "message": "error message",
    "details": "error details"
  },
  "trace_id": "trace ID"
}
```

## 7. Logging and Monitoring Design

### 7.1 Logging Design

- Support for multi-level logging (DEBUG, INFO, WARNING, ERROR)
- Logs include timestamps, levels, messages, and trace IDs
- Support for custom log formats

### 7.2 Monitoring Design

- Tool health check mechanism
- Tool status statistics (healthy, warning, error)
- LLM integration status monitoring

## 8. Extensibility Design

Zephyr MCP adopts the following extensibility designs:

### 8.1 Modular Architecture

- Core components are decoupled for easy extension and maintenance
- Tool registration mechanism supports dynamically adding new tools

### 8.2 Plugin-based Design

- Support for extending functionality through plugin mechanisms
- Tool modules can be developed and deployed independently

### 8.3 Integration Support

- Support for LLM integration extensions
- Provide standard interfaces for easy integration with other systems

## 9. Security Design

### 9.1 Parameter Validation

- Strict parameter type and range validation
- Prevention of injection attacks

### 9.2 Error Information Protection

- Avoid exposing sensitive information
- Provide user-friendly error prompts

### 9.3 Access Control (Reserved)

- Reserved access control interfaces for extensible implementation of authentication and authorization

## 10. Deployment and Operations

### 10.1 Deployment Methods

- Support for local deployment and containerized deployment
- Provide command line parameters to control different operation modes

### 10.2 Operation Tools

- Health check commands
- Tool documentation generation
- Tool listing and searching functionality

## 11. Testing and Validation

### 11.1 Testing Mode

- Provide testing mode to verify tool registration without starting the service
- Support tool health status checking

### 11.2 Validation Mechanisms

- Tool parameter validation
- Tool function signature checking
- Documentation completeness validation

## 12. Summary

Zephyr MCP is a well-designed, feature-rich modular control plane system with the following advantages:

1. **Flexible Modular Design**: Core components are decoupled for easy extension and maintenance
2. **Unified Tool Management**: Provides a unified interface for registering, discovering, executing, and monitoring tools
3. **Complete API Interface**: RESTful API design for easy integration with other systems
4. **Powerful Error Handling**: Comprehensive error handling mechanism providing friendly error prompts
5. **Rich Operation Tools**: Support for health checks, documentation generation, and other operational functions
6. **LLM Integration Support**: Built-in LLM integration functionality to enhance system intelligence

Zephyr MCP is suitable for scenarios requiring unified management and execution of multiple tools, such as DevOps toolchains, automated testing platforms, integrated development environments, and more.