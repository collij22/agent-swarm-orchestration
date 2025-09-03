#!/usr/bin/env python
"""
RUN WITH DASHBOARD - Shows real-time progress in web browser
"""

import sys
import os
from pathlib import Path
import logging
import webbrowser
import time
import threading

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
print("QUICKSHOP MVP - AGENT SWARM WITH WEB DASHBOARD")
print("=" * 70)

# Safe print function
import builtins
_original_print = builtins.print

def safe_print(*args, **kwargs):
    """Print that handles Unicode safely"""
    try:
        message = ' '.join(str(arg) for arg in args)
        # Remove Unicode that causes issues
        message = message.encode('ascii', 'replace').decode('ascii')
        _original_print(message, **kwargs)
    except:
        try:
            safe_msg = ' '.join(str(arg).encode('ascii', 'ignore').decode('ascii') for arg in args)
            sys.stdout.write(safe_msg + '\n')
            sys.stdout.flush()
        except:
            pass

builtins.print = safe_print

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
    
    def rule(self, title="", **kwargs):
        if title:
            safe = str(title).encode('ascii', 'replace').decode('ascii')
            print(f"\n{'-'*20} {safe} {'-'*20}")
        else:
            print("-" * 70)
    
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

# Install fake Rich
fake = FakeRich()
for mod in ['rich', 'rich.console', 'rich.panel', 'rich.table', 'rich.progress']:
    sys.modules[mod] = fake

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

print("-" * 70)
print("All patches applied successfully!")
print("=" * 70)

# Function to open browser after a delay
def open_dashboard():
    """Open the dashboard in browser after it starts"""
    time.sleep(5)  # Wait for dashboard to start
    print("\n" + "=" * 70)
    print("OPENING WEB DASHBOARD IN BROWSER...")
    print("If it doesn't open automatically, go to:")
    print("  http://localhost:5173")
    print("=" * 70 + "\n")
    try:
        webbrowser.open('http://localhost:5173')
    except:
        print("Could not open browser automatically.")
        print("Please open http://localhost:5173 manually.")

# Import and run orchestrator
from orchestrate_enhanced import main
import asyncio

async def run():
    sys.argv = [
        'orchestrate_enhanced.py',
        '--project-type', 'full_stack_api',
        '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
        '--output-dir', 'projects/quickshop-mvp-test8',  # Changed to test8
        '--dashboard',  # ENABLE DASHBOARD
        '--progress',
        '--summary-level', 'concise',
        '--max-parallel', '2',
        '--human-log'
    ]
    
    print("\nCONFIGURATION")
    print("-" * 70)
    print("Type: Full Stack E-Commerce API")
    print("Output: projects/quickshop-mvp-test8")  # Updated
    print("Agents: 15-agent swarm")
    print("MCPs: Enabled")
    print("Dashboard: ENABLED - http://localhost:5173")
    print("WebSocket: ws://localhost:8765")
    print("=" * 70)
    
    # Start browser opener thread
    browser_thread = threading.Thread(target=open_dashboard)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("\nStarting orchestration with web dashboard...")
    print("\nThe dashboard will show:")
    print("  - Real-time agent execution")
    print("  - Progress bars for each agent")
    print("  - Live completion percentages")
    print("  - Files being created")
    print("  - Error messages if any")
    print("\n" + "=" * 70 + "\n")
    
    try:
        result = await main()
        print("\n" + "=" * 70)
        print("SUCCESS! QuickShop MVP Generated!")
        print("=" * 70)
        print("\nLocation: projects/quickshop-mvp-test8")
        print("\nTo run the application:")
        print("  cd projects\\quickshop-mvp-test8")
        print("  docker-compose up")
        print("\nAccess at:")
        print("  - Frontend: http://localhost:3000")
        print("  - Backend: http://localhost:8000")
        print("=" * 70)
        return 0
    except Exception as e:
        safe_error = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"\nError: {safe_error}")
        return 1

if __name__ == "__main__":
    print("\nIMPORTANT: The web dashboard will open in your browser.")
    print("If you see a connection error, wait a few seconds and refresh.")
    print("-" * 70)
    
    exit_code = asyncio.run(run())
    sys.exit(exit_code)