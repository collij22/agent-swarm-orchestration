#!/usr/bin/env python3
"""Simple test orchestration to demonstrate agent swarm without API key"""

import os
import sys
import time
from pathlib import Path

# Set a dummy API key for testing
os.environ['ANTHROPIC_API_KEY'] = 'test-key-for-mock-mode'

# Now import the orchestration modules
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.agent_logger import create_new_session
from lib.agent_runtime import AnthropicAgentRunner, AgentContext

def test_agent_swarm():
    """Test the agent swarm in simulation mode"""
    
    print("\n" + "="*60)
    print("AGENT SWARM TEST - SIMULATION MODE")
    print("="*60 + "\n")
    
    # Create logger and runtime
    logger = create_new_session()
    
    # Create runtime - it will run in simulation mode since API key is fake
    runtime = AnthropicAgentRunner(api_key='test-key', logger=logger)
    
    # Create context with test requirements
    context = AgentContext(
        project_requirements={
            "name": "TaskManagerAPI",
            "type": "api_service",
            "features": [
                "RESTful API with CRUD operations",
                "User authentication with JWT",
                "SQLite database",
                "AI-powered task categorization",
                "React frontend",
                "Docker deployment"
            ]
        },
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase="planning"
    )
    
    # Define test workflow with 7 agents
    agents_to_test = [
        ("requirements-analyst", "Analyzing project requirements"),
        ("project-architect", "Designing system architecture"),
        ("database-expert", "Creating database schema"),
        ("rapid-builder", "Building API scaffolding"),
        ("api-integrator", "Integrating AI services"),
        ("frontend-specialist", "Creating React interface"),
        ("quality-guardian", "Running tests and security audit")
    ]
    
    print(f"Testing {len(agents_to_test)} agents in sequence...\n")
    
    successful_agents = []
    failed_agents = []
    
    for agent_name, task_description in agents_to_test:
        print(f"[{len(successful_agents) + 1}/{len(agents_to_test)}] Executing {agent_name}...")
        print(f"    Task: {task_description}")
        
        try:
            # Run agent (will use simulation since no real API key)
            success, result, updated_context = runtime.run_agent(
                agent_name=agent_name,
                agent_prompt=f"You are {agent_name}. {task_description}",
                context=context,
                max_iterations=1
            )
            
            if success:
                print(f"    ✓ Success: {result[:100]}...")
                successful_agents.append(agent_name)
                context = updated_context
            else:
                print(f"    ✗ Failed: {result}")
                failed_agents.append(agent_name)
                
        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
            failed_agents.append(agent_name)
        
        print()
        time.sleep(0.5)  # Brief pause for readability
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"\n✅ Successful Agents ({len(successful_agents)}/{len(agents_to_test)}):")
    for agent in successful_agents:
        print(f"   - {agent}")
    
    if failed_agents:
        print(f"\n❌ Failed Agents ({len(failed_agents)}):")
        for agent in failed_agents:
            print(f"   - {agent}")
    
    print(f"\n📊 Final Context:")
    print(f"   - Completed Tasks: {len(context.completed_tasks)}")
    print(f"   - Artifacts Created: {len(context.artifacts)}")
    print(f"   - Decisions Made: {len(context.decisions)}")
    
    # Close session
    logger.close_session()
    
    print("\n✨ Agent Swarm Test Complete!\n")
    
    return len(successful_agents) == len(agents_to_test)

if __name__ == "__main__":
    success = test_agent_swarm()
    sys.exit(0 if success else 1)