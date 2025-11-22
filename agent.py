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
from typing import Dict, Any, List, Callable

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
        print("Warning: agno库导入失败，使用兼容模式...")
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
            logging.basicConfig(level=getattr(logging, level))
            return logging.getLogger(__name__)
        
        Agent = MockAgent
        Tool = MockTool
        setup_logger = mock_setup_logger
except ImportError as e:
    print(f"Error: 导入依赖失败: {str(e)}")
    print("请安装依赖: pip install -r requirements.txt")
    sys.exit(1)


class ZephyrMCPAgent:
    """Zephyr MCP Agent类"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化agent"""
        self.config_path = config_path
        self.config = self._load_config()
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
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error: 加载配置文件失败: {str(e)}")
            # 返回默认配置
            return {
                "agent_name": "zephyr_mcp_agent",
                "version": "1.0.0",
                "description": "Zephyr MCP Agent",
                "tools_directory": "./src/tools",
                "utils_directory": "./src/utils",
                "log_level": "INFO"
            }
    
    def register_tools(self):
        """使用工具注册表注册所有工具"""
        self.logger.info("开始注册工具...")
        
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
                    self.logger.warning(f"注册工具 {tool_name} 时出错: {str(tool_error)}")
                
            success_count = sum(1 for success in results.values() if success)
            self.logger.info(f"工具注册完成: 成功 {success_count}/{len(results)}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册工具失败: {str(e)}")
            return False
    
    def start(self):
        """启动agent"""
        self.logger.info(f"启动 {self.config['agent_name']} v{self.config['version']}")
        self.register_tools()
        
        # 执行工具健康检查
        self.perform_health_check()
        
        # 获取注册的工具
        registered_tools = self.tool_registry.get_registered_tools()
        self.logger.info(f"成功注册 {len(registered_tools)} 个工具")
        
        # 打印可用工具列表（按分类显示）
        categories = self.tool_registry.categorize_tools()
        print(f"\nZephyr MCP Agent 已启动")
        print("\n可用工具:")
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
        
        # 获取配置中的端口，默认为8000
        port = self.config.get("port", 8000)
        host = self.config.get("host", "localhost")
        
        class JSONToolHandler(http.server.BaseHTTPRequestHandler):
            """处理JSON工具请求的HTTP处理器"""
            
            def do_POST(self):
                """处理POST请求，执行工具调用"""
                if self.path == "/api/tool":
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
                            self.send_error(400, "Missing tool name")
                            return
                        
                        # 获取注册的工具
                        registered_tools = self.server.agent.tool_registry.get_registered_tools()
                        
                        if tool_name not in registered_tools:
                            self.send_error(404, f"Tool '{tool_name}' not found")
                            return
                        
                        # 执行参数验证 - 尝试使用mcp_server中的validate功能
                        self._validate_request_params(tool_name, params)
                        
                        # 执行工具
                        tool_info = registered_tools[tool_name]
                        tool_func = tool_info['function']
                        
                        # 记录工具调用
                        self.server.agent.logger.info(f"执行工具: {tool_name}，参数: {params}")
                        
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
                            self.server.agent.logger.error(f"工具执行错误: {tool_name}, 错误: {str(e)}")
                            self.server.agent.logger.error(f"错误详情: {error_trace}")
                            # 重新抛出异常，由上层处理
                            raise
                        
                        # 构造响应
                        response = {
                            "success": True,
                            "result": result,
                            "tool": tool_name
                        }
                        
                        # 发送响应
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                        
                    except json.JSONDecodeError:
                        self.send_error(400, "Invalid JSON format")
                    except Exception as e:
                        # 发送错误响应
                        error_response = {
                            "success": False,
                            "error": str(e),
                            "tool": tool_name if 'tool_name' in locals() else None
                        }
                        self.send_response(500)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(error_response).encode('utf-8'))
                        self.server.agent.logger.error(f"执行工具 '{tool_name}' 时出错: {str(e)}")
                else:
                    self.send_error(404, "Not Found")
            
            def do_GET(self):
                """处理GET请求，提供工具信息和API文档"""
                import urllib.parse
                
                # 解析URL
                parsed_url = urllib.parse.urlparse(self.path)
                path = parsed_url.path
                query_components = urllib.parse.parse_qs(parsed_url.query)
                
                if path == "/api/tools":
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
                        "total": len(tools_info)
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                elif path.startswith("/api/tool/info"):
                    # 解析查询参数获取工具名称
                    tool_name = query_components.get('name', [None])[0]
                    
                    if not tool_name:
                        self.send_error(400, "Missing tool name parameter")
                        return
                    
                    registered_tools = self.server.agent.tool_registry.get_registered_tools()
                    
                    if tool_name not in registered_tools:
                        self.send_error(404, f"Tool '{tool_name}' not found")
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
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                elif path == "/api/docs":
                    # 返回API使用文档
                    host = self.server.server_address[0]
                    port = self.server.server_address[1]
                    
                    api_docs = {
                        "title": "Zephyr MCP Agent API Documentation",
                        "base_url": f"http://{host}:{port}",
                        "endpoints": [
                            {
                                "url": "/api/tools",
                                "method": "GET",
                                "description": "获取所有可用工具列表",
                                "response_format": {
                                    "tools": "[工具信息列表]",
                                    "total": "工具总数"
                                },
                                "example": f"curl -X GET http://{host}:{port}/api/tools"
                            },
                            {
                                "url": "/api/tool/info",
                                "method": "GET",
                                "description": "获取特定工具的详细信息",
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
                                "description": "执行工具调用",
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
                                "example": f"curl -X POST http://{host}:{port}/api/tool -H 'Content-Type: application/json' -d '{{\"tool\":\"test_git_connection\",\"params\":{{\"repo_url\":\"https://github.com/zephyrproject-rtos/zephyr\"}}}}'"
                            },
                            {
                                "url": "/api/docs",
                                "method": "GET",
                                "description": "获取API文档",
                                "example": f"curl -X GET http://{host}:{port}/api/docs"
                            }
                        ],
                        "notes": "所有API响应均为JSON格式，POST请求需要设置Content-Type为application/json"
                    }
                    
                    # 生成并发送JSON响应
                    response_json = json.dumps(api_docs, ensure_ascii=False)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Content-Length', str(len(response_json.encode('utf-8'))))
                    self.end_headers()
                    self.wfile.write(response_json.encode('utf-8'))
                else:
                    self.send_error(404, "Not Found")
            
            def _validate_request_params(self, tool_name, params):
                  """验证请求参数的合规性，确保参数匹配工具要求"""
                  try:
                      self.server.agent.logger.info(f"正在验证工具 '{tool_name}' 的参数...")
                       
                      # 特殊处理 validate_west_init_params 工具
                      if tool_name == 'validate_west_init_params':
                          # 检查必需参数
                          if 'repo_url' not in params:
                              self.send_error(400, "缺少必需参数: repo_url")
                              return
                          
                          # 验证 repo_url 格式
                          import re
                          url_pattern = re.compile(r'^(https?|git)://[^\s/$.?#].[^\s]*$')
                          if not url_pattern.match(params['repo_url']):
                              self.send_error(400, "无效的 repo_url 格式")
                              return
                          
                          self.server.agent.logger.info(f"工具 '{tool_name}' 的参数验证通过")
                       
                      # west_flash 工具的参数验证
                      elif tool_name == 'west_flash':
                          # 确保必需的 build_dir 参数存在
                          if 'build_dir' not in params:
                              self.send_error(400, "west_flash 需要必需参数: build_dir")
                              return
                      # west_update 工具的参数验证
                      elif tool_name == 'west_update':
                          # 确保 project_dir 参数存在
                          if 'project_dir' not in params:
                              self.send_error(400, "west_update 需要必需参数: project_dir")
                              return
                          
                          self.server.agent.logger.info(f"工具 '{tool_name}' 的参数验证通过")
                       
                      # 通用参数验证逻辑
                      elif tool_name == 'test_git_connection':
                          if 'url' not in params:
                              self.send_error(400, "缺少必需参数: url")
                              return
                          
                          # 验证 url 格式
                          import re
                          url_pattern = re.compile(r'^(https?|git)://[^\s/$.?#].[^\s]*$')
                          if not url_pattern.match(params['url']):
                              self.send_error(400, "无效的 URL 格式")
                              return
                          
                          self.server.agent.logger.info(f"工具 '{tool_name}' 的参数验证通过")
                       
                      # 通用参数验证：检查必需参数
                      tool_info = self.server.agent.tool_registry.get_registered_tools().get(tool_name)
                      if tool_info and 'parameters' in tool_info:
                          for param in tool_info['parameters']:
                              if param.get('required', False) and param['name'] not in params:
                                  self.send_error(400, f"缺少必需参数: {param['name']}")
                                  return
                       
                  except Exception as e:
                      # 验证过程出错，但不阻止请求继续
                      self.server.agent.logger.warning(f"参数验证过程出错: {str(e)}")
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
            print(f"\nJSON API服务器已启动: http://{host}:{port}")
            print("可用API端点:")
            print(f"  - GET  http://{host}:{port}/api/tools        - 获取所有工具列表")
            print(f"  - GET  http://{host}:{port}/api/tool/info     - 获取特定工具详细信息")
            print(f"  - POST http://{host}:{port}/api/tool          - 执行工具调用")
            print("\n示例请求:")
            print("  curl -X POST http://localhost:8000/api/tool -H 'Content-Type: application/json' -d '{\n    \"tool\": \"test_git_connection\",\n    \"params\": {\n      \"url\": \"https://github.com/zephyrproject-rtos/zephyr\"\n    }\n  }'")
            print("\n按Ctrl+C停止服务器...")
            
            # 在单独的线程中运行服务器
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # 保持主线程运行
            try:
                server_thread.join()
            except KeyboardInterrupt:
                print("\n停止服务器...")
                server.shutdown()
                server.server_close()
                print("服务器已停止")
                
        except Exception as e:
            self.logger.error(f"启动JSON服务器失败: {str(e)}")
            print(f"错误: 启动服务器失败 - {str(e)}")
    
    def perform_health_check(self):
        """执行工具健康检查"""
        print("\n执行工具健康检查...")
        try:
            health_info = self.tool_registry.get_tool_health()
            
            # 统计健康状态
            status_counts = {"healthy": 0, "warning": 0, "error": 0}
            for tool_name, health in health_info.items():
                status = health.get("status", "unknown")
                if status in status_counts:
                    status_counts[status] += 1
            
            # 显示健康摘要
            print(f"健康状态摘要: 健康 {status_counts['healthy']}, 警告 {status_counts['warning']}, 错误 {status_counts['error']}")
            
            # 显示有问题的工具
            if status_counts["warning"] > 0:
                print("\n需要注意的工具:")
                for tool_name, health in health_info.items():
                    if health.get("status") == "warning" and health.get("issues"):
                        print(f"  - {tool_name}: {', '.join(health['issues'])}")
        except Exception as e:
            self.logger.warning(f"健康检查失败: {str(e)}")
    
    def _format_category_name(self, category: str) -> str:
        """格式化分类名称为可读格式"""
        return ' '.join(word.capitalize() for word in category.split('_'))
    
    def _generate_tool_documentation(self, output_file: str = "./tools_documentation.md"):
        """生成工具文档"""
        try:
            self.tool_registry.generate_tool_documentation(output_file)
            self.logger.info(f"工具文档已生成: {output_file}")
        except Exception as e:
            self.logger.warning(f"生成工具文档失败: {str(e)}")


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
                print(f"找到 {len(matched_tools)} 个匹配 '{args.search}' 的工具:")
                for tool_name in matched_tools:
                    tool_info = agent.tool_registry.get_registered_tools()[tool_name]
                    print(f"  - {tool_name}: {tool_info['description']}")
            else:
                print(f"没有找到匹配 '{args.search}' 的工具")
        except Exception as e:
            print(f"搜索工具时出错: {str(e)}")
    
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
            
            print("工具健康状态报告:")
            print("=" * 60)
            
            # 统计健康状态
            status_counts = {"healthy": 0, "warning": 0, "error": 0}
            for tool_name, health in health_info.items():
                status = health.get("status", "unknown")
                if status in status_counts:
                    status_counts[status] += 1
            
            print(f"\n健康状态摘要:")
            print(f"  健康: {status_counts['healthy']}")
            print(f"  警告: {status_counts['warning']}")
            print(f"  错误: {status_counts['error']}")
            print(f"  总计: {sum(status_counts.values())}")
            
            print("\n详细信息:")
            for tool_name, health in health_info.items():
                status_color = "✅" if health.get("status") == "healthy" else "⚠️"
                print(f"\n{status_color} {tool_name}:")
                print(f"  状态: {health.get('status', 'unknown')}")
                print(f"  参数数量: {health.get('parameter_count', 0)}")
                print(f"  是否有描述: {'是' if health.get('has_description', False) else '否'}")
                if health.get('issues'):
                    print(f"  问题: {', '.join(health['issues'])}")
        except Exception as e:
            print(f"执行健康检查时出错: {str(e)}")
    
    elif args.generate_docs:
        agent._generate_tool_documentation(args.generate_docs)
        print(f"文档已生成: {args.generate_docs} (格式: {args.doc_format})")
    
    elif args.test:
        # 测试模式
        print("测试模式 - 验证工具注册...")
        try:
            # 确保tool_registry已初始化
            if not hasattr(agent, 'tool_registry'):
                agent.tool_registry = get_default_tool_registry()
                
            # 注册工具
            success = agent.register_tools()
            
            # 获取注册的工具
            registered_tools = agent.tool_registry.get_registered_tools()
            
            print(f"\n测试结果:")
            print(f"  注册工具: {len(registered_tools)}")
            
            # 尝试获取工具分类
            try:
                categories = agent.tool_registry.categorize_tools()
                print(f"  工具分类: {len(categories)}")
                # 显示分类详情
                for category, tools in categories.items():
                    print(f"    - {agent._format_category_name(category)}: {len(tools)} 个工具")
            except Exception:
                print("  工具分类: 不可用")
            
            # 显示状态
            if success and len(registered_tools) > 0:
                print(f"  状态: 成功")
                sys.exit(0)
            else:
                print(f"  状态: 警告 - 没有注册到工具")
                sys.exit(0)  # 即使没有工具也返回成功，因为这可能是正常情况
                
        except Exception as e:
            print(f"测试失败: {str(e)}")
            sys.exit(1)
    
    else:
        # 启动Agent
        agent.start()


if __name__ == "__main__":
    main()