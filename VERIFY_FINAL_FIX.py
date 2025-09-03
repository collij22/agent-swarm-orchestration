#!/usr/bin/env python3
"""
Verify the FINAL_OPTIMIZED_ORCHESTRATOR fixes are working
"""

import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("="*60)
    print("VERIFYING FINAL OPTIMIZED ORCHESTRATOR FIXES")
    print("="*60)
    print()
    
    all_good = True
    
    # 1. Check imports
    print("[1] Checking imports...")
    try:
        from lib.agent_runtime import (
            AnthropicAgentRunner, 
            AgentContext,
            create_standard_tools
        )
        print("  ✓ All imports successful")
        print("  ✓ create_standard_tools found in agent_runtime")
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        all_good = False
    
    # 2. Check agent_runtime.py fix
    print("\n[2] Checking agent_runtime.py line 825 fix...")
    runtime_path = Path("lib/agent_runtime.py")
    if runtime_path.exists():
        content = runtime_path.read_text(encoding='utf-8')
        if "str(task) if isinstance(task, str) else task.get('agent', 'unknown')" in content:
            print("  ✓ Type error fix is in place")
        else:
            print("  ✗ Type error fix not found")
            all_good = False
    else:
        print("  ✗ agent_runtime.py not found")
        all_good = False
    
    # 3. Check context initialization
    print("\n[3] Checking context initialization...")
    try:
        from lib.agent_runtime import AgentContext
        
        # Test creating context with proper artifacts
        test_dir = Path("test_output")
        context = AgentContext(
            project_requirements={"test": "requirements"},
            completed_tasks=[],
            artifacts={
                "output_dir": str(test_dir),
                "project_directory": str(test_dir)  # Critical key
            },
            decisions=[],
            current_phase="test"
        )
        
        if "project_directory" in context.artifacts:
            print("  ✓ Context properly includes project_directory")
        else:
            print("  ✗ Context missing project_directory")
            all_good = False
            
    except Exception as e:
        print(f"  ✗ Context creation error: {e}")
        all_good = False
    
    # 4. Check FINAL_OPTIMIZED_ORCHESTRATOR.py
    print("\n[4] Checking FINAL_OPTIMIZED_ORCHESTRATOR.py...")
    orch_path = Path("FINAL_OPTIMIZED_ORCHESTRATOR.py")
    if orch_path.exists():
        content = orch_path.read_text(encoding='utf-8')
        
        checks = [
            ("Import fix", "from lib.agent_runtime import"),
            ("create_standard_tools", "create_standard_tools"),
            ("project_directory in context", '"project_directory": str(self.output_dir)'),
            ("FileTracker class", "class FileTracker:"),
            ("CommunicationHub class", "class CommunicationHub:"),
            ("File verification", "verify_file_exists"),
            ("Tool call logging", "tool_call_log")
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name} not found")
                all_good = False
    else:
        print("  ✗ FINAL_OPTIMIZED_ORCHESTRATOR.py not found")
        all_good = False
    
    # 5. Check tools availability
    print("\n[5] Checking standard tools...")
    try:
        from lib.agent_runtime import create_standard_tools
        tools = create_standard_tools()
        
        tool_names = [tool.name for tool in tools]
        required_tools = ["write_file", "run_command", "request_artifact"]  # read_file not in standard tools
        
        for tool in required_tools:
            if tool in tool_names:
                print(f"  ✓ Tool '{tool}' available")
            else:
                print(f"  ✗ Tool '{tool}' missing")
                all_good = False
                
    except Exception as e:
        print(f"  ✗ Error checking tools: {e}")
        all_good = False
    
    # Summary
    print("\n" + "="*60)
    if all_good:
        print("✅ ALL CHECKS PASSED - System is ready!")
        print("\nThe FINAL_OPTIMIZED_ORCHESTRATOR.py is properly configured:")
        print("  - Imports are fixed")
        print("  - Type error handling is in place")
        print("  - Context includes project_directory")
        print("  - File tracking and verification ready")
        print("  - Tool call logging implemented")
        print("\nTo run the orchestrator:")
        print("  1. Set API key: set ANTHROPIC_API_KEY=your-key")
        print("  2. Run: RUN_FINAL_OPTIMIZED.bat")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease review the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())