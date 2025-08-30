#!/usr/bin/env python3
"""Debug orchestrator with mock mode"""

import os
import sys
import subprocess
from pathlib import Path

# Set mock mode
os.environ['MOCK_MODE'] = 'true'

cmd = [
    sys.executable,
    str(Path(__file__).parent.parent.parent / "orchestrate_enhanced.py"),
    "--project-type", "full_stack_api",
    "--requirements", str(Path(__file__).parent / "requirements" / "ecommerce_platform.yaml"),
    "--verbose"
]

print(f"Running: {' '.join(cmd)}")
print(f"MOCK_MODE: {os.environ.get('MOCK_MODE')}")
print("="*60)

result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', env=os.environ.copy())

print(f"Return code: {result.returncode}")
print("\nStderr:")
stderr_text = result.stderr[:1000] if result.stderr else "No stderr"
print(stderr_text.encode('ascii', 'replace').decode('ascii'))
print("\nLast 1000 chars of stdout:")
stdout_text = result.stdout[-1000:] if result.stdout else "No stdout"
print(stdout_text.encode('ascii', 'replace').decode('ascii'))