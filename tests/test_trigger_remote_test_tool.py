#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trigger remote test tool smoke test.

This repo's test harness is script-based (not pytest).
This file prints a success indicator so it can be picked up by tests/run_all_tests.py.
"""

import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests():
    print("Trigger remote test tool test running...")

    from src.tools.trigger_remote_test import trigger_remote_test

    result = trigger_remote_test()
    assert isinstance(result, dict)
    assert result.get("status") == "success"
    assert "prompt" in result and isinstance(result["prompt"], str)
    assert "trigger_build" in result["prompt"]
    assert "zephyr_test_pipe_quick" in result["prompt"]
    assert "instructions" in result and isinstance(result["instructions"], list)

    # Override job name
    result2 = trigger_remote_test(jobFullName="my_job")
    assert "my_job" in result2["prompt"]

    print("OK - trigger_remote_test tool tests passed")
    print("success")
    return True


if __name__ == "__main__":
    run_all_tests()
    sys.exit(0)
