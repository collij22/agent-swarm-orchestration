#!/usr/bin/env python3
"""Console runner with full Unicode protection"""

import sys
import os
import io

# Set up environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, r"C:\AI projects\1test")

# Import Unicode stripper first
from lib.unicode_stripper import patch_print
patch_print()

print("=" * 80)
print("QUICKSHOP MVP GENERATOR - CONSOLE MODE")
print("=" * 80)
print()

# Configure arguments
sys.argv = [
    'orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
    '--output-dir', 'projects/quickshop-mvp-console',
    '--progress',
    '--summary-level', 'concise',
    '--max-parallel', '2',
    '--human-log'
]

print("Starting agent orchestration...")
print("Unicode protection: ACTIVE")
print("Output: projects/quickshop-mvp-console/")
print()
print("-" * 80)

# Import and run
try:
    import orchestrate_enhanced
    print()
    print("=" * 80)
    print("[DONE] Orchestration complete!")
    print("=" * 80)
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()
