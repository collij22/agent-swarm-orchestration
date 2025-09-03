#!/usr/bin/env python
"""Ultimate stdout wrapper that fixes Python 3.13 issues"""

import sys
import os
import ctypes
import io
from datetime import datetime

# Get direct access to Windows console
if sys.platform == 'win32':
    kernel32 = ctypes.windll.kernel32
    
    # Get console handles
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE = -12
    
    stdout_handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    stderr_handle = kernel32.GetStdHandle(STD_ERROR_HANDLE)
    
    class DirectConsoleWriter:
        """Write directly to Windows console, bypassing Python's I/O"""
        
        def __init__(self, handle, name):
            self.handle = handle
            self.name = name
            self.encoding = 'utf-8'
            self.errors = 'replace'
            self.closed = False
            self.mode = 'w'
            self.newlines = None
            
            # Also create a log file
            self.log_file = open(f'orchestrate_{name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', 'w', encoding='utf-8')
            
        def write(self, text):
            """Write directly to console"""
            if isinstance(text, str):
                bytes_to_write = text.encode('utf-8', errors='replace')
            else:
                bytes_to_write = text
                
            # Write to log file
            self.log_file.write(text if isinstance(text, str) else text.decode('utf-8', errors='replace'))
            self.log_file.flush()
            
            # Write to console
            if self.handle and self.handle != -1:
                written = ctypes.c_ulong(0)
                kernel32.WriteConsoleA(
                    self.handle,
                    bytes_to_write,
                    len(bytes_to_write),
                    ctypes.byref(written),
                    None
                )
            
            return len(text)
            
        def flush(self):
            self.log_file.flush()
            
        def close(self):
            self.log_file.close()
            
        def fileno(self):
            return -1
            
        def isatty(self):
            return True
            
        def readable(self):
            return False
            
        def writable(self):
            return True
            
        def seekable(self):
            return False
    
    # Replace stdout and stderr with direct console writers
    sys.stdout = DirectConsoleWriter(stdout_handle, 'stdout')
    sys.stderr = DirectConsoleWriter(stderr_handle, 'stderr')
    
    print("Stdout/stderr replaced with direct console writers")
    print("This should work even with Python 3.13")

# Now run the orchestrator
if __name__ == "__main__":
    # Import after fixing stdout
    from orchestrate_enhanced import main
    import asyncio
    
    print("Starting orchestration...")
    asyncio.run(main())