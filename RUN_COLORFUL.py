#!/usr/bin/env python
"""
RUN COLORFUL - Restores the colorful console output
"""

import sys
import os
from pathlib import Path
import logging

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['TERM'] = 'dumb'
os.environ['NO_COLOR'] = '1'

# Suppress INFO logging from httpx
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("lib.workflow_loader").setLevel(logging.WARNING)
logging.getLogger("lib.mcp_manager").setLevel(logging.WARNING)

# Save original print
import builtins
_original_print = builtins.print

def console_print(*args, **kwargs):
    """Print that ALWAYS shows on console"""
    message = ' '.join(str(arg) for arg in args)
    
    # ALWAYS write to console
    try:
        # Try original print first
        _original_print(message, flush=True)
    except:
        # Direct stdout write
        try:
            sys.stdout.write(message + '\n')
            sys.stdout.flush()
        except:
            # OS level write
            try:
                os.write(1, (message + '\n').encode('utf-8', 'replace'))
            except:
                pass

# Replace print globally
builtins.print = console_print

print("=" * 70)
print("🚀 QUICKSHOP MVP - AGENT SWARM ORCHESTRATION")
print("=" * 70)

# Create Rich replacement that shows colorful output
class ColorfulPanel:
    def __init__(self, content, title="", border_style="", **kwargs):
        # Colorful panel output
        if title:
            print(f"\n╔{'═' * 68}╗")
            print(f"║ ✨ {title:<64} ║")
            print(f"╠{'═' * 68}╣")
        else:
            print(f"\n╔{'═' * 68}╗")
        
        # Handle content
        content_str = str(content) if hasattr(content, '__str__') else repr(content)
        
        # Remove Rich markup
        import re
        content_str = re.sub(r'\[/?[^\\]+\]', '', content_str)
        
        # Print content with nice formatting
        lines = content_str.split('\n')
        for line in lines[:20]:  # Show first 20 lines
            if line.strip():
                # Truncate long lines
                if len(line) > 66:
                    line = line[:63] + "..."
                print(f"║ {line:<66} ║")
        
        if len(lines) > 20:
            print(f"║ ... {len(lines)-20} more lines ...{' ' * 48} ║")
            
        print(f"╚{'═' * 68}╝")

class ColorfulConsole:
    def __init__(self, *args, **kwargs):
        self.file = kwargs.get('file', sys.stdout)
        
    def print(self, *args, **kwargs):
        """Main output method for agent messages"""
        for arg in args:
            if hasattr(arg, '__class__'):
                class_name = arg.__class__.__name__
                if 'Panel' in class_name:
                    # Panel already printed in __init__
                    pass
                elif 'Table' in class_name:
                    # Table output
                    print("\n📊 TABLE OUTPUT")
                    print("-" * 60)
                else:
                    # Regular output
                    output = str(arg)
                    if output and not output.isspace():
                        print(f"  {output}")
            else:
                output = str(arg)
                if output and not output.isspace():
                    print(f"  {output}")
    
    def log(self, *args, **kwargs):
        print(f"📝 LOG: {' '.join(str(a) for a in args)}")
    
    def status(self, message="", **kwargs):
        print(f"\n⏳ STATUS: {message}")
        class StatusContext:
            def __enter__(self): 
                return self
            def __exit__(self, *args): 
                print(f"✅ DONE: {message}\n")
        return StatusContext()
    
    def rule(self, title="", **kwargs):
        if title:
            print(f"\n{'─' * 20} {title} {'─' * (47-len(title))}")
        else:
            print("─" * 70)
    
    def __getattr__(self, name):
        def method(*args, **kwargs):
            if args and name not in ['clear', 'show_cursor', 'hide_cursor']:
                print(f"[{name.upper()}] {' '.join(str(a) for a in args)}")
        return method

class ColorfulProgress:
    def __init__(self, *args, **kwargs):
        self.tasks = {}
        self.task_counter = 0
        
    def __enter__(self):
        print("\n📊 PROGRESS TRACKING STARTED")
        print("─" * 60)
        return self
        
    def __exit__(self, *args):
        print("─" * 60)
        print("✅ PROGRESS TRACKING COMPLETE\n")
        
    def add_task(self, description, total=None, **kwargs):
        task_id = self.task_counter
        self.task_counter += 1
        self.tasks[task_id] = {
            'description': description,
            'completed': 0,
            'total': total
        }
        print(f"  ▶️  {description}")
        return task_id
        
    def update(self, task_id, description=None, completed=None, **kwargs):
        if task_id in self.tasks:
            if description:
                self.tasks[task_id]['description'] = description
                print(f"  📝 {description}")
            if completed is not None:
                self.tasks[task_id]['completed'] = completed
                total = self.tasks[task_id].get('total')
                if total:
                    percent = (completed / total) * 100
                    bar_length = 30
                    filled = int(bar_length * percent / 100)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    print(f"  [{bar}] {percent:.1f}%")
                    
    def advance(self, task_id, advance=1):
        if task_id in self.tasks:
            self.tasks[task_id]['completed'] += advance
            desc = self.tasks[task_id]['description']
            completed = self.tasks[task_id]['completed']
            total = self.tasks[task_id].get('total')
            if total:
                percent = (completed / total) * 100
                print(f"  ➡️  {percent:.0f}% - {desc}")

class ColorfulTable:
    def __init__(self, title="", **kwargs):
        self.title = title
        self.columns = []
        self.rows = []
        if title:
            print(f"\n📋 {title}")
            print("─" * 60)
            
    def add_column(self, name, **kwargs):
        self.columns.append(name)
        
    def add_row(self, *values, **kwargs):
        self.rows.append(values)
        row_str = " │ ".join(str(v)[:20] for v in values)
        print(f"  {row_str}")

# Create the fake Rich module
class FakeRich:
    Console = ColorfulConsole
    Panel = ColorfulPanel
    Table = ColorfulTable
    Progress = ColorfulProgress
    
    class console:
        Console = ColorfulConsole
    class panel:
        Panel = ColorfulPanel
    class table:
        Table = ColorfulTable
    class progress:
        Progress = ColorfulProgress
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

print("🔧 Initializing Agent Swarm...")
print("─" * 70)

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

print("✅ Tool schemas fixed")

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
        print("✅ MCP tools fixed")
except:
    pass

print("─" * 70)
print("✨ All patches applied successfully!")
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
    
    print("\n🎯 QUICKSHOP MVP CONFIGURATION")
    print("=" * 70)
    print("📦 Type: Full Stack E-Commerce")
    print("📁 Output: projects/quickshop-mvp-test6")
    print("🤖 Agents: 15-agent swarm")
    print("🔌 MCPs: ENABLED")
    print("🚀 Parallel: 2 agents max")
    print("=" * 70)
    print("\n⚡ Starting agent swarm...\n")
    
    try:
        result = await main()
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! QuickShop MVP Generated!")
        print("=" * 70)
        print("\n📁 Location: projects/quickshop-mvp-test6")
        print("\n📋 To run:")
        print("  cd projects/quickshop-mvp-test6")
        print("  docker-compose up")
        print("\n🌐 Access:")
        print("  - Frontend: http://localhost:3000")
        print("  - Backend: http://localhost:8000")
        print("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
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