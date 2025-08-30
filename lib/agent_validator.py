#!/usr/bin/env python3
"""
Agent Validator Module
Validates agent outputs to ensure they meet expected criteria
"""

import json
from typing import Dict, List, Optional, Callable, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class ValidationResult(Enum):
    """Result of validation check"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationCheck:
    """Individual validation check"""
    name: str
    description: str
    validator: Callable
    required: bool = True
    retry_on_fail: bool = False
    
    def execute(self, context: Any) -> Tuple[ValidationResult, str]:
        """Execute the validation check"""
        try:
            result = self.validator(context)
            if isinstance(result, bool):
                return (ValidationResult.PASSED if result else ValidationResult.FAILED, "")
            elif isinstance(result, tuple):
                return result
            else:
                return (ValidationResult.PASSED, str(result))
        except Exception as e:
            return (ValidationResult.FAILED, f"Validation error: {str(e)}")


class AgentValidator:
    """
    Validates agent outputs against expected criteria
    """
    
    def __init__(self):
        """Initialize validator with standard checks"""
        self.validation_rules: Dict[str, List[ValidationCheck]] = {}
        self._setup_standard_validations()
    
    def _setup_standard_validations(self):
        """Setup standard validation rules for each agent"""
        
        # Frontend specialist validations
        self.validation_rules["frontend-specialist"] = [
            ValidationCheck(
                name="minimum_files",
                description="Should create at least 5 React components",
                validator=lambda ctx: self._check_minimum_files(ctx, "frontend-specialist", 5)
            ),
            ValidationCheck(
                name="package_json",
                description="Should create package.json",
                validator=lambda ctx: self._check_file_exists(ctx, "frontend/package.json")
            ),
            ValidationCheck(
                name="app_component",
                description="Should create App.tsx or App.jsx",
                validator=lambda ctx: self._check_file_pattern(ctx, "**/App.*")
            ),
            ValidationCheck(
                name="api_client",
                description="Should create API client",
                validator=lambda ctx: self._check_file_pattern(ctx, "**/api/client.*")
            ),
            ValidationCheck(
                name="auth_components",
                description="Should create authentication components",
                validator=lambda ctx: self._check_file_pattern(ctx, "**/auth/*")
            )
        ]
        
        # AI specialist validations
        self.validation_rules["ai-specialist"] = [
            ValidationCheck(
                name="ai_service",
                description="Should create AI service file",
                validator=lambda ctx: self._check_file_exists(ctx, "backend/services/ai_service.py")
            ),
            ValidationCheck(
                name="ai_content_size",
                description="AI service should be substantial (>100 bytes)",
                validator=lambda ctx: self._check_file_size(ctx, "backend/services/ai_service.py", 100)
            ),
            ValidationCheck(
                name="ai_implementation",
                description="AI service should have actual implementation",
                validator=lambda ctx: self._check_file_content(
                    ctx, 
                    "backend/services/ai_service.py",
                    ["class", "def", "async", "import"]
                )
            )
        ]
        
        # Rapid builder validations
        self.validation_rules["rapid-builder"] = [
            ValidationCheck(
                name="main_file",
                description="Should create main application file",
                validator=lambda ctx: self._check_file_pattern(ctx, "**/main.py")
            ),
            ValidationCheck(
                name="api_routes",
                description="Should create API routes",
                validator=lambda ctx: self._check_file_pattern(ctx, "**/routes/*")
            ),
            ValidationCheck(
                name="models",
                description="Should create data models",
                validator=lambda ctx: self._check_file_pattern(ctx, "**/models/*")
            )
        ]
        
        # Quality guardian validations
        self.validation_rules["quality-guardian"] = [
            ValidationCheck(
                name="test_files",
                description="Should create test files",
                validator=lambda ctx: self._check_file_pattern(ctx, "**/test*.py")
            ),
            ValidationCheck(
                name="test_content",
                description="Tests should have actual test code",
                validator=lambda ctx: self._check_test_content(ctx)
            )
        ]
        
        # DevOps engineer validations
        self.validation_rules["devops-engineer"] = [
            ValidationCheck(
                name="dockerfile",
                description="Should create Dockerfile",
                validator=lambda ctx: self._check_file_exists(ctx, "Dockerfile")
            ),
            ValidationCheck(
                name="docker_compose",
                description="Should create docker-compose.yml",
                validator=lambda ctx: self._check_file_exists(ctx, "docker-compose.yml")
            ),
            ValidationCheck(
                name="ci_config",
                description="Should create CI/CD configuration",
                validator=lambda ctx: self._check_file_pattern(ctx, "**/.github/workflows/*")
            )
        ]
    
    def _check_minimum_files(self, context: Any, agent_name: str, minimum: int) -> bool:
        """Check if agent created minimum number of files"""
        if hasattr(context, 'get_agent_files'):
            files = context.get_agent_files(agent_name)
            return len(files) >= minimum
        return False
    
    def _check_file_exists(self, context: Any, file_path: str) -> bool:
        """Check if specific file exists"""
        if hasattr(context, 'artifacts') and 'project_directory' in context.artifacts:
            project_dir = Path(context.artifacts['project_directory'])
            full_path = project_dir / file_path
            return full_path.exists()
        return False
    
    def _check_file_pattern(self, context: Any, pattern: str) -> bool:
        """Check if files matching pattern exist"""
        if hasattr(context, 'artifacts') and 'project_directory' in context.artifacts:
            project_dir = Path(context.artifacts['project_directory'])
            matches = list(project_dir.glob(pattern))
            return len(matches) > 0
        return False
    
    def _check_file_size(self, context: Any, file_path: str, min_size: int) -> bool:
        """Check if file meets minimum size requirement"""
        if hasattr(context, 'artifacts') and 'project_directory' in context.artifacts:
            project_dir = Path(context.artifacts['project_directory'])
            full_path = project_dir / file_path
            if full_path.exists():
                return full_path.stat().st_size >= min_size
        return False
    
    def _check_file_content(self, context: Any, file_path: str, required_patterns: List[str]) -> bool:
        """Check if file contains required patterns"""
        if hasattr(context, 'artifacts') and 'project_directory' in context.artifacts:
            project_dir = Path(context.artifacts['project_directory'])
            full_path = project_dir / file_path
            if full_path.exists():
                content = full_path.read_text()
                return all(pattern in content for pattern in required_patterns)
        return False
    
    def _check_test_content(self, context: Any) -> bool:
        """Check if test files have actual test content"""
        if hasattr(context, 'artifacts') and 'project_directory' in context.artifacts:
            project_dir = Path(context.artifacts['project_directory'])
            test_files = list(project_dir.glob("**/test*.py"))
            
            if not test_files:
                return False
            
            # Check at least one test file has actual test content
            for test_file in test_files:
                content = test_file.read_text()
                if "def test_" in content or "class Test" in content:
                    return True
        return False
    
    def validate_agent_output(
        self, 
        agent_name: str, 
        context: Any,
        strict: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate agent output against rules
        
        Args:
            agent_name: Name of the agent to validate
            context: Agent context with outputs
            strict: If True, all checks must pass
            
        Returns:
            Tuple of (success, validation_report)
        """
        
        if agent_name not in self.validation_rules:
            return True, {"message": f"No validation rules for {agent_name}"}
        
        results = {}
        passed_count = 0
        failed_count = 0
        warning_count = 0
        
        for check in self.validation_rules[agent_name]:
            result, message = check.execute(context)
            
            results[check.name] = {
                "description": check.description,
                "result": result.value,
                "message": message,
                "required": check.required
            }
            
            if result == ValidationResult.PASSED:
                passed_count += 1
            elif result == ValidationResult.FAILED:
                if check.required:
                    failed_count += 1
                else:
                    warning_count += 1
            elif result == ValidationResult.WARNING:
                warning_count += 1
        
        # Determine overall success
        if strict:
            success = failed_count == 0
        else:
            # At least 50% of checks should pass
            total_checks = len(self.validation_rules[agent_name])
            success = passed_count >= (total_checks * 0.5)
        
        report = {
            "agent": agent_name,
            "success": success,
            "summary": {
                "total_checks": len(self.validation_rules[agent_name]),
                "passed": passed_count,
                "failed": failed_count,
                "warnings": warning_count,
                "pass_rate": (passed_count / len(self.validation_rules[agent_name])) * 100
            },
            "checks": results
        }
        
        return success, report
    
    def add_custom_validation(
        self, 
        agent_name: str, 
        check: ValidationCheck
    ):
        """Add custom validation check for an agent"""
        if agent_name not in self.validation_rules:
            self.validation_rules[agent_name] = []
        self.validation_rules[agent_name].append(check)
    
    def get_retry_suggestions(self, agent_name: str, report: Dict) -> List[str]:
        """Get suggestions for retrying failed agent"""
        suggestions = []
        
        if agent_name == "frontend-specialist":
            if "package_json" in report["checks"] and report["checks"]["package_json"]["result"] == "failed":
                suggestions.append("Ensure React project initialization with 'npm create vite@latest'")
            if "auth_components" in report["checks"] and report["checks"]["auth_components"]["result"] == "failed":
                suggestions.append("Create authentication components (Login.tsx, Register.tsx)")
            if "api_client" in report["checks"] and report["checks"]["api_client"]["result"] == "failed":
                suggestions.append("Generate TypeScript API client from backend routes")
        
        elif agent_name == "ai-specialist":
            if "ai_content_size" in report["checks"] and report["checks"]["ai_content_size"]["result"] == "failed":
                suggestions.append("Implement complete AI service with OpenAI/Anthropic integration")
            if "ai_implementation" in report["checks"] and report["checks"]["ai_implementation"]["result"] == "failed":
                suggestions.append("Add actual AI service implementation, not placeholder")
        
        elif agent_name == "rapid-builder":
            if "main_file" in report["checks"] and report["checks"]["main_file"]["result"] == "failed":
                suggestions.append("Create main.py with FastAPI/Flask application")
            if "api_routes" in report["checks"] and report["checks"]["api_routes"]["result"] == "failed":
                suggestions.append("Implement API routes for all resources")
        
        return suggestions


# Example usage
if __name__ == "__main__":
    from lib.agent_runtime import AgentContext
    
    # Create validator
    validator = AgentValidator()
    
    # Create test context
    context = AgentContext(
        project_requirements={"name": "TestProject"},
        completed_tasks=["frontend-specialist"],
        artifacts={"project_directory": "test_project"},
        decisions=[],
        current_phase="frontend"
    )
    
    # Add some fake files for testing
    context.add_created_file("frontend-specialist", "frontend/package.json")
    context.add_created_file("frontend-specialist", "frontend/src/App.tsx")
    context.add_created_file("frontend-specialist", "frontend/src/api/client.ts")
    
    # Validate
    success, report = validator.validate_agent_output("frontend-specialist", context)
    
    print(f"Validation {'PASSED' if success else 'FAILED'}")
    print(json.dumps(report, indent=2))
    
    if not success:
        suggestions = validator.get_retry_suggestions("frontend-specialist", report)
        print("\nSuggestions for retry:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")