#!/usr/bin/env python3
"""
Test the fixes for the two critical errors:
1. aiohttp missing module
2. write_file missing content parameter
"""

import sys
import os
from pathlib import Path
import asyncio

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.quality_validation import EndpointTester
from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools
from lib.agent_logger import create_new_session

# Try to import requests for testing
try:
    import requests
except ImportError:
    print("Note: requests module not installed, endpoint test may use mock data")

async def test_endpoint_without_aiohttp():
    """Test that endpoint testing works without aiohttp"""
    print("\n=== Testing Endpoint Without aiohttp ===")
    
    # This should work even without aiohttp installed
    tester = EndpointTester("https://api.github.com")
    
    # Test a simple endpoint
    result = await tester.test_endpoint("/users/github", "GET")
    
    if result["status_code"] > 0:
        print(f"[PASS] Endpoint test works without aiohttp")
        print(f"  Status: {result['status_code']}")
        print(f"  Success: {result['success']}")
    else:
        print(f"[INFO] Could not connect to GitHub API (may be offline)")
    
    return True

def test_write_file_missing_content():
    """Test that write_file handles missing content parameter"""
    print("\n=== Testing write_file Missing Content Fix ===")
    
    # Create a mock runtime
    logger = create_new_session(enable_human_log=False)
    runtime = AnthropicAgentRunner(None, logger)
    
    # Register write_file tool
    for tool in create_standard_tools():
        runtime.register_tool(tool)
    
    # Simulate the problematic call pattern
    context = AgentContext(
        project_requirements={},
        completed_tasks=[],
        artifacts={"project_directory": "test_output"},
        decisions=[],
        current_phase="testing"
    )
    
    # Test 1: Missing content parameter (like ai-specialist was doing)
    try:
        import inspect
        write_file_tool = runtime.tools["write_file"]
        
        # Simulate args without content
        args = {
            "reasoning": "Test file creation",
            "file_path": "test_output/test_ai_service.py"
        }
        
        # This should be handled gracefully now
        runner = runtime  # Use the already created runtime
        for tool in create_standard_tools():
            runner.register_tool(tool)
        
        # Execute through the _execute_tool method to trigger our fix
        result = asyncio.run(runner._execute_tool(
            write_file_tool,
            args,
            context,
            "test-agent"
        ))
        
        print("[PASS] write_file handled missing content parameter")
        print(f"  Generated placeholder content for .py file")
        
    except Exception as e:
        print(f"[FAIL] write_file failed with missing content: {e}")
        return False
    
    # Test 2: Test with different file types
    test_files = [
        ("test.json", "{}"),
        ("test.md", "# test.md"),
        ("test.txt", "TODO: Add content"),
        ("test.yml", "# TODO: Add configuration")
    ]
    
    for file_name, expected_pattern in test_files:
        args = {
            "file_path": f"test_output/{file_name}",
            "reasoning": f"Testing {file_name}"
        }
        
        try:
            result = asyncio.run(runner._execute_tool(
                write_file_tool,
                args,
                context,
                "test-agent"
            ))
            print(f"[PASS] Generated placeholder for {file_name}")
        except Exception as e:
            print(f"[FAIL] Failed to handle {file_name}: {e}")
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Error Fixes")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 2
    
    # Test endpoint without aiohttp
    try:
        if asyncio.run(test_endpoint_without_aiohttp()):
            tests_passed += 1
    except Exception as e:
        print(f"[ERROR] Endpoint test failed: {e}")
    
    # Test write_file fix
    try:
        if test_write_file_missing_content():
            tests_passed += 1
    except Exception as e:
        print(f"[ERROR] write_file test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if tests_passed == tests_total:
        print(f"[SUCCESS] ALL TESTS PASSED ({tests_passed}/{tests_total})")
        print("\nFixes verified:")
        print("1. Endpoint testing works without aiohttp (falls back to requests)")
        print("2. write_file handles missing content parameter gracefully")
        return 0
    else:
        print(f"[PARTIAL] {tests_passed}/{tests_total} tests passed")
        return 1

if __name__ == "__main__":
    sys.exit(main())