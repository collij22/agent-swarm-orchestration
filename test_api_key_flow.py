#!/usr/bin/env python3
"""
Test API key validation flow
"""

import os
import sys

# Set invalid API key
invalid_key = 'invalid-key-123'
os.environ['ANTHROPIC_API_KEY'] = invalid_key
os.environ.pop('MOCK_MODE', None)

print(f"[TEST] Testing with API key: {invalid_key}")
print(f"[TEST] Key starts with 'sk-ant-': {invalid_key.startswith('sk-ant-')}")

# Import from lib properly
from lib.agent_runtime import AnthropicAgentRunner, HAS_ANTHROPIC
from lib.agent_logger import create_new_session

print(f"[TEST] HAS_ANTHROPIC: {HAS_ANTHROPIC}")

# Create logger
logger = create_new_session()

# Create runner
print("[TEST] Creating AnthropicAgentRunner...")
runner = AnthropicAgentRunner(api_key=invalid_key, logger=logger)

print(f"[TEST] Runner created")
print(f"[TEST] runner.api_key: {runner.api_key}")
print(f"[TEST] runner.client: {runner.client}")

if runner.client is None:
    print("[TEST] SUCCESS: Client is None as expected with invalid API key")
else:
    print("[TEST] FAILURE: Client was created with invalid API key!")
    print(f"[TEST] Client type: {type(runner.client)}")

logger.close_session()