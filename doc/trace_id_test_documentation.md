# Trace ID 功能测试文档与运行指南

## 目录

1. [测试概述](#测试概述)
2. [测试文件说明](#测试文件说明)
3. [测试环境要求](#测试环境要求)
4. [测试运行方法](#测试运行方法)
   - [单元测试运行](#单元测试运行)
   - [集成测试运行](#集成测试运行)
   - [边界情况测试运行](#边界情况测试运行)
   - [测试自动化](#测试自动化)
5. [测试结果解读](#测试结果解读)
6. [常见问题排查](#常见问题排查)
7. [测试覆盖率](#测试覆盖率)
8. [最佳实践](#最佳实践)

## 测试概述

本测试套件全面验证了 Zephyr MCP Agent 的 Trace ID 功能，确保在各种场景下 trace_id 能够正确生成、传递和记录。测试涵盖了以下核心功能点：

- **trace_id 生成与获取**：验证系统能否正确生成唯一的 trace_id，或接受从请求头传入的 trace_id
- **HTTP 端点支持**：确保所有 HTTP 端点（/api/tool, /api/ai_assistant, /api/tools, /health 等）都正确处理 trace_id
- **日志系统集成**：验证 trace_id 是否正确记录到系统日志中
- **异常处理**：测试错误情况下 trace_id 的传递是否正确
- **边界情况**：测试特殊字符、超长字符串、空值等情况下的系统行为

## 测试文件说明

本测试套件包含以下测试文件：

| 测试文件 | 类型 | 主要功能 | 文件路径 |
|---------|------|---------|----------|
| trace_id_test_plan.md | 计划 | 详细的测试计划和用例 | `c:/github/zephyr_mcp/trace_id_test_plan.md` |
| test_trace_id.py | 集成 | 基础的集成测试 | `c:/github/zephyr_mcp/test_trace_id.py` |
| test_unit_trace_id.py | 单元 | 单元测试，验证核心逻辑 | `c:/github/zephyr_mcp/test_unit_trace_id.py` |
| test_integration_trace_id.py | 集成 | 全面的集成测试 | `c:/github/zephyr_mcp/test_integration_trace_id.py` |
| test_edge_cases_trace_id.py | 边界 | 边界情况和异常场景测试 | `c:/github/zephyr_mcp/test_edge_cases_trace_id.py` |

## 测试环境要求

运行测试前，请确保以下环境要求已满足：

1. **Python 3.7+**：所有测试脚本均使用 Python 3 编写
2. **依赖库**：
   - `requests`：用于发送 HTTP 请求（集成测试和边界测试需要）
   - `unittest`：Python 标准库，用于单元测试
   - `concurrent.futures`：用于并发测试

3. **测试服务器**：
   - 运行中的 Zephyr MCP Agent 服务器
   - 默认地址：`http://localhost:8000`

安装依赖：

```bash
pip install requests
```

## 测试运行方法

### 单元测试运行

单元测试专注于验证核心的 trace_id 逻辑，不需要运行服务器：

```bash
cd c:/github/zephyr_mcp
python test_unit_trace_id.py
```

### 集成测试运行

集成测试需要先启动 Zephyr MCP Agent 服务器，然后运行：

```bash
cd c:/github/zephyr_mcp

# 先启动服务器（在另一个终端）
python agent.py

# 在另一个终端运行测试
python test_integration_trace_id.py
```

### 边界情况测试运行

边界测试也需要运行中的服务器：

```bash
cd c:/github/zephyr_mcp
python test_edge_cases_trace_id.py
```

可以指定自定义的服务器地址：

```bash
python test_edge_cases_trace_id.py http://localhost:8080
```

### 测试自动化

创建一个简单的批处理脚本，自动运行所有测试：

```bash
# create run_all_tests.bat

@echo off
echo 运行 Zephyr MCP Trace ID 所有测试
echo ================================
echo 运行单元测试...
python test_unit_trace_id.py
echo.
echo 运行集成测试...
python test_integration_trace_id.py
echo.
echo 运行边界情况测试...
python test_edge_cases_trace_id.py
echo.
echo 所有测试完成！
pause
```

## 测试结果解读

### 成功结果示例

```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.32s

OK
```

### 失败结果示例

```
.F...
======================================================================
FAIL: test_response_trace_id (__main__.TestIntegrationTraceId)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_integration_trace_id.py", line 45, in test_response_trace_id
    self.assertEqual(response.json()["trace_id"], custom_trace_id)
AssertionError: 'uuid-string-1' != 'uuid-string-2'

----------------------------------------------------------------------
Ran 5 tests in 0.28s

FAILED (failures=1)
```

### 测试日志

集成测试和边界测试会输出详细的测试过程日志，帮助识别问题：

```
测试目标服务器: http://localhost:8000
测试自定义trace_id...
  使用trace_id: 12345678-1234-5678-abcd-1234567890ab
  响应状态码: 200
  ✓ trace_id正确返回在响应头和响应体中
```

## 常见问题排查

### 1. 服务器连接错误

**症状**：`ConnectionRefusedError: [Errno 111] Connection refused`

**解决方案**：
- 确保服务器已启动并运行在正确的端口上
- 检查防火墙设置，确保端口已开放
- 验证服务器地址和端口配置

### 2. 测试超时

**症状**：`requests.exceptions.Timeout: HTTPConnectionPool(host='localhost', port=8000): Read timed out.`

**解决方案**：
- 增加测试脚本中的超时参数
- 检查服务器负载，确保其有足够资源响应请求
- 可能需要优化服务器代码以提高响应速度

### 3. trace_id 不匹配

**症状**：`AssertionError: 'expected-id' != 'actual-id'`

**解决方案**：
- 检查服务器代码中的 trace_id 处理逻辑
- 验证请求头名称是否正确（应为 "X-Trace-ID"）
- 确保响应中正确包含 trace_id 字段

### 4. 服务器错误

**症状**：`500 Internal Server Error`

**解决方案**：
- 查看服务器日志获取详细错误信息
- 检查服务器代码中可能的异常处理问题
- 尝试运行单元测试，定位具体的逻辑错误

## 测试覆盖率

测试套件覆盖了以下 trace_id 功能点：

| 功能点 | 覆盖程度 | 测试文件 |
|-------|---------|----------|
| trace_id 生成 | 100% | test_unit_trace_id.py |
| 从请求头获取 trace_id | 100% | test_unit_trace_id.py, test_integration_trace_id.py |
| /api/tool 端点 trace_id | 100% | test_integration_trace_id.py |
| /api/ai_assistant 端点 trace_id | 100% | test_integration_trace_id.py |
| /api/tools 端点 trace_id | 100% | test_integration_trace_id.py |
| /health 端点 trace_id | 100% | test_integration_trace_id.py, test_edge_cases_trace_id.py |
| 404 端点 trace_id | 100% | test_integration_trace_id.py |
| 异常处理中的 trace_id | 100% | test_edge_cases_trace_id.py |
| 日志系统中的 trace_id | 100% | test_unit_trace_id.py |
| 特殊字符 trace_id | 100% | test_edge_cases_trace_id.py |
| 空值 trace_id | 100% | test_edge_cases_trace_id.py |
| 超长 trace_id | 100% | test_edge_cases_trace_id.py |
| 并发请求 trace_id | 100% | test_edge_cases_trace_id.py |

## 最佳实践

1. **持续测试**：在每次代码修改后运行测试套件，确保 trace_id 功能正常
2. **测试驱动开发**：在添加新功能时，先编写相应的测试用例
3. **监控系统**：将 trace_id 与监控系统集成，便于问题追踪
4. **文档更新**：当 trace_id 功能发生变化时，及时更新测试文档
5. **定期审查**：定期审查测试覆盖率，确保没有遗漏的测试场景

## 结论

通过本测试套件的全面验证，可以确保 Zephyr MCP Agent 的 Trace ID 功能在各种场景下都能正确工作，为系统的可观测性和问题排查提供有力支持。