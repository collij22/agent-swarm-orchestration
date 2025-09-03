#!/usr/bin/env python
"""Debug which tools are causing the schema error"""

import sys
import os
import json
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Fix I/O
class SafeIO:
    def __init__(self, base):
        self.base = base
        self.encoding = 'utf-8'
        self.closed = False
    def write(self, text):
        try:
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            self.base.write(text)
            self.base.flush()
        except:
            pass
        return len(text) if text else 0
    def flush(self):
        try:
            self.base.flush()
        except:
            pass
    def close(self):
        pass
    def __getattr__(self, name):
        return getattr(self.base, name, lambda *a: None)

sys.stdout = SafeIO(sys.stdout)
sys.stderr = SafeIO(sys.stderr)

print("Debugging tool schemas...")
print("=" * 70)

# Import runtime
import lib.agent_runtime as runtime

# Create a test runner
from lib.agent_logger import create_new_session, SummaryLevel
logger = create_new_session("debug", False, SummaryLevel.CONCISE)
runner = runtime.AnthropicAgentRunner(None, logger)

# Register some test tools
test_tools = [
    runtime.Tool(
        name="test_tool_1",
        description="Test tool 1",
        parameters={
            "param1": {"type": "string", "description": "Test param", "required": True}
        },
        function=lambda **k: "test",
        requires_reasoning=True
    ),
    runtime.Tool(
        name="test_tool_2",
        description="Test tool 2",
        parameters={
            "items": {"type": "array", "description": "Array param", "required": False}
        },
        function=lambda **k: "test"
    ),
    runtime.Tool(
        name="test_tool_3",
        description="Test tool 3",
        parameters={
            "data": {"type": "object", "description": "Object param", "required": False}
        },
        function=lambda **k: "test"
    )
]

# Register tools
for tool in test_tools:
    runner.register_tool(tool)

# Now register the standard tools
standard_tools = runtime.create_standard_tools()
for tool in standard_tools:
    runner.register_tool(tool)

print(f"\nTotal tools registered: {len(runner.tools)}")
print("\nTool names:")
for i, name in enumerate(runner.tools.keys()):
    print(f"  {i}: {name}")

# Convert tools to Anthropic format
print("\n" + "=" * 70)
print("Converting tools to Anthropic format...")
print("=" * 70)

anthropic_tools = []
for i, tool in enumerate(runner.tools.values()):
    try:
        converted = runner._convert_tool_for_anthropic(tool)
        anthropic_tools.append(converted)
        
        print(f"\nTool {i}: {tool.name}")
        print(f"  Schema valid: ✓")
        
        # Check for potential issues
        schema = converted.get("input_schema", {})
        props = schema.get("properties", {})
        
        for prop_name, prop_def in props.items():
            prop_type = prop_def.get("type", "unknown")
            if prop_type not in ["string", "integer", "number", "boolean", "array", "object", "null"]:
                print(f"  WARNING: Property '{prop_name}' has invalid type: {prop_type}")
            
            if prop_type == "array" and "items" not in prop_def:
                print(f"  WARNING: Array property '{prop_name}' missing 'items'")
            
            # Check for 'custom' field which might be the issue
            if "custom" in prop_def:
                print(f"  ERROR: Property '{prop_name}' has 'custom' field!")
        
    except Exception as e:
        print(f"\nTool {i}: {tool.name}")
        print(f"  ERROR: {e}")

# Output the problematic tool (index 4)
if len(anthropic_tools) > 4:
    print("\n" + "=" * 70)
    print("Tool at index 4 (the problematic one):")
    print("=" * 70)
    print(json.dumps(anthropic_tools[4], indent=2))

print("\n" + "=" * 70)
print("Debug complete")
print("=" * 70)