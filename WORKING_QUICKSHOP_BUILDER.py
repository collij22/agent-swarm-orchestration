#!/usr/bin/env python3
"""
WORKING QuickShop Builder - Fixed tool calling
This version properly instructs agents to use the tool calling mechanism
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Force UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

print("=" * 80)
print("QUICKSHOP MVP BUILDER - WORKING VERSION")
print("=" * 80)
print()

# Import runtime
sys.path.insert(0, str(Path.cwd()))
from lib.agent_runtime import AgentContext, AnthropicAgentRunner, create_standard_tools, ModelType

def run_single_agent(runner, agent_name, context, requirements):
    """Run a single agent with proper tool instruction"""
    print(f"\n[AGENT] {agent_name}")
    print(f"  Starting at: {datetime.now().strftime('%H:%M:%S')}")
    
    # Build proper prompt that instructs on tool usage
    prompt = f"""You are {agent_name}, a specialized AI agent building a QuickShop MVP e-commerce application.

CRITICAL INSTRUCTIONS FOR TOOL USAGE:
- You have access to tools like write_file, run_command, read_file, etc.
- To use a tool, you MUST use the tool calling mechanism provided by the API
- DO NOT output XML tags like <write_file>...</write_file>
- DO NOT output JSON directly in your response
- Simply call the tool with the required parameters

Example of CORRECT tool usage:
When you need to create a file, use the write_file tool with:
- file_path: The path where the file should be created
- content: The COMPLETE content of the file (not placeholders)

Project Requirements:
{json.dumps(requirements, indent=2)}

Previous work completed:
{json.dumps([task.get('agent', task) if isinstance(task, dict) else task for task in context.completed_tasks], indent=2)}

Output directory: {context.artifacts.get('output_dir', 'projects/quickshop-mvp')}

Your specific role based on your agent type:
- requirements-analyst: Create detailed specifications and documentation
- project-architect: Design system architecture and structure  
- database-expert: Create database schema and migrations
- rapid-builder: Build the backend API with FastAPI
- frontend-specialist: Build the React frontend application
- api-integrator: Connect frontend to backend
- devops-engineer: Create Docker configuration
- quality-guardian: Validate and test the system

IMPORTANT: Create ACTUAL files with COMPLETE working code. Do not use placeholders.
Use the write_file tool to create each file with its full content."""
    
    try:
        # Run agent task
        success, result, updated_context = runner.run_agent_task(
            agent_name=agent_name,
            agent_prompt=prompt,
            context=context,
            model=ModelType.SONNET if agent_name != "project-architect" else ModelType.OPUS,
            max_iterations=2  # Reduced for faster execution
        )
        
        if success:
            print(f"  Status: [SUCCESS]")
            context.completed_tasks.append({
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            # Store a summary of the result
            if result:
                context.artifacts[agent_name] = result[:200] + "..." if len(result) > 200 else result
        else:
            print(f"  Status: [FAILED] {result}")
            
        return success, context
        
    except Exception as e:
        print(f"  Status: [ERROR] {str(e)}")
        return False, context

def main():
    """Main execution"""
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("[ERROR] No ANTHROPIC_API_KEY found!")
        print("Please set: set ANTHROPIC_API_KEY=your-key-here")
        return
    
    print(f"API Key: {api_key[:20]}...")
    
    # Create output directory
    output_dir = Path("projects/quickshop-mvp-working")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
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
    
    # Create runner and register tools
    runner = AnthropicAgentRunner(api_key=api_key)
    
    # Register all standard tools
    for tool in create_standard_tools():
        runner.register_tool(tool)
    
    print(f"Registered {len(runner.tools)} tools")
    
    # Define agent sequence
    agents = [
        "requirements-analyst",
        "database-expert",
        "rapid-builder",
        "frontend-specialist",
        "devops-engineer"
    ]
    
    print(f"Agents to run: {len(agents)}")
    print("=" * 80)
    
    # Track execution
    start_time = time.time()
    successful = []
    failed = []
    
    # Run agents SEQUENTIALLY
    for i, agent in enumerate(agents, 1):
        print(f"\n[{i}/{len(agents)}] Running: {agent}")
        
        # Add delay between agents
        if i > 1:
            print("  Waiting 3 seconds...")
            time.sleep(3)
        
        success, context = run_single_agent(runner, agent, context, requirements)
        
        if success:
            successful.append(agent)
            # Check if files were created
            files_in_dir = list(output_dir.rglob("*"))
            file_count = len([f for f in files_in_dir if f.is_file()])
            print(f"  Files created so far: {file_count}")
        else:
            failed.append(agent)
            print(f"  [WARNING] {agent} failed, continuing...")
    
    # Save context
    context_file = output_dir / "final_context.json"
    with open(context_file, 'w') as f:
        json.dump(context.to_dict(), f, indent=2, default=str)
    
    # Results
    execution_time = time.time() - start_time
    
    print()
    print("=" * 80)
    print("EXECUTION COMPLETE")
    print("=" * 80)
    print(f"Time: {execution_time:.2f} seconds")
    print(f"Successful: {len(successful)}/{len(agents)}")
    print(f"Output: {output_dir}")
    
    # List created files
    print("\nFiles created:")
    for file in output_dir.rglob("*"):
        if file.is_file() and file.name != "final_context.json":
            print(f"  - {file.relative_to(output_dir)}")
    
    if len(list(output_dir.rglob("*"))) <= 2:
        print("\n[WARNING] No actual files were created!")
        print("The agents may still be using XML format instead of tool calls.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOPPED] User cancelled")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()