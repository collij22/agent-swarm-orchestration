#!/usr/bin/env python3
"""
Comprehensive test of API timeout fix
Tests all scenarios to ensure the fix works properly
"""

import os
import sys
import subprocess
import time

def run_test(name, env_setup, expected_result, max_time=15):
    """Run a single test scenario"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    # Set up environment
    env = os.environ.copy()
    # Clear any existing settings
    env.pop('ANTHROPIC_API_KEY', None)
    env.pop('MOCK_MODE', None)
    env.pop('SKIP_API_VALIDATION', None)
    
    # Apply test-specific settings
    for key, value in env_setup.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    
    print(f"Environment: {env_setup}")
    
    # Run the command
    cmd = [
        sys.executable,
        'orchestrate_enhanced.py',
        '--project-type', 'api_service',
        '--requirements', 'tests/phase5_validation/requirements/ecommerce_platform.yaml',
        '--verbose'
    ]
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=max_time,
            encoding='utf-8',
            errors='replace'
        )
        
        elapsed = time.time() - start_time
        
        print(f"Completed in {elapsed:.2f} seconds")
        print(f"Exit code: {result.returncode}")
        
        if expected_result == "fail_fast":
            if result.returncode != 0 and elapsed < max_time - 1:
                # Check for expected error messages
                output = result.stdout + result.stderr
                if any(msg in output for msg in ["Invalid API key", "No API key", "API validation", "authentication failed"]):
                    print("[PASS] Failed fast with appropriate error message")
                    return True
                else:
                    print("[FAIL] Failed but without expected error message")
                    print("Output sample:", output[:500])
                    return False
            else:
                print(f"[FAIL] Did not fail fast (exit={result.returncode}, time={elapsed:.2f}s)")
                return False
                
        elif expected_result == "succeed":
            if result.returncode == 0:
                print("[PASS] Succeeded as expected")
                return True
            else:
                print(f"[FAIL] Failed unexpectedly with exit code {result.returncode}")
                print("Error output:", result.stderr[:500])
                return False
                
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"[FAIL] Process timed out after {elapsed:.2f} seconds")
        print("Process is still hanging - fix not working")
        return False
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return False

# Run all test scenarios
results = []

# Test 1: Invalid API key (should fail fast with validation)
print("\n" + "="*60)
print("RUNNING ALL TESTS")
print("="*60)

results.append(run_test(
    "Invalid API Key Format",
    {'ANTHROPIC_API_KEY': 'invalid-key-123'},
    "fail_fast"
))

# Test 2: Wrong format but looks valid (should fail during validation)
results.append(run_test(
    "Wrong API Key (sk-ant- prefix but invalid)",
    {'ANTHROPIC_API_KEY': 'sk-ant-invalid-test-key'},
    "fail_fast"
))

# Test 3: No API key (should fail immediately)
results.append(run_test(
    "No API Key",
    {},
    "fail_fast"
))

# Test 4: Mock mode (should succeed)
results.append(run_test(
    "Mock Mode",
    {'MOCK_MODE': 'true'},
    "succeed"
))

# Test 5: Skip validation with invalid key (should continue but may fail later)
results.append(run_test(
    "Skip Validation (testing flag)",
    {'ANTHROPIC_API_KEY': 'invalid-key-123', 'SKIP_API_VALIDATION': 'true'},
    "fail_fast"  # Should still fail when trying to use the key
))

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)

passed = sum(results)
total = len(results)

for i, (test_name, result) in enumerate(zip(
    ["Invalid API Key", "Wrong API Key", "No API Key", "Mock Mode", "Skip Validation"],
    results
)):
    status = "PASS" if result else "FAIL"
    print(f"{i+1}. {test_name}: [{status}]")

print(f"\nTotal: {passed}/{total} passed")

if passed == total:
    print("\n[SUCCESS] All tests passed! The API timeout fix is working correctly.")
    sys.exit(0)
else:
    print("\n[FAILURE] Some tests failed. The fix needs more work.")
    sys.exit(1)