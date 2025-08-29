#!/usr/bin/env python3
"""
Workflow Error Hook - Handle errors and attempt recovery

This hook is triggered when an error occurs during workflow execution.
It logs the error, saves state for recovery, and provides guidance.
"""

import json
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.agent_logger import get_logger

def main():
    """Handle workflow errors"""
    
    # Get environment variables
    agent_name = os.getenv("CLAUDE_AGENT_NAME", "unknown")
    session_id = os.getenv("CLAUDE_SESSION_ID", None)
    project_path = os.getenv("CLAUDE_PROJECT_PATH", ".")
    error_type = os.getenv("CLAUDE_ERROR_TYPE", "unknown")
    error_message = os.getenv("CLAUDE_ERROR_MESSAGE", "No error message provided")
    
    # Get logger
    logger = get_logger(session_id)
    
    # Log the error with reasoning
    logger.log_error(
        agent_name,
        f"{error_type}: {error_message}",
        "Attempting error recovery and state preservation"
    )
    
    # Load context to understand current state
    context_file = Path(project_path) / ".claude" / "context.json"
    if context_file.exists():
        with open(context_file) as f:
            context = json.load(f)
    else:
        context = {}
    
    # Save error checkpoint for recovery
    checkpoint_dir = Path(project_path) / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    
    error_checkpoint = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "error_type": error_type,
        "error_message": error_message,
        "context": context,
        "completed_tasks": context.get("completed_tasks", []),
        "recovery_suggestions": []
    }
    
    # Add recovery suggestions based on error type
    if "api" in error_type.lower() or "rate" in error_message.lower():
        error_checkpoint["recovery_suggestions"].append(
            "API rate limit or connection issue - wait and retry"
        )
        logger.log_reasoning(
            agent_name,
            "API issue detected, suggesting retry with backoff",
            "Implement exponential backoff"
        )
    
    elif "file" in error_type.lower() or "permission" in error_message.lower():
        error_checkpoint["recovery_suggestions"].append(
            "File or permission issue - check file paths and permissions"
        )
        logger.log_reasoning(
            agent_name,
            "File system issue detected, check paths and permissions",
            "Verify file access"
        )
    
    elif "memory" in error_type.lower() or "resource" in error_message.lower():
        error_checkpoint["recovery_suggestions"].append(
            "Resource exhaustion - reduce batch size or paralleli"
        )
        logger.log_reasoning(
            agent_name,
            "Resource issue detected, reduce load",
            "Optimize resource usage"
        )
    
    else:
        error_checkpoint["recovery_suggestions"].append(
            "Unknown error - review logs and retry with modifications"
        )
    
    # Save error checkpoint
    checkpoint_file = checkpoint_dir / f"error_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(checkpoint_file, 'w') as f:
        json.dump(error_checkpoint, f, indent=2)
    
    # Display error information and recovery guidance
    print(f"\n⚠️  Error in {agent_name}")
    print(f"Type: {error_type}")
    print(f"Message: {error_message}")
    print(f"\n📌 Recovery checkpoint saved: {checkpoint_file}")
    
    if error_checkpoint["recovery_suggestions"]:
        print("\n💡 Recovery suggestions:")
        for suggestion in error_checkpoint["recovery_suggestions"]:
            print(f"  • {suggestion}")
    
    print(f"\n🔄 To resume from checkpoint:")
    print(f"  uv run orchestrate_v2.py --checkpoint {checkpoint_file}")
    
    # Update context with error information
    context.setdefault("errors", []).append({
        "agent": agent_name,
        "timestamp": datetime.now().isoformat(),
        "type": error_type,
        "message": error_message[:200]
    })
    
    with open(context_file, 'w') as f:
        json.dump(context, f, indent=2)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())