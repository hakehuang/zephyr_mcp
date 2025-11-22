#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查zephyr项目中rebase冲突状态并提供解决指南
"""

import subprocess
import os

ZEPHYR_PROJECT_DIR = "c:/zephyr_project/zephyr"

def run_git_command(command):
    """运行git命令并返回输出"""
    try:
        result = subprocess.run(command, cwd=ZEPHYR_PROJECT_DIR, 
                               capture_output=True, text=True, shell=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip(),
            "exit_code": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "exit_code": -1
        }

def main():
    print("检查rebase冲突状态...")
    print(f"项目目录: {ZEPHYR_PROJECT_DIR}")
    
    # 检查当前状态
    print("\n--- 当前Git状态 ---")
    status = run_git_command("git status")
    if status["success"]:
        print(status["output"])
    else:
        print(f"获取状态失败: {status['error']}")
    
    # 检查冲突文件
    print("\n--- 冲突文件列表 ---")
    conflicts = run_git_command("git diff --name-only --diff-filter=U")
    if conflicts["success"]:
        if conflicts["output"]:
            print("以下文件存在冲突:")
            for file in conflicts["output"].splitlines():
                print(f"  - {file}")
                
                # 显示冲突标记
                print(f"  冲突内容预览:")
                cat_result = run_git_command(f"git show :1:{file} | head -n 20")
                if cat_result["success"]:
                    print("  <<<<<<< YOURS:")
                    print(cat_result["output"])
                
                cat_result = run_git_command(f"git show :3:{file} | head -n 20")
                if cat_result["success"]:
                    print("  >>>>>>> THEIRS:")
                    print(cat_result["output"])
        else:
            print("没有检测到冲突文件")
    else:
        print(f"检查冲突失败: {conflicts['error']}")
    
    print("\n--- Rebase冲突解决指南 ---")
    print("1. 手动编辑冲突文件，解决所有冲突")
    print("2. 解决后标记文件为已解决: git add <冲突文件>")
    print("3. 继续rebase: git rebase --continue")
    print("4. 或者取消rebase: git rebase --abort")
    print("5. 或者跳过当前提交: git rebase --skip")
    
    # 提供自动解决建议（使用--theirs或--ours）
    print("\n--- 快速解决选项 ---")
    print("如果你想接受main分支(上游)的修改:")
    print(f"  cd {ZEPHYR_PROJECT_DIR}")
    print("  git checkout --theirs <冲突文件>")
    print("  git add <冲突文件>")
    print("  git rebase --continue")
    
    print("\n如果你想保留你的分支(pull)的修改:")
    print(f"  cd {ZEPHYR_PROJECT_DIR}")
    print("  git checkout --ours <冲突文件>")
    print("  git add <冲突文件>")
    print("  git rebase --continue")

if __name__ == "__main__":
    main()