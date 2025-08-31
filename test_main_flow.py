#!/usr/bin/env python3
"""
Test the full main() flow with invalid API key
"""

import os
import sys
import asyncio

# Set invalid API key
os.environ['ANTHROPIC_API_KEY'] = 'invalid-key-123'
os.environ.pop('MOCK_MODE', None)

print("[TEST] Running main() with invalid API key...")

# Set sys.argv to simulate command line arguments
sys.argv = [
    'orchestrate_enhanced.py',
    '--project-type', 'api_service',
    '--requirements', 'tests/phase5_validation/requirements/ecommerce_platform.yaml',
    '--verbose'
]

# Import and run main
from orchestrate_enhanced import main

try:
    asyncio.run(main())
    print("[TEST] main() completed")
except SystemExit as e:
    print(f"[TEST] main() exited with code: {e.code}")
except Exception as e:
    print(f"[TEST] main() raised exception: {str(e)}")
    import traceback
    traceback.print_exc()