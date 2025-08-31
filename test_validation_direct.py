#!/usr/bin/env python3
"""
Test API validation directly
"""

import os
import sys
import time

# Set invalid API key
os.environ['ANTHROPIC_API_KEY'] = 'invalid-key-123'
os.environ.pop('MOCK_MODE', None)
os.environ.pop('SKIP_API_VALIDATION', None)

print("[TEST] Testing API validation directly...")
print("-" * 60)

# Import required modules
from lib.agent_runtime import AnthropicAgentRunner
from lib.agent_logger import create_new_session

print("[TEST] Creating logger...")
logger = create_new_session()

print("[TEST] Creating AnthropicAgentRunner with invalid key...")
start_time = time.time()

try:
    runner = AnthropicAgentRunner(api_key='invalid-key-123', logger=logger)
    elapsed = time.time() - start_time
    
    print(f"[TEST] Runner created in {elapsed:.2f} seconds")
    print(f"[TEST] runner.client = {runner.client}")
    print(f"[TEST] runner.api_key = {runner.api_key}")
    
    if runner.client is None:
        print("[SUCCESS] Client is None - validation worked!")
    else:
        print("[FAILURE] Client was created despite invalid key")
        
except Exception as e:
    elapsed = time.time() - start_time
    print(f"[ERROR] Exception after {elapsed:.2f} seconds: {str(e)}")
    
finally:
    logger.close_session()
    
print("[TEST] Complete")