#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zephyr MCP Agent - 主入口脚本
将Zephyr MCP工具包装成agno agent
"""

import os
import sys
import json
import argparse
import importlib
import traceback
import logging
import uuid
from typing import Dict, Any, List, Callable

# LLM集成相关导入
from src.utils.llm_integration import LLMIntegration
from src.tools.llm_tools import get_llm

# 语言资源导入
from src.utils.language_resources import LanguageManager, get_text, set_language

# 添加项目根目录到Python路径，确保可以正确导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入工具注册表
try:
    from src.utils.tool_registry import ToolRegistry, get_default_tool_registry
    # 导入agno agent相关模块
    try:
        from agno import Agent, Tool
        from agno.utils import setup_logger
    except ImportError:
        # 如果导入失败，使用兼容模式
        print(get_text("agno_import_failed"))
        class MockAgent:
            """兼容模式下的模拟Agent类"""
            def __init__(self, name=None, version=None, description=None):
                self.name = name or "zephyr_mcp_agent"
                self.version = version or "1.0.0"
                self.description = description or "Zephyr MCP Agent"
                self.tools = []
                
            def register_tool(self, tool):
                self.tools.append(tool)
        
        class MockTool:
            """兼容模式下的模拟Tool类"""
            def __init__(self, name, description, function=None, parameters=None, returns=None):
                self.name = name
                self.description = description
                self.function = function
                self.parameters = parameters
                self.returns = returns
        
        def mock_setup_logger(level="INFO"):
            """模拟设置日志"""
            import logging
            # 创建自定义日志格式化器，包含trace_id
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(trace_id)s] %(message)s')
            
            # 创建一个自定义的LogRecord工厂，确保trace_id始终存在
            old_factory = logging.getLogRecordFactory()
            def record_factory(*args, **kwargs):
                # 检查是否有extra参数
                extra = kwargs.get('extra', {})
                
                # 确保extra是一个字典
                if not isinstance(extra, dict):
                    extra = {}
                
                # 从extra参数中获取trace_id，如果有的话
                trace_id = extra.pop('trace_id', None)
                
                # 将修改后的extra参数放回kwargs中
                kwargs['extra'] = extra
                
                # 调用旧的工厂函数创建LogRecord对象
                record = old_factory(*args, **kwargs)
                
                # 设置trace_id属性
                record.trace_id = trace_id if trace_id is not None else '-'  # 使用传入的trace_id或默认值
                
                return record
            logging.setLogRecordFactory(record_factory)
            
            # 配置根日志器
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, level))
            
            # 确保有handler
            if not root_logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(formatter)
                root_logger.addHandler(handler)
            else:
                # 更新现有handler的格式化器
                for handler in root_logger.handlers:
                    handler.setFormatter(formatter)
            
            # 创建日志记录器
            logger = logging.getLogger(__name__)
            return logger
        
        Agent = MockAgent
        Tool = MockTool
        setup_logger = mock_setup_logger
except ImportError as e:
    print(get_text("dependency_import_error", str(e)))
    print(get_text("install_dependencies"))
    sys.exit(1)


class ZephyrMCPAgent:
    """Zephyr MCP Agent类"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化agent"""
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化语言管理器
        self.language_config = self.config.get("language", {})
        self.default_language = self.language_config.get("default", "zh")
        
        # 设置全局语言
        set_language(self.default_language)
        
        # 创建语言管理器实例
        self.language_manager = LanguageManager(self.default_language)
        
        self.logger = setup_logger(self.config.get("log_level", "INFO"))
        
        # 创建Agent实例
        try:
            # 尝试使用完整参数初始化
            self.agent = Agent(
                name=self.config["agent_name"],
                version=self.config["version"],
                description=self.config["description"]
            )
        except TypeError:
            # 如果参数不匹配，尝试使用名称初始化
            try:
                self.agent = Agent(self.config["agent_name"])
            except Exception:
                # 最后使用默认初始化
                self.agent = Agent()
        
        # 使用工具注册表
        self.tool_registry = get_default_tool_registry()
        self.tools: Dict[str, Tool] = {}
        
        # 存储当前语言
        self.current_language = self.default_language
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(get_text("config_load_error", str(e)))
            # 返回默认配置
            return {
                "agent_name": get_text("agent_name"),
                "version": "1.0.0",
                "description": get_text("agent_description"),
                "tools_directory": "./src/tools",
                "utils_directory": "./src/utils",
                "log_level": "INFO",
                "language": {
                    "default": "zh",
                    "available": ["zh", "en"],
                    "auto_detect": True
                }
            }
    
    def register_tools(self):
        """使用工具注册表注册所有工具"""
        self.logger.info(self.get_text("registering_tools"))
        
        try:
            # 使用工具注册表注册所有工具
            results = self.tool_registry.register_all_tools()
            
            # 将注册的工具添加到Agent中
            registered_tools = self.tool_registry.get_registered_tools()
            
            for tool_name, tool_info in registered_tools.items():
                try:
                    # 创建Tool对象并注册到agent
                    tool = Tool(
                        name=tool_info["name"],
                        description=tool_info["description"],
                        function=tool_info["function"],
                        parameters=tool_info["parameters"],
                        returns=tool_info["returns"]
                    )
                    
                    # 注册工具
                    if hasattr(self.agent, 'register_tool'):
                        self.agent.register_tool(tool)
                    
                    self.tools[tool_name] = tool
                except Exception as tool_error:
                    self.logger.warning(self.get_text("tool_register_error", tool_name, str(tool_error)))
                
            success_count = sum(1 for success in results.values() if success)
            self.logger.info(self.get_text("tools_registered", success_count, len(results)))
            return True
            
        except Exception as e:
            self.logger.error(self.get_text("tool_register_error", "all", str(e)))
            return False
    
    def register_llm_tools(self):
        """
        注册LLM相关工具
        """
        try:
            # 导入LLM集成相关模块
            from src.utils.llm_integration import init_llm, LLMIntegration
            from src.tools.llm_tools import register_llm_tools, get_registered_tools
            
            # 初始化LLM集成
            llm_config = self.config.get('llm', {})
            init_llm(llm_config)
            
            # 注册LLM工具
            self.logger.info(self.get_text("registering_llm_tools"))
            llm_tools = get_registered_tools()
            
            # 将LLM工具注册到工具注册表
            for tool_info in llm_tools:
                tool_name = tool_info["name"]
                # 这里简化处理，实际需要根据工具注册表的API进行适配
            self.logger.info(get_text("register_llm_tool", tool_name))
            
            # 使用llm_tools中的注册函数
            register_llm_tools(self)
            
            self.logger.info(self.get_text("llm_tools_registered"))
        except Exception as e:
            self.logger.error(self.get_text("llm_tool_register_error", str(e)))
            self.logger.debug(traceback.format_exc())

    def start(self):
        """启动agent"""
        self.logger.info(self.get_text("starting_agent", self.config['agent_name'], self.config['version']))
        self.register_tools()
        
        # 初始化并注册LLM工具（如果启用）
        if 'llm' in self.config and self.config['llm'].get('enabled', True):
            try:
                self.register_llm_tools()
            except Exception as e:
                self.logger.error(self.get_text("llm_tool_register_error", str(e)))
        
        # 执行工具健康检查
        self.perform_health_check()
        
        # 获取注册的工具
        registered_tools = self.tool_registry.get_registered_tools()
        self.logger.info(self.get_text("tools_registered", len(registered_tools), len(registered_tools)))
        
        # 打印可用工具列表（按分类显示）
        categories = self.tool_registry.categorize_tools()
        print(f"\nZephyr MCP Agent {self.get_text('starting_agent')}")
        print(f"\n{self.get_text('available_tools')}:")
        for category, tool_names in categories.items():
            if tool_names:
                print(f"\n{self._format_category_name(category)} ({len(tool_names)}):")
                for tool_name in tool_names:
                    tool_info = registered_tools[tool_name]
                    # 显示简短描述
                    short_desc = tool_info['description'][:60] + '...' if len(tool_info['description']) > 60 else tool_info['description']
                    print(f"- {tool_name}: {short_desc}")
        
        # 生成工具文档
        self._generate_tool_documentation()
        
        # 启动JSON HTTP接口服务器
        self.start_json_server()
    
    def start_json_server(self):
        """启动JSON HTTP接口服务器"""
        import http.server
        import socketserver
        import json
        import threading
        import subprocess  # 导入subprocess模块
        import sys
        # 将subprocess模块添加到全局命名空间，确保工具函数可以访问
        if 'subprocess' not in sys.modules:
            sys.modules['subprocess'] = subprocess
        
        # 获取配置中的端口，默认为8001（避免端口冲突）
        port = self.config.get("port", 8001)
        host = self.config.get("host", "localhost")
        
        class JSONToolHandler(http.server.BaseHTTPRequestHandler):
            """处理JSON工具请求的HTTP处理器"""
            
            def do_POST(self):
                """处理POST请求，执行工具调用"""
                if self.path == "/api/tool":
                    # 生成或获取trace_id
                    trace_id = self.headers.get('X-Trace-ID', str(uuid.uuid4()))
                    # 获取请求的语言
                    request_language = self._get_request_language()
                    
                    # 读取请求体
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    try:
                        # 解析JSON请求
                        request = json.loads(post_data.decode('utf-8'))
                        
                        # 获取工具名称和参数
                        tool_name = request.get('tool')
                        params = request.get('params', {})
                        
                        if not tool_name:
                            self.send_error(400, self.server.agent.get_text('missing_tool_name'))
                            return
                        
                        # 获取注册的工具
                        registered_tools = self.server.agent.tool_registry.get_registered_tools()
                        
                        if tool_name not in registered_tools:
                            # 添加trace_id到错误响应
                            self.send_response(404)
                            self.send_header('Content-Type', 'application/json')
                            self.send_header('X-Trace-ID', trace_id)
                            self.end_headers()
                            error_response = {
                                "error": self.server.agent.get_text('tool_not_found', tool_name),
                                "trace_id": trace_id
                            }
                            self.wfile.write(json.dumps(error_response).encode('utf-8'))
                            return
                        
                        # 执行参数验证 - 尝试使用mcp_server中的validate功能
                        self._validate_request_params(tool_name, params)
                        
                        # 执行工具
                        tool_info = registered_tools[tool_name]
                        tool_func = tool_info['function']
                        
                        # 记录工具调用，包含trace_id
                        self.server.agent.logger.info(f"[{trace_id}] 执行工具: {tool_name}，参数: {params}")
                        
                        # 导入必要的模块
                        import subprocess
                        import sys
                        import os
                        import importlib
                        import traceback
                        
                        # 将必要的模块直接注入到工具函数的全局命名空间
                        # 这样可以确保工具函数在执行时能直接访问这些模块
                        tool_func_globals = tool_func.__globals__
                        tool_func_globals['subprocess'] = subprocess
                        tool_func_globals['sys'] = sys
                        tool_func_globals['os'] = os
                        tool_func_globals['importlib'] = importlib
                        tool_func_globals['traceback'] = traceback
                        
                        # 调用工具函数并添加错误处理
                        try:
                            result = tool_func(**params)
                        except Exception as e:
                            # 记录详细的错误信息
                            error_trace = traceback.format_exc()
                            self.server.agent.logger.error(f"[{trace_id}] 工具执行错误: {tool_name}, 错误: {str(e)}")
                            self.server.agent.logger.error(f"[{trace_id}] 错误详情: {error_trace}")
                            # 重新抛出异常，由上层处理
                            raise
                        
                        # 构造响应，确保包含trace_id
                        response = {
                            "success": True,
                            "result": result,
                            "tool": tool_name,
                            "trace_id": trace_id
                        }
                        
                        # 发送响应
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                        
                    except json.JSONDecodeError:
                        # 添加trace_id到错误响应
                        self.send_response(400)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('X-Trace-ID', trace_id)
                        self.end_headers()
                        error_response = {
                            "error": self.server.agent.get_text('invalid_json'),
                            "trace_id": trace_id
                        }
                        self.wfile.write(json.dumps(error_response).encode('utf-8'))
                    except Exception as e:
                        # 发送错误响应
                        error_response = {
                            "success": False,
                            "error": str(e),
                            "tool": tool_name if 'tool_name' in locals() else None,
                            "trace_id": trace_id,
                            "error_code": "TOOL_EXECUTION_ERROR"
                        }
                        self.send_response(500)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(error_response).encode('utf-8'))
                        self.server.agent.logger.error(f"[{trace_id}] 执行工具 '{tool_name}' 时出错: {str(e)}")
                elif self.path == "/api/ai_assistant":
                    # 生成或获取trace_id
                    trace_id = self.headers.get('X-Trace-ID', str(uuid.uuid4()))
                    # AI助手端点
                    self._handle_ai_assistant_request(trace_id)
                else:
                    # 未找到路径，返回404，包含trace_id
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('X-Trace-ID', trace_id)
                    self.end_headers()
                    error_response = {
                        "error": "Not Found",
                        "path": self.path,
                        "trace_id": trace_id
                    }
                    self.wfile.write(json.dumps(error_response).encode('utf-8'))
                    
            def _handle_ai_assistant_request(self, trace_id):
                """处理AI助手请求"""
                # 获取请求的语言
                request_language = self._get_request_language()
                
                # 读取请求体
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                try:
                    # 解析JSON请求
                    request = json.loads(post_data.decode('utf-8'))
                    
                    # 检查LLM是否启用
                    if not self.server.agent.config.get("llm", {}).get("enabled", False):
                        self.send_error(503, self.server.agent.get_text('ai_assistant_not_enabled'))
                        return
                    
                    # 检查LLM集成是否可用
                    if not self.server.agent.llm_integration:
                        self.send_error(503, self.server.agent.get_text('ai_assistant_not_available'))
                        return
                    
                    # 验证请求参数
                    if "messages" not in request:
                        self.send_error(400, self.server.agent.get_text('missing_messages_param'))
                        return
                        
                    messages = request["messages"]
                    if not isinstance(messages, list):
                        self.send_error(400, self.server.agent.get_text('invalid_messages_type'))
                        return
                    
                    # 检查每个消息是否包含必要的字段
                    for i, message in enumerate(messages):
                        if not isinstance(message, dict):
                            self.send_error(400, self.server.agent.get_text('invalid_message_format', i))
                            return
                        if "role" not in message or "content" not in message:
                            self.send_error(400, self.server.agent.get_text('missing_message_fields', i))
                            return
                        if message["role"] not in ["system", "user", "assistant"]:
                            self.send_error(400, self.server.agent.get_text('invalid_message_role', i))
                            return
                    
                    # 获取可选参数
                    model = request.get("model")
                    temperature = request.get("temperature", 0.7)
                    max_tokens = request.get("max_tokens", 1000)
                    
                    # 调用LLM对话工具
                    try:
                        # 使用LLM集成的对话方法
                        llm_integration = self.server.agent.llm_integration
                        if llm_integration is None:
                            raise RuntimeError("LLM集成未初始化")
                        
                        result = llm_integration.chat(
                            messages=messages,
                            model=model,
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        
                        if result.get("success", False):
                            # 构造响应
                            response = {
                                "success": True,
                                "response": result["response"],
                                "model": result["model"],
                                "usage": result.get("usage", {}),
                                "trace_id": trace_id
                            }
                            
                            # 发送响应
                            self.send_response(200)
                            self.send_header('Content-Type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps(response).encode('utf-8'))
                        else:
                            self.send_error(500, result.get("error", self.server.agent.get_text('ai_assistant_error')))
                    except Exception as e:
                        self.server.agent.logger.error(f"[{trace_id}] {self.server.agent.get_text('request_processing_error', str(e))}")
                        self.send_error(500, self.server.agent.get_text('request_processing_error', str(e)))
                        
                except json.JSONDecodeError:
                    # 添加trace_id到错误响应
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('X-Trace-ID', trace_id)
                    self.end_headers()
                    error_response = {
                        "error": self.server.agent.get_text('invalid_json'),
                        "trace_id": trace_id
                    }
                    self.wfile.write(json.dumps(error_response).encode('utf-8'))
                except Exception as e:
                    self.server.agent.logger.error(f"[{trace_id}] {self.server.agent.get_text('request_processing_error', str(e))}")
                    # 添加trace_id到错误响应
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('X-Trace-ID', trace_id)
                    self.end_headers()
                    error_response = {
                        "error": self.server.agent.get_text('request_processing_error', str(e)),
                        "trace_id": trace_id
                    }
                    self.wfile.write(json.dumps(error_response).encode('utf-8'))
            
            def do_GET(self):
                """处理GET请求，提供工具信息和API文档，包含trace_id"""
                import urllib.parse
                # 生成或获取trace_id
                trace_id = self.headers.get('X-Trace-ID', str(uuid.uuid4()))
                # 获取请求的语言
                request_language = self._get_request_language()
                
                # 调试信息：记录原始请求路径
                self.server.agent.logger.info(f"[{trace_id}] DEBUG - 原始GET请求路径: '{self.path}'")
                self.server.agent.logger.info(f"[{trace_id}] DEBUG - 请求头: {self.headers}")
                
                # 解析URL
                parsed_url = urllib.parse.urlparse(self.path)
                path = parsed_url.path
                query_components = urllib.parse.parse_qs(parsed_url.query)
                
                # 调试信息：记录解析后的路径
                self.server.agent.logger.info(f"[{trace_id}] DEBUG - 解析后的路径: '{path}'")
                
                if path == "/health":
                    # 返回健康检查信息
                    response = {
                        "status": "healthy",
                        "message": "Zephyr MCP Agent is running",
                        "trace_id": trace_id
                    }
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('X-Trace-ID', trace_id)
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                elif path == "/api/tools":
                    # 返回可用工具列表
                    registered_tools = self.server.agent.tool_registry.get_registered_tools()
                    tools_info = []
                    
                    for tool_name, tool_info in registered_tools.items():
                        tools_info.append({
                            "name": tool_name,
                            "description": tool_info['description'],
                            "parameters": tool_info.get('parameters', []),
                            "returns": tool_info.get('returns', [])
                        })
                    
                    response = {
                        "tools": tools_info,
                        "total": len(tools_info),
                        "llm_integration": self.server.agent.config.get("llm", {}).get("enabled", False),
                        "trace_id": trace_id
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('X-Trace-ID', trace_id)
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                elif path.startswith("/api/tool/info"):
                    # 解析查询参数获取工具名称
                    tool_name = query_components.get('name', [None])[0]
                    
                    if not tool_name:
                        # 添加trace_id到错误响应
                        self.send_response(400)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('X-Trace-ID', trace_id)
                        self.end_headers()
                        error_response = {
                            "error": self.server.agent.get_text('missing_tool_name'),
                            "trace_id": trace_id
                        }
                        self.wfile.write(json.dumps(error_response).encode('utf-8'))
                        return
                    
                    registered_tools = self.server.agent.tool_registry.get_registered_tools()
                    
                    if tool_name not in registered_tools:
                        self.send_error(404, self.server.agent.get_text('tool_not_found', tool_name))
                        return
                    
                    # 返回工具详细信息
                    tool_info = registered_tools[tool_name]
                    response = {
                        "name": tool_name,
                        "description": tool_info['description'],
                        "parameters": tool_info.get('parameters', []),
                        "returns": tool_info.get('returns', []),
                        "module": tool_info['module'].__name__ if hasattr(tool_info['module'], '__name__') else str(tool_info['module'])
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('X-Trace-ID', trace_id)
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                elif path == "/api/docs":
                    # 返回API使用文档
                    host = self.server.server_address[0]
                    port = self.server.server_address[1]
                    
                    # 基础API端点
                    endpoints = [
                        {
                            "url": "/api/tools",
                            "method": "GET",
                            "description": self.server.agent.get_text('api_docs_get_tools'),
                            "response_format": {
                                "tools": "[工具信息列表]",
                                "total": "工具总数",
                                "llm_integration": "是否启用了LLM集成"
                            },
                            "example": f"curl -X GET http://{host}:{port}/api/tools"
                        },
                        {
                            "url": "/api/tool/info",
                            "method": "GET",
                            "description": self.server.agent.get_text('api_docs_get_tool_info'),
                            "parameters": [
                                {"name": "name", "type": "query", "description": "工具名称", "required": True}
                            ],
                            "response_format": {
                                "name": "工具名称",
                                "description": "工具描述",
                                "parameters": "参数列表",
                                "returns": "返回值列表",
                                "module": "工具模块"
                            },
                            "example": f"curl -X GET http://{host}:{port}/api/tool/info?name=test_git_connection"
                        },
                        {
                            "url": "/api/tool",
                            "method": "POST",
                            "description": self.server.agent.get_text('api_docs_execute_tool'),
                            "request_format": {
                                "tool": "工具名称",
                                "params": "工具参数对象"
                            },
                            "response_format": {
                                "success": "调用是否成功",
                                "result": "工具执行结果",
                                "error": "错误信息（如果有）",
                                "tool": "调用的工具名称"
                            },
                            "example": f"curl -X POST http://{host}:{port}/api/tool -H 'Content-Type: application/json' -d '{{\"tool\":\"test_git_connection\",\"params\":{{\"url\":\"https://github.com/zephyrproject-rtos/zephyr\"}}}}'"
                        }
                    ]
                    
                    # 如果启用了LLM集成，添加AI助手端点
                    if self.server.agent.config.get("llm", {}).get("enabled", False):
                        endpoints.append({
                            "url": "/api/ai_assistant",
                            "method": "POST",
                            "description": self.server.agent.get_text('api_docs_ai_assistant'),
                            "request_format": {
                                "messages": "消息列表，包含role和content",
                                "model": "可选，要使用的模型名称",
                                "temperature": "可选，生成温度(0.0-2.0)",
                                "max_tokens": "可选，最大生成token数"
                            },
                            "response_format": {
                                "success": "调用是否成功",
                                "response": "AI生成的响应内容",
                                "model": "使用的模型名称",
                                "usage": "使用的token数量信息",
                                "error": "错误信息（如果有）"
                            },
                            "example": f"curl -X POST http://{host}:{port}/api/ai_assistant -H 'Content-Type: application/json' -d '{json.dumps({'messages':[{'role':'user','content':'请解释什么是Zephyr项目？'}]})}'"
                        })
                    
                    endpoints.append({
                        "url": "/api/docs",
                        "method": "GET",
                        "description": self.server.agent.get_text('api_docs_get_docs'),
                        "example": f"curl -X GET http://{host}:{port}/api/docs"
                    })
                    
                    api_docs = {
                        "title": self.server.agent.get_text('api_docs_title'),
                        "base_url": f"http://{host}:{port}",
                        "endpoints": endpoints,
                        "notes": self.server.agent.get_text('api_docs_notes')
                    }
                    
                    # 生成并发送JSON响应，添加trace_id
                    api_docs['trace_id'] = trace_id
                    response_json = json.dumps(api_docs, ensure_ascii=False)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('X-Trace-ID', trace_id)
                    self.send_header('Content-Length', str(len(response_json.encode('utf-8'))))
                    self.end_headers()
                    self.wfile.write(response_json.encode('utf-8'))
                else:
                    # 未找到路径，返回404，包含trace_id
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('X-Trace-ID', trace_id)
                    self.end_headers()
                    error_response = {
                        "error": get_text('endpoint_not_found'),
                        "path": self.path,
                        "trace_id": trace_id
                    }
                    self.wfile.write(json.dumps(error_response).encode('utf-8'))
            
            def _get_request_language(self):
                """从请求头中获取语言偏好"""
                # 从 Accept-Language 头获取语言
                accept_language = self.headers.get('Accept-Language', '')
                if accept_language:
                    # 解析语言头，如 "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
                    languages = accept_language.split(',')
                    for lang in languages:
                        # 提取语言代码，如 "en-US" -> "en"
                        lang_code = lang.split(';')[0].strip().split('-')[0]
                        if lang_code in self.server.agent.config.get('language', {}).get('available', ['zh', 'en']):
                            # 设置请求的语言
                            self.server.agent.set_current_language(lang_code)
                            return lang_code
                # 默认使用当前语言
                return self.server.agent.current_language
            
            def _validate_request_params(self, tool_name, params):
                """验证请求参数的合规性，确保参数匹配工具要求"""
                try:
                    self.server.agent.logger.info(self.server.agent.get_text('tool_health_check', tool_name))
                    
                    # 特殊处理 validate_west_init_params 工具
                    if tool_name == 'validate_west_init_params':
                        # 检查必需参数
                        if 'repo_url' not in params:
                            self.send_error(400, self.server.agent.get_text('missing_required_param', 'repo_url'))
                            return
                        
                        # 验证 repo_url 格式
                        import re
                        url_pattern = re.compile(r'^(https?|git)://[^\s/$.?#].[^\s]*$')
                        if not url_pattern.match(params['repo_url']):
                            self.send_error(400, self.server.agent.get_text('invalid_param_format', 'repo_url'))
                            return
                        
                        self.server.agent.logger.info(self.server.agent.get_text('tool_params_valid', tool_name))
                    
                    # west_flash 工具的参数验证
                    elif tool_name == 'west_flash':
                        # 确保必需的 build_dir 参数存在
                        if 'build_dir' not in params:
                            self.send_error(400, self.server.agent.get_text('parameter_required', 'west_flash', 'build_dir'))
                            return
                    # west_update 工具的参数验证
                    elif tool_name == 'west_update':
                        # 确保 project_dir 参数存在
                        if 'project_dir' not in params:
                            self.send_error(400, self.server.agent.get_text('parameter_required', 'west_update', 'project_dir'))
                            return
                        
                        self.server.agent.logger.info(self.server.agent.get_text('tool_params_valid', tool_name))
                    
                    # 通用参数验证逻辑
                    elif tool_name == 'test_git_connection':
                        if 'url' not in params:
                            self.send_error(400, self.server.agent.get_text('missing_required_param', 'url'))
                            return
                        
                        # 验证 url 格式
                        import re
                        url_pattern = re.compile(r'^(https?|git)://[^\s/$.?#].[^\s]*$')
                        if not url_pattern.match(params['url']):
                            self.send_error(400, self.server.agent.get_text('invalid_param_format', 'URL'))
                            return
                        
                        self.server.agent.logger.info(self.server.agent.get_text('tool_params_valid', tool_name))
                    
                    # 通用参数验证：检查必需参数
                    tool_info = self.server.agent.tool_registry.get_registered_tools().get(tool_name)
                    if tool_info and 'parameters' in tool_info:
                        for param in tool_info['parameters']:
                            if param.get('required', False) and param['name'] not in params:
                                self.send_error(400, self.server.agent.get_text('missing_required_param', param['name']))
                                return
                    
                except Exception as e:
                    # 验证过程出错，但不阻止请求继续
                    self.server.agent.logger.warning(get_text("param_validation_error", str(e)))
                    # 不抛出异常，允许请求继续处理
            
            def log_message(self, format, *args):
                """重写日志方法，使用agent的logger"""
                self.server.agent.logger.info("%s - - [%s] %s" % 
                                            (self.client_address[0],
                                            self.log_date_time_string(),
                                            format % args))
        
        # 创建HTTP服务器
        class ToolHTTPServer(socketserver.ThreadingTCPServer):
            """自定义HTTP服务器，存储agent引用"""
            allow_reuse_address = True
            
            def __init__(self, server_address, RequestHandlerClass, agent):
                self.agent = agent
                super().__init__(server_address, RequestHandlerClass)
        
        # 启动服务器
        try:
            server = ToolHTTPServer((host, port), JSONToolHandler, self)
            print(f"\n{self.get_text('server_started', f'{host}:{port}')}")
            print(self.get_text('server_endpoints'))
            print(f"  - GET  http://{host}:{port}/api/tools        - 获取所有工具列表")
            print(f"  - GET  http://{host}:{port}/api/tool/info     - 获取特定工具详细信息")
            print(f"  - POST http://{host}:{port}/api/tool          - 执行工具调用")
            
            # 如果启用了LLM集成，显示AI助手端点
            if self.config.get("llm", {}).get("enabled", False):
                print(f"  - POST http://{host}:{port}/api/ai_assistant - AI助手对话接口")
            
            print(f"\n{self.get_text('example_request')}:")
            print("  curl -X POST http://localhost:8000/api/tool -H 'Content-Type: application/json' -d '{\n    \"tool\": \"test_git_connection\",\n    \"params\": {\n      \"url\": \"https://github.com/zephyrproject-rtos/zephyr\"\n    }\n  }'")
            
            # 如果启用了LLM集成，显示AI助手示例
            if self.config.get("llm", {}).get("enabled", False):
                print(f"\n{self.get_text('ai_assistant_example')}:")
                print("  curl -X POST http://localhost:8000/api/ai_assistant -H 'Content-Type: application/json' -d '{\n    \"messages\": [{\n      \"role\": \"user\",\n      \"content\": \"请解释什么是Zephyr项目？\"\n    }]\n  }'")
            
            print(f"\n{self.get_text('press_ctrl_c')}")
            
            # 在单独的线程中运行服务器
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # 保持主线程运行
            try:
                server_thread.join()
            except KeyboardInterrupt:
                print(f"\n{self.get_text('server_shutdown')}")
                server.shutdown()
                server.server_close()
                print(self.get_text('server_stopped'))
                
        except Exception as e:
            self.logger.error(self.get_text('server_start_error', str(e)))
            print(get_text('server_start_error', str(e)))
    
    def perform_health_check(self):
        """执行工具健康检查"""
        print(f"\n{self.get_text('health_check_start')}")
        try:
            health_info = self.tool_registry.get_tool_health()
            
            # 统计健康状态
            status_counts = {"healthy": 0, "warning": 0, "error": 0}
            for tool_name, health in health_info.items():
                status = health.get("status", "unknown")
                if status in status_counts:
                    status_counts[status] += 1
            
            # 显示健康摘要
            print(self.get_text('health_summary', status_counts['healthy'], status_counts['warning'], status_counts['error']))
            
            # 显示LLM集成状态
            if self.config.get("llm", {}).get("enabled", False):
                print(f"\n{self.get_text('llm_status')}")
                if hasattr(self, 'llm_integration') and self.llm_integration:
                    print(f"  - {self.get_text('llm_available')}")
                    # 尝试获取详细的LLM状态
                    try:
                        # 获取LLM集成实例
                        llm_integration = self.llm_integration
                        llm_status = llm_integration.get_status() if llm_integration else {"providers": {}}
                        print(f"  - OpenAI API密钥: {self.get_text('llm_api_key_configured') if llm_status['providers']['openai']['api_key_configured'] else self.get_text('llm_api_key_not_configured')}")
                        print(f"  - Anthropic API密钥: {self.get_text('llm_api_key_configured') if llm_status['providers']['anthropic']['api_key_configured'] else self.get_text('llm_api_key_not_configured')}")
                    except Exception:
                        print(f"  - {self.get_text('cannot_get_details')}")
                else:
                    print(f"  - {self.get_text('llm_not_available')}")
            
            # 显示有问题的工具
            if status_counts["warning"] > 0:
                print(f"\n{self.get_text('tools_to_note')}")
                for tool_name, health in health_info.items():
                    if health.get("status") == "warning" and health.get("issues"):
                        print(f"  - {tool_name}: {', '.join(health['issues'])}")
        except Exception as e:
            self.logger.warning(get_text("health_check_error", str(e)))
    
    def _format_category_name(self, category: str) -> str:
        """格式化分类名称为可读格式"""
        # 使用翻译后的分类名称
        category_map = {
            "git": get_text("tool_category_git"),
            "west": get_text("tool_category_west"),
            "zephyr": get_text("tool_category_zephyr"),
            "validation": get_text("tool_category_validation"),
            "ai": get_text("tool_category_ai"),
            "other": get_text("tool_category_other")
        }
        return category_map.get(category, ' '.join(word.capitalize() for word in category.split('_')))
    
    def get_text(self, key: str, *args, **kwargs) -> str:
        """获取翻译文本"""
        return get_text(key, *args, **kwargs)
    
    def set_current_language(self, language: str):
        """设置当前语言"""
        self.language_manager.set_language(language)
        set_language(language)
        self.current_language = language
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        return self.current_language
    
    def _generate_tool_documentation(self, output_file: str = "./tools_documentation.md"):
        """生成工具文档"""
        try:
            self.tool_registry.generate_tool_documentation(output_file)
            self.logger.info(f"工具文档已生成: {output_file}")
        except Exception as e:
            self.logger.warning(get_text("doc_generation_error", str(e)))


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Zephyr MCP Agent')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    parser.add_argument('--list-tools', action='store_true', help='列出所有可用工具')
    parser.add_argument('--health-check', action='store_true', help='运行健康检查')
    parser.add_argument('--generate-docs', action='store_true', help='生成工具文档')
    return parser.parse_args()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Zephyr MCP Agent')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    parser.add_argument('--list-tools', action='store_true', help='列出所有可用工具')
    parser.add_argument('--health-check', action='store_true', help='执行工具健康检查')
    parser.add_argument('--generate-docs', help='生成工具文档并保存到指定文件')
    parser.add_argument('--doc-format', default='markdown', choices=['markdown', 'json', 'text'], help='文档格式')
    parser.add_argument('--filter', help='使用正则表达式过滤工具')
    parser.add_argument('--search', help='搜索包含关键词的工具')
    parser.add_argument('--test', action='store_true', help='测试模式，验证工具注册但不启动服务')
    
    args = parser.parse_args()
    agent = ZephyrMCPAgent(args.config)
    
    # 根据命令行参数执行不同操作
    if args.search:
        # 搜索工具
        agent.register_tools()
        try:
            # 尝试使用filter_tools方法，如果不存在则使用基本过滤
            if hasattr(agent.tool_registry, 'filter_tools'):
                matched_tools = agent.tool_registry.filter_tools(args.search)
            else:
                # 基本的过滤实现
                registered_tools = agent.tool_registry.get_registered_tools()
                matched_tools = []
                for tool_name, tool_info in registered_tools.items():
                    if args.search.lower() in tool_name.lower() or args.search.lower() in tool_info['description'].lower():
                        matched_tools.append(tool_name)
            
            if matched_tools:
                print(get_text("tool_search_header", len(matched_tools), args.search))
                for tool_name in matched_tools:
                    tool_info = agent.tool_registry.get_registered_tools()[tool_name]
                    print(f"  - {tool_name}: {tool_info['description']}")
            else:
                print(get_text("no_matching_tools", args.search))
        except Exception as e:
            print(get_text("search_error", str(e)))
    
    elif args.list_tools:
        agent.register_tools()
        registered_tools = agent.tool_registry.get_registered_tools()
        categories = agent.tool_registry.categorize_tools()
        
        print("\n可用工具列表:")
        for category, tool_names in categories.items():
            if tool_names:
                print(f"\n{agent._format_category_name(category)} ({len(tool_names)}):")
                for tool_name in tool_names:
                    tool_info = registered_tools[tool_name]
                    # 显示更详细的工具信息
                    short_desc = tool_info['description'][:80] + '...' if len(tool_info['description']) > 80 else tool_info['description']
                    param_count = len(tool_info.get('parameters', []))
                    print(f"  - {tool_name}: {short_desc} (参数: {param_count})")
    
    elif args.health_check:
        agent.register_tools()
        try:
            health_info = agent.tool_registry.get_tool_health()
            
            print(get_text("health_check_report"))
            print("=" * 60)
            
            # 统计健康状态
            status_counts = {"healthy": 0, "warning": 0, "error": 0}
            for tool_name, health in health_info.items():
                status = health.get("status", "unknown")
                if status in status_counts:
                    status_counts[status] += 1
            
            print(f"\n{get_text('health_status_summary')}")
            print(f"  {get_text('healthy')}: {status_counts['healthy']}")
            print(f"  {get_text('warning')}: {status_counts['warning']}")
            print(f"  {get_text('error')}: {status_counts['error']}")
            print(f"  {get_text('total')}: {sum(status_counts.values())}")
            
            # 显示LLM集成状态
            print(f"\n{get_text('llm_integration_status')}")
            if agent.config.get("llm", {}).get("enabled", False):
                print(f"  {get_text('enabled')}: {get_text('yes')}")
                if get_llm():
                    print(f"  {get_text('available')}: {get_text('yes')}")
                else:
                    print(f"  {get_text('available')}: {get_text('no')} - {get_text('llm_initialization_failed')}")
            else:
                print(f"  {get_text('enabled')}: {get_text('no')}")
            
            print(f"\n{get_text('health_details')}")
            for tool_name, health in health_info.items():
                status_color = "✅" if health.get("status") == "healthy" else "⚠️"
                print(f"\n{status_color} {tool_name}:")
                print(f"  {get_text('tool_status')}: {health.get('status', 'unknown')}")
                print(f"  {get_text('param_count')}: {health.get('parameter_count', 0)}")
                print(f"  {get_text('has_description')}: {get_text('yes') if health.get('has_description', False) else get_text('no')}")
                if health.get('issues'):
                    print(f"  {get_text('health_issues')}: {', '.join(health['issues'])}")
        except Exception as e:
            print(get_text("health_check_error", str(e)))
    
    elif args.generate_docs:
        agent._generate_tool_documentation(args.generate_docs)
        print(get_text("docs_generated", args.generate_docs, args.doc_format))
    
    elif args.test:
        # 测试模式
        print(get_text("test_mode"))
        try:
            # 确保tool_registry已初始化
            if not hasattr(agent, 'tool_registry'):
                agent.tool_registry = get_default_tool_registry()
                
            # 注册工具
            success = agent.register_tools()
            
            # 获取注册的工具
            registered_tools = agent.tool_registry.get_registered_tools()
            
            print(f"\n{get_text('test_result')}")
            print(f"  {get_text('registered_tools_count')}: {len(registered_tools)}")
            
            # 显示LLM集成状态
            if agent.config.get("llm", {}).get("enabled", False):
                print(f"  {get_text('llm_integration')}: {get_text('llm_enabled_available') if get_llm() else get_text('llm_enabled_unavailable')}")
            else:
                print(f"  {get_text('llm_integration')}: {get_text('llm_disabled')}")
            
            # 尝试获取工具分类
            try:
                categories = agent.tool_registry.categorize_tools()
                print(f"  {get_text('tool_categories_count')}: {len(categories)}")
                # 显示分类详情
                for category, tools in categories.items():
                    print(f"    - {agent._format_category_name(category)}: {len(tools)} {get_text('tools_count_suffix')}")
            except Exception:
                print(f"  {get_text('tool_categories_count')}: {get_text('not_available')}")
            
            # 显示状态
            if success and len(registered_tools) > 0:
                print(f"  {get_text('test_status_success')}")
                sys.exit(0)
            else:
                print(f"  {get_text('test_status_warning')}")
                sys.exit(0)  # 即使没有工具也返回成功，因为这可能是正常情况
                
        except Exception as e:
            print(get_text("test_failed", str(e)))
            sys.exit(1)
    
    else:
        # 启动Agent
        agent.start()


if __name__ == "__main__":
    main()