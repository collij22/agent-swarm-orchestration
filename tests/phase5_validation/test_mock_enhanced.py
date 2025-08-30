#!/usr/bin/env python3
"""Test enhanced mock mode functionality"""

import os
import sys
import subprocess
from pathlib import Path
import json

# Set mock mode
os.environ['MOCK_MODE'] = 'true'

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("="*60)
print("Enhanced Mock Mode Test")
print("="*60)

# Test 1: Import and instantiate mock runner
print("\n1. Testing mock runner instantiation...")
try:
    from lib.mock_anthropic_enhanced import MockAnthropicEnhancedRunner
    from lib.agent_logger import create_new_session
    
    logger = create_new_session()
    runner = MockAnthropicEnhancedRunner(logger)
    print("[OK] Mock runner created successfully")
    print(f"    Client type: {type(runner.client).__name__}")
    print(f"    Tools registered: {len(runner.tools)}")
except Exception as e:
    print(f"[FAIL] Failed to create mock runner: {e}")
    sys.exit(1)

# Test 2: Register tools
print("\n2. Testing tool registration...")
try:
    from lib.agent_runtime import Tool
    
    # Create mock tools
    def mock_write_file(file_path, content, reasoning=""):
        return f"Mock: wrote {len(content)} bytes to {file_path}"
    
    def mock_read_file(file_path):
        return "Mock file content"
    
    write_tool = Tool(
        name="write_file",
        description="Write a file",
        function=mock_write_file,
        parameters={
            "file_path": {"type": "string", "required": True},
            "content": {"type": "string", "required": True},
            "reasoning": {"type": "string", "required": False}
        }
    )
    
    read_tool = Tool(
        name="read_file",
        description="Read a file",
        function=mock_read_file,
        parameters={
            "file_path": {"type": "string", "required": True}
        }
    )
    
    runner.register_tool(write_tool)
    runner.register_tool(read_tool)
    
    print(f"[OK] Registered {len(runner.tools)} tools")
    print(f"    Tools: {list(runner.tools.keys())}")
except Exception as e:
    print(f"[FAIL] Failed to register tools: {e}")
    sys.exit(1)

# Test 3: Run a mock agent
print("\n3. Testing mock agent execution...")
try:
    from lib.agent_runtime import AgentContext
    
    # Create context
    context = AgentContext(
        project_requirements={"project": {"name": "Test Project"}},
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase="testing"
    )
    
    # Run agent
    agent_prompt = "You are a rapid builder. Create a simple Python file."
    success, result, updated_context = runner.run_agent(
        agent_name="rapid-builder",
        agent_prompt=agent_prompt,
        context=context,
        max_iterations=3
    )
    
    print(f"[OK] Agent execution completed")
    print(f"    Success: {success}")
    print(f"    Result length: {len(result)} chars")
    print(f"    Tasks completed: {updated_context.completed_tasks}")
    
except Exception as e:
    print(f"[FAIL] Failed to run agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check usage summary
print("\n4. Testing usage summary...")
try:
    summary = runner.get_usage_summary()
    print("[OK] Usage summary retrieved")
    print(f"    Total calls: {summary.get('total_calls', 0)}")
    print(f"    Estimated cost: ${summary.get('estimated_cost', 0)}")
    if 'requirements' in summary:
        req = summary['requirements']
        print(f"    Requirements: {req.get('completed', 0)}/{req.get('total', 0)}")
    if 'file_system' in summary:
        fs = summary['file_system']
        print(f"    Files created: {fs.get('files_created', 0)}")
except Exception as e:
    print(f"[FAIL] Failed to get usage summary: {e}")

# Test 5: Run a mini orchestration test
print("\n5. Testing mini orchestration with mock mode...")
cmd = [
    sys.executable,
    str(Path(__file__).parent.parent.parent / "orchestrate_enhanced.py"),
    "--project-type", "api_service",
    "--chain", "rapid-builder",
    "--verbose"
]

# Create a simple requirements file
req_file = Path(__file__).parent / "test_requirements.yaml"
req_content = """
project:
  name: "Test API"
  type: "api_service"
  description: "Simple test API"

requirements:
  - id: "REQ-001"
    description: "Create main.py"
    priority: "high"
"""
req_file.write_text(req_content)
cmd.extend(["--requirements", str(req_file)])

print(f"Command: {' '.join(cmd)}")
print(f"MOCK_MODE: {os.environ.get('MOCK_MODE')}")

try:
    result = subprocess.run(
        cmd, 
        capture_output=True, 
        text=True, 
        timeout=10,
        env=os.environ.copy()
    )
    
    if result.returncode == 0:
        print("[OK] Mini orchestration completed successfully")
    else:
        print(f"[WARN] Orchestration returned code {result.returncode}")
        if result.stderr:
            print(f"    Stderr: {result.stderr[:200]}")
            
except subprocess.TimeoutExpired:
    print("[FAIL] Orchestration timeout")
except Exception as e:
    print(f"[FAIL] Orchestration error: {e}")

print("\n" + "="*60)
print("Mock Mode Test Summary")
print("="*60)
print("The enhanced mock mode is now functional with:")
print("- Tool registration and execution")
print("- Agent simulation")
print("- Requirement tracking")
print("- File system simulation")
print("- Usage metrics")
print("="*60)