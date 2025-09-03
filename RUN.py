#!/usr/bin/env python
"""
RUN - Direct execution bypassing all I/O issues
"""

import sys
import os
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Create persistent stdout that NEVER closes
class PersistentOut:
    def write(self, text):
        try:
            # Try console output
            import ctypes
            import ctypes.wintypes
            
            # Get handle to console
            STD_OUTPUT_HANDLE = -11
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            
            # Write directly to console
            text_bytes = str(text).encode('cp1252', 'replace')
            written = ctypes.wintypes.DWORD()
            kernel32.WriteConsoleA(handle, text_bytes, len(text_bytes), ctypes.byref(written), None)
        except:
            # Fallback to OS write
            try:
                os.write(1, str(text).encode('ascii', 'replace'))
            except:
                pass
    
    def flush(self):
        pass
    
    def close(self):
        # NEVER close
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# Replace stdout/stderr
sys.stdout = PersistentOut()
sys.stderr = PersistentOut()

# Override print
import builtins
builtins.print = lambda *args, **kwargs: sys.stdout.write(' '.join(str(a) for a in args) + '\n')

print("Starting orchestrator...")

# Fake Rich before ANY imports
class FakeModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

sys.modules['rich'] = FakeModule()
sys.modules['rich.console'] = FakeModule()
sys.modules['rich.panel'] = FakeModule()
sys.modules['rich.table'] = FakeModule()
sys.modules['rich.progress'] = FakeModule()

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Import and patch runtime
import lib.agent_runtime as runtime

def fixed_tool_converter(self, tool):
    properties = {}
    required = []
    
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
            }
            
            param_type = type_map.get(param_type, param_type)
            
            prop = {"type": param_type}
            if "description" in param_info:
                prop["description"] = param_info.get("description", "")
            
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

# Fix standard tools
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

print("Patches applied")

# Now try to run
def run_main():
    import sys
    import asyncio
    
    # Set arguments
    sys.argv = [
        'orchestrate_enhanced.py',
        '--project-type', 'full_stack_api',
        '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
        '--output-dir', 'projects/quickshop-mvp-test7',
        '--progress',
        '--max-parallel', '2',
        '--human-log'
    ]
    
    print("Arguments set")
    
    # Import main
    try:
        from orchestrate_enhanced import main
        print("Main imported")
    except Exception as e:
        print(f"Import error: {e}")
        return 1
    
    # Create and run event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("Running orchestration...")
        result = loop.run_until_complete(main())
        print(f"Result: {result}")
        return 0
    except Exception as e:
        print(f"Runtime error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        try:
            loop.close()
        except:
            pass

if __name__ == "__main__":
    exit_code = run_main()
    sys.exit(exit_code)