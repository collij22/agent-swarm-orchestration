#!/usr/bin/env python3
"""
BULLETPROOF RUNNER - All issues fixed
- No Unicode characters
- Correct method names
- Proper synchronous execution
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Force UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

print("=" * 80)
print("BULLETPROOF AGENT RUNNER - ALL ISSUES FIXED")
print("=" * 80)
print()

# Add path
sys.path.insert(0, str(Path.cwd()))

from lib.agent_runtime import (
    AgentContext,
    AnthropicAgentRunner,
    ModelType,
    get_optimal_model,
    create_standard_tools
)

def run_agent_sync(runner, agent_name, context, requirements):
    """Run a single agent synchronously using the CORRECT method"""
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
{json.dumps([task.get('agent', task) if isinstance(task, dict) else task for task in context.completed_tasks], indent=2)}

Your role: Complete your specialized tasks for this project. Create actual files with working code.

IMPORTANT: Use the available tools (write_file, run_command, etc.) to create actual files. Include full content, not placeholders."""
        
        # Use the CORRECT method: run_agent (not run_agent_task)
        success, result, updated_context = runner.run_agent(
            agent_name=agent_name,
            agent_prompt=prompt,
            context=context,
            model=get_optimal_model(agent_name),
            max_iterations=2  # Reduced for faster execution
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
            # Store result summary
            if result:
                context.artifacts[agent_name] = result[:200] + "..." if len(result) > 200 else result
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
    """Main execution - synchronous"""
    
    # Create output directory
    output_dir = Path("projects/quickshop-mvp-bulletproof")
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
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("[ERROR] No ANTHROPIC_API_KEY found!")
        print("Set it with: set ANTHROPIC_API_KEY=your-key-here")
        return
    
    print(f"API Key: {api_key[:20]}...")
    
    # Create runner
    runner = AnthropicAgentRunner(api_key=api_key)
    
    # Register tools properly
    tools = create_standard_tools()
    for tool in tools:
        runner.register_tool(tool)
    
    print(f"Registered {len(tools)} tools successfully")
    
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
            # Check for created files
            files_in_dir = list(output_dir.rglob("*"))
            file_count = len([f for f in files_in_dir if f.is_file() and f.name != "final_context.json"])
            print(f"  Files created so far: {file_count}")
        else:
            failed_agents.append(agent)
            print(f"  [WARNING] {agent} failed, continuing with next agent...")
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Save final context (with ASCII-safe encoding)
    context_file = output_dir / "final_context.json"
    with open(context_file, 'w', encoding='utf-8') as f:
        json.dump(context.to_dict(), f, indent=2, default=str, ensure_ascii=True)
    
    # Save execution summary (ASCII-safe)
    summary_file = output_dir / "execution_summary.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# Execution Summary\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Time**: {execution_time:.2f} seconds\n")
        f.write(f"**Successful Agents**: {len(successful_agents)}/{len(agents)}\n\n")
        f.write("## Successful Agents\n")
        for agent in successful_agents:
            f.write(f"- [OK] {agent}\n")  # No Unicode, just ASCII
        f.write("\n## Failed Agents\n")
        for agent in failed_agents:
            f.write(f"- [FAIL] {agent}\n")  # No Unicode, just ASCII
    
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
    file_count = 0
    for file in output_dir.rglob("*"):
        if file.is_file():
            file_count += 1
            print(f"  - {file.relative_to(output_dir)}")
    
    if file_count <= 2:  # Only context and summary
        print("\n[WARNING] No actual project files were created!")
        print("The agents may not be using tools correctly.")
    else:
        print(f"\n[SUCCESS] {file_count} files created!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOPPED] User cancelled")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()