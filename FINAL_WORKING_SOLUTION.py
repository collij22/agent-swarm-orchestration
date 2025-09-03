#!/usr/bin/env python3
"""
FINAL WORKING SOLUTION - Direct execution bypassing all issues
"""

import sys
import os
import asyncio
from pathlib import Path

print("=" * 80)
print("QUICKSHOP MVP GENERATOR - FINAL SOLUTION")
print("=" * 80)
print()

# Set up environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['NO_COLOR'] = '1'
sys.path.insert(0, str(Path.cwd()))

# Import what we need directly
from lib.orchestration_enhanced import EnhancedOrchestrator
from lib.agent_runtime import AgentContext

async def run_agents():
    """Run the agent swarm directly"""
    
    # Create context
    context = AgentContext(
        project_requirements={
            "project_name": "QuickShop MVP",
            "type": "full_stack_api",
            "features": [
                "User authentication",
                "Product catalog",
                "Shopping cart",
                "Order management",
                "Admin dashboard"
            ],
            "tech_stack": {
                "frontend": "React + TypeScript",
                "backend": "FastAPI",
                "database": "PostgreSQL"
            }
        }
    )
    
    # Create orchestrator
    orchestrator = EnhancedOrchestrator(
        workflow_type="full_stack_api",
        output_dir="projects/quickshop-mvp-final",
        enable_dashboard=False,
        max_parallel=2
    )
    
    # Define agents to run
    agents = [
        "requirements-analyst",
        "project-architect",
        "rapid-builder",
        "frontend-specialist",
        "database-expert",
        "api-integrator",
        "quality-guardian",
        "devops-engineer"
    ]
    
    print("Starting agent execution...")
    print("-" * 80)
    
    # Run each agent
    for agent in agents:
        print(f"\n[AGENT] {agent}")
        print(f"  Status: Starting...")
        
        try:
            # Execute agent
            success = await orchestrator.execute_agent(
                agent_name=agent,
                context=context,
                requirements=["Build QuickShop MVP"]
            )
            
            if success:
                print(f"  Status: [OK] Complete")
            else:
                print(f"  Status: [FAIL] Failed")
                
        except Exception as e:
            print(f"  Status: [ERROR] {str(e)}")
    
    print()
    print("=" * 80)
    print("ORCHESTRATION COMPLETE")
    print("=" * 80)
    print()
    print("Output: projects/quickshop-mvp-final/")

# Run the async function
if __name__ == "__main__":
    try:
        asyncio.run(run_agents())
    except KeyboardInterrupt:
        print("\n[STOPPED] User cancelled")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()