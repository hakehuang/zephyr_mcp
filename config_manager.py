#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
处理配置文件的加载、验证和管理
"""

import json
import os
from typing import Dict, Any

# 导入语言资源
from src.utils.language_resources import get_text


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 验证和补充配置
        return validate_and_complete_config(config)
        
    except Exception as e:
        print(get_text("config_load_error", str(e)))
        # 返回默认配置
        return get_default_config()


def validate_and_complete_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """验证和补充配置"""
    # 确保必需字段存在
    if "agent_name" not in config:
        config["agent_name"] = get_text("agent_name")
    
    if "version" not in config:
        config["version"] = "1.0.0"
    
    if "description" not in config:
        config["description"] = get_text("agent_description")
    
    # 确保工具目录配置
    if "tools_directory" not in config:
        config["tools_directory"] = "./src/tools"
    
    if "utils_directory" not in config:
        config["utils_directory"] = "./src/utils"
    
    # 确保日志级别配置
    if "log_level" not in config:
        config["log_level"] = "INFO"
    
    # 确保语言配置
    if "language" not in config:
        config["language"] = {
            "default": "zh",
            "available": ["zh", "en"],
            "auto_detect": True
        }
    
    # 确保OpenTelemetry配置
    if "opentelemetry" not in config:
        config["opentelemetry"] = get_default_opentelemetry_config()
    
    # 确保服务器配置
    if "port" not in config:
        config["port"] = 8001
    
    if "host" not in config:
        config["host"] = "localhost"
    
    # 确保LLM配置
    if "llm" not in config:
        config["llm"] = {
            "enabled": False,
            "providers": {
                "openai": {
                    "api_key": "",
                    "model": "gpt-3.5-turbo"
                },
                "anthropic": {
                    "api_key": "",
                    "model": "claude-3-sonnet-20240229"
                }
            }
        }
    
    return config


def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
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
        },
        "opentelemetry": get_default_opentelemetry_config(),
        "port": 8001,
        "host": "localhost",
        "llm": {
            "enabled": False,
            "providers": {
                "openai": {
                    "api_key": "",
                    "model": "gpt-3.5-turbo"
                },
                "anthropic": {
                    "api_key": "",
                    "model": "claude-3-sonnet-20240229"
                }
            }
        }
    }


def get_default_opentelemetry_config() -> Dict[str, Any]:
    """获取默认的OpenTelemetry配置"""
    return {
        "enabled": False,
        "service_name": get_text("agent_name"),
        "exporter": "console",  # console, otlp
        "otlp_endpoint": "http://localhost:4318/v1/traces",
        "sampler": "always_on",
        "headers": {},  # OTLP导出器的自定义头部
        "api_key": "",  # LangSmith等平台的API密钥
        "project_name": "zephyr_mcp_agent"  # LangSmith项目名
    }


def save_config(config: Dict[str, Any], config_path: str = "config.json") -> bool:
    """保存配置到文件"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(get_text("config_save_error", str(e)))
        return False


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """通过路径获取配置值"""
    keys = key_path.split('.')
    current = config
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def set_config_value(config: Dict[str, Any], key_path: str, value: Any) -> bool:
    """通过路径设置配置值"""
    keys = key_path.split('.')
    current = config
    
    # 遍历到最后一个键的父级
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    # 设置最终值
    current[keys[-1]] = value
    return True


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """验证配置的有效性"""
    errors = []
    
    # 验证必需字段
    if not config.get("agent_name"):
        errors.append("agent_name is required")
    
    if not config.get("version"):
        errors.append("version is required")
    
    # 验证端口范围
    port = config.get("port", 8001)
    if not isinstance(port, int) or port < 1 or port > 65535:
        errors.append("port must be an integer between 1 and 65535")
    
    # 验证日志级别
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.get("log_level") not in valid_log_levels:
        errors.append(f"log_level must be one of {valid_log_levels}")
    
    # 验证语言配置
    language_config = config.get("language", {})
    if language_config.get("default") not in language_config.get("available", []):
        errors.append("default language must be in available languages")
    
    # 验证OpenTelemetry配置
    otel_config = config.get("opentelemetry", {})
    if otel_config.get("enabled", False):
        if otel_config.get("exporter") not in ["console", "otlp"]:
            errors.append("opentelemetry.exporter must be 'console' or 'otlp'")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def create_sample_config(config_path: str = "config.json") -> bool:
    """创建示例配置文件"""
    sample_config = {
        "agent_name": "Zephyr MCP Agent",
        "version": "1.0.0",
        "description": "Zephyr MCP Agent for Zephyr RTOS development",
        "tools_directory": "./src/tools",
        "utils_directory": "./src/utils",
        "log_level": "INFO",
        "port": 8001,
        "host": "localhost",
        "language": {
            "default": "zh",
            "available": ["zh", "en"],
            "auto_detect": True
        },
        "opentelemetry": {
            "enabled": False,
            "service_name": "zephyr_mcp_agent",
            "exporter": "console",
            "otlp_endpoint": "http://localhost:4318/v1/traces",
            "sampler": "always_on"
        },
        "llm": {
            "enabled": False,
            "providers": {
                "openai": {
                    "api_key": "your_openai_api_key_here",
                    "model": "gpt-3.5-turbo"
                },
                "anthropic": {
                    "api_key": "your_anthropic_api_key_here",
                    "model": "claude-3-sonnet-20240229"
                }
            }
        }
    }
    
    return save_config(sample_config, config_path)