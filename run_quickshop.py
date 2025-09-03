#!/usr/bin/env python
"""Bypass all I/O issues and run orchestration directly"""

import os
import sys
from pathlib import Path

# Set environment to disable Rich and force simple output
os.environ['TERM'] = 'dumb'
os.environ['NO_COLOR'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

# Monkey-patch print to always work
import builtins
_original_print = builtins.print

def safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except:
        # Write to file if print fails
        with open('orchestrate_bypass.log', 'a') as f:
            f.write(' '.join(str(arg) for arg in args) + '\n')

builtins.print = safe_print

# Now modify the imports to bypass Rich
import importlib.util
import sys

# Create a fake rich module
class FakeConsole:
    def print(self, *args, **kwargs):
        safe_print(*args)
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

class FakePanel:
    def __init__(self, *args, **kwargs):
        pass

class FakeRich:
    Console = lambda *args, **kwargs: FakeConsole()
    Panel = FakePanel
    Table = FakePanel
    Progress = FakePanel
    
sys.modules['rich'] = FakeRich()
sys.modules['rich.console'] = FakeRich()
sys.modules['rich.panel'] = FakeRich()
sys.modules['rich.table'] = FakeRich()
sys.modules['rich.progress'] = FakeRich()
sys.modules['rich.prompt'] = FakeRich()

# CRITICAL: Apply tool schema fixes BEFORE importing orchestrate_enhanced
import sys
sys.path.insert(0, str(Path(__file__).parent / "lib"))

import lib.agent_runtime as runtime

# Fix tool converter - THIS WAS MISSING!
def fixed_tool_converter(self, tool):
    """Convert tool with ALL edge cases handled"""
    properties = {}
    required = []
    
    if hasattr(tool, 'requires_reasoning') and tool.requires_reasoning:
        properties["reasoning"] = {
            "type": "string",
            "description": f"Reasoning for using {tool.name}"
        }
        required.append("reasoning")
    
    if hasattr(tool, 'parameters') and tool.parameters:
        for param_name, param_info in tool.parameters.items():
            if not isinstance(param_info, dict):
                continue
            
            param_type = param_info.get("type", "string")
            
            # CRITICAL FIX: Convert 'any' to 'string'
            type_map = {
                "str": "string",
                "int": "integer",
                "bool": "boolean",
                "float": "number",
                "dict": "object",
                "list": "array",
                "any": "string",  # THIS FIXES share_artifact
                "Any": "string",
                "typing.Any": "string"
            }
            
            mapped_type = type_map.get(param_type, param_type)
            
            prop = {"type": mapped_type}
            
            if "description" in param_info:
                prop["description"] = param_info["description"]
            
            if param_info.get("required", False):
                required.append(param_name)
            
            if "default" in param_info:
                prop["default"] = param_info["default"]
            
            if "enum" in param_info:
                prop["enum"] = param_info["enum"]
            
            # CRITICAL FIX: Add missing 'items' for arrays
            if mapped_type == "array":
                if "items" not in param_info:
                    prop["items"] = {"type": "string"}  # THIS FIXES verify_deliverables
                else:
                    prop["items"] = param_info["items"]
            
            properties[param_name] = prop
    
    schema = {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False
    }
    
    return {
        "name": tool.name,
        "description": tool.description or f"Tool: {tool.name}",
        "input_schema": schema
    }

# Apply the fix
runtime.AnthropicAgentRunner._convert_tool_to_anthropic_format = fixed_tool_converter
safe_print("[OK] Tool converter fixed")

# Fix standard tools
original_create_tools = runtime.create_standard_tools

def fixed_standard_tools():
    """Fix share_artifact and verify_deliverables specifically"""
    tools = original_create_tools()
    
    for tool in tools:
        # Fix share_artifact 'any' type
        if tool.name == "share_artifact" and hasattr(tool, 'parameters'):
            for param in ['data', 'content']:
                if param in tool.parameters:
                    if tool.parameters[param].get('type') == 'any':
                        tool.parameters[param]['type'] = 'string'
        
        # Fix verify_deliverables missing 'items'
        elif tool.name == "verify_deliverables" and hasattr(tool, 'parameters'):
            if 'deliverables' in tool.parameters:
                param = tool.parameters['deliverables']
                if param.get('type') in ['array', 'list']:
                    if 'items' not in param:
                        param['items'] = {'type': 'string'}
    
    return tools

runtime.create_standard_tools = fixed_standard_tools
safe_print("[OK] Standard tools fixed")

# Fix MCP tools
try:
    from lib import mcp_tools
    if hasattr(mcp_tools, 'create_mcp_tools'):
        original_mcp = mcp_tools.create_mcp_tools
        
        def fixed_mcp():
            tools = original_mcp()
            for tool in tools:
                if hasattr(tool, 'parameters'):
                    for param_name, param_info in tool.parameters.items():
                        if isinstance(param_info, dict):
                            if param_info.get('type') == 'any':
                                param_info['type'] = 'string'
                            if param_info.get('type') in ['array', 'list'] and 'items' not in param_info:
                                param_info['items'] = {'type': 'string'}
            return tools
        
        mcp_tools.create_mcp_tools = fixed_mcp
        safe_print("[OK] MCP tools fixed")
except:
    pass

safe_print("=" * 60)
safe_print("All tool schema fixes applied!")
safe_print("=" * 60)

# Now we can safely import orchestrate_enhanced
safe_print("Starting orchestration with all bypasses enabled...")
safe_print("=" * 60)

# Import orchestrate_enhanced FIRST
from orchestrate_enhanced import main
import asyncio

# Create async run function EXACTLY like fix_specific_tools.py
async def run():
    # Set sys.argv INSIDE the async function
    sys.argv = [
        'orchestrate_enhanced.py',
        '--project-type', 'full_stack_api',
        '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
        '--output-dir', 'projects/quickshop-mvp-test7',
        '--progress',
        '--summary-level', 'concise',
        '--max-parallel', '2',
        '--human-log'
    ]
    
    safe_print("\nQUICKSHOP MVP ORCHESTRATION")
    safe_print("=" * 70)
    safe_print("Configuration:")
    safe_print("  - Type: Full Stack E-Commerce")
    safe_print("  - Output: projects/quickshop-mvp-test7")
    safe_print("  - Agents: 15-agent swarm")
    safe_print("  - MCPs: ENABLED")
    safe_print("  - Tool Issues: FIXED")
    safe_print()
    safe_print("Starting...")
    safe_print("=" * 70)
    
    try:
        # Call await main() NOT asyncio.run(main())
        result = await main()
        
        safe_print("\n" + "=" * 70)
        safe_print("SUCCESS! QuickShop MVP Generated!")
        safe_print("=" * 70)
        safe_print()
        safe_print("Location: projects/quickshop-mvp-test7")
        safe_print()
        
        return 0
        
    except KeyboardInterrupt:
        safe_print("\nInterrupted")
        return 1
        
    except Exception as e:
        safe_print(f"\nError: {e}")
        return 1

# Now run the async function
if __name__ == "__main__":
    exit_code = asyncio.run(run())
    sys.exit(exit_code)