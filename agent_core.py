#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zephyr MCP Agent - 核心类模块
"""

import os
import sys
import json
import traceback
import logging
import datetime
from typing import Dict, Any, List

# 导入其他模块
from config_manager import load_config
from opentelemetry_integration import init_opentelemetry
from http_server import start_json_server
from language_manager import setup_language

# 导入工具注册表
try:
    from src.utils.tool_registry import ToolRegistry, get_default_tool_registry
    # 导入agno agent相关模块
    try:
        from agno.agent import Agent
        from agno.tools import Function as Tool
    except ImportError:
        # 如果导入失败，使用兼容模式
        from src.utils.language_resources import get_text
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
        
        Agent = MockAgent
        Tool = MockTool
except ImportError as e:
    from src.utils.language_resources import get_text
    print(get_text("dependency_import_error", str(e)))
    print(get_text("install_dependencies"))
    sys.exit(1)


class ZephyrMCPAgent:
    """Zephyr MCP Agent核心类"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化agent"""
        self.config_path = config_path
        self.config = load_config(config_path)
        
        # 初始化语言管理器
        self.language_config = self.config.get("language", {})
        self.default_language = self.language_config.get("default", "zh")
        
        # 设置全局语言
        setup_language(self.default_language)
        
        # 创建语言管理器实例
        from src.utils.language_resources import LanguageManager
        self.language_manager = LanguageManager(self.default_language)
        
        # 设置日志器
        self.logger = self._setup_logger(self.config.get("log_level", "INFO"))
        
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
        
        # 初始化OpenTelemetry
        self.otel_tracer = init_opentelemetry(self.config, self.agent, self.logger)
        
    def _setup_logger(self, level="INFO"):
        """设置日志"""
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
        
    def register_tools(self):
        """使用工具注册表注册所有工具"""
        self.logger.info(self.get_text("registering_tools"))
        
        # 开始追踪
        if self.otel_tracer:
            with self.otel_tracer.start_as_current_span("register_tools") as span:
                return self._register_tools_with_trace(span)
        else:
            return self._register_tools_with_trace(None)
            
    def _register_tools_with_trace(self, span):
        """带追踪的工具注册"""
        try:
            # 使用工具注册表注册所有工具
            results = self.tool_registry.register_all_tools()
            
            # 将注册的工具添加到Agent中
            registered_tools = self.tool_registry.get_registered_tools()
            
            for tool_name, tool_info in registered_tools.items():
                try:
                    if span:
                        with self.otel_tracer.start_as_current_span(f"register_tool_{tool_name}") as tool_span:
                            tool_span.set_attribute("tool.name", tool_name)
                            tool_span.set_attribute("tool.description", tool_info["description"])
                            tool_span.set_attribute("tool.param_count", len(tool_info.get("parameters", [])))
                            
                            # 创建Tool对象并注册到agent
                            tool = Tool(
                                name=tool_info["name"],
                                description=tool_info["description"],
                                function=tool_info["function"],
                                parameters=tool_info["parameters"],
                                returns=tool_info["returns"]
                            )
                            
                            # 注册工具到agno Agent
                            if hasattr(self.agent, 'add_tool'):
                                self.agent.add_tool(tool)
                            elif hasattr(self.agent, 'register_tool'):
                                self.agent.register_tool(tool)  # 兼容旧版本
                            
                            self.tools[tool_name] = tool
                            tool_span.set_attribute("tool.registered", True)
                    else:
                        # 不使用追踪的版本
                        tool = Tool(
                            name=tool_info["name"],
                            description=tool_info["description"],
                            function=tool_info["function"],
                            parameters=tool_info["parameters"],
                            returns=tool_info["returns"]
                        )
                        
                        # 注册工具到agno Agent
                        if hasattr(self.agent, 'add_tool'):
                            self.agent.add_tool(tool)
                        elif hasattr(self.agent, 'register_tool'):
                            self.agent.register_tool(tool)  # 兼容旧版本
                        
                        self.tools[tool_name] = tool
                except Exception as tool_error:
                    if span:
                        with self.otel_tracer.start_as_current_span(f"register_tool_{tool_name}_error") as error_span:
                            error_span.set_attribute("tool.name", tool_name)
                            error_span.set_attribute("error", True)
                            error_span.set_attribute("error.message", str(tool_error))
                    
                    self.logger.warning(self.get_text("tool_register_error", tool_name, str(tool_error)))
                
            success_count = sum(1 for success in results.values() if success)
            self.logger.info(self.get_text("tools_registered", success_count, len(results)))
            
            if span:
                span.set_attribute("registered_tools_count", len(registered_tools))
                span.set_attribute("success_count", success_count)
                span.set_attribute("total_tools", len(results))
                
            return True
            
        except Exception as e:
            if span:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
            
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
            self.logger.info(self.get_text("register_llm_tool", tool_name))
            
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
        start_json_server(self)
    
    def perform_health_check(self):
        """执行工具健康检查"""
        self.logger.info(self.get_text("performing_health_check"))
        
        # 获取注册的工具
        registered_tools = self.tool_registry.get_registered_tools()
        
        # 执行简单的健康检查
        for tool_name, tool_info in registered_tools.items():
            try:
                # 检查工具函数是否可调用
                if callable(tool_info.get("function")):
                    self.logger.info(self.get_text("tool_health_check_passed", tool_name))
                else:
                    self.logger.warning(self.get_text("tool_health_check_failed", tool_name, "工具函数不可调用"))
            except Exception as e:
                self.logger.warning(self.get_text("tool_health_check_failed", tool_name, str(e)))
    
    def _format_category_name(self, category: str) -> str:
        """格式化分类名称"""
        category_map = {
            "git": "Git 工具",
            "zephyr": "Zephyr 工具",
            "west": "West 工具",
            "llm": "LLM 工具",
            "test": "测试工具",
            "other": "其他工具"
        }
        return category_map.get(category, category)
    
    def get_text(self, key: str, *args, **kwargs) -> str:
        """获取本地化文本"""
        return self.language_manager.get(key, *args, **kwargs)
    
    def set_current_language(self, language: str):
        """设置当前语言"""
        self.current_language = language
        setup_language(language)
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        return self.current_language
    
    def _generate_tool_documentation(self, output_file: str = "./tools_documentation.md"):
        """生成工具文档"""
        try:
            # 获取注册的工具
            registered_tools = self.tool_registry.get_registered_tools()
            
            # 生成Markdown文档
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Zephyr MCP Agent 工具文档\n\n")
                f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 按分类显示工具
                categories = self.tool_registry.categorize_tools()
                
                for category, tool_names in categories.items():
                    if tool_names:
                        f.write(f"## {self._format_category_name(category)} ({len(tool_names)})\n\n")
                        
                        for tool_name in tool_names:
                            tool_info = registered_tools[tool_name]
                            f.write(f"### {tool_name}\n\n")
                            f.write(f"**描述**: {tool_info['description']}\n\n")
                            
                            if tool_info.get('parameters'):
                                f.write("**参数**:\n\n")
                                for param_name, param_info in tool_info['parameters'].items():
                                    f.write(f"- `{param_name}`: {param_info.get('description', '无描述')}\n")
                                f.write("\n")
                            
                            if tool_info.get('returns'):
                                f.write(f"**返回值**: {tool_info['returns'].get('description', '无描述')}\n\n")
                
            self.logger.info(self.get_text("tool_documentation_generated", output_file))
        except Exception as e:
            self.logger.error(self.get_text("tool_documentation_error", str(e)))