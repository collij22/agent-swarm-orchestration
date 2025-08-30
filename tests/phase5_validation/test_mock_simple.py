#!/usr/bin/env python3
"""Simple test to verify mock mode works"""

import os
import sys
from pathlib import Path

# Set mock mode
os.environ['MOCK_MODE'] = 'true'

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("Testing mock mode with minimal configuration...")

# Import the orchestrator directly
from orchestrate_enhanced import EnhancedOrchestrator

# Create a minimal requirements file
req_data = {
    "project": {
        "name": "Test Project",
        "type": "api_service",
        "description": "Test"
    },
    "requirements": [
        {
            "id": "REQ-001",
            "description": "Test requirement",
            "priority": "high"
        }
    ]
}

# Create orchestrator
try:
    print("Creating orchestrator with mock mode...")
    orchestrator = EnhancedOrchestrator()
    print(f"Orchestrator created with runtime: {type(orchestrator.runtime).__name__}")
    
    # Check if mock runner is being used
    if hasattr(orchestrator.runtime, 'client'):
        print(f"Client type: {type(orchestrator.runtime.client).__name__}")
    
    # Try to run a simple agent
    from lib.agent_runtime import AgentContext
    
    context = AgentContext(
        project_requirements=req_data,
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase="testing"
    )
    
    print("\nAttempting to run a mock agent...")
    success, result, _ = orchestrator.runtime.run_agent(
        agent_name="test-agent",
        agent_prompt="This is a test",
        context=context,
        max_iterations=1
    )
    
    print(f"Agent execution: {'SUCCESS' if success else 'FAILED'}")
    print(f"Result: {result[:100] if result else 'No result'}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nMock mode test complete.")