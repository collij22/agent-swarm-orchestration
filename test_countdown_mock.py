#!/usr/bin/env python3
"""
Test the orchestrator in mock mode with verbose output
"""

import os
import sys

# Set mock mode
os.environ['MOCK_MODE'] = 'true'

# Import and run
sys.argv = [
    'orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'countdown_requirements.yaml',
    '--verbose',
    '--output-dir', 'countdown_game'
]

try:
    import orchestrate_enhanced
except Exception as e:
    print(f"Error running orchestrator: {e}")
    import traceback
    traceback.print_exc()