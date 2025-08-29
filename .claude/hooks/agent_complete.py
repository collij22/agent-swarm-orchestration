#!/usr/bin/env python3
"""
Agent Complete Hook - Cleanup and save results after agent execution

This hook is triggered when an agent completes execution.
It saves artifacts, updates metrics, and performs cleanup.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.agent_logger import get_logger

def main():
    """Finalize agent session"""
    
    # Get environment variables
    agent_name = os.getenv("CLAUDE_AGENT_NAME", "unknown")
    session_id = os.getenv("CLAUDE_SESSION_ID", None)
    project_path = os.getenv("CLAUDE_PROJECT_PATH", ".")
    success = os.getenv("CLAUDE_AGENT_SUCCESS", "true").lower() == "true"
    
    # Get logger
    logger = get_logger(session_id)
    
    # Load context
    context_file = Path(project_path) / ".claude" / "context.json"
    if context_file.exists():
        with open(context_file) as f:
            context = json.load(f)
    else:
        context = {}
    
    # Update completed tasks
    if success and agent_name not in context.get("completed_tasks", []):
        context.setdefault("completed_tasks", []).append(agent_name)
    
    # Save any artifacts created
    artifacts_dir = Path(project_path) / "artifacts"
    if artifacts_dir.exists():
        artifacts = []
        for artifact_file in artifacts_dir.glob(f"{agent_name}_*"):
            artifacts.append(str(artifact_file.relative_to(project_path)))
        
        if artifacts:
            context.setdefault("artifacts", {})[agent_name] = artifacts
            logger.log_reasoning(
                agent_name,
                f"Saved {len(artifacts)} artifacts",
                "Preserving agent outputs"
            )
    
    # Log completion
    result_summary = f"Tasks completed: {len(context.get('completed_tasks', []))}"
    logger.log_agent_complete(agent_name, success, result_summary)
    
    # Save updated context
    context["last_update"] = datetime.now().isoformat()
    with open(context_file, 'w') as f:
        json.dump(context, f, indent=2)
    
    # Display summary
    status = "✅ Success" if success else "❌ Failed"
    print(f"{status}: Agent {agent_name} completed")
    print(f"  Completed tasks: {', '.join(context.get('completed_tasks', []))}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())