#!/usr/bin/env python3
"""
Test the complete human logging implementation
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_logger import create_new_session
from lib.human_logger import SummaryLevel

def test_mock_execution():
    """Simulate a mock agent execution with human logging"""
    print("=" * 60)
    print("Testing Human-Readable Logging with Mock Execution")
    print("=" * 60)
    print()
    
    # Create session with human logging enabled
    logger = create_new_session(
        enable_human_log=True,
        summary_level=SummaryLevel.DETAILED
    )
    
    print(f"Session ID: {logger.session_id}")
    print(f"Human log: {logger.human_logger.summary_file if logger.human_logger else 'Disabled'}")
    print()
    
    # Simulate agent execution flow
    agents = [
        ("api-integrator", ["PORTFOLIO-001", "DEVTOOLS-001"]),
        ("rapid-builder", ["PORTFOLIO-002", "BLOG-001"]),
        ("database-expert", ["DATABASE-001"]),
        ("frontend-specialist", ["FRONTEND-001"]),
    ]
    
    for agent_name, requirements in agents:
        print(f"Executing {agent_name}...")
        
        # Start agent
        context = {"requirements": requirements, "project": "DevPortfolio"}
        logger.log_agent_start(agent_name, str(context), f"Starting {agent_name} with requirements")
        
        # Simulate some work
        if agent_name == "api-integrator":
            logger.log_tool_call(agent_name, "write_file", 
                               {"file_path": "integrations/config.json"}, 
                               "Setting up API integrations")
            logger.log_tool_call(agent_name, "write_file", 
                               {"file_path": ".env.example"}, 
                               "Creating environment template")
            logger.log_reasoning(agent_name, "Analyzing API requirements", 
                               "OAuth2 for GitHub, API key for OpenAI")
            
        elif agent_name == "rapid-builder":
            files = ["main.py", "database.py", "config.json", "requirements.txt"]
            for file in files:
                logger.log_tool_call(agent_name, "write_file", 
                                   {"file_path": file}, 
                                   f"Creating {file}")
            logger.log_reasoning(agent_name, "Implementing core application", 
                               "Using FastAPI framework")
        
        elif agent_name == "database-expert":
            logger.log_tool_call(agent_name, "write_file", 
                               {"file_path": "models/user.py"}, 
                               "Creating database models")
            logger.log_reasoning(agent_name, "Designing database schema", 
                               "PostgreSQL with proper indexing")
            
        elif agent_name == "frontend-specialist":
            logger.log_tool_call(agent_name, "write_file", 
                               {"file_path": "frontend/App.tsx"}, 
                               "Creating React application")
            # Simulate an error and recovery
            logger.log_error(agent_name, "Module not found: @tanstack/react-query", 
                           "Missing dependency")
            logger.log_tool_call(agent_name, "run_command", 
                               {"command": "npm install @tanstack/react-query"}, 
                               "Installing missing dependency")
        
        # Complete agent
        logger.log_agent_complete(agent_name, True, f"{agent_name} completed successfully")
        
    # Close session and generate summary
    print("\nClosing session and generating summary...")
    logger.close_session()
    
    # Read and display the human-readable summary
    if logger.human_logger:
        print("\n" + "=" * 60)
        print("HUMAN-READABLE SUMMARY")
        print("=" * 60)
        with open(logger.human_logger.summary_file, 'r') as f:
            print(f.read())
    
    print("\n[SUCCESS] Human logging test completed!")
    return True

def main():
    """Run the test"""
    try:
        test_mock_execution()
        return 0
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())