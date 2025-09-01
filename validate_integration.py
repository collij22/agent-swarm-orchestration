#!/usr/bin/env python3
"""
Simple validation of Phase 1 & 2 integration
"""

import os
import sys
from pathlib import Path

def check_file_contains(filepath, search_text):
    """Check if file contains specific text."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return search_text in f.read()
    except:
        return False

def main():
    print("="*60)
    print("PHASE 1 & 2 INTEGRATION VALIDATION")
    print("="*60)
    
    checks = []
    
    # Phase 1 Checks
    print("\nPhase 1 Checks:")
    
    # 1.1 Automated debugger
    check1 = check_file_contains("lib/agent_runtime.py", "'automated-debugger'")
    print(f"  Automated-debugger registered: {'YES' if check1 else 'NO'}")
    checks.append(check1)
    
    # 1.2 UTF-8 encoding
    check2 = check_file_contains("lib/agent_runtime.py", "sys.stdout = io.TextIOWrapper")
    print(f"  UTF-8 encoding configured: {'YES' if check2 else 'NO'}")
    checks.append(check2)
    
    # 1.3 Phase 1 agents prioritized
    check3 = check_file_contains("lib/orchestration_enhanced.py", 'phase1_agents = ["requirements-analyst", "project-architect"]')
    print(f"  Phase 1 agents prioritized: {'YES' if check3 else 'NO'}")
    checks.append(check3)
    
    # 1.4 Max parallel = 3
    check4 = check_file_contains("orchestrate_enhanced.py", "max_parallel: int = 3")
    print(f"  Max parallel agents = 3: {'YES' if check4 else 'NO'}")
    checks.append(check4)
    
    # Phase 2 Checks
    print("\nPhase 2 Checks:")
    
    # 2.1 File coordinator exists
    check5 = Path("lib/file_coordinator.py").exists()
    print(f"  File coordinator exists: {'YES' if check5 else 'NO'}")
    checks.append(check5)
    
    # 2.2 Agent verification exists
    check6 = Path("lib/agent_verification.py").exists()
    print(f"  Agent verification exists: {'YES' if check6 else 'NO'}")
    checks.append(check6)
    
    # 2.3 Clean reasoning function
    check7 = check_file_contains("lib/agent_runtime.py", "def clean_reasoning")
    print(f"  Clean reasoning function: {'YES' if check7 else 'NO'}")
    checks.append(check7)
    
    # 2.4 Share artifact tool
    check8 = check_file_contains("lib/agent_runtime.py", "share_artifact_tool")
    print(f"  Share artifact tool: {'YES' if check8 else 'NO'}")
    checks.append(check8)
    
    # Integration Checks
    print("\nIntegration Checks:")
    
    # Phase 2 imports in orchestrator
    check9 = check_file_contains("orchestrate_enhanced.py", "from lib.phase2_integration import Phase2Integration")
    print(f"  Phase 2 imports added: {'YES' if check9 else 'NO'}")
    checks.append(check9)
    
    # Phase 2 initialization
    check10 = check_file_contains("orchestrate_enhanced.py", "self.phase2_integration = Phase2Integration")
    print(f"  Phase 2 initialized: {'YES' if check10 else 'NO'}")
    checks.append(check10)
    
    # Pre-execution hooks
    check11 = check_file_contains("orchestrate_enhanced.py", "self.phase2_integration.before_agent_execution")
    print(f"  Pre-execution hooks: {'YES' if check11 else 'NO'}")
    checks.append(check11)
    
    # Post-execution hooks
    check12 = check_file_contains("orchestrate_enhanced.py", "self.phase2_integration.after_agent_execution")
    print(f"  Post-execution hooks: {'YES' if check12 else 'NO'}")
    checks.append(check12)
    
    # Agent Verification Requirements
    print("\nAgent Verification:")
    agents_dir = Path(".claude/agents")
    total_agents = 0
    agents_with_verification = 0
    
    for agent_file in agents_dir.glob("*.md"):
        total_agents += 1
        if check_file_contains(agent_file, "MANDATORY VERIFICATION STEPS"):
            agents_with_verification += 1
    
    check13 = agents_with_verification == total_agents
    print(f"  Agents with verification: {agents_with_verification}/{total_agents}")
    checks.append(check13)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\nTotal Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("\n[SUCCESS] All Phase 1 & 2 components are integrated!")
        print("\nIntegration Complete:")
        print("  Phase 1: Critical Infrastructure [OK]")
        print("  Phase 2: Agent Enhancement [OK]")
        print("  Orchestration: Fully Integrated [OK]")
        print("  Agents: All Updated [OK]")
    else:
        print(f"\n[WARNING] {total - passed} checks failed")
        print("\nMissing Components:")
        if not check9 or not check10:
            print("  - Phase 2 integration not fully added to orchestrator")
        if not check11 or not check12:
            print("  - Phase 2 hooks not integrated")
        if not check13:
            print(f"  - {total_agents - agents_with_verification} agents missing verification")
    
    print("="*60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)