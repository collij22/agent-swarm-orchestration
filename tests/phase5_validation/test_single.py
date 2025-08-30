#!/usr/bin/env python3
"""Test single scenario with mock mode"""

import os
import sys
import subprocess
from pathlib import Path

# Set mock mode
os.environ['MOCK_MODE'] = 'true'

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Test imports
print("Testing imports...")
try:
    from lib.mock_anthropic_enhanced import MockAnthropicEnhancedRunner
    print("[OK] Mock runner imported successfully")
except Exception as e:
    print(f"[FAIL] Failed to import mock runner: {e}")
    sys.exit(1)

# Test running orchestrator
print("\nTesting orchestrator with mock mode...")
cmd = [
    sys.executable,
    str(Path(__file__).parent.parent.parent / "orchestrate_enhanced.py"),
    "--project-type", "full_stack_api",
    "--requirements", str(Path(__file__).parent / "requirements" / "ecommerce_platform.yaml"),
    "--human-log",
    "--summary-level", "detailed",
    "--verbose"
]

print(f"Command: {' '.join(cmd)}")
print(f"MOCK_MODE: {os.environ.get('MOCK_MODE')}")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=os.environ.copy())
    print(f"\nReturn code: {result.returncode}")
    
    if result.stdout:
        print("\nStdout (first 1000 chars):")
        print(result.stdout[:1000])
    
    if result.stderr:
        print("\nStderr (first 1000 chars):")
        print(result.stderr[:1000])
        
    if result.returncode != 0:
        print(f"\n[FAIL] Orchestrator failed with return code {result.returncode}")
    else:
        print("\n[OK] Orchestrator completed successfully")
        
except subprocess.TimeoutExpired:
    print("[FAIL] Test timeout")
except Exception as e:
    print(f"[FAIL] Error: {e}")