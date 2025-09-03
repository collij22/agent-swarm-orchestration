#!/usr/bin/env python3
"""
Verify the optimized orchestrator is ready to run
"""

import os
import sys
from pathlib import Path
import json

def check(name: str, condition: bool, details: str = "") -> bool:
    """Print check result"""
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {name}")
    if details and condition:
        print(f"      -> {details}")
    elif details and not condition:
        print(f"      -> ERROR: {details}")
    return condition

def main():
    print("=" * 60)
    print("OPTIMIZED ORCHESTRATOR VERIFICATION")
    print("=" * 60)
    print()
    
    all_good = True
    
    # 1. Check API Key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    all_good &= check("API Key", 
                     bool(api_key),
                     f"{api_key[:20]}..." if api_key else "Not set")
    
    # 2. Check agent_runtime.py fix
    runtime_path = Path("lib/agent_runtime.py")
    if runtime_path.exists():
        content = runtime_path.read_text(encoding='utf-8')
        fixed = "str(task) if isinstance(task, str) else task.get('agent', 'unknown')" in content
        all_good &= check("agent_runtime.py Fix",
                         fixed,
                         "Line 825 handles both strings and dicts" if fixed else "Type error not fixed")
    else:
        all_good &= check("agent_runtime.py", False, "File not found")
    
    # 3. Check optimized orchestrator
    orch_path = Path("OPTIMIZED_ORCHESTRATOR.py")
    if orch_path.exists():
        content = orch_path.read_text(encoding='utf-8')
        
        has_comm_hub = "class CommunicationHub:" in content
        has_file_tracker = "class FileTracker:" in content
        has_artifact_sharing = "share_artifact" in content
        has_proper_strings = 'f"{agent_name}: SUCCESS' in content
        
        all_good &= check("CommunicationHub", has_comm_hub)
        all_good &= check("FileTracker", has_file_tracker)
        all_good &= check("Artifact Sharing", has_artifact_sharing)
        all_good &= check("String Handling", has_proper_strings,
                         "Uses strings for completed_tasks")
    else:
        all_good &= check("Optimized Orchestrator", False, "File not found")
    
    # 4. Check runner script
    runner_path = Path("RUN_OPTIMIZED.bat")
    all_good &= check("Runner Script", 
                     runner_path.exists(),
                     "RUN_OPTIMIZED.bat ready")
    
    # 5. Check Python environment
    try:
        sys.path.insert(0, str(Path.cwd()))
        from lib.agent_runtime import AnthropicAgentRunner
        runner = AnthropicAgentRunner(api_key="test")
        
        has_async = hasattr(runner, 'run_agent_async')
        has_sync = hasattr(runner, 'run_agent')
        
        all_good &= check("Agent Runner Methods",
                         has_async or has_sync,
                         f"async={has_async}, sync={has_sync}")
    except Exception as e:
        all_good &= check("Agent Runner", False, str(e)[:50])
    
    # 6. Check output directory
    output_dir = Path("projects/quickshop-mvp-optimized")
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    all_good &= check("Output Directory",
                     output_dir.exists(),
                     str(output_dir))
    
    # Summary
    print()
    print("-" * 60)
    
    if all_good:
        print("[SUCCESS] ALL CHECKS PASSED")
        print()
        print("The Optimized Orchestrator is ready to run!")
        print()
        print("To execute:")
        print("  1. Ensure API key is set (if not already)")
        print("  2. Run: RUN_OPTIMIZED.bat")
        print()
        print("Expected outcome:")
        print("  - All 8 agents will execute successfully")
        print("  - project-architect will NOT fail with type error")
        print("  - Files will be accurately tracked")
        print("  - Agents will share artifacts properly")
        return 0
    else:
        print("[ERROR] SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before running.")
        print()
        print("Critical fixes needed:")
        if not api_key:
            print("  - Set ANTHROPIC_API_KEY environment variable")
        if not (runtime_path.exists() and "isinstance(task, str)" in runtime_path.read_text()):
            print("  - Fix agent_runtime.py line 825")
        if not orch_path.exists():
            print("  - Create OPTIMIZED_ORCHESTRATOR.py")
        return 1

if __name__ == "__main__":
    exit(main())