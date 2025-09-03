#!/usr/bin/env python3
"""
Safe wrapper to run orchestrator with Unicode protection
Without modifying core files
"""

import sys
import os
import io
import builtins

# Force UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Create safe print function
original_print = print

def safe_print(*args, **kwargs):
    """Print with Unicode safety"""
    new_args = []
    for arg in args:
        if isinstance(arg, str):
            # Replace common Unicode with ASCII
            arg = (arg.replace('✅', '[OK]')
                     .replace('❌', '[X]')
                     .replace('🎯', '[TARGET]')
                     .replace('🔧', '[TOOL]')
                     .replace('📝', '[NOTE]')
                     .replace('🚀', '[START]')
                     .replace('💡', '[IDEA]')
                     .replace('⚠️', '[WARN]')
                     .replace('→', '->')
                     .replace('•', '*'))
            # Remove any remaining Unicode
            try:
                arg.encode('ascii')
            except UnicodeEncodeError:
                arg = arg.encode('ascii', 'ignore').decode('ascii')
        new_args.append(arg)
    return original_print(*new_args, **kwargs)

# Override print
builtins.print = safe_print

# Set up arguments for orchestration
sys.argv = [
    'orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
    '--output-dir', 'projects/quickshop-mvp-safe',
    '--progress',
    '--summary-level', 'concise',
    '--max-parallel', '2',
    '--human-log'
]

print("=" * 80)
print("QUICKSHOP MVP GENERATOR - SAFE MODE")
print("=" * 80)
print()
print("Starting with Unicode protection...")
print()

# Import and run
try:
    import orchestrate_enhanced
    print("[OK] Complete!")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
