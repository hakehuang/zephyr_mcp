#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tool Registry Module - For managing and registering Zephyr MCP tools to agno agent
工具注册模块 - 用于管理和注册Zephyr MCP工具到agno agent
"""

import os
import importlib
import inspect
import re

from typing import Dict, Any, List, Optional
from src.utils.tool_wrapper import create_agno_tool, ToolWrapper    

class ToolRegistry:
    """
    Tool Registry, for managing and registering tools
    工具注册表，用于管理和注册工具
    """

    def __init__(self, tools_dir: str = "./src/tools"):
        """
        Initialize tool registry
        初始化工具注册表

        Args:
            tools_dir: Directory path containing tools
            tools_dir: 包含工具的目录路径
        """
        self.tools_dir = os.path.abspath(tools_dir)
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.loaded_modules: Dict[str, Any] = {}
        # Store tool metadata
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}  # 存储工具元数据

    def discover_tools(self, include_hidden: bool = False) -> List[str]:
        """
        Discover all available tool modules
        发现所有可用的工具模块

        Args:
            include_hidden: Whether to include hidden tools (starting with _)
            include_hidden: 是否包含隐藏工具（以下划线开头）

        Returns:
            List of tool names
            工具名称列表
        """
        if not os.path.exists(self.tools_dir):
            print(f"警告: 工具目录不存在: {self.tools_dir}")
            return []

        tool_names = []
        for filename in os.listdir(self.tools_dir):
            if filename.endswith(".py") and (
                include_hidden or not filename.startswith("_")
            ):
                # Remove .py extension
                # 移除.py扩展名
                tool_name = filename[:-3]
                tool_names.append(tool_name)

        return tool_names

    def load_tool_module(self, tool_name: str) -> Optional[Any]:
        """
        Load tool module
        加载工具模块

        Args:
            tool_name: Name of the tool to load
            tool_name: 要加载的工具名称

        Returns:
            Loaded module or None if failed
            加载的模块，如果失败则返回None
        """
        if tool_name in self.loaded_modules:
            return self.loaded_modules[tool_name]

        try:
            # Import tool module
            # 导入工具模块
            module_path = f"src.tools.{tool_name}"
            module = importlib.import_module(module_path)
            self.loaded_modules[tool_name] = module
            return module
        except Exception as e:
            print(f"错误: 加载工具模块 {tool_name} 失败: {str(e)}")
            return None

    def get_tool_functions(self, module: Any, module_name: str) -> Dict[str, Any]:
        """
        Get all tool functions from module
        从模块中获取所有工具函数

        Search rules:
        查找规则：
        1. Search for function with exact name matching the module name (most common case)
        1. 查找与模块名完全匹配的函数（最常见情况）
        2. Search for public functions (not starting with underscore)
        2. 查找公共函数（不以下划线开头的函数）
        3. Search for functions with special decorator markers
        3. 查找带有特殊装饰器标记的函数

        Args:
            module: Module object
            module: 模块对象
            module_name: Name of the module
            module_name: 模块名称

        Returns:
            Dictionary mapping function names to function objects
            函数名到函数对象的映射字典
        """
        tools = {}

        # First try to use module name as function name directly (most common case)
        # 首先尝试直接使用模块名作为函数名（最常见情况）
        if hasattr(module, module_name):
            tools[module_name] = getattr(module, module_name)
            return tools

        # 如果没有找到，尝试查找所有公共函数
        for name, obj in inspect.getmembers(module):
            # 排除以下划线开头的私有/特殊属性
            if not name.startswith("_") and name != "mcp" and not inspect.ismodule(obj):
                # 检查是否是函数或可调用对象
                if inspect.isfunction(obj) or callable(obj):
                    tools[name] = obj
                # 也处理被装饰器包装的对象
                elif hasattr(obj, "__call__") or hasattr(obj, "fn"):
                    tools[name] = obj

        # 如果仍然没有找到，尝试特殊装饰器标记
        if not tools:
            for name, obj in inspect.getmembers(module):
                if (
                    hasattr(obj, "_is_mcp_tool")
                    or hasattr(obj, "__mcp_tool__")
                    or hasattr(obj, "fn")
                ):
                    tools[name] = obj

        return tools

    def register_tool(self, tool_name: str) -> Dict[str, bool]:
        """
        Register all tool functions in a single tool module
        注册单个工具模块中的所有工具函数

        Args:
            tool_name: Name of the tool module to register
            tool_name: 要注册的工具模块名称

        Returns:
            Dictionary mapping function names to registration status
            函数名到注册状态的映射字典
        """
        # Load tool module
        # 加载工具模块
        module = self.load_tool_module(tool_name)
        if not module:
            return {}

        # 直接检查模块中是否有与模块名相同的函数
        if hasattr(module, tool_name):
            direct_func = getattr(module, tool_name)

            # 尝试直接注册这个函数
            try:
                # 检查是否可调用
                if callable(direct_func):
                    # Create tool information with necessary parameters and returns fields
                    # 创建工具信息，包含必要的parameters和returns字段
                    self.registry[tool_name] = {
                        "name": tool_name,
                        "description": getattr(direct_func, "__doc__", "").strip(),
                        "function": direct_func,
                        "module": module,
                        "original_name": tool_name,
                        "parameters": [],  # 添加parameters字段
                        "returns": [],  # 添加returns字段以避免警告
                    }

                    # Store metadata
                    # 存储元数据
                    self.tool_metadata[tool_name] = {
                        "module_name": tool_name,
                        "function_name": tool_name,
                        "source_file": module.__file__
                        if hasattr(module, "__file__")
                        else None,
                    }

                    results = {tool_name: True}
                    return results
            except Exception as e:
                print(f"错误: 直接注册失败: {str(e)}")

        # 如果直接方法失败，使用get_tool_functions
        tool_functions = self.get_tool_functions(module, tool_name)
        results = {}

        for func_name, tool_func in tool_functions.items():
            # Try various methods to find callable function
            # 尝试各种方法来找到可调用的函数
            actual_func = None

            # Check if directly callable
            # 检查直接是否可调用
            if callable(tool_func):
                actual_func = tool_func
            # Check if has fn attribute
            # 检查是否有fn属性
            elif hasattr(tool_func, "fn") and callable(tool_func.fn):
                actual_func = tool_func.fn
            # Check if has __call__ method
            # 检查是否有__call__方法
            elif hasattr(tool_func, "__call__"):
                actual_func = tool_func

            if actual_func:
                try:
                    reg_name = func_name if len(tool_functions) > 1 else tool_name

                    # Create complete tool information with parameters and returns fields
                    # 创建完整的工具信息，包含parameters和returns字段
                    self.registry[reg_name] = {
                        "name": func_name,
                        "description": getattr(actual_func, "__doc__", "").strip(),
                        "function": actual_func,
                        "module": module,
                        "original_name": func_name,
                        "parameters": [],  # 添加parameters字段
                        "returns": [],  # 添加returns字段
                    }

                    # 存储元数据
                    self.tool_metadata[reg_name] = {
                        "module_name": tool_name,
                        "function_name": func_name,
                        "source_file": module.__file__
                        if hasattr(module, "__file__")
                        else None,
                    }

                    results[func_name] = True
                except Exception as e:
                    print(f"错误: 注册工具 {func_name} 失败: {str(e)}")
                    results[func_name] = False
            else:
                print(f"警告: {func_name} 不是可调用对象，跳过")
                results[func_name] = False

        return results

    def register_all_tools(
        self, filter_pattern: str = None
    ) -> Dict[str, Dict[str, bool]]:
        """
        Register all available tools
        注册所有可用的工具

        Args:
            filter_pattern: Regular expression pattern to filter tool names
            filter_pattern: 正则表达式模式，用于过滤工具名称

        Returns:
            Dictionary of registration results
            注册结果字典
        """
        results = {}
        tool_names = self.discover_tools()

        # Apply filter
        # 应用过滤器
        if filter_pattern:
            pattern = re.compile(filter_pattern)
            tool_names = [name for name in tool_names if pattern.match(name)]

        print(f"开始注册 {len(tool_names)} 个工具模块...")

        for tool_name in tool_names:
            print(f"处理模块: {tool_name}")
            module_results = self.register_tool(tool_name)
            if module_results:
                results[tool_name] = module_results
                # Display registration results for tools in module
                # 显示模块内工具的注册结果
                for func_name, success in module_results.items():
                    status = "✅" if success else "❌"
                    print(f"  {status} {func_name}")

        # Calculate overall statistics
        # 计算总体统计
        total_tools = sum(len(module_results) for module_results in results.values())
        success_tools = sum(
            sum(1 for success in module_results.values() if success)
            for module_results in results.values()
        )

        print(
            f"工具注册完成: 模块 {len(results)}, 工具总数 {total_tools}, 成功 {success_tools}, 失败 {total_tools - success_tools}"
        )

        return results

    def get_registered_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered tools
        获取所有已注册的工具

        Returns:
            Dictionary of registered tools
            已注册工具的字典
        """
        return self.registry.copy()

    def get_tool_by_name(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get tool by name
        根据名称获取工具

        Args:
            tool_name: Name of the tool to get
            tool_name: 要获取的工具名称

        Returns:
            Tool information or None if not found
            工具信息，如果未找到则返回None
        """
        return self.registry.get(tool_name)

    def categorize_tools(self) -> Dict[str, List[str]]:
        """
        Categorize tools
        对工具进行分类

        Returns:
            Dictionary of tool categories mapping to tool names
            工具类别到工具名称的映射字典
        """
        categories = {
            "git_operations": [],  # Git-related operations
            # Git相关操作
            "west_commands": [],  # West commands
            # West命令相关
            "zephyr_management": [],  # Zephyr management
            # Zephyr管理相关
            "validation_tools": [],  # Validation tools
            # 验证工具
            "other_tools": [],  # Other tools
            # 其他工具
        }

        # More detailed keyword classification
        # 更详细的关键词分类
        git_keywords = [
            "git",
            "branch",
            "pr",
            "checkout",
            "rebase",
            "fetch",
            "status",
            "clone",
            "push",
            "pull",
        ]
        west_keywords = ["west", "flash", "update", "build", "config", "init"]
        zephyr_keywords = ["zephyr", "version", "switch", "board", "device"]
        validation_keywords = ["validate", "check", "verify", "test", "lint"]

        for tool_name, tool_info in self.registry.items():
            # Get tool description
            # 获取工具描述
            description = tool_info.get("description", "").lower()

            # Consider both tool name and description for classification
            # 综合考虑工具名称和描述进行分类
            name_lower = tool_name.lower()

            if any(
                keyword in name_lower or keyword in description
                for keyword in git_keywords
            ):
                categories["git_operations"].append(tool_name)
            elif any(
                keyword in name_lower or keyword in description
                for keyword in west_keywords
            ):
                categories["west_commands"].append(tool_name)
            elif any(
                keyword in name_lower or keyword in description
                for keyword in zephyr_keywords
            ):
                categories["zephyr_management"].append(tool_name)
            elif any(
                keyword in name_lower or keyword in description
                for keyword in validation_keywords
            ):
                categories["validation_tools"].append(tool_name)
            else:
                categories["other_tools"].append(tool_name)

        return categories

    def _snake_to_camel(self, snake_str: str) -> str:
        """
        Convert snake_case to camelCase
        将蛇形命名法转换为驼峰命名法

        Args:
            snake_str: String in snake_case
            snake_str: 蛇形命名法的字符串

        Returns:
            String in camelCase
            驼峰命名法的字符串
        """
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def generate_tool_documentation(
        self, output_file: str = None, format: str = "markdown"
    ) -> str:
        """
        Generate tool documentation
        生成工具文档

        Args:
            output_file: Output file path
            output_file: 输出文件路径
            format: Output format, supports "markdown", "json", "text"
            format: 输出格式，支持 "markdown", "json", "text"

        Returns:
            Generated documentation as string
            生成的文档字符串
        """
        if format == "json":
            # Generate JSON format documentation
            # 生成JSON格式文档
            doc_data = {"title": "Zephyr MCP Agent 工具文档", "categories": {}}

            categories = self.categorize_tools()
            for category, tool_names in categories.items():
                if tool_names:
                    doc_data["categories"][self._format_category_name(category)] = {}
                    for tool_name in tool_names:
                        tool_info = self.registry[tool_name]
                        doc_data["categories"][self._format_category_name(category)][
                            tool_name
                        ] = {
                            "description": tool_info["description"],
                            "parameters": tool_info["parameters"],
                            "returns": tool_info["returns"],
                        }

            import json

            documentation = json.dumps(doc_data, ensure_ascii=False, indent=2)

        elif format == "text":
            # Generate plain text format documentation
            # 生成纯文本格式文档
            doc_lines = ["Zephyr MCP Agent 工具文档", "=" * 40, ""]

            categories = self.categorize_tools()
            for category, tool_names in categories.items():
                if tool_names:
                    doc_lines.append(f"{self._format_category_name(category)}")
                    doc_lines.append("-" * len(self._format_category_name(category)))
                    doc_lines.append("")

                    for tool_name in tool_names:
                        tool_info = self.registry[tool_name]
                        doc_lines.append(f"工具名: {tool_name}")
                        doc_lines.append(f"描述: {tool_info['description']}")

                        if tool_info["parameters"]:
                            doc_lines.append("参数:")
                            for param in tool_info["parameters"]:
                                required_mark = (
                                    "(必需)" if param["required"] else "(可选)"
                                )
                                doc_lines.append(
                                    f"  - {param['name']}: {param['description']} {required_mark}"
                                )

                        doc_lines.append(f"返回值: {tool_info['returns']}")
                        doc_lines.append("")

            documentation = "\n".join(doc_lines)

        else:  # 默认markdown格式
            doc_lines = ["# Zephyr MCP Agent 工具文档", "", "## 可用工具列表", ""]

            # Add statistical information
            # 添加统计信息
            total_tools = len(self.registry)
            categories = self.categorize_tools()
            doc_lines.append(f"**总工具数量:** {total_tools}")
            doc_lines.append("")

            for category, tool_names in categories.items():
                if tool_names:
                    doc_lines.append(
                        f"### {self._format_category_name(category)} ({len(tool_names)})"
                    )
                    doc_lines.append("")

                    for tool_name in tool_names:
                        tool_info = self.registry[tool_name]
                        doc_lines.append(f"#### {tool_name}")
                        doc_lines.append(f"**描述:** {tool_info['description']}")
                        doc_lines.append("")

                        # Add parameter information
                        # 添加参数信息
                        if tool_info["parameters"]:
                            doc_lines.append("**参数:**")
                            for param in tool_info["parameters"]:
                                required_mark = (
                                    " (必需)" if param["required"] else " (可选)"
                                )
                                param_type = (
                                    f" <{param.get('type', 'any')}>"
                                    if "type" in param
                                    else ""
                                )
                                doc_lines.append(
                                    f"- `{param['name']}`{param_type}: {param['description']}{required_mark}"
                                )
                            doc_lines.append("")

                        # Add return value information
                        # 添加返回值信息
                        doc_lines.append(f"**返回值:** {tool_info['returns']}")

                        # Add source information
                        # 添加来源信息
                        if tool_name in self.tool_metadata:
                            meta = self.tool_metadata[tool_name]
                            doc_lines.append(f"**来源:** {meta['module_name']} 模块")

                        doc_lines.append("")

            documentation = "\n".join(doc_lines)

        # Write to output file if specified
        # 如果指定了输出文件，写入文件
        if output_file:
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(documentation)
                print(f"工具文档已生成: {output_file}")
            except Exception as e:
                print(f"错误: 生成工具文档失败: {str(e)}")

        return documentation

    def filter_tools(self, keyword: str) -> List[str]:
        """
        Filter tools by keyword
        根据关键词过滤工具

        Args:
            keyword: Search keyword
            keyword: 搜索关键词

        Returns:
            List of matching tool names
            匹配的工具名称列表
        """
        keyword_lower = keyword.lower()
        matched_tools = []

        for tool_name, tool_info in self.registry.items():
            if (
                keyword_lower in tool_name.lower()
                or keyword_lower in tool_info.get("description", "").lower()
            ):
                matched_tools.append(tool_name)

        return matched_tools

    def get_tool_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Get tool health status
        获取工具健康状态

        Returns:
            Dictionary containing health information for each tool
            包含每个工具健康信息的字典
        """
        health_info = {}

        for tool_name, tool_info in self.registry.items():
            health = {
                "status": "healthy",
                "issues": [],
                "parameter_count": len(tool_info.get("parameters", [])),
                "has_description": bool(tool_info.get("description", "")),
            }

            # Check if has description
            # 检查是否有描述
            if not health["has_description"]:
                health["status"] = "warning"
                health["issues"].append("工具没有描述")

            # Check if parameters have descriptions
            # 检查参数是否有描述
            for param in tool_info.get("parameters", []):
                if not param.get("description", ""):
                    health["status"] = "warning"
                    health["issues"].append(f"参数 '{param['name']}' 没有描述")

            health_info[tool_name] = health

        return health_info

    def _format_category_name(self, category: str) -> str:
        """
        Format category name to readable format
        格式化分类名称为可读格式

        Args:
            category: Category name in snake_case
            category: 蛇形命名法的分类名称

        Returns:
            Formatted category name with capitalized words
            格式化后的分类名称（单词首字母大写）
        """
        # Replace underscores with spaces and capitalize each word
        # 替换下划线为空格，并将每个单词首字母大写
        return " ".join(word.capitalize() for word in category.split("_"))


def get_default_tool_registry() -> ToolRegistry:
    """
    Get default tool registry instance
    获取默认的工具注册表实例

    Returns:
        Default ToolRegistry instance
        默认的ToolRegistry实例
    """
    # Determine absolute path of tools directory
    # 确定工具目录的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tools_dir = os.path.join(current_dir, "..", "tools")

    return ToolRegistry(tools_dir)
