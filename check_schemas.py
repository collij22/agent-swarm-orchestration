#!/usr/bin/env python
"""
Check tool schemas without needing API key
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

print("Checking tool schemas...")
print("=" * 70)

# Import runtime
import lib.agent_runtime as runtime

# Create a test runner (with None client since we're not making API calls)
from lib.agent_logger import create_new_session, SummaryLevel
logger = create_new_session("schema_check", False, SummaryLevel.CONCISE)
runner = runtime.AnthropicAgentRunner(None, logger)

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

# Convert all tools and check for issues
print("\nChecking tool schemas for issues...")
print("-" * 70)

issues = []
valid_types = ["string", "integer", "number", "boolean", "array", "object", "null"]

for i, tool in enumerate(runner.tools.values()):
    try:
        converted = runner._convert_tool_for_anthropic(tool)
        
        # Check for common issues
        tool_issues = []
        
        # Check input_schema
        if "input_schema" not in converted:
            tool_issues.append("Missing input_schema")
        else:
            schema = converted["input_schema"]
            
            # Check properties
            if "properties" in schema:
                for prop_name, prop_def in schema["properties"].items():
                    # Check type
                    if "type" not in prop_def:
                        tool_issues.append(f"Property '{prop_name}' missing 'type'")
                    else:
                        prop_type = prop_def["type"]
                        if prop_type not in valid_types:
                            tool_issues.append(f"Property '{prop_name}' has invalid type '{prop_type}'")
                        
                        # Check array items
                        if prop_type == "array" and "items" not in prop_def:
                            tool_issues.append(f"Array property '{prop_name}' missing 'items'")
                        
                        # Check for invalid fields that Anthropic might reject
                        invalid_fields = set(prop_def.keys()) - {
                            "type", "description", "items", "properties", 
                            "additionalProperties", "enum", "default",
                            "minimum", "maximum", "minLength", "maxLength",
                            "pattern", "format", "minItems", "maxItems",
                            "uniqueItems", "multipleOf", "const", "required"
                        }
                        if invalid_fields:
                            tool_issues.append(f"Property '{prop_name}' has invalid fields: {invalid_fields}")
        
        if tool_issues:
            issues.append({
                "index": i,
                "name": tool.name,
                "issues": tool_issues
            })
            print(f"\n❌ Tool {i}: {tool.name}")
            for issue in tool_issues:
                print(f"     {issue}")
        else:
            print(f"✓ Tool {i}: {tool.name}")
            
    except Exception as e:
        issues.append({
            "index": i,
            "name": tool.name,
            "issues": [f"Conversion error: {e}"]
        })
        print(f"\n❌ Tool {i}: {tool.name}")
        print(f"     Conversion error: {e}")

# Save all schemas for inspection
print("\n" + "-" * 70)
print("Saving all schemas for inspection...")

all_schemas = []
for tool in runner.tools.values():
    try:
        converted = runner._convert_tool_for_anthropic(tool)
        all_schemas.append(converted)
    except Exception as e:
        all_schemas.append({
            "name": tool.name,
            "error": str(e)
        })

output_file = Path("all_tool_schemas.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_schemas, f, indent=2)

print(f"Saved {len(all_schemas)} schemas to: {output_file}")

# Summary
print("\n" + "=" * 70)
print("SCHEMA CHECK RESULTS")
print("=" * 70)

if issues:
    print(f"\n❌ Found {len(issues)} tools with issues:")
    for item in issues[:5]:  # Show first 5
        print(f"  - {item['name']}: {len(item['issues'])} issues")
else:
    print("\n✅ All tool schemas are valid!")

print("\nTo inspect full schemas, check: all_tool_schemas.json")
print("=" * 70)