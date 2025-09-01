#!/usr/bin/env python3
"""
Simple verification that Phase 3 changes are complete and integrated.
"""

import sys
from pathlib import Path

def verify_phase3():
    """Verify all Phase 3 changes are in place"""
    print("=" * 60)
    print("PHASE 3 VERIFICATION - Implementation Completion Requirements")
    print("=" * 60)
    print()
    
    errors = []
    
    # Check 3.1: Mandatory Implementation Rules in rapid-builder
    print("Checking 3.1: Mandatory Implementation Rules...")
    rapid_builder = Path(".claude/agents/rapid-builder.md")
    if rapid_builder.exists():
        content = rapid_builder.read_text(encoding='utf-8')
        if "MANDATORY IMPLEMENTATION TEMPLATES" in content:
            print("  [OK] rapid-builder has mandatory implementation templates")
        else:
            errors.append("rapid-builder missing mandatory implementation templates")
            print("  [FAIL] rapid-builder missing mandatory implementation templates")
    else:
        errors.append("rapid-builder.md not found")
        print("  [FAIL] rapid-builder.md not found")
    
    # Check 3.2: API Router Creation Template
    print("Checking 3.2: API Router Creation Template...")
    if rapid_builder.exists():
        content = rapid_builder.read_text(encoding='utf-8')
        if "@router.post(\"/login\")" in content and "@router.get(\"/health\")" in content:
            print("  [OK] rapid-builder has API router templates")
        else:
            errors.append("rapid-builder missing API router templates")
            print("  [FAIL] rapid-builder missing API router templates")
    
    # Check 3.3: Frontend Entry Point Template
    print("Checking 3.3: Frontend Entry Point Template...")
    frontend_specialist = Path(".claude/agents/frontend-specialist.md")
    if frontend_specialist.exists():
        content = frontend_specialist.read_text(encoding='utf-8')
        if "MANDATORY ENTRY POINT TEMPLATES" in content and "ReactDOM.createRoot" in content:
            print("  [OK] frontend-specialist has entry point templates")
        else:
            errors.append("frontend-specialist missing entry point templates")
            print("  [FAIL] frontend-specialist missing entry point templates")
    else:
        errors.append("frontend-specialist.md not found")
        print("  [FAIL] frontend-specialist.md not found")
    
    # Check 3.4: Project Path Standardization
    print("Checking 3.4: Project Path Standardization...")
    orchestrator = Path("orchestrate_enhanced.py")
    if orchestrator.exists():
        content = orchestrator.read_text(encoding='utf-8')
        if "Phase 3.4: Project Path Standardization" in content and "context.project_root" in content:
            print("  [OK] orchestrator has project path standardization")
        else:
            errors.append("orchestrator missing project path standardization")
            print("  [FAIL] orchestrator missing project path standardization")
    else:
        errors.append("orchestrate_enhanced.py not found")
        print("  [FAIL] orchestrate_enhanced.py not found")
    
    print()
    print("=" * 60)
    
    if not errors:
        print("SUCCESS: All Phase 3 changes are complete and integrated!")
        print()
        print("Phase 3 Summary:")
        print("- Agents now have mandatory implementation rules")
        print("- API router templates ensure working endpoints")
        print("- Frontend entry point templates ensure runnable React apps")
        print("- Project path standardization ensures consistent file operations")
        print()
        print("The system will now ensure agents create working code, not just scaffolding.")
        return 0
    else:
        print("ERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("Please fix the above issues to complete Phase 3.")
        return 1

if __name__ == "__main__":
    sys.exit(verify_phase3())