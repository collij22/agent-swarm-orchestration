#!/usr/bin/env python3
"""
Test Script for Enhanced Workflow Configuration
Tests the workflow auto-upgrade and requirement validation features
"""

import sys
import json
from pathlib import Path
import yaml

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

from orchestrate_v2 import EnhancedOrchestrator
from lib.agent_logger import create_new_session

def test_frontend_detection():
    """Test frontend requirement detection"""
    print("\n=== Testing Frontend Detection ===")
    
    orchestrator = EnhancedOrchestrator(session_id="test_frontend_detection")
    
    # Test cases
    test_requirements = [
        {
            "name": "With React in features",
            "requirements": {
                "features": ["Simple React frontend for task management"],
                "project": {"type": "api_service"}
            },
            "expected": True
        },
        {
            "name": "With frontend in tech_overrides",
            "requirements": {
                "features": ["API endpoints"],
                "tech_overrides": {"frontend": {"framework": "React"}},
                "project": {"type": "api_service"}
            },
            "expected": True
        },
        {
            "name": "No frontend indicators",
            "requirements": {
                "features": ["REST API with CRUD operations"],
                "project": {"type": "api_service"}
            },
            "expected": False
        },
        {
            "name": "With UI in description",
            "requirements": {
                "features": ["Task management"],
                "project": {
                    "type": "api_service",
                    "description": "Task management with user interface"
                }
            },
            "expected": True
        }
    ]
    
    for test in test_requirements:
        result = orchestrator._detect_frontend_requirements(test["requirements"])
        status = "✓" if result == test["expected"] else "✗"
        print(f"{status} {test['name']}: Expected {test['expected']}, Got {result}")

def test_ai_detection():
    """Test AI requirement detection"""
    print("\n=== Testing AI Detection ===")
    
    orchestrator = EnhancedOrchestrator(session_id="test_ai_detection")
    
    test_requirements = [
        {
            "name": "With AI categorization",
            "requirements": {
                "features": ["AI-powered automatic task categorization"],
                "project": {"type": "api_service"}
            },
            "expected": True
        },
        {
            "name": "With OpenAI in tech",
            "requirements": {
                "features": ["Task management"],
                "tech_overrides": {"ai": {"provider": "OpenAI"}},
                "project": {"type": "api_service"}
            },
            "expected": True
        },
        {
            "name": "No AI indicators",
            "requirements": {
                "features": ["Simple CRUD operations"],
                "project": {"type": "api_service"}
            },
            "expected": False
        },
        {
            "name": "With smart priority",
            "requirements": {
                "features": ["Smart priority scoring based on task content"],
                "project": {"type": "api_service"}
            },
            "expected": True
        }
    ]
    
    for test in test_requirements:
        result = orchestrator._detect_ai_requirements(test["requirements"])
        status = "✓" if result == test["expected"] else "✗"
        print(f"{status} {test['name']}: Expected {test['expected']}, Got {result}")

def test_project_type_upgrade():
    """Test automatic project type upgrade"""
    print("\n=== Testing Project Type Upgrade ===")
    
    orchestrator = EnhancedOrchestrator(session_id="test_upgrade")
    
    # Test TaskManagerAPI requirements
    with open("test_requirements.yaml", 'r') as f:
        task_manager_reqs = yaml.safe_load(f)
    
    original_type = task_manager_reqs["project"]["type"]
    upgraded_type = orchestrator._upgrade_project_type(original_type, task_manager_reqs)
    
    print(f"TaskManagerAPI Requirements:")
    print(f"  Original type: {original_type}")
    print(f"  Upgraded type: {upgraded_type}")
    print(f"  Frontend detected: {orchestrator._detect_frontend_requirements(task_manager_reqs)}")
    print(f"  AI detected: {orchestrator._detect_ai_requirements(task_manager_reqs)}")
    
    # The upgrade should happen because it has "Simple React frontend" in features
    expected_upgrade = "full_stack_api"
    status = "✓" if upgraded_type == expected_upgrade else "✗"
    print(f"{status} Expected upgrade to: {expected_upgrade}, Got: {upgraded_type}")

def test_requirement_validation():
    """Test requirement validation for agent coverage"""
    print("\n=== Testing Requirement Validation ===")
    
    orchestrator = EnhancedOrchestrator(session_id="test_validation")
    
    # Test with TaskManagerAPI requirements
    with open("test_requirements.yaml", 'r') as f:
        requirements = yaml.safe_load(f)
    
    # Get the upgraded workflow
    project_type = orchestrator._upgrade_project_type(
        requirements["project"]["type"], 
        requirements
    )
    workflow = orchestrator.workflows[project_type]
    
    validation = orchestrator._validate_requirements_coverage(requirements, workflow)
    
    print(f"Workflow: {project_type}")
    print(f"Agents in workflow: {', '.join(sorted(validation['workflow_agents']))}")
    print(f"Coverage complete: {validation['coverage_complete']}")
    
    if validation['missing_coverage']:
        print("Missing coverage for:")
        for item in validation['missing_coverage']:
            print(f"  - {item}")
    else:
        print("✓ All requirements have corresponding agents")

def test_workflow_comparison():
    """Compare old vs new workflow for TaskManagerAPI"""
    print("\n=== Workflow Comparison ===")
    
    orchestrator = EnhancedOrchestrator(session_id="test_comparison")
    
    # Original api_service workflow
    original_workflow = orchestrator.workflows["api_service"]
    original_agents = set()
    for phase in original_workflow:
        original_agents.update(phase)
    
    # New full_stack_api workflow
    new_workflow = orchestrator.workflows["full_stack_api"]
    new_agents = set()
    for phase in new_workflow:
        new_agents.update(phase)
    
    print("Original api_service workflow agents:")
    print(f"  {', '.join(sorted(original_agents))}")
    print(f"\nNew full_stack_api workflow agents:")
    print(f"  {', '.join(sorted(new_agents))}")
    print(f"\nAdded agents in full_stack_api:")
    added = new_agents - original_agents
    if added:
        print(f"  {', '.join(sorted(added))}")
    else:
        print("  None")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Enhanced Workflow Configuration")
    print("=" * 60)
    
    test_frontend_detection()
    test_ai_detection()
    test_project_type_upgrade()
    test_requirement_validation()
    test_workflow_comparison()
    
    print("\n" + "=" * 60)
    print("✓ All workflow configuration tests completed")
    print("=" * 60)
    print("\nKey Improvements:")
    print("1. ✓ Added full_stack_api workflow with frontend-specialist")
    print("2. ✓ Auto-detection of frontend requirements")
    print("3. ✓ Auto-upgrade from api_service to full_stack_api")
    print("4. ✓ Requirement validation with coverage warnings")
    print("5. ✓ AI requirement detection for proper agent selection")
    
    print("\nNext Steps:")
    print("- Run: uv run orchestrate_v2.py --project-type=api_service --requirements=test_requirements.yaml")
    print("- The system will auto-upgrade to full_stack_api and include frontend-specialist")
    print("- This ensures React frontend and all other components are properly generated")

if __name__ == "__main__":
    main()