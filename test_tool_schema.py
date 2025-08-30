#!/usr/bin/env python3
"""Test tool schema format to ensure it matches JSON Schema draft 2020-12"""

import json
import sys
from pathlib import Path

# Add lib to path
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.agent_runtime import AnthropicAgentRunner, create_standard_tools

def test_tool_schema():
    """Test that tool schemas are correctly formatted"""
    
    print("Testing Tool Schema Format...")
    print("=" * 50)
    
    # Create runtime with dummy API key for schema testing
    runtime = AnthropicAgentRunner(api_key="test-key-for-schema-testing")
    
    # Register standard tools
    for tool in create_standard_tools():
        runtime.register_tool(tool)
    
    print(f"Registered {len(runtime.tools)} tools")
    print()
    
    # Test each tool's schema conversion
    for tool_name, tool in runtime.tools.items():
        print(f"Testing tool: {tool_name}")
        
        try:
            # Convert to Anthropic format
            anthropic_tool = runtime._convert_tool_for_anthropic(tool)
            
            # Print schema
            schema = anthropic_tool['input_schema']
            print(f"  Schema properties: {list(schema['properties'].keys())}")
            print(f"  Required fields: {schema.get('required', [])}")
            
            # Validate structure
            assert 'type' in schema
            assert schema['type'] == 'object'
            assert 'properties' in schema
            assert 'required' in schema
            assert 'additionalProperties' in schema
            
            # Validate properties don't have 'required' field inside them
            for prop_name, prop_def in schema['properties'].items():
                if 'required' in prop_def:
                    raise ValueError(f"Property '{prop_name}' has 'required' field inside property definition")
            
            print("  [OK] Schema format valid")
            
        except Exception as e:
            print(f"  [ERROR] Schema error: {e}")
            return False
        
        print()
    
    print("=" * 50)
    print("[SUCCESS] All tool schemas are valid!")
    
    # Show example schema
    example_tool = list(runtime.tools.values())[0]
    example_schema = runtime._convert_tool_for_anthropic(example_tool)
    
    print("\nExample tool schema:")
    print(json.dumps(example_schema, indent=2))
    
    return True

if __name__ == "__main__":
    success = test_tool_schema()
    sys.exit(0 if success else 1)