#!/usr/bin/env python
"""Bypass all I/O issues and run orchestration directly"""

import os
import sys

# Set environment to disable Rich and force simple output
os.environ['TERM'] = 'dumb'
os.environ['NO_COLOR'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

# Monkey-patch print to always work
import builtins
_original_print = builtins.print

def safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except:
        # Write to file if print fails
        with open('orchestrate_bypass.log', 'a') as f:
            f.write(' '.join(str(arg) for arg in args) + '\n')

builtins.print = safe_print

# Now modify the imports to bypass Rich
import importlib.util
import sys

# Create a fake rich module
class FakeConsole:
    def print(self, *args, **kwargs):
        safe_print(*args)
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

class FakePanel:
    def __init__(self, *args, **kwargs):
        pass

class FakeRich:
    Console = lambda *args, **kwargs: FakeConsole()
    Panel = FakePanel
    Table = FakePanel
    Progress = FakePanel
    
sys.modules['rich'] = FakeRich()
sys.modules['rich.console'] = FakeRich()
sys.modules['rich.panel'] = FakeRich()
sys.modules['rich.table'] = FakeRich()
sys.modules['rich.progress'] = FakeRich()
sys.modules['rich.prompt'] = FakeRich()

# Now we can safely import orchestrate_enhanced
safe_print("Starting orchestration with all bypasses enabled...")
safe_print("=" * 60)

# Set up arguments
sys.argv = [
    'orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
    '--output-dir', 'projects/quickshop-mvp-test6',
    '--progress',
    '--summary-level', 'concise',
    '--max-parallel', '2',
    '--human-log'
]

# Import and run
try:
    from orchestrate_enhanced import main
    import asyncio
    
    safe_print("Running main orchestration...")
    asyncio.run(main())
    safe_print("Orchestration complete!")
    
except Exception as e:
    safe_print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to show the log file
    safe_print("\nCheck orchestrate_bypass.log for any output that couldn't be displayed")