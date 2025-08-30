#!/usr/bin/env python3
"""
Test script to diagnose frontend-specialist agent failures
"""

import asyncio
import json
import os
from pathlib import Path
from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools
from lib.agent_logger import get_logger

# Try to use mock client if no API key
if not os.getenv("ANTHROPIC_API_KEY"):
    try:
        from lib.mock_anthropic_enhanced import EnhancedMockAnthropicClient
        print("Using enhanced mock client for testing")
    except ImportError:
        print("Enhanced mock client not available")

async def test_frontend_specialist():
    """Test frontend-specialist agent in isolation"""
    
    # Setup
    logger = get_logger()
    
    # Use mock client if no API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        runner = AnthropicAgentRunner(logger=logger)
        # Inject mock client with file creation enabled
        runner.client = EnhancedMockAnthropicClient(
            enable_file_creation=True,
            progress_tracking=True,
            deterministic=False  # Allow variation in responses
        )
    else:
        runner = AnthropicAgentRunner(logger=logger)
    
    # Register standard tools
    for tool in create_standard_tools():
        runner.register_tool(tool)
    
    # Create test context with a simple API backend
    context = AgentContext(
        project_requirements={
            "name": "TestFrontend",
            "type": "web_app",
            "features": [
                {"id": "AUTH-001", "name": "User authentication"},
                {"id": "CRUD-001", "name": "Task CRUD operations"}
            ]
        },
        completed_tasks=["rapid-builder"],  # Simulate backend already created
        artifacts={
            "project_directory": str(Path.cwd() / "test_frontend_output"),
            "backend_routes": {
                "/api/auth/login": {"method": "POST", "returns": "JWT token"},
                "/api/auth/register": {"method": "POST", "returns": "User object"},
                "/api/tasks": {"method": "GET", "returns": "Task list"},
                "/api/tasks/{id}": {"method": "GET", "returns": "Task object"},
                "/api/tasks": {"method": "POST", "returns": "Created task"},
                "/api/tasks/{id}": {"method": "PUT", "returns": "Updated task"},
                "/api/tasks/{id}": {"method": "DELETE", "returns": "Success"}
            }
        },
        decisions=[],
        current_phase="frontend"
    )
    
    # Read the agent prompt
    agent_prompt_path = Path(".claude/agents/frontend-specialist.md")
    if not agent_prompt_path.exists():
        print(f"ERROR: Agent prompt not found at {agent_prompt_path}")
        return
    
    agent_prompt = agent_prompt_path.read_text()
    
    # Extract just the prompt content (after the metadata)
    lines = agent_prompt.split('\n')
    prompt_start = 0
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 0:
            prompt_start = i + 1
            break
    
    agent_prompt_content = '\n'.join(lines[prompt_start:])
    
    # Add specific instructions for this test
    test_prompt = f"""
{agent_prompt_content}

SPECIFIC TASK FOR THIS TEST:
You have a backend API already created with the following endpoints:
{json.dumps(context.artifacts.get('backend_routes', {}), indent=2)}

Please create a React frontend application that:
1. Initializes a React + TypeScript project with Vite
2. Sets up Tailwind CSS
3. Creates an API client for the backend endpoints
4. Implements authentication components (Login and Register)
5. Creates Task CRUD components (List, Form, Detail)
6. Sets up routing with protected routes
7. Implements state management with Zustand

Create at minimum these files:
- frontend/package.json
- frontend/src/App.tsx
- frontend/src/main.tsx
- frontend/src/api/client.ts
- frontend/src/components/auth/Login.tsx
- frontend/src/components/auth/Register.tsx
- frontend/src/components/tasks/TaskList.tsx
- frontend/src/components/tasks/TaskForm.tsx
- frontend/src/stores/authStore.ts
- frontend/tailwind.config.js

Use the write_file tool to create each file with actual implementation code, not placeholders.
"""
    
    print("Starting frontend-specialist test...")
    print(f"Project directory: {context.artifacts['project_directory']}")
    print("-" * 50)
    
    # Run the agent
    try:
        success, result, updated_context = await runner.run_agent_async(
            agent_name="frontend-specialist",
            agent_prompt=test_prompt,
            context=context,
            max_iterations=15,  # Give it enough iterations
            temperature=0.7
        )
        
        print(f"\nAgent completed: {success}")
        print(f"Result summary: {result[:500] if result else 'No result'}")
        
        # Check files created
        files_created = updated_context.get_agent_files("frontend-specialist")
        print(f"\nFiles created: {len(files_created)}")
        for file_info in files_created:
            file_path = Path(file_info['path'])
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"  - {file_info['path']} ({size} bytes)")
            else:
                print(f"  - {file_info['path']} (NOT FOUND)")
        
        # Check for critical files
        critical_files = [
            "frontend/package.json",
            "frontend/src/App.tsx",
            "frontend/src/main.tsx",
            "frontend/src/api/client.ts"
        ]
        
        project_dir = Path(context.artifacts['project_directory'])
        print("\nCritical files check:")
        for file_rel in critical_files:
            file_path = project_dir / file_rel
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"  ✓ {file_rel} ({size} bytes)")
            else:
                print(f"  ✗ {file_rel} (missing)")
        
        # Save the session for analysis
        session_data = {
            "success": success,
            "files_created": len(files_created),
            "context": updated_context.to_dict()
        }
        
        session_file = Path("test_frontend_session.json")
        session_file.write_text(json.dumps(session_data, indent=2))
        print(f"\nSession saved to {session_file}")
        
    except Exception as e:
        print(f"ERROR during agent execution: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        logger.close_session()

if __name__ == "__main__":
    # Clean up any previous test
    import shutil
    test_dir = Path.cwd() / "test_frontend_output"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    # Run the test
    asyncio.run(test_frontend_specialist())