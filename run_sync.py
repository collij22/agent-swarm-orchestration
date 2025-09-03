#!/usr/bin/env python
"""Run orchestration synchronously without asyncio"""

import sys
import os
import subprocess

# Build the command
cmd = [
    sys.executable,
    "-c",
    """
import sys
import os
sys.path.insert(0, r'C:\\AI projects\\1test')
os.chdir(r'C:\\AI projects\\1test')

# Import and run synchronously
from orchestrate_enhanced import main
import asyncio

# Create a new event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    # Run the main function
    loop.run_until_complete(main())
finally:
    loop.close()
"""
]

# Add arguments
sys.argv = ['orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
    '--output-dir', 'projects/quickshop-mvp-test6',
    '--progress',
    '--summary-level', 'concise',
    '--max-parallel', '2',
    '--human-log'
]

# Run as subprocess with proper I/O
result = subprocess.run(
    cmd,
    env={**os.environ, 'PYTHONUNBUFFERED': '1', 'PYTHONIOENCODING': 'utf-8'},
    text=True,
    capture_output=False  # Let output go directly to console
)

sys.exit(result.returncode)