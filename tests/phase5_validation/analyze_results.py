#!/usr/bin/env python3
"""
Phase 5 Test Results Analyzer
Analyzes test execution results and generates comprehensive reports
"""

import os
import sys
import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

RESULTS_DIR = Path(__file__).parent / "results"
REPORTS_DIR = Path(__file__).parent / "reports"

class ResultsAnalyzer:
    """Analyzes test results and generates reports"""
    
    def __init__(self, results_file: Optional[Path] = None):
        self.results_file = results_file or self._find_latest_results()
        self.results_data = None
        self.analysis = {}
        
        # Create reports directory
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _find_latest_results(self) -> Path:
        """Find the most recent results file"""
        result_files = list(RESULTS_DIR.glob("test_results_*.json"))
        if not result_files:
            raise FileNotFoundError("No test result files found")
        return max(result_files, key=lambda f: f.stat().st_mtime)
    
    def load_results(self):
        """Load test results from JSON file"""
        with open(self.results_file, 'r') as f:
            self.results_data = json.load(f)
        print(f"Loaded results from: {self.results_file}")
    
    def analyze(self):
        """Perform comprehensive analysis of test results"""
        if not self.results_data:
            self.load_results()
        
        results = self.results_data["results"]
        
        # Overall statistics
        self.analysis["overall"] = self._calculate_overall_stats(results)
        
        # Per-test analysis
        self.analysis["per_test"] = self._analyze_per_test(results)
        
        # Agent performance
        self.analysis["agent_performance"] = self._analyze_agent_performance(results)
        
        # Requirement coverage
        self.analysis["requirement_coverage"] = self._analyze_requirement_coverage(results)
        
        # Error patterns
        self.analysis["error_patterns"] = self._analyze_error_patterns(results)
        
        # Performance metrics
        self.analysis["performance"] = self._analyze_performance(results)
        
        # Phase validation
        self.analysis["phase_validation"] = self._validate_phases(results)
    
    def _calculate_overall_stats(self, results: Dict) -> Dict:
        """Calculate overall test statistics"""
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.get("success"))
        
        quality_scores = [r.get("quality_score", 0) for r in results.values()]
        execution_times = [r.get("execution_time", 0) for r in results.values()]
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": (successful_tests / max(1, total_tests)) * 100,
            "average_quality_score": statistics.mean(quality_scores) if quality_scores else 0,
            "min_quality_score": min(quality_scores) if quality_scores else 0,
            "max_quality_score": max(quality_scores) if quality_scores else 0,
            "total_execution_time": sum(execution_times),
            "average_execution_time": statistics.mean(execution_times) if execution_times else 0,
            "test_date": self.results_data.get("start_time", "Unknown")
        }
    
    def _analyze_per_test(self, results: Dict) -> List[Dict]:
        """Analyze each test individually"""
        test_analysis = []
        
        for test_key, result in results.items():
            metrics = result.get("metrics", {})
            
            analysis = {
                "test_key": test_key,
                "name": result.get("name", test_key),
                "success": result.get("success", False),
                "quality_score": result.get("quality_score", 0),
                "execution_time": result.get("execution_time", 0),
                "agents_executed": len(metrics.get("agents_executed", [])),
                "files_created": metrics.get("files_created", 0),
                "requirements_completed": metrics.get("requirements_completed", 0),
                "total_requirements": metrics.get("total_requirements", 0),
                "completion_rate": 0,
                "errors": metrics.get("errors", 0),
                "warnings": metrics.get("warnings", 0)
            }
            
            # Calculate completion rate
            if analysis["total_requirements"] > 0:
                analysis["completion_rate"] = (
                    analysis["requirements_completed"] / analysis["total_requirements"]
                ) * 100
            
            test_analysis.append(analysis)
        
        # Sort by quality score
        test_analysis.sort(key=lambda x: x["quality_score"], reverse=True)
        
        return test_analysis
    
    def _analyze_agent_performance(self, results: Dict) -> Dict:
        """Analyze agent utilization and performance"""
        agent_stats = {}
        
        for result in results.values():
            for agent in result.get("metrics", {}).get("agents_executed", []):
                if agent not in agent_stats:
                    agent_stats[agent] = {
                        "executions": 0,
                        "tests_used_in": [],
                        "total_time": 0
                    }
                
                agent_stats[agent]["executions"] += 1
                agent_stats[agent]["tests_used_in"].append(result.get("test_key", "unknown"))
        
        # Calculate agent efficiency
        agent_performance = []
        for agent, stats in agent_stats.items():
            agent_performance.append({
                "agent": agent,
                "executions": stats["executions"],
                "tests_count": len(set(stats["tests_used_in"])),
                "utilization_rate": (len(set(stats["tests_used_in"])) / len(results)) * 100
            })
        
        # Sort by executions
        agent_performance.sort(key=lambda x: x["executions"], reverse=True)
        
        return {
            "agent_utilization": agent_performance,
            "total_unique_agents": len(agent_stats),
            "most_used_agent": agent_performance[0]["agent"] if agent_performance else None,
            "least_used_agent": agent_performance[-1]["agent"] if agent_performance else None
        }
    
    def _analyze_requirement_coverage(self, results: Dict) -> Dict:
        """Analyze requirement completion across tests"""
        total_requirements = 0
        completed_requirements = 0
        
        coverage_by_test = {}
        
        for test_key, result in results.items():
            metrics = result.get("metrics", {})
            test_total = metrics.get("total_requirements", 0)
            test_completed = metrics.get("requirements_completed", 0)
            
            total_requirements += test_total
            completed_requirements += test_completed
            
            if test_total > 0:
                coverage_by_test[test_key] = (test_completed / test_total) * 100
        
        return {
            "total_requirements": total_requirements,
            "completed_requirements": completed_requirements,
            "overall_coverage": (completed_requirements / max(1, total_requirements)) * 100,
            "coverage_by_test": coverage_by_test,
            "average_coverage": statistics.mean(coverage_by_test.values()) if coverage_by_test else 0
        }
    
    def _analyze_error_patterns(self, results: Dict) -> Dict:
        """Identify error patterns across tests"""
        error_types = {}
        tests_with_errors = []
        
        for test_key, result in results.items():
            if not result.get("success"):
                tests_with_errors.append(test_key)
                error = result.get("error", "Unknown error")
                
                # Categorize error
                if "timeout" in error.lower():
                    error_type = "timeout"
                elif "file" in error.lower():
                    error_type = "file_operation"
                elif "agent" in error.lower():
                    error_type = "agent_failure"
                else:
                    error_type = "other"
                
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Count errors from metrics
            metrics = result.get("metrics", {})
            if metrics.get("errors", 0) > 0:
                error_types["execution_errors"] = error_types.get("execution_errors", 0) + metrics["errors"]
        
        return {
            "tests_with_errors": tests_with_errors,
            "error_count": len(tests_with_errors),
            "error_types": error_types,
            "error_rate": (len(tests_with_errors) / max(1, len(results))) * 100
        }
    
    def _analyze_performance(self, results: Dict) -> Dict:
        """Analyze performance metrics"""
        execution_times = []
        quality_scores = []
        file_counts = []
        
        for result in results.values():
            if result.get("success"):
                execution_times.append(result.get("execution_time", 0))
                quality_scores.append(result.get("quality_score", 0))
                file_counts.append(result.get("metrics", {}).get("files_created", 0))
        
        performance = {}
        
        if execution_times:
            performance["execution_time"] = {
                "min": min(execution_times),
                "max": max(execution_times),
                "mean": statistics.mean(execution_times),
                "median": statistics.median(execution_times),
                "stdev": statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            }
        
        if quality_scores:
            performance["quality_scores"] = {
                "min": min(quality_scores),
                "max": max(quality_scores),
                "mean": statistics.mean(quality_scores),
                "median": statistics.median(quality_scores),
                "stdev": statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0
            }
        
        if file_counts:
            performance["file_generation"] = {
                "total_files": sum(file_counts),
                "average_per_test": statistics.mean(file_counts),
                "max_files": max(file_counts),
                "min_files": min(file_counts)
            }
        
        return performance
    
    def _validate_phases(self, results: Dict) -> Dict:
        """Validate that all phases are working correctly"""
        phase_checks = {
            "phase1_core_integration": False,
            "phase2_production_infrastructure": False,
            "phase3_quality_assurance": False,
            "phase4_advanced_features": False,
            "phase5_production_readiness": False
        }
        
        # Check for phase 1: Requirement tracking
        for result in results.values():
            metrics = result.get("metrics", {})
            if metrics.get("total_requirements", 0) > 0:
                phase_checks["phase1_core_integration"] = True
                break
        
        # Check for phase 2: Error recovery (low error rate indicates recovery)
        error_rate = self.analysis.get("error_patterns", {}).get("error_rate", 100)
        if error_rate < 20:  # Less than 20% error rate
            phase_checks["phase2_production_infrastructure"] = True
        
        # Check for phase 3: Quality scores
        avg_quality = self.analysis.get("overall", {}).get("average_quality_score", 0)
        if avg_quality > 70:
            phase_checks["phase3_quality_assurance"] = True
        
        # Check for phase 4: Agent orchestration (multiple agents per test)
        agent_counts = [len(r.get("metrics", {}).get("agents_executed", [])) for r in results.values()]
        if agent_counts and statistics.mean(agent_counts) > 5:
            phase_checks["phase4_advanced_features"] = True
        
        # Check for phase 5: Overall success rate
        success_rate = self.analysis.get("overall", {}).get("success_rate", 0)
        if success_rate > 80:
            phase_checks["phase5_production_readiness"] = True
        
        return {
            "phases_validated": phase_checks,
            "phases_passed": sum(phase_checks.values()),
            "total_phases": len(phase_checks),
            "validation_rate": (sum(phase_checks.values()) / len(phase_checks)) * 100
        }
    
    def generate_report(self, format: str = "all"):
        """Generate analysis report in specified format"""
        if not self.analysis:
            self.analyze()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format in ["markdown", "all"]:
            self._generate_markdown_report(timestamp)
        
        if format in ["json", "all"]:
            self._generate_json_report(timestamp)
        
        if format in ["html", "all"]:
            self._generate_html_report(timestamp)
    
    def _generate_markdown_report(self, timestamp: str):
        """Generate markdown report"""
        report_file = REPORTS_DIR / f"analysis_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Phase 5 Validation Test Results Analysis\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Results File**: {self.results_file.name}\n\n")
            
            # Overall Statistics
            f.write("## Overall Statistics\n\n")
            overall = self.analysis["overall"]
            f.write(f"- **Total Tests**: {overall['total_tests']}\n")
            f.write(f"- **Successful Tests**: {overall['successful_tests']}\n")
            f.write(f"- **Success Rate**: {overall['success_rate']:.1f}%\n")
            f.write(f"- **Average Quality Score**: {overall['average_quality_score']:.1f}%\n")
            f.write(f"- **Total Execution Time**: {overall['total_execution_time']:.2f}s\n\n")
            
            # Per-Test Results
            f.write("## Test Results\n\n")
            f.write("| Test | Success | Quality | Time (s) | Files | Requirements | Errors |\n")
            f.write("|------|---------|---------|----------|-------|--------------|--------|\n")
            
            for test in self.analysis["per_test"]:
                status = "[OK]" if test["success"] else "[FAIL]"
                f.write(f"| {test['name']} | {status} | {test['quality_score']:.1f}% | "
                       f"{test['execution_time']:.2f} | {test['files_created']} | "
                       f"{test['requirements_completed']}/{test['total_requirements']} | "
                       f"{test['errors']} |\n")
            
            # Agent Performance
            f.write("\n## Agent Performance\n\n")
            f.write("| Agent | Executions | Tests Used In | Utilization |\n")
            f.write("|-------|------------|---------------|-------------|\n")
            
            for agent in self.analysis["agent_performance"]["agent_utilization"][:10]:
                f.write(f"| {agent['agent']} | {agent['executions']} | "
                       f"{agent['tests_count']} | {agent['utilization_rate']:.1f}% |\n")
            
            # Phase Validation
            f.write("\n## Phase Validation\n\n")
            phases = self.analysis["phase_validation"]["phases_validated"]
            for phase, validated in phases.items():
                status = "[OK]" if validated else "[FAIL]"
                phase_name = phase.replace("_", " ").title()
                f.write(f"- {status} **{phase_name}**\n")
            
            f.write(f"\n**Phases Validated**: {self.analysis['phase_validation']['phases_passed']}/5 "
                   f"({self.analysis['phase_validation']['validation_rate']:.1f}%)\n")
            
            # Performance Metrics
            f.write("\n## Performance Metrics\n\n")
            if "execution_time" in self.analysis["performance"]:
                perf = self.analysis["performance"]["execution_time"]
                f.write(f"### Execution Time\n")
                f.write(f"- Min: {perf['min']:.2f}s\n")
                f.write(f"- Max: {perf['max']:.2f}s\n")
                f.write(f"- Mean: {perf['mean']:.2f}s\n")
                f.write(f"- Median: {perf['median']:.2f}s\n\n")
            
            if "quality_scores" in self.analysis["performance"]:
                qual = self.analysis["performance"]["quality_scores"]
                f.write(f"### Quality Scores\n")
                f.write(f"- Min: {qual['min']:.1f}%\n")
                f.write(f"- Max: {qual['max']:.1f}%\n")
                f.write(f"- Mean: {qual['mean']:.1f}%\n")
                f.write(f"- Median: {qual['median']:.1f}%\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            
            # Generate recommendations based on analysis
            if overall["success_rate"] < 80:
                f.write("- [!] **Success rate below 80%**: Review error patterns and fix failing tests\n")
            
            if overall["average_quality_score"] < 70:
                f.write("- [!] **Quality score below 70%**: Improve agent execution and requirement completion\n")
            
            error_rate = self.analysis["error_patterns"]["error_rate"]
            if error_rate > 10:
                f.write(f"- [!] **High error rate ({error_rate:.1f}%)**: Investigate error patterns\n")
            
            if self.analysis["phase_validation"]["phases_passed"] < 4:
                f.write("- [!] **Not all phases validated**: Review phase-specific features\n")
            
            if overall["success_rate"] >= 80 and overall["average_quality_score"] >= 80:
                f.write("- [OK] **System performing well**: All key metrics meet production standards\n")
        
        print(f"Markdown report saved to: {report_file}")
    
    def _generate_json_report(self, timestamp: str):
        """Generate JSON report"""
        report_file = REPORTS_DIR / f"analysis_report_{timestamp}.json"
        
        report_data = {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "results_file": str(self.results_file),
                "timestamp": timestamp
            },
            "analysis": self.analysis
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"JSON report saved to: {report_file}")
    
    def _generate_html_report(self, timestamp: str):
        """Generate HTML report with charts"""
        report_file = REPORTS_DIR / f"analysis_report_{timestamp}.html"
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Phase 5 Test Results Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #4CAF50; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .success {{ color: #4CAF50; font-weight: bold; }}
        .fail {{ color: #f44336; font-weight: bold; }}
        .phase-check {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 5px; }}
        .phase-check.valid {{ border-left: 4px solid #4CAF50; }}
        .phase-check.invalid {{ border-left: 4px solid #f44336; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Phase 5 Validation Test Results Analysis</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Overall Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{self.analysis['overall']['total_tests']}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.analysis['overall']['success_rate']:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.analysis['overall']['average_quality_score']:.1f}%</div>
                <div class="stat-label">Avg Quality Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.analysis['overall']['total_execution_time']:.1f}s</div>
                <div class="stat-label">Total Execution Time</div>
            </div>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <tr>
                <th>Test</th>
                <th>Status</th>
                <th>Quality Score</th>
                <th>Time (s)</th>
                <th>Files</th>
                <th>Requirements</th>
            </tr>"""
        
        for test in self.analysis["per_test"]:
            status_class = "success" if test["success"] else "fail"
            status_text = "[OK] Pass" if test["success"] else "[FAIL] Fail"
            html_content += f"""
            <tr>
                <td>{test['name']}</td>
                <td class="{status_class}">{status_text}</td>
                <td>{test['quality_score']:.1f}%</td>
                <td>{test['execution_time']:.2f}</td>
                <td>{test['files_created']}</td>
                <td>{test['requirements_completed']}/{test['total_requirements']}</td>
            </tr>"""
        
        html_content += """
        </table>
        
        <h2>Phase Validation</h2>"""
        
        for phase, validated in self.analysis["phase_validation"]["phases_validated"].items():
            phase_name = phase.replace("_", " ").title()
            valid_class = "valid" if validated else "invalid"
            status = "✓" if validated else "✗"
            html_content += f"""
        <div class="phase-check {valid_class}">
            {status} <strong>{phase_name}</strong>
        </div>"""
        
        html_content += f"""
        
        <h2>Agent Utilization</h2>
        <table>
            <tr>
                <th>Agent</th>
                <th>Executions</th>
                <th>Tests Used In</th>
                <th>Utilization Rate</th>
            </tr>"""
        
        for agent in self.analysis["agent_performance"]["agent_utilization"][:10]:
            html_content += f"""
            <tr>
                <td>{agent['agent']}</td>
                <td>{agent['executions']}</td>
                <td>{agent['tests_count']}</td>
                <td>{agent['utilization_rate']:.1f}%</td>
            </tr>"""
        
        html_content += """
        </table>
    </div>
</body>
</html>"""
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        print(f"HTML report saved to: {report_file}")
    
    def print_summary(self):
        """Print a summary of the analysis to console"""
        if not self.analysis:
            self.analyze()
        
        print("\n" + "="*60)
        print("PHASE 5 VALIDATION TEST RESULTS SUMMARY")
        print("="*60)
        
        overall = self.analysis["overall"]
        print(f"\nOverall Performance:")
        print(f"  Success Rate: {overall['success_rate']:.1f}%")
        print(f"  Average Quality: {overall['average_quality_score']:.1f}%")
        print(f"  Total Time: {overall['total_execution_time']:.2f}s")
        
        print(f"\nTop Performing Tests:")
        for test in self.analysis["per_test"][:3]:
            print(f"  - {test['name']}: {test['quality_score']:.1f}% quality")
        
        print(f"\nPhase Validation: {self.analysis['phase_validation']['phases_passed']}/5 phases validated")
        
        print(f"\nMost Used Agents:")
        for agent in self.analysis["agent_performance"]["agent_utilization"][:3]:
            print(f"  - {agent['agent']}: {agent['executions']} executions")
        
        if self.analysis["error_patterns"]["error_rate"] > 10:
            print(f"\n[!] Warning: High error rate ({self.analysis['error_patterns']['error_rate']:.1f}%)")
        
        print("\n" + "="*60)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Analyze Phase 5 test results")
    parser.add_argument("--file", type=Path, help="Specific results file to analyze")
    parser.add_argument("--format", choices=["json", "markdown", "html", "all"], 
                       default="all", help="Report format")
    parser.add_argument("--summary", action="store_true", help="Print summary to console")
    
    args = parser.parse_args()
    
    try:
        analyzer = ResultsAnalyzer(args.file)
        analyzer.analyze()
        
        if args.summary:
            analyzer.print_summary()
        
        analyzer.generate_report(args.format)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run tests first using: python run_tests.py --all")
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing results: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()