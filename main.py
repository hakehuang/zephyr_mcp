#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zephyr MCP Agent - 主入口脚本
重构后的模块化版本
"""

import os
import sys
import argparse

# 添加项目根目录到Python路径，确保可以正确导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from agent_core import ZephyrMCPAgent
from config_manager import load_config, create_sample_config
from language_manager import setup_language


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Zephyr MCP Agent")
    parser.add_argument(
        "--config", "-c", default="config.json", help="配置文件路径 (默认: config.json)"
    )
    parser.add_argument("--create-config", action="store_true", help="创建示例配置文件")
    parser.add_argument("--port", "-p", type=int, help="HTTP服务器端口 (覆盖配置文件)")
    parser.add_argument("--host", "-H", help="HTTP服务器主机 (覆盖配置文件)")
    parser.add_argument(
        "--language", "-l", choices=["zh", "en"], help="设置语言 (覆盖配置文件)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="设置日志级别 (覆盖配置文件)",
    )

    args = parser.parse_args()

    # 处理创建配置文件选项
    if args.create_config:
        if create_sample_config(args.config):
            print(f"示例配置文件已创建: {args.config}")
            return 0
        else:
            print(f"创建配置文件失败: {args.config}")
            return 1

    # 加载配置
    config = load_config(args.config)

    # 应用命令行参数覆盖
    if args.port:
        config["port"] = args.port
    if args.host:
        config["host"] = args.host
    if args.language:
        config["language"]["default"] = args.language
    if args.log_level:
        config["log_level"] = args.log_level

    # 设置全局语言
    setup_language(config.get("language", {}).get("default", "zh"))

    try:
        # 创建并启动Agent
        agent = ZephyrMCPAgent(config)
        agent.start()
        return 0
    except KeyboardInterrupt:
        print("\nAgent 被用户中断")
        return 0
    except Exception as e:
        print(f"Agent 启动失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
