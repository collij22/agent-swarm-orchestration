#!/usr/bin/env python3
"""
Quality Metrics Collector for E2E Testing

Features:
- Requirement coverage tracking (0-100%)
- Code quality scoring
- Security compliance validation
- Performance benchmark recording
- Comprehensive metrics aggregation
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import statistics
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.agent_runtime import AgentContext

class MetricType(Enum):
    """Types of metrics collected"""
    REQUIREMENT_COVERAGE = "requirement_coverage"
    CODE_QUALITY = "code_quality"
    SECURITY_COMPLIANCE = "security_compliance"
    PERFORMANCE = "performance"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION = "documentation"
    MAINTAINABILITY = "maintainability"

class QualityDimension(Enum):
    """Dimensions of quality measurement"""
    CORRECTNESS = "correctness"      # Does it work correctly?
    COMPLETENESS = "completeness"    # Is it complete?
    CONSISTENCY = "consistency"      # Is it consistent?
    EFFICIENCY = "efficiency"        # Is it efficient?
    RELIABILITY = "reliability"      # Is it reliable?
    SECURITY = "security"           # Is it secure?
    USABILITY = "usability"         # Is it usable?
    MAINTAINABILITY = "maintainability"  # Is it maintainable?

@dataclass
class RequirementMetric:
    """Metrics for a single requirement"""
    requirement_id: str
    description: str
    priority: str
    agents_assigned: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    tests_created: List[str] = field(default_factory=list)
    acceptance_criteria: Dict[str, bool] = field(default_factory=dict)
    completion_percentage: float = 0.0
    quality_score: float = 0.0
    verification_status: str = "pending"
    implementation_time_seconds: float = 0.0
    
    def calculate_completion(self) -> float:
        """Calculate requirement completion percentage"""
        if not self.acceptance_criteria:
            return 0.0
            
        met_criteria = sum(1 for met in self.acceptance_criteria.values() if met)
        total_criteria = len(self.acceptance_criteria)
        
        self.completion_percentage = (met_criteria / total_criteria * 100) if total_criteria > 0 else 0
        return self.completion_percentage

@dataclass
class CodeQualityMetric:
    """Code quality metrics for generated code"""
    file_path: str
    language: str
    lines_of_code: int = 0
    cyclomatic_complexity: int = 0
    duplication_percentage: float = 0.0
    comment_ratio: float = 0.0
    test_coverage: float = 0.0
    security_issues: List[str] = field(default_factory=list)
    code_smells: List[str] = field(default_factory=list)
    best_practices_violations: List[str] = field(default_factory=list)
    
    @property
    def quality_score(self) -> float:
        """Calculate overall quality score"""
        scores = []
        
        # Complexity score (lower is better)
        if self.cyclomatic_complexity <= 10:
            scores.append(100)
        elif self.cyclomatic_complexity <= 20:
            scores.append(75)
        elif self.cyclomatic_complexity <= 30:
            scores.append(50)
        else:
            scores.append(25)
            
        # Duplication score (lower is better)
        scores.append(max(0, 100 - self.duplication_percentage * 2))
        
        # Comment ratio score
        if self.comment_ratio >= 0.2:
            scores.append(100)
        elif self.comment_ratio >= 0.1:
            scores.append(75)
        else:
            scores.append(50)
            
        # Test coverage score
        scores.append(self.test_coverage)
        
        # Security score
        security_penalty = len(self.security_issues) * 10
        scores.append(max(0, 100 - security_penalty))
        
        # Code smell score
        smell_penalty = len(self.code_smells) * 5
        scores.append(max(0, 100 - smell_penalty))
        
        return statistics.mean(scores) if scores else 0

@dataclass
class SecurityMetric:
    """Security compliance metrics"""
    scan_timestamp: datetime
    vulnerabilities: Dict[str, List[str]] = field(default_factory=dict)  # severity -> list of issues
    compliance_checks: Dict[str, bool] = field(default_factory=dict)
    security_headers: Dict[str, bool] = field(default_factory=dict)
    authentication_implemented: bool = False
    authorization_implemented: bool = False
    encryption_enabled: bool = False
    input_validation: bool = False
    sql_injection_protected: bool = False
    xss_protected: bool = False
    csrf_protected: bool = False
    
    @property
    def compliance_score(self) -> float:
        """Calculate security compliance score"""
        checks_passed = sum(1 for passed in self.compliance_checks.values() if passed)
        total_checks = len(self.compliance_checks)
        
        if total_checks == 0:
            return 0
            
        base_score = (checks_passed / total_checks) * 100
        
        # Apply penalties for vulnerabilities
        critical_vulns = len(self.vulnerabilities.get("critical", []))
        high_vulns = len(self.vulnerabilities.get("high", []))
        medium_vulns = len(self.vulnerabilities.get("medium", []))
        
        penalty = (critical_vulns * 20) + (high_vulns * 10) + (medium_vulns * 5)
        
        return max(0, base_score - penalty)

@dataclass
class PerformanceMetric:
    """Performance benchmark metrics"""
    operation: str
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput: float  # operations per second
    latency_p50: float
    latency_p95: float
    latency_p99: float
    error_rate: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def meets_sla(self, sla_requirements: Dict[str, float]) -> bool:
        """Check if performance meets SLA requirements"""
        if "max_latency_p95" in sla_requirements:
            if self.latency_p95 > sla_requirements["max_latency_p95"]:
                return False
                
        if "min_throughput" in sla_requirements:
            if self.throughput < sla_requirements["min_throughput"]:
                return False
                
        if "max_error_rate" in sla_requirements:
            if self.error_rate > sla_requirements["max_error_rate"]:
                return False
                
        return True

class QualityMetricsCollector:
    """Collects and analyzes quality metrics for E2E testing"""
    
    def __init__(self, project_name: str):
        """Initialize the metrics collector
        
        Args:
            project_name: Name of the project being tested
        """
        self.project_name = project_name
        self.start_time = datetime.now()
        
        # Metric collections
        self.requirement_metrics: Dict[str, RequirementMetric] = {}
        self.code_quality_metrics: Dict[str, CodeQualityMetric] = {}
        self.security_metrics: List[SecurityMetric] = []
        self.performance_metrics: List[PerformanceMetric] = []
        
        # Aggregated metrics
        self.aggregate_metrics = {
            "total_requirements": 0,
            "requirements_completed": 0,
            "average_completion": 0.0,
            "total_files_created": 0,
            "total_tests_created": 0,
            "average_code_quality": 0.0,
            "security_compliance": 0.0,
            "performance_score": 0.0,
            "overall_quality_score": 0.0,
            "quality_dimensions": {}
        }
        
        # Quality thresholds
        self.thresholds = {
            "min_requirement_coverage": 80.0,
            "min_code_quality": 70.0,
            "min_security_compliance": 85.0,
            "min_test_coverage": 60.0,
            "max_complexity": 20,
            "max_duplication": 10.0
        }
        
    def track_requirement(self, metric: RequirementMetric):
        """Track a requirement metric"""
        self.requirement_metrics[metric.requirement_id] = metric
        self.aggregate_metrics["total_requirements"] += 1
        
        # Update completion
        completion = metric.calculate_completion()
        if completion >= 80:  # 80% threshold for completion
            self.aggregate_metrics["requirements_completed"] += 1
            
    def track_code_quality(self, file_path: str, context: Optional[AgentContext] = None):
        """Track code quality metrics for a file"""
        if not Path(file_path).exists():
            return
            
        metric = self._analyze_code_file(file_path)
        self.code_quality_metrics[file_path] = metric
        
        # Update aggregate
        self.aggregate_metrics["total_files_created"] += 1
        
    def track_security(self, security_metric: SecurityMetric):
        """Track security compliance metrics"""
        self.security_metrics.append(security_metric)
        
    def track_performance(self, performance_metric: PerformanceMetric):
        """Track performance benchmark"""
        self.performance_metrics.append(performance_metric)
        
    def _analyze_code_file(self, file_path: str) -> CodeQualityMetric:
        """Analyze code file for quality metrics"""
        path = Path(file_path)
        content = path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
        
        # Determine language
        language = self._detect_language(file_path)
        
        metric = CodeQualityMetric(
            file_path=file_path,
            language=language,
            lines_of_code=len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        )
        
        # Calculate cyclomatic complexity (simplified)
        metric.cyclomatic_complexity = self._calculate_complexity(content, language)
        
        # Calculate duplication (simplified)
        metric.duplication_percentage = self._calculate_duplication(lines)
        
        # Calculate comment ratio
        comment_lines = len([l for l in lines if l.strip().startswith('#') or l.strip().startswith('//')])
        metric.comment_ratio = comment_lines / len(lines) if lines else 0
        
        # Check for security issues
        metric.security_issues = self._scan_security_issues(content, language)
        
        # Check for code smells
        metric.code_smells = self._detect_code_smells(content, language)
        
        # Check best practices
        metric.best_practices_violations = self._check_best_practices(content, language)
        
        return metric
        
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin'
        }
        return language_map.get(ext, 'unknown')
        
    def _calculate_complexity(self, content: str, language: str) -> int:
        """Calculate cyclomatic complexity (simplified)"""
        complexity = 1  # Base complexity
        
        # Count decision points
        if language in ['python', 'javascript', 'typescript']:
            complexity += content.count('if ')
            complexity += content.count('elif ')
            complexity += content.count('else if ')
            complexity += content.count('for ')
            complexity += content.count('while ')
            complexity += content.count('except ')
            complexity += content.count('catch ')
            complexity += content.count('case ')
            
        return complexity
        
    def _calculate_duplication(self, lines: List[str]) -> float:
        """Calculate code duplication percentage (simplified)"""
        if len(lines) < 10:
            return 0.0
            
        # Check for duplicate lines (simplified)
        unique_lines = set(l.strip() for l in lines if l.strip())
        total_lines = len([l for l in lines if l.strip()])
        
        if total_lines == 0:
            return 0.0
            
        duplication = (1 - len(unique_lines) / total_lines) * 100
        return min(duplication, 100.0)
        
    def _scan_security_issues(self, content: str, language: str) -> List[str]:
        """Scan for common security issues"""
        issues = []
        
        # Common security patterns to check
        security_patterns = {
            'hardcoded_secrets': r'(api_key|password|secret|token)\s*=\s*["\'][^"\']+["\']',
            'sql_injection': r'(execute|query)\([^?]+\+|f".*SELECT.*{',
            'command_injection': r'os\.(system|exec|popen)\(',
            'path_traversal': r'\.\./|\.\.\\',
            'unsafe_eval': r'eval\(|exec\(',
            'weak_random': r'random\.(random|randint)\(',
            'no_input_validation': r'request\.(args|form|json)\[.+\](?!\s*\.strip)',
            'missing_auth': r'@app\.route.*(?!.*@requires_auth)',
            'insecure_deserialization': r'pickle\.loads?\(|yaml\.load\('
        }
        
        for issue_type, pattern in security_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(issue_type)
                
        return issues
        
    def _detect_code_smells(self, content: str, language: str) -> List[str]:
        """Detect common code smells"""
        smells = []
        lines = content.split('\n')
        
        # Long method (>50 lines)
        method_lines = 0
        in_method = False
        for line in lines:
            if language == 'python' and line.strip().startswith('def '):
                if in_method and method_lines > 50:
                    smells.append('long_method')
                in_method = True
                method_lines = 0
            elif in_method:
                method_lines += 1
                
        # Large class (>300 lines)
        if len(lines) > 300:
            smells.append('large_class')
            
        # Too many parameters (>5)
        if re.search(r'def \w+\([^)]{50,}\)', content):
            smells.append('too_many_parameters')
            
        # Deep nesting (>4 levels)
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent // 4)
        if max_indent > 4:
            smells.append('deep_nesting')
            
        # Duplicate code blocks
        if self._calculate_duplication(lines) > 20:
            smells.append('duplicate_code')
            
        # God class (too many responsibilities)
        if content.count('def ') > 20:
            smells.append('god_class')
            
        # Dead code (commented out code)
        if re.search(r'#\s*(def |class |if |for |while )', content):
            smells.append('dead_code')
            
        return smells
        
    def _check_best_practices(self, content: str, language: str) -> List[str]:
        """Check for best practice violations"""
        violations = []
        
        if language == 'python':
            # PEP 8 violations (simplified)
            if re.search(r'class [a-z]', content):
                violations.append('class_naming_convention')
            if re.search(r'def [A-Z]', content):
                violations.append('function_naming_convention')
            if re.search(r'^from .* import \*', content, re.MULTILINE):
                violations.append('wildcard_import')
            if not re.search(r'""".*"""', content, re.DOTALL):
                violations.append('missing_docstrings')
                
        elif language in ['javascript', 'typescript']:
            # JavaScript best practices
            if re.search(r'var ', content):
                violations.append('use_let_const_instead_of_var')
            if re.search(r'==(?!=)', content):
                violations.append('use_strict_equality')
            if re.search(r'console\.(log|error|warn)', content):
                violations.append('console_statements_in_production')
                
        # General best practices
        if not re.search(r'try.*except|try.*catch', content, re.DOTALL):
            violations.append('missing_error_handling')
            
        return violations
        
    def calculate_requirement_coverage(self) -> float:
        """Calculate overall requirement coverage"""
        if not self.requirement_metrics:
            return 0.0
            
        total_completion = sum(
            metric.completion_percentage 
            for metric in self.requirement_metrics.values()
        )
        
        coverage = total_completion / len(self.requirement_metrics)
        self.aggregate_metrics["average_completion"] = coverage
        
        return coverage
        
    def calculate_code_quality_score(self) -> float:
        """Calculate overall code quality score"""
        if not self.code_quality_metrics:
            return 0.0
            
        scores = [metric.quality_score for metric in self.code_quality_metrics.values()]
        
        quality_score = statistics.mean(scores) if scores else 0
        self.aggregate_metrics["average_code_quality"] = quality_score
        
        return quality_score
        
    def calculate_security_compliance(self) -> float:
        """Calculate overall security compliance score"""
        if not self.security_metrics:
            return 0.0
            
        scores = [metric.compliance_score for metric in self.security_metrics]
        
        compliance = statistics.mean(scores) if scores else 0
        self.aggregate_metrics["security_compliance"] = compliance
        
        return compliance
        
    def calculate_performance_score(self, sla_requirements: Dict[str, float]) -> float:
        """Calculate performance score against SLA"""
        if not self.performance_metrics:
            return 0.0
            
        meeting_sla = sum(
            1 for metric in self.performance_metrics
            if metric.meets_sla(sla_requirements)
        )
        
        score = (meeting_sla / len(self.performance_metrics)) * 100
        self.aggregate_metrics["performance_score"] = score
        
        return score
        
    def evaluate_quality_dimensions(self) -> Dict[str, float]:
        """Evaluate all quality dimensions"""
        dimensions = {}
        
        # Correctness - based on requirement completion
        dimensions[QualityDimension.CORRECTNESS.value] = self.calculate_requirement_coverage()
        
        # Completeness - based on files and tests created
        total_expected = self.aggregate_metrics["total_requirements"] * 3  # Assume 3 files per requirement
        total_created = self.aggregate_metrics["total_files_created"]
        dimensions[QualityDimension.COMPLETENESS.value] = min(100, (total_created / total_expected * 100) if total_expected > 0 else 0)
        
        # Consistency - based on code quality metrics
        dimensions[QualityDimension.CONSISTENCY.value] = self.calculate_code_quality_score()
        
        # Efficiency - based on performance metrics
        dimensions[QualityDimension.EFFICIENCY.value] = self.aggregate_metrics["performance_score"]
        
        # Reliability - based on error rates and test coverage
        avg_test_coverage = statistics.mean(
            [m.test_coverage for m in self.code_quality_metrics.values()]
        ) if self.code_quality_metrics else 0
        dimensions[QualityDimension.RELIABILITY.value] = avg_test_coverage
        
        # Security - based on security compliance
        dimensions[QualityDimension.SECURITY.value] = self.calculate_security_compliance()
        
        # Usability - based on documentation and comment ratio
        avg_comment_ratio = statistics.mean(
            [m.comment_ratio * 100 for m in self.code_quality_metrics.values()]
        ) if self.code_quality_metrics else 0
        dimensions[QualityDimension.USABILITY.value] = min(100, avg_comment_ratio * 5)  # Scale up
        
        # Maintainability - based on complexity and code smells
        complexity_scores = []
        for metric in self.code_quality_metrics.values():
            if metric.cyclomatic_complexity <= 10:
                complexity_scores.append(100)
            elif metric.cyclomatic_complexity <= 20:
                complexity_scores.append(75)
            else:
                complexity_scores.append(50)
        dimensions[QualityDimension.MAINTAINABILITY.value] = statistics.mean(complexity_scores) if complexity_scores else 0
        
        self.aggregate_metrics["quality_dimensions"] = dimensions
        
        return dimensions
        
    def check_thresholds(self) -> Dict[str, bool]:
        """Check if quality thresholds are met"""
        results = {}
        
        # Check requirement coverage
        results["requirement_coverage"] = (
            self.aggregate_metrics["average_completion"] >= self.thresholds["min_requirement_coverage"]
        )
        
        # Check code quality
        results["code_quality"] = (
            self.aggregate_metrics["average_code_quality"] >= self.thresholds["min_code_quality"]
        )
        
        # Check security compliance
        results["security_compliance"] = (
            self.aggregate_metrics["security_compliance"] >= self.thresholds["min_security_compliance"]
        )
        
        # Check complexity
        high_complexity_files = [
            f for f, m in self.code_quality_metrics.items()
            if m.cyclomatic_complexity > self.thresholds["max_complexity"]
        ]
        results["complexity"] = len(high_complexity_files) == 0
        
        # Check duplication
        high_duplication_files = [
            f for f, m in self.code_quality_metrics.items()
            if m.duplication_percentage > self.thresholds["max_duplication"]
        ]
        results["duplication"] = len(high_duplication_files) == 0
        
        return results
        
    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        # Calculate all metrics
        self.calculate_requirement_coverage()
        self.calculate_code_quality_score()
        self.calculate_security_compliance()
        
        # Default SLA requirements
        default_sla = {
            "max_latency_p95": 1000,  # 1 second
            "min_throughput": 100,     # 100 ops/sec
            "max_error_rate": 0.01     # 1% error rate
        }
        self.calculate_performance_score(default_sla)
        
        # Evaluate quality dimensions
        dimensions = self.evaluate_quality_dimensions()
        
        # Calculate overall quality score
        self.aggregate_metrics["overall_quality_score"] = statistics.mean(dimensions.values())
        
        # Check thresholds
        threshold_results = self.check_thresholds()
        
        # Find top issues
        top_security_issues = []
        for metric in self.code_quality_metrics.values():
            top_security_issues.extend(metric.security_issues)
        top_security_issues = list(set(top_security_issues))[:5]
        
        top_code_smells = []
        for metric in self.code_quality_metrics.values():
            top_code_smells.extend(metric.code_smells)
        top_code_smells = list(set(top_code_smells))[:5]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(threshold_results, dimensions)
        
        return {
            "project_name": self.project_name,
            "execution_time": (datetime.now() - self.start_time).total_seconds(),
            "summary": {
                "overall_quality_score": self.aggregate_metrics["overall_quality_score"],
                "requirements_completed": f"{self.aggregate_metrics['requirements_completed']}/{self.aggregate_metrics['total_requirements']}",
                "average_completion": f"{self.aggregate_metrics['average_completion']:.1f}%",
                "files_created": self.aggregate_metrics["total_files_created"],
                "tests_created": self.aggregate_metrics["total_tests_created"]
            },
            "quality_dimensions": {
                dim: f"{score:.1f}%" for dim, score in dimensions.items()
            },
            "threshold_compliance": threshold_results,
            "top_issues": {
                "security": top_security_issues,
                "code_smells": top_code_smells
            },
            "detailed_metrics": {
                "requirement_coverage": self.aggregate_metrics["average_completion"],
                "code_quality": self.aggregate_metrics["average_code_quality"],
                "security_compliance": self.aggregate_metrics["security_compliance"],
                "performance_score": self.aggregate_metrics["performance_score"]
            },
            "recommendations": recommendations
        }
        
    def _generate_recommendations(self, 
                                 threshold_results: Dict[str, bool],
                                 dimensions: Dict[str, float]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Threshold-based recommendations
        if not threshold_results.get("requirement_coverage"):
            recommendations.append(
                f"Increase requirement coverage from {self.aggregate_metrics['average_completion']:.1f}% "
                f"to at least {self.thresholds['min_requirement_coverage']}%"
            )
            
        if not threshold_results.get("code_quality"):
            recommendations.append(
                f"Improve code quality score from {self.aggregate_metrics['average_code_quality']:.1f} "
                f"to at least {self.thresholds['min_code_quality']}"
            )
            
        if not threshold_results.get("security_compliance"):
            recommendations.append(
                f"Enhance security compliance from {self.aggregate_metrics['security_compliance']:.1f}% "
                f"to at least {self.thresholds['min_security_compliance']}%"
            )
            
        if not threshold_results.get("complexity"):
            recommendations.append(
                "Refactor high complexity methods to reduce cyclomatic complexity below 20"
            )
            
        if not threshold_results.get("duplication"):
            recommendations.append(
                "Extract duplicate code into reusable functions to reduce duplication below 10%"
            )
            
        # Dimension-based recommendations
        low_dimensions = [dim for dim, score in dimensions.items() if score < 70]
        
        for dim in low_dimensions:
            if dim == QualityDimension.CORRECTNESS.value:
                recommendations.append("Review and complete missing requirement acceptance criteria")
            elif dim == QualityDimension.COMPLETENESS.value:
                recommendations.append("Ensure all required files and tests are created")
            elif dim == QualityDimension.CONSISTENCY.value:
                recommendations.append("Apply consistent coding standards across all files")
            elif dim == QualityDimension.EFFICIENCY.value:
                recommendations.append("Optimize performance bottlenecks to meet SLA requirements")
            elif dim == QualityDimension.RELIABILITY.value:
                recommendations.append("Increase test coverage to at least 60%")
            elif dim == QualityDimension.SECURITY.value:
                recommendations.append("Address security vulnerabilities and implement security best practices")
            elif dim == QualityDimension.USABILITY.value:
                recommendations.append("Add comprehensive documentation and code comments")
            elif dim == QualityDimension.MAINTAINABILITY.value:
                recommendations.append("Reduce code complexity and eliminate code smells")
                
        return recommendations[:10]  # Top 10 recommendations