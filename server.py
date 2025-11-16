from fastmcp import FastMCP
import requests
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

mcp = FastMCP(name="VSCode-Tools")

# 数学工具
@mcp.tool
def add(a: int, b: int) -> int:
    """计算两数之和"""
    return a + b

@mcp.tool
def multiply(a: float, b: float) -> float:
    """计算两数乘积"""
    return a * b

if __name__ == "__main__":
    # 本地调试用 stdio 模式
    # mcp.run(transport="stdio")
    
    # 远程调用用 HTTP 模式    
    mcp.run(transport="http", port=5002)
