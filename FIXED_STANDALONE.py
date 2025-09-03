#!/usr/bin/env python3
"""
FIXED STANDALONE RUNNER - Ensures proper sequential execution
"""

import sys
import os
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

# Force UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', '')

print("=" * 80)
print("FIXED STANDALONE AGENT RUNNER")
print("=" * 80)
print()

# Import only what we need
sys.path.insert(0, str(Path.cwd()))

from lib.agent_runtime import (
    AgentContext,
    AnthropicAgentRunner,
    ModelType,
    get_optimal_model
)

def run_agent_sync(runner, agent_name, context, requirements):
    """Run a single agent synchronously"""
    print(f"\n{'='*60}")
    print(f"[AGENT] {agent_name}")
    print(f"  Model: {get_optimal_model(agent_name)}")
    print(f"  Starting at: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 60)
    
    try:
        # Build prompt
        prompt = f"""You are {agent_name}, a specialized AI agent building a QuickShop MVP e-commerce application.

Project Requirements:
{json.dumps(requirements, indent=2)}

Previous agents completed:
{json.dumps([task if isinstance(task, str) else task.get('agent', 'unknown') for task in context.completed_tasks], indent=2)}

Your role: Complete your specialized tasks for this project. Create actual files with working code.
IMPORTANT: Use the write_file tool to create actual files. Include full content, not placeholders.
"""
        
        # Run agent synchronously
        success, result, updated_context = runner.run_agent_task(
            agent_name=agent_name,
            agent_prompt=prompt,
            context=context,
            model=get_optimal_model(agent_name),
            max_iterations=3  # Reduced for faster execution
        )
        
        end_time = datetime.now().strftime('%H:%M:%S')
        
        if success:
            print(f"  Status: [SUCCESS] at {end_time}")
            # Update context with completion
            context.completed_tasks.append({
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            # Store result in artifacts
            context.artifacts[agent_name] = result[:500] if result else "No output"
        else:
            print(f"  Status: [FAILED] at {end_time}")
            print(f"  Error: {result}")
            context.incomplete_tasks.append({
                "agent": agent_name,
                "error": str(result),
                "timestamp": datetime.now().isoformat()
            })
            
        return success, context
        
    except Exception as e:
        print(f"  Status: [ERROR] {str(e)}")
        return False, context

def main():
    """Main execution - NOT async to ensure sequential execution"""
    
    # Create output directory
    output_dir = Path("projects/quickshop-mvp-fixed")
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
        },
        "output_directory": str(output_dir)
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
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("[ERROR] No ANTHROPIC_API_KEY found!")
        print("Set it with: set ANTHROPIC_API_KEY=your-key-here")
        return
    
    print(f"API Key: {api_key[:20]}...")
    runner = AnthropicAgentRunner(api_key=api_key)
    
    # Import and register standard tools
    from lib.agent_runtime import create_standard_tools
    for tool in create_standard_tools():
        runner.register_tool(tool)
    
    # Define agent sequence - CRITICAL ORDER
    agents = [
        "requirements-analyst",    # Must run first
        "project-architect",      # Designs system
        "database-expert",        # Creates schema
        "rapid-builder",          # Builds backend
        "frontend-specialist",    # Builds frontend
        "api-integrator",        # Connects components
        "devops-engineer",       # Docker setup
        "quality-guardian"       # Final validation
    ]
    
    print(f"Output directory: {output_dir}")
    print(f"Agents to run: {len(agents)}")
    print(f"Execution mode: SEQUENTIAL (one at a time)")
    print("=" * 80)
    
    # Track execution
    start_time = time.time()
    successful_agents = []
    failed_agents = []
    
    # Run agents SEQUENTIALLY
    for i, agent in enumerate(agents, 1):
        print(f"\n[{i}/{len(agents)}] Executing: {agent}")
        
        # Add delay between agents to prevent rate limiting
        if i > 1:
            print("  Waiting 2 seconds before next agent...")
            time.sleep(2)
        
        success, context = run_agent_sync(runner, agent, context, requirements)
        
        if success:
            successful_agents.append(agent)
        else:
            failed_agents.append(agent)
            print(f"  [WARNING] {agent} failed, continuing with next agent...")
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Save final context
    context_file = output_dir / "final_context.json"
    with open(context_file, 'w') as f:
        json.dump(context.to_dict(), f, indent=2, default=str)
    
    # Save execution summary
    summary_file = output_dir / "execution_summary.md"
    with open(summary_file, 'w') as f:
        f.write("# Execution Summary\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Time**: {execution_time:.2f} seconds\n")
        f.write(f"**Successful Agents**: {len(successful_agents)}/{len(agents)}\n\n")
        f.write("## Successful Agents\n")
        for agent in successful_agents:
            f.write(f"- ✅ {agent}\n")
        f.write("\n## Failed Agents\n")
        for agent in failed_agents:
            f.write(f"- ❌ {agent}\n")
    
    print()
    print("=" * 80)
    print("EXECUTION COMPLETE")
    print("=" * 80)
    print()
    print(f"Execution Time: {execution_time:.2f} seconds")
    print(f"Successful: {len(successful_agents)}/{len(agents)} agents")
    print(f"Output: {output_dir}")
    print(f"Context: {context_file}")
    print(f"Summary: {summary_file}")
    
    # List created files
    print("\nFiles created:")
    for file in output_dir.rglob("*"):
        if file.is_file():
            print(f"  - {file.relative_to(output_dir)}")

if __name__ == "__main__":
    try:
        main()  # NOT asyncio.run() - run synchronously!
    except KeyboardInterrupt:
        print("\n[STOPPED] User cancelled")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()