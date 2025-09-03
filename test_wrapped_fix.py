#!/usr/bin/env python3
"""
Test script to verify wrapped function parameter passing fix
"""

import os
import sys
from pathlib import Path

# Set environment variables
os.environ['ANTHROPIC_API_KEY'] = 'test-key-123'
os.environ['MOCK_MODE'] = 'true'

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("Testing Wrapped Function Parameter Fix")
print("=" * 80)

# Import required modules
from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools, ModelType
from lib.mock_anthropic_enhanced import MockAnthropicEnhancedRunner

print("\n[INFO] Using mock mode for testing")

# Create context
context = AgentContext(
    project_requirements={},
    completed_tasks=[],
    artifacts={},
    decisions=[],
    current_phase="testing"
)

# Create runner
runner = MockAnthropicEnhancedRunner()

print("\n[INFO] Testing agent with wrapped function calls...")

# Test prompt that will trigger tool calls
test_prompt = """
Please create a simple Python file at test_file.py with a hello world function.
Then share an artifact about the project structure.
Finally, verify that the deliverables exist.
"""

try:
    # Run agent
    success, result, updated_context = runner.run_agent(
        agent_name="rapid-builder",
        agent_prompt=test_prompt,
        context=context
    )
    
    if success:
        print("\n[SUCCESS] Agent completed without parameter errors!")
        print(f"Result: {str(result)[:200]}...")
    
    # Check if wrapped function detection was logged
    if hasattr(context, 'reasoning_traces') and context.reasoning_traces:
        for trace in context.reasoning_traces:
            if "wrapped function" in str(trace).lower():
                print(f"\n[DETECTED] Wrapped function handling: {trace}")
                
except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)