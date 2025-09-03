#!/usr/bin/env python
"""
RUN WITHOUT RICH - Disables Rich console entirely
This bypasses all Rich console issues while keeping MCPs enabled
"""

import sys
import os
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['NO_RICH_CONSOLE'] = 'true'  # Signal to disable Rich

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

print("Starting QuickShop Orchestration (Rich disabled)...")
print("=" * 70)

# 1. Create fake Rich console that does nothing
class FakeConsole:
    """Fake Rich console that just prints normally"""
    def __init__(self, *args, **kwargs):
        pass
    
    def print(self, *args, **kwargs):
        # Extract text from Rich markup
        text = str(args[0]) if args else ""
        # Remove Rich markup
        import re
        text = re.sub(r'\[.*?\]', '', text)
        print(text)
    
    def log(self, *args, **kwargs):
        self.print(*args, **kwargs)
    
    def rule(self, *args, **kwargs):
        print("-" * 70)
    
    def __getattr__(self, name):
        return lambda *a, **k: None

class FakePanel:
    """Fake Panel that just returns the text"""
    def __init__(self, text, *args, **kwargs):
        self.text = text
    
    def __str__(self):
        return str(self.text)

class FakeProgress:
    """Fake Progress that does nothing"""
    def __init__(self, *args, **kwargs):
        pass
    
    def add_task(self, *args, **kwargs):
        return 0
    
    def update(self, *args, **kwargs):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass

# 2. Replace Rich before any imports
import sys
import types

# Create fake rich module
fake_rich = types.ModuleType('rich')
fake_rich.console = types.ModuleType('rich.console')
fake_rich.console.Console = FakeConsole
fake_rich.panel = types.ModuleType('rich.panel')
fake_rich.panel.Panel = FakePanel
fake_rich.progress = types.ModuleType('rich.progress')
fake_rich.progress.Progress = FakeProgress
fake_rich.progress.SpinnerColumn = lambda: None
fake_rich.progress.TextColumn = lambda *a: None
fake_rich.progress.BarColumn = lambda: None
fake_rich.progress.TimeRemainingColumn = lambda: None

# Install fake rich
sys.modules['rich'] = fake_rich
sys.modules['rich.console'] = fake_rich.console
sys.modules['rich.panel'] = fake_rich.panel
sys.modules['rich.progress'] = fake_rich.progress

print("[OK] Rich console disabled")

# 3. Fix tool schemas
import lib.agent_runtime as runtime

def fix_tool_schema(self, tool):
    """Convert tool to valid JSON Schema"""
    properties = {}
    required = []
    
    if hasattr(tool, 'requires_reasoning') and tool.requires_reasoning:
        properties["reasoning"] = {
            "type": "string",
            "description": f"Reasoning for {tool.name}"
        }
        required.append("reasoning")
    
    if hasattr(tool, 'parameters') and tool.parameters:
        for param_name, param_info in tool.parameters.items():
            if not isinstance(param_info, dict):
                continue
                
            param_type = param_info.get("type", "string")
            
            # Type mapping
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
print("[OK] Tool schemas fixed")

# Fix standard tools
original_create = runtime.create_standard_tools
def fixed_create():
    tools = original_create()
    for tool in tools:
        if tool.name == "share_artifact" and hasattr(tool, 'parameters'):
            if 'data' in tool.parameters and tool.parameters['data'].get('type') == 'any':
                tool.parameters['data']['type'] = 'object'
                tool.parameters['data']['additionalProperties'] = True
    return tools
runtime.create_standard_tools = fixed_create

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
    print("[OK] MCP tools fixed")
except:
    pass

print("[OK] All fixes applied")
print("=" * 70)

# 4. Now import and run orchestrate_enhanced
import asyncio
from orchestrate_enhanced import main

async def run():
    """Run the orchestration"""
    
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
    print()
    print("Configuration:")
    print("  - Type: Full Stack E-Commerce")
    print("  - Output: projects/quickshop-mvp-test6")
    print("  - Agents: 15-agent swarm")
    print("  - MCPs: ENABLED")
    print("  - Rich: DISABLED (for stability)")
    print()
    print("Starting...")
    print("=" * 70)
    print()
    
    try:
        result = await main()
        
        print("\n" + "=" * 70)
        print("SUCCESS! QuickShop MVP Generated!")
        print("=" * 70)
        print()
        print("Your application is ready at:")
        print("  projects/quickshop-mvp-test6")
        print()
        print("To run:")
        print("  cd projects/quickshop-mvp-test6")
        print("  docker-compose up")
        print()
        print("Access:")
        print("  - Frontend: http://localhost:3000")
        print("  - Backend: http://localhost:8000")
        print("  - API Docs: http://localhost:8000/docs")
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
    try:
        exit_code = asyncio.run(run())
    except Exception as e:
        print(f"Fatal error: {e}")
        exit_code = 1
    
    sys.exit(exit_code)