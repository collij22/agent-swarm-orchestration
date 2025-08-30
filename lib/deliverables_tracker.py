#!/usr/bin/env python3
"""
Deliverables Tracker - Section 9.2 Implementation

Features:
- Track expected vs actual deliverables
- File categorization and validation
- Missing component detection
- Deliverable quality assessment
- Time-to-completion tracking
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict


class DeliverableCategory(Enum):
    """Categories of deliverables"""
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    API = "api"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"


class DeliverableStatus(Enum):
    """Status of a deliverable"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    VALIDATED = "validated"
    FAILED = "failed"
    MISSING = "missing"


@dataclass
class Deliverable:
    """Represents a single deliverable"""
    name: str
    category: DeliverableCategory
    description: str
    expected_path: str
    actual_path: Optional[str] = None
    status: DeliverableStatus = DeliverableStatus.NOT_STARTED
    size_bytes: int = 0
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    validation_errors: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    dependent_on_by: List[str] = field(default_factory=list)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the deliverable"""
        errors = []
        
        if not self.actual_path:
            errors.append(f"Deliverable {self.name} not found at expected path {self.expected_path}")
            self.status = DeliverableStatus.MISSING
            return False, errors
        
        # Check if file exists
        if not Path(self.actual_path).exists():
            errors.append(f"File {self.actual_path} does not exist")
            self.status = DeliverableStatus.MISSING
            return False, errors
        
        # Check file size
        if self.size_bytes == 0:
            errors.append(f"File {self.actual_path} is empty")
        
        # Category-specific validation
        if self.category == DeliverableCategory.BACKEND:
            errors.extend(self._validate_backend())
        elif self.category == DeliverableCategory.FRONTEND:
            errors.extend(self._validate_frontend())
        elif self.category == DeliverableCategory.DATABASE:
            errors.extend(self._validate_database())
        elif self.category == DeliverableCategory.TESTING:
            errors.extend(self._validate_testing())
        elif self.category == DeliverableCategory.INFRASTRUCTURE:
            errors.extend(self._validate_infrastructure())
        
        self.validation_errors = errors
        
        if not errors:
            self.status = DeliverableStatus.VALIDATED
            self.quality_score = 100.0
        else:
            self.status = DeliverableStatus.COMPLETE if self.actual_path else DeliverableStatus.MISSING
            self.quality_score = max(0, 100 - len(errors) * 10)
        
        return len(errors) == 0, errors
    
    def _validate_backend(self) -> List[str]:
        """Validate backend deliverables"""
        errors = []
        
        if self.actual_path and self.actual_path.endswith('.py'):
            try:
                with open(self.actual_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for basic Python structure
                if not any(keyword in content for keyword in ['def ', 'class ', 'import ']):
                    errors.append("Python file lacks basic structure")
                
                # Check for main entry point
                if 'main.py' in self.actual_path and '__main__' not in content:
                    errors.append("Main file lacks entry point")
                
                # Check for error handling
                if 'try:' not in content and 'except' not in content:
                    errors.append("No error handling found")
                    
            except Exception as e:
                errors.append(f"Failed to validate file: {str(e)}")
        
        return errors
    
    def _validate_frontend(self) -> List[str]:
        """Validate frontend deliverables"""
        errors = []
        
        if self.actual_path:
            if self.actual_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                try:
                    with open(self.actual_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Check for React components
                    if '.jsx' in self.actual_path or '.tsx' in self.actual_path:
                        if 'import React' not in content and 'from "react"' not in content:
                            errors.append("React import missing")
                        if 'export' not in content:
                            errors.append("No exports found")
                    
                    # Check for proper structure
                    if not any(keyword in content for keyword in ['function', 'const', 'class']):
                        errors.append("JavaScript/TypeScript file lacks basic structure")
                        
                except Exception as e:
                    errors.append(f"Failed to validate file: {str(e)}")
            
            elif 'package.json' in self.actual_path:
                try:
                    with open(self.actual_path, 'r') as f:
                        package = json.load(f)
                        
                    # Check required fields
                    if 'name' not in package:
                        errors.append("package.json missing 'name' field")
                    if 'dependencies' not in package:
                        errors.append("package.json missing 'dependencies'")
                        
                except Exception as e:
                    errors.append(f"Invalid package.json: {str(e)}")
        
        return errors
    
    def _validate_database(self) -> List[str]:
        """Validate database deliverables"""
        errors = []
        
        if self.actual_path and self.actual_path.endswith('.sql'):
            try:
                with open(self.actual_path, 'r', encoding='utf-8') as f:
                    content = f.read().upper()
                    
                # Check for basic SQL structure
                if not any(keyword in content for keyword in ['CREATE', 'TABLE', 'ALTER']):
                    errors.append("SQL file lacks DDL statements")
                
                # Check for primary keys
                if 'PRIMARY KEY' not in content:
                    errors.append("No primary key definitions found")
                    
            except Exception as e:
                errors.append(f"Failed to validate SQL file: {str(e)}")
        
        return errors
    
    def _validate_testing(self) -> List[str]:
        """Validate testing deliverables"""
        errors = []
        
        if self.actual_path:
            try:
                with open(self.actual_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for test structure
                if self.actual_path.endswith('.py'):
                    if 'test_' not in content and 'Test' not in content:
                        errors.append("No test functions or classes found")
                    if 'assert' not in content:
                        errors.append("No assertions found in test file")
                        
                elif self.actual_path.endswith(('.js', '.ts')):
                    if not any(keyword in content for keyword in ['test(', 'it(', 'describe(']):
                        errors.append("No test definitions found")
                    if 'expect(' not in content:
                        errors.append("No expectations found in test file")
                        
            except Exception as e:
                errors.append(f"Failed to validate test file: {str(e)}")
        
        return errors
    
    def _validate_infrastructure(self) -> List[str]:
        """Validate infrastructure deliverables"""
        errors = []
        
        if self.actual_path:
            if 'Dockerfile' in self.actual_path:
                try:
                    with open(self.actual_path, 'r') as f:
                        content = f.read()
                        
                    # Check for required Dockerfile elements
                    if 'FROM' not in content:
                        errors.append("Dockerfile missing FROM statement")
                    if 'WORKDIR' not in content:
                        errors.append("Dockerfile missing WORKDIR")
                    if 'EXPOSE' not in content and 'CMD' not in content:
                        errors.append("Dockerfile missing EXPOSE or CMD")
                        
                except Exception as e:
                    errors.append(f"Failed to validate Dockerfile: {str(e)}")
            
            elif 'docker-compose' in self.actual_path:
                try:
                    import yaml
                    with open(self.actual_path, 'r') as f:
                        compose = yaml.safe_load(f)
                        
                    if 'services' not in compose:
                        errors.append("docker-compose.yml missing 'services' section")
                        
                except Exception as e:
                    errors.append(f"Failed to validate docker-compose: {str(e)}")
        
        return errors


class DeliverablesTracker:
    """Tracks and compares expected vs actual deliverables"""
    
    def __init__(self, project_path: str = "."):
        """Initialize deliverables tracker"""
        self.project_path = Path(project_path)
        self.expected_deliverables: Dict[str, Deliverable] = {}
        self.actual_deliverables: Dict[str, Deliverable] = {}
        self.deliverable_graph: Dict[str, Set[str]] = defaultdict(set)
        self.category_stats: Dict[DeliverableCategory, Dict] = {}
        
    def define_expected_deliverables(self, project_type: str, features: List[str]) -> None:
        """Define expected deliverables based on project type and features"""
        
        if project_type == "web_app":
            self._define_web_app_deliverables(features)
        elif project_type == "api_service":
            self._define_api_service_deliverables(features)
        elif project_type == "mobile_app":
            self._define_mobile_app_deliverables(features)
        elif project_type == "ai_solution":
            self._define_ai_solution_deliverables(features)
        else:
            self._define_generic_deliverables(features)
        
        # Build dependency graph
        self._build_dependency_graph()
    
    def _define_web_app_deliverables(self, features: List[str]) -> None:
        """Define deliverables for a web application"""
        # Backend deliverables
        self._add_deliverable(
            "main.py", DeliverableCategory.BACKEND,
            "Main application entry point", "backend/main.py"
        )
        self._add_deliverable(
            "requirements.txt", DeliverableCategory.BACKEND,
            "Python dependencies", "backend/requirements.txt"
        )
        self._add_deliverable(
            "routes", DeliverableCategory.API,
            "API route definitions", "backend/routes/"
        )
        self._add_deliverable(
            "models", DeliverableCategory.DATABASE,
            "Database models", "backend/models/"
        )
        
        # Frontend deliverables
        self._add_deliverable(
            "package.json", DeliverableCategory.FRONTEND,
            "Node.js dependencies", "frontend/package.json"
        )
        self._add_deliverable(
            "App.js", DeliverableCategory.FRONTEND,
            "Main React component", "frontend/src/App.js"
        )
        self._add_deliverable(
            "components", DeliverableCategory.FRONTEND,
            "React components", "frontend/src/components/"
        )
        
        # Database deliverables
        self._add_deliverable(
            "schema.sql", DeliverableCategory.DATABASE,
            "Database schema", "database/schema.sql"
        )
        self._add_deliverable(
            "migrations", DeliverableCategory.DATABASE,
            "Database migrations", "database/migrations/"
        )
        
        # Testing deliverables
        self._add_deliverable(
            "test_api.py", DeliverableCategory.TESTING,
            "API tests", "tests/test_api.py"
        )
        self._add_deliverable(
            "test_frontend.js", DeliverableCategory.TESTING,
            "Frontend tests", "frontend/src/__tests__/"
        )
        
        # Documentation deliverables
        self._add_deliverable(
            "README.md", DeliverableCategory.DOCUMENTATION,
            "Project documentation", "README.md"
        )
        self._add_deliverable(
            "API.md", DeliverableCategory.DOCUMENTATION,
            "API documentation", "docs/API.md"
        )
        
        # Infrastructure deliverables
        self._add_deliverable(
            "Dockerfile", DeliverableCategory.INFRASTRUCTURE,
            "Docker container definition", "Dockerfile"
        )
        self._add_deliverable(
            "docker-compose.yml", DeliverableCategory.INFRASTRUCTURE,
            "Docker composition", "docker-compose.yml"
        )
        self._add_deliverable(
            ".env.example", DeliverableCategory.CONFIGURATION,
            "Environment variables template", ".env.example"
        )
        
        # Add feature-specific deliverables
        for feature in features:
            feature_lower = feature.lower()
            
            if "authentication" in feature_lower:
                self._add_deliverable(
                    "auth.py", DeliverableCategory.SECURITY,
                    "Authentication module", "backend/auth/auth.py"
                )
                self._add_deliverable(
                    "LoginComponent", DeliverableCategory.FRONTEND,
                    "Login component", "frontend/src/components/Login.js"
                )
            
            if "payment" in feature_lower:
                self._add_deliverable(
                    "payment.py", DeliverableCategory.BACKEND,
                    "Payment processing", "backend/services/payment.py"
                )
                self._add_deliverable(
                    "CheckoutComponent", DeliverableCategory.FRONTEND,
                    "Checkout component", "frontend/src/components/Checkout.js"
                )
            
            if "notification" in feature_lower:
                self._add_deliverable(
                    "notifications.py", DeliverableCategory.BACKEND,
                    "Notification service", "backend/services/notifications.py"
                )
            
            if "analytics" in feature_lower or "dashboard" in feature_lower:
                self._add_deliverable(
                    "Dashboard", DeliverableCategory.FRONTEND,
                    "Analytics dashboard", "frontend/src/pages/Dashboard.js"
                )
    
    def _define_api_service_deliverables(self, features: List[str]) -> None:
        """Define deliverables for an API service"""
        self._add_deliverable(
            "main.py", DeliverableCategory.BACKEND,
            "API entry point", "main.py"
        )
        self._add_deliverable(
            "requirements.txt", DeliverableCategory.BACKEND,
            "Python dependencies", "requirements.txt"
        )
        self._add_deliverable(
            "routes", DeliverableCategory.API,
            "API endpoints", "routes/"
        )
        self._add_deliverable(
            "models", DeliverableCategory.DATABASE,
            "Data models", "models/"
        )
        self._add_deliverable(
            "tests", DeliverableCategory.TESTING,
            "API tests", "tests/"
        )
        self._add_deliverable(
            "README.md", DeliverableCategory.DOCUMENTATION,
            "API documentation", "README.md"
        )
        self._add_deliverable(
            "Dockerfile", DeliverableCategory.INFRASTRUCTURE,
            "Container definition", "Dockerfile"
        )
    
    def _define_mobile_app_deliverables(self, features: List[str]) -> None:
        """Define deliverables for a mobile application"""
        # Add mobile-specific deliverables
        self._add_deliverable(
            "App.js", DeliverableCategory.FRONTEND,
            "Main app component", "src/App.js"
        )
        self._add_deliverable(
            "package.json", DeliverableCategory.FRONTEND,
            "Dependencies", "package.json"
        )
        self._add_deliverable(
            "screens", DeliverableCategory.FRONTEND,
            "App screens", "src/screens/"
        )
        self._add_deliverable(
            "components", DeliverableCategory.FRONTEND,
            "Reusable components", "src/components/"
        )
        self._add_deliverable(
            "api", DeliverableCategory.API,
            "API client", "src/api/"
        )
        self._add_deliverable(
            "tests", DeliverableCategory.TESTING,
            "Unit tests", "__tests__/"
        )
    
    def _define_ai_solution_deliverables(self, features: List[str]) -> None:
        """Define deliverables for an AI solution"""
        self._add_deliverable(
            "model.py", DeliverableCategory.BACKEND,
            "AI model implementation", "model/model.py"
        )
        self._add_deliverable(
            "training.py", DeliverableCategory.BACKEND,
            "Training pipeline", "training/training.py"
        )
        self._add_deliverable(
            "inference.py", DeliverableCategory.API,
            "Inference API", "api/inference.py"
        )
        self._add_deliverable(
            "requirements.txt", DeliverableCategory.BACKEND,
            "Python dependencies", "requirements.txt"
        )
        self._add_deliverable(
            "data", DeliverableCategory.DATABASE,
            "Training data", "data/"
        )
        self._add_deliverable(
            "notebooks", DeliverableCategory.DOCUMENTATION,
            "Jupyter notebooks", "notebooks/"
        )
        self._add_deliverable(
            "tests", DeliverableCategory.TESTING,
            "Model tests", "tests/"
        )
        self._add_deliverable(
            "Dockerfile", DeliverableCategory.INFRASTRUCTURE,
            "Container for model serving", "Dockerfile"
        )
    
    def _define_generic_deliverables(self, features: List[str]) -> None:
        """Define generic deliverables"""
        self._add_deliverable(
            "main", DeliverableCategory.BACKEND,
            "Main application file", "main.*"
        )
        self._add_deliverable(
            "requirements", DeliverableCategory.BACKEND,
            "Dependencies", "requirements.*"
        )
        self._add_deliverable(
            "tests", DeliverableCategory.TESTING,
            "Test files", "tests/"
        )
        self._add_deliverable(
            "README.md", DeliverableCategory.DOCUMENTATION,
            "Documentation", "README.md"
        )
    
    def _add_deliverable(self, name: str, category: DeliverableCategory, 
                        description: str, expected_path: str) -> None:
        """Add an expected deliverable"""
        deliverable = Deliverable(
            name=name,
            category=category,
            description=description,
            expected_path=expected_path
        )
        self.expected_deliverables[name] = deliverable
    
    def _build_dependency_graph(self) -> None:
        """Build dependency relationships between deliverables"""
        # Frontend depends on API
        for name, deliverable in self.expected_deliverables.items():
            if deliverable.category == DeliverableCategory.FRONTEND:
                for api_name, api_del in self.expected_deliverables.items():
                    if api_del.category == DeliverableCategory.API:
                        deliverable.dependencies.append(api_name)
                        api_del.dependent_on_by.append(name)
                        self.deliverable_graph[name].add(api_name)
        
        # Tests depend on implementation
        for name, deliverable in self.expected_deliverables.items():
            if deliverable.category == DeliverableCategory.TESTING:
                # Find related implementation files
                if "api" in name.lower():
                    for impl_name, impl_del in self.expected_deliverables.items():
                        if impl_del.category in [DeliverableCategory.API, DeliverableCategory.BACKEND]:
                            deliverable.dependencies.append(impl_name)
                            impl_del.dependent_on_by.append(name)
                            self.deliverable_graph[name].add(impl_name)
        
        # Infrastructure depends on all code
        for name, deliverable in self.expected_deliverables.items():
            if deliverable.category == DeliverableCategory.INFRASTRUCTURE:
                for code_name, code_del in self.expected_deliverables.items():
                    if code_del.category in [DeliverableCategory.BACKEND, 
                                            DeliverableCategory.FRONTEND,
                                            DeliverableCategory.API]:
                        deliverable.dependencies.append(code_name)
                        code_del.dependent_on_by.append(name)
                        self.deliverable_graph[name].add(code_name)
    
    def scan_actual_deliverables(self, scan_path: Optional[str] = None) -> None:
        """Scan project directory for actual deliverables"""
        scan_dir = Path(scan_path) if scan_path else self.project_path
        
        for root, dirs, files in os.walk(scan_dir):
            # Skip hidden directories and common non-deliverable directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if not file.startswith('.'):
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(scan_dir)
                    
                    # Match against expected deliverables
                    matched = False
                    for expected_name, expected_del in self.expected_deliverables.items():
                        if self._path_matches(str(relative_path), expected_del.expected_path):
                            # Create actual deliverable
                            actual = Deliverable(
                                name=expected_name,
                                category=expected_del.category,
                                description=expected_del.description,
                                expected_path=expected_del.expected_path,
                                actual_path=str(file_path),
                                status=DeliverableStatus.COMPLETE,
                                size_bytes=file_path.stat().st_size,
                                created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                                modified_at=datetime.fromtimestamp(file_path.stat().st_mtime)
                            )
                            
                            # Validate the deliverable
                            actual.validate()
                            
                            self.actual_deliverables[expected_name] = actual
                            matched = True
                            break
                    
                    # Track unexpected deliverables
                    if not matched:
                        category = self._categorize_file(str(relative_path))
                        unexpected = Deliverable(
                            name=file,
                            category=category,
                            description="Unexpected deliverable",
                            expected_path="",
                            actual_path=str(file_path),
                            status=DeliverableStatus.COMPLETE,
                            size_bytes=file_path.stat().st_size
                        )
                        self.actual_deliverables[f"unexpected_{file}"] = unexpected
    
    def _path_matches(self, actual_path: str, expected_pattern: str) -> bool:
        """Check if actual path matches expected pattern"""
        # Normalize paths
        actual = actual_path.replace('\\', '/').lower()
        expected = expected_pattern.replace('\\', '/').lower()
        
        # Handle directory patterns
        if expected.endswith('/'):
            return actual.startswith(expected)
        
        # Handle wildcard patterns
        if '*' in expected:
            pattern = expected.replace('*', '.*')
            return bool(re.match(pattern, actual))
        
        # Handle exact matches
        return expected in actual or actual.endswith(expected)
    
    def _categorize_file(self, file_path: str) -> DeliverableCategory:
        """Categorize a file based on its path and extension"""
        path_lower = file_path.lower()
        
        if any(term in path_lower for term in ['test', 'spec']):
            return DeliverableCategory.TESTING
        elif any(term in path_lower for term in ['frontend', 'src/components', 'src/pages', '.jsx', '.tsx']):
            return DeliverableCategory.FRONTEND
        elif any(term in path_lower for term in ['backend', 'server', 'api', 'routes', 'controllers']):
            return DeliverableCategory.BACKEND
        elif any(term in path_lower for term in ['model', 'schema', 'migration', '.sql']):
            return DeliverableCategory.DATABASE
        elif any(term in path_lower for term in ['docker', 'k8s', 'kubernetes', '.yml', '.yaml']):
            return DeliverableCategory.INFRASTRUCTURE
        elif any(term in path_lower for term in ['.md', '.rst', 'readme', 'docs']):
            return DeliverableCategory.DOCUMENTATION
        elif any(term in path_lower for term in ['.env', 'config', 'settings']):
            return DeliverableCategory.CONFIGURATION
        elif any(term in path_lower for term in ['auth', 'security', 'permission']):
            return DeliverableCategory.SECURITY
        else:
            return DeliverableCategory.BACKEND
    
    def compare_deliverables(self) -> Dict:
        """Compare expected vs actual deliverables"""
        comparison = {
            "expected_count": len(self.expected_deliverables),
            "actual_count": len([d for d in self.actual_deliverables.values() 
                               if not d.name.startswith("unexpected_")]),
            "missing": [],
            "unexpected": [],
            "validated": [],
            "failed": [],
            "completion_rate": 0.0,
            "quality_score": 0.0,
            "by_category": {}
        }
        
        # Find missing deliverables
        for expected_name, expected_del in self.expected_deliverables.items():
            if expected_name not in self.actual_deliverables:
                comparison["missing"].append({
                    "name": expected_name,
                    "category": expected_del.category.value,
                    "description": expected_del.description,
                    "expected_path": expected_del.expected_path,
                    "impact": self._assess_impact(expected_del)
                })
        
        # Find unexpected deliverables
        for actual_name, actual_del in self.actual_deliverables.items():
            if actual_name.startswith("unexpected_"):
                comparison["unexpected"].append({
                    "name": actual_del.name,
                    "category": actual_del.category.value,
                    "path": actual_del.actual_path,
                    "size": actual_del.size_bytes
                })
        
        # Categorize validated and failed deliverables
        for actual_name, actual_del in self.actual_deliverables.items():
            if not actual_name.startswith("unexpected_"):
                if actual_del.status == DeliverableStatus.VALIDATED:
                    comparison["validated"].append(actual_name)
                elif actual_del.validation_errors:
                    comparison["failed"].append({
                        "name": actual_name,
                        "errors": actual_del.validation_errors,
                        "quality_score": actual_del.quality_score
                    })
        
        # Calculate completion rate
        if comparison["expected_count"] > 0:
            comparison["completion_rate"] = (
                (comparison["expected_count"] - len(comparison["missing"])) / 
                comparison["expected_count"] * 100
            )
        
        # Calculate quality score
        total_quality = sum(d.quality_score for d in self.actual_deliverables.values() 
                          if not d.name.startswith("unexpected_"))
        actual_count = comparison["actual_count"]
        comparison["quality_score"] = total_quality / actual_count if actual_count > 0 else 0
        
        # Group by category
        for category in DeliverableCategory:
            expected = sum(1 for d in self.expected_deliverables.values() 
                         if d.category == category)
            actual = sum(1 for d in self.actual_deliverables.values() 
                       if d.category == category and not d.name.startswith("unexpected_"))
            missing = sum(1 for m in comparison["missing"] 
                        if m["category"] == category.value)
            
            comparison["by_category"][category.value] = {
                "expected": expected,
                "actual": actual,
                "missing": missing,
                "completion_rate": (actual / expected * 100) if expected > 0 else 100
            }
        
        self.category_stats = comparison["by_category"]
        
        return comparison
    
    def _assess_impact(self, deliverable: Deliverable) -> str:
        """Assess the impact of a missing deliverable"""
        # Critical categories
        if deliverable.category in [DeliverableCategory.BACKEND, 
                                   DeliverableCategory.DATABASE,
                                   DeliverableCategory.SECURITY]:
            return "critical"
        
        # High impact if many depend on it
        if len(deliverable.dependent_on_by) > 2:
            return "high"
        
        # Medium impact for most deliverables
        if deliverable.category in [DeliverableCategory.FRONTEND,
                                   DeliverableCategory.API,
                                   DeliverableCategory.TESTING]:
            return "medium"
        
        # Low impact for documentation and configuration
        return "low"
    
    def generate_completion_timeline(self) -> List[Dict]:
        """Generate timeline for completing missing deliverables"""
        timeline = []
        
        # Sort missing deliverables by priority
        missing_sorted = []
        for expected_name, expected_del in self.expected_deliverables.items():
            if expected_name not in self.actual_deliverables:
                priority = self._calculate_priority(expected_del)
                missing_sorted.append((priority, expected_name, expected_del))
        
        missing_sorted.sort(key=lambda x: x[0])
        
        # Generate timeline
        current_time = datetime.now()
        accumulated_hours = 0
        
        for priority, name, deliverable in missing_sorted:
            estimated_hours = self._estimate_hours(deliverable)
            accumulated_hours += estimated_hours
            
            timeline.append({
                "deliverable": name,
                "category": deliverable.category.value,
                "description": deliverable.description,
                "estimated_hours": estimated_hours,
                "accumulated_hours": accumulated_hours,
                "target_date": (current_time + timedelta(hours=accumulated_hours)).isoformat(),
                "suggested_agent": self._suggest_agent(deliverable),
                "dependencies": deliverable.dependencies
            })
        
        return timeline
    
    def _calculate_priority(self, deliverable: Deliverable) -> int:
        """Calculate priority score for a deliverable (lower is higher priority)"""
        priority = 100
        
        # Adjust based on category
        category_priorities = {
            DeliverableCategory.SECURITY: 1,
            DeliverableCategory.DATABASE: 2,
            DeliverableCategory.BACKEND: 3,
            DeliverableCategory.API: 4,
            DeliverableCategory.FRONTEND: 5,
            DeliverableCategory.TESTING: 6,
            DeliverableCategory.INFRASTRUCTURE: 7,
            DeliverableCategory.DOCUMENTATION: 8,
            DeliverableCategory.CONFIGURATION: 9,
            DeliverableCategory.MONITORING: 10
        }
        
        priority = category_priorities.get(deliverable.category, 50)
        
        # Adjust based on dependencies
        priority -= len(deliverable.dependent_on_by) * 5
        
        # Ensure dependencies come first
        if deliverable.dependencies:
            # Check if dependencies are missing
            missing_deps = [d for d in deliverable.dependencies 
                          if d not in self.actual_deliverables]
            if missing_deps:
                priority += 50  # Push down if dependencies are missing
        
        return priority
    
    def _estimate_hours(self, deliverable: Deliverable) -> float:
        """Estimate hours needed to complete a deliverable"""
        # Base estimates by category
        category_hours = {
            DeliverableCategory.BACKEND: 3.0,
            DeliverableCategory.FRONTEND: 4.0,
            DeliverableCategory.DATABASE: 2.0,
            DeliverableCategory.API: 2.5,
            DeliverableCategory.TESTING: 2.0,
            DeliverableCategory.DOCUMENTATION: 1.0,
            DeliverableCategory.INFRASTRUCTURE: 2.5,
            DeliverableCategory.CONFIGURATION: 0.5,
            DeliverableCategory.SECURITY: 3.5,
            DeliverableCategory.MONITORING: 2.0,
            DeliverableCategory.DEPLOYMENT: 3.0
        }
        
        return category_hours.get(deliverable.category, 2.0)
    
    def _suggest_agent(self, deliverable: Deliverable) -> str:
        """Suggest the best agent for creating a deliverable"""
        agent_mapping = {
            DeliverableCategory.BACKEND: "rapid-builder",
            DeliverableCategory.FRONTEND: "frontend-specialist",
            DeliverableCategory.DATABASE: "database-expert",
            DeliverableCategory.API: "api-integrator",
            DeliverableCategory.TESTING: "quality-guardian",
            DeliverableCategory.DOCUMENTATION: "documentation-writer",
            DeliverableCategory.INFRASTRUCTURE: "devops-engineer",
            DeliverableCategory.CONFIGURATION: "devops-engineer",
            DeliverableCategory.SECURITY: "quality-guardian",
            DeliverableCategory.MONITORING: "performance-optimizer",
            DeliverableCategory.DEPLOYMENT: "devops-engineer"
        }
        
        return agent_mapping.get(deliverable.category, "rapid-builder")
    
    def export_report(self, output_file: str) -> None:
        """Export deliverables report to file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "expected_deliverables": {
                name: {
                    "category": d.category.value,
                    "description": d.description,
                    "expected_path": d.expected_path,
                    "dependencies": d.dependencies
                }
                for name, d in self.expected_deliverables.items()
            },
            "actual_deliverables": {
                name: {
                    "category": d.category.value,
                    "actual_path": d.actual_path,
                    "status": d.status.value,
                    "quality_score": d.quality_score,
                    "validation_errors": d.validation_errors,
                    "size_bytes": d.size_bytes
                }
                for name, d in self.actual_deliverables.items()
            },
            "comparison": self.compare_deliverables(),
            "timeline": self.generate_completion_timeline()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)


def main():
    """Main function for testing"""
    tracker = DeliverablesTracker()
    
    # Define expected deliverables for a web app
    tracker.define_expected_deliverables(
        "web_app",
        ["User authentication", "API endpoints", "React frontend", "PostgreSQL database"]
    )
    
    # Scan for actual deliverables
    tracker.scan_actual_deliverables()
    
    # Compare and generate report
    comparison = tracker.compare_deliverables()
    print("Deliverables Comparison:")
    print(json.dumps(comparison, indent=2))
    
    # Generate timeline
    timeline = tracker.generate_completion_timeline()
    print("\nCompletion Timeline:")
    for item in timeline[:5]:  # Show first 5 items
        print(f"  {item['deliverable']}: {item['estimated_hours']}h - {item['suggested_agent']}")
    
    # Export report
    tracker.export_report("deliverables_report.json")
    print("\nReport exported to deliverables_report.json")


if __name__ == "__main__":
    main()