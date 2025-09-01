#!/usr/bin/env python3
"""
Phase 1 & Phase 2 Integration Audit
Verifies that all Phase 1 and Phase 2 changes are properly integrated
into the orchestration system.
"""

import os
import sys
from pathlib import Path
import json
from typing import Dict, List, Tuple

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

class IntegrationAuditor:
    """Audits Phase 1 and Phase 2 integration status."""
    
    def __init__(self):
        self.results = {
            "phase1": {},
            "phase2": {},
            "orchestration_integration": {},
            "missing_integrations": []
        }
    
    def audit_phase1(self):
        """Audit Phase 1 components."""
        print("\n" + "="*60)
        print("PHASE 1 AUDIT: Critical Infrastructure Repairs")
        print("="*60)
        
        # 1.1 Automated Debugger Registration
        print("\n1.1 Automated Debugger Registration:")
        try:
            # Check directly in the file since import fails
            with open("lib/agent_runtime.py", 'r', encoding='utf-8') as f:
                content = f.read()
            has_debugger = "'automated-debugger'" in content and "AGENT_REGISTRY" in content
            print(f"  [{'PASS' if has_debugger else 'FAIL'}] automated-debugger in AGENT_REGISTRY")
            self.results["phase1"]["automated_debugger"] = has_debugger
        except Exception as e:
            print(f"  [FAIL] Error checking AGENT_REGISTRY: {e}")
            self.results["phase1"]["automated_debugger"] = False
        
        # 1.2 Character Encoding Fix
        print("\n1.2 Character Encoding Fix:")
        try:
            with open("lib/agent_runtime.py", 'r', encoding='utf-8') as f:
                content = f.read()
            has_encoding = "sys.stdout = io.TextIOWrapper" in content
            print(f"  [{'PASS' if has_encoding else 'FAIL'}] UTF-8 encoding wrapper in agent_runtime.py")
            self.results["phase1"]["encoding_fix"] = has_encoding
        except Exception as e:
            print(f"  [FAIL] Error checking encoding fix: {e}")
            self.results["phase1"]["encoding_fix"] = False
        
        # 1.3 Dependency Fixes (Check if pydantic is available)
        print("\n1.3 Dependency Fixes:")
        try:
            import pydantic
            print(f"  [PASS] pydantic available (version {pydantic.__version__})")
            has_pydantic = True
        except ImportError:
            print(f"  [INFO] pydantic not installed (may not be needed for orchestration)")
            has_pydantic = False
        self.results["phase1"]["pydantic"] = has_pydantic
        
        # 1.4 Workflow Phase Restoration
        print("\n1.4 Workflow Phase Restoration:")
        # Check if Phase 1 agents are prioritized
        phase1_agents = ["requirements-analyst", "project-architect"]
        print(f"  [INFO] Phase 1 agents should execute first: {phase1_agents}")
        self.results["phase1"]["workflow_phases"] = "manual_check_needed"
        
        # 1.5 Parallel Agent Configuration
        print("\n1.5 Parallel Agent Configuration:")
        try:
            with open("orchestrate_enhanced.py", 'r', encoding='utf-8') as f:
                content = f.read()
            has_max_parallel = "max_parallel: int = 3" in content or "max_parallel=3" in content
            print(f"  [{'PASS' if has_max_parallel else 'FAIL'}] max_parallel set to 3 in orchestrate_enhanced.py")
            self.results["phase1"]["max_parallel"] = has_max_parallel
        except Exception as e:
            print(f"  [FAIL] Error checking max_parallel: {e}")
            self.results["phase1"]["max_parallel"] = False
    
    def audit_phase2(self):
        """Audit Phase 2 components."""
        print("\n" + "="*60)
        print("PHASE 2 AUDIT: Agent Enhancement & Coordination")
        print("="*60)
        
        # 2.1 File Locking Mechanism
        print("\n2.1 File Locking Mechanism:")
        try:
            from file_coordinator import get_file_coordinator
            fc = get_file_coordinator()
            print(f"  [PASS] FileCoordinator available")
            print(f"    Statistics: {fc.get_statistics()}")
            self.results["phase2"]["file_coordinator"] = True
        except Exception as e:
            print(f"  [FAIL] FileCoordinator not available: {e}")
            self.results["phase2"]["file_coordinator"] = False
        
        # 2.2 Agent Verification Requirements
        print("\n2.2 Agent Verification Requirements:")
        try:
            from agent_verification import AgentVerification
            av = AgentVerification()
            has_template = hasattr(av, 'MANDATORY_VERIFICATION_TEMPLATE')
            print(f"  [{'PASS' if has_template else 'FAIL'}] AgentVerification has mandatory template")
            
            # Check if agents have verification requirements
            agents_dir = Path(".claude/agents")
            agents_with_verification = 0
            total_agents = 0
            
            for agent_file in agents_dir.glob("*.md"):
                total_agents += 1
                with open(agent_file, 'r', encoding='utf-8') as f:
                    if "MANDATORY VERIFICATION STEPS" in f.read():
                        agents_with_verification += 1
            
            print(f"  [INFO] {agents_with_verification}/{total_agents} agents have verification requirements")
            self.results["phase2"]["agent_verification"] = agents_with_verification == total_agents
        except Exception as e:
            print(f"  [FAIL] AgentVerification error: {e}")
            self.results["phase2"]["agent_verification"] = False
        
        # 2.3 Clean Reasoning Fix
        print("\n2.3 Clean Reasoning Fix:")
        try:
            # Check if clean_reasoning exists in agent_runtime
            with open("lib/agent_runtime.py", 'r', encoding='utf-8') as f:
                content = f.read()
            has_clean_reasoning = "def clean_reasoning" in content
            print(f"  [{'PASS' if has_clean_reasoning else 'FAIL'}] clean_reasoning function exists")
            self.results["phase2"]["clean_reasoning"] = has_clean_reasoning
        except Exception as e:
            print(f"  [FAIL] Error checking clean_reasoning: {e}")
            self.results["phase2"]["clean_reasoning"] = False
        
        # 2.4 Inter-Agent Communication
        print("\n2.4 Inter-Agent Communication:")
        try:
            # Check if share_artifact is in agent_runtime
            with open("lib/agent_runtime.py", 'r', encoding='utf-8') as f:
                content = f.read()
            has_share_artifact = "share_artifact_tool" in content
            print(f"  [{'PASS' if has_share_artifact else 'FAIL'}] share_artifact_tool in agent_runtime.py")
            self.results["phase2"]["share_artifact"] = has_share_artifact
        except Exception as e:
            print(f"  [FAIL] Error checking share_artifact: {e}")
            self.results["phase2"]["share_artifact"] = False
    
    def audit_orchestration_integration(self):
        """Check if Phase 1 & 2 components are integrated into orchestration."""
        print("\n" + "="*60)
        print("ORCHESTRATION INTEGRATION AUDIT")
        print("="*60)
        
        print("\nChecking orchestrate_enhanced.py integration:")
        
        try:
            with open("orchestrate_enhanced.py", 'r', encoding='utf-8') as f:
                orch_content = f.read()
            
            # Check for file coordinator usage
            uses_file_coordinator = "file_coordinator" in orch_content.lower() or "FileCoordinator" in orch_content
            print(f"  [{'PASS' if uses_file_coordinator else 'MISSING'}] FileCoordinator integration")
            if not uses_file_coordinator:
                self.results["missing_integrations"].append("FileCoordinator not used in orchestrate_enhanced.py")
            
            # Check for agent verification usage
            uses_verification = "agent_verification" in orch_content.lower() or "AgentVerification" in orch_content
            print(f"  [{'PASS' if uses_verification else 'MISSING'}] AgentVerification integration")
            if not uses_verification:
                self.results["missing_integrations"].append("AgentVerification not used in orchestrate_enhanced.py")
            
            # Check for clean_reasoning usage
            uses_clean_reasoning = "clean_reasoning" in orch_content
            print(f"  [{'PASS' if uses_clean_reasoning else 'MISSING'}] clean_reasoning integration")
            if not uses_clean_reasoning:
                self.results["missing_integrations"].append("clean_reasoning not used in orchestrate_enhanced.py")
            
            # Check for workflow phase enforcement
            enforces_phase1 = "requirements-analyst" in orch_content and "project-architect" in orch_content
            print(f"  [{'INFO' if enforces_phase1 else 'MISSING'}] Phase 1 agents mentioned")
            if not enforces_phase1:
                self.results["missing_integrations"].append("Phase 1 agents not explicitly prioritized")
            
            self.results["orchestration_integration"] = {
                "file_coordinator": uses_file_coordinator,
                "agent_verification": uses_verification,
                "clean_reasoning": uses_clean_reasoning,
                "phase1_enforcement": enforces_phase1
            }
            
        except Exception as e:
            print(f"  [ERROR] Failed to check orchestration integration: {e}")
    
    def generate_recommendations(self):
        """Generate recommendations for missing integrations."""
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        
        if self.results["missing_integrations"]:
            print("\n[CRITICAL] Missing Integrations Detected:")
            for missing in self.results["missing_integrations"]:
                print(f"  - {missing}")
            
            print("\n[ACTION REQUIRED] The following integrations should be added to orchestrate_enhanced.py:")
            print("""
1. Import Phase 2 components at the top:
   from lib.file_coordinator import get_file_coordinator
   from lib.agent_verification import AgentVerification
   from lib.agent_runtime import clean_reasoning
   from lib.phase2_integration import Phase2Integration

2. Initialize Phase2Integration in the orchestrator:
   self.phase2_integration = Phase2Integration(project_name)

3. Use file locking before agent execution:
   if self.phase2_integration.before_agent_execution(agent_name, files_to_modify):
       # Execute agent
   
4. Run verification after agent execution:
   results = self.phase2_integration.after_agent_execution(agent_name, created_files)
   
5. Clean reasoning output:
   cleaned_output = self.phase2_integration.clean_agent_reasoning(agent_name, raw_output)

6. Ensure Phase 1 agents execute first by adding dependencies
""")
        else:
            print("\n[SUCCESS] All Phase 1 & 2 components appear to be integrated!")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        phase1_pass = sum(1 for v in self.results["phase1"].values() if v is True)
        phase1_total = len(self.results["phase1"])
        phase2_pass = sum(1 for v in self.results["phase2"].values() if v is True)
        phase2_total = len(self.results["phase2"])
        
        print(f"\nPhase 1 Components: {phase1_pass}/{phase1_total} passing")
        print(f"Phase 2 Components: {phase2_pass}/{phase2_total} passing")
        print(f"Missing Integrations: {len(self.results['missing_integrations'])}")
        
        # Save results
        with open("phase1_phase2_audit_results.json", 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: phase1_phase2_audit_results.json")
    
    def run_full_audit(self):
        """Run complete audit."""
        print("="*60)
        print("PHASE 1 & 2 INTEGRATION AUDIT")
        print("="*60)
        
        self.audit_phase1()
        self.audit_phase2()
        self.audit_orchestration_integration()
        self.generate_recommendations()


if __name__ == "__main__":
    auditor = IntegrationAuditor()
    auditor.run_full_audit()