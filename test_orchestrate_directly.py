#!/usr/bin/env python3
"""
Direct test of orchestrate_enhanced.py with invalid API key
"""

import os
import sys
import subprocess
import time

# Set up invalid API key
env = os.environ.copy()
env['ANTHROPIC_API_KEY'] = 'invalid-key-123'
env['PYTHONUNBUFFERED'] = '1'  # Unbuffered output

# Command to run
cmd = [
    sys.executable,
    'orchestrate_enhanced.py',
    '--project-type', 'api_service',
    '--requirements', 'tests/phase5_validation/requirements/ecommerce_platform.yaml',
    '--verbose'
]

print("Testing orchestrate_enhanced.py with invalid API key...")
print("Command:", ' '.join(cmd))
print("-" * 60)

start_time = time.time()

try:
    # Run with timeout
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,  # 15 second timeout
        encoding='utf-8',
        errors='replace'  # Replace invalid chars instead of failing
    )
    
    elapsed = time.time() - start_time
    
    print(f"Process completed in {elapsed:.2f} seconds")
    print(f"Exit code: {result.returncode}")
    print("\n--- STDOUT ---")
    print(result.stdout[:2000] if result.stdout else "(empty)")
    print("\n--- STDERR ---")
    print(result.stderr[:2000] if result.stderr else "(empty)")
    
    if result.returncode != 0 and elapsed < 10:
        print("\n[SUCCESS] Process failed quickly as expected with invalid API key")
    else:
        print("\n[FAILURE] Process did not fail as expected")
        
except subprocess.TimeoutExpired as e:
    elapsed = time.time() - start_time
    print(f"\n[FAILURE] Process timed out after {elapsed:.2f} seconds")
    print("The process is still hanging with invalid API key")
    print("\nPartial output:")
    if e.stdout:
        print("STDOUT:", e.stdout.decode('utf-8', errors='replace')[:1000])
    if e.stderr:
        print("STDERR:", e.stderr.decode('utf-8', errors='replace')[:1000])
        
except Exception as e:
    print(f"\n[ERROR] Unexpected error: {str(e)}")
    import traceback
    traceback.print_exc()