#!/usr/bin/env python
"""Run orchestration with proper stdout/stderr handling"""

import sys
import os
import io

# Force stdout and stderr to be properly configured
sys.stdout = io.TextIOWrapper(
    io.BufferedWriter(io.FileIO(1, 'wb')),
    encoding='utf-8',
    line_buffering=True
)
sys.stderr = io.TextIOWrapper(
    io.BufferedWriter(io.FileIO(2, 'wb')),
    encoding='utf-8',
    line_buffering=True
)

# Add the project root to path
sys.path.insert(0, r'C:\AI projects\1test')

# Now run the orchestration
from orchestrate_enhanced import main
import asyncio

# Set the arguments
sys.argv = [
    'orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
    '--output-dir', 'projects/quickshop-mvp-test5',
    '--progress',
    '--summary-level', 'concise',
    '--max-parallel', '2',
    '--human-log'
]

# Run it
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error running orchestration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)