#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言管理模块
处理多语言支持和资源管理
"""

import os
import sys
from typing import Dict, Any, Optional

# 导入语言资源
from src.utils.language_resources import LanguageManager, get_text, set_language


def setup_language(default_language: str = "zh") -> None:
    """设置全局语言"""
    set_language(default_language)


def get_localized_text(key: str, *args, **kwargs) -> str:
    """获取本地化文本"""
    return get_text(key, *args, **kwargs)


def create_language_manager(default_language: str = "zh") -> LanguageManager:
    """创建语言管理器实例"""
    return LanguageManager(default_language)


def get_available_languages() -> Dict[str, str]:
    """获取可用语言列表"""
    return {
        "zh": "中文 (Chinese)",
        "en": "English (英语)"
    }


def validate_language(language: str) -> bool:
    """验证语言代码是否有效"""
    available_languages = get_available_languages()
    return language in available_languages


def switch_language(language: str, language_manager: Optional[LanguageManager] = None) -> bool:
    """切换语言"""
    if not validate_language(language):
        return False
    
    set_language(language)
    
    if language_manager:
        language_manager.set_language(language)
    
    return True


def get_language_info(language: str) -> Dict[str, Any]:
    """获取语言信息"""
    available_languages = get_available_languages()
    
    if language not in available_languages:
        return {
            "code": language,
            "name": "Unknown",
            "available": False
        }
    
    return {
        "code": language,
        "name": available_languages[language],
        "available": True
    }


def format_language_display(language: str) -> str:
    """格式化语言显示"""
    info = get_language_info(language)
    if info["available"]:
        return f"{info['name']} ({info['code']})"
    else:
        return f"Unknown ({language})"


def get_language_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """从配置中获取语言配置"""
    language_config = config.get("language", {})
    
    # 确保配置完整性
    default_language = language_config.get("default", "zh")
    available_languages = language_config.get("available", ["zh", "en"])
    auto_detect = language_config.get("auto_detect", True)
    
    # 验证默认语言是否在可用语言中
    if default_language not in available_languages:
        default_language = available_languages[0] if available_languages else "zh"
    
    return {
        "default": default_language,
        "available": available_languages,
        "auto_detect": auto_detect
    }


def detect_language_from_request(headers: Dict[str, str]) -> str:
    """从HTTP请求头检测语言"""
    accept_language = headers.get('Accept-Language', '')
    
    # 简单的语言检测逻辑
    if 'zh' in accept_language:
        return 'zh'
    elif 'en' in accept_language:
        return 'en'
    else:
        return 'zh'  # 默认中文


def get_language_aware_text(language_manager: LanguageManager, key: str, *args, **kwargs) -> str:
    """获取语言感知的文本（使用语言管理器）"""
    return language_manager.get_text(key, *args, **kwargs)


def create_language_aware_logger(logger, language_manager: LanguageManager):
    """创建语言感知的日志器"""
    class LanguageAwareLogger:
        def __init__(self, logger, language_manager):
            self.logger = logger
            self.language_manager = language_manager
        
        def debug(self, key, *args, **kwargs):
            message = self.language_manager.get_text(key, *args, **kwargs)
            self.logger.debug(message)
        
        def info(self, key, *args, **kwargs):
            message = self.language_manager.get_text(key, *args, **kwargs)
            self.logger.info(message)
        
        def warning(self, key, *args, **kwargs):
            message = self.language_manager.get_text(key, *args, **kwargs)
            self.logger.warning(message)
        
        def error(self, key, *args, **kwargs):
            message = self.language_manager.get_text(key, *args, **kwargs)
            self.logger.error(message)
        
        def critical(self, key, *args, **kwargs):
            message = self.language_manager.get_text(key, *args, **kwargs)
            self.logger.critical(message)
        
        # 传递其他方法
        def __getattr__(self, name):
            return getattr(self.logger, name)
    
    return LanguageAwareLogger(logger, language_manager)