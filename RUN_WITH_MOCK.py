#!/usr/bin/env python3
"""
Run agents using Enhanced Mock Mode - Creates actual files without API calls
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Enable mock mode
os.environ['MOCK_MODE'] = 'true'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

print("=" * 80)
print("QUICKSHOP MVP BUILDER - MOCK MODE (Creates Real Files)")
print("=" * 80)
print()

# Import runtime
sys.path.insert(0, str(Path.cwd()))

from lib.agent_runtime import AgentContext
from lib.mock_anthropic_enhanced import MockAnthropicEnhancedRunner

def run_agent(runner, agent_name, context, requirements):
    """Run a single agent in mock mode"""
    print(f"\n[AGENT] {agent_name}")
    print(f"  Starting at: {datetime.now().strftime('%H:%M:%S')}")
    
    prompt = f"""You are {agent_name}, a specialized AI agent building a QuickShop MVP e-commerce application.

Project Requirements:
{json.dumps(requirements, indent=2)}

Previous work:
{json.dumps([t.get('agent', t) if isinstance(t, dict) else t for t in context.completed_tasks], indent=2)}

Output directory: {context.artifacts.get('output_dir')}

Your task: Complete your specialized role for this project. Create actual files with working code."""
    
    try:
        # Run agent in mock mode
        success, result, updated_context = runner.run_agent(
            agent_name=agent_name,
            agent_prompt=prompt,
            context=context,
            model="sonnet",  # Mock runner doesn't use real models
            max_iterations=1
        )
        
        if success:
            print(f"  Status: [SUCCESS]")
            # Get file system simulator stats
            if hasattr(runner, 'file_simulator'):
                files_created = len(runner.file_simulator.created_files)
                print(f"  Files created by this agent: {files_created}")
                for file_path in runner.file_simulator.created_files:
                    print(f"    - {file_path}")
            
            context.completed_tasks.append({
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
        else:
            print(f"  Status: [FAILED]")
            
        return success, context
        
    except Exception as e:
        print(f"  Status: [ERROR] {str(e)}")
        return False, context

def main():
    """Main execution"""
    
    print("Running in MOCK MODE - No API calls will be made")
    print("Files will be created in a temporary directory and copied to output")
    print()
    
    # Create output directory
    output_dir = Path("projects/quickshop-mvp-mock")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Requirements
    requirements = {
        "name": "QuickShop MVP",
        "type": "E-commerce platform",
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
            "database": "PostgreSQL",
            "deployment": "Docker"
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
    
    # Create mock runner
    runner = MockAnthropicEnhancedRunner()
    
    # Define agents
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
    
    # Run agents
    for i, agent in enumerate(agents, 1):
        print(f"\n[{i}/{len(agents)}] Running: {agent}")
        
        success, context = run_agent(runner, agent, context, requirements)
        
        if success:
            successful.append(agent)
    
    # Copy created files to output directory
    print("\n" + "=" * 80)
    print("COPYING FILES TO OUTPUT")
    print("-" * 80)
    
    if hasattr(runner, 'file_simulator') and runner.file_simulator.created_files:
        for src_path, content in runner.file_simulator.created_files.items():
            # Create relative path in output directory
            if src_path.startswith('/'):
                src_path = src_path[1:]
            
            dest_path = output_dir / src_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  Created: {dest_path.relative_to(output_dir)}")
    
    # Get requirement tracking summary
    if hasattr(runner, 'requirement_tracker'):
        summary = runner.requirement_tracker.get_summary()
        print(f"\nRequirement Tracking:")
        print(f"  Total: {summary['total']}")
        print(f"  Completed: {summary['completed']}")
        print(f"  Completion: {summary['percentage']}%")
    
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
    
    # List all files
    print("\nFiles in output directory:")
    files_created = 0
    for file in output_dir.rglob("*"):
        if file.is_file():
            files_created += 1
            size = file.stat().st_size
            print(f"  - {file.relative_to(output_dir)} ({size} bytes)")
    
    print(f"\nTotal files created: {files_created}")
    
    if files_created <= 1:
        print("\n[WARNING] No actual project files were created!")
        print("Check the mock implementation.")
    else:
        print("\n[SUCCESS] Files created successfully in mock mode!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOPPED] User cancelled")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()