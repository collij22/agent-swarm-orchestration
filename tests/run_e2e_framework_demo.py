#!/usr/bin/env python3
"""
E2E Test Framework Demo Runner

Demonstrates how to use the Phase 1 Enhanced Test Framework
for comprehensive agent swarm testing.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tests.e2e_infrastructure.workflow_engine import (
    AdvancedWorkflowEngine, WorkflowPhase, RequirementPriority, FailureInjection
)
from tests.e2e_infrastructure.interaction_validator import AgentInteractionValidator
from tests.e2e_infrastructure.metrics_collector import QualityMetricsCollector
from tests.e2e_infrastructure.test_data_generators import (
    TestDataGenerator, ProjectType, ComplexityLevel
)

async def run_enterprise_crm_scenario():
    """
    Scenario 1: Complex Enterprise Application
    Tests full agent coordination, dependency management, and quality validation
    """
    print("\n" + "="*80)
    print("SCENARIO 1: Enterprise CRM System")
    print("="*80)
    
    # Initialize components
    generator = TestDataGenerator(seed=42)
    engine = AdvancedWorkflowEngine(
        name="enterprise_crm",
        use_mock=True,
        checkpoint_dir=Path("tests/checkpoints")
    )
    validator = AgentInteractionValidator("crm_session")
    collector = QualityMetricsCollector("Enterprise CRM")
    
    # Generate complex project requirements
    project = generator.generate_project_requirements(
        ProjectType.ENTERPRISE_SYSTEM,
        ComplexityLevel.COMPLEX
    )
    
    print(f"\nProject: {project['name']}")
    print(f"Complexity: {project['complexity']}")
    print(f"Features: {len(project['features'])} requirements")
    print(f"Tech Stack: {json.dumps(project['tech_stack'], indent=2)}")
    
    # Generate requirements with dependencies and conflicts
    requirements = generator.generate_requirements_list(
        project,
        include_conflicts=True
    )
    
    # Add requirements to engine
    for req in requirements:
        engine.add_requirement(req)
        
    print(f"\nRequirements loaded: {len(requirements)}")
    print(f"Critical: {sum(1 for r in requirements if r.priority == RequirementPriority.CRITICAL)}")
    print(f"With dependencies: {sum(1 for r in requirements if r.dependencies)}")
    print(f"With conflicts: {sum(1 for r in requirements if r.conflicts_with)}")
    
    # Execute workflow
    print("\nExecuting workflow...")
    report = await engine.execute_workflow()
    
    # Display results
    print("\n" + "-"*40)
    print("WORKFLOW RESULTS")
    print("-"*40)
    print(f"Duration: {report['duration_seconds']:.2f} seconds")
    print(f"Requirements completed: {report['requirements']['completed']}/{report['requirements']['total']}")
    print(f"Agents executed: {report['agents']['total_executed']}")
    print(f"Agent success rate: {report['agents']['success_rate']:.1f}%")
    print(f"Conflicts resolved: {report['conflicts']['resolved']}/{report['conflicts']['detected']}")
    print(f"Overall quality score: {report['quality_scores'].get('overall', 0):.1f}%")
    
    return report

async def run_failure_recovery_scenario():
    """
    Scenario 2: Agent Recovery & Failure Handling
    Tests error recovery, partial completion, and checkpoint restoration
    """
    print("\n" + "="*80)
    print("SCENARIO 2: Failure Recovery Testing")
    print("="*80)
    
    # Initialize with failure injection
    generator = TestDataGenerator(seed=123)
    
    # Configure 30% failure rate
    failure_config = generator.generate_failure_injection_config(
        failure_rate=0.3,
        targeted_agents=["rapid-builder", "frontend-specialist"]
    )
    
    engine = AdvancedWorkflowEngine(
        name="failure_recovery",
        use_mock=True,
        failure_injection=failure_config
    )
    
    # Generate e-commerce project
    project = generator.generate_project_requirements(
        ProjectType.WEB_APP,
        ComplexityLevel.MEDIUM
    )
    
    print(f"\nProject: E-commerce Platform")
    print(f"Failure injection: {failure_config.enabled}")
    print(f"Failure rate: 30%")
    print(f"Targeted agents: rapid-builder, frontend-specialist")
    print(f"Recovery strategy: {failure_config.recovery_strategy}")
    print(f"Max retries: {failure_config.max_retries}")
    
    requirements = generator.generate_requirements_list(project)
    
    for req in requirements[:5]:  # Test with subset
        engine.add_requirement(req)
        
    # Execute with failure handling
    print("\nExecuting workflow with failures...")
    report = await engine.execute_workflow()
    
    # Display recovery results
    print("\n" + "-"*40)
    print("RECOVERY RESULTS")
    print("-"*40)
    print(f"Failed agents: {report['agents']['failed']}")
    print(f"Recovery attempts: {report['recovery']['attempts']}")
    print(f"Successful recoveries: {report['recovery']['successful']}")
    print(f"Recovery success rate: {report['recovery']['success_rate']:.1f}%")
    print(f"Checkpoints created: {report['checkpoints']}")
    
    return report

async def run_progressive_enhancement_scenario():
    """
    Scenario 4: Progressive Enhancement Workflow
    Tests incremental development, agent handoffs, and artifact reuse
    """
    print("\n" + "="*80)
    print("SCENARIO 3: Progressive Enhancement (Blog → CMS)")
    print("="*80)
    
    generator = TestDataGenerator(seed=456)
    validator = AgentInteractionValidator("progressive_session")
    collector = QualityMetricsCollector("Blog to CMS")
    
    # Phase 1: MVP Blog
    print("\n--- Phase 1: MVP Blog ---")
    engine_mvp = AdvancedWorkflowEngine("blog_mvp", use_mock=True)
    
    mvp_features = [
        "Basic blog with markdown support",
        "User authentication",
        "Simple commenting system"
    ]
    
    for i, feature in enumerate(mvp_features):
        req = generator.generate_requirements_list(
            {"features": [feature], "name": "BlogMVP"},
            include_conflicts=False
        )[0]
        engine_mvp.add_requirement(req)
        
    mvp_report = await engine_mvp.execute_workflow()
    print(f"MVP Completion: {mvp_report['requirements']['completion_rate']:.1f}%")
    
    # Phase 2: Enhancement
    print("\n--- Phase 2: Enhancement ---")
    engine_enhanced = AdvancedWorkflowEngine("blog_enhanced", use_mock=True)
    
    # Inherit context from MVP
    engine_enhanced.context = engine_mvp.context
    
    enhancement_features = [
        "Category management",
        "Tag system",
        "Search functionality"
    ]
    
    for feature in enhancement_features:
        req = generator.generate_requirements_list(
            {"features": [feature], "name": "BlogEnhanced"},
            include_conflicts=False
        )[0]
        engine_enhanced.add_requirement(req)
        
    enhanced_report = await engine_enhanced.execute_workflow()
    print(f"Enhancement Completion: {enhanced_report['requirements']['completion_rate']:.1f}%")
    
    # Phase 3: Full CMS
    print("\n--- Phase 3: Full CMS ---")
    engine_cms = AdvancedWorkflowEngine("full_cms", use_mock=True)
    
    # Inherit enhanced context
    engine_cms.context = engine_enhanced.context
    
    cms_features = [
        "Admin panel with RBAC",
        "Media management",
        "Content versioning",
        "Multi-language support"
    ]
    
    for feature in cms_features:
        req = generator.generate_requirements_list(
            {"features": [feature], "name": "FullCMS"},
            include_conflicts=False
        )[0]
        engine_cms.add_requirement(req)
        
    cms_report = await engine_cms.execute_workflow()
    print(f"CMS Completion: {cms_report['requirements']['completion_rate']:.1f}%")
    
    # Overall metrics
    print("\n" + "-"*40)
    print("PROGRESSIVE DEVELOPMENT RESULTS")
    print("-"*40)
    print(f"Total phases: 3")
    print(f"Total requirements: {len(mvp_features) + len(enhancement_features) + len(cms_features)}")
    print(f"Context preserved: Yes")
    print(f"Artifacts reused: {len(engine_cms.context.artifacts)}")
    
    return cms_report

async def run_comprehensive_quality_analysis():
    """
    Demonstrates comprehensive quality analysis across all dimensions
    """
    print("\n" + "="*80)
    print("COMPREHENSIVE QUALITY ANALYSIS")
    print("="*80)
    
    generator = TestDataGenerator(seed=789)
    collector = QualityMetricsCollector("Quality Test Project")
    
    # Generate a medium complexity project
    project = generator.generate_project_requirements(
        ProjectType.API_SERVICE,
        ComplexityLevel.MEDIUM
    )
    
    print(f"\nAnalyzing: {project['name']}")
    print(f"Requirements: {len(project['features'])}")
    
    # Simulate requirement completion with varying quality
    for i, feature in enumerate(project['features']):
        # Generate quality metrics with variation
        completion_level = 0.6 + (i * 0.05)  # Increasing completion
        metrics = generator.generate_quality_metrics(f"REQ-{i+1:03d}", completion_level)
        
        # Create requirement metric
        from tests.e2e_infrastructure.metrics_collector import RequirementMetric
        req_metric = RequirementMetric(
            requirement_id=f"REQ-{i+1:03d}",
            description=feature,
            priority="high" if i < 3 else "medium",
            files_created=[f"file_{i}.py" for _ in range(metrics["files_created"])],
            tests_created=[f"test_{i}.py" for _ in range(metrics["tests_created"])],
            completion_percentage=metrics["completion_percentage"]
        )
        
        collector.track_requirement(req_metric)
        
    # Generate quality report
    report = collector.generate_quality_report()
    
    # Display quality dimensions
    print("\n" + "-"*40)
    print("QUALITY DIMENSIONS")
    print("-"*40)
    for dimension, score in report["quality_dimensions"].items():
        bar = "█" * int(float(score[:-1]) / 10)  # Remove % and create bar
        print(f"{dimension:20} {score:>6} {bar}")
        
    # Display threshold compliance
    print("\n" + "-"*40)
    print("THRESHOLD COMPLIANCE")
    print("-"*40)
    for threshold, passed in report["threshold_compliance"].items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{threshold:20} {status}")
        
    # Display recommendations
    print("\n" + "-"*40)
    print("TOP RECOMMENDATIONS")
    print("-"*40)
    for i, recommendation in enumerate(report["recommendations"][:5], 1):
        print(f"{i}. {recommendation}")
        
    return report

async def main():
    """Main demo runner"""
    print("\n" + "="*80)
    print(" ENHANCED E2E TEST FRAMEWORK DEMONSTRATION ")
    print(" Phase 1 Implementation - Expert Developer Standards ")
    print("="*80)
    
    print("""
This demonstration showcases the Phase 1 Enhanced Test Framework with:
1. Advanced Workflow Engine - Progressive requirements & conflict resolution
2. Agent Interaction Validator - Communication testing & dependency chains
3. Quality Metrics Collector - Comprehensive quality tracking
4. Test Data Generators - Realistic scenario generation
    """)
    
    # Run scenarios
    scenarios = [
        ("Enterprise CRM", run_enterprise_crm_scenario),
        ("Failure Recovery", run_failure_recovery_scenario),
        ("Progressive Enhancement", run_progressive_enhancement_scenario),
        ("Quality Analysis", run_comprehensive_quality_analysis)
    ]
    
    results = {}
    
    for name, scenario_func in scenarios:
        try:
            print(f"\nRunning: {name}")
            results[name] = await scenario_func()
        except Exception as e:
            print(f"Error in {name}: {str(e)}")
            results[name] = {"error": str(e)}
            
    # Summary
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nThe Enhanced E2E Test Framework provides:")
    print("✓ Progressive requirement introduction with dependency management")
    print("✓ Conflict detection and resolution strategies")
    print("✓ Multi-phase checkpoint management for recovery")
    print("✓ Comprehensive agent interaction validation")
    print("✓ Quality metrics across 8 dimensions")
    print("✓ Realistic test data generation")
    print("✓ Production-ready integration testing")
    
    # Save results
    results_file = Path("tests/e2e_framework_results.json")
    results_file.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())