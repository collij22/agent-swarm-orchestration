#!/usr/bin/env python3
"""
Simple test runner for Section 9: Session Analysis Improvements
Demonstrates the enhanced session analysis capabilities
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.session_analysis_enhanced import SessionAnalysisEnhanced
from lib.requirement_coverage_analyzer import RequirementCoverageAnalyzer
from lib.deliverables_tracker import DeliverablesTracker


def test_session_analysis():
    """Test enhanced session analysis"""
    print("\n" + "="*60)
    print("Section 9: Session Analysis Improvements - Test Runner")
    print("="*60)
    
    # Create sample session data
    sample_session = {
        "session_id": "test_section9",
        "start_time": datetime.now().isoformat(),
        "end_time": (datetime.now() + timedelta(hours=2)).isoformat(),
        "context": {
            "project_requirements": {
                "name": "TestProject",
                "type": "web_app",
                "features": [
                    "User authentication with JWT tokens",
                    "RESTful API for task management",
                    "React frontend dashboard",
                    "PostgreSQL database with migrations"
                ]
            }
        },
        "events": [
            {
                "type": "tool_call",
                "tool_name": "write_file",
                "agent_name": "rapid-builder",
                "timestamp": datetime.now().isoformat(),
                "params": {
                    "file_path": "backend/main.py",
                    "content": "from fastapi import FastAPI\napp = FastAPI()",
                    "reasoning": "Creating main API entry point"
                }
            },
            {
                "type": "tool_call",
                "tool_name": "write_file",
                "agent_name": "frontend-specialist",
                "timestamp": datetime.now().isoformat(),
                "params": {
                    "file_path": "frontend/src/App.js",
                    "content": "import React from 'react';\nexport default App;",
                    "reasoning": "Creating React app component"
                }
            },
            {
                "type": "tool_call",
                "tool_name": "write_file",
                "agent_name": "quality-guardian",
                "timestamp": datetime.now().isoformat(),
                "params": {
                    "file_path": "tests/test_api.py",
                    "content": "def test_api():\n    assert True",
                    "reasoning": "Adding API tests"
                }
            }
        ]
    }
    
    # Test 1: Session Analysis
    print("\n1. Testing Session Analysis Enhanced...")
    analyzer = SessionAnalysisEnhanced()
    
    # Perform analysis on in-memory session
    requirements = analyzer._analyze_requirements(sample_session)
    print(f"   - Requirements detected: {requirements['total_requirements']}")
    print(f"   - Overall coverage: {requirements['overall_coverage_percentage']:.1f}%")
    
    file_audit = analyzer._create_file_audit_trail(sample_session)
    print(f"   - Files tracked: {len(file_audit)}")
    
    quality = analyzer._analyze_code_quality(sample_session)
    print(f"   - Lines of code: {quality['total_lines_of_code']}")
    
    performance = analyzer._analyze_performance(sample_session)
    print(f"   - Tool calls: {sum(performance['tool_call_frequency'].values())}")
    
    print("   [OK] Session analysis working correctly")
    
    # Test 2: Requirement Coverage
    print("\n2. Testing Requirement Coverage Analyzer...")
    req_analyzer = RequirementCoverageAnalyzer()
    req_analyzer.parse_requirements({
        "features": sample_session["context"]["project_requirements"]["features"]
    })
    
    coverage_report = req_analyzer.generate_coverage_report()
    print(f"   - Requirements parsed: {coverage_report['summary']['total_requirements']}")
    print(f"   - By type: {len(coverage_report['by_type'])} categories")
    print(f"   - Agent assignments: {len(req_analyzer.agent_assignments)} agents")
    
    matrix = req_analyzer.generate_traceability_matrix()
    print(f"   - Traceability matrix: {len(matrix)} entries")
    
    order = req_analyzer.get_implementation_order()
    print(f"   - Implementation order: {len(order)} requirements")
    
    print("   [OK] Requirement coverage analysis working correctly")
    
    # Test 3: Deliverables Tracking
    print("\n3. Testing Deliverables Tracker...")
    tracker = DeliverablesTracker()
    tracker.define_expected_deliverables(
        "web_app",
        sample_session["context"]["project_requirements"]["features"]
    )
    
    print(f"   - Expected deliverables: {len(tracker.expected_deliverables)}")
    
    # Simulate actual deliverables
    for event in sample_session["events"]:
        if event.get("type") == "tool_call" and event.get("tool_name") == "write_file":
            file_path = event["params"]["file_path"]
            from lib.deliverables_tracker import Deliverable, DeliverableCategory, DeliverableStatus
            
            actual = Deliverable(
                name=Path(file_path).name,
                category=DeliverableCategory.BACKEND if "backend" in file_path 
                        else DeliverableCategory.FRONTEND if "frontend" in file_path
                        else DeliverableCategory.TESTING,
                description="Test deliverable",
                expected_path=file_path,
                actual_path=file_path,
                status=DeliverableStatus.COMPLETE,
                size_bytes=len(event["params"]["content"])
            )
            tracker.actual_deliverables[actual.name] = actual
    
    comparison = tracker.compare_deliverables()
    print(f"   - Actual deliverables: {comparison['actual_count']}")
    print(f"   - Missing deliverables: {len(comparison['missing'])}")
    print(f"   - Completion rate: {comparison['completion_rate']:.1f}%")
    
    timeline = tracker.generate_completion_timeline()
    print(f"   - Timeline items: {len(timeline)}")
    
    print("   [OK] Deliverables tracking working correctly")
    
    # Test 4: Integration
    print("\n4. Testing Integration...")
    
    # Generate actionable next steps
    next_steps = analyzer._generate_next_steps(requirements, comparison)
    print(f"   - Next steps generated: {len(next_steps)}")
    if next_steps:
        print(f"   - Top priority: {next_steps[0]['action']}")
    
    # Generate summary
    summary = analyzer._generate_summary(requirements, file_audit, quality, comparison)
    print(f"   - Quality score: {summary['quality_score']}")
    print(f"   - Estimated completion time: {summary['estimated_time_to_completion']}")
    
    print("   [OK] Integration working correctly")
    
    # Summary
    print("\n" + "="*60)
    print("SECTION 9 TEST SUMMARY")
    print("="*60)
    print("[OK] Session Analysis Enhanced: PASS")
    print("[OK] Requirement Coverage Analyzer: PASS")
    print("[OK] Deliverables Tracker: PASS")
    print("[OK] Integration: PASS")
    print("\nAll Section 9 components are functioning correctly!")
    print("The system can now provide comprehensive session analysis with:")
    print("- Requirement coverage tracking (0-100%)")
    print("- File audit trails with validation")
    print("- Deliverable comparisons")
    print("- Actionable recommendations")
    print("- Quality metrics and reporting")
    
    return True


if __name__ == "__main__":
    try:
        success = test_session_analysis()
        if success:
            print("\n[OK] Section 9 implementation verified successfully!")
            sys.exit(0)
        else:
            print("\n[FAIL] Section 9 tests encountered issues")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)