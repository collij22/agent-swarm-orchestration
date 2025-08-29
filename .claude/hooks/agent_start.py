#!/usr/bin/env python3
"""
Agent Start Hook - Initialize agent session and load context

This hook is triggered when an agent starts execution.
It initializes logging, loads previous context, and prepares the workspace.
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
    """Initialize agent session"""
    
    # Get environment variables from Claude
    agent_name = os.getenv("CLAUDE_AGENT_NAME", "unknown")
    session_id = os.getenv("CLAUDE_SESSION_ID", None)
    project_path = os.getenv("CLAUDE_PROJECT_PATH", ".")
    
    # Initialize logger
    logger = get_logger(session_id)
    
    # Log agent start
    logger.log_agent_start(
        agent_name,
        f"Project: {project_path}",
        "Initializing agent session with context loading"
    )
    
    # Load previous context if available
    context_file = Path(project_path) / ".claude" / "context.json"
    if context_file.exists():
        with open(context_file) as f:
            context = json.load(f)
        logger.log_reasoning(
            agent_name,
            f"Loaded context with {len(context.get('completed_tasks', []))} completed tasks",
            "Continuing from previous session"
        )
    else:
        context = {
            "completed_tasks": [],
            "artifacts": {},
            "decisions": [],
            "session_start": datetime.now().isoformat()
        }
        logger.log_reasoning(
            agent_name,
            "No previous context found, starting fresh",
            "Initialize new session"
        )
    
    # Save context for agent use
    context["current_agent"] = agent_name
    context["session_id"] = session_id
    
    with open(context_file, 'w') as f:
        json.dump(context, f, indent=2)
    
    print(f"✅ Agent {agent_name} initialized with session {session_id}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())