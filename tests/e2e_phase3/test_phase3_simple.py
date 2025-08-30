#!/usr/bin/env python3
"""
Simple test script to verify Phase 3 implementation
Runs a subset of tests to quickly validate the implementation.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from test_agent_interaction_patterns import AgentInteractionPatternTester
from test_interagent_communication_tools import InterAgentCommunicationToolsTester
from test_quality_validation_tools import QualityValidationToolsTester
from enhanced_e2e_mock_client import EnhancedE2EMockClient
from lib.agent_runtime import AgentContext


async def test_interaction_patterns():
    """Test basic interaction patterns"""
    print("\n" + "="*60)
    print("Testing Agent Interaction Patterns")
    print("="*60)
    
    tester = AgentInteractionPatternTester(use_mock=True, verbose=True)
    
    try:
        tester.setup()
        
        # Test sequential dependencies
        print("\n1. Sequential Dependencies Test")
        result = await tester.test_sequential_dependencies()
        print(f"   Result: {'✓ PASSED' if result.success else '✗ FAILED'}")
        print(f"   Quality Score: {result.quality_score:.2%}")
        
        return result.success
        
    finally:
        tester.teardown()


async def test_communication_tools():
    """Test inter-agent communication tools"""
    print("\n" + "="*60)
    print("Testing Inter-Agent Communication Tools")
    print("="*60)
    
    tester = InterAgentCommunicationToolsTester(verbose=True)
    
    try:
        tester.setup()
        
        # Test dependency check tool
        print("\n1. Dependency Check Tool Test")
        results = await tester.test_dependency_check_tool()
        passed = sum(1 for r in results if r.success)
        print(f"   Result: {passed}/{len(results)} tests passed")
        
        return passed == len(results)
        
    finally:
        tester.teardown()


async def test_quality_validation():
    """Test quality validation tools"""
    print("\n" + "="*60)
    print("Testing Quality Validation Tools")
    print("="*60)
    
    tester = QualityValidationToolsTester(verbose=True)
    
    try:
        tester.setup()
        
        # Test validate requirements
        print("\n1. Validate Requirements Tool Test")
        results = await tester.test_validate_requirements()
        passed = sum(1 for r in results if r.success)
        avg_score = sum(r.validation_score for r in results) / len(results) if results else 0
        print(f"   Result: {passed}/{len(results)} tests passed")
        print(f"   Average Validation Score: {avg_score:.2f}")
        
        return passed > 0
        
    finally:
        tester.teardown()


async def test_enhanced_mock():
    """Test enhanced mock client"""
    print("\n" + "="*60)
    print("Testing Enhanced Mock Client")
    print("="*60)
    
    mock = EnhancedE2EMockClient(
        failure_mode="contextual",
        base_failure_rate=0.05,
        verbose=True
    )
    
    try:
        # Create test context
        context = AgentContext(
            project_requirements={
                "features": ["Authentication", "API", "Database"],
                "tech_stack": {"backend": "FastAPI", "frontend": "React"}
            },
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="planning"
        )
        
        # Test agent execution
        print("\n1. Mock Agent Execution Test")
        agents = ["project-architect", "rapid-builder"]
        successes = 0
        
        for agent in agents:
            success, output, context = await mock.execute_agent(
                agent,
                f"Execute {agent} tasks",
                context
            )
            if success:
                successes += 1
                print(f"   ✓ {agent} executed successfully")
            else:
                print(f"   ✗ {agent} failed: {output}")
        
        # Check metrics
        metrics = mock.get_execution_metrics()
        print(f"\n2. Execution Metrics:")
        print(f"   API Calls: {metrics['api_calls']}")
        print(f"   Estimated Cost: ${metrics['estimated_cost']:.4f}")
        print(f"   Artifacts Created: {metrics['artifact_count']}")
        
        # Check requirement coverage
        print(f"\n3. Requirement Coverage:")
        for req, coverage in metrics['requirement_coverage'].items():
            bar = "█" * int(coverage * 10) + "░" * (10 - int(coverage * 10))
            print(f"   {req:15} [{bar}] {coverage*100:.0f}%")
        
        return successes == len(agents)
        
    finally:
        mock.cleanup()


async def main():
    """Run all simple tests"""
    print("="*60)
    print("PHASE 3: SIMPLE TEST VALIDATION")
    print("="*60)
    print("\nThis script runs a subset of Phase 3 tests to validate")
    print("the implementation without running the full test suite.")
    
    # Track results
    results = []
    
    # Run tests
    tests = [
        ("Interaction Patterns", test_interaction_patterns),
        ("Communication Tools", test_communication_tools),
        ("Quality Validation", test_quality_validation),
        ("Enhanced Mock", test_enhanced_mock)
    ]
    
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} test failed with error: {e}")
            results.append((name, False))
    
    # Display summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ Phase 3 implementation validated successfully!")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)