#!/usr/bin/env python3
"""
Enhanced Session Analysis Module - Section 9 Implementation

Features:
- Requirement coverage analysis with detailed tracking
- File creation audit trail with validation
- Actionable next steps generation
- Performance metrics and quality analysis
- Time-to-completion tracking
- Cross-session pattern detection
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import re
from collections import defaultdict

# Import existing modules
try:
    from .session_manager import SessionManager
    from .agent_logger import get_logger
except ImportError:
    # Fallback for testing
    SessionManager = None
    def get_logger():
        return None

class RequirementStatus(Enum):
    """Status of a requirement implementation"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PARTIALLY_COMPLETE = "partially_complete"
    COMPLETE = "complete"
    FAILED = "failed"
    BLOCKED = "blocked"

class DeliverableType(Enum):
    """Type of deliverable"""
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    TEST = "test"
    INFRASTRUCTURE = "infrastructure"
    API = "api"
    FRONTEND = "frontend"
    DATABASE = "database"

@dataclass
class RequirementCoverage:
    """Tracks coverage for a single requirement"""
    requirement_id: str
    description: str
    status: RequirementStatus
    completion_percentage: float
    agents_involved: List[str]
    files_created: List[str]
    tests_written: List[str]
    issues_found: List[str]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_spent: Optional[timedelta] = None
    blocking_issues: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "requirement_id": self.requirement_id,
            "description": self.description,
            "status": self.status.value,
            "completion_percentage": self.completion_percentage,
            "agents_involved": self.agents_involved,
            "files_created": self.files_created,
            "tests_written": self.tests_written,
            "issues_found": self.issues_found,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "time_spent": str(self.time_spent) if self.time_spent else None,
            "blocking_issues": self.blocking_issues,
            "dependencies": self.dependencies
        }

@dataclass
class FileAuditEntry:
    """Audit trail for a created file"""
    file_path: str
    agent_name: str
    created_at: datetime
    file_type: DeliverableType
    size_bytes: int
    verified: bool
    validation_errors: List[str]
    related_requirements: List[str]
    modifications: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "file_path": self.file_path,
            "agent_name": self.agent_name,
            "created_at": self.created_at.isoformat(),
            "file_type": self.file_type.value,
            "size_bytes": self.size_bytes,
            "verified": self.verified,
            "validation_errors": self.validation_errors,
            "related_requirements": self.related_requirements,
            "modifications": self.modifications
        }

@dataclass
class QualityMetrics:
    """Code quality metrics for a session"""
    total_lines_of_code: int
    test_coverage_percentage: float
    documentation_coverage: float
    complexity_score: float
    security_issues: int
    performance_issues: int
    best_practices_violations: int
    duplicate_code_percentage: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total_lines_of_code": self.total_lines_of_code,
            "test_coverage_percentage": self.test_coverage_percentage,
            "documentation_coverage": self.documentation_coverage,
            "complexity_score": self.complexity_score,
            "security_issues": self.security_issues,
            "performance_issues": self.performance_issues,
            "best_practices_violations": self.best_practices_violations,
            "duplicate_code_percentage": self.duplicate_code_percentage
        }

class SessionAnalysisEnhanced:
    """Enhanced session analysis with comprehensive reporting"""
    
    def __init__(self, session_path: Optional[str] = None):
        """Initialize enhanced session analyzer"""
        self.session_path = Path(session_path) if session_path else Path("sessions")
        self.logger = get_logger() if get_logger else None
        self.requirement_coverage: Dict[str, RequirementCoverage] = {}
        self.file_audit_trail: List[FileAuditEntry] = []
        self.quality_metrics = None
        self.deliverables_expected: Dict[str, List[str]] = {}
        self.deliverables_actual: Dict[str, List[str]] = {}
        
    def analyze_session(self, session_id: str) -> Dict[str, Any]:
        """Perform comprehensive session analysis"""
        session_file = self.session_path / f"session_{session_id}.json"
        
        if not session_file.exists():
            return {"error": f"Session {session_id} not found"}
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Extract and analyze different aspects
        requirements_analysis = self._analyze_requirements(session_data)
        file_audit = self._create_file_audit_trail(session_data)
        quality_analysis = self._analyze_code_quality(session_data)
        performance_analysis = self._analyze_performance(session_data)
        deliverables_analysis = self._analyze_deliverables(session_data)
        next_steps = self._generate_next_steps(requirements_analysis, deliverables_analysis)
        
        return {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "requirements_coverage": requirements_analysis,
            "file_audit_trail": file_audit,
            "quality_metrics": quality_analysis,
            "performance_metrics": performance_analysis,
            "deliverables_comparison": deliverables_analysis,
            "actionable_next_steps": next_steps,
            "summary": self._generate_summary(
                requirements_analysis,
                file_audit,
                quality_analysis,
                deliverables_analysis
            )
        }
    
    def _analyze_requirements(self, session_data: Dict) -> Dict[str, Any]:
        """Analyze requirement coverage from session data"""
        requirements = {}
        
        # Extract requirements from context
        if "context" in session_data and "project_requirements" in session_data["context"]:
            project_reqs = session_data["context"]["project_requirements"]
            
            # Parse features into requirements
            if "features" in project_reqs:
                for idx, feature in enumerate(project_reqs["features"]):
                    req_id = f"REQ-{idx+1:03d}"
                    requirements[req_id] = self._analyze_single_requirement(
                        req_id, feature, session_data
                    )
        
        # Calculate overall coverage
        total_reqs = len(requirements)
        completed_reqs = sum(1 for r in requirements.values() 
                           if r["status"] == RequirementStatus.COMPLETE.value)
        partial_reqs = sum(1 for r in requirements.values() 
                         if r["status"] == RequirementStatus.PARTIALLY_COMPLETE.value)
        
        overall_coverage = (completed_reqs + (partial_reqs * 0.5)) / total_reqs * 100 if total_reqs > 0 else 0
        
        return {
            "total_requirements": total_reqs,
            "completed": completed_reqs,
            "partially_completed": partial_reqs,
            "not_started": total_reqs - completed_reqs - partial_reqs,
            "overall_coverage_percentage": overall_coverage,
            "requirements": requirements,
            "critical_gaps": self._identify_critical_gaps(requirements)
        }
    
    def _analyze_single_requirement(self, req_id: str, description: str, 
                                   session_data: Dict) -> Dict:
        """Analyze coverage for a single requirement"""
        coverage = RequirementCoverage(
            requirement_id=req_id,
            description=description,
            status=RequirementStatus.NOT_STARTED,
            completion_percentage=0.0,
            agents_involved=[],
            files_created=[],
            tests_written=[],
            issues_found=[]
        )
        
        # Check events for requirement implementation
        if "events" in session_data:
            for event in session_data["events"]:
                if "requirement" in str(event).lower() or description.lower() in str(event).lower():
                    # Track agent involvement
                    if "agent_name" in event:
                        if event["agent_name"] not in coverage.agents_involved:
                            coverage.agents_involved.append(event["agent_name"])
                    
                    # Track file creation
                    if "file_path" in event or "file_created" in event:
                        file_path = event.get("file_path") or event.get("file_created")
                        if file_path and file_path not in coverage.files_created:
                            coverage.files_created.append(file_path)
                    
                    # Track test creation
                    if "test" in str(event).lower() and "file_path" in event:
                        test_file = event["file_path"]
                        if test_file not in coverage.tests_written:
                            coverage.tests_written.append(test_file)
        
        # Determine status and completion
        if coverage.files_created:
            if coverage.tests_written:
                coverage.status = RequirementStatus.COMPLETE
                coverage.completion_percentage = 100.0
            else:
                coverage.status = RequirementStatus.PARTIALLY_COMPLETE
                coverage.completion_percentage = 70.0
        elif coverage.agents_involved:
            coverage.status = RequirementStatus.IN_PROGRESS
            coverage.completion_percentage = 30.0
        
        return coverage.to_dict()
    
    def _create_file_audit_trail(self, session_data: Dict) -> List[Dict]:
        """Create comprehensive file audit trail"""
        audit_trail = []
        
        if "events" in session_data:
            for event in session_data["events"]:
                if event.get("type") == "tool_call" and event.get("tool_name") == "write_file":
                    # Extract file information
                    params = event.get("params", {})
                    file_path = params.get("file_path", "")
                    
                    # Determine file type
                    file_type = self._determine_file_type(file_path)
                    
                    # Create audit entry
                    entry = FileAuditEntry(
                        file_path=file_path,
                        agent_name=event.get("agent_name", "unknown"),
                        created_at=datetime.fromisoformat(event.get("timestamp", datetime.now().isoformat())),
                        file_type=file_type,
                        size_bytes=len(params.get("content", "")),
                        verified=self._verify_file_creation(file_path),
                        validation_errors=self._validate_file_content(file_path, params.get("content", "")),
                        related_requirements=self._extract_related_requirements(params.get("reasoning", ""))
                    )
                    
                    audit_trail.append(entry.to_dict())
        
        return audit_trail
    
    def _determine_file_type(self, file_path: str) -> DeliverableType:
        """Determine the type of deliverable from file path"""
        path_lower = file_path.lower()
        
        if any(ext in path_lower for ext in ['.py', '.js', '.ts', '.java', '.cpp']):
            if 'test' in path_lower:
                return DeliverableType.TEST
            return DeliverableType.CODE
        elif any(ext in path_lower for ext in ['.md', '.rst', '.txt']):
            return DeliverableType.DOCUMENTATION
        elif any(ext in path_lower for ext in ['.json', '.yaml', '.yml', '.toml', '.ini']):
            return DeliverableType.CONFIGURATION
        elif 'docker' in path_lower or '.sh' in path_lower:
            return DeliverableType.INFRASTRUCTURE
        elif 'api' in path_lower or 'route' in path_lower or 'endpoint' in path_lower:
            return DeliverableType.API
        elif any(term in path_lower for term in ['component', 'page', 'view', '.jsx', '.tsx']):
            return DeliverableType.FRONTEND
        elif any(term in path_lower for term in ['model', 'schema', 'migration', '.sql']):
            return DeliverableType.DATABASE
        else:
            return DeliverableType.CODE
    
    def _verify_file_creation(self, file_path: str) -> bool:
        """Verify if file was actually created"""
        return Path(file_path).exists() if file_path else False
    
    def _validate_file_content(self, file_path: str, content: str) -> List[str]:
        """Validate file content for common issues"""
        errors = []
        
        if not content:
            errors.append("Empty file content")
        
        # Check for common issues
        if "TODO" in content or "FIXME" in content:
            errors.append("Contains unfinished TODO/FIXME markers")
        
        if file_path.endswith('.py'):
            # Python-specific validation
            if "import" not in content and "def" not in content and "class" not in content:
                errors.append("Python file lacks basic structure")
            if "```" in content:
                errors.append("Contains markdown code blocks (possible formatting error)")
        
        if file_path.endswith(('.js', '.ts')):
            # JavaScript/TypeScript validation
            if "function" not in content and "const" not in content and "class" not in content:
                errors.append("JavaScript/TypeScript file lacks basic structure")
        
        return errors
    
    def _extract_related_requirements(self, reasoning: str) -> List[str]:
        """Extract requirement IDs from reasoning text"""
        requirements = []
        
        # Look for REQ-XXX patterns
        req_pattern = r'REQ-\d{3}'
        matches = re.findall(req_pattern, reasoning)
        requirements.extend(matches)
        
        # Look for feature mentions
        feature_keywords = ['authentication', 'api', 'frontend', 'database', 'testing', 
                          'deployment', 'monitoring', 'security']
        for keyword in feature_keywords:
            if keyword in reasoning.lower():
                requirements.append(f"FEATURE-{keyword.upper()}")
        
        return list(set(requirements))
    
    def _analyze_code_quality(self, session_data: Dict) -> Dict:
        """Analyze code quality metrics"""
        metrics = QualityMetrics(
            total_lines_of_code=0,
            test_coverage_percentage=0.0,
            documentation_coverage=0.0,
            complexity_score=0.0,
            security_issues=0,
            performance_issues=0,
            best_practices_violations=0,
            duplicate_code_percentage=0.0
        )
        
        total_files = 0
        test_files = 0
        doc_files = 0
        
        if "events" in session_data:
            for event in session_data["events"]:
                if event.get("type") == "tool_call" and event.get("tool_name") == "write_file":
                    params = event.get("params", {})
                    content = params.get("content", "")
                    file_path = params.get("file_path", "")
                    
                    # Count lines of code
                    metrics.total_lines_of_code += len(content.split('\n'))
                    total_files += 1
                    
                    # Track test files
                    if 'test' in file_path.lower():
                        test_files += 1
                    
                    # Track documentation
                    if file_path.endswith(('.md', '.rst', '.txt')):
                        doc_files += 1
                    
                    # Check for security issues
                    security_patterns = ['password', 'secret', 'api_key', 'token']
                    for pattern in security_patterns:
                        if pattern in content.lower() and '=' in content:
                            metrics.security_issues += 1
                    
                    # Check for performance issues
                    performance_patterns = ['sleep(', 'time.sleep', 'SELECT *', 'N+1']
                    for pattern in performance_patterns:
                        if pattern in content:
                            metrics.performance_issues += 1
                    
                    # Check for best practices violations
                    if file_path.endswith('.py'):
                        if 'except:' in content:  # Bare except
                            metrics.best_practices_violations += 1
                        if 'import *' in content:  # Star imports
                            metrics.best_practices_violations += 1
        
        # Calculate coverage percentages
        if total_files > 0:
            metrics.test_coverage_percentage = (test_files / total_files) * 100
            metrics.documentation_coverage = (doc_files / total_files) * 100
        
        # Estimate complexity (simplified)
        metrics.complexity_score = min(10, metrics.total_lines_of_code / 1000)
        
        return metrics.to_dict()
    
    def _analyze_performance(self, session_data: Dict) -> Dict:
        """Analyze performance metrics"""
        performance = {
            "total_duration": 0,
            "agent_execution_times": {},
            "tool_call_frequency": {},
            "bottlenecks": [],
            "optimization_opportunities": []
        }
        
        # Calculate total duration
        if "start_time" in session_data and "end_time" in session_data:
            start = datetime.fromisoformat(session_data["start_time"])
            end = datetime.fromisoformat(session_data["end_time"])
            performance["total_duration"] = (end - start).total_seconds()
        
        # Analyze agent execution times
        agent_times = defaultdict(list)
        if "events" in session_data:
            for event in session_data["events"]:
                if event.get("type") == "agent_complete":
                    agent_name = event.get("agent_name")
                    duration = event.get("duration", 0)
                    agent_times[agent_name].append(duration)
        
        # Calculate average times
        for agent, times in agent_times.items():
            avg_time = sum(times) / len(times) if times else 0
            performance["agent_execution_times"][agent] = {
                "average": avg_time,
                "total": sum(times),
                "count": len(times)
            }
            
            # Identify bottlenecks
            if avg_time > 30:  # More than 30 seconds average
                performance["bottlenecks"].append({
                    "agent": agent,
                    "average_time": avg_time,
                    "recommendation": f"Consider optimizing {agent} or splitting into smaller tasks"
                })
        
        # Analyze tool call frequency
        tool_calls = defaultdict(int)
        if "events" in session_data:
            for event in session_data["events"]:
                if event.get("type") == "tool_call":
                    tool_name = event.get("tool_name")
                    tool_calls[tool_name] += 1
        
        performance["tool_call_frequency"] = dict(tool_calls)
        
        # Identify optimization opportunities
        if tool_calls.get("write_file", 0) > 50:
            performance["optimization_opportunities"].append(
                "High file write frequency - consider batching file operations"
            )
        
        if len(performance["bottlenecks"]) > 3:
            performance["optimization_opportunities"].append(
                "Multiple bottlenecks detected - consider parallel execution"
            )
        
        return performance
    
    def _analyze_deliverables(self, session_data: Dict) -> Dict:
        """Compare expected vs actual deliverables"""
        comparison = {
            "expected": {},
            "actual": {},
            "missing": [],
            "unexpected": [],
            "completion_rate": 0.0
        }
        
        # Define expected deliverables based on project type
        project_type = session_data.get("context", {}).get("project_requirements", {}).get("type", "")
        
        if project_type == "web_app":
            comparison["expected"] = {
                "backend": ["main.py", "requirements.txt", "Dockerfile"],
                "frontend": ["package.json", "src/App.js", "src/index.js"],
                "database": ["schema.sql", "migrations/"],
                "tests": ["test_*.py", "*.test.js"],
                "documentation": ["README.md", "API.md"],
                "infrastructure": ["docker-compose.yml", ".env.example"]
            }
        elif project_type == "api_service":
            comparison["expected"] = {
                "backend": ["main.py", "requirements.txt", "routes/"],
                "tests": ["test_*.py"],
                "documentation": ["README.md", "API.md"],
                "infrastructure": ["Dockerfile", "docker-compose.yml"]
            }
        
        # Track actual deliverables
        actual_by_category = defaultdict(list)
        if "events" in session_data:
            for event in session_data["events"]:
                if event.get("type") == "tool_call" and event.get("tool_name") == "write_file":
                    file_path = event.get("params", {}).get("file_path", "")
                    category = self._categorize_deliverable(file_path)
                    actual_by_category[category].append(file_path)
        
        comparison["actual"] = dict(actual_by_category)
        
        # Find missing deliverables
        for category, expected_files in comparison["expected"].items():
            actual_files = comparison["actual"].get(category, [])
            for expected in expected_files:
                if not any(expected in actual or actual.endswith(expected) 
                          for actual in actual_files):
                    comparison["missing"].append({
                        "category": category,
                        "file": expected,
                        "importance": "high" if category in ["backend", "frontend"] else "medium"
                    })
        
        # Find unexpected deliverables
        for category, actual_files in comparison["actual"].items():
            if category not in comparison["expected"]:
                for file in actual_files:
                    comparison["unexpected"].append({
                        "category": category,
                        "file": file,
                        "note": "Additional deliverable not in initial requirements"
                    })
        
        # Calculate completion rate
        total_expected = sum(len(files) for files in comparison["expected"].values())
        total_found = sum(min(len(comparison["actual"].get(cat, [])), len(files)) 
                         for cat, files in comparison["expected"].items())
        comparison["completion_rate"] = (total_found / total_expected * 100) if total_expected > 0 else 0
        
        return comparison
    
    def _categorize_deliverable(self, file_path: str) -> str:
        """Categorize a deliverable based on file path"""
        path_lower = file_path.lower()
        
        if 'test' in path_lower:
            return "tests"
        elif any(term in path_lower for term in ['component', 'src/', 'public/', '.jsx', '.tsx', '.js']):
            return "frontend"
        elif any(term in path_lower for term in ['route', 'api', 'endpoint', 'controller']):
            return "backend"
        elif any(term in path_lower for term in ['model', 'schema', 'migration', '.sql']):
            return "database"
        elif any(term in path_lower for term in ['.md', '.rst', 'readme', 'doc']):
            return "documentation"
        elif any(term in path_lower for term in ['docker', '.yml', '.yaml', '.env']):
            return "infrastructure"
        else:
            return "other"
    
    def _generate_next_steps(self, requirements_analysis: Dict, 
                            deliverables_analysis: Dict) -> List[Dict]:
        """Generate actionable next steps based on analysis"""
        next_steps = []
        priority = 1
        
        # Address missing critical deliverables
        for missing in deliverables_analysis.get("missing", []):
            if missing.get("importance", "medium") == "high":
                next_steps.append({
                    "priority": priority,
                    "action": f"Create missing {missing['category']} file: {missing['file']}",
                    "agent": self._suggest_agent_for_task(missing['category']),
                    "estimated_time": "15-30 minutes",
                    "impact": "Critical - Required for basic functionality"
                })
                priority += 1
        
        # Complete partial requirements
        for req_id, req_data in requirements_analysis.get("requirements", {}).items():
            if req_data["status"] == RequirementStatus.PARTIALLY_COMPLETE.value:
                next_steps.append({
                    "priority": priority,
                    "action": f"Complete requirement {req_id}: {req_data['description']}",
                    "details": f"Missing: Tests and documentation",
                    "agent": "quality-guardian",
                    "estimated_time": "30-45 minutes",
                    "impact": "High - Improves reliability and maintainability"
                })
                priority += 1
        
        # Address quality issues
        quality_metrics = requirements_analysis.get("quality_metrics", {})
        if quality_metrics:
            if quality_metrics.get("security_issues", 0) > 0:
                next_steps.append({
                    "priority": priority,
                    "action": "Fix security issues in code",
                    "details": f"Found {quality_metrics['security_issues']} potential security issues",
                    "agent": "quality-guardian",
                    "estimated_time": "1-2 hours",
                    "impact": "Critical - Security vulnerabilities must be addressed"
                })
                priority += 1
            
            if quality_metrics.get("test_coverage_percentage", 0) < 80:
                next_steps.append({
                    "priority": priority,
                    "action": "Increase test coverage",
                    "details": f"Current coverage: {quality_metrics.get('test_coverage_percentage', 0):.1f}%",
                    "agent": "quality-guardian",
                    "estimated_time": "2-3 hours",
                    "impact": "High - Improves code reliability"
                })
                priority += 1
        
        # Start unimplemented requirements
        for req_id, req_data in requirements_analysis.get("requirements", {}).items():
            if req_data["status"] == RequirementStatus.NOT_STARTED.value and priority <= 10:
                next_steps.append({
                    "priority": priority,
                    "action": f"Implement requirement {req_id}",
                    "details": req_data["description"],
                    "agent": self._suggest_agent_for_requirement(req_data["description"]),
                    "estimated_time": "1-3 hours",
                    "impact": "Medium - Adds planned functionality"
                })
                priority += 1
        
        return next_steps[:10]  # Return top 10 priority items
    
    def _suggest_agent_for_task(self, category: str) -> str:
        """Suggest the best agent for a task category"""
        agent_mapping = {
            "backend": "rapid-builder",
            "frontend": "frontend-specialist",
            "database": "database-expert",
            "tests": "quality-guardian",
            "documentation": "documentation-writer",
            "infrastructure": "devops-engineer",
            "api": "api-integrator"
        }
        return agent_mapping.get(category, "rapid-builder")
    
    def _suggest_agent_for_requirement(self, description: str) -> str:
        """Suggest the best agent based on requirement description"""
        desc_lower = description.lower()
        
        if any(term in desc_lower for term in ['ui', 'interface', 'frontend', 'react']):
            return "frontend-specialist"
        elif any(term in desc_lower for term in ['api', 'endpoint', 'rest', 'graphql']):
            return "api-integrator"
        elif any(term in desc_lower for term in ['database', 'sql', 'migration', 'schema']):
            return "database-expert"
        elif any(term in desc_lower for term in ['test', 'quality', 'security']):
            return "quality-guardian"
        elif any(term in desc_lower for term in ['deploy', 'docker', 'ci/cd', 'infrastructure']):
            return "devops-engineer"
        elif any(term in desc_lower for term in ['ai', 'ml', 'gpt', 'llm']):
            return "ai-specialist"
        else:
            return "rapid-builder"
    
    def _identify_critical_gaps(self, requirements: Dict[str, Dict]) -> List[Dict]:
        """Identify critical gaps in requirement implementation"""
        gaps = []
        
        for req_id, req_data in requirements.items():
            if req_data["status"] in [RequirementStatus.NOT_STARTED.value, 
                                     RequirementStatus.FAILED.value]:
                # Determine criticality
                description = req_data["description"].lower()
                is_critical = any(term in description for term in 
                                ['authentication', 'security', 'payment', 'core', 'main'])
                
                gaps.append({
                    "requirement_id": req_id,
                    "description": req_data["description"],
                    "status": req_data["status"],
                    "criticality": "critical" if is_critical else "normal",
                    "recommendation": self._get_gap_recommendation(req_data)
                })
        
        # Sort by criticality
        gaps.sort(key=lambda x: (x["criticality"] != "critical", x["requirement_id"]))
        
        return gaps
    
    def _get_gap_recommendation(self, requirement: Dict) -> str:
        """Get recommendation for addressing a requirement gap"""
        if requirement["status"] == RequirementStatus.FAILED.value:
            return f"Retry with {self._suggest_agent_for_requirement(requirement['description'])} after addressing blocking issues"
        elif requirement["status"] == RequirementStatus.NOT_STARTED.value:
            return f"Start implementation with {self._suggest_agent_for_requirement(requirement['description'])}"
        else:
            return "Review and complete remaining tasks"
    
    def _generate_summary(self, requirements: Dict, file_audit: List, 
                         quality: Dict, deliverables: Dict) -> Dict:
        """Generate executive summary of session analysis"""
        return {
            "overall_success": requirements.get("overall_coverage_percentage", 0) >= 80,
            "requirement_coverage": f"{requirements.get('overall_coverage_percentage', 0):.1f}%",
            "files_created": len(file_audit),
            "deliverable_completion": f"{deliverables.get('completion_rate', 0):.1f}%",
            "critical_issues": len([g for g in requirements.get('critical_gaps', []) 
                                   if g.get('criticality') == 'critical']),
            "quality_score": self._calculate_quality_score(quality),
            "recommended_priority": "Complete missing critical deliverables" 
                                  if deliverables.get("missing") 
                                  else "Increase test coverage",
            "estimated_time_to_completion": self._estimate_completion_time(
                requirements, deliverables
            )
        }
    
    def _calculate_quality_score(self, quality: Dict) -> float:
        """Calculate overall quality score (0-100)"""
        if not quality:
            return 0.0
        
        score = 100.0
        
        # Deduct for issues
        score -= quality.get("security_issues", 0) * 10
        score -= quality.get("performance_issues", 0) * 5
        score -= quality.get("best_practices_violations", 0) * 3
        
        # Factor in coverage
        test_coverage = quality.get("test_coverage_percentage", 0)
        doc_coverage = quality.get("documentation_coverage", 0)
        
        coverage_score = (test_coverage * 0.6 + doc_coverage * 0.4) / 100 * 30
        score = max(0, min(100, score * 0.7 + coverage_score))
        
        return round(score, 1)
    
    def _estimate_completion_time(self, requirements: Dict, deliverables: Dict) -> str:
        """Estimate time to complete remaining work"""
        remaining_reqs = (requirements.get("total_requirements", 0) - 
                         requirements.get("completed", 0))
        missing_deliverables = len(deliverables.get("missing", []))
        
        # Estimate 2 hours per requirement, 30 min per missing file
        total_hours = remaining_reqs * 2 + missing_deliverables * 0.5
        
        if total_hours < 1:
            return "Less than 1 hour"
        elif total_hours < 8:
            return f"{total_hours:.1f} hours"
        else:
            days = total_hours / 8
            return f"{days:.1f} days"
    
    def generate_html_report(self, analysis: Dict) -> str:
        """Generate HTML report from analysis"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Session Analysis Report - {analysis['session_id']}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                .summary {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
                .metric-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; }}
                .progress-bar {{ width: 100%; height: 30px; background: #ecf0f1; border-radius: 15px; overflow: hidden; }}
                .progress-fill {{ height: 100%; background: linear-gradient(90deg, #3498db, #2ecc71); transition: width 0.3s; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #3498db; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
                tr:hover {{ background: #f8f9fa; }}
                .status-complete {{ color: #27ae60; font-weight: bold; }}
                .status-partial {{ color: #f39c12; font-weight: bold; }}
                .status-failed {{ color: #e74c3c; font-weight: bold; }}
                .next-step {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }}
                .critical {{ border-left-color: #dc3545; background: #f8d7da; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Session Analysis Report</h1>
                <div class="summary">
                    <div class="metric">
                        <div class="metric-value">{analysis['summary']['requirement_coverage']}</div>
                        <div class="metric-label">Requirement Coverage</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{analysis['summary']['files_created']}</div>
                        <div class="metric-label">Files Created</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{analysis['summary']['quality_score']}</div>
                        <div class="metric-label">Quality Score</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{analysis['summary']['estimated_time_to_completion']}</div>
                        <div class="metric-label">Time to Complete</div>
                    </div>
                </div>
                
                <h2>Requirements Coverage</h2>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {analysis['requirements_coverage']['overall_coverage_percentage']}%"></div>
                </div>
                <table>
                    <tr>
                        <th>Requirement ID</th>
                        <th>Description</th>
                        <th>Status</th>
                        <th>Completion</th>
                        <th>Agents Involved</th>
                    </tr>
        """
        
        for req_id, req_data in analysis['requirements_coverage']['requirements'].items():
            status_class = 'status-complete' if req_data['status'] == 'complete' else 'status-partial' if req_data['status'] == 'partially_complete' else 'status-failed'
            html += f"""
                    <tr>
                        <td>{req_id}</td>
                        <td>{req_data['description']}</td>
                        <td class="{status_class}">{req_data['status'].replace('_', ' ').title()}</td>
                        <td>{req_data['completion_percentage']:.0f}%</td>
                        <td>{', '.join(req_data['agents_involved']) or 'None'}</td>
                    </tr>
            """
        
        html += """
                </table>
                
                <h2>Actionable Next Steps</h2>
        """
        
        for step in analysis['actionable_next_steps']:
            critical_class = 'critical' if step.get('impact', '').startswith('Critical') else ''
            html += f"""
                <div class="next-step {critical_class}">
                    <strong>Priority {step['priority']}:</strong> {step['action']}<br>
                    <small>Agent: {step['agent']} | Time: {step['estimated_time']} | Impact: {step['impact']}</small>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html


def main():
    """Main function for testing"""
    analyzer = SessionAnalysisEnhanced()
    
    # Example usage
    import sys
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
        analysis = analyzer.analyze_session(session_id)
        
        # Save JSON report
        report_file = f"session_analysis_{session_id}.json"
        with open(report_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"Analysis saved to {report_file}")
        
        # Save HTML report
        html_file = f"session_analysis_{session_id}.html"
        with open(html_file, 'w') as f:
            f.write(analyzer.generate_html_report(analysis))
        print(f"HTML report saved to {html_file}")
    else:
        print("Usage: python session_analysis_enhanced.py <session_id>")


if __name__ == "__main__":
    main()