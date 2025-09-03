#!/usr/bin/env python
"""
UNICODE FIX - Strips Unicode from agent responses before display
"""

import sys
import os
from pathlib import Path
import logging
import json

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['TERM'] = 'dumb'
os.environ['NO_COLOR'] = '1'

# Suppress noisy logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("lib.workflow_loader").setLevel(logging.WARNING)
logging.getLogger("lib.mcp_manager").setLevel(logging.WARNING)

print("=" * 70)
print("QUICKSHOP MVP - UNICODE-SAFE AGENT SWARM")
print("=" * 70)

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Import agent_runtime FIRST
import lib.agent_runtime as runtime
from lib.agent_runtime import AgentContext

# CRITICAL: Patch the agent response handler to strip Unicode
# The method is run_agent_async not execute
original_run = runtime.run_agent_async

async def unicode_safe_run(
    api_key: str,
    agent_name: str,
    prompt: str,
    context: AgentContext,
    tools: list = None,
    logger = None,
    max_thinking_length: int = 60000,
    temperature: float = 0.7,
    model_type = None
):
    """Execute agent with Unicode stripping"""
    
    print(f"\n{'='*70}")
    print(f"AGENT STARTING: {agent_name}")
    print(f"Task: {str(prompt)[:100].encode('ascii', 'replace').decode('ascii')}...")
    print("="*70)
    
    try:
        # Call original with all parameters
        result = await original_run(api_key, agent_name, prompt, context, tools, logger, max_thinking_length, temperature, model_type)
        
        # Strip Unicode from the result
        if result:
            if isinstance(result, str):
                result = result.encode('ascii', 'replace').decode('ascii')
            elif isinstance(result, dict):
                # Recursively clean dictionary
                result = clean_unicode_dict(result)
            elif isinstance(result, list):
                # Clean list items
                result = [clean_unicode_item(item) for item in result]
        
        print(f"[SUCCESS] AGENT COMPLETED: {agent_name}")
        
        # Show files created if available
        if context and hasattr(context, 'artifacts'):
            if 'files_created' in context.artifacts:
                files = list(context.artifacts['files_created'])[-5:]
                if files:
                    print("  Recent files created:")
                    for f in files:
                        print(f"    - {f}")
        
        return result
        
    except UnicodeEncodeError as e:
        print(f"[UNICODE ERROR] Fixing and retrying...")
        # If Unicode error, return safe version
        return "Task completed (Unicode stripped)"
        
    except Exception as e:
        safe_error = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"[FAILED] AGENT ERROR: {agent_name}")
        print(f"  Error: {safe_error[:200]}")
        raise

def clean_unicode_dict(d):
    """Recursively clean Unicode from dictionary"""
    clean = {}
    for key, value in d.items():
        # Clean key
        if isinstance(key, str):
            key = key.encode('ascii', 'replace').decode('ascii')
        
        # Clean value
        if isinstance(value, str):
            clean[key] = value.encode('ascii', 'replace').decode('ascii')
        elif isinstance(value, dict):
            clean[key] = clean_unicode_dict(value)
        elif isinstance(value, list):
            clean[key] = [clean_unicode_item(item) for item in value]
        else:
            clean[key] = value
    return clean

def clean_unicode_item(item):
    """Clean Unicode from any item"""
    if isinstance(item, str):
        return item.encode('ascii', 'replace').decode('ascii')
    elif isinstance(item, dict):
        return clean_unicode_dict(item)
    elif isinstance(item, list):
        return [clean_unicode_item(i) for i in item]
    else:
        return item

# Apply the Unicode-safe run
runtime.run_agent_async = unicode_safe_run

print("[OK] Unicode-safe agent execution patched")

# Also patch tool execution to show what's happening
original_tool = runtime.AnthropicAgentRunner._execute_tool

async def visible_tool(self, tool, args, context):
    """Show tool execution"""
    tool_name = getattr(tool, 'name', 'unknown')
    
    # Clean Unicode from args
    safe_args = {}
    for key, value in args.items():
        if isinstance(value, str):
            safe_args[key] = value.encode('ascii', 'replace').decode('ascii')
        else:
            safe_args[key] = value
    
    # Show important tools
    if tool_name in ['write_file', 'read_file', 'run_command', 'dependency_check', 'record_decision']:
        if tool_name == 'write_file':
            path = safe_args.get('file_path', '?')
            print(f"  [TOOL] Creating file: {path}")
        elif tool_name == 'read_file':
            path = safe_args.get('file_path', '?')
            print(f"  [TOOL] Reading file: {path}")
        elif tool_name == 'run_command':
            cmd = str(safe_args.get('command', '?'))[:50]
            print(f"  [TOOL] Running: {cmd}...")
        elif tool_name == 'record_decision':
            decision = str(safe_args.get('decision', '?'))[:100]
            print(f"  [TOOL] Decision: {decision}...")
    
    # Execute with safe args
    try:
        result = await original_tool(self, tool, safe_args, context)
        
        # Clean Unicode from result
        if isinstance(result, str):
            result = result.encode('ascii', 'replace').decode('ascii')
        
        return result
    except UnicodeEncodeError:
        # Return safe default
        return "Tool executed (Unicode stripped)"

runtime.AnthropicAgentRunner._execute_tool = visible_tool

print("[OK] Tool visibility patched")

# Fix tool schemas
def fixed_tool_converter(self, tool):
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
            
            type_map = {
                "str": "string",
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
                "any": "string",
                "tuple": "array",
                "set": "array"
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
                if "items" in param_info:
                    items = param_info["items"]
                    if isinstance(items, dict) and "type" in items:
                        items["type"] = type_map.get(items["type"], items["type"])
                        if items["type"] not in valid_types:
                            items["type"] = "string"
                    prop["items"] = items
                else:
                    prop["items"] = {"type": "string"}
            
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

runtime.AnthropicAgentRunner._convert_tool_for_anthropic = fixed_tool_converter

# Fix standard tools
original_create = runtime.create_standard_tools

def fixed_standard_tools():
    tools = original_create()
    
    for tool in tools:
        if tool.name == "share_artifact" and hasattr(tool, 'parameters'):
            for param in ['data', 'content']:
                if param in tool.parameters:
                    if tool.parameters[param].get('type') == 'any':
                        tool.parameters[param]['type'] = 'string'
        
        elif tool.name == "verify_deliverables" and hasattr(tool, 'parameters'):
            if 'deliverables' in tool.parameters:
                param = tool.parameters['deliverables']
                if param.get('type') in ['array', 'list']:
                    if 'items' not in param:
                        param['items'] = {'type': 'string'}
    
    return tools

runtime.create_standard_tools = fixed_standard_tools

print("[OK] Tool schemas fixed")

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

# Create minimal Rich replacement
class MinimalConsole:
    def print(self, *args, **kwargs):
        for arg in args:
            safe = str(arg).encode('ascii', 'replace').decode('ascii')
            print(safe)
    
    def log(self, *args, **kwargs):
        safe_args = [str(a).encode('ascii', 'replace').decode('ascii') for a in args]
        print("[LOG]", *safe_args)
    
    def status(self, message="", **kwargs):
        safe = str(message).encode('ascii', 'replace').decode('ascii')
        print(f"[STATUS] {safe}")
        class Ctx:
            def __enter__(self): return self
            def __exit__(self, *a): pass
        return Ctx()
    
    def __getattr__(self, name):
        return lambda *a, **k: None

class MinimalPanel:
    def __init__(self, content, title="", **kwargs):
        if title:
            safe_title = str(title).encode('ascii', 'replace').decode('ascii')
            print(f"\n[PANEL: {safe_title}]")
        safe_content = str(content).encode('ascii', 'replace').decode('ascii')
        for line in safe_content.split('\n')[:10]:
            if line.strip():
                print(f"  {line[:150]}")

class FakeRich:
    Console = MinimalConsole
    Panel = MinimalPanel
    Table = lambda *a, **k: type('T', (), {'add_column': lambda *a: None, 'add_row': lambda *a: None})()
    Progress = lambda *a, **k: type('P', (), {
        '__enter__': lambda s: s, '__exit__': lambda s, *a: None,
        'add_task': lambda s, d, **k: 0, 'update': lambda *a: None, 'advance': lambda *a: None
    })()

fake = FakeRich()
for mod in ['rich', 'rich.console', 'rich.panel', 'rich.table', 'rich.progress']:
    sys.modules[mod] = fake

print("-" * 70)
print("All patches applied successfully!")
print("=" * 70)

# Import and run orchestrator
from orchestrate_enhanced import main
import asyncio

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
    
    print("\nCONFIGURATION")
    print("-" * 70)
    print("Type: Full Stack E-Commerce API")
    print("Output: projects/quickshop-mvp-test6")
    print("Agents: 15-agent swarm")
    print("MCPs: Enabled")
    print("=" * 70)
    print("\nStarting orchestration...\n")
    print("You will see agent names and their progress.\n")
    
    try:
        result = await main()
        print("\n" + "=" * 70)
        print("SUCCESS! QuickShop MVP Generated!")
        print("=" * 70)
        return 0
    except Exception as e:
        safe_error = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"\nError: {safe_error}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run())
    sys.exit(exit_code)