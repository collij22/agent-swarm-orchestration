#!/usr/bin/env python
"""
WORKING FINAL - Fixes Unicode encoding issues and shows agent output
"""

import sys
import os
from pathlib import Path
import logging

# Configure environment for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Suppress noisy INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("lib.workflow_loader").setLevel(logging.WARNING)
logging.getLogger("lib.mcp_manager").setLevel(logging.WARNING)

# Create a safe print that handles Unicode
import builtins
_original_print = builtins.print

def safe_print(*args, **kwargs):
    """Print that safely handles Unicode on Windows"""
    try:
        # Join args into message
        message = ' '.join(str(arg) for arg in args)
        
        # Remove problematic Unicode characters
        message = message.encode('ascii', 'ignore').decode('ascii')
        
        # Try normal print
        _original_print(message, **kwargs)
    except:
        # Fallback - write directly
        try:
            safe_msg = ' '.join(str(arg).encode('ascii', 'ignore').decode('ascii') for arg in args)
            sys.stdout.write(safe_msg + '\n')
            sys.stdout.flush()
        except:
            pass

builtins.print = safe_print

print("=" * 70)
print("QUICKSHOP MVP - AGENT SWARM ORCHESTRATION")
print("=" * 70)

# Create Rich replacement that strips Unicode
class SafePanel:
    def __init__(self, content, title="", **kwargs):
        # Strip Unicode from title and content
        if title:
            title = str(title).encode('ascii', 'replace').decode('ascii')
            print(f"\n{'='*70}")
            print(f"[AGENT: {title}]")
            print("-"*70)
        else:
            print(f"\n{'='*70}")
        
        # Handle content - remove Unicode
        content_str = str(content) if hasattr(content, '__str__') else repr(content)
        
        # Remove Rich markup AND Unicode
        import re
        content_str = re.sub(r'\[/?[^\\]+\]', '', content_str)
        content_str = content_str.encode('ascii', 'replace').decode('ascii')
        
        # Print content
        lines = content_str.split('\n')
        for line in lines[:30]:  # Show first 30 lines
            if line.strip():
                print(line[:200])  # Limit line length
        
        if len(lines) > 30:
            print(f"... ({len(lines)-30} more lines)")
        print("="*70)

class SafeConsole:
    def __init__(self, *args, **kwargs):
        pass
        
    def print(self, *args, **kwargs):
        """Main output method - strips Unicode"""
        for arg in args:
            if hasattr(arg, '__class__') and 'Panel' in arg.__class__.__name__:
                # Panel prints itself
                pass
            else:
                # Strip Unicode and print
                output = str(arg).encode('ascii', 'replace').decode('ascii')
                if output and not output.isspace():
                    print(output)
    
    def log(self, *args, **kwargs):
        safe_args = [str(a).encode('ascii', 'replace').decode('ascii') for a in args]
        print("[LOG]", *safe_args)
    
    def status(self, message="", **kwargs):
        safe_msg = str(message).encode('ascii', 'replace').decode('ascii')
        print(f"\n[STATUS] {safe_msg}")
        class StatusContext:
            def __enter__(self): return self
            def __exit__(self, *args): print(f"[DONE] {safe_msg}\n")
        return StatusContext()
    
    def rule(self, title="", **kwargs):
        if title:
            safe_title = str(title).encode('ascii', 'replace').decode('ascii')
            print(f"\n{'-'*20} {safe_title} {'-'*20}")
        else:
            print("-"*70)
    
    def __getattr__(self, name):
        def method(*args, **kwargs):
            if args and name not in ['clear', 'show_cursor', 'hide_cursor']:
                safe_args = [str(a).encode('ascii', 'replace').decode('ascii') for a in args]
                print(f"[{name.upper()}]", *safe_args)
        return method

class SafeProgress:
    def __init__(self, *args, **kwargs):
        self.tasks = {}
        self.task_counter = 0
        
    def __enter__(self):
        print("\n[PROGRESS TRACKING STARTED]")
        return self
        
    def __exit__(self, *args):
        print("[PROGRESS TRACKING COMPLETE]\n")
        
    def add_task(self, description, total=None, **kwargs):
        task_id = self.task_counter
        self.task_counter += 1
        safe_desc = str(description).encode('ascii', 'replace').decode('ascii')
        self.tasks[task_id] = {
            'description': safe_desc,
            'completed': 0,
            'total': total
        }
        print(f"  > Task: {safe_desc}")
        return task_id
        
    def update(self, task_id, description=None, completed=None, **kwargs):
        if task_id in self.tasks:
            if description:
                safe_desc = str(description).encode('ascii', 'replace').decode('ascii')
                self.tasks[task_id]['description'] = safe_desc
                print(f"  > Update: {safe_desc}")
            if completed is not None:
                self.tasks[task_id]['completed'] = completed
                total = self.tasks[task_id].get('total')
                if total:
                    percent = (completed / total) * 100
                    print(f"  > Progress: {percent:.1f}%")
                    
    def advance(self, task_id, advance=1):
        if task_id in self.tasks:
            self.tasks[task_id]['completed'] += advance
            desc = self.tasks[task_id]['description']
            print(f"  > Advanced: {desc}")

class SafeTable:
    def __init__(self, title="", **kwargs):
        if title:
            safe_title = str(title).encode('ascii', 'replace').decode('ascii')
            print(f"\n[TABLE: {safe_title}]")
        self.columns = []
        self.rows = []
            
    def add_column(self, name, **kwargs):
        self.columns.append(name)
        
    def add_row(self, *values, **kwargs):
        self.rows.append(values)
        safe_values = [str(v).encode('ascii', 'replace').decode('ascii')[:20] for v in values]
        print("  " + " | ".join(safe_values))

# Create fake Rich module
class FakeRich:
    Console = SafeConsole
    Panel = SafePanel
    Table = SafeTable
    Progress = SafeProgress
    
    class console:
        Console = SafeConsole
    class panel:
        Panel = SafePanel
    class table:
        Table = SafeTable
    class progress:
        Progress = SafeProgress
        SpinnerColumn = lambda: None
        TextColumn = lambda *a, **k: None
        BarColumn = lambda: None
        TimeElapsedColumn = lambda: None

# Install fake Rich BEFORE any imports
fake_rich = FakeRich()
sys.modules['rich'] = fake_rich
sys.modules['rich.console'] = fake_rich.console
sys.modules['rich.panel'] = fake_rich.panel
sys.modules['rich.table'] = fake_rich.table
sys.modules['rich.progress'] = fake_rich.progress

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

print("Initializing Agent Swarm...")
print("-" * 70)

# Import and patch agent_runtime
import lib.agent_runtime as runtime

# Fix tool converter
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

# CRITICAL: Also patch agent execution to strip Unicode
original_execute = runtime.AnthropicAgentRunner._execute_tool

async def safe_execute_tool(self, tool, args, context):
    """Execute tool with Unicode-safe output"""
    # Strip Unicode from args if they're strings
    safe_args = {}
    for key, value in args.items():
        if isinstance(value, str):
            safe_args[key] = value.encode('ascii', 'replace').decode('ascii')
        else:
            safe_args[key] = value
    
    # Call original with safe args
    result = await original_execute(self, tool, safe_args, context)
    
    # Strip Unicode from result if it's a string
    if isinstance(result, str):
        result = result.encode('ascii', 'replace').decode('ascii')
    
    return result

runtime.AnthropicAgentRunner._execute_tool = safe_execute_tool

print("[OK] Unicode safety patches applied")
print("-" * 70)
print("All patches applied successfully!")
print("=" * 70)

# Import orchestrator
from orchestrate_enhanced import main

# Run orchestration
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
    
    print("\nQUICKSHOP MVP CONFIGURATION")
    print("=" * 70)
    print("Type: Full Stack E-Commerce")
    print("Output: projects/quickshop-mvp-test6")
    print("Agents: 15-agent swarm")
    print("MCPs: ENABLED")
    print("Parallel: 2 agents max")
    print("=" * 70)
    print("\nStarting agent swarm...\n")
    
    try:
        result = await main()
        
        print("\n" + "=" * 70)
        print("SUCCESS! QuickShop MVP Generated!")
        print("=" * 70)
        print("\nLocation: projects/quickshop-mvp-test6")
        print("\nTo run:")
        print("  cd projects/quickshop-mvp-test6")
        print("  docker-compose up")
        print("\nAccess:")
        print("  - Frontend: http://localhost:3000")
        print("  - Backend: http://localhost:8000")
        print("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
        
    except UnicodeEncodeError as e:
        print(f"\nUnicode error (fixing): {e}")
        return 1
        
    except Exception as e:
        # Strip Unicode from error message
        safe_error = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"\nError: {safe_error}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Create new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        exit_code = loop.run_until_complete(run())
    finally:
        loop.close()
    
    sys.exit(exit_code)