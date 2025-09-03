#!/usr/bin/env python3
"""
Quick diagnostic to verify intelligent orchestrator is ready
"""

import os
import sys
from pathlib import Path

def check_status():
    """Check system status"""
    print("="*60)
    print("INTELLIGENT ORCHESTRATOR - Quick Diagnostic")
    print("="*60)
    print()
    
    checks = []
    
    # 1. API Key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        checks.append(("[OK]", f"API Key: {api_key[:20]}..."))
    else:
        checks.append(("[FAIL]", "API Key: NOT SET"))
    
    # 2. Required files
    files = {
        "INTELLIGENT_ORCHESTRATOR.py": "Main orchestrator",
        "VERIFY_AND_RUN.py": "Verification runner",
        "START_INTELLIGENT.bat": "Easy start script",
        "lib/agent_runtime.py": "Agent runtime",
        "lib/agent_logger.py": "Agent logger"
    }
    
    for file, desc in files.items():
        if Path(file).exists():
            checks.append(("[OK]", f"{desc}: {file}"))
        else:
            checks.append(("[FAIL]", f"{desc}: {file} MISSING"))
    
    # 3. Check async method
    try:
        sys.path.insert(0, str(Path.cwd()))
        from lib.agent_runtime import AnthropicAgentRunner
        runner = AnthropicAgentRunner(api_key="test")
        
        if hasattr(runner, 'run_agent_async'):
            checks.append(("[OK]", "Async method: run_agent_async available"))
        elif hasattr(runner, 'run_agent'):
            checks.append(("[OK]", "Sync method: run_agent available (will use wrapper)"))
        else:
            checks.append(("[FAIL]", "No run_agent method found!"))
    except Exception as e:
        checks.append(("[WARN]", f"Method check: {str(e)[:50]}"))
    
    # Print results
    print("System Check Results:")
    print("-"*60)
    
    passed = 0
    failed = 0
    
    for status, msg in checks:
        print(f"  {status} {msg}")
        if status == "[OK]":
            passed += 1
        elif status == "[FAIL]":
            failed += 1
    
    print("-"*60)
    print(f"Passed: {passed}/{len(checks)}")
    
    if failed > 0:
        print("\n[ERROR] System not ready. Fix the issues above.")
        return False
    else:
        print("\n[SUCCESS] System ready!")
        print("\nTo run the intelligent orchestrator:")
        print("  1. Run: START_INTELLIGENT.bat")
        print("     OR")
        print("  2. Run: python VERIFY_AND_RUN.py")
        return True

if __name__ == "__main__":
    ready = check_status()
    sys.exit(0 if ready else 1)