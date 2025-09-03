#!/usr/bin/env python
"""Force stdout to stay open and run orchestration"""

import sys
import os
import io

# Create new stdout/stderr that can't be closed
class UnclosableStream:
    def __init__(self, stream):
        self._stream = stream
        
    def write(self, data):
        try:
            return self._stream.write(data)
        except:
            # If write fails, write to file instead
            with open('orchestrate_output.txt', 'a') as f:
                f.write(data)
            return len(data)
    
    def flush(self):
        try:
            self._stream.flush()
        except:
            pass
    
    def close(self):
        # Never actually close
        pass
        
    @property
    def closed(self):
        # Always report as open
        return False
        
    def __getattr__(self, name):
        return getattr(self._stream, name)

# Replace stdout and stderr with unclosable versions
sys.stdout = UnclosableStream(sys.__stdout__)
sys.stderr = UnclosableStream(sys.__stderr__)

# Now run the orchestration
if __name__ == "__main__":
    print("Starting with forced-open stdout...")
    
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
    
    # Import and run
    from orchestrate_enhanced import main
    import asyncio
    
    asyncio.run(main())