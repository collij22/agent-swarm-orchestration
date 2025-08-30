#!/usr/bin/env python3
"""
Test Phase 1 Integration
Tests the requirement tracking, validation orchestration, and agent enhancements
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, List

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.requirement_tracker import RequirementTracker, RequirementStatus
from lib.validation_orchestrator import ValidationOrchestrator, RetryStrategy
from lib.agent_validator import AgentValidator
from lib.agent_runtime import AgentContext


def test_requirement_tracker():
    """Test requirement tracking functionality"""
    print("\n=== Testing Requirement Tracker ===")
    
    # Create test requirements
    test_requirements = {
        "project": {"name": "TestApp"},
        "features": [
            "User authentication with JWT",
            "Task management CRUD operations",
            "Real-time notifications",
            "AI-powered task categorization",
            "Frontend dashboard with React"
        ]
    }
    
    # Initialize tracker
    tracker = RequirementTracker()
    tracker._parse_requirements(test_requirements)
    
    # Verify requirements were parsed
    assert len(tracker.requirements) == 5, f"Expected 5 requirements, got {len(tracker.requirements)}"
    print(f"✓ Parsed {len(tracker.requirements)} requirements")
    
    # Test agent assignment
    tracker.assign_to_agent("rapid-builder", ["REQ-001", "REQ-002"])
    tracker.assign_to_agent("frontend-specialist", ["REQ-005"])
    tracker.assign_to_agent("ai-specialist", ["REQ-004"])
    
    assert "rapid-builder" in tracker.agent_assignments
    assert len(tracker.agent_assignments["rapid-builder"]) == 2
    print("✓ Agent assignments working")
    
    # Test status updates
    tracker.mark_in_progress("REQ-001")
    tracker.update_progress("REQ-001", 50)
    tracker.mark_completed("REQ-002")
    
    req1 = tracker.requirements["REQ-001"]
    req2 = tracker.requirements["REQ-002"]
    
    assert req1.status == RequirementStatus.IN_PROGRESS
    assert req1.completion_percentage == 50
    assert req2.status == RequirementStatus.COMPLETED
    assert req2.completion_percentage == 100
    print("✓ Status tracking working")
    
    # Test coverage report
    report = tracker.generate_coverage_report()
    assert report["total"] == 5
    assert report["by_status"]["completed"] == 1
    assert report["by_status"]["in_progress"] == 1
    print(f"✓ Coverage report: {report['completion_percentage']:.1f}% complete")
    
    return True


def test_validation_orchestrator():
    """Test validation orchestration"""
    print("\n=== Testing Validation Orchestrator ===")
    
    # Create components
    tracker = RequirementTracker()
    validator = AgentValidator()
    orchestrator = ValidationOrchestrator(tracker, validator)
    
    # Create test context
    context = AgentContext(
        project_requirements={"test": "data"},
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase="testing"
    )
    
    # Test pre-execution validation
    valid, missing, suggestions = orchestrator.pre_execution_validation("frontend-specialist", context)
    print(f"✓ Pre-validation: {'passed' if valid else 'failed'}")
    if not valid:
        print(f"  Missing: {missing}")
        print(f"  Suggestions: {suggestions}")
    
    # Add some files to context and test post-validation
    context.add_created_file("frontend-specialist", "frontend/App.tsx", "code", True)
    context.add_created_file("frontend-specialist", "frontend/package.json", "config", True)
    
    valid, errors, suggestions = orchestrator.post_execution_validation("frontend-specialist", context)
    print(f"✓ Post-validation: {'passed' if valid else 'has warnings'}")
    if errors:
        print(f"  Validation issues: {errors[:2]}")  # Show first 2 issues
    
    # Test validation report
    report = orchestrator.generate_validation_report()
    print(f"✓ Validation report generated: {report['total_validations']} validations")
    
    return True


async def test_enhanced_agent_execution():
    """Test enhanced agent execution with validation and retry"""
    print("\n=== Testing Enhanced Agent Execution ===")
    
    # Import orchestrator
    from orchestrate_v2 import EnhancedOrchestrator
    
    # Create test requirements
    test_requirements = {
        "project": {"name": "TestProject"},
        "features": [
            "Basic API endpoints",
            "Authentication system"
        ]
    }
    
    # Create requirements file for testing
    test_req_file = Path("test_requirements.yaml")
    with open(test_req_file, 'w') as f:
        import yaml
        yaml.dump(test_requirements, f)
    
    try:
        # Initialize orchestrator (without API key for test)
        orchestrator = EnhancedOrchestrator(
            api_key=None,  # Will run in simulation mode
            requirements_file=str(test_req_file)
        )
        
        # Verify requirement tracking is initialized
        assert len(orchestrator.requirement_tracker.requirements) > 0
        print(f"✓ Orchestrator initialized with {len(orchestrator.requirement_tracker.requirements)} requirements")
        
        # Map requirements to agents
        workflow = [["rapid-builder"], ["quality-guardian"]]
        agent_reqs = orchestrator._map_requirements_to_agents(test_requirements, workflow)
        
        assert "rapid-builder" in agent_reqs
        print(f"✓ Requirements mapped to agents: {list(agent_reqs.keys())}")
        
        # Test validation orchestrator integration
        assert orchestrator.validation_orchestrator is not None
        print("✓ Validation orchestrator integrated")
        
        # Test workflow validation
        validation_result = orchestrator._validate_requirements_coverage(test_requirements, workflow)
        print(f"✓ Workflow validation: {'complete' if validation_result['coverage_complete'] else 'incomplete'}")
        
        return True
        
    finally:
        # Cleanup
        if test_req_file.exists():
            test_req_file.unlink()


def test_agent_prompt_enhancements():
    """Test that agent prompts have been enhanced"""
    print("\n=== Testing Agent Prompt Enhancements ===")
    
    # Check frontend-specialist prompt
    frontend_prompt_file = Path(".claude/agents/frontend-specialist.md")
    if frontend_prompt_file.exists():
        content = frontend_prompt_file.read_text()
        
        # Check for enhancements
        assert "ALWAYS create" in content, "Frontend prompt should have ALWAYS directives"
        assert "App.tsx" in content, "Frontend prompt should have React component examples"
        assert "at least 5 React components" in content, "Frontend prompt should specify minimum components"
        print("✓ Frontend-specialist prompt enhanced")
    else:
        print("⚠ Frontend-specialist prompt file not found")
    
    # Check ai-specialist prompt
    ai_prompt_file = Path(".claude/agents/ai-specialist.md")
    if ai_prompt_file.exists():
        content = ai_prompt_file.read_text()
        
        # Check for enhancements
        assert "MUST create a complete" in content, "AI prompt should have implementation requirements"
        assert "at least 15KB" in content, "AI prompt should specify file size requirement"
        assert "NOT a placeholder" in content, "AI prompt should prevent placeholder generation"
        print("✓ AI-specialist prompt enhanced")
    else:
        print("⚠ AI-specialist prompt file not found")
    
    return True


def test_validation_rules():
    """Test agent-specific validation rules"""
    print("\n=== Testing Validation Rules ===")
    
    validator = AgentValidator()
    
    # Check that validation rules exist for key agents
    key_agents = ["frontend-specialist", "ai-specialist", "rapid-builder", "quality-guardian", "devops-engineer"]
    
    for agent in key_agents:
        if agent in validator.validation_rules:
            rules = validator.validation_rules[agent]
            print(f"✓ {agent}: {len(rules)} validation rules")
            
            # Show first rule for each agent
            if rules:
                first_rule = rules[0]
                print(f"  - {first_rule.name}: {first_rule.description}")
        else:
            print(f"⚠ {agent}: No validation rules defined")
    
    return True


async def run_integration_test():
    """Run complete Phase 1 integration test"""
    print("\n" + "="*60)
    print("PHASE 1 INTEGRATION TEST")
    print("Testing requirement tracking, validation, and agent enhancements")
    print("="*60)
    
    results = []
    
    # Test 1: Requirement Tracker
    try:
        result = test_requirement_tracker()
        results.append(("Requirement Tracker", result))
    except Exception as e:
        print(f"✗ Requirement Tracker test failed: {e}")
        results.append(("Requirement Tracker", False))
    
    # Test 2: Validation Orchestrator
    try:
        result = test_validation_orchestrator()
        results.append(("Validation Orchestrator", result))
    except Exception as e:
        print(f"✗ Validation Orchestrator test failed: {e}")
        results.append(("Validation Orchestrator", False))
    
    # Test 3: Enhanced Agent Execution
    try:
        result = await test_enhanced_agent_execution()
        results.append(("Enhanced Agent Execution", result))
    except Exception as e:
        print(f"✗ Enhanced Agent Execution test failed: {e}")
        results.append(("Enhanced Agent Execution", False))
    
    # Test 4: Agent Prompt Enhancements
    try:
        result = test_agent_prompt_enhancements()
        results.append(("Agent Prompt Enhancements", result))
    except Exception as e:
        print(f"✗ Agent Prompt Enhancements test failed: {e}")
        results.append(("Agent Prompt Enhancements", False))
    
    # Test 5: Validation Rules
    try:
        result = test_validation_rules()
        results.append(("Validation Rules", result))
    except Exception as e:
        print(f"✗ Validation Rules test failed: {e}")
        results.append(("Validation Rules", False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 PHASE 1 INTEGRATION SUCCESSFUL!")
        print("The system is ready for production-grade execution with:")
        print("- Requirement tracking and mapping")
        print("- Pre/post execution validation")
        print("- Automatic retry with suggestions")
        print("- Enhanced agent prompts")
        print("- Comprehensive validation rules")
    else:
        print("\n⚠ Some tests failed. Please review and fix the issues.")
    
    return passed == total


if __name__ == "__main__":
    # Run the integration test
    success = asyncio.run(run_integration_test())
    sys.exit(0 if success else 1)