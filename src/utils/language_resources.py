#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言资源模块 - 提供多语言支持
"""

from typing import Dict, Any, Optional

# 语言资源字典
LANGUAGE_RESOURCES: Dict[str, Dict[str, Any]] = {
    "zh": {
        # 代理基本信息
        "agent_name": "zephyr_mcp_agent",
        "agent_description": "Zephyr MCP Agent - 提供Zephyr项目管理和Git操作工具集",
        
        # 日志和错误消息
        "loading_config": "加载配置文件...",
        "config_loaded_success": "配置文件加载成功",
        "config_load_error": "加载配置文件失败: {}",
        "config_save_error": "保存配置文件失败: {}",
        "registering_tools": "开始注册工具...",
        "tools_registered": "工具注册完成: 成功 {}/{}",
        "tool_register_error": "注册工具 {} 时出错: {}",
        "registering_llm_tools": "开始注册LLM工具...",
        "llm_tools_registered": "LLM工具注册完成",
        "llm_tool_register_error": "注册LLM工具失败: {}",
        "starting_agent": "启动 {} v{}",
        "server_started": "JSON API服务器已启动: http://{}",
        "server_endpoints": "可用API端点:",
        "server_shutdown": "停止服务器...",
        "server_stopped": "服务器已停止",
        "server_start_error": "启动JSON服务器失败: {}",
        "health_check_start": "执行工具健康检查...",
        "health_summary": "健康状态摘要: 健康 {}, 警告 {}, 错误 {}",
        "llm_status": "LLM集成状态:",
        "llm_available": "可用: 是",
        "llm_not_available": "可用: 否",
        "llm_api_key_configured": "已配置",
        "llm_api_key_not_configured": "未配置",
        "health_issues": "问题: {}",
        "tool_health_check": "正在验证工具 '{}' 的参数...",
        "tool_params_valid": "工具 '{}' 的参数验证通过",
        "missing_required_param": "缺少必需参数: {}",
        "invalid_param_format": "无效的 {} 格式",
        "tool_not_found": "工具 '{}' 不存在",
        "invalid_json": "无效的JSON格式",
        "ai_assistant_not_enabled": "AI助手功能未启用",
        "ai_assistant_not_available": "LLM集成不可用，请检查配置和依赖",
        "missing_messages_param": "缺少消息参数 'messages'",
        "invalid_messages_type": "消息参数必须是一个列表",
        "invalid_message_format": "消息 {} 必须是一个字典",
        "missing_message_fields": "消息 {} 缺少必要字段 'role' 或 'content'",
        "invalid_message_role": "消息 {} 的 'role' 必须是 'system', 'user' 或 'assistant'",
        "ai_assistant_error": "AI助手处理失败",
        "request_processing_error": "处理请求时发生错误: {}",
        "endpoint_not_found": "Not Found",
        "missing_tool_name": "Missing tool name",
        "tools_to_note": "Tools that need attention:",
        "cannot_get_details": "Unable to get detailed status",
        "parameter_required": "{} requires required parameter: {}",
        
        # 服务器启动消息
        "available_tools": "可用工具:",
        "example_request": "示例请求:",
        "ai_assistant_example": "AI助手示例请求:",
        "press_ctrl_c": "按Ctrl+C停止服务器...",
        "server_started_full": "JSON HTTP服务器启动在 http://{}",
        "available_endpoints": "可用端点:",
        "endpoint_get_tools": "获取可用工具列表",
        "endpoint_get_tool_info": "获取工具详细信息", 
        "endpoint_execute_tool": "执行工具",
        "endpoint_get_docs": "获取API文档",
        "endpoint_ai_assistant": "AI助手对话",
        "server_interrupted": "服务器被用户中断",
        "server_error": "服务器错误: {}",
        "server_closed": "服务器已关闭",
        
        # 命令行输出
        "list_tools_header": "可用工具列表:",
        "tool_search_header": "找到 {} 个匹配 '{}' 的工具:",
        "no_matching_tools": "没有找到匹配 '{}' 的工具",
        "search_error": "搜索工具时出错: {}",
        "health_check_report": "工具健康状态报告:",
        "health_status_summary": "健康状态摘要:",
        "llm_integration_status": "LLM集成状态:",
        "llm_enabled": "启用: {}",
        "llm_available": "可用: {}",
        "health_details": "详细信息:",
        "tool_name": "{}",
        "tool_status": "状态: {}",
        "param_count": "参数数量: {}",
        "has_description": "是否有描述: {}",
        "docs_generated": "文档已生成: {} (格式: {})",
        "test_mode": "测试模式 - 验证工具注册...",
        "test_result": "测试结果:",
        "registered_tools_count": "注册工具",
        "llm_integration": "LLM集成: {}",
        "tool_categories_count": "工具分类: {}",
        "test_status_success": "状态: 成功",
        "test_status_warning": "状态: 警告 - 没有注册到工具",
        "test_failed": "测试失败: {}",
        
        # API文档
        "api_docs_title": "Zephyr MCP Agent API Documentation",
        "api_docs_base_url": "基础URL",
        "api_docs_endpoints": "API端点",
        "api_docs_notes": "所有API响应均为JSON格式，POST请求需要设置Content-Type为application/json",
        "api_docs_get_tools": "获取所有可用工具列表",
        "api_docs_get_tool_info": "获取特定工具的详细信息",
        "api_docs_execute_tool": "执行工具调用",
        "api_docs_ai_assistant": "使用大模型进行对话",
        "api_docs_get_docs": "获取API文档",
        "api_docs_tools_list": "可用工具列表",
        "api_docs_total_tools": "工具总数",
        "api_docs_llm_integration": "LLM集成状态",
        "api_docs_tool_name": "工具名称",
        "api_docs_tool_description": "工具描述",
        "api_docs_parameters_list": "参数列表",
        "api_docs_returns_list": "返回值列表",
        "api_docs_tool_module": "工具模块",
        "api_docs_tool_params": "工具参数",
        "api_docs_success": "执行状态",
        "api_docs_execution_result": "执行结果",
        "api_docs_error_info": "错误信息",
        "api_docs_called_tool": "调用的工具",
        "api_docs_messages_list": "消息列表",
        "api_docs_model_name": "模型名称",
        "api_docs_temperature": "温度参数",
        "api_docs_max_tokens": "最大令牌数",
        "api_docs_ai_response": "AI响应",
        "api_docs_used_model": "使用的模型",
        "api_docs_token_usage": "令牌使用情况",
        
        # 工具参数描述
        "param_name": "名称",
        "param_type": "类型",
        "param_description": "描述",
        "param_required": "是否必需",
        "request_format": "请求格式",
        "response_format": "响应格式",
        "example": "示例",
        
        # 健康检查图标
        "status_healthy": "✅",
        "status_warning": "⚠️",
        "status_error": "❌",
        
        # 工具分类
        "tool_category_git": "Git操作",
        "tool_category_west": "West命令",
        "tool_category_zephyr": "Zephyr管理",
        "tool_category_validation": "验证工具",
        "tool_category_ai": "AI助手",
        "tool_category_other": "其他工具",
        
        # 兼容模式和依赖
        "agno_import_failed": "Warning: agno库导入失败，使用兼容模式...",
        "dependency_import_error": "Error: 导入依赖失败: {}",
        "install_dependencies": "请安装依赖: pip install -r requirements.txt",
        "register_llm_tool": "注册LLM工具: {}",
        "param_validation_error": "参数验证过程出错: {}",
        "config_load_error": "Error: 加载配置文件失败: {}",
        "doc_generation_error": "生成工具文档失败: {}",
        "health_check_error": "执行健康检查时出错: {}",
        "yes": "是",
        "no": "否",
        "llm_initialization_failed": "集成初始化失败",
        "llm_enabled_available": "已启用且可用",
        "llm_enabled_unavailable": "已启用但不可用",
        "llm_disabled": "未启用",
        "tools_count_suffix": "个工具",
        "not_available": "不可用",
        "total": "总计",
        "enabled": "启用",
        "available": "可用",
    },
    "en": {
        # 代理基本信息
        "agent_name": "zephyr_mcp_agent",
        "agent_description": "Zephyr MCP Agent - Provides Zephyr project management and Git operation tools",
        
        # 日志和错误消息
        "loading_config": "Loading configuration file...",
        "config_loaded_success": "Configuration file loaded successfully",
        "config_load_error": "Failed to load configuration file: {}",
        "config_save_error": "Failed to save configuration file: {}",
        "registering_tools": "Registering tools...",
        "tools_registered": "Tool registration completed: {} succeeded out of {}",
        "tool_register_error": "Error registering tool {}: {}",
        "registering_llm_tools": "Registering LLM tools...",
        "llm_tools_registered": "LLM tool registration completed",
        "llm_tool_register_error": "Failed to register LLM tools: {}",
        "starting_agent": "Starting {} v{}",
        "server_started": "JSON API server started: http://{}",
        "server_endpoints": "Available API endpoints:",
        "server_shutdown": "Shutting down server...",
        "server_stopped": "Server stopped",
        "server_start_error": "Failed to start JSON server: {}",
        "health_check_start": "Performing tool health check...",
        "health_summary": "Health status summary: {} healthy, {} warning, {} error",
        "llm_status": "LLM integration status:",
        "llm_available": "Available: Yes",
        "llm_not_available": "Available: No",
        "llm_api_key_configured": "Configured",
        "llm_api_key_not_configured": "Not configured",
        "health_issues": "Issues: {}",
        "tool_health_check": "Validating parameters for tool '{}'...",
        "tool_params_valid": "Parameter validation passed for tool '{}'",
        "missing_required_param": "Missing required parameter: {}",
        "invalid_param_format": "Invalid {} format",
        "tool_not_found": "Tool '{}' not found",
        "invalid_json": "Invalid JSON format",
        "ai_assistant_not_enabled": "AI assistant feature not enabled",
        "ai_assistant_not_available": "LLM integration not available, please check configuration and dependencies",
        "missing_messages_param": "Missing message parameter 'messages'",
        "invalid_messages_type": "Message parameter must be a list",
        "invalid_message_format": "Message {} must be a dictionary",
        "missing_message_fields": "Message {} is missing required fields 'role' or 'content'",
        "invalid_message_role": "Message {} 'role' must be 'system', 'user' or 'assistant'",
        "ai_assistant_error": "AI assistant processing failed",
        "request_processing_error": "Error processing request: {}",
        "endpoint_not_found": "Not Found",
        "missing_tool_name": "Missing tool name",
        "tools_to_note": "Tools that need attention:",
        "cannot_get_details": "Unable to get detailed status",
        "parameter_required": "{} requires required parameter: {}",
        
        # 服务器启动消息
        "available_tools": "Available tools:",
        "example_request": "Example request:",
        "ai_assistant_example": "AI assistant example request:",
        "press_ctrl_c": "Press Ctrl+C to stop the server...",
        "server_started_full": "JSON HTTP server started at http://{}",
        "available_endpoints": "Available endpoints:",
        "endpoint_get_tools": "Get available tools list",
        "endpoint_get_tool_info": "Get tool details", 
        "endpoint_execute_tool": "Execute tool",
        "endpoint_get_docs": "Get API documentation",
        "endpoint_ai_assistant": "AI assistant conversation",
        "server_interrupted": "Server interrupted by user",
        "server_error": "Server error: {}",
        "server_closed": "Server closed",
        
        # 命令行输出
        "list_tools_header": "Available tools list:",
        "tool_search_header": "Found {} tools matching '{}':",
        "no_matching_tools": "No tools matching '{}' found",
        "search_error": "Error searching tools: {}",
        "health_check_report": "Tool health status report:",
        "health_status_summary": "Health status summary:",
        "llm_integration_status": "LLM integration status:",
        "llm_enabled": "Enabled: {}",
        "llm_available": "Available: {}",
        "health_details": "Details:",
        "tool_name": "{}",
        "tool_status": "Status: {}",
        "param_count": "Parameter count: {}",
        "has_description": "Has description: {}",
        "docs_generated": "Documentation generated: {} (format: {})",
        "test_mode": "Test mode - Validating tool registration...",
        "test_result": "Test results:",
        "registered_tools_count": "Registered tools",
        "llm_integration": "LLM integration: {}",
        "tool_categories_count": "Tool categories: {}",
        "test_status_success": "Status: Success",
        "test_status_warning": "Status: Warning - No tools registered",
        "test_failed": "Test failed: {}",
        
        # API文档
        "api_docs_title": "Zephyr MCP Agent API Documentation",
        "api_docs_base_url": "Base URL",
        "api_docs_endpoints": "API Endpoints",
        "api_docs_notes": "All API responses are in JSON format, POST requests require Content-Type: application/json",
        "api_docs_get_tools": "Get all available tools",
        "api_docs_get_tool_info": "Get detailed information about a specific tool",
        "api_docs_execute_tool": "Execute a tool call",
        "api_docs_ai_assistant": "Use AI assistant for conversation",
        "api_docs_get_docs": "Get API documentation",
        "api_docs_tools_list": "Available tools list",
        "api_docs_total_tools": "Total tools",
        "api_docs_llm_integration": "LLM integration status",
        "api_docs_tool_name": "Tool name",
        "api_docs_tool_description": "Tool description",
        "api_docs_parameters_list": "Parameters list",
        "api_docs_returns_list": "Returns list",
        "api_docs_tool_module": "Tool module",
        "api_docs_tool_params": "Tool parameters",
        "api_docs_success": "Execution status",
        "api_docs_execution_result": "Execution result",
        "api_docs_error_info": "Error information",
        "api_docs_called_tool": "Called tool",
        "api_docs_messages_list": "Messages list",
        "api_docs_model_name": "Model name",
        "api_docs_temperature": "Temperature parameter",
        "api_docs_max_tokens": "Maximum tokens",
        "api_docs_ai_response": "AI response",
        "api_docs_used_model": "Model used",
        "api_docs_token_usage": "Token usage",
        
        # 工具参数描述
        "param_name": "Name",
        "param_type": "Type",
        "param_description": "Description",
        "param_required": "Required",
        "request_format": "Request Format",
        "response_format": "Response Format",
        "example": "Example",
        
        # 健康检查图标
        "status_healthy": "✅",
        "status_warning": "⚠️",
        "status_error": "❌",
        
        # 工具分类
        "tool_category_git": "Git Operations",
        "tool_category_west": "West Commands",
        "tool_category_zephyr": "Zephyr Management",
        "tool_category_validation": "Validation Tools",
        "tool_category_ai": "AI Assistant",
        "tool_category_other": "Other Tools",
        
        # 兼容模式和依赖
        "agno_import_failed": "Warning: Failed to import agno library, using compatibility mode...",
        "dependency_import_error": "Error: Failed to import dependencies: {}",
        "install_dependencies": "Please install dependencies: pip install -r requirements.txt",
        "register_llm_tool": "Registering LLM tool: {}",
        "param_validation_error": "Error during parameter validation: {}",
        "config_load_error": "Error: Failed to load configuration file: {}",
        "doc_generation_error": "Failed to generate tool documentation: {}",
        "health_check_error": "Error during health check: {}",
        "yes": "Yes",
        "no": "No",
        "llm_initialization_failed": "Integration initialization failed",
        "llm_enabled_available": "Enabled and available",
        "llm_enabled_unavailable": "Enabled but unavailable",
        "llm_disabled": "Disabled",
        "tools_count_suffix": "tools",
        "not_available": "Not available",
        "total": "Total",
        "enabled": "Enabled",
        "available": "Available",
    }
}


class LanguageManager:
    """
    语言管理器类，用于处理多语言支持
    """
    
    def __init__(self, language: str = "zh"):
        """
        初始化语言管理器
        
        Args:
            language: 语言代码，默认为中文(zh)
        """
        self.language = language
        self.resources = LANGUAGE_RESOURCES.get(language, LANGUAGE_RESOURCES["zh"])
        
    def set_language(self, language: str):
        """
        设置当前语言
        
        Args:
            language: 语言代码
        """
        if language in LANGUAGE_RESOURCES:
            self.language = language
            self.resources = LANGUAGE_RESOURCES[language]
        else:
            # 如果指定的语言不存在，使用中文作为默认语言
            self.language = "zh"
            self.resources = LANGUAGE_RESOURCES["zh"]
    
    def get(self, key: str, *args, **kwargs) -> str:
        """
        获取指定键的翻译文本
        
        Args:
            key: 资源键名
            *args: 格式化参数
            **kwargs: 格式化关键字参数
            
        Returns:
            翻译后的文本
        """
        text = self.resources.get(key, key)
        if args or kwargs:
            return text.format(*args, **kwargs)
        return text
    
    def get_language(self) -> str:
        """
        获取当前语言
        
        Returns:
            当前语言代码
        """
        return self.language
    
    def get_available_languages(self) -> list:
        """
        获取可用的语言列表
        
        Returns:
            可用语言代码列表
        """
        return list(LANGUAGE_RESOURCES.keys())


# 创建全局语言管理器实例
global_language_manager = LanguageManager()


def get_text(key: str, *args, **kwargs) -> str:
    """
    获取翻译文本的便捷函数
    
    Args:
        key: 资源键名
        *args: 格式化参数
        **kwargs: 格式化关键字参数
        
    Returns:
        翻译后的文本
    """
    return global_language_manager.get(key, *args, **kwargs)


def set_language(language: str):
    """
    设置全局语言
    
    Args:
        language: 语言代码
    """
    global_language_manager.set_language(language)


def get_current_language() -> str:
    """
    获取当前全局语言
    
    Returns:
        当前语言代码
    """
    return global_language_manager.get_language()


def get_available_languages() -> list:
    """
    获取可用的语言列表
    
    Returns:
        可用语言代码列表
    """
    return global_language_manager.get_available_languages()
