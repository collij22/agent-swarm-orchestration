#!/usr/bin/env python3
"""
Test script to verify API timeout fix
Tests both invalid API key and missing API key scenarios
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def test_invalid_api_key():
    """Test with an invalid API key that doesn't start with sk-ant-"""
    print("=" * 60)
    print("Test 1: Invalid API Key Format")
    print("=" * 60)
    
    # Set an invalid API key
    env = os.environ.copy()
    env['ANTHROPIC_API_KEY'] = 'invalid-key-12345'
    env.pop('MOCK_MODE', None)  # Ensure we're not in mock mode
    
    start_time = time.time()
    
    # Run orchestrate_enhanced.py with the invalid key
    cmd = [
        sys.executable,
        'orchestrate_enhanced.py',
        '--project-type', 'api_service',
        '--requirements', 'tests/phase5_validation/requirements/ecommerce_platform.yaml',
        '--verbose'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=10  # Should fail quickly now
        )
        
        elapsed = time.time() - start_time
        print(f"Process exited in {elapsed:.2f} seconds")
        print(f"Exit code: {result.returncode}")
        print("\nStdout:")
        print(result.stdout)
        print("\nStderr:")
        print(result.stderr)
        
        # Check that it failed quickly (not after 180s timeout)
        if elapsed < 15:
            print("[PASS] Failed quickly with invalid API key")
            return True
        else:
            print("[FAIL] Took too long to fail")
            return False
            
    except subprocess.TimeoutExpired:
        print("[FAIL] Process timed out (still hanging)")
        return False

def test_missing_api_key():
    """Test with no API key set"""
    print("\n" + "=" * 60)
    print("Test 2: Missing API Key")
    print("=" * 60)
    
    # Remove API key from environment
    env = os.environ.copy()
    env.pop('ANTHROPIC_API_KEY', None)
    env.pop('MOCK_MODE', None)  # Ensure we're not in mock mode
    
    start_time = time.time()
    
    # Run orchestrate_enhanced.py without API key
    cmd = [
        sys.executable,
        'orchestrate_enhanced.py',
        '--project-type', 'api_service',
        '--requirements', 'tests/phase5_validation/requirements/ecommerce_platform.yaml',
        '--verbose'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=10  # Should fail quickly now
        )
        
        elapsed = time.time() - start_time
        print(f"Process exited in {elapsed:.2f} seconds")
        print(f"Exit code: {result.returncode}")
        print("\nStdout:")
        print(result.stdout)
        print("\nStderr:")
        print(result.stderr)
        
        # Check that it failed quickly
        if elapsed < 15 and result.returncode != 0:
            print("[PASS] Failed quickly with missing API key")
            return True
        else:
            print("[FAIL] Unexpected behavior")
            return False
            
    except subprocess.TimeoutExpired:
        print("[FAIL] Process timed out (still hanging)")
        return False

def test_mock_mode():
    """Test that mock mode still works"""
    print("\n" + "=" * 60)
    print("Test 3: Mock Mode (Should Work)")
    print("=" * 60)
    
    # Enable mock mode
    env = os.environ.copy()
    env['MOCK_MODE'] = 'true'
    env.pop('ANTHROPIC_API_KEY', None)  # Remove API key to test mock mode
    
    start_time = time.time()
    
    # Run orchestrate_enhanced.py in mock mode
    cmd = [
        sys.executable,
        'orchestrate_enhanced.py',
        '--project-type', 'api_service',
        '--requirements', 'tests/phase5_validation/requirements/ecommerce_platform.yaml',
        '--verbose'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=30  # Mock mode should complete quickly
        )
        
        elapsed = time.time() - start_time
        print(f"Process completed in {elapsed:.2f} seconds")
        print(f"Exit code: {result.returncode}")
        
        # In mock mode, it should succeed (exit code 0)
        if result.returncode == 0:
            print("[PASS] Mock mode works correctly")
            return True
        else:
            print("[FAIL] Mock mode failed unexpectedly")
            print("\nStdout:")
            print(result.stdout)
            print("\nStderr:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("[FAIL] Mock mode timed out")
        return False

def main():
    """Run all tests"""
    print("Testing API Timeout Fix")
    print("=" * 60)
    
    results = []
    
    # Test 1: Invalid API key
    results.append(test_invalid_api_key())
    
    # Test 2: Missing API key
    results.append(test_missing_api_key())
    
    # Test 3: Mock mode
    results.append(test_mock_mode())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] All tests passed! The timeout fix is working correctly.")
        return 0
    else:
        print("[FAILURE] Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())