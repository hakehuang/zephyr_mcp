#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenTelemetry集成模块 / OpenTelemetry Integration Module
处理分布式追踪的初始化和管理 / Handle distributed tracing initialization and management
"""

import os
import sys
from typing import Dict, Any, Optional, TYPE_CHECKING

# OpenTelemetry相关导入 / OpenTelemetry related imports
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider, Span
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.instrumentation.http import HTTPInstrumentor
    
    # Agno Instrumentor 导入 / Agno Instrumentor import
    try:
        from openinference.instrumentation.agno import AgnoInstrumentor
        AGNO_INSTRUMENTOR_AVAILABLE = True
    except ImportError:
        AGNO_INSTRUMENTOR_AVAILABLE = False
        AgnoInstrumentor = None
    
    OPENTELEMETRY_AVAILABLE = True
    
    if TYPE_CHECKING:
        from opentelemetry import trace
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    AGNO_INSTRUMENTOR_AVAILABLE = False
    # 为类型检查提供占位符 / Placeholder for type checking
    if TYPE_CHECKING:
        from typing import Any as trace


class OpenTelemetryManager:
    """OpenTelemetry管理器类 / OpenTelemetry Manager Class"""
    
    def __init__(self, config: Dict[str, Any], logger):
        """初始化OpenTelemetry管理器 / Initialize OpenTelemetry manager"""
        self.config = config
        self.logger = logger
        self.tracer = None
        self.initialized = False
        
    def init_opentelemetry(self, agent):
        """初始化OpenTelemetry追踪 / Initialize OpenTelemetry tracing"""
        if not OPENTELEMETRY_AVAILABLE:
            self.logger.info("OpenTelemetry 依赖未安装，将禁用分布式追踪功能")
            return None
            
        try:
            otel_config = self.config.get("opentelemetry", {})
            
            # 检查配置是否启用，以及agno Agent的telemetry属性是否允许
            # Check if configuration is enabled and if agno Agent's telemetry attribute allows
            if not otel_config.get("enabled", False) or (hasattr(agent, 'telemetry') and not agent.telemetry):
                self.logger.info("OpenTelemetry 已禁用")
                return None
            
            # 创建资源 / Create resource
            resource = Resource.create({
                SERVICE_NAME: otel_config.get("service_name", self.config.get("agent_name", "zephyr_mcp_agent")),
                "agent_version": self.config.get("version", "1.0.0"),
                "language": self.config.get("language", {}).get("default", "zh")
            })
            
            # 创建追踪提供者 / Create tracer provider
            tracer_provider = TracerProvider(resource=resource)
            
            # 添加Span处理器 / Add span processor
            exporter_type = otel_config.get("exporter", "console")
            
            if exporter_type == "otlp":
                otlp_endpoint = otel_config.get("otlp_endpoint", "http://localhost:4318/v1/traces")
                headers = otel_config.get("headers", {})
                
                # 如果配置了LangSmith端点，使用对应的配置
                # If LangSmith endpoint is configured, use corresponding configuration
                if "langchain.com" in otlp_endpoint:
                    headers = {
                        "x-api-key": otel_config.get("api_key", ""),
                        "Langsmith-Project": otel_config.get("project_name", "zephyr_mcp_agent")
                    }
                
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint, headers=headers)
                self.logger.info(f"使用OTLP导出器，端点: {otlp_endpoint}")
                
                # 使用SimpleSpanProcessor以获得更快的响应
                # Use SimpleSpanProcessor for faster response
                span_processor = SimpleSpanProcessor(exporter)
            else:
                exporter = ConsoleSpanExporter()
                self.logger.info("使用控制台导出器")
                span_processor = BatchSpanProcessor(exporter)
            
            tracer_provider.add_span_processor(span_processor)
            
            # 设置全局追踪提供者 / Set global tracer provider
            trace.set_tracer_provider(tracer_provider)
            
            # 获取tracer / Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            # 启用HTTP工具自动检测 / Enable HTTP instrumentation
            HTTPInstrumentor().instrument()
            
            # 启用Agno的自动埋点（如果可用）
            # Enable Agno auto-instrumentation (if available)
            if AGNO_INSTRUMENTOR_AVAILABLE and AgnoInstrumentor:
                AgnoInstrumentor().instrument()
                self.logger.info("Agno Instrumentor 已启用")
            else:
                self.logger.info("Agno Instrumentor 不可用，使用标准OpenTelemetry")
            
            self.initialized = True
            self.logger.info("OpenTelemetry 初始化成功")
            return self.tracer
            
        except Exception as e:
            self.logger.error(f"OpenTelemetry 初始化失败: {str(e)}")
            return None
    
    def create_span(self, name: str, attributes: Dict[str, Any] = None):
        """创建新的Span / Create new Span"""
        if not self.initialized or not self.tracer:
            return None
            
        try:
            span = self.tracer.start_span(name)
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            return span
        except Exception as e:
            self.logger.error(f"创建Span失败: {str(e)}")
            return None
    
    def end_span(self, span, status_code: int = None, error: bool = False, error_message: str = None):
        """结束Span / End Span"""
        if not span:
            return
            
        try:
            if status_code is not None:
                span.set_attribute("http.status_code", status_code)
            
            if error:
                span.set_attribute("error", True)
                if error_message:
                    span.set_attribute("error.message", error_message)
            
            span.end()
        except Exception as e:
            self.logger.error(f"结束Span失败: {str(e)}")
    
    def is_enabled(self) -> bool:
        """检查OpenTelemetry是否启用 / Check if OpenTelemetry is enabled"""
        return self.initialized and self.tracer is not None


def init_opentelemetry(config: Dict[str, Any], agent, logger):
    """初始化OpenTelemetry的便捷函数 / Convenience function to initialize OpenTelemetry"""
    manager = OpenTelemetryManager(config, logger)
    return manager.init_opentelemetry(agent)


def get_default_opentelemetry_config() -> Dict[str, Any]:
    """获取默认的OpenTelemetry配置 / Get default OpenTelemetry configuration"""
    return {
        "enabled": False,
        "service_name": "zephyr_mcp_agent",
        "exporter": "console",  # console, otlp / 控制台, OTLP
        "otlp_endpoint": "http://localhost:4318/v1/traces",
        "sampler": "always_on",
        "headers": {},  # OTLP导出器的自定义头部 / Custom headers for OTLP exporter
        "api_key": "",  # LangSmith等平台的API密钥 / API key for platforms like LangSmith
        "project_name": "zephyr_mcp_agent"  # LangSmith项目名 / LangSmith project name
    }