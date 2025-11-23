# Trace ID Functionality Test Documentation and Running Guide

## Table of Contents

1. [Test Overview](#test-overview)
2. [Test File Description](#test-file-description)
3. [Test Environment Requirements](#test-environment-requirements)
4. [Test Running Methods](#test-running-methods)
   - [Unit Test Execution](#unit-test-execution)
   - [Integration Test Execution](#integration-test-execution)
   - [Edge Case Test Execution](#edge-case-test-execution)
   - [Test Automation](#test-automation)
5. [Test Result Interpretation](#test-result-interpretation)
6. [Common Issue Troubleshooting](#common-issue-troubleshooting)
7. [Test Coverage](#test-coverage)
8. [Best Practices](#best-practices)

## Test Overview

This test suite comprehensively validates the Trace ID functionality of Zephyr MCP Agent, ensuring that trace_id can be correctly generated, passed, and recorded in various scenarios. The tests cover the following core functionality points:

- **trace_id Generation and Retrieval**: Verify whether the system can correctly generate unique trace_id or accept trace_id passed from request headers
- **HTTP Endpoint Support**: Ensure all HTTP endpoints (/api/tool, /api/ai_assistant, /api/tools, /health, etc.) correctly handle trace_id
- **Log System Integration**: Verify whether trace_id is correctly recorded in system logs
- **Exception Handling**: Test whether trace_id is correctly passed in error situations
- **Edge Cases**: Test system behavior with special characters,超长 strings, empty values, etc.

## Test File Description

This test suite contains the following test files:

| Test File | Type | Main Function | File Path |
|---------|------|-------------|----------|
| trace_id_test_plan.md | Plan | Detailed test plan and use cases | `c:/github/zephyr_mcp/trace_id_test_plan.md` |
| test_trace_id.py | Integration | Basic integration tests | `c:/github/zephyr_mcp/test_trace_id.py` |
| test_unit_trace_id.py | Unit | Unit tests to verify core logic | `c:/github/zephyr_mcp/test_unit_trace_id.py` |
| test_integration_trace_id.py | Integration | Comprehensive integration tests | `c:/github/zephyr_mcp/test_integration_trace_id.py` |
| test_edge_cases_trace_id.py | Edge | Edge cases and exception scenario tests | `c:/github/zephyr_mcp/test_edge_cases_trace_id.py` |

## Test Environment Requirements

Before running the tests, please ensure the following environment requirements are met:

1. **Python 3.7+**: All test scripts are written in Python 3
2. **Dependencies**:
   - `requests`: Used for sending HTTP requests (required for integration tests and edge tests)
   - `unittest`: Python standard library for unit testing
   - `concurrent.futures`: Used for concurrent testing

3. **Test Server**:
   - Running Zephyr MCP Agent server
   - Default address: `http://localhost:8000`

Install dependencies:

```bash
pip install requests
```

## Test Running Methods

### Unit Test Execution

Unit tests focus on verifying core trace_id logic and do not require running the server:

```bash
cd c:/github/zephyr_mcp
python test_unit_trace_id.py
```

### Integration Test Execution

Integration tests require starting the Zephyr MCP Agent server first, then running:

```bash
cd c:/github/zephyr_mcp

# First start the server (in another terminal)
python agent.py

# Run the tests in another terminal
python test_integration_trace_id.py
```

### Edge Case Test Execution

Edge tests also require a running server:

```bash
cd c:/github/zephyr_mcp
python test_edge_cases_trace_id.py
```

You can specify a custom server address:

```bash
python test_edge_cases_trace_id.py http://localhost:8080
```

### Test Automation

Create a simple batch script to automatically run all tests:

```bash
# create run_all_tests.bat

@echo off
echo Running Zephyr MCP Trace ID All Tests
echo ================================
echo Running unit tests...
python test_unit_trace_id.py
echo.
echo Running integration tests...
python test_integration_trace_id.py
echo.
echo Running edge case tests...
python test_edge_cases_trace_id.py
echo.
echo All tests completed!
pause
```

## Test Result Interpretation

### Successful Result Example

```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.32s

OK
```

### Failed Result Example

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

### Test Logs

Integration tests and edge tests will output detailed test process logs to help identify issues:

```
Test target server: http://localhost:8000
Testing custom trace_id...
  Using trace_id: 12345678-1234-5678-abcd-1234567890ab
  Response status code: 200
  ✓ trace_id correctly returned in response header and response body
```

## Common Issue Troubleshooting

### 1. Server Connection Error

**Symptom**: `ConnectionRefusedError: [Errno 111] Connection refused`

**Solutions**:
- Ensure the server is started and running on the correct port
- Check firewall settings to ensure the port is open
- Verify server address and port configuration

### 2. Test Timeout

**Symptom**: `requests.exceptions.Timeout: HTTPConnectionPool(host='localhost', port=8000): Read timed out.`

**Solutions**:
- Increase the timeout parameter in test scripts
- Check server load to ensure it has enough resources to respond to requests
- May need to optimize server code to improve response speed

### 3. trace_id Mismatch

**Symptom**: `AssertionError: 'expected-id' != 'actual-id'`

**Solutions**:
- Check the trace_id handling logic in server code
- Verify the request header name is correct (should be "X-Trace-ID")
- Ensure the response correctly includes the trace_id field

### 4. Server Error

**Symptom**: `500 Internal Server Error`

**Solutions**:
- Check server logs for detailed error information
- Check for possible exception handling issues in server code
- Try running unit tests to locate specific logic errors

## Test Coverage

The test suite covers the following trace_id functionality points:

| Functionality Point | Coverage | Test File |
|-------------------|---------|----------|
| trace_id generation | 100% | test_unit_trace_id.py |
| Getting trace_id from request header | 100% | test_unit_trace_id.py, test_integration_trace_id.py |
| /api/tool endpoint trace_id | 100% | test_integration_trace_id.py |
| /api/ai_assistant endpoint trace_id | 100% | test_integration_trace_id.py |
| /api/tools endpoint trace_id | 100% | test_integration_trace_id.py |
| /health endpoint trace_id | 100% | test_integration_trace_id.py, test_edge_cases_trace_id.py |
| 404 endpoint trace_id | 100% | test_integration_trace_id.py |
| trace_id in exception handling | 100% | test_edge_cases_trace_id.py |
| trace_id in log system | 100% | test_unit_trace_id.py |
| Special character trace_id | 100% | test_edge_cases_trace_id.py |
| Empty value trace_id | 100% | test_edge_cases_trace_id.py |
| Very long trace_id | 100% | test_edge_cases_trace_id.py |
| Concurrent request trace_id | 100% | test_edge_cases_trace_id.py |

## Best Practices

1. **Continuous Testing**: Run the test suite after each code modification to ensure trace_id functionality is normal
2. **Test-Driven Development**: Write corresponding test cases before adding new functionality
3. **Monitoring System**: Integrate trace_id with monitoring systems for easier issue tracking
4. **Documentation Updates**: Update test documentation in a timely manner when trace_id functionality changes
5. **Regular Review**: Regularly review test coverage to ensure no test scenarios are missed

## Conclusion

Through comprehensive validation by this test suite, we can ensure that the Trace ID functionality of Zephyr MCP Agent works correctly in various scenarios, providing strong support for system observability and troubleshooting.