#!/usr/bin/env python3
"""
Run fix_specific_tools.py with proper environment setup
"""

import sys
import os
import subprocess

# Force UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Windows console UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

print("=" * 80)
print("RUNNING FIX_SPECIFIC_TOOLS WITH PROPER SETUP")
print("=" * 80)
print()
print("This will:")
print("  1. Fix tool schemas")
print("  2. Run orchestrate_bypass.py")
print("  3. Generate QuickShop MVP")
print()
print("Starting...")
print("-" * 80)

# Run fix_specific_tools.py in a subprocess with proper encoding
cmd = [sys.executable, "fix_specific_tools.py"]

try:
    # Use Popen to see output in real-time
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1
    )
    
    # Print output line by line
    for line in process.stdout:
        # Clean the line from Unicode
        line = (line.replace('✅', '[OK]')
                   .replace('❌', '[X]')
                   .replace('🎯', '[TARGET]')
                   .replace('🔧', '[TOOL]')
                   .replace('📝', '[NOTE]')
                   .replace('🚀', '[START]')
                   .replace('→', '->')
                   .replace('•', '*'))
        print(line, end='')
    
    # Wait for completion
    process.wait()
    
    if process.returncode == 0:
        print()
        print("=" * 80)
        print("[SUCCESS] Agents completed!")
        print("=" * 80)
    else:
        print()
        print("[WARNING] Process ended with code:", process.returncode)
        
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print()
print("Check the output in: projects/quickshop-mvp-test8/")
print("And logs in: orchestrate_bypass.log")