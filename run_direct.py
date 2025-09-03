#!/usr/bin/env python
"""
RUN DIRECT - Minimal runner that shows agent execution
"""

import sys
import os
from pathlib import Path

# Basic environment setup
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

print("Starting QuickShop MVP Agent Swarm...")
print("=" * 70)

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Disable Rich completely by making it raise ImportError
import builtins
original_import = builtins.__import__

def custom_import(name, *args, **kwargs):
    if 'rich' in name:
        # Create a minimal fake module
        class FakeMod:
            def __getattr__(self, item):
                if item == 'Console':
                    return lambda *a, **k: type('FC', (), {
                        'print': lambda self, *a, **k: print(*[str(x) for x in a]),
                        'log': lambda self, *a, **k: print('[LOG]', *a),
                        'status': lambda self, *a, **k: type('ctx', (), {'__enter__': lambda s: s, '__exit__': lambda s, *a: None})(),
                        'rule': lambda self, *a, **k: print('=' * 60),
                        '__getattr__': lambda self, n: lambda *a, **k: None
                    })()
                elif item == 'Panel':
                    return lambda c, **k: print(f"\n[AGENT OUTPUT]\n{c}\n")
                elif item == 'Table':
                    return type('FT', (), {'add_column': lambda *a, **k: None, 'add_row': lambda *a, **k: None})
                elif item == 'Progress':
                    return lambda *a, **k: type('FP', (), {
                        '__enter__': lambda s: s,
                        '__exit__': lambda s, *a: None,
                        'add_task': lambda s, d, **k: (print(f"Task: {d}"), 0)[1],
                        'update': lambda s, *a, **k: None,
                        'advance': lambda s, *a, **k: None
                    })()
                return lambda *a, **k: None
        
        fake = FakeMod()
        sys.modules[name] = fake
        return fake
    
    return original_import(name, *args, **kwargs)

builtins.__import__ = custom_import

# Now we can import and patch
import lib.agent_runtime as runtime

# Apply the tool fixes
def fixed_tool_converter(self, tool):
    properties = {}
    required = []
    
    if hasattr(tool, 'parameters') and tool.parameters:
        for param_name, param_info in tool.parameters.items():
            if not isinstance(param_info, dict):
                continue
            
            param_type = param_info.get("type", "string")
            
            # Fix type mapping
            type_map = {
                "any": "string",
                "str": "string",
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
            }
            
            param_type = type_map.get(param_type, param_type)
            
            prop = {"type": param_type}
            if "description" in param_info:
                prop["description"] = param_info["description"]
            
            # Arrays need items
            if param_type == "array" and "items" not in param_info:
                prop["items"] = {"type": "string"}
            elif param_type == "array" and "items" in param_info:
                prop["items"] = param_info["items"]
            
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

# Fix tools
original_create = runtime.create_standard_tools

def fixed_standard_tools():
    tools = original_create()
    for tool in tools:
        if tool.name == "share_artifact" and hasattr(tool, 'parameters'):
            for param in ['data', 'content']:
                if param in tool.parameters and tool.parameters[param].get('type') == 'any':
                    tool.parameters[param]['type'] = 'string'
        elif tool.name == "verify_deliverables" and hasattr(tool, 'parameters'):
            if 'deliverables' in tool.parameters:
                param = tool.parameters['deliverables']
                if param.get('type') in ['array', 'list'] and 'items' not in param:
                    param['items'] = {'type': 'string'}
    return tools

runtime.create_standard_tools = fixed_standard_tools

# Hook into agent execution to show progress
original_execute = runtime.AnthropicAgentRunner.execute

async def logged_execute(self, prompt, context=None):
    agent_name = getattr(self, 'name', 'Unknown')
    print(f"\n>>> AGENT STARTING: {agent_name}")
    print(f"    Task: {prompt[:100]}..." if len(prompt) > 100 else f"    Task: {prompt}")
    
    try:
        result = await original_execute(self, prompt, context)
        print(f"<<< AGENT COMPLETED: {agent_name}")
        return result
    except Exception as e:
        print(f"!!! AGENT FAILED: {agent_name} - {e}")
        raise

runtime.AnthropicAgentRunner.execute = logged_execute

print("Patches applied successfully!")
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
    print("Configuration:")
    print("  - Output: projects/quickshop-mvp-test6")
    print("  - Agents: 15-agent swarm")
    print("  - MCPs: Enabled")
    print("=" * 70)
    print("\nStarting orchestration...\n")
    
    result = await main()
    
    print("\n" + "=" * 70)
    print("ORCHESTRATION COMPLETE!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        exit_code = 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    
    sys.exit(exit_code)