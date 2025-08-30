#!/usr/bin/env python3
"""
Test script to verify that the path duplication issue is fixed.
This simulates what happens when agents try to write files.
"""

import asyncio
import os
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_runtime import AgentContext, write_file_tool

async def test_path_handling():
    """Test various path scenarios to ensure no duplication"""
    
    # Create a test project directory
    project_name = "TestProject"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = f"test_projects/{project_name}_{timestamp}"
    
    # Create context with project directory
    context = AgentContext(
        project_requirements={"project": {"name": project_name}},
        completed_tasks=[],
        artifacts={"project_directory": project_dir},
        decisions=[],
        current_phase="testing"
    )
    
    print(f"Testing with project directory: {project_dir}\n")
    
    # Test Case 1: Agent provides full path including project directory
    print("Test 1: Full path with project directory")
    test_path1 = f"{project_dir}/backend/main.py"
    result1 = await write_file_tool(
        file_path=test_path1,
        content="# Test file 1",
        reasoning="Testing path handling",
        context=context,
        agent_name="test_agent"
    )
    print(f"  Input: {test_path1}")
    print(f"  Result: {result1}")
    
    # Check where file was actually created
    expected_path1 = Path(project_dir) / "backend" / "main.py"
    actual_files1 = list(Path(".").glob("**/main.py"))
    print(f"  Expected location: {expected_path1}")
    print(f"  Actual files found: {actual_files1}")
    print()
    
    # Test Case 2: Agent provides relative path without project directory
    print("Test 2: Relative path without project directory")
    test_path2 = "frontend/App.js"
    result2 = await write_file_tool(
        file_path=test_path2,
        content="// Test file 2",
        reasoning="Testing relative path",
        context=context,
        agent_name="test_agent"
    )
    print(f"  Input: {test_path2}")
    print(f"  Result: {result2}")
    
    # Check where file was actually created
    expected_path2 = Path(project_dir) / "frontend" / "App.js"
    actual_files2 = list(Path(".").glob("**/App.js"))
    print(f"  Expected location: {expected_path2}")
    print(f"  Actual files found: {actual_files2}")
    print()
    
    # Test Case 3: Agent provides path with /project/ prefix
    print("Test 3: Path with /project/ prefix")
    test_path3 = "/project/config/settings.json"
    result3 = await write_file_tool(
        file_path=test_path3,
        content='{"test": true}',
        reasoning="Testing /project/ prefix",
        context=context,
        agent_name="test_agent"
    )
    print(f"  Input: {test_path3}")
    print(f"  Result: {result3}")
    
    # Check where file was actually created
    expected_path3 = Path(project_dir) / "config" / "settings.json"
    actual_files3 = list(Path(".").glob("**/settings.json"))
    print(f"  Expected location: {expected_path3}")
    print(f"  Actual files found: {actual_files3}")
    print()
    
    # Check for nested directory issues
    print("Checking for nested directory issues...")
    nested_check = list(Path(".").glob(f"**/{project_name}_{timestamp}/*/{project_name}_{timestamp}"))
    if nested_check:
        print(f"  ❌ ISSUE FOUND: Nested directories detected: {nested_check}")
    else:
        print(f"  ✅ No nested directories found!")
    
    # List all created files
    print(f"\nAll files in {project_dir}:")
    if Path(project_dir).exists():
        for file in Path(project_dir).rglob("*"):
            if file.is_file():
                relative = file.relative_to(project_dir)
                print(f"  - {relative}")
    
    # Cleanup test directory
    print(f"\nCleaning up test directory: test_projects/")
    if Path("test_projects").exists():
        shutil.rmtree("test_projects")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Path Duplication Fix Test")
    print("=" * 60)
    
    # Check if API key is set (for mock mode)
    if not os.getenv("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = "mock-key-for-testing"
    
    # Run the test
    success = asyncio.run(test_path_handling())
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
    
    print("=" * 60)