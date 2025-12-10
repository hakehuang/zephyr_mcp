#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP服务器模块
处理JSON-RPC HTTP接口和请求处理
"""

import http.server
import socketserver
import json
import threading
import subprocess
import sys
import uuid
import traceback
import urllib.parse
from typing import Dict, Any, List, Optional
from http import HTTPStatus

# 导入OpenTelemetry集成
from opentelemetry_integration import OpenTelemetryManager


class JSONToolHandler(http.server.BaseHTTPRequestHandler):
    """处理JSON工具请求的HTTP处理器"""
    
    def __init__(self, *args, **kwargs):
        self.agent = kwargs.pop('agent', None)
        super().__init__(*args, **kwargs)
    
    def _get_request_language(self) -> str:
        """从请求头获取语言设置"""
        accept_language = self.headers.get('Accept-Language', '')
        if 'zh' in accept_language:
            return 'zh'
        elif 'en' in accept_language:
            return 'en'
        else:
            return self.server.agent.current_language
    
    def _validate_request_params(self, tool_name: str, params: Dict[str, Any]):
        """验证请求参数"""
        # 获取注册的工具信息
        registered_tools = self.server.agent.tool_registry.get_registered_tools()
        if tool_name not in registered_tools:
            self.send_error(404, self.server.agent.get_text('tool_not_found', tool_name))
            return
        
        tool_info = registered_tools[tool_name]
        
        # 特定工具的参数验证
        if tool_name == 'west_flash':
            if 'build_dir' not in params:
                self.send_error(400, self.server.agent.get_text('parameter_required', 'west_flash', 'build_dir'))
                return
        elif tool_name == 'west_update':
            if 'project_dir' not in params:
                self.send_error(400, self.server.agent.get_text('parameter_required', 'west_update', 'project_dir'))
                return
        elif tool_name == 'test_git_connection':
            if 'url' not in params:
                self.send_error(400, self.server.agent.get_text('missing_required_param', 'url'))
                return
            
            # 验证URL格式
            import re
            url_pattern = re.compile(r'^(https?|git)://[^\s/$.?#].[^\s]*$')
            if not url_pattern.match(params['url']):
                self.send_error(400, self.server.agent.get_text('invalid_param_format', 'URL'))
                return
        
        self.server.agent.logger.info(self.server.agent.get_text('tool_params_valid', tool_name))
    
    def _handle_tool_request(self, trace_id: str, span=None):
        """处理工具执行请求"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self.send_error(400, self.server.agent.get_text('missing_request_body'))
            if span:
                span.set_attribute("http.status_code", 400)
                span.set_attribute("error", True)
                span.set_attribute("error.message", "Missing request body")
            return
        
        post_data = self.rfile.read(content_length)
        
        try:
            # 解析JSON请求
            request = json.loads(post_data.decode('utf-8'))
            
            # 获取工具名称和参数
            tool_name = request.get('tool')
            params = request.get('params', {})
            
            if span:
                span.set_attribute("tool.name", tool_name)
            
            if not tool_name:
                self.send_error(400, self.server.agent.get_text('missing_tool_name'))
                if span:
                    span.set_attribute("http.status_code", 400)
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", "Missing tool name")
                return
            
            # 获取注册的工具
            registered_tools = self.server.agent.tool_registry.get_registered_tools()
            if tool_name not in registered_tools:
                self.send_error(404, self.server.agent.get_text('tool_not_found', tool_name))
                if span:
                    span.set_attribute("http.status_code", 404)
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", f"Tool not found: {tool_name}")
                return
            
            # 执行参数验证
            self._validate_request_params(tool_name, params)
            
            # 执行工具
            tool_info = registered_tools[tool_name]
            tool_func = tool_info['function']
            
            # 记录工具调用，包含trace_id
            self.server.agent.logger.info(f"[{trace_id}] 执行工具: {tool_name}，参数: {params}")
            
            # 导入必要的模块并注入到工具函数的全局命名空间
            tool_func_globals = tool_func.__globals__
            tool_func_globals['subprocess'] = subprocess
            tool_func_globals['sys'] = sys
            tool_func_globals['os'] = __import__('os')
            tool_func_globals['importlib'] = __import__('importlib')
            tool_func_globals['traceback'] = traceback
            
            # 执行工具函数
            result = tool_func(**params)
            
            # 构造响应
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
            self.send_header('X-Trace-ID', trace_id)
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
            
            if span:
                span.set_attribute("http.status_code", 500)
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
    
    def _handle_api_tools_request(self, trace_id: str, span=None):
        """处理/api/tools端点请求"""
        registered_tools = self.server.agent.tool_registry.get_registered_tools()
        
        # 构建工具信息列表
        tools_info = []
        for tool_name, tool_info in registered_tools.items():
            tools_info.append({
                "name": tool_name,
                "description": str(tool_info.get('description', '')),
                "parameters": tool_info.get('parameters', []),
                "returns": tool_info.get('returns', []),
                "module": str(tool_info.get('module', ''))
            })
        
        response = {
            "tools": tools_info,
            "total": len(tools_info),
            "llm_integration": self.server.agent.config.get("llm", {}).get("enabled", False)
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
        
        if span:
            span.set_attribute("http.status_code", 200)
            span.set_attribute("returned_tools_count", len(tools_info))
    
    def _handle_api_docs_request(self, trace_id: str, span=None):
        """处理/api/docs端点请求"""
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
                    "response": "AI助手回复",
                    "model": "使用的模型",
                    "usage": "token使用情况"
                },
                "example": f"curl -X POST http://{host}:{port}/api/ai_assistant -H 'Content-Type: application/json' -d '{{\"messages\":[{{\"role\":\"user\",\"content\":\"你好\"}}]}}'"
            })
        
        response = {
            "endpoints": endpoints,
            "version": self.server.agent.config.get("version", "1.0.0"),
            "agent_name": self.server.agent.config.get("agent_name", "Zephyr MCP Agent")
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
        
        if span:
            span.set_attribute("http.status_code", 200)
    
    def do_POST(self):
        """处理POST请求"""
        # 生成或获取trace_id
        trace_id = self.headers.get('X-Trace-ID', str(uuid.uuid4()))
        
        # 检查是否启用OpenTelemetry
        otel_manager = OpenTelemetryManager(self.server.agent.config, self.server.agent.logger)
        
        if otel_manager.is_enabled():
            # 使用追踪的版本
            span = otel_manager.create_span("HTTP_POST", {
                "http.method": "POST",
                "http.url": self.path,
                "trace_id": trace_id
            })
            
            try:
                if self.path == "/api/tool":
                    self._handle_tool_request(trace_id, span)
                elif self.path == "/api/ai_assistant":
                    # AI助手端点处理（简化版本）
                    self.send_response(501)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": "AI Assistant endpoint not implemented in this module",
                        "trace_id": trace_id
                    }).encode('utf-8'))
                    span.set_attribute("http.status_code", 501)
                else:
                    # 未找到路径，返回404
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
                    span.set_attribute("http.status_code", 404)
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", f"Path not found: {self.path}")
            except Exception as e:
                self.server.agent.logger.error(f"[{trace_id}] POST请求处理错误: {str(e)}")
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
            finally:
                otel_manager.end_span(span)
        else:
            # 不使用追踪的版本
            if self.path == "/api/tool":
                self._handle_tool_request(trace_id)
            elif self.path == "/api/ai_assistant":
                self.send_response(501)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "AI Assistant endpoint not implemented in this module",
                    "trace_id": trace_id
                }).encode('utf-8'))
            else:
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
    
    def do_GET(self):
        """处理GET请求"""
        # 生成或获取trace_id
        trace_id = self.headers.get('X-Trace-ID', str(uuid.uuid4()))
        
        # 解析路径和查询参数
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_components = urllib.parse.parse_qs(parsed_path.query)
        
        # 检查是否启用OpenTelemetry
        otel_manager = OpenTelemetryManager(self.server.agent.config, self.server.agent.logger)
        
        if otel_manager.is_enabled():
            span = otel_manager.create_span("HTTP_GET", {
                "http.method": "GET",
                "http.url": self.path,
                "trace_id": trace_id
            })
            
            try:
                if path == "/api/tools":
                    span.set_attribute("endpoint", "api_tools")
                    self._handle_api_tools_request(trace_id, span)
                elif path == "/api/docs":
                    span.set_attribute("endpoint", "api_docs")
                    self._handle_api_docs_request(trace_id, span)
                elif path.startswith("/api/tool/info"):
                    # 解析查询参数获取工具名称
                    tool_name = query_components.get('name', [None])[0]
                    span.set_attribute("endpoint", "api_tool_info")
                    
                    if not tool_name:
                        self.send_response(400)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('X-Trace-ID', trace_id)
                        self.end_headers()
                        error_response = {
                            "error": self.server.agent.get_text('missing_tool_name'),
                            "trace_id": trace_id
                        }
                        self.wfile.write(json.dumps(error_response).encode('utf-8'))
                        span.set_attribute("http.status_code", 400)
                        span.set_attribute("error", True)
                        span.set_attribute("error.message", "Missing tool name")
                    else:
                        span.set_attribute("tool.name", tool_name)
                        registered_tools = self.server.agent.tool_registry.get_registered_tools()
                        
                        if tool_name not in registered_tools:
                            self.send_response(404)
                            self.send_header('Content-Type', 'application/json')
                            self.send_header('X-Trace-ID', trace_id)
                            self.end_headers()
                            error_response = {
                                "error": self.server.agent.get_text('tool_not_found', tool_name),
                                "trace_id": trace_id
                            }
                            self.wfile.write(json.dumps(error_response).encode('utf-8'))
                            span.set_attribute("http.status_code", 404)
                            span.set_attribute("error", True)
                            span.set_attribute("error.message", f"Tool not found: {tool_name}")
                        else:
                            tool_info = registered_tools[tool_name]
                            response = {
                                "name": tool_name,
                                "description": tool_info.get('description', ''),
                                "parameters": tool_info.get('parameters', []),
                                "returns": tool_info.get('returns', []),
                                "module": tool_info.get('module', '')
                            }
                            self.send_response(200)
                            self.send_header('Content-Type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps(response).encode('utf-8'))
                            span.set_attribute("http.status_code", 200)
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('X-Trace-ID', trace_id)
                    self.end_headers()
                    error_response = {
                        "error": "Not Found",
                        "path": path,
                        "trace_id": trace_id
                    }
                    self.wfile.write(json.dumps(error_response).encode('utf-8'))
                    span.set_attribute("http.status_code", 404)
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", f"Path not found: {path}")
            except Exception as e:
                self.server.agent.logger.error(f"[{trace_id}] GET请求处理错误: {str(e)}")
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
            finally:
                otel_manager.end_span(span)
        else:
            # 不使用追踪的版本
            if path == "/api/tools":
                self._handle_api_tools_request(trace_id)
            elif path == "/api/docs":
                self._handle_api_docs_request(trace_id)
            elif path.startswith("/api/tool/info"):
                tool_name = query_components.get('name', [None])[0]
                
                if not tool_name:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('X-Trace-ID', trace_id)
                    self.end_headers()
                    error_response = {
                        "error": self.server.agent.get_text('missing_tool_name'),
                        "trace_id": trace_id
                    }
                    self.wfile.write(json.dumps(error_response).encode('utf-8'))
                else:
                    registered_tools = self.server.agent.tool_registry.get_registered_tools()
                    
                    if tool_name not in registered_tools:
                        self.send_response(404)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('X-Trace-ID', trace_id)
                        self.end_headers()
                        error_response = {
                            "error": self.server.agent.get_text('tool_not_found', tool_name),
                            "trace_id": trace_id
                        }
                        self.wfile.write(json.dumps(error_response).encode('utf-8'))
                    else:
                        tool_info = registered_tools[tool_name]
                        response = {
                            "name": tool_name,
                            "description": tool_info.get('description', ''),
                            "parameters": tool_info.get('parameters', []),
                            "returns": tool_info.get('returns', []),
                            "module": tool_info.get('module', '')
                        }
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('X-Trace-ID', trace_id)
                self.end_headers()
                error_response = {
                    "error": "Not Found",
                    "path": path,
                    "trace_id": trace_id
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def log_message(self, format, *args):
        """自定义日志消息格式"""
        self.server.agent.logger.info(f"[{self.headers.get('X-Trace-ID', 'unknown')}] {format % args}")


def start_json_server(agent):
    """启动JSON HTTP接口服务器"""
    # 获取配置中的端口，默认为8001
    port = agent.config.get("port", 8001)
    host = agent.config.get("host", "localhost")
    
    # 创建自定义的HTTP服务器类
    class JSONHTTPServer(socketserver.TCPServer):
        def __init__(self, server_address, handler_class):
            super().__init__(server_address, handler_class)
            self.agent = agent
    
    # 创建处理器类工厂
    def handler_factory(*args, **kwargs):
        return JSONToolHandler(*args, agent=agent, **kwargs)
    
    # 启动服务器
    with JSONHTTPServer((host, port), handler_factory) as httpd:
        agent.logger.info(f"JSON HTTP服务器启动在 http://{host}:{port}")
        agent.logger.info("可用端点:")
        agent.logger.info(f"  GET  http://{host}:{port}/api/tools - 获取可用工具列表")
        agent.logger.info(f"  GET  http://{host}:{port}/api/tool/info?name=<tool_name> - 获取工具详细信息")
        agent.logger.info(f"  POST http://{host}:{port}/api/tool - 执行工具")
        agent.logger.info(f"  GET  http://{host}:{port}/api/docs - 获取API文档")
        
        if agent.config.get("llm", {}).get("enabled", False):
            agent.logger.info(f"  POST http://{host}:{port}/api/ai_assistant - AI助手对话")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            agent.logger.info("服务器被用户中断")
        except Exception as e:
            agent.logger.error(f"服务器错误: {str(e)}")
        finally:
            httpd.server_close()
            agent.logger.info("服务器已关闭")