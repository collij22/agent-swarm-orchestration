#!/usr/bin/env python3
"""
Quality Enforcer - Automated quality validation and enforcement system
Ensures all quality standards are met before deployment
"""

import os
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import ast
import re

# Import existing components
from .requirement_tracker import RequirementTracker
from .agent_validator import AgentValidator
from .production_monitor import ProductionMonitor


@dataclass
class QualityMetrics:
    """Quality metrics for the system"""
    requirement_coverage: float = 0.0
    agent_success_rate: float = 0.0
    test_coverage: float = 0.0
    code_complexity: float = 0.0
    security_score: float = 100.0
    performance_score: float = 0.0
    documentation_coverage: float = 0.0
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    passed: bool = False


@dataclass
class QualityGate:
    """Represents a quality gate with threshold"""
    name: str
    metric: str
    threshold: float
    operator: str  # ">=", "<=", ">", "<", "=="
    severity: str  # "critical", "warning", "info"
    message: str


class QualityEnforcer:
    """
    Enforces quality standards across the entire system
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.requirement_tracker = RequirementTracker()
        self.agent_validator = AgentValidator()
        self.monitor = ProductionMonitor()
        
        # Quality gates configuration
        self.quality_gates = [
            QualityGate(
                name="requirement_coverage",
                metric="requirement_coverage",
                threshold=80.0,
                operator=">=",
                severity="critical",
                message="Requirement coverage must be at least 80%"
            ),
            QualityGate(
                name="agent_success",
                metric="agent_success_rate",
                threshold=90.0,
                operator=">=",
                severity="critical",
                message="Agent success rate must be at least 90%"
            ),
            QualityGate(
                name="test_coverage",
                metric="test_coverage",
                threshold=85.0,
                operator=">=",
                severity="critical",
                message="Test coverage must be at least 85%"
            ),
            QualityGate(
                name="code_complexity",
                metric="code_complexity",
                threshold=10.0,
                operator="<=",
                severity="warning",
                message="Code complexity should not exceed 10"
            ),
            QualityGate(
                name="security_score",
                metric="security_score",
                threshold=80.0,
                operator=">=",
                severity="critical",
                message="Security score must be at least 80"
            ),
            QualityGate(
                name="performance_score",
                metric="performance_score",
                threshold=70.0,
                operator=">=",
                severity="warning",
                message="Performance score should be at least 70"
            )
        ]
        
        self.metrics = QualityMetrics()
    
    def enforce_quality(self, 
                        requirements_file: Optional[str] = None,
                        run_tests: bool = True,
                        check_security: bool = True) -> QualityMetrics:
        """
        Main method to enforce all quality standards
        """
        print("Starting Quality Enforcement...")
        print("=" * 60)
        
        # Step 1: Check requirement coverage
        self._check_requirement_coverage(requirements_file)
        
        # Step 2: Validate agent outputs
        self._validate_agent_outputs()
        
        # Step 3: Check for placeholder files
        self._check_for_placeholders()
        
        # Step 4: Run tests and check coverage
        if run_tests:
            self._run_tests_and_coverage()
        
        # Step 5: Analyze code complexity
        self._analyze_code_complexity()
        
        # Step 6: Security analysis
        if check_security:
            self._run_security_analysis()
        
        # Step 7: Performance validation
        self._validate_performance()
        
        # Step 8: Documentation check
        self._check_documentation()
        
        # Step 9: Apply quality gates
        self._apply_quality_gates()
        
        # Step 10: Generate report
        self._generate_quality_report()
        
        return self.metrics
    
    def _check_requirement_coverage(self, requirements_file: Optional[str] = None):
        """Check requirement coverage"""
        print("\n1. Checking Requirement Coverage...")
        
        if requirements_file and Path(requirements_file).exists():
            self.requirement_tracker.load_requirements_from_file(requirements_file)
        
        coverage = self.requirement_tracker.get_coverage_report()
        self.metrics.requirement_coverage = coverage.get("overall_completion", 0)
        
        print(f"   Requirement coverage: {self.metrics.requirement_coverage:.1f}%")
        
        # Check for uncovered requirements
        for req_id, req_data in self.requirement_tracker.requirements.items():
            if req_data["completion_percentage"] < 50:
                self.metrics.warnings.append(
                    f"Low coverage for {req_id}: {req_data['completion_percentage']}%"
                )
    
    def _validate_agent_outputs(self):
        """Validate all agent outputs"""
        print("\n2. Validating Agent Outputs...")
        
        agents_to_validate = [
            "project-architect",
            "rapid-builder",
            "frontend-specialist",
            "quality-guardian",
            "devops-engineer"
        ]
        
        successful = 0
        total = len(agents_to_validate)
        
        for agent in agents_to_validate:
            # Check if agent has output
            agent_path = self.project_path / "outputs" / agent
            if agent_path.exists():
                result = self.agent_validator.validate_agent_output(
                    agent,
                    {"files": list(agent_path.glob("**/*"))},
                    str(self.project_path)
                )
                
                if result["is_valid"]:
                    successful += 1
                else:
                    self.metrics.warnings.extend(result["issues"])
        
        self.metrics.agent_success_rate = (successful / total * 100) if total > 0 else 0
        print(f"   Agent success rate: {self.metrics.agent_success_rate:.1f}%")
    
    def _check_for_placeholders(self):
        """Check for placeholder files"""
        print("\n3. Checking for Placeholder Files...")
        
        placeholder_patterns = [
            "TODO",
            "PLACEHOLDER",
            "IMPLEMENT",
            "FIXME",
            "pass  # TODO"
        ]
        
        placeholder_files = []
        
        # Check Python files
        for py_file in self.project_path.glob("**/*.py"):
            if "test" in py_file.name or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Check for placeholder patterns
                for pattern in placeholder_patterns:
                    if pattern in content:
                        # Check if it's a significant placeholder (not just a comment)
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if pattern in line:
                                # Check if it's the only content in a function
                                if "def " in lines[max(0, i-5):i]:
                                    if len([l for l in lines[i:i+5] if l.strip() and not l.strip().startswith('#')]) <= 1:
                                        placeholder_files.append(str(py_file))
                                        break
                                        
            except Exception as e:
                self.metrics.warnings.append(f"Could not check {py_file}: {e}")
        
        if placeholder_files:
            self.metrics.critical_issues.append(
                f"Found {len(placeholder_files)} placeholder files"
            )
            for file in placeholder_files[:5]:  # Show first 5
                self.metrics.warnings.append(f"Placeholder in: {file}")
        
        print(f"   Placeholder files found: {len(placeholder_files)}")
    
    def _run_tests_and_coverage(self):
        """Run tests and check coverage"""
        print("\n4. Running Tests and Coverage...")
        
        try:
            # Run pytest with coverage
            result = subprocess.run(
                ["pytest", "--cov=lib", "--cov=sfa", "--cov-report=json", "--quiet"],
                capture_output=True,
                text=True,
                cwd=self.project_path
            )
            
            # Parse coverage report
            coverage_file = self.project_path / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    self.metrics.test_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
            
            print(f"   Test coverage: {self.metrics.test_coverage:.1f}%")
            
        except Exception as e:
            self.metrics.warnings.append(f"Could not run tests: {e}")
            print(f"   Warning: Could not run tests: {e}")
    
    def _analyze_code_complexity(self):
        """Analyze code complexity"""
        print("\n5. Analyzing Code Complexity...")
        
        complexity_scores = []
        
        for py_file in self.project_path.glob("**/*.py"):
            if "test" in py_file.name or "__pycache__" in str(py_file):
                continue
            
            try:
                complexity = self._calculate_complexity(py_file)
                complexity_scores.append(complexity)
                
                if complexity > 10:
                    self.metrics.warnings.append(
                        f"High complexity in {py_file.name}: {complexity}"
                    )
                    
            except Exception as e:
                continue
        
        if complexity_scores:
            self.metrics.code_complexity = sum(complexity_scores) / len(complexity_scores)
        
        print(f"   Average complexity: {self.metrics.code_complexity:.1f}")
    
    def _calculate_complexity(self, file_path: Path) -> int:
        """Calculate cyclomatic complexity of a Python file"""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            
            complexity = 1  # Base complexity
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.With):
                    complexity += 1
                elif isinstance(node, ast.Assert):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            return complexity
            
        except Exception:
            return 0
    
    def _run_security_analysis(self):
        """Run security analysis"""
        print("\n6. Running Security Analysis...")
        
        security_issues = []
        
        # Check for common security issues
        patterns = {
            r"eval\(": "Use of eval() is dangerous",
            r"exec\(": "Use of exec() is dangerous",
            r"pickle\.loads": "Pickle deserialization can be unsafe",
            r"os\.system\(": "Use subprocess instead of os.system",
            r"shell=True": "Shell injection risk with shell=True",
            r"verify=False": "SSL verification disabled",
            r"password\s*=\s*['\"]": "Hardcoded password detected",
            r"api_key\s*=\s*['\"]": "Hardcoded API key detected"
        }
        
        for py_file in self.project_path.glob("**/*.py"):
            if "test" in py_file.name:
                continue
                
            try:
                content = py_file.read_text()
                
                for pattern, message in patterns.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        security_issues.append(f"{py_file.name}: {message}")
                        
            except Exception:
                continue
        
        # Calculate security score
        if security_issues:
            self.metrics.security_score = max(0, 100 - len(security_issues) * 10)
            for issue in security_issues[:5]:  # Show first 5
                self.metrics.warnings.append(f"Security: {issue}")
        
        print(f"   Security score: {self.metrics.security_score:.0f}/100")
    
    def _validate_performance(self):
        """Validate performance metrics"""
        print("\n7. Validating Performance...")
        
        # Check system health from production monitor
        health = self.monitor.get_system_health()
        
        # Calculate performance score based on various metrics
        performance_factors = []
        
        # Response time factor
        if health.get("average_duration"):
            if health["average_duration"] < 1.0:
                performance_factors.append(100)
            elif health["average_duration"] < 5.0:
                performance_factors.append(80)
            else:
                performance_factors.append(60)
        
        # Success rate factor
        if health.get("success_rate"):
            performance_factors.append(health["success_rate"] * 100)
        
        # Error rate factor
        if health.get("error_rate"):
            performance_factors.append(100 - health["error_rate"] * 100)
        
        if performance_factors:
            self.metrics.performance_score = sum(performance_factors) / len(performance_factors)
        else:
            self.metrics.performance_score = 75  # Default if no metrics
        
        print(f"   Performance score: {self.metrics.performance_score:.0f}/100")
    
    def _check_documentation(self):
        """Check documentation coverage"""
        print("\n8. Checking Documentation...")
        
        doc_files = list(self.project_path.glob("**/*.md"))
        py_files = list(self.project_path.glob("**/*.py"))
        
        # Check for docstrings in Python files
        documented_functions = 0
        total_functions = 0
        
        for py_file in py_files:
            if "test" in py_file.name or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1
                            
            except Exception:
                continue
        
        if total_functions > 0:
            self.metrics.documentation_coverage = (documented_functions / total_functions * 100)
        
        # Check for README and other docs
        if not (self.project_path / "README.md").exists():
            self.metrics.warnings.append("Missing README.md")
        
        print(f"   Documentation coverage: {self.metrics.documentation_coverage:.1f}%")
        print(f"   Documentation files: {len(doc_files)}")
    
    def _apply_quality_gates(self):
        """Apply quality gates to determine pass/fail"""
        print("\n9. Applying Quality Gates...")
        
        critical_failures = []
        warnings = []
        
        for gate in self.quality_gates:
            # Get metric value
            metric_value = getattr(self.metrics, gate.metric, 0)
            
            # Check threshold
            passed = self._check_threshold(metric_value, gate.threshold, gate.operator)
            
            if not passed:
                message = f"{gate.message} (actual: {metric_value:.1f})"
                
                if gate.severity == "critical":
                    critical_failures.append(message)
                    self.metrics.critical_issues.append(message)
                else:
                    warnings.append(message)
                    self.metrics.warnings.append(message)
                
                print(f"   ❌ {gate.name}: FAILED - {message}")
            else:
                print(f"   ✅ {gate.name}: PASSED")
        
        # Determine overall pass/fail
        self.metrics.passed = len(critical_failures) == 0
        
        if not self.metrics.passed:
            print(f"\n❌ Quality Gates FAILED - {len(critical_failures)} critical issues")
        else:
            print(f"\n✅ Quality Gates PASSED with {len(warnings)} warnings")
    
    def _check_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Check if value meets threshold with given operator"""
        if operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == "==":
            return abs(value - threshold) < 0.01
        return False
    
    def _generate_quality_report(self):
        """Generate quality enforcement report"""
        print("\n" + "=" * 60)
        print("QUALITY ENFORCEMENT REPORT")
        print("=" * 60)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "passed": self.metrics.passed,
            "metrics": {
                "requirement_coverage": f"{self.metrics.requirement_coverage:.1f}%",
                "agent_success_rate": f"{self.metrics.agent_success_rate:.1f}%",
                "test_coverage": f"{self.metrics.test_coverage:.1f}%",
                "code_complexity": f"{self.metrics.code_complexity:.1f}",
                "security_score": f"{self.metrics.security_score:.0f}/100",
                "performance_score": f"{self.metrics.performance_score:.0f}/100",
                "documentation_coverage": f"{self.metrics.documentation_coverage:.1f}%"
            },
            "critical_issues": self.metrics.critical_issues,
            "warnings": self.metrics.warnings[:10]  # First 10 warnings
        }
        
        # Save report
        report_file = self.project_path / "quality-report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: {report_file}")
        
        # Print summary
        print("\nSUMMARY:")
        for key, value in report["metrics"].items():
            print(f"  {key}: {value}")
        
        if self.metrics.critical_issues:
            print(f"\nCritical Issues: {len(self.metrics.critical_issues)}")
            for issue in self.metrics.critical_issues[:3]:
                print(f"  - {issue}")
        
        if self.metrics.warnings:
            print(f"\nWarnings: {len(self.metrics.warnings)}")
            for warning in self.metrics.warnings[:3]:
                print(f"  - {warning}")
        
        return report
    
    def validate_critical_paths(self) -> bool:
        """Validate all critical paths are tested"""
        print("\n10. Validating Critical Paths...")
        
        critical_paths = [
            "agent_execution",
            "requirement_tracking",
            "error_recovery",
            "monitoring",
            "validation"
        ]
        
        tested_paths = []
        
        # Check for test files
        for path in critical_paths:
            test_file = self.project_path / "tests" / f"test_{path}.py"
            if test_file.exists() or (self.project_path / "tests" / "e2e" / f"test_{path}.py").exists():
                tested_paths.append(path)
            else:
                self.metrics.warnings.append(f"Missing tests for critical path: {path}")
        
        coverage = len(tested_paths) / len(critical_paths) * 100
        print(f"   Critical path coverage: {coverage:.0f}%")
        
        return coverage >= 80


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enforce quality standards")
    parser.add_argument("--project-path", default=".", help="Project path")
    parser.add_argument("--requirements", help="Requirements file")
    parser.add_argument("--no-tests", action="store_true", help="Skip test execution")
    parser.add_argument("--no-security", action="store_true", help="Skip security analysis")
    parser.add_argument("--strict", action="store_true", help="Fail on any warning")
    
    args = parser.parse_args()
    
    enforcer = QualityEnforcer(args.project_path)
    
    metrics = enforcer.enforce_quality(
        requirements_file=args.requirements,
        run_tests=not args.no_tests,
        check_security=not args.no_security
    )
    
    # Validate critical paths
    enforcer.validate_critical_paths()
    
    # Exit with appropriate code
    if not metrics.passed:
        print("\n❌ QUALITY ENFORCEMENT FAILED")
        exit(1)
    elif args.strict and metrics.warnings:
        print("\n⚠️ QUALITY ENFORCEMENT FAILED (strict mode)")
        exit(1)
    else:
        print("\n✅ QUALITY ENFORCEMENT PASSED")
        exit(0)


if __name__ == "__main__":
    main()