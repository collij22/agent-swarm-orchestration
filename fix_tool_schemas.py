#!/usr/bin/env python
"""
Fix tool schemas to be JSON Schema 2020-12 compliant
Run this before starting orchestration
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

def patch_agent_runtime():
    """Patch agent_runtime to fix tool conversion"""
    
    import lib.agent_runtime as runtime
    
    # Store original method
    original_convert = runtime.AnthropicAgentRunner._convert_tool_for_anthropic
    
    def fixed_convert_tool(self, tool):
        """Convert tool to Anthropic format with proper JSON Schema 2020-12"""
        properties = {}
        required = []
        
        # Always add reasoning parameter if required
        if hasattr(tool, 'requires_reasoning') and tool.requires_reasoning:
            properties["reasoning"] = {
                "type": "string",
                "description": f"Explanation for why we're using {tool.name}"
            }
            required.append("reasoning")
        
        # Add tool-specific parameters
        if hasattr(tool, 'parameters') and tool.parameters:
            for param_name, param_info in tool.parameters.items():
                if isinstance(param_info, dict):
                    # Build clean property definition
                    prop = {}
                    
                    # Get type and ensure it's valid
                    param_type = param_info.get("type", "string")
                    
                    # Fix common type issues
                    if param_type == "str":
                        param_type = "string"
                    elif param_type == "int":
                        param_type = "integer"
                    elif param_type == "float" or param_type == "number":
                        param_type = "number"
                    elif param_type == "bool":
                        param_type = "boolean"
                    elif param_type == "list":
                        param_type = "array"
                    elif param_type == "dict":
                        param_type = "object"
                    
                    prop["type"] = param_type
                    
                    # Add description if present
                    if "description" in param_info:
                        prop["description"] = param_info["description"]
                    
                    # Handle array types properly
                    if param_type == "array":
                        # Ensure items property exists
                        if "items" in param_info:
                            prop["items"] = param_info["items"]
                        else:
                            prop["items"] = {"type": "string"}
                    
                    # Handle object types properly
                    elif param_type == "object":
                        # Allow additional properties for objects
                        prop["additionalProperties"] = True
                        if "properties" in param_info:
                            prop["properties"] = param_info["properties"]
                    
                    # Add to properties
                    properties[param_name] = prop
                    
                    # Check if required
                    if param_info.get("required", False):
                        required.append(param_name)
        
        # Build the tool schema
        result = {
            "name": tool.name,
            "description": tool.description if hasattr(tool, 'description') else "",
            "input_schema": {
                "type": "object",
                "properties": properties
            }
        }
        
        # Only add required array if there are required fields
        if required:
            result["input_schema"]["required"] = required
        
        # Don't add additionalProperties: false as it might cause issues
        
        return result
    
    # Replace the method
    runtime.AnthropicAgentRunner._convert_tool_for_anthropic = fixed_convert_tool
    print("✓ Fixed tool conversion for JSON Schema 2020-12 compliance")

if __name__ == "__main__":
    patch_agent_runtime()
    print("\nTool schemas have been fixed.")
    print("You can now run the orchestration without schema errors.")