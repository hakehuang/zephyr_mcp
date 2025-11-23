# Trace ID 功能测试计划

## 1. 测试目标

验证 Zephyr MCP Agent 中的 trace_id 功能是否正常工作，确保每个请求都包含唯一的 trace_id，并且该 trace_id 在整个请求处理流程中保持一致，同时在日志和响应中正确显示。

## 2. 测试范围

- **trace_id 生成与获取**
- **HTTP 请求处理流程中的 trace_id 传递**
- **日志系统中的 trace_id 记录**
- **HTTP 响应中的 trace_id 包含**
- **异常情况下的 trace_id 处理**
- **各种端点的 trace_id 支持**

## 3. 测试场景

### 3.1 trace_id 生成与获取测试

- **场景 1.1**: 客户端提供 X-Trace-ID 头
  - 验证服务器是否正确使用客户端提供的 trace_id
  - 验证响应中返回的 trace_id 与请求头中的一致

- **场景 1.2**: 客户端未提供 X-Trace-ID 头
  - 验证服务器是否自动生成有效的 UUID 格式的 trace_id
  - 验证生成的 trace_id 长度为 36 字符（标准 UUID 格式）

### 3.2 HTTP 端点测试

- **场景 2.1**: 健康检查端点 (`/health`)
  - 测试 GET 请求是否包含 trace_id
  - 测试响应 JSON 和响应头中是否都包含 trace_id

- **场景 2.2**: 工具列表端点 (`/api/tools`)
  - 测试 GET 请求的 trace_id 处理
  - 验证工具信息响应中包含 trace_id

- **场景 2.3**: AI 助手端点 (`/api/ai_assistant`)
  - 测试 POST 请求的 trace_id 处理
  - 验证聊天响应中包含 trace_id

- **场景 2.4**: 工具调用端点 (`/api/tool`)
  - 测试工具执行请求的 trace_id 处理
  - 验证工具执行结果中包含 trace_id

- **场景 2.5**: 无效端点 (404 响应)
  - 测试对不存在端点的请求是否也包含 trace_id
  - 验证错误响应中包含 trace_id

### 3.3 异常处理测试

- **场景 3.1**: JSON 解析错误
  - 发送格式错误的 JSON 数据
  - 验证错误响应中包含 trace_id

- **场景 3.2**: 工具执行错误
  - 调用不存在的工具
  - 验证错误响应和日志中都包含 trace_id

- **场景 3.3**: 服务器内部错误
  - 模拟服务器内部异常
  - 验证错误响应和日志中都包含 trace_id

### 3.4 日志系统测试

- **场景 4.1**: 正常操作日志
  - 验证正常请求处理的日志中包含 trace_id
  - 验证日志格式正确：`[timestamp] [log_level] [trace_id] message`

- **场景 4.2**: 错误日志
  - 验证错误情况下的日志中包含 trace_id
  - 验证异常堆栈日志中包含 trace_id

## 4. 测试方法

### 4.1 单元测试

- 测试 `uuid` 导入和 trace_id 生成函数
- 测试 HTTP 处理器中的 trace_id 获取逻辑
- 测试响应构造函数中的 trace_id 添加逻辑

### 4.2 集成测试

- 使用 `requests` 库模拟 HTTP 请求
- 发送各种类型的请求（GET/POST）到不同端点
- 验证请求头、响应头和响应体中的 trace_id

### 4.3 日志验证

- 捕获服务器日志输出
- 验证日志中包含预期的 trace_id 格式
- 验证每个请求的日志条目都包含相同的 trace_id

## 5. 测试用例

### 5.1 单元测试用例

1. **test_trace_id_generation()**
   - 验证生成的 trace_id 是有效的 UUID
   - 验证生成的 trace_id 长度正确

2. **test_trace_id_from_header()**
   - 模拟 HTTP 请求头包含 X-Trace-ID
   - 验证正确提取并使用该 trace_id

3. **test_response_trace_id_inclusion()**
   - 验证各种响应类型都包含 trace_id

### 5.2 集成测试用例

1. **test_health_endpoint_trace_id()**
   - 测试 /health 端点的 trace_id 处理

2. **test_tools_endpoint_trace_id()**
   - 测试 /api/tools 端点的 trace_id 处理

3. **test_ai_assistant_trace_id()**
   - 测试 /api/ai_assistant 端点的 trace_id 处理

4. **test_error_response_trace_id()**
   - 测试各种错误场景下的 trace_id 处理

## 6. 测试工具和依赖

- **Python 3.x**
- **requests 库** - 用于发送 HTTP 请求
- **unittest/pytest** - 测试框架
- **uuid 模块** - 用于验证 UUID 格式
- **mock 库** - 用于模拟服务器行为

## 7. 预期结果

- 所有请求都应包含 trace_id（无论是否由客户端提供）
- 响应 JSON 中应包含与请求相同的 trace_id
- 响应头中应包含 X-Trace-ID 字段
- 所有日志条目都应包含 trace_id
- 异常情况下的错误响应也应包含 trace_id

## 8. 测试执行步骤

1. 启动 Zephyr MCP Agent 服务器
2. 运行自动化测试脚本
3. 验证测试结果是否符合预期
4. 检查服务器日志中的 trace_id 格式

## 9. 验收标准

- 所有测试用例通过
- 日志格式符合规范
- 响应中始终包含 trace_id
- 异常处理正确包含 trace_id

## 10. 风险和缓解措施

- **风险**: 日志系统配置可能影响 trace_id 的格式
  **缓解措施**: 测试前确保日志配置正确

- **风险**: 某些错误路径可能未正确传递 trace_id
  **缓解措施**: 全面测试所有错误场景

- **风险**: 第三方依赖可能影响 UUID 生成
  **缓解措施**: 使用标准的 uuid 模块