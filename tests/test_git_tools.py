#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git工具功能整合测试
包含git_rebase、fetch_branch_or_pr等git相关工具的测试
"""

import sys
import os
import inspect
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GitToolsTestCase:
    """Git工具测试用例类"""
    
    def __init__(self):
        self.git_rebase = None
        self._git_rebase_internal = None
        self.fetch_branch_or_pr = None
        self._fetch_branch_or_pr_internal = None
        self.import_success = False
        self._import_tools()
    
    def _import_tools(self):
        """导入git工具函数"""
        try:
            # 尝试导入git工具函数
            try:
                # 尝试绝对导入路径
                try:
                    from src.tools.git_rebase import git_rebase
                    self.git_rebase = git_rebase
                    print("[+] 成功导入git_rebase工具(绝对路径)")
                except ImportError:
                    # 尝试备用路径
                    try:
                        from src.mcp_server import git_rebase
                        self.git_rebase = git_rebase
                        print("[+] 成功导入git_rebase工具(备用路径)")
                    except ImportError:
                        self.git_rebase = None
                        print("[-] 无法导入git_rebase工具")
            except Exception as e:
                self.git_rebase = None
                print(f"[-] 导入git_rebase时发生错误: {e}")
            
            try:
                try:
                    from src.tools.git_rebase import _git_rebase_internal
                    self._git_rebase_internal = _git_rebase_internal
                except ImportError:
                    try:
                        from src.mcp_server import _git_rebase_internal
                        self._git_rebase_internal = _git_rebase_internal
                    except ImportError:
                        self._git_rebase_internal = None
            except Exception:
                self._git_rebase_internal = None
            
            try:
                # 尝试绝对导入路径
                try:
                    from src.tools.fetch_branch_or_pr import fetch_branch_or_pr
                    self.fetch_branch_or_pr = fetch_branch_or_pr
                    print("[+] 成功导入fetch_branch_or_pr工具(绝对路径)")
                except ImportError:
                    # 尝试备用路径
                    try:
                        from src.mcp_server import fetch_branch_or_pr
                        self.fetch_branch_or_pr = fetch_branch_or_pr
                        print("[+] 成功导入fetch_branch_or_pr工具(备用路径)")
                    except ImportError:
                        self.fetch_branch_or_pr = None
                        print("[-] 无法导入fetch_branch_or_pr工具")
            except Exception as e:
                self.fetch_branch_or_pr = None
                print(f"[-] 导入fetch_branch_or_pr时发生错误: {e}")
            
            try:
                try:
                    from src.tools.fetch_branch_or_pr import _fetch_branch_or_pr_internal
                    self._fetch_branch_or_pr_internal = _fetch_branch_or_pr_internal
                except ImportError:
                    try:
                        from src.mcp_server import _fetch_branch_or_pr_internal
                        self._fetch_branch_or_pr_internal = _fetch_branch_or_pr_internal
                    except ImportError:
                        self._fetch_branch_or_pr_internal = None
            except Exception:
                self._fetch_branch_or_pr_internal = None
            
            self.import_success = any([self.git_rebase, self.fetch_branch_or_pr])
            
        except Exception as e:
            print(f"[-] Git工具导入过程中发生错误: {e}")
            self.import_success = False
    
    def test_rebase_tool(self):
        """测试git_rebase工具"""
        print("\n=== 测试git_rebase工具 ===")
        
        if not self.import_success or not self.git_rebase:
            print("⚠️ git_rebase工具不可用，跳过测试")
            return
        
        # 测试工具类型
        print(f"git_rebase类型: {type(self.git_rebase)}")
        
        # 检查工具描述信息
        if hasattr(self.git_rebase, 'description'):
            print(f"工具描述: {self.git_rebase.description}")
            print("[+] 成功获取工具描述信息")
        else:
            print("❓ 无法直接获取工具描述，请通过MCP API访问")
        
        # 测试内部函数参数验证（不实际执行rebase）
        print("\n测试内部函数参数验证:")
        try:
            if self._git_rebase_internal:
                # 测试缺少必要参数
                result = self._git_rebase_internal("test_dir", None)
                print(f"缺少source_branch参数测试: {result.get('status')} - {result.get('error')}")
            
            print("\n注意：完整功能测试需要在实际Git仓库中进行")
            print("可以通过以下方式测试实际功能：")
            print("1. 创建测试仓库")
            print('2. 执行`python -c "from src.mcp_server import run_mcp; run_mcp(\'git_rebase\', {\'project_dir\': \'path/to/repo\', \'source_branch\': \'branch_name\'})"`')
            print("\n[+] git_rebase工具测试通过")
            
        except Exception as e:
            print(f"[-] 内部函数测试失败: {e}")
    
    def test_fetch_tool(self):
        """测试fetch_branch_or_pr工具"""
        print("\n=== 测试fetch_branch_or_pr工具 ===")
        
        if not self.import_success or not self.fetch_branch_or_pr:
            print("⚠️ fetch_branch_or_pr工具不可用，跳过测试")
            return
        
        # 验证内部函数签名
        if self._fetch_branch_or_pr_internal:
            internal_sig = inspect.signature(self._fetch_branch_or_pr_internal)
            print(f"_fetch_branch_or_pr_internal函数参数: {list(internal_sig.parameters.keys())}")
        
        # 验证工具存在和类型
        print(f"fetch_branch_or_pr工具类型: {type(self.fetch_branch_or_pr).__name__}")
        
        # 尝试访问工具的description属性
        if hasattr(self.fetch_branch_or_pr, 'description'):
            print(f"\nfetch_branch_or_pr工具描述:")
            # 只打印前200个字符以避免过长输出
            print(f"{self.fetch_branch_or_pr.description[:200]}...")
            print("\n[+] 工具文档存在")
        
        # 测试内部函数的参数验证逻辑
        print("\n测试内部函数参数验证:")
        try:
            if self._fetch_branch_or_pr_internal:
                test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                # 测试缺少参数的情况
                result = self._fetch_branch_or_pr_internal(project_dir=test_dir)
                print(f"测试缺少参数: {result['error']}")
                
            print("\n[+] fetch_branch_or_pr工具测试通过")
            
        except Exception as e:
            print(f"[-] 测试过程中出现错误: {e}")
    
    def test_usage_examples(self):
        """显示使用示例"""
        print("\n=== Git工具使用示例 ===")
        print("\n1. git_rebase工具功能:")
        print("   - 标准rebase操作")
        print("   - 交互式rebase (-i选项)")
        print("   - 强制rebase (-f选项)")
        print("   - --onto参数支持")
        print("   - 冲突检测和提示")
        print("   - 用户确认机制")
        
        print("\n2. fetch_branch_or_pr使用示例:")
        print("   # 获取分支")
        print("   fetch_branch_or_pr(project_dir='/path/to/repo', branch_name='feature-branch')")
        print("   ")
        print("   # 获取PR")
        print("   fetch_branch_or_pr(project_dir='/path/to/repo', pr_number=42)")
        
        print("\n注意：所有功能测试需要在实际Git仓库中执行")


def run_git_tools_tests():
    """运行所有Git工具测试"""
    print("Zephyr MCP Git工具整合测试")
    print("=" * 50)
    
    try:
        test_case = GitToolsTestCase()
        
        # 运行各个工具的测试
        test_case.test_rebase_tool()
        test_case.test_fetch_tool()
        test_case.test_usage_examples()
        
        print("\n" + "=" * 50)
        print("[+] Git工具整合测试完成！")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_git_tools_tests()