#!/usr/bin/env python3
"""Dashboard runner - bypasses all console issues"""

import sys
import os
import time
import subprocess
import webbrowser

print("=" * 80)
print("QUICKSHOP MVP GENERATOR - DASHBOARD MODE")
print("=" * 80)
print()

# Set port
os.environ['DASHBOARD_PORT'] = '5174'

# Configure arguments
cmd = [
    sys.executable,
    'orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
    '--output-dir', 'projects/quickshop-mvp-dashboard',
    '--dashboard',
    '--progress',
    '--summary-level', 'detailed',
    '--max-parallel', '3',
    '--human-log'
]

print(f"Dashboard URL: http://localhost:5174")
print("Opening browser in 3 seconds...")
print()

# Open browser
time.sleep(3)
webbrowser.open(f'http://localhost:5174')

# Run orchestrator
print("Starting orchestration...")
print("-" * 80)

try:
    subprocess.run(cmd, check=True)
    print()
    print("[DONE] Success! Check projects/quickshop-mvp-dashboard/")
except Exception as e:
    print(f"[ERROR] Failed: {e}")
