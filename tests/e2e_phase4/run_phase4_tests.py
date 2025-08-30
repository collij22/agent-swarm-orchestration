#!/usr/bin/env python3
"""
Phase 4 Test Runner - Comprehensive Mock Mode Testing Suite

Executes and analyzes 5 comprehensive test scenarios:
1. Open Source Library Development
2. Real-time Collaboration Platform  
3. DevOps Pipeline Automation
4. AI-Powered Content Management
5. Cross-Platform Game Development

Features:
- Sequential and parallel execution modes
- Comprehensive results analysis
- Performance metrics aggregation
- Issue tracking and recommendations
- HTML/JSON reporting
"""

import sys
import os
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import test scenarios
from tests.e2e_phase4.test_opensource_library import TestOpenSourceLibrary
from tests.e2e_phase4.test_realtime_collaboration import TestRealtimeCollaboration
from tests.e2e_phase4.test_devops_pipeline import TestDevOpsPipeline
from tests.e2e_phase4.test_ai_content_management import TestAIContentManagement
from tests.e2e_phase4.test_game_development import TestGameDevelopment

class Phase4TestRunner:
    """Orchestrates execution of Phase 4 comprehensive tests."""
    
    def __init__(self, parallel: bool = False, verbose: bool = False):
        """Initialize test runner.
        
        Args:
            parallel: Run tests in parallel if True
            verbose: Enable verbose output
        """
        self.parallel = parallel
        self.verbose = verbose
        self.results = []
        self.start_time = None
        self.end_time = None
        
        # Test scenarios
        self.test_scenarios = [
            ("Open Source Library", TestOpenSourceLibrary),
            ("Real-time Collaboration", TestRealtimeCollaboration),
            ("DevOps Pipeline", TestDevOpsPipeline),
            ("AI Content Management", TestAIContentManagement),
            ("Cross-Platform Game", TestGameDevelopment)
        ]
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test scenarios."""
        print("\n" + "="*80)
        print("PHASE 4 COMPREHENSIVE MOCK MODE TEST SUITE")
        print("="*80)
        print(f"Execution Mode: {'Parallel' if self.parallel else 'Sequential'}")
        print(f"Test Scenarios: {len(self.test_scenarios)}")
        print("="*80)
        
        self.start_time = time.time()
        
        if self.parallel:
            await self._run_parallel()
        else:
            await self._run_sequential()
        
        self.end_time = time.time()
        
        # Analyze results
        analysis = self._analyze_results()
        
        # Generate report
        report = self._generate_report(analysis)
        
        # Save results
        self._save_results(report)
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    async def _run_sequential(self):
        """Run tests sequentially."""
        for i, (name, test_class) in enumerate(self.test_scenarios, 1):
            print(f"\n[{i}/{len(self.test_scenarios)}] Running: {name}")
            print("-" * 40)
            
            try:
                test = test_class()
                result = await test.run_test()
                self.results.append(result)
                
                if self.verbose:
                    print(f"✓ Completed: {name}")
                    print(f"  Duration: {result['duration']:.2f}s")
                    print(f"  Completion: {result['requirements']['completion_percentage']:.1f}%")
            
            except Exception as e:
                print(f"✗ Failed: {name}")
                print(f"  Error: {str(e)}")
                if self.verbose:
                    traceback.print_exc()
                
                self.results.append({
                    "test_name": name,
                    "status": "failed",
                    "error": str(e),
                    "duration": 0
                })
    
    async def _run_parallel(self):
        """Run tests in parallel."""
        print("\nLaunching parallel test execution...")
        
        tasks = []
        for name, test_class in self.test_scenarios:
            task = self._run_test_async(name, test_class)
            tasks.append(task)
        
        # Execute all tests in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                name = self.test_scenarios[i][0]
                print(f"✗ Failed: {name}")
                print(f"  Error: {str(result)}")
                
                self.results.append({
                    "test_name": name,
                    "status": "failed",
                    "error": str(result),
                    "duration": 0
                })
            else:
                self.results.append(result)
    
    async def _run_test_async(self, name: str, test_class) -> Dict[str, Any]:
        """Run a single test asynchronously."""
        print(f"  Starting: {name}")
        
        try:
            test = test_class()
            result = await test.run_test()
            print(f"  ✓ Completed: {name} ({result['duration']:.2f}s)")
            return result
        except Exception as e:
            print(f"  ✗ Failed: {name} - {str(e)}")
            raise
    
    def _analyze_results(self) -> Dict[str, Any]:
        """Analyze test results comprehensively."""
        analysis = {
            "total_tests": len(self.test_scenarios),
            "successful_tests": 0,
            "failed_tests": 0,
            "total_requirements": 0,
            "completed_requirements": 0,
            "agents_used": set(),
            "total_files_created": 0,
            "common_issues": [],
            "performance_metrics": {},
            "quality_scores": {},
            "recommendations": []
        }
        
        # Aggregate data from all tests
        for result in self.results:
            if result.get("status") == "failed":
                analysis["failed_tests"] += 1
                continue
            
            analysis["successful_tests"] += 1
            
            # Requirements tracking
            if "requirements" in result:
                analysis["total_requirements"] += result["requirements"]["total"]
                analysis["completed_requirements"] += result["requirements"]["completed"]
            
            # Agents used
            if "agents_used" in result:
                analysis["agents_used"].update(result["agents_used"])
            
            # Files created
            if "files_created" in result:
                analysis["total_files_created"] += len(result["files_created"])
            
            # Issues found
            if "issues_found" in result:
                analysis["common_issues"].extend(result["issues_found"])
            
            # Performance metrics
            if "performance_metrics" in result:
                test_name = result["test_name"]
                analysis["performance_metrics"][test_name] = result["performance_metrics"]
            
            # Quality scores
            if "quality_metrics" in result:
                test_name = result["test_name"]
                scores = result["quality_metrics"]
                avg_score = sum(scores.values()) / len(scores) if scores else 0
                analysis["quality_scores"][test_name] = avg_score
            
            # Recommendations
            if "recommendations" in result:
                analysis["recommendations"].extend(result["recommendations"])
        
        # Calculate aggregates
        analysis["agents_used"] = list(analysis["agents_used"])
        analysis["overall_completion_rate"] = (
            (analysis["completed_requirements"] / analysis["total_requirements"] * 100)
            if analysis["total_requirements"] > 0 else 0
        )
        analysis["overall_quality_score"] = (
            sum(analysis["quality_scores"].values()) / len(analysis["quality_scores"])
            if analysis["quality_scores"] else 0
        )
        
        # Identify patterns in issues
        analysis["issue_patterns"] = self._identify_issue_patterns(analysis["common_issues"])
        
        return analysis
    
    def _identify_issue_patterns(self, issues: List[str]) -> Dict[str, int]:
        """Identify common patterns in issues."""
        patterns = {
            "memory": 0,
            "performance": 0,
            "compatibility": 0,
            "network": 0,
            "security": 0
        }
        
        for issue in issues:
            issue_lower = issue.lower()
            if "memory" in issue_lower or "leak" in issue_lower:
                patterns["memory"] += 1
            if "performance" in issue_lower or "slow" in issue_lower or "latency" in issue_lower:
                patterns["performance"] += 1
            if "compatibility" in issue_lower or "platform" in issue_lower:
                patterns["compatibility"] += 1
            if "network" in issue_lower or "connection" in issue_lower:
                patterns["network"] += 1
            if "security" in issue_lower or "vulnerability" in issue_lower:
                patterns["security"] += 1
        
        return {k: v for k, v in patterns.items() if v > 0}
    
    def _generate_report(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        duration = self.end_time - self.start_time
        
        report = {
            "phase": "Phase 4 - Comprehensive Mock Mode Testing",
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "execution_mode": "parallel" if self.parallel else "sequential",
            "summary": {
                "total_tests": analysis["total_tests"],
                "successful": analysis["successful_tests"],
                "failed": analysis["failed_tests"],
                "success_rate": (analysis["successful_tests"] / analysis["total_tests"] * 100)
                    if analysis["total_tests"] > 0 else 0
            },
            "requirements": {
                "total": analysis["total_requirements"],
                "completed": analysis["completed_requirements"],
                "completion_rate": analysis["overall_completion_rate"]
            },
            "agents": {
                "total_unique": len(analysis["agents_used"]),
                "list": analysis["agents_used"]
            },
            "quality": {
                "overall_score": analysis["overall_quality_score"],
                "by_test": analysis["quality_scores"]
            },
            "performance": analysis["performance_metrics"],
            "files_created": analysis["total_files_created"],
            "issues": {
                "total": len(analysis["common_issues"]),
                "patterns": analysis["issue_patterns"],
                "list": list(set(analysis["common_issues"]))  # Unique issues
            },
            "recommendations": list(set(analysis["recommendations"])),  # Unique recommendations
            "individual_results": self.results
        }
        
        return report
    
    def _save_results(self, report: Dict[str, Any]):
        """Save test results to files."""
        output_dir = Path("tests/e2e_phase4/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON report
        json_path = output_dir / f"phase4_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nResults saved to: {json_path}")
        
        # Generate HTML report
        html_path = output_dir / f"phase4_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        self._generate_html_report(report, html_path)
        
        print(f"HTML report saved to: {html_path}")
    
    def _generate_html_report(self, report: Dict[str, Any], output_path: Path):
        """Generate HTML report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Phase 4 Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .card {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ font-size: 24px; font-weight: bold; color: #3498db; }}
        .label {{ color: #7f8c8d; font-size: 14px; }}
        .success {{ color: #27ae60; }}
        .failed {{ color: #e74c3c; }}
        .warning {{ color: #f39c12; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #34495e; color: white; }}
        .progress-bar {{ background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ background: #3498db; height: 100%; transition: width 0.3s; }}
        .issue {{ background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; border-left: 4px solid #f39c12; }}
        .recommendation {{ background: #d4edda; padding: 10px; margin: 5px 0; border-radius: 3px; border-left: 4px solid #27ae60; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Phase 4 - Comprehensive Mock Mode Test Report</h1>
        <p>Generated: {report['timestamp']}</p>
        <p>Duration: {report['duration']:.2f} seconds | Mode: {report['execution_mode'].upper()}</p>
    </div>
    
    <div class="summary">
        <div class="card">
            <div class="label">Tests Run</div>
            <div class="metric">{report['summary']['total_tests']}</div>
            <div class="success">{report['summary']['successful']} Passed</div>
            <div class="failed">{report['summary']['failed']} Failed</div>
        </div>
        
        <div class="card">
            <div class="label">Success Rate</div>
            <div class="metric">{report['summary']['success_rate']:.1f}%</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {report['summary']['success_rate']}%"></div>
            </div>
        </div>
        
        <div class="card">
            <div class="label">Requirements</div>
            <div class="metric">{report['requirements']['completion_rate']:.1f}%</div>
            <div>{report['requirements']['completed']} / {report['requirements']['total']} Completed</div>
        </div>
        
        <div class="card">
            <div class="label">Quality Score</div>
            <div class="metric">{report['quality']['overall_score']:.1f}%</div>
            <div>{len(report['agents']['list'])} Agents Used</div>
        </div>
    </div>
    
    <h2>Test Results</h2>
    <table>
        <tr>
            <th>Test Scenario</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Completion</th>
            <th>Quality Score</th>
        </tr>"""
        
        for result in report['individual_results']:
            status_class = "success" if result.get('status') == 'completed' else "failed"
            completion = result.get('requirements', {}).get('completion_percentage', 0)
            test_name = result.get('test_name', 'Unknown')
            quality = report['quality']['by_test'].get(test_name, 0)
            
            html += f"""
        <tr>
            <td>{test_name}</td>
            <td class="{status_class}">{result.get('status', 'N/A')}</td>
            <td>{result.get('duration', 0):.2f}s</td>
            <td>{completion:.1f}%</td>
            <td>{quality:.1f}%</td>
        </tr>"""
        
        html += """
    </table>
    
    <h2>Issues Identified</h2>
    <div>"""
        
        for issue in report['issues']['list']:
            html += f'<div class="issue">{issue}</div>'
        
        html += """
    </div>
    
    <h2>Recommendations</h2>
    <div>"""
        
        for rec in report['recommendations']:
            html += f'<div class="recommendation">{rec}</div>'
        
        html += """
    </div>
    
    <h2>Agent Usage</h2>
    <p>Total Unique Agents: {}</p>
    <p>{}</p>
    
    <h2>Performance Metrics</h2>
    <pre>{}</pre>
</body>
</html>""".format(
            len(report['agents']['list']),
            ', '.join(report['agents']['list']),
            json.dumps(report['performance'], indent=2)
        )
        
        with open(output_path, "w") as f:
            f.write(html)
    
    def _print_summary(self, report: Dict[str, Any]):
        """Print test summary to console."""
        print("\n" + "="*80)
        print("TEST EXECUTION SUMMARY")
        print("="*80)
        
        print(f"\nExecution Time: {report['duration']:.2f} seconds")
        print(f"Tests Run: {report['summary']['total_tests']}")
        print(f"  ✓ Successful: {report['summary']['successful']}")
        print(f"  ✗ Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        
        print(f"\nRequirements:")
        print(f"  Total: {report['requirements']['total']}")
        print(f"  Completed: {report['requirements']['completed']}")
        print(f"  Completion Rate: {report['requirements']['completion_rate']:.1f}%")
        
        print(f"\nQuality:")
        print(f"  Overall Score: {report['quality']['overall_score']:.1f}%")
        
        if report['quality']['by_test']:
            print("  By Test:")
            for test, score in report['quality']['by_test'].items():
                print(f"    - {test}: {score:.1f}%")
        
        print(f"\nAgents Used: {len(report['agents']['list'])}")
        print(f"Files Created: {report['files_created']}")
        
        if report['issues']['patterns']:
            print(f"\nIssue Patterns:")
            for pattern, count in report['issues']['patterns'].items():
                print(f"  - {pattern.capitalize()}: {count} occurrences")
        
        if report['recommendations']:
            print(f"\nTop Recommendations:")
            for i, rec in enumerate(report['recommendations'][:5], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*80)
        print("Phase 4 Testing Complete!")
        print("="*80)


async def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Phase 4 Comprehensive Test Runner")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--test", type=str, help="Run specific test (1-5)")
    
    args = parser.parse_args()
    
    if args.test:
        # Run specific test
        test_map = {
            "1": TestOpenSourceLibrary,
            "2": TestRealtimeCollaboration,
            "3": TestDevOpsPipeline,
            "4": TestAIContentManagement,
            "5": TestGameDevelopment
        }
        
        if args.test in test_map:
            print(f"Running test {args.test}...")
            test = test_map[args.test]()
            result = await test.run_test()
            print(f"Test completed. Status: {result['status']}")
        else:
            print(f"Invalid test number: {args.test}. Use 1-5.")
    else:
        # Run all tests
        runner = Phase4TestRunner(parallel=args.parallel, verbose=args.verbose)
        await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())