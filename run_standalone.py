#!/usr/bin/env python
"""Standalone orchestrator runner that fixes all I/O issues"""

import sys
import os
import io

# Fix encoding first
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Create safe stdout/stderr wrappers
class SafeIO:
    def __init__(self, name):
        self.name = name
        self.buffer = []
        
    def write(self, text):
        try:
            sys.__stdout__.write(text)
        except:
            self.buffer.append(text)
        return len(text)
    
    def flush(self):
        try:
            sys.__stdout__.flush()
        except:
            pass
    
    def __getattr__(self, name):
        return getattr(sys.__stdout__, name, lambda *args: None)

# Only replace if there's an issue
try:
    print("Testing stdout...", end="")
    print(" OK")
except:
    sys.stdout = SafeIO('stdout')
    sys.stderr = SafeIO('stderr')

# Now we can safely continue
print("Initializing orchestrator...")

# Set command line arguments
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

# Import with error handling
try:
    # First disable Rich to avoid console issues
    import builtins
    _original_import = builtins.__import__
    
    def custom_import(name, *args, **kwargs):
        if 'rich' in name:
            # Return a dummy module for Rich
            class DummyModule:
                def __getattr__(self, item):
                    return lambda *args, **kwargs: None
                Console = lambda *args, **kwargs: None
                Panel = lambda *args, **kwargs: None
            return DummyModule()
        return _original_import(name, *args, **kwargs)
    
    # Temporarily replace import
    builtins.__import__ = custom_import
    
    # Import orchestrate_enhanced
    from orchestrate_enhanced import main
    import asyncio
    
    # Restore original import
    builtins.__import__ = _original_import
    
    print("Starting orchestration...")
    print("=" * 60)
    
    # Run the main function
    asyncio.run(main())
    
    print("=" * 60)
    print("Orchestration completed successfully!")
    
except KeyboardInterrupt:
    print("\nOrchestration interrupted by user")
    sys.exit(1)
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    
    # Save buffer if we have one
    if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer:
        with open('orchestrate_output.txt', 'w') as f:
            f.write('\n'.join(sys.stdout.buffer))
        print("\nOutput saved to orchestrate_output.txt")
    
    sys.exit(1)