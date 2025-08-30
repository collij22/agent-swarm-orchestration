#!/usr/bin/env python3
"""Simple tool execution test with ASCII output"""

import sys
from pathlib import Path
import asyncio

# Fix encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add lib to path
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools

async def test_record_decision():
    """Test the record_decision tool specifically"""
    
    print("Testing record_decision tool execution...")
    
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
    
    # Test record_decision tool
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
        
        print(f"[OK] Tool executed successfully: {result}")
        print(f"[OK] Decisions added to context: {len(context.decisions)}")
        
        if context.decisions:
            print(f"[OK] Latest decision: {context.decisions[-1]['decision']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Tool execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_record_decision())
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)