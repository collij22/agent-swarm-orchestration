#!/usr/bin/env python
"""
QUICKSHOP RUNNER - Runs orchestration with all fixes in subprocess
This avoids I/O conflicts by running in a separate process
"""

import sys
import os
import subprocess
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

print("QuickShop MVP Orchestration")
print("=" * 70)

# Apply schema fixes before running
import lib.agent_runtime as runtime

def fix_tool_schema(self, tool):
    """Convert tool to valid JSON Schema"""
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
            
            # Map types
            type_map = {
                "str": "string",
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
                "any": "string"
            }
            
            param_type = type_map.get(param_type, param_type)
            
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

runtime.AnthropicAgentRunner._convert_tool_for_anthropic = fix_tool_schema
print("✓ Schema fixes applied")

# Fix standard tools
original_create = runtime.create_standard_tools
def fixed_create_standard_tools():
    tools = original_create()
    for tool in tools:
        if tool.name == "share_artifact" and hasattr(tool, 'parameters'):
            if 'data' in tool.parameters and tool.parameters['data'].get('type') == 'any':
                tool.parameters['data']['type'] = 'object'
                tool.parameters['data']['additionalProperties'] = True
    return tools
runtime.create_standard_tools = fixed_create_standard_tools

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
                            if param_info.get('type') == 'array' and 'items' not in param_info:
                                param_info['items'] = {'type': 'string'}
            return tools
        mcp_tools.create_mcp_tools = fixed_mcp
        print("✓ MCP fixes applied")
except:
    pass

print("✓ All fixes complete")
print("=" * 70)

# Run orchestration in subprocess
def run_orchestration():
    """Run orchestration in subprocess to avoid I/O conflicts"""
    
    cmd = [
        sys.executable,
        "orchestrate_enhanced.py",
        "--project-type", "full_stack_api",
        "--requirements", "projects/quickshop-mvp-test/requirements.yaml",
        "--output-dir", "projects/quickshop-mvp-test6",
        "--progress",
        "--summary-level", "concise",
        "--max-parallel", "2",
        "--human-log"
    ]
    
    print("\n🚀 Running QuickShop MVP Generation")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  • Type: Full Stack E-Commerce API")
    print("  • Output: projects/quickshop-mvp-test6")
    print("  • Agents: 15-agent swarm")
    print("  • MCPs: ENABLED")
    print()
    print("Starting orchestration...")
    print("=" * 70)
    print()
    
    try:
        # Run in subprocess with proper encoding
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output in real-time
        for line in process.stdout:
            print(line, end='')
        
        # Wait for completion
        return_code = process.wait()
        
        if return_code == 0:
            print("\n" + "=" * 70)
            print("✅ SUCCESS! QuickShop MVP Generated!")
            print("=" * 70)
            print()
            print("Your application is ready at:")
            print("  📁 projects/quickshop-mvp-test6")
            print()
            print("To run the application:")
            print("  1. cd projects/quickshop-mvp-test6")
            print("  2. docker-compose up")
            print()
            print("Access points:")
            print("  • Frontend: http://localhost:3000")
            print("  • Backend API: http://localhost:8000")
            print("  • API Documentation: http://localhost:8000/docs")
            print()
        else:
            print(f"\nOrchestration exited with code {return_code}")
            
        return return_code
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        if process:
            process.terminate()
        return 1
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_orchestration()
    sys.exit(exit_code)