#!/usr/bin/env python3
"""
Simple test script that mimics orchestrate_enhanced.py behavior
"""

import os
import sys

# Get API key from environment
api_key = os.environ.get('ANTHROPIC_API_KEY')

print(f"API key provided: {'yes' if api_key else 'no'}")
print(f"Mock mode: {os.environ.get('MOCK_MODE', 'false')}")

if os.environ.get('MOCK_MODE') != 'true':
    # We're in API mode
    if not api_key:
        print("[ERROR] No API key provided in API mode")
        sys.exit(1)
    elif not api_key.startswith('sk-ant-'):
        print(f"[ERROR] Invalid API key format. Expected 'sk-ant-...' but got '{api_key[:10]}...'")
        sys.exit(1)

print("[SUCCESS] Would continue with execution...")
sys.exit(0)