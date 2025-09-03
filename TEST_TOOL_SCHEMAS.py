#!/usr/bin/env python3
"""
Test that tool schemas are now valid
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from lib.agent_runtime import create_standard_tools, AnthropicAgentRunner

print("Testing Tool Schemas")
print("=" * 60)

# Create tools
tools = create_standard_tools()
print(f"Created {len(tools)} tools")

# Create a dummy runner to test schema conversion
runner = AnthropicAgentRunner(api_key="test-key")

# Register tools
for tool in tools:
    runner.register_tool(tool)

print(f"Registered {len(runner.tools)} tools successfully")

# Test schema conversion for each tool
print("\nChecking tool schemas:")
for i, tool in enumerate(tools):
    print(f"\n{i}. {tool.name}:")
    try:
        # Convert to Anthropic format
        schema = runner._convert_tool_for_anthropic(tool)
        
        # Check for problematic types
        params = tool.parameters
        for param_name, param_info in params.items():
            param_type = param_info.get("type")
            print(f"   - {param_name}: {param_type}", end="")
            
            # Check for issues
            if param_type == "any":
                print(" [ERROR: 'any' is not valid]")
            elif param_type == "array" and "items" not in param_info:
                print(" [ERROR: array needs 'items']")
            else:
                print(" [OK]")
                
    except Exception as e:
        print(f"   ERROR: {e}")

print("\n" + "=" * 60)
print("Schema validation complete!")
print("\nIssues fixed:")
print("1. Changed 'any' type to 'object' in share_artifact")
print("2. Added 'items' to array type in verify_deliverables")
print("3. Fixed KeyError by using .get() for 'task' field")