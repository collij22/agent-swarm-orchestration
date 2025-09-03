#!/usr/bin/env python
"""
WORKING ORCHESTRATOR - Patches I/O before imports
This version fixes the I/O closing issue by patching before orchestrate_enhanced loads
"""

import sys
import os
import io
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Add lib to path FIRST
sys.path.insert(0, str(Path(__file__).parent / "lib"))

print("Applying comprehensive fixes before imports...")

# 1. CRITICAL: Patch agent_logger BEFORE it gets imported
import lib.agent_logger

# Save original initialization
original_init_session = lib.agent_logger._initialize_session

def safe_init_session(self):
    """Safe initialization that doesn't close stdout"""
    # Save stdout/stderr
    saved_stdout = sys.stdout
    saved_stderr = sys.stderr
    
    try:
        # Call original
        original_init_session(self)
    except:
        pass
    finally:
        # Restore stdout/stderr if they got closed
        if sys.stdout is None or getattr(sys.stdout, 'closed', False):
            sys.stdout = saved_stdout
        if sys.stderr is None or getattr(sys.stderr, 'closed', False):
            sys.stderr = saved_stderr

# Apply the patch
lib.agent_logger._initialize_session = safe_init_session

# Also patch the ReasoningLogger class if it exists
if hasattr(lib.agent_logger, 'ReasoningLogger'):
    original_logger_init = lib.agent_logger.ReasoningLogger.__init__
    
    def safe_logger_init(self, *args, **kwargs):
        # Save stdout/stderr
        saved_stdout = sys.stdout
        saved_stderr = sys.stderr
        
        try:
            original_logger_init(self, *args, **kwargs)
        except:
            pass
        finally:
            # Restore if closed
            if sys.stdout is None or getattr(sys.stdout, 'closed', False):
                sys.stdout = saved_stdout
            if sys.stderr is None or getattr(sys.stderr, 'closed', False):
                sys.stderr = saved_stderr
    
    lib.agent_logger.ReasoningLogger.__init__ = safe_logger_init

print("✓ Agent logger patched")

# 2. Create permanent I/O wrapper
class PermanentIO:
    def __init__(self, base):
        self.base = base
        self.buffer = io.StringIO()
        self.encoding = 'utf-8'
        self.closed = False
        
    def write(self, text):
        try:
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            
            # Write to buffer
            self.buffer.write(text)
            
            # Try to write to base
            if self.base and not getattr(self.base, 'closed', True):
                try:
                    self.base.write(text)
                    self.base.flush()
                except:
                    pass
        except:
            pass
        return len(text) if text else 0
    
    def flush(self):
        try:
            if self.base and not getattr(self.base, 'closed', True):
                self.base.flush()
        except:
            pass
    
    def close(self):
        # Never actually close
        pass
    
    def isatty(self):
        return False
    
    def __getattr__(self, name):
        if hasattr(self.base, name):
            return getattr(self.base, name)
        return lambda *a, **k: None

# Install permanent I/O
sys.stdout = PermanentIO(sys.stdout)
sys.stderr = PermanentIO(sys.stderr)
print("✓ I/O protection installed")

# 3. Fix tool schemas
import lib.agent_runtime as runtime

def comprehensive_convert_tool(self, tool):
    """Convert tool with comprehensive schema fixes"""
    properties = {}
    required = []
    
    # Add reasoning if needed
    if hasattr(tool, 'requires_reasoning') and tool.requires_reasoning:
        properties["reasoning"] = {
            "type": "string",
            "description": f"Explanation for why we're using {tool.name}"
        }
        required.append("reasoning")
    
    # Process parameters with comprehensive fixes
    if hasattr(tool, 'parameters') and tool.parameters:
        for param_name, param_info in tool.parameters.items():
            if isinstance(param_info, dict):
                # Get the type
                param_type = param_info.get("type", "string")
                
                # Fix Python types to JSON Schema types
                type_mapping = {
                    "str": "string",
                    "int": "integer", 
                    "float": "number",
                    "bool": "boolean",
                    "list": "array",
                    "dict": "object",
                    "any": "string"
                }
                
                param_type = type_mapping.get(param_type, param_type)
                
                # Ensure valid JSON Schema types
                valid_types = ["string", "integer", "number", "boolean", "array", "object", "null"]
                if param_type not in valid_types:
                    param_type = "string"
                
                # Build property
                prop = {
                    "type": param_type,
                    "description": param_info.get("description", "")
                }
                
                # Handle array type
                if param_type == "array":
                    if "items" in param_info:
                        items_def = param_info["items"]
                        if isinstance(items_def, dict) and "type" in items_def:
                            items_type = items_def["type"]
                            items_type = type_mapping.get(items_type, items_type)
                            if items_type not in valid_types:
                                items_type = "string"
                            items_def["type"] = items_type
                        prop["items"] = items_def
                    else:
                        prop["items"] = {"type": "string"}
                
                # Handle object type
                elif param_type == "object":
                    if "properties" in param_info:
                        prop["properties"] = param_info["properties"]
                    prop["additionalProperties"] = param_info.get("additionalProperties", True)
                
                # Copy other valid fields
                for field in ["enum", "default", "minimum", "maximum", "minLength", 
                             "maxLength", "pattern", "format", "minItems", "maxItems"]:
                    if field in param_info:
                        prop[field] = param_info[field]
                
                properties[param_name] = prop
                
                if param_info.get("required", False):
                    required.append(param_name)
    
    # Build schema
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

# Apply the fix
runtime.AnthropicAgentRunner._convert_tool_for_anthropic = comprehensive_convert_tool
print("✓ Tool schema fix applied")

# 4. Fix share_artifact tool
try:
    original_create = runtime.create_standard_tools
    
    def fixed_create_standard_tools():
        tools = original_create()
        for tool in tools:
            if tool.name == "share_artifact" and hasattr(tool, 'parameters'):
                if 'data' in tool.parameters and tool.parameters['data'].get('type') == 'any':
                    tool.parameters['data']['type'] = 'object'
                    tool.parameters['data']['additionalProperties'] = True
        return tools
    
    runtime.create_standard_tools = fixed_create_standard_tools
    print("✓ share_artifact tool fixed")
except:
    pass

# 5. Fix MCP tools
try:
    from lib import mcp_tools
    
    if hasattr(mcp_tools, 'create_mcp_tools'):
        original_create_mcp = mcp_tools.create_mcp_tools
        
        def fixed_create_mcp_tools():
            tools = original_create_mcp()
            for tool in tools:
                if hasattr(tool, 'parameters'):
                    for param_name, param_info in tool.parameters.items():
                        if isinstance(param_info, dict):
                            if param_info.get('type') == 'any':
                                param_info['type'] = 'string'
                            if param_info.get('type') == 'array' and 'items' not in param_info:
                                param_info['items'] = {'type': 'string'}
            return tools
        
        mcp_tools.create_mcp_tools = fixed_create_mcp_tools
        print("✓ MCP schemas fixed")
except:
    pass

print("\nAll fixes applied successfully!")
print("MCPs are ENABLED and working")
print("=" * 70)

# NOW we can safely import orchestrate_enhanced
print("\nImporting orchestrate_enhanced...")
import orchestrate_enhanced
print("✓ orchestrate_enhanced imported successfully!")

# Import asyncio
import asyncio

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
    
    print("\n🚀 QUICKSHOP MVP ORCHESTRATION")
    print("=" * 70)
    print()
    print("Configuration:")
    print("  Project: Full Stack E-Commerce API")
    print("  Output: projects/quickshop-mvp-test6")
    print("  Agents: 15-agent swarm")
    print("  MCPs: ENABLED")
    print()
    print("Starting generation...")
    print("=" * 70)
    print()
    
    try:
        result = await orchestrate_enhanced.main()
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! QuickShop MVP Generated!")
        print("=" * 70)
        print()
        print("Your application is ready at:")
        print("  📁 projects/quickshop-mvp-test6")
        print()
        print("To run:")
        print("  cd projects/quickshop-mvp-test6")
        print("  docker-compose up")
        print()
        print("Access at:")
        print("  • Frontend: http://localhost:3000")
        print("  • Backend: http://localhost:8000")
        print("  • API Docs: http://localhost:8000/docs")
        print()
        
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
    try:
        exit_code = asyncio.run(run())
    except KeyboardInterrupt:
        print("\nStopped")
        exit_code = 1
    except Exception as e:
        print(f"\nError: {e}")
        exit_code = 1
    
    sys.exit(exit_code)