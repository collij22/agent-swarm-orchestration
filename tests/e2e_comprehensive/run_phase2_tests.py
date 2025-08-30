#!/usr/bin/env python3
"""
Phase 2 Comprehensive Test Runner

Executes all Phase 2 E2E test scenarios and generates a consolidated report.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import time
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all test modules
from test_enterprise_crm import run_enterprise_crm_tests
from test_failure_recovery import run_failure_recovery_tests
from test_conflict_resolution import run_conflict_resolution_tests
from test_progressive_development import run_progressive_development_tests
from test_multi_language_stack import run_multi_language_stack_tests
from test_security_critical import run_security_critical_tests

class Phase2TestRunner:
    """Orchestrates execution of all Phase 2 comprehensive tests."""
    
    def __init__(self, verbose: bool = False, parallel: bool = False):
        """Initialize test runner."""
        self.verbose = verbose
        self.parallel = parallel
        self.results = {}
        self.summary = {}
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 2 test scenarios."""
        print("=" * 80)
        print("PHASE 2 COMPREHENSIVE E2E TEST SUITE")
        print("=" * 80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Execution Mode: {'Parallel' if self.parallel else 'Sequential'}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Define test scenarios
        test_scenarios = [
            ("Enterprise CRM", run_enterprise_crm_tests),
            ("Failure Recovery", run_failure_recovery_tests),
            ("Conflict Resolution", run_conflict_resolution_tests),
            ("Progressive Development", run_progressive_development_tests),
            ("Multi-Language Stack", run_multi_language_stack_tests),
            ("Security Critical", run_security_critical_tests)
        ]
        
        if self.parallel:
            # Run tests in parallel
            print("\nRunning tests in parallel...")
            tasks = [self._run_test_scenario(name, test_func) for name, test_func in test_scenarios]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for (name, _), result in zip(test_scenarios, results):
                if isinstance(result, Exception):
                    self.results[name] = {"error": str(result)}
                else:
                    self.results[name] = result
        else:
            # Run tests sequentially
            for name, test_func in test_scenarios:
                print(f"\n{'=' * 40}")
                print(f"Running: {name}")
                print('=' * 40)
                
                try:
                    result = await test_func()
                    self.results[name] = result
                    print(f"✓ {name} completed successfully")
                except Exception as e:
                    self.results[name] = {"error": str(e)}
                    print(f"✗ {name} failed: {e}")
        
        # Generate summary
        self.summary = self._generate_summary(time.time() - start_time)
        
        # Save consolidated results
        await self._save_results()
        
        # Print final summary
        self._print_summary()
        
        return {
            "results": self.results,
            "summary": self.summary
        }
    
    async def _run_test_scenario(self, name: str, test_func) -> Any:
        """Run a single test scenario."""
        try:
            if self.verbose:
                print(f"Starting {name}...")
            result = await test_func()
            if self.verbose:
                print(f"Completed {name}")
            return result
        except Exception as e:
            if self.verbose:
                print(f"Failed {name}: {e}")
            raise
    
    def _generate_summary(self, total_time: float) -> Dict[str, Any]:
        """Generate test execution summary."""
        summary = {
            "total_scenarios": len(self.results),
            "successful": 0,
            "failed": 0,
            "execution_time": total_time,
            "timestamp": datetime.now().isoformat(),
            "scenario_results": {}
        }
        
        for scenario, result in self.results.items():
            if "error" in result:
                summary["failed"] += 1
                summary["scenario_results"][scenario] = "FAILED"
            else:
                summary["successful"] += 1
                summary["scenario_results"][scenario] = "PASSED"
        
        summary["success_rate"] = (summary["successful"] / summary["total_scenarios"] * 100) if summary["total_scenarios"] > 0 else 0
        
        return summary
    
    async def _save_results(self):
        """Save consolidated test results."""
        output_dir = Path("tests/e2e_comprehensive/results")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        detailed_file = output_dir / f"phase2_detailed_results_{timestamp}.json"
        with open(detailed_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Save summary
        summary_file = output_dir / f"phase2_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(self.summary, f, indent=2, default=str)
        
        # Generate HTML report
        html_file = output_dir / f"phase2_report_{timestamp}.html"
        self._generate_html_report(html_file)
        
        print(f"\nResults saved:")
        print(f"  - Detailed: {detailed_file}")
        print(f"  - Summary: {summary_file}")
        print(f"  - HTML Report: {html_file}")
    
    def _generate_html_report(self, output_path: Path):
        """Generate HTML report of test results."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Phase 2 Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .passed {{ color: green; font-weight: bold; }}
                .failed {{ color: red; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background: #f2f2f2; }}
                .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric-box {{ background: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; text-align: center; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
            </style>
        </head>
        <body>
            <h1>Phase 2 Comprehensive E2E Test Report</h1>
            
            <div class="summary">
                <h2>Execution Summary</h2>
                <p><strong>Date:</strong> {self.summary['timestamp']}</p>
                <p><strong>Total Scenarios:</strong> {self.summary['total_scenarios']}</p>
                <p><strong>Execution Time:</strong> {self.summary['execution_time']:.2f} seconds</p>
            </div>
            
            <div class="metrics">
                <div class="metric-box">
                    <div class="metric-value passed">{self.summary['successful']}</div>
                    <div>Passed</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value failed">{self.summary['failed']}</div>
                    <div>Failed</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{self.summary['success_rate']:.1f}%</div>
                    <div>Success Rate</div>
                </div>
            </div>
            
            <h2>Scenario Results</h2>
            <table>
                <tr>
                    <th>Scenario</th>
                    <th>Status</th>
                    <th>Key Metrics</th>
                </tr>
        """
        
        for scenario, status in self.summary['scenario_results'].items():
            status_class = "passed" if status == "PASSED" else "failed"
            key_metrics = self._extract_key_metrics(scenario)
            html_content += f"""
                <tr>
                    <td>{scenario}</td>
                    <td class="{status_class}">{status}</td>
                    <td>{key_metrics}</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h2>Test Categories Covered</h2>
            <ul>
                <li><strong>Enterprise Complexity:</strong> Multi-tenant architecture, real-time features, compliance</li>
                <li><strong>Failure Handling:</strong> Retry logic, checkpoint restoration, partial completion</li>
                <li><strong>Conflict Resolution:</strong> Requirement negotiation, priority-based decisions</li>
                <li><strong>Progressive Development:</strong> Incremental enhancement, artifact reuse</li>
                <li><strong>Multi-Language Integration:</strong> Cross-language coordination, technology stack</li>
                <li><strong>Security Critical:</strong> Compliance validation, audit trails, data protection</li>
            </ul>
            
            <footer>
                <p><small>Generated by Phase 2 Test Runner</small></p>
            </footer>
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _extract_key_metrics(self, scenario: str) -> str:
        """Extract key metrics for a scenario."""
        if scenario not in self.results or "error" in self.results[scenario]:
            return "N/A - Test failed"
        
        # Extract scenario-specific metrics
        metrics = []
        
        if scenario == "Enterprise CRM":
            if "agent_coordination" in self.results[scenario]:
                phases = len(self.results[scenario]["agent_coordination"].get("phases_completed", []))
                metrics.append(f"{phases} phases completed")
        
        elif scenario == "Failure Recovery":
            if "exponential_backoff" in self.results[scenario]:
                recoveries = len(self.results[scenario]["exponential_backoff"].get("successful_recoveries", []))
                metrics.append(f"{recoveries} successful recoveries")
        
        elif scenario == "Conflict Resolution":
            if "conflict_detection" in self.results[scenario]:
                accuracy = self.results[scenario]["conflict_detection"].get("detection_accuracy", 0)
                metrics.append(f"{accuracy:.1f}% detection accuracy")
        
        elif scenario == "Progressive Development":
            if "incremental_development" in self.results[scenario]:
                overall = self.results[scenario]["incremental_development"].get("overall_metrics", {})
                features = overall.get("total_features_delivered", 0)
                metrics.append(f"{features} features delivered")
        
        elif scenario == "Multi-Language Stack":
            if "language_coordination" in self.results[scenario]:
                languages = len(self.results[scenario]["language_coordination"].get("language_agents", {}))
                metrics.append(f"{languages} languages coordinated")
        
        elif scenario == "Security Critical":
            if "compliance_checking" in self.results[scenario]:
                score = self.results[scenario]["compliance_checking"].get("compliance_score", 0)
                metrics.append(f"{score:.1f}% compliance score")
        
        return ", ".join(metrics) if metrics else "Tests executed successfully"
    
    def _print_summary(self):
        """Print test execution summary to console."""
        print("\n" + "=" * 80)
        print("PHASE 2 TEST EXECUTION COMPLETE")
        print("=" * 80)
        
        print(f"\nTotal Scenarios: {self.summary['total_scenarios']}")
        print(f"Successful: {self.summary['successful']} ✓")
        print(f"Failed: {self.summary['failed']} ✗")
        print(f"Success Rate: {self.summary['success_rate']:.1f}%")
        print(f"Execution Time: {self.summary['execution_time']:.2f} seconds")
        
        print("\nScenario Results:")
        for scenario, status in self.summary['scenario_results'].items():
            symbol = "✓" if status == "PASSED" else "✗"
            print(f"  {symbol} {scenario}: {status}")
        
        if self.summary['success_rate'] == 100:
            print("\n🎉 All tests passed successfully!")
        elif self.summary['success_rate'] >= 80:
            print("\n✅ Most tests passed. Review failures for improvements.")
        else:
            print("\n⚠️ Multiple test failures detected. Investigation required.")


async def main():
    """Main entry point for Phase 2 test runner."""
    parser = argparse.ArgumentParser(description="Run Phase 2 Comprehensive E2E Tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run tests in parallel")
    parser.add_argument("--scenario", "-s", type=str, help="Run specific scenario only")
    
    args = parser.parse_args()
    
    if args.scenario:
        # Run specific scenario
        scenario_map = {
            "crm": ("Enterprise CRM", run_enterprise_crm_tests),
            "failure": ("Failure Recovery", run_failure_recovery_tests),
            "conflict": ("Conflict Resolution", run_conflict_resolution_tests),
            "progressive": ("Progressive Development", run_progressive_development_tests),
            "multilang": ("Multi-Language Stack", run_multi_language_stack_tests),
            "security": ("Security Critical", run_security_critical_tests)
        }
        
        if args.scenario.lower() in scenario_map:
            name, test_func = scenario_map[args.scenario.lower()]
            print(f"Running single scenario: {name}")
            result = await test_func()
            print(f"\n{name} completed.")
        else:
            print(f"Unknown scenario: {args.scenario}")
            print(f"Available scenarios: {', '.join(scenario_map.keys())}")
    else:
        # Run all scenarios
        runner = Phase2TestRunner(verbose=args.verbose, parallel=args.parallel)
        await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())