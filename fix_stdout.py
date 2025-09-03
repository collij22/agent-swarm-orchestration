#!/usr/bin/env python
"""Fix stdout issues for Python 3.13"""

import sys
import builtins
import datetime

class SafePrinter:
    """Safe printer that writes to file when stdout fails"""
    
    def __init__(self):
        self.log_file = f"orchestrate_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.file_handle = None
        
    def _get_file(self):
        if self.file_handle is None:
            self.file_handle = open(self.log_file, 'a', encoding='utf-8')
        return self.file_handle
        
    def __call__(self, *args, **kwargs):
        """Print safely"""
        message = ' '.join(str(arg) for arg in args)
        
        # Try normal print first
        try:
            original_print(message)
        except:
            # If that fails, write to file
            f = self._get_file()
            f.write(message + '\n')
            f.flush()
            
    def close(self):
        if self.file_handle:
            self.file_handle.close()

# Save original print
original_print = builtins.print

# Replace print with safe version
safe_printer = SafePrinter()
builtins.print = safe_printer

# Also fix sys.stdout and sys.stderr
import io

class SafeWriter:
    """Safe writer that doesn't fail"""
    
    def __init__(self, name):
        self.name = name
        self.log_file = f"orchestrate_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def write(self, text):
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(text)
        except:
            pass  # Silently ignore write failures
            
    def flush(self):
        pass
        
    def close(self):
        pass
        
    @property
    def closed(self):
        return False
        
    @property 
    def buffer(self):
        return io.BytesIO()

# Replace stdout and stderr
sys.stdout = SafeWriter('stdout')
sys.stderr = SafeWriter('stderr')

print("Stdout/stderr fixed. Now importing orchestrate_enhanced...")

# Now import and run the orchestrator
from orchestrate_enhanced import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())