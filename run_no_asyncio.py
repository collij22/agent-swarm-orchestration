#!/usr/bin/env python
"""Run orchestration without asyncio.run() which is causing the I/O issues"""

import sys
import os
import asyncio

# Set encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

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

print("Starting orchestration with custom event loop...")
print("=" * 60)

# Import the main function
from orchestrate_enhanced import main

# Create and run event loop manually instead of using asyncio.run()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    # Run the main coroutine
    result = loop.run_until_complete(main())
    print("\n" + "=" * 60)
    print("Orchestration completed successfully!")
except KeyboardInterrupt:
    print("\nOrchestration interrupted by user")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Clean up
    loop.close()