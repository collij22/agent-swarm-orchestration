#!/usr/bin/env python3
"""
Phase 3: Comprehensive Test Runner
Executes all Phase 3 tests with parallel execution support and comprehensive reporting.
Generates HTML and JSON reports with visualizations.

Production-ready test runner following CLAUDE.md standards.
"""

import asyncio
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import test modules
from test_agent_interaction_patterns import AgentInteractionPatternTester
from test_interagent_communication_tools import InterAgentCommunicationToolsTester
from test_quality_validation_tools import QualityValidationToolsTester
from enhanced_e2e_mock_client import EnhancedE2EMockClient


@dataclass
class TestSuiteResult:
    """Overall test suite results"""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time: float
    success_rate: float
    details: Dict[str, Any]


@dataclass
class Phase3TestReport:
    """Complete Phase 3 test report"""
    execution_date: str
    total_duration: float
    overall_success_rate: float
    test_suites: List[TestSuiteResult]
    summary_metrics: Dict[str, Any]
    recommendations: List[str]


class Phase3TestRunner:
    """
    Comprehensive test runner for Phase 3 tests.
    Executes all test suites and generates unified reports.
    """
    
    def __init__(
        self,
        parallel: bool = False,
        verbose: bool = False,
        use_mock: bool = True,
        output_dir: str = "test_results"
    ):
        """Initialize test runner"""
        self.parallel = parallel
        self.verbose = verbose
        self.use_mock = use_mock
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.test_results: List[TestSuiteResult] = []
        self.start_time = None
        self.end_time = None
    
    async def run_interaction_patterns_tests(self) -> TestSuiteResult:
        """Run agent interaction patterns tests"""
        print("\n" + "="*60)
        print("Running Agent Interaction Patterns Tests")
        print("="*60)
        
        start_time = time.time()
        tester = AgentInteractionPatternTester(use_mock=self.use_mock, verbose=self.verbose)
        
        try:
            tester.setup()
            
            # Run all interaction pattern tests
            test_methods = [
                ("Sequential Dependencies", tester.test_sequential_dependencies),
                ("Parallel Coordination", tester.test_parallel_coordination),
                ("Feedback Loops", tester.test_feedback_loops),
                ("Resource Sharing", tester.test_resource_sharing)
            ]
            
            if self.parallel:
                # Run tests in parallel
                tasks = [method() for _, method in test_methods]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # Run tests sequentially
                results = []
                for name, method in test_methods:
                    print(f"\nTesting {name}...")
                    result = await method()
                    results.append(result)
            
            # Process results
            passed = sum(1 for r in results if r and not isinstance(r, Exception) and r.success)
            failed = len(results) - passed
            
            # Generate report
            report = tester.generate_report()
            report_path = self.output_dir / "interaction_patterns_report.txt"
            report_path.write_text(report)
            
            return TestSuiteResult(
                suite_name="Agent Interaction Patterns",
                total_tests=len(results),
                passed_tests=passed,
                failed_tests=failed,
                execution_time=time.time() - start_time,
                success_rate=(passed / len(results)) if results else 0,
                details={
                    "test_results": [
                        {
                            "pattern": r.pattern.pattern_type if hasattr(r, 'pattern') else "unknown",
                            "success": r.success if hasattr(r, 'success') else False,
                            "quality_score": r.quality_score if hasattr(r, 'quality_score') else 0
                        }
                        for r in results if not isinstance(r, Exception)
                    ]
                }
            )
            
        finally:
            tester.teardown()
    
    async def run_communication_tools_tests(self) -> TestSuiteResult:
        """Run inter-agent communication tools tests"""
        print("\n" + "="*60)
        print("Running Inter-Agent Communication Tools Tests")
        print("="*60)
        
        start_time = time.time()
        tester = InterAgentCommunicationToolsTester(verbose=self.verbose)
        
        try:
            tester.setup()
            
            # Run all communication tools tests
            test_methods = [
                ("dependency_check tool", tester.test_dependency_check_tool),
                ("request_artifact tool", tester.test_request_artifact_tool),
                ("verify_deliverables tool", tester.test_verify_deliverables_tool),
                ("Integration scenarios", tester.test_integration_scenarios)
            ]
            
            all_results = []
            
            if self.parallel:
                # Run tests in parallel
                tasks = [method() for _, method in test_methods]
                results_lists = await asyncio.gather(*tasks, return_exceptions=True)
                for results in results_lists:
                    if not isinstance(results, Exception):
                        all_results.extend(results)
            else:
                # Run tests sequentially
                for name, method in test_methods:
                    print(f"\nTesting {name}...")
                    results = await method()
                    all_results.extend(results)
            
            # Process results
            passed = sum(1 for r in all_results if r.success)
            failed = len(all_results) - passed
            
            # Generate report
            report = tester.generate_report()
            report_path = self.output_dir / "communication_tools_report.txt"
            report_path.write_text(report)
            
            return TestSuiteResult(
                suite_name="Inter-Agent Communication Tools",
                total_tests=len(all_results),
                passed_tests=passed,
                failed_tests=failed,
                execution_time=time.time() - start_time,
                success_rate=(passed / len(all_results)) if all_results else 0,
                details={
                    "tools_tested": ["dependency_check", "request_artifact", "verify_deliverables"],
                    "integration_tests": 3,
                    "test_cases": len(all_results)
                }
            )
            
        finally:
            tester.teardown()
    
    async def run_quality_validation_tests(self) -> TestSuiteResult:
        """Run quality validation tools tests"""
        print("\n" + "="*60)
        print("Running Quality Validation Tools Tests")
        print("="*60)
        
        start_time = time.time()
        tester = QualityValidationToolsTester(verbose=self.verbose)
        
        try:
            tester.setup()
            
            # Run all quality validation tests
            test_methods = [
                ("validate_requirements", tester.test_validate_requirements),
                ("endpoint testing", tester.test_endpoint_testing),
                ("Docker validation", tester.test_docker_validation),
                ("completion report", tester.test_completion_report_generation)
            ]
            
            all_results = []
            
            if self.parallel:
                # Run tests in parallel
                tasks = [method() for _, method in test_methods]
                results_lists = await asyncio.gather(*tasks, return_exceptions=True)
                for results in results_lists:
                    if not isinstance(results, Exception):
                        all_results.extend(results)
            else:
                # Run tests sequentially
                for name, method in test_methods:
                    print(f"\nTesting {name}...")
                    results = await method()
                    all_results.extend(results)
            
            # Process results
            passed = sum(1 for r in all_results if r.success)
            failed = len(all_results) - passed
            avg_validation_score = sum(r.validation_score for r in all_results) / len(all_results) if all_results else 0
            
            # Generate report
            report = tester.generate_report()
            report_path = self.output_dir / "quality_validation_report.txt"
            report_path.write_text(report)
            
            return TestSuiteResult(
                suite_name="Quality Validation Tools",
                total_tests=len(all_results),
                passed_tests=passed,
                failed_tests=failed,
                execution_time=time.time() - start_time,
                success_rate=(passed / len(all_results)) if all_results else 0,
                details={
                    "average_validation_score": avg_validation_score,
                    "tools_tested": ["validate_requirements", "test_endpoints", "validate_docker", "generate_completion_report"],
                    "test_scenarios": len(all_results)
                }
            )
            
        finally:
            tester.teardown()
    
    async def run_enhanced_mock_tests(self) -> TestSuiteResult:
        """Run enhanced mock client tests"""
        print("\n" + "="*60)
        print("Running Enhanced Mock Client Tests")
        print("="*60)
        
        start_time = time.time()
        
        # Test different failure modes
        failure_modes = ["random", "contextual", "progressive"]
        test_results = []
        
        for mode in failure_modes:
            print(f"\nTesting failure mode: {mode}")
            
            mock = EnhancedE2EMockClient(
                failure_mode=mode,
                base_failure_rate=0.1,
                verbose=False
            )
            
            # Create test context
            context = AgentContext(
                project_requirements={
                    "features": ["auth", "api", "database", "frontend", "testing"],
                    "tech_stack": {"backend": "FastAPI", "frontend": "React"}
                },
                completed_tasks=[],
                artifacts={},
                decisions=[],
                current_phase="development"
            )
            
            # Execute test workflow
            agents = ["project-architect", "rapid-builder", "frontend-specialist", "quality-guardian"]
            successes = 0
            failures = 0
            
            for agent in agents:
                success, _, context = await mock.execute_agent(
                    agent,
                    f"Execute {agent} tasks",
                    context
                )
                if success:
                    successes += 1
                else:
                    failures += 1
            
            # Get metrics
            metrics = mock.get_execution_metrics()
            
            test_results.append({
                "mode": mode,
                "successes": successes,
                "failures": failures,
                "metrics": metrics
            })
            
            mock.cleanup()
        
        # Calculate overall results
        total_tests = sum(r["successes"] + r["failures"] for r in test_results)
        total_passed = sum(r["successes"] for r in test_results)
        
        return TestSuiteResult(
            suite_name="Enhanced Mock Client",
            total_tests=total_tests,
            passed_tests=total_passed,
            failed_tests=total_tests - total_passed,
            execution_time=time.time() - start_time,
            success_rate=(total_passed / total_tests) if total_tests else 0,
            details={
                "failure_modes_tested": failure_modes,
                "test_results": test_results
            }
        )
    
    async def run_all_tests(self) -> Phase3TestReport:
        """Run all Phase 3 tests"""
        self.start_time = time.time()
        
        print("\n" + "="*80)
        print("PHASE 3: AGENT INTERACTION PATTERNS TESTING")
        print("="*80)
        print(f"Execution Mode: {'Parallel' if self.parallel else 'Sequential'}")
        print(f"Using Mock: {self.use_mock}")
        print(f"Output Directory: {self.output_dir}")
        
        # Define test suites
        test_suites = [
            ("Interaction Patterns", self.run_interaction_patterns_tests),
            ("Communication Tools", self.run_communication_tools_tests),
            ("Quality Validation", self.run_quality_validation_tests),
            ("Enhanced Mock", self.run_enhanced_mock_tests)
        ]
        
        # Run test suites
        if self.parallel:
            print("\nRunning test suites in parallel...")
            tasks = [suite() for _, suite in test_suites]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            print("\nRunning test suites sequentially...")
            results = []
            for name, suite in test_suites:
                try:
                    result = await suite()
                    results.append(result)
                except Exception as e:
                    print(f"Error in {name}: {e}")
                    results.append(None)
        
        # Filter out exceptions and None results
        self.test_results = [r for r in results if r and not isinstance(r, Exception)]
        
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        # Calculate overall metrics
        total_tests = sum(r.total_tests for r in self.test_results)
        total_passed = sum(r.passed_tests for r in self.test_results)
        overall_success_rate = (total_passed / total_tests) if total_tests else 0
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Create report
        report = Phase3TestReport(
            execution_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_duration=total_duration,
            overall_success_rate=overall_success_rate,
            test_suites=self.test_results,
            summary_metrics={
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_tests - total_passed,
                "suites_executed": len(self.test_results),
                "execution_mode": "parallel" if self.parallel else "sequential"
            },
            recommendations=recommendations
        )
        
        # Generate reports
        self._generate_text_report(report)
        self._generate_json_report(report)
        self._generate_html_report(report)
        
        # Display summary
        self._display_summary(report)
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for suite in self.test_results:
            if suite.success_rate < 0.8:
                recommendations.append(f"Improve {suite.suite_name} - success rate only {suite.success_rate:.1%}")
            
            if suite.suite_name == "Agent Interaction Patterns":
                if suite.success_rate < 0.9:
                    recommendations.append("Strengthen agent coordination and communication patterns")
            
            elif suite.suite_name == "Inter-Agent Communication Tools":
                if suite.failed_tests > 0:
                    recommendations.append("Review and fix inter-agent communication tool implementations")
            
            elif suite.suite_name == "Quality Validation Tools":
                if suite.details.get("average_validation_score", 0) < 0.8:
                    recommendations.append("Enhance quality validation accuracy and coverage")
        
        if not recommendations:
            recommendations.append("All tests performing well - maintain current quality standards")
        
        return recommendations
    
    def _generate_text_report(self, report: Phase3TestReport):
        """Generate text report"""
        lines = ["="*80]
        lines.append("PHASE 3 TEST REPORT")
        lines.append("="*80)
        lines.append(f"Execution Date: {report.execution_date}")
        lines.append(f"Total Duration: {report.total_duration:.2f} seconds")
        lines.append(f"Overall Success Rate: {report.overall_success_rate:.1%}")
        lines.append("")
        
        lines.append("TEST SUITES")
        lines.append("-"*40)
        for suite in report.test_suites:
            lines.append(f"\n{suite.suite_name}")
            lines.append(f"  Tests: {suite.total_tests}")
            lines.append(f"  Passed: {suite.passed_tests}")
            lines.append(f"  Failed: {suite.failed_tests}")
            lines.append(f"  Success Rate: {suite.success_rate:.1%}")
            lines.append(f"  Execution Time: {suite.execution_time:.2f}s")
        
        lines.append("")
        lines.append("RECOMMENDATIONS")
        lines.append("-"*40)
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        
        lines.append("")
        lines.append("="*80)
        
        report_path = self.output_dir / "phase3_report.txt"
        report_path.write_text("\n".join(lines))
        print(f"\nText report saved to: {report_path}")
    
    def _generate_json_report(self, report: Phase3TestReport):
        """Generate JSON report"""
        # Convert to dictionary
        report_dict = {
            "execution_date": report.execution_date,
            "total_duration": report.total_duration,
            "overall_success_rate": report.overall_success_rate,
            "summary_metrics": report.summary_metrics,
            "test_suites": [asdict(suite) for suite in report.test_suites],
            "recommendations": report.recommendations
        }
        
        report_path = self.output_dir / "phase3_report.json"
        with open(report_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        print(f"JSON report saved to: {report_path}")
    
    def _generate_html_report(self, report: Phase3TestReport):
        """Generate HTML report with visualizations"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Phase 3 Test Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .suite-card {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background-color: #ecf0f1;
            border-radius: 15px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #27ae60, #2ecc71);
            display: flex;
            align-items: center;
            padding-left: 10px;
            color: white;
            font-weight: bold;
        }}
        .recommendations {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }}
        .status-pass {{ color: #27ae60; }}
        .status-fail {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Phase 3: Agent Interaction Patterns Test Report</h1>
        <p>Generated: {report.execution_date}</p>
    </div>
    
    <div class="summary">
        <div class="metric-card">
            <div class="metric-value">{report.summary_metrics['total_tests']}</div>
            <div class="metric-label">Total Tests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value class="status-pass">{report.summary_metrics['total_passed']}</div>
            <div class="metric-label">Passed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value class="status-fail">{report.summary_metrics['total_failed']}</div>
            <div class="metric-label">Failed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{report.overall_success_rate:.1%}</div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{report.total_duration:.1f}s</div>
            <div class="metric-label">Duration</div>
        </div>
    </div>
    
    <h2>Test Suites</h2>
"""
        
        for suite in report.test_suites:
            success_width = int(suite.success_rate * 100)
            html += f"""
    <div class="suite-card">
        <h3>{suite.suite_name}</h3>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {success_width}%">
                {suite.success_rate:.1%}
            </div>
        </div>
        <p>
            <span class="status-pass">✓ {suite.passed_tests} passed</span> | 
            <span class="status-fail">✗ {suite.failed_tests} failed</span> | 
            Total: {suite.total_tests} tests | 
            Time: {suite.execution_time:.2f}s
        </p>
    </div>
"""
        
        if report.recommendations:
            html += """
    <div class="recommendations">
        <h3>Recommendations</h3>
        <ul>
"""
            for rec in report.recommendations:
                html += f"            <li>{rec}</li>\n"
            
            html += """        </ul>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        report_path = self.output_dir / "phase3_report.html"
        report_path.write_text(html)
        print(f"HTML report saved to: {report_path}")
    
    def _display_summary(self, report: Phase3TestReport):
        """Display summary to console"""
        print("\n" + "="*80)
        print("TEST EXECUTION SUMMARY")
        print("="*80)
        print(f"Total Duration: {report.total_duration:.2f} seconds")
        print(f"Overall Success Rate: {report.overall_success_rate:.1%}")
        print(f"Total Tests: {report.summary_metrics['total_tests']}")
        print(f"Passed: {report.summary_metrics['total_passed']}")
        print(f"Failed: {report.summary_metrics['total_failed']}")
        
        print("\nSuite Results:")
        for suite in report.test_suites:
            status = "✓" if suite.success_rate >= 0.8 else "✗"
            print(f"  {status} {suite.suite_name}: {suite.success_rate:.1%} ({suite.passed_tests}/{suite.total_tests})")
        
        print("\nReports generated in:", self.output_dir)
        print("  - phase3_report.txt")
        print("  - phase3_report.json")
        print("  - phase3_report.html")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Phase 3 Test Runner")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--live", action="store_true", help="Use live API instead of mock")
    parser.add_argument("--output", default="test_results", help="Output directory for reports")
    
    args = parser.parse_args()
    
    # Create runner
    runner = Phase3TestRunner(
        parallel=args.parallel,
        verbose=args.verbose,
        use_mock=not args.live,
        output_dir=args.output
    )
    
    # Run all tests
    try:
        report = await runner.run_all_tests()
        
        # Exit with appropriate code
        if report.overall_success_rate >= 0.8:
            print("\n✓ Phase 3 tests completed successfully!")
            sys.exit(0)
        else:
            print("\n✗ Phase 3 tests completed with failures")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test execution failed: {e}")
        sys.exit(2)


if __name__ == "__main__":
    # Import AgentContext if needed
    from lib.agent_runtime import AgentContext
    
    asyncio.run(main())