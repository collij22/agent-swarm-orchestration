#!/usr/bin/env python3
"""Direct test of orchestrator with timeout"""

import os
import sys
import subprocess
import signal
from pathlib import Path

# Set mock mode
os.environ['MOCK_MODE'] = 'true'

# Timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError("Test timed out after 5 seconds")

# Set signal for timeout (Unix only, won't work on Windows)
# signal.signal(signal.SIGALRM, timeout_handler)
# signal.alarm(5)

cmd = [
    sys.executable,
    str(Path(__file__).parent.parent.parent / "orchestrate_enhanced.py"),
    "--project-type", "api_service",
    "--help"  # Just test help first
]

print(f"Testing help command: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
print(f"Help return code: {result.returncode}")

if result.returncode == 0:
    print("Help command works!")
    
    # Now test with minimal requirements
    minimal_req = Path(__file__).parent / "minimal_test.yaml"
    minimal_req.write_text("""
project:
  name: "MinimalTest"
  type: "api_service"
  description: "Minimal test"

features:
  - "Basic API endpoint"
  - "Health check"

requirements:
  - id: "REQ-001"
    description: "Test requirement"
    priority: "high"
    category: "functional"
""")
    
    cmd2 = [
        sys.executable,
        str(Path(__file__).parent.parent.parent / "orchestrate_enhanced.py"),
        "--project-type", "api_service",
        "--requirements", str(minimal_req)
    ]
    
    print(f"\nTesting minimal requirements: {' '.join(cmd2)}")
    print("Running with 10 second timeout...")
    
    try:
        result2 = subprocess.run(cmd2, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10)
        print(f"Return code: {result2.returncode}")
        
        if result2.returncode != 0:
            print("\nStderr (first 500 chars):")
            stderr_text = result2.stderr[:500] if result2.stderr else "No stderr"
            print(stderr_text.encode('ascii', 'replace').decode('ascii'))
            print("\nStdout (last 500 chars):")
            stdout_text = result2.stdout[-500:] if result2.stdout else "No stdout"
            print(stdout_text.encode('ascii', 'replace').decode('ascii'))
            
            # Try to find error in output
            if "error" in result2.stdout.lower() or "traceback" in result2.stdout.lower():
                print("\nFound error in output - searching for details...")
                lines = result2.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'error' in line.lower() or 'traceback' in line.lower():
                        # Print context around error
                        start = max(0, i-2)
                        end = min(len(lines), i+5)
                        print("\nError context:")
                        for j in range(start, end):
                            safe_line = lines[j].encode('ascii', 'replace').decode('ascii')
                            print(f"  {j}: {safe_line}")
                        break
    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out after 10 seconds")
        print("The orchestrator appears to be hanging in mock mode")
else:
    print("Help command failed!")
    print(f"Stderr: {result.stderr[:500] if result.stderr else 'No stderr'}")