#!/usr/bin/env python3
# 从zephyr仓库获取PR 1

import os
import sys

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    # 导入内部函数，因为公共工具函数需要通过MCP服务器调用
    from mcp_server import _fetch_branch_or_pr_internal
    
    print("尝试从zephyr仓库获取PR 1...")
    
    # 设置项目目录为c://zephyr_project/zephyr
    project_dir = "c:/zephyr_project/zephyr"
    
    # 调用内部函数获取PR 1
    result = _fetch_branch_or_pr_internal(
        project_dir=project_dir,
        pr_number=1,
        remote_name="origin"
    )
    
    # 打印结果
    print(f"\n操作状态: {result['status']}")
    
    if 'error' in result and result['error']:
        print(f"错误信息: {result['error']}")
    else:
        print(f"日志输出: {result.get('log', '无日志输出')}")
        print("\nPR 1 获取成功!")
    
    sys.exit(0)
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 执行过程中出现错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)