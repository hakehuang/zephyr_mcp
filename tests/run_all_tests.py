#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zephyr MCP 测试框架 - 主测试入口
统一运行所有整合后的测试文件
"""

import sys
import os
import time
import subprocess
import importlib.util
import platform
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRunner:
    """测试运行器类"""
    
    def __init__(self):
        self.test_modules = [
            'test_trace_id',
            'test_git_tools',
            'test_api', 
            'test_interactive',
            'test_api_integration',
            'test_confirm',
            'test_docs_api',
            'test_edge_cases_trace_id',
            'test_fetch_tool',
            'test_integration_trace_id',
            'test_interactive_demo',
            'test_interactive_features',
            'test_llm_integration',
            'test_multi_language_support',
            'test_rebase_tool',
            'test_refactored_code',
            'test_type_fix',
            'test_unit_trace_id',
            'test_validation'
        ]
        self.test_results = {}
        self.tests_dir = os.path.dirname(os.path.abspath(__file__))
        self.is_windows = platform.system() == "Windows"
        
    def is_windows_os(self) -> bool:
        """检查当前是否为Windows操作系统"""
        return self.is_windows
    
    # WSL路径转换功能已移除，所有平台直接使用系统路径
    
    def print_banner(self):
        """打印测试运行器横幅"""
        banner = [
            "--------------------------------------------",
            "         Zephyr MCP 测试运行器               ",
            "--------------------------------------------",
        ]
        
        print("\n" + "=" * 50)
        for line in banner:
            print(line)
        print("=" * 50)
        print(f"测试目录: {self.tests_dir}")
        print(f"测试模块数量: {len(self.test_modules)}")
        print("=" * 50 + "\n")
    
    def check_test_file_exists(self, module_name: str) -> bool:
        """检查测试文件是否存在"""
        file_path = os.path.join(self.tests_dir, f"{module_name}.py")
        exists = os.path.exists(file_path)
        if exists:
            print(f"[OK] 找到测试文件: {module_name}.py")
        else:
            print(f"[ERROR] 测试文件不存在: {module_name}.py")
        return exists
    
    def run_test_module_as_script(self, module_name: str) -> Dict[str, Any]:
        """以脚本方式运行测试模块"""
        start_time = time.time()
        module_path = os.path.join(self.tests_dir, f"{module_name}.py")
        
        result = {
            'module': module_name,
            'success': False,
            'duration': 0,
            'output': [],
            'error': None
        }
        
        try:
            print(f"\n[RUN] 运行测试模块: {module_name}")
            print("-" * 40)
            
            # 使用subprocess运行测试模块，使用系统区域设置编码
            import locale
            
            # 在所有系统上直接运行测试
            process = subprocess.Popen(
                [sys.executable, module_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8-sig',  # 使用带BOM的UTF-8编码
                errors='replace'  # 替换无法解码的字符
            )
            
            stdout, stderr = process.communicate()
            
            # 输出测试结果
            if stdout:
                for line in stdout.splitlines():
                    print(f"  {line}")
                    result['output'].append(line)
            
            if stderr:
                print(f"\n[ERROR] 错误输出:")
                for line in stderr.splitlines():
                    print(f"  [错误] {line}")
                result['error'] = stderr
            
            # 检查是否成功（基于输出判断）
            success_indicators = ['OK', 'PASSED', 'success', 'successfully', 'completed']
            failure_indicators = ['FAILED', 'ERROR', 'Traceback']
            
            # 首先检查返回码
            result['success'] = process.returncode == 0
            
            # 然后检查输出内容以确保准确性
            stdout_lower = stdout.lower() if stdout else ''
            if any(indicator.lower() in stdout_lower for indicator in failure_indicators):
                result['success'] = False
            elif any(indicator.lower() in stdout_lower for indicator in success_indicators):
                result['success'] = True
            
            if process.returncode == 0 and not result['error']:
                result['success'] = True
                
        except Exception as e:
            print(f"\n[ERROR] 运行测试模块时出错: {e}")
            result['error'] = str(e)
        finally:
            result['duration'] = round(time.time() - start_time, 2)
            
        return result
    
    def run_all_tests(self):
        """运行所有测试模块"""
        self.print_banner()
        start_time = time.time()
        success_count = 0
        failure_count = 0
        
        # 首先检查所有测试文件是否存在
        print("📁 检查测试文件...")
        existing_modules = [module for module in self.test_modules 
                           if self.check_test_file_exists(module)]
        
        print(f"\n📊 将运行 {len(existing_modules)} 个测试模块\n")
        
        # 逐个运行测试模块
        for module_name in existing_modules:
            result = self.run_test_module_as_script(module_name)
            self.test_results[module_name] = result
            
            if result['success']:
                success_count += 1
                print(f"\n[OK] 测试模块 {module_name} 完成! ({result['duration']}s)")
            else:
                failure_count += 1
                print(f"\n[ERROR] 测试模块 {module_name} 失败! ({result['duration']}s)")
            
            print("-" * 40)
        
        # 生成测试报告
        total_time = round(time.time() - start_time, 2)
        self.generate_report(success_count, failure_count, total_time)
        
        return self.test_results
    
    def generate_report(self, success_count: int, failure_count: int, total_time: float):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📋 ZEPHYR MCP 测试报告")
        print("=" * 50)
        print(f"总测试模块: {len(self.test_results)}")
        print(f"通过: {success_count}")
        print(f"失败: {failure_count}")
        print(f"总用时: {total_time} 秒")
        print("=" * 50)
        
        # 显示详细结果
        if failure_count > 0:
            print("\n[ERROR] 失败的测试模块:")
            for module, result in self.test_results.items():
                if not result['success']:
                    error_msg = result.get('error', '未知错误')
                    error_preview = str(error_msg)[:100] if error_msg else '未知错误'
                    print(f"  - {module}: {error_preview}...")
        
        print("\n[OK] 成功的测试模块:")
        for module, result in self.test_results.items():
            if result['success']:
                print(f"  - {module} ({result['duration']}s)")
        
        # 提供运行建议
        print("\n[TIPS] 运行建议:")
        print("1. 单独运行特定测试: python tests/test_module_name.py")
        print("2. 完整运行: python tests/run_all_tests.py")
        print("3. 运行测试时可以使用 -v 参数查看详细输出")
        print("4. 确保系统编码设置正确，避免Unicode编码问题")
        print("\n" + "=" * 50)
    
    def print_usage(self):
        """打印使用说明"""
        print("\n使用方法:")
        print(f"  python {os.path.basename(__file__)} [options]")
        print("\n选项:")
        print("  -h, --help    显示此帮助信息")
        print("  -v, --verbose 显示详细输出")
        print("  --module=NAME 只运行指定的测试模块")
        print("\n示例:")
        print("  python run_all_tests.py")
        print("  python run_all_tests.py --verbose")
        print("  python run_all_tests.py --module=test_trace_id")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Zephyr MCP 测试运行器')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细输出')
    parser.add_argument('--module', help='只运行指定的测试模块')
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.module:
        # 只运行指定模块
        if args.module in runner.test_modules:
            runner.run_test_module_as_script(args.module)
        else:
            print(f"❌ 未知的测试模块: {args.module}")
            print(f"可用模块: {', '.join(runner.test_modules)}")
    else:
        # 运行所有测试
        runner.run_all_tests()


if __name__ == "__main__":
    main()
