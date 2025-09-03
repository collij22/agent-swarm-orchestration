#!/usr/bin/env python
"""
FINAL FIX - Shows all agent execution in console
"""

import sys
import os
import threading
import time

# Step 1: Create a comprehensive Rich replacement that SHOWS everything
class FakePanel:
    def __init__(self, content, title="", border_style="", **kwargs):
        # Extract actual content and display it
        print("\n" + "="*70)
        if title:
            print(f"*** {title} ***")
        
        # Handle content - could be string or object
        if hasattr(content, '__str__'):
            content_str = str(content)
        else:
            content_str = repr(content)
        
        # Remove Rich markup
        import re
        content_str = re.sub(r'\[/?[^\]]+\]', '', content_str)
        
        # Print the content
        for line in content_str.split('\n'):
            if line.strip():
                print(line)
        print("="*70)

class FakeConsole:
    def __init__(self, *args, **kwargs):
        self.file = kwargs.get('file', sys.stdout)
        
    def print(self, *args, **kwargs):
        """This is where agent messages come through!"""
        for arg in args:
            if arg.__class__.__name__ == 'Panel':
                # Panel already printed in its __init__
                pass
            elif hasattr(arg, '__rich_console__'):
                # This is a Rich renderable, extract its content
                print(f"[AGENT OUTPUT] {str(arg)}")
            else:
                # Regular print
                print(str(arg))
    
    def log(self, *args, **kwargs):
        print("[LOG]", *[str(a) for a in args])
    
    def status(self, message="", **kwargs):
        print(f"\n[STATUS] {message}")
        class StatusContext:
            def __enter__(self): return self
            def __exit__(self, *args): print(f"[STATUS DONE] {message}\n")
        return StatusContext()
    
    def rule(self, title="", **kwargs):
        print("\n" + "="*70)
        if title:
            print(f"  {title}")
        print("="*70)
    
    def __getattr__(self, name):
        def method(*args, **kwargs):
            if args:
                print(f"[CONSOLE.{name.upper()}]", *[str(a) for a in args])
        return method

class FakeProgress:
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
        self.tasks[task_id] = {
            'description': description,
            'completed': 0,
            'total': total
        }
        print(f">>> TASK STARTED: {description}")
        return task_id
        
    def update(self, task_id, description=None, completed=None, **kwargs):
        if task_id in self.tasks:
            if description:
                self.tasks[task_id]['description'] = description
                print(f"    TASK UPDATE: {description}")
            if completed is not None:
                self.tasks[task_id]['completed'] = completed
                total = self.tasks[task_id].get('total')
                if total:
                    percent = (completed / total) * 100
                    print(f"    PROGRESS: {percent:.1f}% - {self.tasks[task_id]['description']}")
                    
    def advance(self, task_id, advance=1):
        if task_id in self.tasks:
            self.tasks[task_id]['completed'] += advance
            desc = self.tasks[task_id]['description']
            completed = self.tasks[task_id]['completed']
            total = self.tasks[task_id].get('total')
            if total:
                percent = (completed / total) * 100
                print(f"    PROGRESS: {percent:.1f}% - {desc}")
            else:
                print(f"    PROGRESS: Step {completed} - {desc}")

class FakeTable:
    def __init__(self, title="", **kwargs):
        self.title = title
        self.columns = []
        self.rows = []
        if title:
            print(f"\n[TABLE: {title}]")
            
    def add_column(self, name, **kwargs):
        self.columns.append(name)
        
    def add_row(self, *values, **kwargs):
        self.rows.append(values)
        # Print the row immediately
        row_str = " | ".join(str(v) for v in values)
        print(f"  {row_str}")

# Create fake Rich module
class FakeRich:
    Console = FakeConsole
    Panel = FakePanel
    Table = FakeTable
    Progress = FakeProgress
    
    # Also create submodules
    class console:
        Console = FakeConsole
    class panel:
        Panel = FakePanel
    class table:
        Table = FakeTable
    class progress:
        Progress = FakeProgress
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

# Environment setup
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['MOCK_MODE'] = 'false'

print("="*70)
print("QUICKSHOP MVP - AGENT SWARM ORCHESTRATION")
print("="*70)

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

# Import and patch agent_runtime
import lib.agent_runtime as agent_runtime

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
                "any": "string",
                "str": "string", 
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
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

# CRITICAL: Intercept agent execution
original_execute_tool = agent_runtime.AnthropicAgentRunner._execute_tool

async def logged_execute_tool(self, tool, args, context):
    """Show tool execution in console"""
    tool_name = getattr(tool, 'name', 'unknown')
    
    # Show tool execution
    if tool_name in ['write_file', 'read_file', 'run_command', 'run_tests']:
        # Important tools - show details
        print(f"\n  [TOOL: {tool_name}]")
        if tool_name == 'write_file':
            print(f"    Creating: {args.get('file_path', 'unknown')}")
        elif tool_name == 'read_file':
            print(f"    Reading: {args.get('file_path', 'unknown')}")
        elif tool_name == 'run_command':
            print(f"    Running: {args.get('command', 'unknown')[:50]}...")
    
    result = await original_execute_tool(self, tool, args, context)
    
    return result

agent_runtime.AnthropicAgentRunner._execute_tool = logged_execute_tool

# Also monitor log file for agent messages
def monitor_log():
    """Monitor the bypass log for agent activity"""
    if not os.path.exists('orchestrate_bypass.log'):
        return
        
    last_pos = 0
    last_size = 0
    
    while True:
        try:
            current_size = os.path.getsize('orchestrate_bypass.log')
            if current_size > last_size:
                with open('orchestrate_bypass.log', 'r', encoding='utf-8', errors='replace') as f:
                    f.seek(last_pos)
                    new_content = f.read()
                    
                    # Look for agent-related content
                    for line in new_content.split('\n'):
                        if 'Agent:' in line or 'AGENT' in line or '>>>' in line:
                            print(f"[FROM LOG] {line}")
                    
                    last_pos = f.tell()
                    last_size = current_size
                    
        except:
            pass
        
        time.sleep(0.5)

# Start log monitor in background
log_thread = threading.Thread(target=monitor_log)
log_thread.daemon = True
log_thread.start()

print("[OK] Agent execution monitor started")

# Import orchestrator
from orchestrate_enhanced import main

print("[OK] Orchestrator imported")

# Run orchestration
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
    print("="*70)
    print("\nStarting agent swarm...\n")
    print("You will see:")
    print("  - Agent names and tasks")
    print("  - Tool execution (file creation, etc.)")
    print("  - Progress updates")
    print("="*70 + "\n")
    
    try:
        result = await main()
        print("\n" + "="*70)
        print("SUCCESS! QuickShop MVP Generated!")
        print("="*70)
        print("\nLocation: projects/quickshop-mvp-test6")
        print("\nTo run:")
        print("  cd projects/quickshop-mvp-test6")
        print("  docker-compose up")
        print("\nAccess:")
        print("  - Frontend: http://localhost:3000")
        print("  - Backend: http://localhost:8000")
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