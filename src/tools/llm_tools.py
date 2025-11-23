#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Tools - Provide tool functions for interacting with large language models
大模型工具 - 提供与大语言模型交互的工具函数
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
# 加载环境变量
load_dotenv()

# Add project root directory to Python path
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import LLM integration module
# 导入LLM集成模块
try:
    from src.utils.llm_integration import LLMIntegration
    LLM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Failed to import LLM integration module: {str(e)}")
    print(f"警告: 无法导入LLM集成模块: {str(e)}")
    LLM_AVAILABLE = False

# Configure logging
# 配置日志
logger = logging.getLogger(__name__)

# Global LLM integration instance
# 全局LLM集成实例
_llm_integration = None

def init_llm(config: Dict[str, Any]) -> None:
    """
    Initialize LLM integration
    初始化LLM集成
    
    Args:
        config: LLM configuration dictionary
        config: LLM配置字典
    """
    global _llm_integration
    _llm_integration = LLMIntegration(config)
    logger.info("LLM tools initialized")

def get_llm() -> Optional[LLMIntegration]:
    """
    Get LLM integration instance
    获取LLM集成实例
    
    Returns:
        LLMIntegration: LLM integration instance
        LLMIntegration: LLM集成实例
    """
    global _llm_integration
    return _llm_integration

def get_registered_tools() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all registered LLM tools
    获取所有注册的LLM工具信息
    
    Returns:
        Dict: Tool information dictionary
        Dict: 工具信息字典
    """
    return {
        "generate_text": {
            "name": "generate_text",
            "description": "Generate text using large language model",
                "chinese_description": "使用大语言模型生成文本",
            "params": [
                {"name": "prompt", "type": "string", "required": True, "description": "提示文本"},
                {"name": "model", "type": "string", "required": False, "description": "模型名称，支持 'gpt-4-turbo', 'gpt-3.5-turbo', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'deepseek-chat', 'deepseek-coder' 等"},
                {"name": "max_tokens", "type": "integer", "required": False, "description": "最大token数"},
                {"name": "temperature", "type": "number", "required": False, "description": "生成温度"},
                {"name": "system_message", "type": "string", "required": False, "description": "系统提示"}
            ]
        },
        "analyze_code": {
            "name": "analyze_code",
            "description": "Analyze code and answer questions",
                "chinese_description": "分析代码并回答问题",
            "params": [
                {"name": "code", "type": "string", "required": True, "description": "要分析的代码"},
                {"name": "question", "type": "string", "required": True, "description": "关于代码的问题"}
            ]
        },
        "explain_error": {
            "name": "explain_error",
            "description": "Explain error messages and provide solutions",
                "chinese_description": "解释错误消息并提供解决方案",
            "params": [
                {"name": "error_message", "type": "string", "required": True, "description": "错误消息"},
                {"name": "code_context", "type": "string", "required": False, "description": "相关代码上下文"}
            ]
        },
        "llm_chat": {
            "name": "llm_chat",
            "description": "Conduct multi-turn conversations",
                "chinese_description": "进行多轮对话",
            "params": [
                {"name": "messages", "type": "array", "required": True, "description": "消息列表"},
                {"name": "model", "type": "string", "required": False, "description": "模型名称，支持 'gpt-4-turbo', 'gpt-3.5-turbo', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'deepseek-chat', 'deepseek-coder' 等"},
                {"name": "max_tokens", "type": "integer", "required": False, "description": "最大token数"},
                {"name": "temperature", "type": "number", "required": False, "description": "生成温度"}
            ]
        },
        "get_llm_status": {
            "name": "get_llm_status",
            "description": "Get LLM integration status",
                "chinese_description": "获取LLM集成状态",
            "params": []
        }
    }


def generate_text(prompt: str, model: Optional[str] = None, 
                 system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, 
                 max_tokens: int = 1000) -> Dict[str, Any]:
    """
    Generate text response using large language model
    使用大模型生成文本响应
    
    Args:
        prompt: User prompt text
        prompt: 用户提示文本
        model: Model name to use (uses default if not specified)
        model: 要使用的模型名称（如不指定，使用默认模型）
        system_prompt: System prompt text to guide model behavior
        system_prompt: 系统提示文本，用于指导模型行为
        temperature: Generation temperature, controls output randomness (0.0-2.0)
        temperature: 生成温度，控制输出的随机性 (0.0-2.0)
        max_tokens: Maximum number of tokens to generate
        max_tokens: 最大生成的token数量
    
    Returns:
        Dictionary containing generated text and metadata
        包含生成文本和元数据的字典
    """
    if not LLM_AVAILABLE:
        return {
            "success": False,
            "error": "LLM integration module not available",
            "chinese_error": "LLM集成模块不可用",
            "text": "",
            "model": model
        }
    
    try:
        # 调用LLM集成模块生成文本
        llm = get_llm()
        if llm is None:
            return {
                "success": False,
                "error": "LLM integration not initialized",
            "chinese_error": "LLM集成未初始化",
                "text": "",
                "model": model
            }
        result = llm.generate_text(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to generate text: {str(e)}")
        logger.error(f"生成文本失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "model": model
        }


def analyze_code(code: str, query: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze code and answer related questions using large language model
    使用大模型分析代码并回答相关问题
    
    Args:
        code: Code to analyze
        code: 要分析的代码
        query: Question about the code
        query: 关于代码的问题
        model: Model name to use
        model: 要使用的模型名称
    
    Returns:
        Dictionary containing analysis results
        包含分析结果的字典
    """
    if not LLM_AVAILABLE:
        return {
            "success": False,
            "error": "LLM integration module not available",
            "chinese_error": "LLM集成模块不可用",
            "analysis": "",
            "model": model
        }
    
    try:
        # 调用LLM集成模块分析代码
        llm = get_llm()
        if llm is None:
            return {
                "success": False,
                "error": "LLM integration not initialized",
            "chinese_error": "LLM集成未初始化",
                "analysis": "",
                "model": model
            }
        result = llm.analyze_code(code, query, model)
        
        # 调整返回格式以匹配工具预期
        return {
            "success": result.get("success", False),
            "analysis": result.get("text", ""),
            "error": result.get("error", ""),
            "model": result.get("model", model),
            "usage": result.get("usage", {})
        }
    except Exception as e:
        logger.error(f"Code analysis failed: {str(e)}")
        logger.error(f"代码分析失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "analysis": "",
            "model": model
        }


def explain_error(error_message: str, context: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Explain error messages and provide solutions using large language model
    使用大模型解释错误信息并提供解决方案
    
    Args:
        error_message: Error message
        error_message: 错误信息
        context: Context where the error occurred (code snippet, execution environment, etc.)
        context: 错误发生的上下文（如代码片段、执行环境等）
        model: Model name to use
        model: 要使用的模型名称
    
    Returns:
        Dictionary containing error explanation and solutions
        包含错误解释和解决方案的字典
    """
    if not LLM_AVAILABLE:
        return {
            "success": False,
            "error": "LLM integration module not available",
            "chinese_error": "LLM集成模块不可用",
            "explanation": "",
            "solutions": [],
            "model": model
        }
    
    try:
        system_prompt = "You are a professional software debugging expert, skilled at explaining error messages and providing clear solutions."
            # 你是一位专业的软件调试专家，擅长解释错误信息并提供清晰的解决方案。
        
        prompt = f"错误信息:\n```\n{error_message}\n```\n"
        if context:
            prompt += f"上下文信息:\n```\n{context}\n```\n"
        
        prompt += "请提供:\n1. 对错误的清晰解释\n2. 可能的原因\n3. 具体的解决方案步骤\n4. 预防此类错误的建议\n\n请以结构化的方式回答。"
        
        llm = get_llm()
        if llm is None:
            return {
                "success": False,
                "error": "LLM integration not initialized",
            "chinese_error": "LLM集成未初始化",
                "explanation": "",
                "model": model
            }
        result = llm.generate_text(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.3,  # 低温度以获取更精确的技术解释
            max_tokens=1500
        )
        
        # 处理结果
        if result.get("success", False):
            return {
                "success": True,
                "explanation": result.get("text", ""),
                "model": result.get("model", model),
                "usage": result.get("usage", {})
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate explanation"),
            "chinese_error": result.get("error", "生成解释失败"),
                "explanation": "",
                "model": model
            }
    except Exception as e:
        logger.error(f"Failed to explain error: {str(e)}")
        logger.error(f"错误解释失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "explanation": "",
            "model": model
        }


def generate_tool_documentation(tool_function_name: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate documentation for the specified tool function
    为指定的工具函数生成文档
    
    Args:
        tool_function_name: Tool function name
        tool_function_name: 工具函数名称
        model: Model name to use
        model: 要使用的模型名称
    
    Returns:
        Dictionary containing generated documentation
        包含生成文档的字典
    """
    if not LLM_AVAILABLE:
        return {
            "success": False,
            "error": "LLM integration module not available",
            "chinese_error": "LLM集成模块不可用",
            "documentation": "",
            "model": model
        }
    
    try:
        # Try to import and get the tool function
        # 尝试导入并获取工具函数
        import importlib
        from src.utils.tool_registry import get_default_tool_registry
        
        tool_registry = get_default_tool_registry()
        tool_registry.register_all_tools()
        registered_tools = tool_registry.get_registered_tools()
        
        if tool_function_name not in registered_tools:
            return {
                "success": False,
                "error": f"Tool function '{tool_function_name}' does not exist",
                "chinese_error": f"工具函数 '{tool_function_name}' 不存在",
                "documentation": "",
                "model": model
            }
        
        tool_info = registered_tools[tool_function_name]
        tool_func = tool_info['function']
        
        # 调用LLM生成文档
        llm = get_llm()
        if llm is None:
            return {
                "success": False,
                "error": "LLM integration not initialized",
            "chinese_error": "LLM集成未初始化",
                "documentation": "",
                "model": model
            }
        result = llm.generate_tool_description(tool_func, model)
        
        # 处理结果
        if result.get("success", False):
            try:
                # Try to parse JSON format documentation
            # 尝试解析JSON格式的文档
                doc_json = json.loads(result.get("text", "{}"))
                return {
                    "success": True,
                    "documentation": doc_json,
                    "raw_text": result.get("text", ""),
                    "model": result.get("model", model),
                    "usage": result.get("usage", {})
                }
            except json.JSONDecodeError:
                # If not valid JSON, return raw text
                # 如果不是有效的JSON，返回原始文本
                return {
                    "success": True,
                    "documentation": {"raw_text": result.get("text", "")},
                    "raw_text": result.get("text", ""),
                    "model": result.get("model", model),
                    "usage": result.get("usage", {})
                }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate documentation"),
            "chinese_error": result.get("error", "生成文档失败"),
                "documentation": "",
                "model": model
            }
    except Exception as e:
        logger.error(f"Failed to generate tool documentation: {str(e)}")
        logger.error(f"生成工具文档失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "documentation": "",
            "model": model
        }


def llm_chat(messages: List[Dict[str, str]], model: Optional[str] = None, 
             temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
    """
    Conduct multi-turn conversations using large language model
    使用大模型进行多轮对话
    
    Args:
        messages: List of conversation messages, each containing role and content
        messages: 对话消息列表，每个消息包含role和content
        model: Model name to use
        model: 要使用的模型名称
        temperature: Generation temperature
        temperature: 生成温度
        max_tokens: Maximum number of tokens to generate
        max_tokens: 最大生成token数
    
    Returns:
        Dictionary containing conversation response
        包含对话响应的字典
    """
    if not LLM_AVAILABLE:
        return {
            "success": False,
            "error": "LLM integration module not available",
            "chinese_error": "LLM集成模块不可用",
            "response": "",
            "model": model
        }
    
    try:
        # Build conversation history
        # 构建对话历史
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        # Extract system prompt (if any)
        # 提取系统提示（如果有）
        system_prompt = None
        for msg in messages:
            if msg.get('role') == 'system':
                system_prompt = msg.get('content')
                break
        
        # Call LLM to generate response
            # 调用LLM生成响应
        llm = get_llm()
        if llm is None:
            return {
                "success": False,
                "error": "LLM integration not initialized",
            "chinese_error": "LLM集成未初始化",
                "response": "",
                "model": model
            }
        result = llm.generate_text(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 处理结果
        if result.get("success", False):
            return {
                "success": True,
                "response": result.get("text", ""),
                "model": result.get("model", model),
                "usage": result.get("usage", {})
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to generate conversation response"),
            "chinese_error": result.get("error", "生成对话响应失败"),
                "response": "",
                "model": model
            }
    except Exception as e:
        logger.error(f"Conversation generation failed: {str(e)}")
        logger.error(f"对话生成失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "response": "",
            "model": model
        }


def get_llm_status() -> Dict[str, Any]:
    """
    Get large language model integration status
    获取大模型集成状态
    
    Returns:
        Dictionary containing large language model status information
        包含大模型状态信息的字典
    """
    status = {
        "available": LLM_AVAILABLE,
        "providers": {}
    }
    
    if LLM_AVAILABLE:
        # Check API keys in environment variables
        # 检查环境变量中的API密钥
        status["providers"]["openai"] = {
            "api_key_configured": bool(os.getenv("OPENAI_API_KEY", ""))
        }
        status["providers"]["anthropic"] = {
            "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY", ""))
        }
        status["providers"]["deepseek"] = {
            "api_key_configured": bool(os.getenv("DEEPSEEK_API_KEY", ""))
        }
    
    return status