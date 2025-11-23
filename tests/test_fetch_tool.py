#!/usr/bin/env python3
# 测试fetch_branch_or_pr工具函数的基本功能和集成

import os
import sys
from typing import Dict, Any, Optional

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    # 尝试导入我们添加的函数和内部实现，验证集成是否正常
    from mcp_server import fetch_branch_or_pr, _fetch_branch_or_pr_internal
    print("✅ 成功导入fetch_branch_or_pr工具和_fetch_branch_or_pr_internal内部函数")
    
    # 验证内部函数签名（内部函数是可调用的）
    import inspect
    internal_sig = inspect.signature(_fetch_branch_or_pr_internal)
    print(f"\n_fetch_branch_or_pr_internal函数参数: {list(internal_sig.parameters.keys())}")
    
    # 验证工具存在和类型
    print(f"\nfetch_branch_or_pr工具类型: {type(fetch_branch_or_pr).__name__}")
    
    # 尝试访问工具的description属性来验证文档存在
    if hasattr(fetch_branch_or_pr, 'description'):
        print(f"\nfetch_branch_or_pr工具描述:")
        # 只打印前200个字符以避免过长输出
        print(f"{fetch_branch_or_pr.description[:200]}...")
        print("\n✅ 工具文档存在")
    
    # 测试内部函数的参数验证逻辑（使用模拟参数）
    # 注意：这里不会实际执行Git操作，只是验证参数验证逻辑
    test_dir = os.path.dirname(__file__)
    
    # 测试缺少参数的情况
    result = _fetch_branch_or_pr_internal(project_dir=test_dir)
    print(f"\n测试缺少参数: {result['error']}")
    
    print("\n🎯 测试完成：函数集成验证通过")
    print("\n注意：完整功能测试需要在实际Git仓库中执行，本脚本仅验证代码集成是否正常")
    print("\n使用示例:")
    print("1. 获取分支: fetch_branch_or_pr(project_dir='/path/to/repo', branch_name='feature-branch')")
    print("2. 获取PR: fetch_branch_or_pr(project_dir='/path/to/repo', pr_number=42)")
    
    sys.exit(0)
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 测试过程中出现错误: {e}")
    sys.exit(1)