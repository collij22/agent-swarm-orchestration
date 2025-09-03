#!/usr/bin/env python
"""Fix I/O issues and run orchestration directly"""

import sys
import os
import io
import asyncio
from pathlib import Path

# Fix encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Create bulletproof I/O streams
class SafeStream:
    """Stream that never closes and handles all errors"""
    
    def __init__(self, base_stream=None):
        self.base = base_stream or sys.__stdout__
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.closed = False
        self.buffer = []
        
    def write(self, text):
        """Write with fallback"""
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
            
        # Try base stream
        try:
            if self.base and not getattr(self.base, 'closed', False):
                result = self.base.write(text)
                self.base.flush()
                return result
        except:
            pass
            
        # Fallback to buffer
        self.buffer.append(text)
        
        # Try to print to terminal directly
        try:
            sys.__stdout__.write(text)
            sys.__stdout__.flush()
        except:
            pass
            
        return len(text) if text else 0
        
    def flush(self):
        """Flush safely"""
        try:
            if self.base:
                self.base.flush()
        except:
            pass
            
    def close(self):
        """Never close"""
        pass
        
    def fileno(self):
        """Return file descriptor"""
        try:
            return self.base.fileno()
        except:
            return 1
            
    def isatty(self):
        """Check if terminal"""
        try:
            return self.base.isatty()
        except:
            return False
            
    def __getattr__(self, name):
        """Delegate other methods"""
        return getattr(self.base, name, lambda *a, **k: None)

# Install safe streams immediately
sys.stdout = SafeStream(sys.stdout)
sys.stderr = SafeStream(sys.stderr)

# Now patch all the modules before importing
def patch_all_modules():
    """Patch all modules to handle I/O issues"""
    
    # Patch Rich
    import importlib
    import types
    
    # Create fake Rich module
    fake_rich = types.ModuleType('rich')
    fake_rich_console = types.ModuleType('rich.console')
    fake_rich_panel = types.ModuleType('rich.panel')
    fake_rich_table = types.ModuleType('rich.table')
    fake_rich_progress = types.ModuleType('rich.progress')
    
    class FakeConsole:
        def __init__(self, *args, **kwargs):
            pass
        def print(self, *args, **kwargs):
            print(*[str(a) for a in args])
        def log(self, *args, **kwargs):
            print(*[str(a) for a in args])
        def __getattr__(self, name):
            return lambda *a, **k: None
            
    class FakePanel:
        def __init__(self, content, *args, **kwargs):
            self.content = content
        def __str__(self):
            return str(self.content)
            
    class FakeTable:
        def __init__(self, *args, **kwargs):
            pass
        def add_column(self, *args, **kwargs):
            pass
        def add_row(self, *args, **kwargs):
            pass
        def __str__(self):
            return "Table"
            
    fake_rich_console.Console = FakeConsole
    fake_rich_panel.Panel = FakePanel
    fake_rich_table.Table = FakeTable
    fake_rich_progress.Progress = FakeConsole
    
    # Register fake modules
    sys.modules['rich'] = fake_rich
    sys.modules['rich.console'] = fake_rich_console
    sys.modules['rich.panel'] = fake_rich_panel
    sys.modules['rich.table'] = fake_rich_table
    sys.modules['rich.progress'] = fake_rich_progress

# Apply patches
patch_all_modules()

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Now we can safely import
from orchestrate_enhanced import main

async def run_safe():
    """Run with safety wrapper"""
    # Set arguments
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
    
    print("=" * 60)
    print("Fixed I/O Orchestration Runner")
    print("=" * 60)
    print()
    
    try:
        result = await main()
        print("\n" + "=" * 60)
        print("SUCCESS: Orchestration completed!")
        print("=" * 60)
        
        # Save any buffered output
        if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer:
            with open('orchestration_output.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(sys.stdout.buffer))
            print("Output saved to orchestration_output.txt")
            
        return result
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Save error output
        if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer:
            with open('orchestration_error.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(sys.stdout.buffer))
            print("Error output saved to orchestration_error.txt")
        
        raise

if __name__ == "__main__":
    try:
        # Run with asyncio
        asyncio.run(run_safe())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL: {e}")
        sys.exit(1)