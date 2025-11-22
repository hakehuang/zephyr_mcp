#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将zephyr项目中的pull分支rebase到main分支
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from mcp_server import _git_rebase_internal
    print("✅ 成功导入git_rebase内部函数")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 设置zephyr项目目录和分支信息
ZEPHYR_PROJECT_DIR = "c:/zephyr_project/zephyr"
SOURCE_BRANCH = "pull"
TARGET_BRANCH = "main"

print(f"\n准备将 {SOURCE_BRANCH} 分支 rebase 到 {TARGET_BRANCH} 分支")
print(f"项目目录: {ZEPHYR_PROJECT_DIR}")

# 执行rebase操作
print("\n开始执行rebase操作...")
result = _git_rebase_internal(
    project_dir=ZEPHYR_PROJECT_DIR,
    source_branch=TARGET_BRANCH,  # 注意：在标准rebase中，source_branch是要rebase到的分支
    onto_branch=None,  # 不使用--onto参数
    interactive=False,
    force=False
)

# 显示rebase结果
print("\n--- Rebase 结果 ---")
print(f"状态: {result.get('status')}")

if result.get('status') == 'success':
    print("✅ Rebase 成功完成!")
    print(f"日志: {result.get('log', '无详细日志')}")
elif result.get('status') == 'conflict':
    print("⚠️ Rebase 遇到冲突")
    print(f"错误: {result.get('error')}")
    print(f"冲突解决提示: {result.get('conflict_resolution_hint')}")
    print(f"详细日志: {result.get('log', '无详细日志')}")
elif result.get('status') == 'canceled':
    print("ℹ️ Rebase 操作已取消")
    print(f"日志: {result.get('log')}")
else:
    print("❌ Rebase 失败")
    print(f"错误: {result.get('error')}")
    print(f"详细日志: {result.get('log', '无详细日志')}")