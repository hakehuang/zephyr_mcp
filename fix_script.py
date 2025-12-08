import os

# 读取文件内容
with open("tests/run_all_tests.py", "r", encoding="utf-8") as f:
    content = f.read()

# 修复1: NoneType错误 - 在调用lower()前检查stdout是否为None
content = content.replace("stdout_lower = stdout.lower()", "stdout_lower = stdout.lower() if stdout else ")

# 修复2: Unicode解码错误 - 使用utf-8编码
content = content.replace("encoding=locale.getpreferredencoding(False)", "encoding=utf-8")

# 保存修复后的内容
with open("tests/run_all_tests.py", "w", encoding="utf-8") as f:
    f.write(content)

print("修复完成！")
