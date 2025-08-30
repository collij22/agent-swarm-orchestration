#!/usr/bin/env python3
"""Test tool execution to verify the reasoning parameter fix"""

import sys
from pathlib import Path
import asyncio

# Add lib to path
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools

async def test_tool_execution():
    """Test that tool execution properly handles reasoning parameter"""
    
    print("Testing Tool Execution...")
    print("=" * 40)
    
    # Create runtime with dummy key
    runtime = AnthropicAgentRunner(api_key="test-key")
    
    # Register standard tools
    for tool in create_standard_tools():
        runtime.register_tool(tool)
    
    # Create test context
    context = AgentContext(
        project_requirements={"name": "Test"},
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase="testing"
    )
    
    # Test record_decision tool (the one that was failing)
    print("Testing record_decision tool...")
    
    try:
        result = await runtime._execute_tool(
            tool=runtime.tools['record_decision'],
            args={
                'reasoning': 'Testing the tool execution fix',
                'decision': 'Use FastAPI for backend',
                'rationale': 'FastAPI is fast and modern'
            },
            context=context
        )
        
        print(f"✓ Success: {result}")
        print(f"✓ Decisions in context: {len(context.decisions)}")
        print(f"✓ Latest decision: {context.decisions[-1] if context.decisions else 'None'}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Test other tools
    test_tools = ['write_file', 'complete_task']
    
    for tool_name in test_tools:
        print(f"\nTesting {tool_name} tool...")
        
        try:
            if tool_name == 'write_file':
                result = await runtime._execute_tool(
                    tool=runtime.tools[tool_name],
                    args={
                        'reasoning': f'Testing {tool_name}',
                        'file_path': 'test_file.txt',
                        'content': 'Test content'
                    },
                    context=context
                )
            elif tool_name == 'complete_task':
                result = await runtime._execute_tool(
                    tool=runtime.tools[tool_name],
                    args={
                        'reasoning': f'Testing {tool_name}',
                        'summary': 'Task completed successfully'
                    },
                    context=context
                )
            
            print(f"✓ Success: {result}")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    print("\n" + "=" * 40)
    print("✅ All tool execution tests passed!")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_tool_execution())
    sys.exit(0 if success else 1)