#!/usr/bin/env python
"""
SHOW AGENTS - Direct monitoring of agent execution
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Environment setup
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

print("="*70)
print("QUICKSHOP MVP - AGENT SWARM WITH VISIBLE OUTPUT")
print("="*70)

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Completely replace Rich with output-showing version
class ShowingPanel:
    def __init__(self, content, title="", **kwargs):
        print(f"\n{'='*70}")
        if title:
            print(f"[AGENT: {title}]")
        print("-"*70)
        
        # Extract and show content
        content_str = str(content)
        
        # Remove Rich markup
        import re
        content_str = re.sub(r'\[/?[^\]]+\]', '', content_str)
        
        # Show the content
        lines = content_str.split('\n')
        for line in lines[:50]:  # Limit to first 50 lines
            if line.strip():
                print(line[:200])  # Limit line length
        
        if len(lines) > 50:
            print(f"... ({len(lines)-50} more lines)")
        print("="*70)

class ShowingConsole:
    def __init__(self, *args, **kwargs):
        pass
        
    def print(self, *args, **kwargs):
        for arg in args:
            if hasattr(arg, '__class__') and 'Panel' in arg.__class__.__name__:
                pass  # Panel prints itself
            else:
                print(f"[OUTPUT] {str(arg)[:500]}")  # Limit output length
    
    def log(self, *args, **kwargs):
        print(f"[LOG] {' '.join(str(a) for a in args)[:200]}")
    
    def status(self, message="", **kwargs):
        print(f"[WORKING] {message}")
        class Ctx:
            def __enter__(self): return self
            def __exit__(self, *a): print(f"[DONE] {message}")
        return Ctx()
    
    def rule(self, title="", **kwargs):
        if title:
            print(f"\n{'='*30} {title} {'='*30}")
        else:
            print("="*70)
    
    def __getattr__(self, name):
        return lambda *a, **k: None

class ShowingProgress:
    def __init__(self, *args, **kwargs):
        self.tasks = {}
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
        
    def add_task(self, description, total=None, **kwargs):
        task_id = len(self.tasks)
        self.tasks[task_id] = description
        print(f"[TASK START] {description}")
        return task_id
        
    def update(self, task_id, **kwargs):
        if 'description' in kwargs and task_id in self.tasks:
            print(f"[TASK UPDATE] {kwargs['description']}")
            
    def advance(self, task_id, advance=1):
        if task_id in self.tasks:
            print(f"[PROGRESS] {self.tasks[task_id]}")

# Fake Rich module
class FakeRich:
    Console = ShowingConsole
    Panel = ShowingPanel
    Progress = ShowingProgress
    Table = lambda *a, **k: type('T', (), {'add_column': lambda *a: None, 'add_row': lambda *a: None})()

fake = FakeRich()
for module in ['rich', 'rich.console', 'rich.panel', 'rich.table', 'rich.progress']:
    sys.modules[module] = fake

# Import and patch runtime
import lib.agent_runtime as runtime

# Fix tools
def fix_tool(self, tool):
    props = {}
    req = []
    
    if hasattr(tool, 'parameters'):
        for name, info in tool.parameters.items():
            if isinstance(info, dict):
                t = info.get("type", "string")
                t = {"any": "string", "str": "string", "int": "integer", 
                     "float": "number", "bool": "boolean", "list": "array", 
                     "dict": "object"}.get(t, t)
                
                prop = {"type": t, "description": info.get("description", "")}
                
                if t == "array" and "items" not in info:
                    prop["items"] = {"type": "string"}
                    
                props[name] = prop
                if info.get("required"):
                    req.append(name)
    
    return {
        "name": tool.name,
        "description": getattr(tool, 'description', ''),
        "input_schema": {
            "type": "object",
            "properties": props,
            "additionalProperties": False,
            "required": req
        }
    }

runtime.AnthropicAgentRunner._convert_tool_for_anthropic = fix_tool

# Fix standard tools
old_create = runtime.create_standard_tools
def new_create():
    tools = old_create()
    for t in tools:
        if t.name == "share_artifact" and hasattr(t, 'parameters'):
            for p in ['data', 'content']:
                if p in t.parameters and t.parameters[p].get('type') == 'any':
                    t.parameters[p]['type'] = 'string'
        elif t.name == "verify_deliverables" and hasattr(t, 'parameters'):
            if 'deliverables' in t.parameters:
                d = t.parameters['deliverables']
                if d.get('type') in ['array', 'list'] and 'items' not in d:
                    d['items'] = {'type': 'string'}
    return tools

runtime.create_standard_tools = new_create

print("[OK] Patches applied")

# Patch print before importing orchestrate_enhanced
import builtins
_orig_print = builtins.print
def safe_print(*args, **kwargs):
    try:
        _orig_print(*args, **kwargs)
    except:
        pass
builtins.print = safe_print

# Hook into the orchestrator to show agent execution
from orchestrate_enhanced import EnhancedOrchestrator, main

# Create new working print
def print(*args, **kwargs):
    message = ' '.join(str(arg) for arg in args)
    try:
        sys.stdout.write(message + '\n')
        sys.stdout.flush()
    except:
        try:
            os.write(1, (message + '\n').encode('utf-8', 'replace'))
        except:
            pass

builtins.print = print

# Patch the execute_agent method to show what's happening  
original_execute = EnhancedOrchestrator._execute_agent_with_enhanced_features

async def visible_execute(self, *args, **kwargs):
    """Show agent execution"""
    # Extract agent name from args
    agent_name = args[0] if args else "Unknown"
    
    print(f"\n{'='*70}")
    print(f"AGENT STARTING: {agent_name}")
    if len(args) > 1:
        prompt = str(args[1])[:200]
        print(f"Task: {prompt}...")
    print("="*70)
    
    try:
        # Call original with all parameters
        result = await original_execute(self, *args, **kwargs)
        
        print(f"\n[✓] AGENT COMPLETED: {agent_name}")
        
        # Show what was created
        if hasattr(context, 'artifacts') and 'files_created' in context.artifacts:
            recent_files = list(context.artifacts['files_created'])[-5:]
            if recent_files:
                print(f"    Recent files created:")
                for f in recent_files:
                    print(f"      - {f}")
        
        return result
        
    except Exception as e:
        print(f"\n[✗] AGENT FAILED: {agent_name}")
        print(f"    Error: {str(e)[:200]}")
        raise

EnhancedOrchestrator._execute_agent_with_enhanced_features = visible_execute

print("[OK] Agent visibility patches applied")

# Also show tool execution
orig_tool = runtime.AnthropicAgentRunner._execute_tool

async def visible_tool(self, tool, args, context):
    tool_name = getattr(tool, 'name', 'unknown')
    
    # Show important tools
    if tool_name in ['write_file', 'read_file', 'run_command', 'dependency_check']:
        if tool_name == 'write_file':
            print(f"  📝 Creating: {args.get('file_path', '?')}")
        elif tool_name == 'read_file':
            print(f"  📖 Reading: {args.get('file_path', '?')}")
        elif tool_name == 'run_command':
            cmd = args.get('command', '?')[:50]
            print(f"  ⚡ Running: {cmd}...")
        elif tool_name == 'dependency_check':
            print(f"  🔍 Checking dependencies...")
    
    return await orig_tool(self, tool, args, context)

runtime.AnthropicAgentRunner._execute_tool = visible_tool

print("[OK] Tool visibility patches applied")

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
    print("  - Output: projects/quickshop-mvp-test6")
    print("  - Agents: 15-agent swarm")
    print("  - Parallel: 2 agents max")
    print("="*70)
    print("\nStarting orchestration...\n")
    print("You will see each agent as it starts and completes.\n")
    
    try:
        result = await main()
        print("\n" + "="*70)
        print("ORCHESTRATION COMPLETE!")
        print("="*70)
        return 0
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[!] Error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run())
    sys.exit(exit_code)