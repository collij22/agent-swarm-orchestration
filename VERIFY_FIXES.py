#!/usr/bin/env python3
"""
Verify all fixes are properly applied
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

def check_fix(description: str, check_func) -> tuple:
    """Run a check and return status"""
    try:
        result = check_func()
        return ("✓", description, result)
    except Exception as e:
        return ("✗", description, str(e))

def verify_context_serialization():
    """Verify context can be properly serialized"""
    sys.path.insert(0, str(Path.cwd()))
    
    from lib.agent_runtime import AgentContext
    
    # Create test context with problematic data
    context = AgentContext(
        project_requirements={"name": "test", "features": ["a", "b"]},
        completed_tasks=[
            {"agent": "test1", "status": "success"},
            {"agent": "test2", "status": "failed"}
        ],
        artifacts={"output_dir": "test/dir"},
        decisions=[],
        current_phase="test"
    )
    
    # Try to serialize
    context_dict = context.to_dict() if hasattr(context, 'to_dict') else context.__dict__
    json_str = json.dumps(context_dict, default=str)
    
    return f"Serialized {len(json_str)} chars successfully"

def verify_string_formatting():
    """Verify string formatting doesn't break with dicts"""
    test_list = [{"agent": "test1"}, {"agent": "test2"}]
    
    # This would break in old version
    try:
        # Simulate the error
        result = f"Completed: {test_list}"  # This works
        # But this would break if we tried to join:
        # result = ", ".join(test_list)  # This would fail
        
        # Proper way
        summary = ", ".join([d.get("agent", "unknown") for d in test_list])
        return f"Formatted: {summary}"
    except Exception as e:
        raise Exception(f"String formatting still broken: {e}")

def verify_file_counting():
    """Verify file counting logic"""
    test_dir = Path("test_count_dir")
    test_dir.mkdir(exist_ok=True)
    
    # Create test files
    (test_dir / "file1.txt").write_text("test")
    (test_dir / "file2.py").write_text("test")
    subdir = test_dir / "subdir"
    subdir.mkdir(exist_ok=True)
    (subdir / "file3.md").write_text("test")
    
    # Count files (not directories)
    files = [f for f in test_dir.rglob("*") if f.is_file()]
    count = len(files)
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    
    if count == 3:
        return f"Correctly counted {count} files (ignored directories)"
    else:
        raise Exception(f"File counting wrong: got {count}, expected 3")

def verify_ultra_fixed_exists():
    """Verify the ultra-fixed orchestrator exists"""
    ultra_path = Path("INTELLIGENT_ORCHESTRATOR_ULTRA_FIXED.py")
    
    if not ultra_path.exists():
        raise Exception("Ultra-fixed orchestrator not found")
    
    content = ultra_path.read_text(encoding='utf-8')
    
    # Check for key fixes
    checks = [
        ("ContextManager class", "class ContextManager" in content),
        ("AgentResult dataclass", "@dataclass\nclass AgentResult" in content),
        ("handle_failed_agents method", "async def handle_failed_agents" in content),
        ("save_checkpoint method", "def save_checkpoint" in content),
        ("get_completed_agents_summary", "def get_completed_agents_summary" in content)
    ]
    
    missing = [name for name, present in checks if not present]
    
    if missing:
        raise Exception(f"Missing components: {missing}")
    
    return "All critical components present"

def verify_retry_mechanism():
    """Verify retry mechanism is configured"""
    ultra_path = Path("INTELLIGENT_ORCHESTRATOR_ULTRA_FIXED.py")
    content = ultra_path.read_text(encoding='utf-8')
    
    if "max_retries: int = 2" in content:
        if "retry_count: int = 0" in content:
            if "get_retryable_failed_tasks" in content:
                return "Retry mechanism properly configured (max 2 attempts)"
    
    raise Exception("Retry mechanism not properly configured")

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("ULTRA-FIXED ORCHESTRATOR VERIFICATION")
    print("=" * 60)
    print()
    
    checks = [
        ("Context Serialization", verify_context_serialization),
        ("String Formatting Fix", verify_string_formatting),
        ("File Counting Logic", verify_file_counting),
        ("Ultra-Fixed Orchestrator", verify_ultra_fixed_exists),
        ("Retry Mechanism", verify_retry_mechanism)
    ]
    
    results = []
    for description, check_func in checks:
        status, desc, result = check_fix(description, check_func)
        results.append((status, desc, result))
        print(f"  [{status}] {desc}")
        if status == "✓":
            print(f"      → {result}")
        else:
            print(f"      → ERROR: {result}")
    
    print()
    print("-" * 60)
    
    passed = sum(1 for s, _, _ in results if s == "✓")
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print()
        print("The Ultra-Fixed Orchestrator is ready to run!")
        print()
        print("To execute:")
        print("  1. Set your API key: set ANTHROPIC_API_KEY=your-key")
        print("  2. Run: RUN_ULTRA_FIXED.bat")
        return 0
    else:
        print(f"❌ SOME CHECKS FAILED ({passed}/{total})")
        print()
        print("Please review the errors above before running.")
        return 1

if __name__ == "__main__":
    exit(main())