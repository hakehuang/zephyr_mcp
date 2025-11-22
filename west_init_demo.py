#!/usr/bin/env python3
"""
West init 演示脚本
展示 west init 命令的基本用法
"""

import os
import subprocess
import sys

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    print(f"运行命令: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        print(f"退出码: {result.returncode}")
        if result.stdout:
            print(f"输出:\n{result.stdout}")
        if result.stderr:
            print(f"错误:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"运行命令失败: {e}")
        return False

def main():
    """主函数"""
    print("=== West Init 演示 ===\n")
    
    # 1. 检查 west 是否安装
    print("1. 检查 west 工具:")
    if not run_command("west --version"):
        print("west 未安装，请先安装: pip install west")
        return
    
    print("\n2. West init 基本用法:")
    print("west init [选项] [目录]")
    print("常用选项:")
    print("  -m URL, --manifest-url URL  指定 manifest 仓库 URL")
    print("  --mr REV, --manifest-rev REV  指定 manifest 版本")
    print("  目录                        指定项目目录 (默认: 当前目录)")
    
    print("\n3. 示例命令:")
    print("# 基本初始化")
    print("west init my-zephyr-project")
    print()
    print("# 使用自定义 manifest 仓库")
    print("west init my-project -m https://github.com/myorg/manifest")
    print()
    print("# 使用特定分支")
    print("west init my-project -m https://github.com/zephyrproject-rtos/zephyr --mr v3.5.0")
    
    print("\n4. 初始化后的步骤:")
    print("cd my-zephyr-project")
    print("west update  # 更新所有项目")
    
    print("\n=== 演示完成 ===")

if __name__ == "__main__":
    main()