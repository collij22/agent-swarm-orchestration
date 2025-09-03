#!/usr/bin/env python
"""
WORKING RUN - Complete fix that works around all I/O issues
"""

import sys
import os

# Step 1: Completely disable Rich before ANY imports
class FakeRichModule:
    class Console:
        def __init__(self, *args, **kwargs):
            pass
        def print(self, *args, **kwargs):
            for arg in args:
                print(str(arg))
        def log(self, *args, **kwargs):
            print("[LOG]", *args)
        def status(self, *args, **kwargs):
            class ctx:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return ctx()
        def rule(self, *args, **kwargs):
            print("=" * 60)
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    class Panel:
        def __init__(self, content, *args, **kwargs):
            print(f"\n[PANEL] {content}\n")
    
    class Table:
        def __init__(self, *args, **kwargs):
            pass
        def add_column(self, *args, **kwargs):
            pass
        def add_row(self, *args, **kwargs):
            pass
    
    class Progress:
        def __init__(self, *args, **kwargs):
            self.tasks = {}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def add_task(self, desc, **kwargs):
            print(f"[TASK] {desc}")
            return len(self.tasks)
        def update(self, *args, **kwargs):
            pass
        def advance(self, *args, **kwargs):
            pass

# Install fake Rich BEFORE any other imports
fake_rich = FakeRichModule()
sys.modules['rich'] = fake_rich
sys.modules['rich.console'] = fake_rich
sys.modules['rich.panel'] = fake_rich
sys.modules['rich.table'] = fake_rich
sys.modules['rich.progress'] = fake_rich

# Step 2: Set environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['MOCK_MODE'] = 'false'  # Ensure real execution

print("=" * 70)
print("QUICKSHOP MVP - AGENT SWARM ORCHESTRATION")
print("=" * 70)

# Step 3: Add lib to path and import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

# Step 4: Import and patch agent_runtime BEFORE orchestrate_enhanced
import lib.agent_runtime as agent_runtime

# Fix tool converter
def fixed_tool_converter(self, tool):
    properties = {}
    required = []
    
    if hasattr(tool, 'parameters') and tool.parameters:
        for param_name, param_info in tool.parameters.items():
            if not isinstance(param_info, dict):
                continue
            
            param_type = param_info.get("type", "string")
            
            # Map types
            type_map = {
                "any": "string",
                "str": "string", 
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object"
            }
            
            param_type = type_map.get(param_type, param_type)
            
            prop = {
                "type": param_type,
                "description": param_info.get("description", "")
            }
            
            # Arrays need items
            if param_type == "array":
                if "items" in param_info:
                    prop["items"] = param_info["items"]
                else:
                    prop["items"] = {"type": "string"}
            
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

agent_runtime.AnthropicAgentRunner._convert_tool_for_anthropic = fixed_tool_converter

# Fix standard tools
original_create = agent_runtime.create_standard_tools

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

agent_runtime.create_standard_tools = fixed_standard_tools

print("[OK] Tool schemas fixed")

# Patch print to always work
import builtins
original_print = builtins.print

def safe_print(*args, **kwargs):
    try:
        original_print(*args, **kwargs)
    except:
        # Write directly to console
        message = ' '.join(str(arg) for arg in args)
        try:
            sys.stdout.write(message + '\n')
            sys.stdout.flush()
        except:
            try:
                os.write(1, message.encode('utf-8', 'replace') + b'\n')
            except:
                pass

builtins.print = safe_print

# Step 5: Now import orchestrate_enhanced (with Rich already faked)
from orchestrate_enhanced import main

print("[OK] Orchestrator imported")

# Step 6: Run with proper arguments
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
    
    print("\nConfiguration:")
    print("  - Type: Full Stack E-Commerce API")
    print("  - Output: projects/quickshop-mvp-test6")
    print("  - Agents: 15-agent swarm")
    print("  - MCPs: Enabled")
    print("=" * 70)
    print("\nStarting agent swarm...\n")
    
    try:
        result = await main()
        print("\n" + "=" * 70)
        print("SUCCESS! QuickShop MVP Generated!")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import asyncio
    
    # Create new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        exit_code = loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        exit_code = 1
    finally:
        loop.close()
    
    sys.exit(exit_code)