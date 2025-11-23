#!/usr/bin/env python3
"""
测试类型修复的脚本
"""

# 直接导入函数进行类型测试
def test_type_compatibility():
    """测试类型兼容性"""
    print("测试类型修复...")
    
    # 测试1: 验证函数签名
    from src.mcp_server import west_init_interactive, _west_init_core
    import inspect
    
    print("1. 检查 west_init_interactive 函数签名:")
    sig = inspect.signature(west_init_interactive)
    for name, param in sig.parameters.items():
        if name in ['repo_url', 'branch', 'project_dir', 'username', 'token', 'auth_method']:
            print(f"   {name}: {param.annotation}")
    
    print("\n2. 检查 _west_init_core 函数签名:")
    sig = inspect.signature(_west_init_core)
    for name, param in sig.parameters.items():
        if name in ['repo_url', 'branch', 'project_dir', 'username', 'token', 'auth_method']:
            print(f"   {name}: {param.annotation}")
    
    print("\n3. 测试 None 参数处理:")
    try:
        # 测试 None 参数 - 应该能正常处理，不会抛出类型错误
        result = west_init_interactive(
            repo_url="https://github.com/zephyrproject-rtos/zephyr.git",
            branch="main", 
            project_dir="c:/temp/test-zephyr",
            username=None,  # 这应该是允许的
            token=None,
            auth_method=None,  # 这应该是允许的
            require_confirmation=False,  # 禁用确认以便测试
            auto_prompt=False  # 禁用自动提示以便测试
        )
        print("   ✓ None 参数测试通过")
        print(f"   返回结果状态: {result.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"   ✗ None 参数测试失败: {e}")
    
    print("\n4. 测试默认值处理:")
    try:
        # 测试默认值 - 应该使用默认值 "env"
        result = west_init_interactive(
            repo_url="https://github.com/zephyrproject-rtos/zephyr.git",
            branch="main", 
            project_dir="c:/temp/test-zephyr2",
            require_confirmation=False,
            auto_prompt=False
        )
        print("   ✓ 默认值测试通过")
        print(f"   返回结果状态: {result.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"   ✗ 默认值测试失败: {e}")
    
    print("\n✅ 类型兼容性测试完成")

if __name__ == "__main__":
    test_type_compatibility()