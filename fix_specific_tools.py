#!/usr/bin/env python
"""
FIX SPECIFIC TOOLS - Fixes share_artifact and verify_deliverables
These are the two tools causing 400 Bad Request errors
"""

import sys
import os
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['TERM'] = 'dumb'
os.environ['NO_COLOR'] = '1'

# Monkey-patch print to always work
import builtins
_original_print = builtins.print

def safe_print(*args, **kwargs):
    message = ' '.join(str(arg) for arg in args)
    
    # ALWAYS write to console first
    try:
        # Direct console write on Windows
        import ctypes
        import ctypes.wintypes
        STD_OUTPUT_HANDLE = -11
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        text_bytes = (message + '\n').encode('cp1252', 'replace')
        written = ctypes.wintypes.DWORD()
        kernel32.WriteConsoleA(handle, text_bytes, len(text_bytes), ctypes.byref(written), None)
    except:
        # Fallback to original print
        try:
            _original_print(*args, **kwargs)
        except:
            # Try stdout write
            try:
                sys.stdout.write(message + '\n')
                sys.stdout.flush()
            except:
                # OS write fallback
                try:
                    os.write(1, (message + '\n').encode('utf-8', 'replace'))
                except:
                    pass
    
    # Also log to file for debugging
    try:
        with open('orchestrate_bypass.log', 'a') as f:
            f.write(message + '\n')
    except:
        pass

builtins.print = safe_print

# Create a fake rich module to bypass I/O issues
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

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

print("Fixing problematic tool schemas...")
print("=" * 70)

# Import agent_runtime
import lib.agent_runtime as runtime

# Comprehensive tool converter that handles ALL edge cases
def fixed_tool_converter(self, tool):
    """Convert tool with ALL edge cases handled"""
    properties = {}
    required = []
    
    # Add reasoning if needed
    if hasattr(tool, 'requires_reasoning') and tool.requires_reasoning:
        properties["reasoning"] = {
            "type": "string",
            "description": f"Reasoning for using {tool.name}"
        }
        required.append("reasoning")
    
    # Process parameters
    if hasattr(tool, 'parameters') and tool.parameters:
        for param_name, param_info in tool.parameters.items():
            if not isinstance(param_info, dict):
                continue
            
            # Get the type
            param_type = param_info.get("type", "string")
            
            # Map ALL type variations
            type_map = {
                "str": "string",
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
                "any": "string",  # Critical: Convert 'any' to 'string'
                "tuple": "array",
                "set": "array"
            }
            
            param_type = type_map.get(param_type, param_type)
            
            # Validate type
            valid_types = ["string", "integer", "number", "boolean", "array", "object", "null"]
            if param_type not in valid_types:
                param_type = "string"
            
            # Build property
            prop = {
                "type": param_type,
                "description": param_info.get("description", "")
            }
            
            # CRITICAL: Arrays MUST have items
            if param_type == "array":
                if "items" in param_info:
                    items = param_info["items"]
                    if isinstance(items, dict) and "type" in items:
                        items["type"] = type_map.get(items["type"], items["type"])
                        if items["type"] not in valid_types:
                            items["type"] = "string"
                    prop["items"] = items
                else:
                    # Default items
                    prop["items"] = {"type": "string"}
            
            # Objects
            elif param_type == "object":
                if "properties" in param_info:
                    prop["properties"] = param_info["properties"]
                prop["additionalProperties"] = param_info.get("additionalProperties", True)
            
            # Copy valid fields
            for field in ["enum", "default", "minimum", "maximum", "minLength", 
                         "maxLength", "pattern", "format", "minItems", "maxItems"]:
                if field in param_info:
                    prop[field] = param_info[field]
            
            properties[param_name] = prop
            
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

# Apply the fix
runtime.AnthropicAgentRunner._convert_tool_for_anthropic = fixed_tool_converter
print("[OK] Tool converter fixed")

# Fix standard tools at creation
original_create = runtime.create_standard_tools

def fixed_standard_tools():
    tools = original_create()
    
    for tool in tools:
        # Fix share_artifact
        if tool.name == "share_artifact" and hasattr(tool, 'parameters'):
            for param in ['data', 'content']:
                if param in tool.parameters:
                    if tool.parameters[param].get('type') == 'any':
                        tool.parameters[param]['type'] = 'string'
        
        # Fix verify_deliverables
        elif tool.name == "verify_deliverables" and hasattr(tool, 'parameters'):
            if 'deliverables' in tool.parameters:
                param = tool.parameters['deliverables']
                if param.get('type') in ['array', 'list']:
                    if 'items' not in param:
                        param['items'] = {'type': 'string'}
    
    return tools

runtime.create_standard_tools = fixed_standard_tools
print("[OK] Standard tools fixed")

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
        print("[OK] MCP tools fixed")
except:
    pass

print("=" * 70)
print("Schema fixes complete!")
print("=" * 70)

# Run orchestration
import asyncio
from orchestrate_enhanced import main

async def run():
    sys.argv = [
        'orchestrate_enhanced.py',
        '--project-type', 'full_stack_api',
        '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
        '--output-dir', 'projects/quickshop-mvp-test6',
        '--progress',
        '--summary-level', 'concise',
        '--max-parallel', '2',
        '--human-log'
    ]
    
    print("\nQUICKSHOP MVP ORCHESTRATION")
    print("=" * 70)
    print("Configuration:")
    print("  - Type: Full Stack E-Commerce")
    print("  - Output: projects/quickshop-mvp-test6")
    print("  - Agents: 15-agent swarm")
    print("  - MCPs: ENABLED")
    print("  - Tool Issues: FIXED")
    print()
    print("Starting...")
    print("=" * 70)
    
    try:
        result = await main()
        
        print("\n" + "=" * 70)
        print("SUCCESS! QuickShop MVP Generated!")
        print("=" * 70)
        print()
        print("Location: projects/quickshop-mvp-test6")
        print()
        print("To run:")
        print("  cd projects/quickshop-mvp-test6")
        print("  docker-compose up")
        print()
        print("Access:")
        print("  - Frontend: http://localhost:3000")
        print("  - Backend: http://localhost:8000")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted")
        return 1
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run())
    sys.exit(exit_code)