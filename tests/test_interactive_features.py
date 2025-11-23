#!/usr/bin/env python3
"""
Test script for interactive features in Zephyr MCP Server
测试Zephyr MCP服务器交互功能的脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the raw functions from the module, not the MCP-wrapped versions
import mcp_server
from mcp_server import validate_west_init_params as raw_validate_west_init_params
from mcp_server import west_init_interactive as raw_west_init_interactive

def test_parameter_validation():
    """Test parameter validation function"""
    print("=== 测试参数验证功能 ===")
    
    # Test 1: Empty parameters
    print("\n1. 测试空参数:")
    result = raw_validate_west_init_params()
    print(f"状态: {result['status']}")
    print(f"缺失参数: {result['missing_params']}")
    print(f"警告: {result['warnings']}")
    print(f"建议: {result['suggestions']}")
    
    # Test 2: Partial parameters
    print("\n2. 测试部分参数:")
    result = raw_validate_west_init_params(
        repo_url="https://github.com/zephyrproject-rtos/zephyr.git"
    )
    print(f"状态: {result['status']}")
    print(f"缺失参数: {result['missing_params']}")
    print(f"警告: {result['warnings']}")
    
    # Test 3: Invalid URL
    print("\n3. 测试无效URL:")
    result = raw_validate_west_init_params(
        repo_url="invalid-url",
        branch="main",
        project_dir="/tmp/test"
    )
    print(f"状态: {result['status']}")
    print(f"警告: {result['warnings']}")
    print(f"建议: {result['suggestions']}")
    
    # Test 4: Valid parameters
    print("\n4. 测试有效参数:")
    result = raw_validate_west_init_params(
        repo_url="https://github.com/zephyrproject-rtos/zephyr.git",
        branch="main",
        project_dir="c:/temp/zephyr-test"
    )
    print(f"状态: {result['status']}")
    print(f"警告: {result['warnings']}")
    print(f"建议: {result['suggestions']}")

def test_interactive_mode():
    """Test interactive mode (requires user input)"""
    print("\n=== 测试交互模式 ===")
    print("注意: 以下测试需要用户输入")
    
    # Test 1: Interactive with confirmation
    print("\n1. 测试交互模式（带确认）:")
    print("这将提示您输入参数并要求确认")
    try:
        result = raw_west_init_interactive(
            require_confirmation=True,
            auto_prompt=True
        )
        print(f"结果状态: {result.get('status', 'unknown')}")
        if result.get('error'):
            print(f"错误: {result['error']}")
        if result.get('log'):
            print(f"日志: {result['log']}")
    except KeyboardInterrupt:
        print("用户取消了操作")
    except Exception as e:
        print(f"执行错误: {e}")

def test_validation_workflow():
    """Test complete validation workflow"""
    print("\n=== 测试完整验证工作流程 ===")
    
    # Step 1: Validate parameters
    print("\n步骤1: 验证参数")
    validation = raw_validate_west_init_params()
    
    if validation["status"] in ["missing_params", "warnings"]:
        print("参数验证结果:")
        print(f"状态: {validation['status']}")
        print(f"缺失参数: {validation['missing_params']}")
        print(f"警告: {validation['warnings']}")
        print(f"建议: {validation['suggestions']}")
        
        # Step 2: Use interactive mode to fill missing parameters
        print("\n步骤2: 使用交互模式填充缺失参数")
        print("您可以使用交互模式来填充这些缺失的参数")
        print("示例: west_init_interactive(require_confirmation=True, auto_prompt=True)")
    else:
        print("所有参数验证通过！")

def main():
    """Main test function"""
    print("Zephyr MCP服务器交互功能测试")
    print("=" * 50)
    
    try:
        # Test parameter validation (no user input required)
        test_parameter_validation()
        
        # Test validation workflow
        test_validation_workflow()
        
        # Ask user if they want to test interactive mode
        print("\n" + "=" * 50)
        response = input("是否要继续测试交互模式？(需要用户输入) [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            test_interactive_mode()
        else:
            print("跳过交互模式测试")
        
        print("\n=== 测试完成 ===")
        print("\n使用建议:")
        print("1. 在实际使用中，先调用 validate_west_init_params() 验证参数")
        print("2. 根据验证结果，决定是否需要使用交互模式")
        print("3. 使用 west_init_interactive() 获取用户输入和确认")
        print("4. 查看返回的状态和错误信息进行调试")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()