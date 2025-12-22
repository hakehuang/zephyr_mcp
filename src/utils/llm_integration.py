#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Integration Module - Provides interfaces with various large language models
大模型集成模块 - 提供与各种大语言模型的接口
"""

import os
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
# 加载环境变量
load_dotenv()

# Configure logging
# 配置日志
logger = logging.getLogger(__name__)


class LLMIntegration:
    """
    LLM Integration class, provides unified interface to access different large language models
    大语言模型集成类，提供统一的接口访问不同的大模型
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM integration
        初始化LLM集成

        Args:
            config: LLM configuration information
            config: 大模型配置信息
        """
        self.config = config or self._load_default_config()
        self._openai_client = None
        self._anthropic_client = None
        self._deepseek_client = None
        # Ensure all required properties are properly initialized
        # 确保所有必需的属性都被正确初始化
        self.enabled = True
        self.default_model = self.config.get("default_model", "gpt-3.5-turbo")
        self.cache_enabled = False
        self.clients = {"openai": None, "anthropic": None, "deepseek": None}

    def get_status(self):
        """
        Get LLM integration status
        获取LLM集成状态

        Returns:
            Dictionary containing status information
            包含状态信息的字典
        """
        # Safely get status information
        # 安全地获取状态信息
        return {
            "enabled": self.enabled,
            "default_model": self.default_model,
            "cache_enabled": self.cache_enabled,
            "available_providers": list(self.clients.keys()),
            "config": self.config,
        }

    def _load_default_config(self) -> Dict[str, Any]:
        """
        Load default configuration
        加载默认配置

        Returns:
            Default configuration dictionary
            默认配置字典
        """
        return {
            "default_model": os.getenv("LLM_DEFAULT_MODEL", "gpt-4-turbo"),
            "models": {
                "openai": {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "models": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                    "default": "gpt-4-turbo",
                },
                "anthropic": {
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                    "default": "claude-3-sonnet-20240229",
                },
                "deepseek": {
                    "api_key": os.getenv("DEEPSEEK_API_KEY"),
                    "models": ["deepseek-chat", "deepseek-coder"],
                    "default": "deepseek-chat",
                },
            },
        }

    def _get_openai_client(self):
        """
        Lazy initialize OpenAI client
        延迟初始化OpenAI客户端

        Returns:
            OpenAI client instance
            OpenAI客户端实例
        """
        if self._openai_client is None:
            try:
                from openai import OpenAI

                api_key = self.config["models"]["openai"]["api_key"]
                if api_key:
                    self._openai_client = OpenAI(api_key=api_key)
            except ImportError:
                logger.warning("未安装OpenAI库，请运行 'pip install openai'")
            except Exception as e:
                logger.error(f"初始化OpenAI客户端失败: {str(e)}")
        return self._openai_client

    def _get_anthropic_client(self):
        """
        Lazy initialize Anthropic client
        延迟初始化Anthropic客户端

        Returns:
            Anthropic client instance
            Anthropic客户端实例
        """
        if self._anthropic_client is None:
            try:
                import anthropic

                api_key = self.config["models"]["anthropic"]["api_key"]
                if api_key:
                    self._anthropic_client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                logger.warning("未安装Anthropic库，请运行 'pip install anthropic'")
            except Exception as e:
                logger.error(f"初始化Anthropic客户端失败: {str(e)}")
        return self._anthropic_client

    def _determine_provider(self, model_name: str) -> str:
        """
        Determine provider based on model name
        根据模型名称确定提供商

        Args:
            model_name: Model name
            model_name: 模型名称

        Returns:
            Provider name ('openai', 'anthropic' or 'deepseek')
            提供商名称 ('openai', 'anthropic' 或 'deepseek')
        """
        if model_name.startswith(
            ("gpt-", "text-", "davinci-", "curie-", "babbage-", "ada-")
        ):
            return "openai"
        elif model_name.startswith(("claude-",)):
            return "anthropic"
        elif model_name.startswith(("deepseek-",)):
            return "deepseek"
        else:
            # Choose based on default configuration
            # 根据默认配置选择
            return "openai"  # 默认使用OpenAI

    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Generate text response
        生成文本响应

        Args:
            prompt: User prompt
            prompt: 用户提示
            model: Model name to use
            model: 使用的模型名称
            system_prompt: System prompt
            system_prompt: 系统提示
            temperature: Temperature parameter (0.0-2.0)
            temperature: 温度参数 (0.0-2.0)
            max_tokens: Maximum number of tokens to generate
            max_tokens: 最大生成token数

        Returns:
            Dictionary containing generated text and metadata
            包含生成文本和元数据的字典
        """
        try:
            # Determine the model to use
            # 确定使用的模型
            model_name = model or self.config["default_model"]
            provider = self._determine_provider(model_name)

            logger.info(f"使用模型 {model_name} 生成响应")

            # 根据提供商调用不同的API
            if provider == "openai":
                return self._generate_openai(
                    prompt, model_name, system_prompt, temperature, max_tokens
                )
            elif provider == "anthropic":
                return self._generate_anthropic(
                    prompt, model_name, system_prompt, temperature, max_tokens
                )
            elif provider == "deepseek":
                return self._generate_deepseek(
                    prompt, model_name, system_prompt, temperature, max_tokens
                )
            else:
                raise ValueError(f"不支持的模型提供商: {provider}")

        except Exception as e:
            logger.error(f"生成文本失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "model": model or self.config["default_model"],
            }

    def _generate_openai(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """
        Generate text using OpenAI API
        使用OpenAI API生成文本
        """
        client = self._get_openai_client()
        if not client:
            raise RuntimeError("OpenAI客户端未初始化，请检查API密钥")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "success": True,
            "text": response.choices[0].message.content,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }

    def _generate_anthropic(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """
        Generate text using Anthropic API
        使用Anthropic API生成文本
        """
        client = self._get_anthropic_client()
        if not client:
            raise RuntimeError("Anthropic客户端未初始化，请检查API密钥")

        response = client.messages.create(
            model=model,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "success": True,
            "text": response.content[0].text,
            "model": model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens
                + response.usage.output_tokens,
            },
        }

    def analyze_code(
        self, code: str, query: str, model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze code and answer related questions
        分析代码并回答相关问题

        Args:
            code: Code to analyze
            code: 要分析的代码
            query: Question about the code
            query: 关于代码的问题
            model: Model name to use
            model: 使用的模型名称

        Returns:
            Analysis result
            分析结果
        """
        system_prompt = "你是一位专业的代码分析专家，帮助开发者理解代码功能、发现问题并提供改进建议。"
        prompt = f"代码:\n```python\n{code}\n```\n\n问题: {query}"

        return self.generate_text(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.3,  # Code analysis uses lower temperature for more accurate results
            # 代码分析使用较低温度以获取更准确的结果
            max_tokens=1500,
        )

    def generate_tool_description(
        self, tool_function, model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed description and documentation for tool function
        为工具函数生成详细的描述和文档

        Args:
            tool_function: Tool function object
            tool_function: 工具函数对象
            model: Model name to use
            model: 使用的模型名称

        Returns:
            Generated tool description
            生成的工具描述
        """
        import inspect

        # Get function source code
        # 获取函数源码
        source_code = inspect.getsource(tool_function)
        function_name = tool_function.__name__

        system_prompt = (
            "你是一位专业的API文档生成专家，为给定的函数生成清晰、准确的描述和文档。"
        )
        prompt = f"函数源码:\n```python\n{source_code}\n```\n\n请为这个名为{function_name}的函数生成:\n1. 简洁明了的描述（一句话）\n2. 详细的功能说明\n3. 参数说明，包括参数类型、是否必需和用途\n4. 返回值说明\n5. 可能的错误或异常情况\n\n请格式化为JSON格式，包含description、parameters和returns字段。"

        return self.generate_text(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=1500,
        )

    def _get_deepseek_client(self):
        """
        Lazy initialize DeepSeek client
        延迟初始化DeepSeek客户端

        Returns:
            DeepSeek client instance
            DeepSeek客户端实例
        """
        if self._deepseek_client is None:
            try:
                # DeepSeek uses requests for API calls
                # DeepSeek使用requests进行API调用
                import requests

                api_key = self.config["models"]["deepseek"]["api_key"]
                if api_key:
                    # DeepSeek client implementation
                    # DeepSeek客户端实现
                    self._deepseek_client = {"api_key": api_key, "requests": requests}
            except ImportError:
                logger.warning("未安装requests库，请运行 'pip install requests'")
            except Exception as e:
                logger.error(f"初始化DeepSeek客户端失败: {str(e)}")
        return self._deepseek_client

    def _generate_deepseek(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """
        Generate text using DeepSeek API
        使用DeepSeek API生成文本
        """
        client = self._get_deepseek_client()
        if not client:
            raise RuntimeError("DeepSeek客户端未初始化，请检查API密钥")

        # DeepSeek API endpoint
        # DeepSeek API 端点
        url = "https://api.deepseek.com/v1/chat/completions"

        # Build message list
        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Prepare request parameters
        # 准备请求参数
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Set request headers
        # 设置请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {client['api_key']}",
        }

        # Send request
        # 发送请求
        response = client["requests"].post(url, json=data, headers=headers)
        response.raise_for_status()  # 如果请求失败，抛出异常

        # Process response
        # 处理响应
        result = response.json()

        return {
            "success": True,
            "text": result["choices"][0]["message"]["content"],
            "model": model,
            "usage": {
                "prompt_tokens": result["usage"]["prompt_tokens"],
                "completion_tokens": result["usage"]["completion_tokens"],
                "total_tokens": result["usage"]["total_tokens"],
            },
        }

    def is_available(self) -> bool:
        """
        Check if any LLM is available
        检查是否有可用的大模型

        Returns:
            Whether any LLM is available
            是否有可用的大模型
        """
        has_openai = self.config["models"]["openai"]["api_key"] is not None
        has_anthropic = self.config["models"]["anthropic"]["api_key"] is not None
        has_deepseek = self.config["models"]["deepseek"]["api_key"] is not None

        return has_openai or has_anthropic or has_deepseek


# Create global LLM integration instance
# 创建全局LLM集成实例
llm_integration = LLMIntegration()


def get_llm_integration() -> LLMIntegration:
    """
    Get LLM integration instance
    获取LLM集成实例

    Returns:
        LLMIntegration instance
        LLMIntegration实例
    """
    return llm_integration
