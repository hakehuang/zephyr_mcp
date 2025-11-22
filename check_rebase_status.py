#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查zephyr项目中rebase的最终状态并提供处理选项
"""

import subprocess
import os
import sys

ZEPHYR_PROJECT_DIR = "c:/zephyr_project/zephyr"

def run_git_command(command, get_output=True):
    """运行git命令并返回输出"""
    try:
        print(f"执行: {command}")
        result = subprocess.run(command, cwd=ZEPHYR_PROJECT_DIR, 
                               capture_output=True, text=True, shell=True)
        if get_output:
            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "error": result.stderr.strip()
            }
        else:
            return result.returncode == 0
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }

def main():
    print("检查zephyr项目的rebase最终状态...")
    
    # 检查当前状态
    print("\n--- 当前Git状态 ---")
    status = run_git_command("git status")
    if status["success"]:
        print(status["output"])
        # 检查是否仍在rebase中
        is_rebasing = "rebase in progress" in status["output"].lower()
    else:
        print(f"获取状态失败: {status['error']}")
        is_rebasing = False
    
    # 检查分支信息
    print("\n--- 当前分支信息 ---")
    branch = run_git_command("git branch --show-current")
    if branch["success"]:
        print(f"当前分支: {branch['output']}")
    
    # 检查是否仍有冲突
    print("\n--- 冲突检查 ---")
    conflicts = run_git_command("git diff --name-only --diff-filter=U")
    if conflicts["success"]:
        if conflicts["output"]:
            print("仍然存在以下冲突文件:")
            for file in conflicts["output"].splitlines():
                print(f"  - {file}")
        else:
            print("当前没有检测到冲突文件")
    
    # 检查rebase合并编辑器是否在等待输入
    # 这通常意味着需要编辑提交信息
    print("\n--- 检查是否等待提交信息编辑 ---")
    rebase_merge_dir = os.path.join(ZEPHYR_PROJECT_DIR, ".git", "rebase-merge")
    if os.path.exists(rebase_merge_dir):
        print("检测到rebase-merge目录，可能在等待编辑提交信息")
        
        # 检查提交信息文件
        msg_file = os.path.join(rebase_merge_dir, "git-rebase-todo")
        if os.path.exists(msg_file):
            print(f"找到git-rebase-todo文件: {msg_file}")
            print("可以查看该文件了解当前rebase进度")
    
    # 提供操作选项
    print("\n--- 建议操作 ---")
    if is_rebasing:
        print("1. 如果rebase在等待编辑提交信息，请手动编辑")
        print("2. 如果有新的冲突，需要继续解决")
        print("3. 或者取消整个rebase操作")
        
        print("\n是否要取消rebase操作？(y/N)")
        try:
            # 在自动化环境中，我们默认不取消
            # 用户可以手动执行取消命令
            print("为安全起见，脚本不会自动取消rebase")
            print("如果需要取消，请手动运行:")
            print(f"cd {ZEPHYR_PROJECT_DIR}")
            print("git rebase --abort")
        except:
            pass
    else:
        print("✅ Rebase操作似乎已经完成或未在进行中")
        
    # 显示当前提交历史
    print("\n--- 最近提交历史 ---")
    log = run_git_command("git log --oneline -5")
    if log["success"]:
        print(log["output"])
    
    print("\n--- 操作完成 ---")
    print("rebase状态检查完成")

if __name__ == "__main__":
    main()