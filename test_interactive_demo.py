#!/usr/bin/env python3
"""
Demo script showing how to use the enhanced interactive features
演示脚本展示如何使用增强的交互功能
"""

import sys
import os

def demo_validation_workflow():
    """Demonstrate the validation workflow"""
    print("=== Zephyr MCP 交互功能演示 ===")
    print()
    
    print("1. 参数验证功能演示")
    print("-" * 30)
    print("当您调用 validate_west_init_params() 时，系统会:")
    print("✓ 检查缺失的必需参数")
    print("✓ 验证URL格式")
    print("✓ 提供分支名称建议")
    print("✓ 检查目录状态")
    print("✓ 给出具体的建议")
    print()
    
    print("示例输出 (空参数):")
    print("{")
    print('    "status": "missing_params",')
    print('    "missing_params": ["repo_url", "branch", "project_dir"],')
    print('    "warnings": [],')
    print('    "suggestions": [')
    print('        "repo_url: 使用 Zephyr 官方仓库 https://github.com/zephyrproject-rtos/zephyr",')
    print('        "branch: 常用分支有 \'main\', \'master\', \'v3.5-branch\' 等",')
    print('        "project_dir: 建议使用空目录，例如: c:/temp/zephyr-project"')
    print('    ]')
    print("}")
    print()
    
    print("2. 交互模式功能演示")
    print("-" * 30)
    print("当您调用 west_init_interactive() 时，系统会:")
    print("✓ 自动提示缺失的参数")
    print("✓ 显示配置摘要")
    print("✓ 要求用户确认")
    print("✓ 提供友好的错误消息")
    print("✓ 允许用户随时取消")
    print()
    
    print("交互流程示例:")
    print("1. 系统: '请输入Git仓库地址 (或按Enter使用默认值):'")
    print("   用户: 'https://github.com/zephyrproject-rtos/zephyr.git'")
    print()
    print("2. 系统: '请输入分支名称:'")
    print("   用户: 'main'")
    print()
    print("3. 系统: '请输入项目目录:'")
    print("   用户: 'c:/temp/zephyr-project'")
    print()
    print("4. 系统显示配置摘要并要求确认")
    print("5. 用户确认后执行 west init 命令")
    print()
    
    print("3. 完整工作流程演示")
    print("-" * 30)
    print("推荐的使用流程:")
    print()
    print("步骤1: 验证参数")
    print("   validation = validate_west_init_params()")
    print("   if validation['status'] == 'valid':")
    print("       # 参数有效，直接执行")
    print("   else:")
    print("       # 显示缺失参数和警告")
    print("       print(validation['missing_params'])")
    print("       print(validation['suggestions'])")
    print()
    
    print("步骤2: 使用交互模式")
    print("   result = west_init_interactive(")
    print("       require_confirmation=True,")
    print("       auto_prompt=True")
    print("   )")
    print()
    
    print("步骤3: 处理结果")
    print("   if result['status'] == 'success':")
    print("       print('初始化成功!')")
    print("   else:")
    print("       print(f'错误: {result[\"error\"]}')")
    print("       print(f'建议: {result.get(\"suggestions\", [])}')")
    print()

def demo_usage_examples():
    """Show usage examples"""
    print("4. 使用示例")
    print("-" * 30)
    print()
    
    print("示例1: 完全交互模式")
    print("```python")
    print("# 用户将被提示输入所有必需参数")
    print("result = west_init_interactive()")
    print("```")
    print()
    
    print("示例2: 部分参数 + 交互")
    print("```python")
    print("# 提供部分参数，系统会提示缺失的参数")
    print("result = west_init_interactive(")
    print("    repo_url='https://github.com/zephyrproject-rtos/zephyr.git'")
    print("    # branch 和 project_dir 将被提示")
    print(")")
    print("```")
    print()
    
    print("示例3: 禁用确认（自动化脚本）")
    print("```python")
    print("# 自动化环境中禁用确认")
    print("result = west_init_interactive(")
    print("    repo_url='https://github.com/zephyrproject-rtos/zephyr.git',")
    print("    branch='main',")
    print("    project_dir='c:/temp/zephyr-project',")
    print("    require_confirmation=False")
    print(")")
    print("```")
    print()
    
    print("示例4: 参数验证 + 交互")
    print("```python")
    print("# 先验证参数，再决定是否需要交互")
    print("validation = validate_west_init_params()")
    print("if validation['status'] != 'valid':")
    print("    print('发现以下问题:')")
    print("    for warning in validation['warnings']:")
    print("        print(f'⚠️  {warning}')")
    print("    for suggestion in validation['suggestions']:")
    print("        print(f'💡 {suggestion}')")
    print("    ")
    print("    # 使用交互模式获取用户输入")
    print("    result = west_init_interactive(")
    print("        require_confirmation=True,")
    print("        auto_prompt=True")
    print("    )")
    print("```")
    print()

def demo_error_handling():
    """Show error handling examples"""
    print("5. 错误处理演示")
    print("-" * 30)
    print()
    
    print("系统提供友好的错误处理:")
    print("✓ 缺失工具检测")
    print("✓ 参数验证错误")
    print("✓ 认证失败处理")
    print("✓ 连接问题处理")
    print("✓ 权限错误处理")
    print()
    
    print("错误响应格式:")
    print("{")
    print('    "status": "error",')
    print('    "log": "详细的执行日志",')
    print('    "error": "用户友好的错误消息",')
    print('    "suggestions": ["建议1", "建议2"]')
    print("}")
    print()

def main():
    """Main demo function"""
    try:
        demo_validation_workflow()
        demo_usage_examples()
        demo_error_handling()
        
        print("=" * 50)
        print("演示完成！")
        print()
        print("主要优势:")
        print("🎯 用户友好的参数提示")
        print("🎯 智能的参数验证")
        print("🎯 清晰的确认机制")
        print("🎯 详细的错误消息")
        print("🎯 灵活的使用方式")
        print()
        print("现在您可以在自己的代码中使用这些功能了！")
        
    except KeyboardInterrupt:
        print("\n演示被中断")
    except Exception as e:
        print(f"演示过程中发生错误: {e}")

if __name__ == "__main__":
    main()