#!/usr/bin/env python3
"""
Simple fix to restore agent_runtime.py to working state
"""

import os
import shutil
from pathlib import Path

print("Restoring agent_runtime.py from backup...")

runtime_path = Path("lib/agent_runtime.py")
backup_path = Path("lib/agent_runtime_backup.py")

if backup_path.exists():
    # Restore from backup
    shutil.copy2(backup_path, runtime_path)
    print(f"[OK] Restored agent_runtime.py from backup")
else:
    print("[ERROR] No backup found. Looking for other backups...")
    # Try to find another backup
    for backup in Path("lib").glob("agent_runtime*.py"):
        if backup != runtime_path:
            print(f"Found backup: {backup}")
            response = input("Use this backup? (y/n): ")
            if response.lower() == 'y':
                shutil.copy2(backup, runtime_path)
                print(f"[OK] Restored from {backup}")
                break

print("\nNow applying safe Unicode fix...")

# Create a wrapper that doesn't modify the original files
wrapper_code = '''#!/usr/bin/env python3
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
'''

wrapper_path = Path("RUN_SAFE.py")
wrapper_path.write_text(wrapper_code, encoding='utf-8')
print(f"[OK] Created safe wrapper: {wrapper_path}")

print("\n" + "=" * 80)
print("FIXES APPLIED")
print("=" * 80)
print()
print("Run the orchestrator with:")
print("  python RUN_SAFE.py")
print()
print("This wrapper:")
print("  - Does NOT modify core files")
print("  - Intercepts print statements")
print("  - Replaces Unicode with ASCII")
print("  - Runs orchestration safely")