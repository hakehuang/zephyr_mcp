#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zephyr MCP Agent - 核心类模块 / Core Class Module

这个模块包含Zephyr MCP Agent的核心实现，负责：
- 初始化和管理Agent实例
- 注册和管理工具
- 处理OpenTelemetry追踪
- 支持多语言界面
- 提供HTTP接口服务

This module contains the core implementation of Zephyr MCP Agent, responsible for:
- Initializing and managing Agent instances
- Registering and managing tools
- Handling OpenTelemetry tracing
- Supporting multi-language interfaces
- Providing HTTP interface services
"""

import os
import sys
import json
import traceback
import logging
import datetime
from typing import Dict, Any, List

# 导入其他模块 / Import other modules
from config_manager import load_config
from opentelemetry_integration import init_opentelemetry
from http_server import start_json_server
from language_manager import setup_language

# 导入工具注册表 / Import tool registry
try:
    from src.utils.tool_registry import ToolRegistry, get_default_tool_registry

    # 导入agno agent相关模块 / Import agno agent related modules
    try:
        from agno.agent import Agent
        from agno.tools import Function as Tool
    except ImportError:
        # 如果导入失败，使用兼容模式 / If import fails, use compatibility mode
        from src.utils.language_resources import get_text

        print(get_text("agno_import_failed"))

        class MockAgent:
            """兼容模式下的模拟Agent类 / Mock Agent class for compatibility mode"""

            def __init__(self, name=None, version=None, description=None):
                self.name = name or "zephyr_mcp_agent"
                self.version = version or "1.0.0"
                self.description = description or "Zephyr MCP Agent"
                self.tools = []

            def register_tool(self, tool):
                self.tools.append(tool)

        class MockTool:
            """兼容模式下的模拟Tool类 / Mock Tool class for compatibility mode"""

            def __init__(
                self, name, description, function=None, parameters=None, returns=None
            ):
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
    """
    Zephyr MCP Agent核心类 / Zephyr MCP Agent Core Class

    这个类负责管理整个Zephyr MCP Agent的生命周期，包括：
    - 初始化配置和依赖项
    - 注册和管理所有可用工具
    - 处理多语言支持
    - 集成OpenTelemetry追踪
    - 提供HTTP接口服务
    - 生成工具文档

    This class is responsible for managing the entire lifecycle of Zephyr MCP Agent, including:
    - Initializing configuration and dependencies
    - Registering and managing all available tools
    - Handling multi-language support
    - Integrating OpenTelemetry tracing
    - Providing HTTP interface services
    - Generating tool documentation
    """

    def __init__(self, config_path: str = "config.json"):
        """
        初始化agent / Initialize Agent

        参数 / Parameters:
        - config_path: 配置文件路径，默认为config.json / Configuration file path, defaults to config.json

        功能 / Functionality:
        - 加载配置文件和语言设置 / Load configuration file and language settings
        - 初始化日志系统和语言管理器 / Initialize logging system and language manager
        - 创建Agno Agent实例 / Create Agno Agent instance
        - 初始化工具注册表 / Initialize tool registry
        - 设置OpenTelemetry追踪 / Set up OpenTelemetry tracing
        - 验证语言支持 / Validate language support
        """
        self.config_path = config_path
        self.config = load_config(config_path)

        # 初始化语言管理器 / Initialize language manager
        self.language_config = self.config.get("language", {})
        self.default_language = self.language_config.get("default", "zh")

        # 设置全局语言 / Set global language
        setup_language(self.default_language)

        # 创建语言管理器实例 / Create language manager instance
        from src.utils.language_resources import LanguageManager

        self.language_manager = LanguageManager(self.default_language)

        # 设置日志器 / Set up logger
        self.logger = self._setup_logger(self.config.get("log_level", "INFO"))

        # 创建Agent实例 / Create Agent instance
        try:
            # 尝试使用完整参数初始化 / Try to initialize with full parameters
            self.agent = Agent(
                name=self.config["agent_name"],
                version=self.config["version"],
                description=self.config["description"],
            )
        except TypeError:
            # 如果参数不匹配，尝试使用名称初始化 / If parameters don't match, try name-only initialization
            try:
                self.agent = Agent(self.config["agent_name"])
            except Exception:
                # 最后使用默认初始化 / Finally use default initialization
                self.agent = Agent()

        # 使用工具注册表 / Use tool registry
        self.tool_registry = get_default_tool_registry()
        self.tools: Dict[str, Tool] = {}

        # 存储当前语言 / Store current language
        self.current_language = self.default_language

        # 初始化OpenTelemetry / Initialize OpenTelemetry
        self.otel_tracer = init_opentelemetry(self.config, self.agent, self.logger)

        # 记录语言配置信息 / Log language configuration information
        self.logger.info(f"Agent initialized with language: {self.current_language}")

        # 检查是否支持双语 / Check if bilingual support is available
        self.supported_languages = ["zh", "en"]
        if self.current_language not in self.supported_languages:
            self.logger.warning(
                f"Language '{self.current_language}' not supported, defaulting to 'zh'"
            )
            self.current_language = "zh"
            setup_language("zh")

    def _setup_logger(self, level="INFO"):
        """
        设置日志系统 / Set up logging system

        参数 / Parameters:
        - level: 日志级别，默认为INFO / Log level, defaults to INFO

        功能 / Functionality:
        - 创建自定义日志格式化器，包含trace_id / Create custom log formatter with trace_id
        - 配置根日志器 / Configure root logger
        - 设置日志处理器 / Set up log handlers
        - 返回配置好的日志器 / Return configured logger

        返回 / Returns:
        - 配置好的日志器实例 / Configured logger instance
        """
        # 创建自定义日志格式化器，包含trace_id / Create custom log formatter with trace_id
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(trace_id)s] %(message)s"
        )

        # 创建一个自定义的LogRecord工厂，确保trace_id始终存在 / Create custom LogRecord factory to ensure trace_id always exists
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            # 检查是否有extra参数 / Check if there are extra parameters
            extra = kwargs.get("extra", {})

            # 确保extra是一个字典 / Ensure extra is a dictionary
            if not isinstance(extra, dict):
                extra = {}

            # 从extra参数中获取trace_id，如果有的话 / Get trace_id from extra parameters if available
            trace_id = extra.pop("trace_id", None)

            # 将修改后的extra参数放回kwargs中 / Put modified extra parameters back into kwargs
            kwargs["extra"] = extra

            # 调用旧的工厂函数创建LogRecord对象 / Call old factory function to create LogRecord object
            record = old_factory(*args, **kwargs)

            # 设置trace_id属性 / Set trace_id attribute
            record.trace_id = (
                trace_id if trace_id is not None else "-"
            )  # 使用传入的trace_id或默认值 / Use provided trace_id or default value

            return record

        logging.setLogRecordFactory(record_factory)

        # 配置根日志器 / Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level))

        # 确保有handler / Ensure there is a handler
        if not root_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)
        else:
            # 更新现有handler的格式化器 / Update existing handler's formatter
            for handler in root_logger.handlers:
                handler.setFormatter(formatter)

        # 创建日志记录器 / Create logger
        logger = logging.getLogger(__name__)
        return logger

    def register_tools(self):
        """
        使用工具注册表注册所有工具 / Register all tools using tool registry

        功能 / Functionality:
        - 从工具注册表获取所有可用工具 / Get all available tools from tool registry
        - 为每个工具创建追踪span / Create tracing span for each tool
        - 将工具注册到Agno Agent实例 / Register tools to Agno Agent instance
        - 处理工具注册过程中的错误 / Handle errors during tool registration
        - 记录注册结果统计信息 / Log registration result statistics

        返回 / Returns:
        - 注册成功返回True，失败返回False / Returns True if successful, False if failed
        """
        self.logger.info(self.get_text("registering_tools"))

        # 开始追踪 / Start tracing
        if self.otel_tracer:
            with self.otel_tracer.start_as_current_span("register_tools") as span:
                return self._register_tools_with_trace(span)
        else:
            return self._register_tools_with_trace(None)

    def _register_tools_with_trace(self, span):
        """
        带追踪的工具注册 / Tool registration with tracing

        参数 / Parameters:
        - span: OpenTelemetry span对象，用于追踪 / OpenTelemetry span object for tracing

        功能 / Functionality:
        - 批量注册所有工具 / Batch register all tools
        - 为每个工具创建详细的追踪信息 / Create detailed tracing information for each tool
        - 处理工具注册异常 / Handle tool registration exceptions
        - 记录成功和失败的注册数量 / Log successful and failed registration counts

        返回 / Returns:
        - 注册成功返回True，失败返回False / Returns True if successful, False if failed
        """
        try:
            # 使用工具注册表注册所有工具 / Register all tools using tool registry
            results = self.tool_registry.register_all_tools()

            # 将注册的工具添加到Agent中 / Add registered tools to Agent
            registered_tools = self.tool_registry.get_registered_tools()

            for tool_name, tool_info in registered_tools.items():
                try:
                    if span:
                        with self.otel_tracer.start_as_current_span(
                            f"register_tool_{tool_name}"
                        ) as tool_span:
                            tool_span.set_attribute("tool.name", tool_name)
                            tool_span.set_attribute(
                                "tool.description", tool_info["description"]
                            )
                            tool_span.set_attribute(
                                "tool.param_count", len(tool_info.get("parameters", []))
                            )

                            # 创建Tool对象并注册到agent / Create Tool object and register to agent
                            tool = Tool(
                                name=tool_info["name"],
                                description=tool_info["description"],
                                function=tool_info["function"],
                                parameters=tool_info["parameters"],
                                returns=tool_info["returns"],
                            )

                            # 注册工具到agno Agent / Register tool to agno Agent
                            if hasattr(self.agent, "add_tool"):
                                self.agent.add_tool(tool)
                            elif hasattr(self.agent, "register_tool"):
                                self.agent.register_tool(
                                    tool
                                )  # 兼容旧版本 / Compatible with older versions

                            self.tools[tool_name] = tool
                            tool_span.set_attribute("tool.registered", True)
                    else:
                        # 不使用追踪的版本 / Version without tracing
                        tool = Tool(
                            name=tool_info["name"],
                            description=tool_info["description"],
                            function=tool_info["function"],
                            parameters=tool_info["parameters"],
                            returns=tool_info["returns"],
                        )

                        # 注册工具到agno Agent / Register tool to agno Agent
                        if hasattr(self.agent, "add_tool"):
                            self.agent.add_tool(tool)
                        elif hasattr(self.agent, "register_tool"):
                            self.agent.register_tool(
                                tool
                            )  # 兼容旧版本 / Compatible with older versions

                        self.tools[tool_name] = tool
                except Exception as tool_error:
                    if span:
                        with self.otel_tracer.start_as_current_span(
                            f"register_tool_{tool_name}_error"
                        ) as error_span:
                            error_span.set_attribute("tool.name", tool_name)
                            error_span.set_attribute("error", True)
                            error_span.set_attribute("error.message", str(tool_error))

                    self.logger.warning(
                        self.get_text("tool_register_error", tool_name, str(tool_error))
                    )

            success_count = sum(1 for success in results.values() if success)
            self.logger.info(
                self.get_text("tools_registered", success_count, len(results))
            )

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
        注册LLM相关工具 / Register LLM-related tools

        功能 / Functionality:
        - 初始化LLM集成配置 / Initialize LLM integration configuration
        - 获取所有可用的LLM工具 / Get all available LLM tools
        - 将LLM工具注册到工具注册表 / Register LLM tools to tool registry
        - 处理LLM工具注册过程中的异常 / Handle exceptions during LLM tool registration

        注意 / Notes:
        - 需要配置文件中启用LLM功能 / Requires LLM feature to be enabled in configuration
        - 依赖LLM集成模块 / Depends on LLM integration module
        """
        try:
            # 导入LLM集成相关模块 / Import LLM integration related modules
            from src.utils.llm_integration import init_llm, LLMIntegration
            from tools.llm_tools import register_llm_tools, get_registered_tools

            # 初始化LLM集成 / Initialize LLM integration
            llm_config = self.config.get("llm", {})
            init_llm(llm_config)

            # 注册LLM工具 / Register LLM tools
            self.logger.info(self.get_text("registering_llm_tools"))
            llm_tools = get_registered_tools()

            # 将LLM工具注册到工具注册表 / Register LLM tools to tool registry
            for tool_info in llm_tools:
                tool_name = tool_info["name"]
                # 这里简化处理，实际需要根据工具注册表的API进行适配 / Simplified processing, actual adaptation needed based on tool registry API
            self.logger.info(self.get_text("register_llm_tool", tool_name))

            # 使用llm_tools中的注册函数 / Use registration function from llm_tools
            register_llm_tools(self)

            self.logger.info(self.get_text("llm_tools_registered"))
        except Exception as e:
            self.logger.error(self.get_text("llm_tool_register_error", str(e)))
            self.logger.debug(traceback.format_exc())

    def start(self, show_language_info: bool = False):
        """
        启动agent / Start the agent

        参数 / Parameters:
        - show_language_info: 是否显示语言信息，默认为False / Whether to display language information, defaults to False

        功能 / Functionality:
        - 显示语言信息（可选） / Display language information (optional)
        - 注册所有可用工具 / Register all available tools
        - 初始化并注册LLM工具（如果启用） / Initialize and register LLM tools (if enabled)
        - 执行工具健康检查 / Perform tool health checks
        - 显示可用工具列表 / Display available tools list
        - 生成工具文档 / Generate tool documentation
        - 启动HTTP接口服务器 / Start HTTP interface server

        这是Agent的主要启动方法 / This is the main startup method for the Agent
        """
        if show_language_info:
            self.display_language_info()

        self.logger.info(
            self.get_text(
                "starting_agent", self.config["agent_name"], self.config["version"]
            )
        )
        self.register_tools()

        # 初始化并注册LLM工具（如果启用） / Initialize and register LLM tools (if enabled)
        if "llm" in self.config and self.config["llm"].get("enabled", True):
            try:
                self.register_llm_tools()
            except Exception as e:
                self.logger.error(self.get_text("llm_tool_register_error", str(e)))

        # 执行工具健康检查 / Perform tool health checks
        self.perform_health_check()

        # 获取注册的工具 / Get registered tools
        registered_tools = self.tool_registry.get_registered_tools()
        self.logger.info(
            self.get_text(
                "tools_registered", len(registered_tools), len(registered_tools)
            )
        )

        # 打印可用工具列表（按分类显示） / Print available tools list (grouped by category)
        categories = self.tool_registry.categorize_tools()

        # 双语显示标题 / Bilingual display title
        if self.current_language == "zh":
            print(f"\nZephyr MCP Agent {self.get_text('starting_agent')}")
            print(f"\n{self.get_text('available_tools')}:")
        else:
            print(f"\nZephyr MCP Agent - Starting Agent")
            print(f"\nAvailable Tools:")

        for category, tool_names in categories.items():
            if tool_names:
                # 根据当前语言显示分类名称 / Display category name based on current language
                if self.current_language == "zh":
                    category_display = self._format_category_name(category)
                else:
                    category_display = self._format_category_name_en(category)

                print(f"\n{category_display} ({len(tool_names)}):")
                for tool_name in tool_names:
                    tool_info = registered_tools[tool_name]
                    # 显示简短描述 / Display short description
                    short_desc = (
                        tool_info["description"][:60] + "..."
                        if len(tool_info["description"]) > 60
                        else tool_info["description"]
                    )
                    print(f"- {tool_name}: {short_desc}")

        # 生成工具文档 / Generate tool documentation
        self._generate_tool_documentation()

        # 启动JSON HTTP接口服务器 / Start JSON HTTP interface server
        start_json_server(self)

    def perform_health_check(self):
        """
        执行工具健康检查 / Perform tool health checks

        功能 / Functionality:
        - 检查所有已注册工具的可调用性 / Check callability of all registered tools
        - 验证工具函数是否可用 / Verify tool functions are available
        - 记录健康检查结果 / Log health check results
        - 报告有问题的工具 / Report problematic tools

        注意 / Notes:
        - 健康检查是轻量级的，只验证基本功能 / Health checks are lightweight, only verifying basic functionality
        - 不会执行实际的工具功能 / Does not execute actual tool functions
        """
        self.logger.info(self.get_text("performing_health_check"))

        # 获取注册的工具 / Get registered tools
        registered_tools = self.tool_registry.get_registered_tools()

        # 执行简单的健康检查 / Perform simple health checks
        for tool_name, tool_info in registered_tools.items():
            try:
                # 检查工具函数是否可调用 / Check if tool function is callable
                if callable(tool_info.get("function")):
                    self.logger.info(
                        self.get_text("tool_health_check_passed", tool_name)
                    )
                else:
                    self.logger.warning(
                        self.get_text(
                            "tool_health_check_failed", tool_name, "工具函数不可调用"
                        )
                    )
            except Exception as e:
                self.logger.warning(
                    self.get_text("tool_health_check_failed", tool_name, str(e))
                )

    def _format_category_name(self, category: str) -> str:
        """
        格式化分类名称（中文） / Format category name (Chinese)

        参数 / Parameters:
        - category: 原始分类名称 / Original category name

        返回 / Returns:
        - 格式化的中文分类名称 / Formatted Chinese category name

        功能 / Functionality:
        - 将英文分类名称转换为中文显示名称 / Convert English category names to Chinese display names
        - 提供统一的分类名称格式 / Provide unified category name formatting
        - 支持未知分类名称的默认处理 / Support default handling for unknown category names
        """
        category_map = {
            "git": "Git 工具",
            "zephyr": "Zephyr 工具",
            "west": "West 工具",
            "llm": "LLM 工具",
            "test": "测试工具",
            "other": "其他工具",
        }
        return category_map.get(category, category)

    def get_text(self, key: str, *args, **kwargs) -> str:
        """
        获取本地化文本 / Get localized text

        参数 / Parameters:
        - key: 文本键值 / Text key
        - *args: 格式化参数 / Formatting arguments
        - **kwargs: 关键字格式化参数 / Keyword formatting arguments

        返回 / Returns:
        - 根据当前语言设置的本地化文本 / Localized text based on current language setting

        功能 / Functionality:
        - 通过语言管理器获取对应语言的文本 / Get text in corresponding language through language manager
        - 支持文本格式化 / Support text formatting
        - 处理多语言文本替换 / Handle multi-language text substitution
        """
        return self.language_manager.get(key, *args, **kwargs)

    def set_current_language(self, language: str):
        """设置当前语言"""
        self.current_language = language
        setup_language(language)

    def get_current_language(self) -> str:
        """获取当前语言"""
        return self.current_language

    def _generate_tool_documentation(
        self, output_file: str = "./tools_documentation.md"
    ):
        """生成工具文档 / Generate tool documentation"""
        try:
            # 获取注册的工具 / Get registered tools
            registered_tools = self.tool_registry.get_registered_tools()

            # 生成Markdown文档 / Generate Markdown documentation
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("# Zephyr MCP Agent 工具文档\n\n")
                f.write(
                    f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                # 按分类显示工具 / Display tools by category
                categories = self.tool_registry.categorize_tools()

                for category, tool_names in categories.items():
                    if tool_names:
                        f.write(
                            f"## {self._format_category_name(category)} ({len(tool_names)})\n\n"
                        )

                        for tool_name in tool_names:
                            tool_info = registered_tools[tool_name]
                            f.write(f"### {tool_name}\n\n")
                            f.write(f"**描述**: {tool_info['description']}\n\n")

                            if tool_info.get("parameters"):
                                f.write("**参数**:\n\n")
                                for param_name, param_info in tool_info[
                                    "parameters"
                                ].items():
                                    f.write(
                                        f"- `{param_name}`: {param_info.get('description', '无描述')}\n"
                                    )
                                f.write("\n")

                            if tool_info.get("returns"):
                                f.write(
                                    f"**返回值**: {tool_info['returns'].get('description', '无描述')}\n\n"
                                )

            self.logger.info(self.get_text("tool_documentation_generated", output_file))
        except Exception as e:
            self.logger.error(self.get_text("tool_documentation_error", str(e)))

    def switch_language(self, language: str) -> bool:
        """
        切换语言 / Switch language

        参数 / Parameters:
        - language: 目标语言代码（zh/en） / Target language code (zh/en)

        返回 / Returns:
        - 切换成功返回True，失败返回False / Returns True if successful, False if failed

        功能 / Functionality:
        - 验证语言代码是否支持 / Validate if language code is supported
        - 更新当前语言设置 / Update current language setting
        - 设置全局语言环境 / Set global language environment
        - 更新语言管理器 / Update language manager
        - 记录语言切换日志 / Log language switching

        注意 / Notes:
        - 只支持zh（中文）和en（英文） / Only supports zh (Chinese) and en (English)
        - 切换失败时会记录错误日志 / Logs error when switching fails
        """
        if language not in self.supported_languages:
            self.logger.error(
                f"Language '{language}' is not supported. Supported languages: {self.supported_languages}"
            )
            return False

        try:
            # 更新当前语言 / Update current language
            self.current_language = language

            # 设置全局语言 / Set global language
            setup_language(language)

            # 更新语言管理器 / Update language manager
            self.language_manager.set_language(language)

            self.logger.info(f"Language switched to: {language}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to switch language to '{language}': {str(e)}")
            return False

    def get_available_languages(self) -> Dict[str, str]:
        """
        获取可用语言列表 / Get available languages list

        返回 / Returns:
        - 语言代码到语言名称的映射字典 / Dictionary mapping language codes to language names

        功能 / Functionality:
        - 返回系统支持的所有语言 / Return all languages supported by the system
        - 提供友好的语言名称显示 / Provide friendly language name display
        - 用于语言选择界面 / Used for language selection interface

        支持的語言 / Supported Languages:
        - zh: 中文 (Chinese)
        - en: English (英语)
        """
        return {"zh": "中文 (Chinese)", "en": "English (英语)"}

    def get_language_info(self) -> Dict[str, Any]:
        """
        获取当前语言信息 / Get current language information

        返回 / Returns:
        - 包含语言详细信息的字典 / Dictionary containing detailed language information

        返回内容 / Return Content:
        - current: 当前语言代码 / Current language code
        - name: 当前语言名称 / Current language name
        - supported_languages: 所有支持的语言 / All supported languages
        - default: 默认语言 / Default language

        功能 / Functionality:
        - 提供完整的语言状态信息 / Provide complete language status information
        - 用于语言信息显示和调试 / Used for language information display and debugging
        """
        available_languages = self.get_available_languages()

        return {
            "current": self.current_language,
            "name": available_languages.get(self.current_language, "Unknown"),
            "supported_languages": available_languages,
            "default": self.default_language,
        }

    def display_language_info(self):
        """显示语言信息 / Display language information"""
        language_info = self.get_language_info()

        print("\n=== Language Information ===")
        print(f"Current Language: {language_info['name']} ({language_info['current']})")
        print(f"Default Language: {language_info['default']}")
        print("\nSupported Languages:")
        for code, name in language_info["supported_languages"].items():
            marker = "*" if code == language_info["current"] else " "
            print(f"  {marker} {code}: {name}")

    def generate_bilingual_documentation(
        self, output_file: str = "./tools_documentation_bilingual.md"
    ):
        """生成双语工具文档 / Generate bilingual tool documentation"""
        try:
            # 获取注册的工具 / Get registered tools
            registered_tools = self.tool_registry.get_registered_tools()

            # 生成双语Markdown文档 / Generate bilingual Markdown documentation
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("# Zephyr MCP Agent 工具文档 / Tool Documentation\n\n")
                f.write(
                    f"生成时间 / Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                # 按分类显示工具 / Display tools by category
                categories = self.tool_registry.categorize_tools()

                for category, tool_names in categories.items():
                    if tool_names:
                        # 双语分类标题 / Bilingual category title
                        category_name_zh = self._format_category_name(category)
                        category_name_en = self._format_category_name_en(category)
                        f.write(
                            f"## {category_name_zh} / {category_name_en} ({len(tool_names)})\n\n"
                        )

                        for tool_name in tool_names:
                            tool_info = registered_tools[tool_name]
                            f.write(f"### {tool_name}\n\n")

                            # 双语描述 / Bilingual description
                            f.write("**描述 / Description**: ")
                            f.write(f"{tool_info['description']}\n\n")

                            if tool_info.get("parameters"):
                                f.write("**参数 / Parameters**:\n\n")
                                for param_name, param_info in tool_info[
                                    "parameters"
                                ].items():
                                    param_desc = param_info.get(
                                        "description", "无描述 / No description"
                                    )
                                    f.write(f"- `{param_name}`: {param_desc}\n")
                                f.write("\n")

                            if tool_info.get("returns"):
                                return_desc = tool_info["returns"].get(
                                    "description", "无描述 / No description"
                                )
                                f.write(f"**返回值 / Returns**: {return_desc}\n\n")

            self.logger.info(f"Bilingual documentation generated: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate bilingual documentation: {str(e)}")
            return False

    def _format_category_name_en(self, category: str) -> str:
        """格式化英文分类名称 / Format English category name"""
        category_map = {
            "git": "Git Tools",
            "zephyr": "Zephyr Tools",
            "west": "West Tools",
            "llm": "LLM Tools",
            "test": "Test Tools",
            "other": "Other Tools",
        }
        return category_map.get(category, category)

    def start_with_language_selection(self):
        """启动agent并显示语言选择 / Start agent and display language selection"""
        # 启动agent并显示语言信息 / Start agent and display language information
        self.start(show_language_info=True)

    def get_bilingual_text(self, key: str, *args, **kwargs) -> Dict[str, str]:
        """获取双语文本 / Get bilingual text"""
        try:
            # 保存当前语言 / Save current language
            original_language = self.current_language

            # 获取中文文本 / Get Chinese text
            self.switch_language("zh")
            text_zh = self.get_text(key, *args, **kwargs)

            # 获取英文文本 / Get English text
            self.switch_language("en")
            text_en = self.get_text(key, *args, **kwargs)

            # 恢复原始语言 / Restore original language
            self.switch_language(original_language)

            return {"zh": text_zh, "en": text_en}

        except Exception as e:
            self.logger.error(f"Failed to get bilingual text for key '{key}': {str(e)}")
            return {"zh": f"Error: {str(e)}", "en": f"Error: {str(e)}"}
