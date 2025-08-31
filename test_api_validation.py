#!/usr/bin/env python3
"""
Direct test of API validation to debug the issue
"""

import os
import sys
from pathlib import Path

# Add lib to path properly
lib_path = Path(__file__).parent / 'lib'
sys.path.insert(0, str(lib_path))

# Test with invalid API key
os.environ['ANTHROPIC_API_KEY'] = 'invalid-key-12345'
os.environ.pop('MOCK_MODE', None)

print("Testing API validation with invalid key...")
print("-" * 60)

try:
    from agent_runtime import AnthropicAgentRunner
    from agent_logger import create_new_session
    
    # Create logger
    logger = create_new_session()
    
    # Try to create runner
    print("Creating AnthropicAgentRunner...")
    runner = AnthropicAgentRunner(api_key='invalid-key-12345', logger=logger)
    
    print(f"Client created: {runner.client is not None}")
    print(f"API key set: {runner.api_key is not None}")
    
    if runner.client is None:
        print("[SUCCESS] Client was not created with invalid API key")
    else:
        print("[FAILURE] Client was created with invalid API key")
        
except Exception as e:
    print(f"[ERROR] Exception during initialization: {str(e)}")
    import traceback
    traceback.print_exc()

print("-" * 60)
print("Test completed")