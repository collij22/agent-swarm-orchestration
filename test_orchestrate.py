#!/usr/bin/env python
"""Test orchestration without asyncio issues"""

import sys
import os

# Add the project root to path
sys.path.insert(0, r'C:\AI projects\1test')

# Now run the orchestration directly
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
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()