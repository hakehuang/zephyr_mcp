#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tool Wrapper Module - For adapting existing Zephyr MCP tools to agno agent
工具包装模块 - 用于将现有Zephyr MCP工具适配到agno agent
"""

from typing import Dict, Any, List, Callable, get_type_hints
import inspect
import os
import sys
import re

# Ensure tools can be imported correctly
# 确保可以正确导入工具模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ToolWrapper:
    """
    Tool Wrapper Class, for adapting existing tools to agno agent
    工具包装类，用于适配现有工具到agno agent
    """
    
    @staticmethod
    def wrap_tool(tool_func: Callable) -> Dict[str, Any]:
        """
        Wrap tool function and extract its metadata
        包装工具函数，提取其元数据
        
        Args:
            tool_func: Tool function
            tool_func: 工具函数
            
        Returns:
            Dictionary containing tool metadata
            包含工具元数据的字典
        """
        if not callable(tool_func):
            return None
        
        # Extract basic information
        # 提取基本信息
        tool_info = {
            "name": getattr(tool_func, "__name__", "unknown_tool"),
            "description": "",
            "function": tool_func,  # Always use the original function
            # 始终使用原始函数
            "parameters": [],
            "returns": {}
        }
        
        # Get function signature
        # 获取函数签名
        signature = inspect.signature(tool_func)
        
        # Get type hints
        # 获取类型提示
        try:
            type_hints = get_type_hints(tool_func)
        except (TypeError, ValueError):
            type_hints = {}
        
        # Extract parameter information
        # 提取参数信息
        tool_info["parameters"] = ToolWrapper._extract_parameters(tool_func, signature, type_hints)
        
        # Extract return value information
        # 提取返回值信息
        tool_info["returns"] = ToolWrapper._extract_returns(tool_func, type_hints)
        
        # Extract function description
        # 提取功能描述
        doc = getattr(tool_func, "__doc__", "") or ""
        doc = doc.strip()
        
        if doc:
            # Try to extract short description
            # 尝试提取简短描述
            doc_lines = doc.split('\n')
            short_description = doc_lines[0].strip()
            
            # Simplify description processing for clarity
            # 简化描述处理，确保清晰可读
            tool_info["description"] = short_description
            
            # Add detailed description if there are more lines
            # 如果有更多行，添加详细描述
            if len(doc_lines) > 1:
                detailed_description = "\n".join(line.strip() for line in doc_lines[1:] if line.strip())
                if detailed_description:
                    tool_info["description"] = f"{short_description}\n\n{detailed_description}"
        
        # Extract exception handling information and module
        # 提取异常处理信息和模块
        tool_info["exception_handling"] = ToolWrapper._extract_exception_handling(tool_func)
        tool_info["module"] = str(tool_func.__module__)  # 转换为字符串避免JSON序列化错误
        
        return tool_info
    
    @staticmethod
    def _extract_parameters(tool_func: Callable, signature: inspect.Signature, 
                          type_hints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract parameter information from function and documentation
        从函数和文档中提取参数信息
        
        Args:
            tool_func: Tool function
            tool_func: 工具函数
            signature: Function signature
            signature: 函数签名
            type_hints: Type hints dictionary
            type_hints: 类型提示字典
        
        Returns:
            List of parameter information dictionaries
            参数信息字典列表
        """
        parameters = []
        docstring = inspect.getdoc(tool_func) or ""
        
        # 从文档字符串中提取参数描述
        param_descriptions = ToolWrapper._parse_param_descriptions(docstring)
        
        # 遍历函数签名中的参数
        for param_name, param in signature.parameters.items():
            # 获取参数类型（优先使用type_hints）
            param_type = "Any"
            if param_name in type_hints:
                param_type = str(type_hints[param_name])
            elif param.annotation != inspect.Parameter.empty:
                param_type = str(param.annotation)
            
            # 获取默认值信息
            has_default = param.default != inspect.Parameter.empty
            default_value = param.default if has_default else None
            
            # 获取参数描述
            description = param_descriptions.get(param_name, 
                                              f"参数 {param_name} 的描述")
            
            # 确定是否必需
            required = param.default == inspect.Parameter.empty and \
                      param.kind not in (inspect.Parameter.VAR_POSITIONAL, 
                                        inspect.Parameter.VAR_KEYWORD)
            
            parameter_info = {
                "name": param_name,
                "type": param_type,
                "required": required,
                "description": description
            }
            
            if has_default:
                parameter_info["default"] = default_value
            
            parameters.append(parameter_info)
        
        return parameters
    
    @staticmethod
    def _parse_param_descriptions(docstring: str) -> Dict[str, str]:
        """
        Parse parameter descriptions from docstring
        解析文档字符串中的参数描述
        
        Args:
            docstring: Function docstring
            docstring: 函数文档字符串
        
        Returns:
            Dictionary mapping parameter names to descriptions
            参数名到描述的映射字典
        """
        param_descriptions = {}
        
        # 支持多种参数文档格式
        patterns = [
            # 标准Python文档格式 (Parameters:)
            r'Parameters:\s*(.*?)(?:Returns|返回值|$)',
            # 中文文档格式 (参数说明:)
            r'参数说明:\s*(.*?)(?:返回值|返回|$)',
            # Google风格 (Args:)
            r'Args:\s*(.*?)(?:Returns|返回值|$)',
            # 其他常见格式
            r'参数:\s*(.*?)(?:返回|$)'
        ]
        
        docstring_lower = docstring.lower()
        
        for pattern in patterns:
            match = re.search(pattern, docstring_lower, re.DOTALL)
            if match:
                param_section = match.group(1)
                # 解析每个参数行
                for line in param_section.split('\n'):
                    line = line.strip()
                    if line:
                        # 处理 - param_name: description 格式
                        if line.startswith('-'):
                            if ':' in line:
                                parts = line[1:].strip().split(':', 1)
                                if len(parts) >= 1:
                                    param_name = parts[0].strip()
                                    # 清理参数名，移除类型信息
                                    param_name = re.sub(r'\(.*?\)', '', param_name).strip()
                                    description = parts[1].strip() if len(parts) > 1 else ""
                                    param_descriptions[param_name] = description
                        # 处理 param_name: description 格式
                        elif ':' in line and not any(keyword in line for keyword in 
                                                   ['returns', '返回', '参数', 'args']):
                            parts = line.split(':', 1)
                            if len(parts) >= 1:
                                param_name = parts[0].strip()
                                # 清理参数名，移除类型信息
                                param_name = re.sub(r'\(.*?\)', '', param_name).strip()
                                description = parts[1].strip() if len(parts) > 1 else ""
                                param_descriptions[param_name] = description
        
        # 如果没有找到标准格式，尝试简单匹配
        if not param_descriptions:
            lines = docstring.split('\n')
            for line in lines:
                line = line.strip()
                # 简单匹配参数行
                if ':' in line and not any(keyword in line.lower() for keyword in 
                                         ['returns', '返回', 'description', '描述']):
                    parts = line.split(':', 1)
                    if len(parts) >= 1:
                        param_candidate = parts[0].strip()
                        # 检查是否看起来像参数名（只有字母、数字、下划线）
                        if re.match(r'^\w+$', param_candidate):
                            param_descriptions[param_candidate] = parts[1].strip() if len(parts) > 1 else ""
        
        return param_descriptions
    
    @staticmethod
    def _extract_returns(tool_func: Callable, type_hints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract return value information
        提取返回值信息
        
        Args:
            tool_func: Tool function
            tool_func: 工具函数
            type_hints: Type hints dictionary
            type_hints: 类型提示字典
        
        Returns:
            Dictionary with return type and description
            包含返回类型和描述的字典
        """
        docstring = inspect.getdoc(tool_func) or ""
        
        # 获取返回值描述
        description = ""
        patterns = [
            # 标准Python文档格式 (Returns:)
            r'Returns:\s*(.*?)(?:Raises|异常|$)',
            # 中文文档格式 (返回值:)
            r'返回值:\s*(.*?)(?:异常|$)',
            # 其他格式
            r'返回:\s*(.*?)(?:异常|$)'
        ]
        
        docstring_lower = docstring.lower()
        
        for pattern in patterns:
            match = re.search(pattern, docstring_lower, re.DOTALL)
            if match:
                description = match.group(1).strip()
                break
        
        # 获取返回值类型（优先使用type_hints）
        return_type = "Any"
        if 'return' in type_hints:
            return_type = str(type_hints['return'])
        elif tool_func.__annotations__ and 'return' in tool_func.__annotations__:
            return_type = str(tool_func.__annotations__['return'])
        
        return {
            "type": return_type,
            "description": description
        }
    
    @staticmethod
    def _extract_description(tool_func: Callable) -> str:
        """
        Extract function description
        提取功能描述
        
        Args:
            tool_func: Tool function
            tool_func: 工具函数
        
        Returns:
            Extracted description
            提取的描述
        """
        docstring = inspect.getdoc(tool_func) or ""
        
        # 清理文档字符串
        docstring = docstring.strip()
        
        if not docstring:
            return f"工具函数: {tool_func.__name__}"
        
        # 获取文档的第一段落
        lines = []
        for line in docstring.split('\n'):
            stripped_line = line.strip()
            # 检查是否到达参数部分
            if any(stripped_line.lower().startswith(keyword) for keyword in 
                  ['parameters:', '参数说明:', 'args:', '参数:', 'returns:', '返回值:']):
                break
            if stripped_line:
                lines.append(stripped_line)
        
        # 如果收集到了行，返回它们的组合
        if lines:
            return ' '.join(lines)
        
        # 否则返回整个文档字符串的前200个字符
        return docstring[:200] + ("..." if len(docstring) > 200 else "")
    
    @staticmethod
    def _extract_exception_handling(tool_func: Callable) -> str:
        """
        Extract exception handling information
        提取异常处理信息
        
        Args:
            tool_func: Tool function
            tool_func: 工具函数
        
        Returns:
            Extracted exception handling information
            提取的异常处理信息
        """
        docstring = inspect.getdoc(tool_func) or ""
        
        # 查找异常处理部分
        patterns = [
            r'Raises:\s*(.*?)$',
            r'异常处理:\s*(.*?)$',
            r'异常:\s*(.*?)$'
        ]
        
        docstring_lower = docstring.lower()
        
        for pattern in patterns:
            match = re.search(pattern, docstring_lower, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    @staticmethod
    def validate_tool(tool_func: Callable) -> Dict[str, Any]:
        """
        Validate if the tool function is valid
        验证工具函数是否有效
        
        Args:
            tool_func: Function to validate
            tool_func: 要验证的函数
            
        Returns:
            Validation result dictionary
            验证结果字典
        """
        # 直接检查是否可调用即可，保持简单
        return {"valid": callable(tool_func)}
        
    @staticmethod
    def is_valid_tool(tool_func: Callable) -> bool:
        """
        Simple check if tool function is valid (for original calls)
        简单检查工具函数是否有效（用于原始调用）
        
        Args:
            tool_func: Function to validate
            tool_func: 要验证的函数
            
        Returns:
            Whether the function is a valid tool function
            是否为有效的工具函数
        """
        return callable(tool_func)


def create_agno_tool(tool_func: Callable) -> Dict[str, Any]:
    """
    Create tool description object suitable for agno agent
    创建适合agno agent的工具描述对象
    
    Args:
        tool_func: Tool function
        tool_func: 工具函数
        
    Returns:
        Formatted tool description dictionary
        格式化的工具描述字典
    """
    # Validate if tool is valid
    # 验证工具是否有效
    if not ToolWrapper.is_valid_tool(tool_func):
        raise ValueError(f"无效的工具函数: {tool_func}")
    
    # Extract tool information
    # 提取工具信息
    wrapped = ToolWrapper.wrap_tool(tool_func)
    
    # Convert to agno tool format, ensuring original function is returned
    # 转换为agno工具格式，确保返回原始函数
    agno_tool = {
        "name": wrapped["name"],
        "description": wrapped["description"],
        "function": tool_func,  # Directly use the original function
        # 直接使用原始函数
        "parameters": wrapped["parameters"],
        "returns": wrapped["returns"]
    }
    
    return agno_tool


def create_tool_wrapper(func: Callable) -> Callable:
    """
    Create tool wrapper decorator to enhance error handling
    创建工具包装装饰器，增强错误处理
    
    Args:
        func: Function to wrap
        func: 要包装的函数
    
    Returns:
        Wrapped function with enhanced error handling
        具有增强错误处理的包装函数
    """
    def wrapper(*args, **kwargs):
        try:
            # 执行原始函数
            result = func(*args, **kwargs)
            
            # 标准化返回值格式
            if isinstance(result, dict):
                # 确保包含status字段
                if 'status' not in result:
                    result['status'] = 'success'
                return result
            else:
                # 转换非字典返回值
                return {
                    'status': 'success',
                    'result': result
                }
        except Exception as e:
            # 捕获所有异常并返回结构化错误信息
            return {
                'status': 'error',
                'error': str(e),
                'exception_type': type(e).__name__
            }
    
    # 复制原始函数的元数据
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__module__ = func.__module__
    
    return wrapper

# Export commonly used functions
# 导出常用函数
__all__ = ['create_agno_tool', 'create_tool_wrapper', 'ToolWrapper']