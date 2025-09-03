#!/usr/bin/env python3
"""
STANDALONE RUNNER - Runs agents directly without orchestrate_enhanced
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Force UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', '')

print("=" * 80)
print("STANDALONE AGENT RUNNER")
print("=" * 80)
print()

# Check API key
if not os.environ.get('ANTHROPIC_API_KEY'):
    print("[WARNING] No ANTHROPIC_API_KEY found")
    print("Set it with: set ANTHROPIC_API_KEY=your-key-here")
    print()

# Import only what we need
sys.path.insert(0, str(Path.cwd()))

from lib.agent_runtime import (
    AgentContext,
    AnthropicAgentRunner,
    ModelType,
    get_optimal_model
)

async def run_agent(runner, agent_name, context, requirements):
    """Run a single agent"""
    print(f"\n[AGENT] {agent_name}")
    print(f"  Model: {get_optimal_model(agent_name)}")
    print(f"  Starting...")
    
    try:
        # Build prompt
        prompt = f"""You are {agent_name}, a specialized AI agent.
        
Your task is to help build a QuickShop MVP e-commerce application.

Requirements:
{json.dumps(requirements, indent=2)}

Previous work:
{json.dumps(context.completed_tasks, indent=2) if context.completed_tasks else 'None'}

Please complete your specialized tasks for this project.
"""
        
        # Run agent
        success, result, updated_context = await runner.run_agent_async(
            agent_name=agent_name,
            agent_prompt=prompt,
            context=context,
            model=get_optimal_model(agent_name),
            max_iterations=5
        )
        
        if success:
            print(f"  Status: [OK] Complete")
            # Update context
            context.completed_tasks.append({
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
        else:
            print(f"  Status: [FAIL] {result}")
            
        return success, updated_context
        
    except Exception as e:
        print(f"  Status: [ERROR] {str(e)}")
        return False, context

async def main():
    """Main execution"""
    
    # Create output directory
    output_dir = Path("projects/quickshop-mvp-standalone")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Requirements
    requirements = {
        "name": "QuickShop MVP",
        "type": "E-commerce platform",
        "features": [
            "User authentication (register, login, logout)",
            "Product catalog with categories",
            "Shopping cart functionality",
            "Order management",
            "Admin dashboard"
        ],
        "tech_stack": {
            "frontend": "React + TypeScript + Tailwind CSS",
            "backend": "FastAPI (Python)",
            "database": "PostgreSQL",
            "deployment": "Docker + docker-compose"
        }
    }
    
    # Create context
    context = AgentContext(
        project_requirements=requirements,
        completed_tasks=[],
        artifacts={"output_dir": str(output_dir)},
        decisions=[],
        current_phase="initialization"
    )
    
    # Create runner
    runner = AnthropicAgentRunner(
        api_key=os.environ.get('ANTHROPIC_API_KEY')
    )
    
    # Define agent sequence
    agents = [
        "requirements-analyst",
        "project-architect", 
        "database-expert",
        "rapid-builder",
        "frontend-specialist",
        "api-integrator",
        "devops-engineer",
        "quality-guardian"
    ]
    
    print(f"Output directory: {output_dir}")
    print(f"Agents to run: {len(agents)}")
    print("-" * 80)
    
    # Run agents
    for agent in agents:
        success, context = await run_agent(runner, agent, context, requirements)
        if not success:
            print(f"\n[WARNING] {agent} failed, continuing...")
    
    # Save final context
    context_file = output_dir / "final_context.json"
    with open(context_file, 'w') as f:
        json.dump(context.to_dict(), f, indent=2, default=str)
    
    print()
    print("=" * 80)
    print("EXECUTION COMPLETE")
    print("=" * 80)
    print()
    print(f"Output: {output_dir}")
    print(f"Context: {context_file}")
    print(f"Completed tasks: {len(context.completed_tasks)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOPPED] User cancelled")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()