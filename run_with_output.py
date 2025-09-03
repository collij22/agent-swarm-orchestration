#!/usr/bin/env python
"""
RUN WITH OUTPUT - Forces all agent output to console
"""

import sys
import os
from pathlib import Path
import ctypes
import ctypes.wintypes

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['TERM'] = 'dumb'
os.environ['NO_COLOR'] = '1'

# Force Windows console output
def force_print(text):
    """Direct Windows console output that ALWAYS works"""
    try:
        # Windows kernel32 direct write
        STD_OUTPUT_HANDLE = -11
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        text_bytes = str(text).encode('cp1252', 'replace')
        written = ctypes.wintypes.DWORD()
        kernel32.WriteConsoleA(handle, text_bytes, len(text_bytes), ctypes.byref(written), None)
    except:
        # Fallback to OS write
        try:
            os.write(1, str(text).encode('ascii', 'replace'))
        except:
            pass

# Override print globally
import builtins
builtins.print = lambda *args, **kwargs: force_print(' '.join(str(a) for a in args) + '\n')

print("Initializing Agent Swarm...")
print("=" * 70)

# Create comprehensive fake Rich that shows agent messages
class FakePanel:
    def __init__(self, content, title="", border_style="", **kwargs):
        if title:
            print(f"\n*** {title} ***")
        print("-" * 60)
        if isinstance(content, str):
            # Remove Rich markup
            import re
            content = re.sub(r'\[/?[^\\]+\]', '', content)
            for line in content.split('\n'):
                if line.strip():
                    print(line)
        else:
            print(str(content))
        print("-" * 60)

class FakeConsole:
    def print(self, *args, **kwargs):
        for arg in args:
            if hasattr(arg, '__class__') and arg.__class__.__name__ == 'Panel':
                # This is a Panel object, extract its content
                pass  # Panel prints itself in __init__
            else:
                print(str(arg))
    
    def log(self, *args, **kwargs):
        print("[LOG]", *args)
    
    def status(self, message="", **kwargs):
        print(f"[STATUS] {message}")
        from contextlib import nullcontext
        return nullcontext()
    
    def rule(self, title="", **kwargs):
        print("\n" + "=" * 60)
        if title:
            print(f"  {title}")
        print("=" * 60)
    
    def __getattr__(self, name):
        def method(*args, **kwargs):
            if args:
                print(f"[{name.upper()}]", *args)
        return method

class FakeProgress:
    def __init__(self, *args, **kwargs):
        self.tasks = {}
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def add_task(self, description, **kwargs):
        task_id = len(self.tasks)
        self.tasks[task_id] = description
        print(f">>> Task Started: {description}")
        return task_id
    def update(self, task_id, **kwargs):
        if task_id in self.tasks:
            if 'description' in kwargs:
                print(f"    Task Update: {kwargs['description']}")
    def advance(self, task_id, advance=1):
        if task_id in self.tasks:
            print(f"    Task Progress: {self.tasks[task_id]}")

class FakeTable:
    def __init__(self, title="", **kwargs):
        self.title = title
        self.columns = []
        self.rows = []
    def add_column(self, name, **kwargs):
        self.columns.append(name)
    def add_row(self, *values, **kwargs):
        self.rows.append(values)
        print(" | ".join(str(v) for v in values))

# Create the fake Rich module
class FakeRich:
    Console = FakeConsole
    Panel = FakePanel
    Table = FakeTable
    Progress = FakeProgress
    
    class console:
        Console = FakeConsole
    class panel:
        Panel = FakePanel
    class table:
        Table = FakeTable
    class progress:
        Progress = FakeProgress

# Install fake Rich BEFORE any imports
fake_rich = FakeRich()
sys.modules['rich'] = fake_rich
sys.modules['rich.console'] = fake_rich.console
sys.modules['rich.panel'] = fake_rich.panel
sys.modules['rich.table'] = fake_rich.table
sys.modules['rich.progress'] = fake_rich.progress

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# CRITICAL: Patch agent_logger BEFORE it's imported by anyone
import importlib.util
spec = importlib.util.spec_from_file_location("agent_logger", "lib/agent_logger.py")
agent_logger = importlib.util.module_from_spec(spec)

# Replace the console in agent_logger BEFORE execution
agent_logger.console = FakeConsole()
sys.modules['lib.agent_logger'] = agent_logger
sys.modules['agent_logger'] = agent_logger

# Now execute the module (this will use our fake console)
spec.loader.exec_module(agent_logger)

print("[OK] Agent logger patched with console output")

# Import agent_runtime
import lib.agent_runtime as runtime

# Tool converter fix
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
print("[OK] Tool converter fixed")

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
print("All patches applied successfully!")
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
    print("Type: Full Stack E-Commerce")
    print("Output: projects/quickshop-mvp-test6")
    print("Agents: 15-agent swarm")
    print("MCPs: All enabled")
    print("=" * 70)
    print("\nStarting agents...\n")
    
    try:
        result = await main()
        
        print("\n" + "=" * 70)
        print("ORCHESTRATION COMPLETE!")
        print("=" * 70)
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Use new event loop to avoid issues
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        exit_code = loop.run_until_complete(run())
    finally:
        loop.close()
    sys.exit(exit_code)