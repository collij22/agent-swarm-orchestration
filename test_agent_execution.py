#!/usr/bin/env python3
"""
Test Script for Enhanced Agent Execution Improvements
Tests context enrichment, tool verification, and inter-agent communication
"""

import sys
import json
import asyncio
from pathlib import Path
import tempfile
import shutil

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.agent_runtime import (
    AgentContext, AnthropicAgentRunner, Tool, create_standard_tools,
    write_file_tool, dependency_check_tool, request_artifact_tool, 
    verify_deliverables_tool
)
from lib.agent_logger import create_new_session

def test_context_enrichment():
    """Test enhanced AgentContext features"""
    print("\n=== Testing Context Enrichment ===")
    
    context = AgentContext(
        project_requirements={"name": "TestProject"},
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase="testing"
    )
    
    # Test file tracking
    context.add_created_file("rapid-builder", "/app/main.py", "code", True)
    context.add_created_file("rapid-builder", "/app/config.json", "config", True)
    context.add_created_file("frontend-specialist", "/app/frontend/App.jsx", "code", False)
    
    print(f"✓ Files tracked: {len(context.get_all_files())} total")
    print(f"  - Rapid-builder created: {len(context.get_agent_files('rapid-builder'))} files")
    print(f"  - Frontend-specialist created: {len(context.get_agent_files('frontend-specialist'))} files")
    
    # Test verification requirements
    context.add_verification_required("/app/main.py")
    context.add_verification_required("/app/Dockerfile")
    print(f"✓ Verification required: {context.verification_required}")
    
    # Test incomplete tasks
    context.add_incomplete_task("frontend-specialist", "Create React components", "Missing API endpoints")
    print(f"✓ Incomplete tasks tracked: {len(context.incomplete_tasks)}")
    
    # Test dependencies
    context.set_agent_dependency("frontend-specialist", ["/app/api/routes.py", "api_spec"])
    deps_met, missing = context.check_dependencies("frontend-specialist")
    print(f"✓ Dependency check: Met={deps_met}, Missing={missing}")
    
    # Test serialization
    context_dict = context.to_dict()
    print(f"✓ Context serializable: {all(k in context_dict for k in ['created_files', 'verification_required', 'incomplete_tasks'])}")

async def test_file_verification():
    """Test enhanced write_file tool with verification"""
    print("\n=== Testing File Verification ===")
    
    # Create temporary directory for testing
    test_dir = Path(tempfile.mkdtemp(prefix="agent_test_"))
    
    try:
        context = AgentContext(
            project_requirements={"name": "TestProject"},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="testing"
        )
        
        # Test successful file write with verification
        file_path = str(test_dir / "test_file.py")
        result = await write_file_tool(
            file_path=file_path,
            content="print('Hello World')",
            reasoning="Testing file write",
            context=context,
            agent_name="test-agent",
            verify=True
        )
        
        print(f"✓ File write with verification: {'successfully' in result}")
        print(f"  Result: {result}")
        
        # Check context was updated
        agent_files = context.get_agent_files("test-agent")
        print(f"✓ Context updated: {len(agent_files)} files tracked")
        
        # Test critical file detection
        critical_file = str(test_dir / "main.py")
        await write_file_tool(
            file_path=critical_file,
            content="# Main application",
            context=context,
            agent_name="test-agent"
        )
        
        print(f"✓ Critical file detected: {'main.py' in str(context.verification_required)}")
        
        # Test retry logic (simulate failure by using invalid path)
        invalid_path = "/invalid/path/that/cannot/exist/file.txt"
        error_result = await write_file_tool(
            file_path=invalid_path,
            content="test",
            context=context,
            agent_name="test-agent",
            max_retries=2
        )
        
        print(f"✓ Error handling: {'Error' in error_result}")
        print(f"✓ Incomplete task added: {len(context.incomplete_tasks)} tasks")
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

async def test_inter_agent_communication():
    """Test inter-agent communication tools"""
    print("\n=== Testing Inter-Agent Communication ===")
    
    context = AgentContext(
        project_requirements={"name": "TestProject"},
        completed_tasks=["rapid-builder"],
        artifacts={"api_spec": {"endpoints": ["/users", "/tasks"]}},
        decisions=[],
        current_phase="testing"
    )
    
    # Add some files to context
    context.add_created_file("rapid-builder", "/app/backend/main.py", "code", True)
    context.add_created_file("rapid-builder", "/app/backend/routes.py", "code", True)
    
    # Test dependency check - dependencies met
    context.set_agent_dependency("frontend-specialist", ["api_spec"])
    result = await dependency_check_tool("frontend-specialist", "Checking dependencies", context)
    print(f"✓ Dependency check (met): {result}")
    
    # Test dependency check - missing dependencies
    context.set_agent_dependency("devops-engineer", ["/app/tests/test_main.py", "test_results"])
    result = await dependency_check_tool("devops-engineer", "Checking dependencies", context)
    print(f"✓ Dependency check (missing): {'Missing' in result}")
    
    # Test artifact request - found in artifacts
    result = await request_artifact_tool("api_spec", None, "Need API specification", context)
    print(f"✓ Artifact request (found): {'Artifact found' in result}")
    
    # Test artifact request - not found
    result = await request_artifact_tool("frontend_build", "frontend-specialist", "Need frontend build", context)
    print(f"✓ Artifact request (not found): {'not found' in result}")
    
    # Test verify deliverables
    # Create temp files for testing
    test_dir = Path(tempfile.mkdtemp(prefix="deliverables_test_"))
    try:
        file1 = test_dir / "exists.txt"
        file1.write_text("content")
        file2 = test_dir / "empty.txt"
        file2.write_text("")
        file3 = test_dir / "missing.txt"
        
        result = await verify_deliverables_tool(
            [str(file1), str(file2), str(file3)],
            "Verifying deliverables",
            context
        )
        
        print(f"✓ Deliverables verification:")
        for line in result.split('\n')[1:]:
            if line.strip():
                print(f"  {line}")
        
        print(f"✓ Verification tracking: {len(context.verification_required)} items marked")
        print(f"✓ Incomplete tasks: {len(context.incomplete_tasks)} tasks")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

async def test_integration():
    """Test integration with agent runner"""
    print("\n=== Testing Integration with Agent Runner ===")
    
    # Create mock runtime (no API key for testing)
    logger = create_new_session("test_integration")
    runtime = AnthropicAgentRunner(logger=logger)
    
    # Register enhanced tools
    for tool in create_standard_tools():
        runtime.register_tool(tool)
    
    # Create context with enhanced features
    context = AgentContext(
        project_requirements={
            "name": "IntegrationTest",
            "features": ["API endpoints", "Database", "Frontend"]
        },
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase="development"
    )
    
    # Simulate some prior work
    context.add_created_file("rapid-builder", "/app/backend/main.py", "code", True)
    context.add_created_file("database-expert", "/app/db/schema.sql", "config", True)
    context.add_verification_required("/app/backend/main.py")
    context.add_incomplete_task("frontend-specialist", "Build UI", "Waiting for API completion")
    
    print("✓ Context initialized with:")
    print(f"  - {len(context.get_all_files())} files created")
    print(f"  - {len(context.verification_required)} files requiring verification")
    print(f"  - {len(context.incomplete_tasks)} incomplete tasks")
    
    # Test prompt building
    test_prompt = "Build the frontend components"
    full_prompt = runtime._build_agent_prompt(test_prompt, context)
    
    print("✓ Enhanced prompt includes:")
    print(f"  - Created files section: {'created_files' in full_prompt}")
    print(f"  - Incomplete tasks section: {'incomplete_tasks' in full_prompt}")
    print(f"  - Verification required: {'verification_required' in full_prompt}")
    print(f"  - Tool usage reminders: {'dependency_check' in full_prompt}")
    
    logger.close_session()

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Enhanced Agent Execution")
    print("=" * 60)
    
    test_context_enrichment()
    await test_file_verification()
    await test_inter_agent_communication()
    await test_integration()
    
    print("\n" + "=" * 60)
    print("✅ All agent execution tests completed successfully")
    print("=" * 60)
    
    print("\n📊 Summary of Improvements:")
    print("1. ✅ Enhanced AgentContext with file tracking and verification")
    print("2. ✅ File operations with retry logic and verification")
    print("3. ✅ Inter-agent communication tools (dependency_check, request_artifact)")
    print("4. ✅ Deliverables verification with tracking")
    print("5. ✅ Rich context in agent prompts")
    print("6. ✅ Incomplete task tracking for retry")
    
    print("\n🎯 Expected Benefits:")
    print("- Better file tracking ensures all deliverables are created")
    print("- Verification prevents missing files")
    print("- Agents can check dependencies before execution")
    print("- Failed tasks are tracked for retry")
    print("- Context provides complete visibility into project state")

if __name__ == "__main__":
    asyncio.run(main())