#!/usr/bin/env python3
"""
Bypass Rich console issues entirely
"""

import sys
import os

# Disable Rich before importing anything
os.environ['NO_COLOR'] = '1'
os.environ['TERM'] = 'dumb'

print("=" * 80)
print("QUICKSHOP MVP - BYPASSING RICH CONSOLE")
print("=" * 80)
print()

# Override Rich imports with dummy implementations
class DummyConsole:
    def print(self, *args, **kwargs):
        text = str(args[0]) if args else ""
        # Strip Rich markup
        import re
        text = re.sub(r'\[.*?\]', '', text)
        print(text)
    
    def status(self, *args, **kwargs):
        class DummyStatus:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def update(self, *a, **kw): pass
        return DummyStatus()
    
    def log(self, *args, **kwargs):
        print(*args)

class DummyPanel:
    def __init__(self, content, **kwargs):
        self.content = content

class DummyProgress:
    def __init__(self, *args, **kwargs):
        pass
    def add_task(self, *args, **kwargs):
        return 0
    def update(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

# Monkey-patch Rich modules
import sys
sys.modules['rich'] = type(sys)('rich')
sys.modules['rich.console'] = type(sys)('console')
sys.modules['rich.console'].Console = DummyConsole
sys.modules['rich.panel'] = type(sys)('panel')
sys.modules['rich.panel'].Panel = DummyPanel
sys.modules['rich.progress'] = type(sys)('progress')
sys.modules['rich.progress'].Progress = DummyProgress
sys.modules['rich.table'] = type(sys)('table')
sys.modules['rich.table'].Table = lambda **kw: None

# Now configure and run
sys.argv = [
    'orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
    '--output-dir', 'projects/quickshop-mvp-bypass',
    '--progress',
    '--summary-level', 'concise',
    '--max-parallel', '2',
    '--human-log'
]

print("Starting orchestration without Rich...")
print("-" * 80)

try:
    import orchestrate_enhanced
    print()
    print("=" * 80)
    print("[SUCCESS] Complete!")
    print("=" * 80)
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()