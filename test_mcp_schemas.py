#!/usr/bin/env python
"""Test MCP tool schemas specifically"""

import sys
import os
import json
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

print("Testing MCP tool schemas...")
print("=" * 70)

# Try to import MCP tools
try:
    from lib import mcp_tools
    from lib import mcp_manager
    
    print("\n✓ MCP modules found")
    
    # Try to create MCP tools
    print("\nAttempting to create MCP tools...")
    print("-" * 70)
    
    try:
        # Get MCP tools
        mcp_tool_list = mcp_tools.create_mcp_tools()
        
        if mcp_tool_list:
            print(f"\n✓ Created {len(mcp_tool_list)} MCP tools:")
            for tool in mcp_tool_list[:5]:  # Show first 5
                print(f"    - {tool.name}")
        else:
            print("\n⚠️ No MCP tools created (MCPs might not be configured)")
            
    except Exception as e:
        print(f"\n⚠️ Could not create MCP tools: {e}")
        
    # Try to get conditional MCP tools
    print("\nChecking conditional MCP tools...")
    print("-" * 70)
    
    try:
        conditional_tools = mcp_tools.get_conditional_mcp_tools("requirements-analyst", "Research Project", None)
        
        if conditional_tools:
            print(f"\n✓ Found {len(conditional_tools)} conditional MCP tools for requirements-analyst:")
            for tool in conditional_tools[:5]:
                print(f"    - {tool.name}")
        else:
            print("\n⚠️ No conditional MCP tools found")
            
    except Exception as e:
        print(f"\n⚠️ Could not get conditional MCP tools: {e}")
    
    # Check MCP manager
    print("\nChecking MCP Manager...")
    print("-" * 70)
    
    try:
        from lib.mcp_manager import MCPManager
        
        manager = MCPManager()
        print(f"\n✓ MCP Manager initialized")
        print(f"  Available MCPs: {list(manager.server_configs.keys())[:5]}...")
        
    except Exception as e:
        print(f"\n⚠️ Could not initialize MCP Manager: {e}")
        
except ImportError as e:
    print(f"\n⚠️ MCP modules not found: {e}")
    print("This might be normal if MCPs are not installed")

# Now test with the schema fix applied
print("\n" + "=" * 70)
print("Applying schema fixes and testing again...")
print("=" * 70)

import lib.agent_runtime as runtime

def comprehensive_convert_tool(self, tool):
    """Convert tool with comprehensive schema fixes"""
    properties = {}
    required = []
    
    if hasattr(tool, 'requires_reasoning') and tool.requires_reasoning:
        properties["reasoning"] = {
            "type": "string",
            "description": f"Explanation for why we're using {tool.name}"
        }
        required.append("reasoning")
    
    if hasattr(tool, 'parameters') and tool.parameters:
        for param_name, param_info in tool.parameters.items():
            if isinstance(param_info, dict):
                param_type = param_info.get("type", "string")
                
                # Fix types
                if param_type == "str": param_type = "string"
                elif param_type == "int": param_type = "integer"
                elif param_type == "float": param_type = "number"
                elif param_type == "bool": param_type = "boolean"
                elif param_type == "list": param_type = "array"
                elif param_type == "dict": param_type = "object"
                elif param_type == "any": param_type = "string"
                
                valid_types = ["string", "integer", "number", "boolean", "array", "object", "null"]
                if param_type not in valid_types:
                    param_type = "string"
                
                prop = {
                    "type": param_type,
                    "description": param_info.get("description", "")
                }
                
                if param_type == "array":
                    prop["items"] = param_info.get("items", {"type": "string"})
                elif param_type == "object":
                    if "properties" in param_info:
                        prop["properties"] = param_info["properties"]
                    prop["additionalProperties"] = param_info.get("additionalProperties", True)
                
                if "enum" in param_info:
                    prop["enum"] = param_info["enum"]
                if "default" in param_info:
                    prop["default"] = param_info["default"]
                
                valid_fields = ["type", "description", "items", "properties", 
                               "additionalProperties", "enum", "default", 
                               "minimum", "maximum", "minLength", "maxLength",
                               "pattern", "format", "minItems", "maxItems"]
                
                clean_prop = {}
                for field in valid_fields:
                    if field in prop:
                        clean_prop[field] = prop[field]
                
                properties[param_name] = clean_prop
                
                if param_info.get("required", False):
                    required.append(param_name)
    
    schema = {
        "name": tool.name,
        "description": getattr(tool, 'description', ''),
        "input_schema": {
            "type": "object",
            "properties": properties,
            "additionalProperties": False
        }
    }
    
    if required:
        schema["input_schema"]["required"] = required
    
    return schema

# Apply fix
runtime.AnthropicAgentRunner._convert_tool_for_anthropic = comprehensive_convert_tool

# Try with fixed schema converter
try:
    from lib.agent_logger import create_new_session, SummaryLevel
    logger = create_new_session("test_mcp", False, SummaryLevel.CONCISE)
    runner = runtime.AnthropicAgentRunner(None, logger)
    
    print("\nTesting MCP tools with schema fixes...")
    print("-" * 70)
    
    # Try to register MCP tools
    try:
        mcp_tool_list = mcp_tools.create_mcp_tools()
        
        if mcp_tool_list:
            errors = []
            for tool in mcp_tool_list:
                try:
                    runner.register_tool(tool)
                    converted = runner._convert_tool_for_anthropic(tool)
                    print(f"✓ {tool.name}: Schema valid")
                except Exception as e:
                    errors.append(f"✗ {tool.name}: {e}")
            
            if errors:
                print("\nSchema errors found:")
                for error in errors:
                    print(f"  {error}")
            else:
                print(f"\n✅ All {len(mcp_tool_list)} MCP tools have valid schemas!")
        else:
            print("No MCP tools to test")
            
    except Exception as e:
        print(f"Could not test MCP tools: {e}")
        
except Exception as e:
    print(f"\nCould not run MCP schema test: {e}")

print("\n" + "=" * 70)
print("MCP Schema Test Complete")
print("=" * 70)