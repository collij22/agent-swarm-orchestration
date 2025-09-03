#!/usr/bin/env python3
"""
Verify that the correct methods exist on AnthropicAgentRunner
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from lib.agent_runtime import AnthropicAgentRunner

print("Checking methods on AnthropicAgentRunner...")
print()

# Create dummy runner (no API key needed for this check)
runner = AnthropicAgentRunner(api_key="dummy-key-for-testing")

# Check what methods exist
methods = [method for method in dir(runner) if not method.startswith('_')]

print("Available public methods:")
for method in sorted(methods):
    print(f"  - {method}")

print()
print("Checking for specific methods:")
print(f"  run_agent: {'YES' if hasattr(runner, 'run_agent') else 'NO'}")
print(f"  run_agent_async: {'YES' if hasattr(runner, 'run_agent_async') else 'NO'}")
print(f"  run_agent_task: {'YES' if hasattr(runner, 'run_agent_task') else 'NO'}")
print(f"  register_tool: {'YES' if hasattr(runner, 'register_tool') else 'NO'}")
print(f"  register_standard_tools: {'YES' if hasattr(runner, 'register_standard_tools') else 'NO'}")

print()
print("Conclusion:")
if hasattr(runner, 'run_agent'):
    print("  ✓ Use runner.run_agent() for synchronous execution")
if hasattr(runner, 'run_agent_async'):
    print("  ✓ Use runner.run_agent_async() for async execution")
if not hasattr(runner, 'run_agent_task'):
    print("  ✗ run_agent_task() does NOT exist - this was the error!")
if hasattr(runner, 'register_tool'):
    print("  ✓ Use runner.register_tool() to register individual tools")
if not hasattr(runner, 'register_standard_tools'):
    print("  ✗ register_standard_tools() does NOT exist - must register individually")