#!/usr/bin/env python
"""
Diagnose the exact API error by capturing what's being sent to Anthropic
"""

import sys
import os
import json
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

print("Diagnosing API errors...")
print("=" * 70)

# Import and patch to capture API calls
import lib.agent_runtime as runtime

# Save original method
original_run = runtime.AnthropicAgentRunner.run if hasattr(runtime.AnthropicAgentRunner, 'run') else None

# Create a test runner
from lib.agent_logger import create_new_session, SummaryLevel
logger = create_new_session("diagnose", False, SummaryLevel.CONCISE)

# Import client
import anthropic
from anthropic import Anthropic

# Get API key
api_key = os.environ.get('ANTHROPIC_API_KEY', '')
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set!")
    sys.exit(1)

print(f"API Key: {api_key[:10]}...")

# Create client
client = Anthropic(api_key=api_key)

# Create runner
runner = runtime.AnthropicAgentRunner(client, logger)

# Register standard tools
print("\nRegistering standard tools...")
standard_tools = runtime.create_standard_tools()
for tool in standard_tools:
    runner.register_tool(tool)
print(f"  Registered {len(standard_tools)} standard tools")

# Register MCP tools
print("\nRegistering MCP tools...")
try:
    from lib import mcp_tools
    mcp_tool_list = mcp_tools.create_mcp_tools()
    for tool in mcp_tool_list:
        runner.register_tool(tool)
    print(f"  Registered {len(mcp_tool_list)} MCP tools")
except Exception as e:
    print(f"  Could not register MCP tools: {e}")

# Convert all tools to Anthropic format
print("\nConverting tools to Anthropic format...")
anthropic_tools = []
for i, tool in enumerate(runner.tools.values()):
    try:
        converted = runner._convert_tool_for_anthropic(tool)
        anthropic_tools.append(converted)
    except Exception as e:
        print(f"  ERROR converting {tool.name}: {e}")

print(f"  Converted {len(anthropic_tools)} tools")

# Save the tools for inspection
output_file = Path("api_tools_debug.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(anthropic_tools, f, indent=2)
print(f"\nSaved tool schemas to: {output_file}")

# Try to make an API call
print("\nTesting API call...")
print("-" * 70)

try:
    # Create a simple message
    messages = [
        {
            "role": "user",
            "content": "Hello, can you help me?"
        }
    ]
    
    # Try without tools first
    print("\n1. Testing without tools...")
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            max_tokens=100
        )
        print("  SUCCESS: API call without tools works!")
    except Exception as e:
        print(f"  ERROR without tools: {e}")
    
    # Try with first 5 tools
    print("\n2. Testing with first 5 tools...")
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            tools=anthropic_tools[:5],
            max_tokens=100
        )
        print("  SUCCESS: API call with first 5 tools works!")
    except Exception as e:
        print(f"  ERROR with first 5 tools: {e}")
        if hasattr(e, 'response'):
            print(f"  Response status: {e.response.status_code}")
            print(f"  Response body: {e.response.text[:500]}")
    
    # Try each tool individually to find the problematic one
    print("\n3. Testing each tool individually...")
    problematic_tools = []
    for i, tool in enumerate(anthropic_tools[:10]):  # Test first 10
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=messages,
                tools=[tool],
                max_tokens=100
            )
            print(f"  Tool {i} ({tool['name']}): OK")
        except Exception as e:
            print(f"  Tool {i} ({tool['name']}): ERROR")
            problematic_tools.append((i, tool['name'], str(e)))
    
    if problematic_tools:
        print(f"\n{len(problematic_tools)} problematic tools found:")
        for idx, name, error in problematic_tools:
            print(f"  - Tool {idx} ({name})")
            # Print the problematic schema
            problematic_schema = anthropic_tools[idx]
            print(f"    Schema: {json.dumps(problematic_schema, indent=4)[:500]}...")
    
except Exception as e:
    print(f"\nFatal error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Diagnosis complete. Check api_tools_debug.json for full schemas.")
print("=" * 70)