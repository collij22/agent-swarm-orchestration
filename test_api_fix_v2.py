#!/usr/bin/env python3
"""
Updated test to verify all API mode fixes including authentication handling
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Add lib to path
sys.path.append(str(Path(__file__).parent / "lib"))

def test_invalid_key_format():
    """Test that invalid key format is rejected immediately"""
    print("Test 1: Invalid key format (should reject immediately)")
    
    # Clear environment
    os.environ.pop('ANTHROPIC_API_KEY', None)
    os.environ.pop('MOCK_MODE', None)
    
    # Set invalid format key
    os.environ['ANTHROPIC_API_KEY'] = 'test-invalid-key'
    
    # Import after environment setup
    from lib.agent_runtime import AnthropicAgentRunner, AgentContext
    from lib.agent_logger import get_logger
    
    logger = get_logger()
    runtime = AnthropicAgentRunner(logger=logger)
    
    context = AgentContext(
        project_requirements={'test': 'test'},
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase='test'
    )
    
    start = time.time()
    success, result, _ = asyncio.run(runtime.run_agent_async('test-agent', 'Test prompt', context))
    duration = time.time() - start
    
    print(f"  Success: {success}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Result: {result[:80] if result else None}...")
    
    assert not success, "Should have failed with invalid key format"
    assert duration < 2, "Should fail immediately without retries"
    assert "ANTHROPIC_API_KEY" in result, "Should mention missing API key"
    print("  ✓ Test passed - invalid key format rejected immediately\n")

def test_valid_format_invalid_key():
    """Test that valid format but invalid key fails quickly with 401"""
    print("Test 2: Valid format but invalid key (should fail quickly with 401)")
    
    # Set valid format but invalid key
    os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-invalid-test-key-123456789'
    os.environ.pop('MOCK_MODE', None)
    
    # Import after environment setup
    from lib.agent_runtime import AnthropicAgentRunner, AgentContext
    from lib.agent_logger import get_logger
    
    logger = get_logger()
    runtime = AnthropicAgentRunner(logger=logger)
    
    context = AgentContext(
        project_requirements={'test': 'test'},
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase='test'
    )
    
    start = time.time()
    success, result, _ = asyncio.run(runtime.run_agent_async('test-agent', 'Test prompt', context))
    duration = time.time() - start
    
    print(f"  Success: {success}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Result: {result[:80] if result else None}...")
    
    assert not success, "Should have failed with 401"
    assert duration < 10, "Should fail quickly without multiple retries"
    assert "401" in result or "authentication" in result.lower(), "Should mention authentication error"
    print("  ✓ Test passed - authentication error handled correctly\n")

def test_mock_mode_still_works():
    """Test that mock mode continues to work"""
    print("Test 3: Mock mode (should work without API key)")
    
    # Set mock mode
    os.environ['MOCK_MODE'] = 'true'
    os.environ.pop('ANTHROPIC_API_KEY', None)
    
    # Import after environment setup
    from lib.mock_anthropic_enhanced import MockAnthropicEnhancedRunner
    from lib.agent_logger import get_logger
    from lib.agent_runtime import AgentContext
    
    logger = get_logger()
    runtime = MockAnthropicEnhancedRunner(logger)
    
    context = AgentContext(
        project_requirements={'test': 'test'},
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase='test'
    )
    
    start = time.time()
    success, result, _ = asyncio.run(runtime.run_agent_async('test-agent', 'Test prompt', context))
    duration = time.time() - start
    
    print(f"  Success: {success}")
    print(f"  Duration: {duration:.2f}s")
    
    assert success, "Mock mode should succeed"
    assert duration < 5, "Mock mode should be fast"
    print("  ✓ Test passed - mock mode works\n")

def test_timeout_wrapper():
    """Verify timeout wrapper is in place"""
    print("Test 4: Timeout wrapper verification")
    
    # Check that orchestration_enhanced has timeout wrapper
    with open("lib/orchestration_enhanced.py", "r") as f:
        content = f.read()
    
    assert "asyncio.wait_for" in content, "Should have asyncio.wait_for wrapper"
    assert "timeout_seconds = 60 if is_api_mode else 30" in content, "Should have different timeouts"
    assert "asyncio.TimeoutError" in content, "Should handle timeout errors"
    
    print("  ✓ Timeout wrapper present in orchestration_enhanced.py")
    print("  ✓ Different timeouts for API (60s) vs mock (30s) mode")
    print("  ✓ TimeoutError handling implemented\n")

if __name__ == "__main__":
    print("=" * 60)
    print("API Mode Fix Verification Tests V2")
    print("=" * 60)
    print()
    
    try:
        test_invalid_key_format()
    except Exception as e:
        print(f"  ✗ Test 1 failed: {e}\n")
    
    try:
        test_valid_format_invalid_key()
    except Exception as e:
        print(f"  ✗ Test 2 failed: {e}\n")
    
    try:
        test_mock_mode_still_works()
    except Exception as e:
        print(f"  ✗ Test 3 failed: {e}\n")
    
    try:
        test_timeout_wrapper()
    except Exception as e:
        print(f"  ✗ Test 4 failed: {e}\n")
    
    print("=" * 60)
    print("Fix Summary V2:")
    print("1. Invalid key format detection (sk-ant- prefix check)")
    print("2. No retry on authentication errors (401)")
    print("3. Timeout wrapper prevents indefinite hanging")
    print("4. Clear error messages for all failure modes")
    print("=" * 60)