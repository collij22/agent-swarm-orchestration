#!/usr/bin/env python3
"""
Quality Validation Tools for Enhanced Quality Guardian
Provides comprehensive validation, testing, and completion metrics
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import time
import re

@dataclass
class RequirementStatus:
    """Track status of a single requirement"""
    requirement: str
    category: str
    status: str  # 'completed', 'partial', 'missing', 'failed'
    evidence: List[str]
    issues: List[str]
    
    def to_dict(self):
        return {
            "requirement": self.requirement,
            "category": self.category,
            "status": self.status,
            "evidence": self.evidence,
            "issues": self.issues
        }

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    total_requirements: int
    completed: int
    partial: int
    missing: int
    failed: int
    completion_percentage: float
    requirement_details: List[RequirementStatus]
    missing_components: List[str]
    recommendations: List[str]
    critical_issues: List[str]
    
    def to_dict(self):
        return {
            "total_requirements": self.total_requirements,
            "completed": self.completed,
            "partial": self.partial,
            "missing": self.missing,
            "failed": self.failed,
            "completion_percentage": self.completion_percentage,
            "requirement_details": [r.to_dict() for r in self.requirement_details],
            "missing_components": self.missing_components,
            "recommendations": self.recommendations,
            "critical_issues": self.critical_issues
        }
    
    def get_summary(self) -> str:
        """Get a formatted summary of the validation report"""
        summary = f"""
## Validation Report Summary

**Overall Completion: {self.completion_percentage:.1f}%**

### Requirement Status:
- ✅ Completed: {self.completed}/{self.total_requirements}
- ⚠️ Partial: {self.partial}/{self.total_requirements}
- ❌ Missing: {self.missing}/{self.total_requirements}
- 🔴 Failed: {self.failed}/{self.total_requirements}

### Critical Issues:
{chr(10).join(f'- {issue}' for issue in self.critical_issues) if self.critical_issues else '- None'}

### Missing Components:
{chr(10).join(f'- {comp}' for comp in self.missing_components) if self.missing_components else '- None'}

### Recommendations:
{chr(10).join(f'- {rec}' for rec in self.recommendations) if self.recommendations else '- None'}
"""
        return summary

class RequirementValidator:
    """Validates project requirements against deliverables"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
    
    async def validate_requirements(self, requirements: Dict, context: Any = None) -> ValidationReport:
        """Validate all requirements and generate report"""
        requirement_statuses = []
        
        # Extract different types of requirements
        features = requirements.get("features", [])
        tech_overrides = requirements.get("tech_overrides", {})
        data_model = requirements.get("data_model", {})
        api_endpoints = requirements.get("api_endpoints", {})
        testing_requirements = requirements.get("testing_requirements", [])
        documentation_requirements = requirements.get("documentation_requirements", [])
        
        # Validate features
        for feature in features:
            status = await self._validate_feature(feature, context)
            requirement_statuses.append(status)
        
        # Validate API endpoints
        for category, endpoints in api_endpoints.items():
            for endpoint in endpoints:
                status = await self._validate_endpoint(endpoint, category)
                requirement_statuses.append(status)
        
        # Validate testing
        for test_req in testing_requirements:
            status = await self._validate_testing(test_req)
            requirement_statuses.append(status)
        
        # Validate documentation
        for doc_req in documentation_requirements:
            status = await self._validate_documentation(doc_req)
            requirement_statuses.append(status)
        
        # Validate Docker if specified
        if "docker" in str(tech_overrides).lower() or "containerization" in str(features).lower():
            status = await self._validate_docker()
            requirement_statuses.append(status)
        
        # Calculate metrics
        total = len(requirement_statuses)
        completed = sum(1 for s in requirement_statuses if s.status == "completed")
        partial = sum(1 for s in requirement_statuses if s.status == "partial")
        missing = sum(1 for s in requirement_statuses if s.status == "missing")
        failed = sum(1 for s in requirement_statuses if s.status == "failed")
        
        completion_percentage = (completed / total * 100) if total > 0 else 0
        
        # Identify missing components
        missing_components = []
        if not (self.project_path / "frontend").exists() and "frontend" in str(requirements).lower():
            missing_components.append("Frontend implementation")
        if not (self.project_path / "tests").exists() and testing_requirements:
            missing_components.append("Test suite")
        if not (self.project_path / "Dockerfile").exists() and "docker" in str(requirements).lower():
            missing_components.append("Docker configuration")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(requirement_statuses)
        
        # Identify critical issues
        critical_issues = []
        for status in requirement_statuses:
            if status.status == "failed" and "authentication" in status.requirement.lower():
                critical_issues.append(f"Authentication not implemented: {status.requirement}")
            if status.status == "missing" and "security" in status.requirement.lower():
                critical_issues.append(f"Security requirement missing: {status.requirement}")
        
        return ValidationReport(
            total_requirements=total,
            completed=completed,
            partial=partial,
            missing=missing,
            failed=failed,
            completion_percentage=completion_percentage,
            requirement_details=requirement_statuses,
            missing_components=missing_components,
            recommendations=recommendations,
            critical_issues=critical_issues
        )
    
    async def _validate_feature(self, feature: str, context: Any = None) -> RequirementStatus:
        """Validate a specific feature requirement"""
        feature_lower = feature.lower()
        evidence = []
        issues = []
        
        # Check for common feature patterns
        if "api" in feature_lower or "endpoint" in feature_lower:
            # Check for API implementation
            api_files = list(self.project_path.glob("**/routes.py")) + \
                       list(self.project_path.glob("**/main.py")) + \
                       list(self.project_path.glob("**/app.py"))
            if api_files:
                evidence.append(f"API files found: {', '.join(str(f) for f in api_files[:3])}")
            else:
                issues.append("No API implementation files found")
        
        if "database" in feature_lower or "storage" in feature_lower:
            # Check for database files
            db_files = list(self.project_path.glob("**/database.py")) + \
                      list(self.project_path.glob("**/models.py")) + \
                      list(self.project_path.glob("**/schema.sql"))
            if db_files:
                evidence.append(f"Database files found: {', '.join(str(f) for f in db_files[:3])}")
            else:
                issues.append("No database implementation found")
        
        if "authentication" in feature_lower or "jwt" in feature_lower:
            # Check for auth implementation
            auth_files = list(self.project_path.glob("**/auth*.py"))
            if auth_files:
                evidence.append(f"Auth files found: {', '.join(str(f) for f in auth_files[:3])}")
            else:
                issues.append("No authentication implementation found")
        
        if "frontend" in feature_lower or "react" in feature_lower:
            # Check for frontend
            frontend_path = self.project_path / "frontend"
            if frontend_path.exists():
                package_json = frontend_path / "package.json"
                if package_json.exists():
                    evidence.append("Frontend with package.json found")
                else:
                    issues.append("Frontend exists but no package.json")
            else:
                issues.append("No frontend directory found")
        
        # Check context for created files if available
        if context and hasattr(context, 'created_files'):
            relevant_files = [f for f in context.get_all_files() if any(
                keyword in f.lower() for keyword in feature_lower.split()
            )]
            if relevant_files:
                evidence.append(f"Context files: {', '.join(relevant_files[:3])}")
        
        # Determine status
        if evidence and not issues:
            status = "completed"
        elif evidence and issues:
            status = "partial"
        elif issues and not evidence:
            status = "missing"
        else:
            status = "partial"  # Default for uncertain cases
        
        return RequirementStatus(
            requirement=feature,
            category="feature",
            status=status,
            evidence=evidence,
            issues=issues
        )
    
    async def _validate_endpoint(self, endpoint: str, category: str) -> RequirementStatus:
        """Validate an API endpoint exists"""
        evidence = []
        issues = []
        
        # Extract endpoint path
        endpoint_path = endpoint.split()[-1] if endpoint else ""
        endpoint_path = endpoint_path.strip("()")
        
        # Search for endpoint in code
        route_patterns = [
            f'"{endpoint_path}"',
            f"'{endpoint_path}'",
            f'@app.route("{endpoint_path}"',
            f'@router.{category.lower()}("{endpoint_path}"',
            f'@app.{category.lower()}("{endpoint_path}"'
        ]
        
        found = False
        for pattern in route_patterns:
            files = list(self.project_path.glob("**/*.py"))
            for file in files:
                try:
                    content = file.read_text()
                    if pattern in content or endpoint_path.replace("/", "") in content:
                        evidence.append(f"Endpoint found in {file.name}")
                        found = True
                        break
                except:
                    pass
            if found:
                break
        
        if not found:
            issues.append(f"Endpoint {endpoint_path} not found in code")
        
        # Check if it's a critical endpoint
        if "auth" in endpoint_path.lower() and not found:
            issues.append("Critical authentication endpoint missing")
        
        status = "completed" if found else "missing"
        
        return RequirementStatus(
            requirement=endpoint,
            category=f"api_{category}",
            status=status,
            evidence=evidence,
            issues=issues
        )
    
    async def _validate_testing(self, test_requirement: str) -> RequirementStatus:
        """Validate testing requirements"""
        evidence = []
        issues = []
        
        test_lower = test_requirement.lower()
        
        # Check for test files
        test_files = list(self.project_path.glob("**/test_*.py")) + \
                    list(self.project_path.glob("**/*_test.py")) + \
                    list(self.project_path.glob("**/test*.py"))
        
        if test_files:
            evidence.append(f"Test files found: {len(test_files)} files")
            
            # Check for specific test types
            if "unit" in test_lower:
                unit_tests = [f for f in test_files if "unit" in str(f).lower() or "test_" in f.name]
                if unit_tests:
                    evidence.append(f"Unit tests: {len(unit_tests)} files")
                else:
                    issues.append("No unit tests found")
            
            if "integration" in test_lower:
                integration_tests = [f for f in test_files if "integration" in str(f).lower()]
                if integration_tests:
                    evidence.append(f"Integration tests: {len(integration_tests)} files")
                else:
                    issues.append("No integration tests found")
            
            if "endpoint" in test_lower or "api" in test_lower:
                api_tests = [f for f in test_files if "api" in str(f).lower() or "endpoint" in str(f).lower()]
                if api_tests:
                    evidence.append(f"API tests: {len(api_tests)} files")
                else:
                    issues.append("No API endpoint tests found")
        else:
            issues.append("No test files found in project")
        
        # Check for test configuration
        pytest_ini = self.project_path / "pytest.ini"
        setup_cfg = self.project_path / "setup.cfg"
        if pytest_ini.exists() or setup_cfg.exists():
            evidence.append("Test configuration found")
        
        # Determine status
        if evidence and not issues:
            status = "completed"
        elif evidence and issues:
            status = "partial"
        else:
            status = "missing"
        
        return RequirementStatus(
            requirement=test_requirement,
            category="testing",
            status=status,
            evidence=evidence,
            issues=issues
        )
    
    async def _validate_documentation(self, doc_requirement: str) -> RequirementStatus:
        """Validate documentation requirements"""
        evidence = []
        issues = []
        
        doc_lower = doc_requirement.lower()
        
        # Check for documentation files
        if "readme" in doc_lower:
            readme = self.project_path / "README.md"
            if readme.exists():
                size = readme.stat().st_size
                if size > 100:
                    evidence.append(f"README.md found ({size} bytes)")
                else:
                    issues.append("README.md exists but is too small")
            else:
                issues.append("README.md not found")
        
        if "openapi" in doc_lower or "swagger" in doc_lower:
            # Check for OpenAPI/Swagger spec
            spec_files = list(self.project_path.glob("**/openapi.json")) + \
                        list(self.project_path.glob("**/swagger.json")) + \
                        list(self.project_path.glob("**/openapi.yaml"))
            
            if spec_files:
                evidence.append(f"OpenAPI spec found: {spec_files[0].name}")
            else:
                # Check if FastAPI auto-docs are available
                main_files = list(self.project_path.glob("**/main.py"))
                for f in main_files:
                    try:
                        if "FastAPI" in f.read_text():
                            evidence.append("FastAPI auto-documentation available")
                            break
                    except:
                        pass
                else:
                    issues.append("No OpenAPI/Swagger specification found")
        
        if "api" in doc_lower and "usage" in doc_lower:
            # Check for API usage examples
            docs_dir = self.project_path / "docs"
            if docs_dir.exists():
                api_docs = list(docs_dir.glob("*api*.md"))
                if api_docs:
                    evidence.append(f"API documentation found in docs/")
                else:
                    issues.append("No API usage documentation in docs/")
            else:
                issues.append("No docs directory found")
        
        # Determine status
        if evidence and not issues:
            status = "completed"
        elif evidence and issues:
            status = "partial"
        else:
            status = "missing"
        
        return RequirementStatus(
            requirement=doc_requirement,
            category="documentation",
            status=status,
            evidence=evidence,
            issues=issues
        )
    
    async def _validate_docker(self) -> RequirementStatus:
        """Validate Docker configuration"""
        evidence = []
        issues = []
        
        # Check for Dockerfile
        dockerfile = self.project_path / "Dockerfile"
        if dockerfile.exists():
            evidence.append("Dockerfile found")
            # Basic validation
            try:
                content = dockerfile.read_text()
                if "FROM" in content and "CMD" in content or "ENTRYPOINT" in content:
                    evidence.append("Dockerfile appears valid")
                else:
                    issues.append("Dockerfile missing required commands")
            except:
                issues.append("Cannot read Dockerfile")
        else:
            issues.append("Dockerfile not found")
        
        # Check for docker-compose
        docker_compose = self.project_path / "docker-compose.yml"
        if not docker_compose.exists():
            docker_compose = self.project_path / "docker-compose.yaml"
        
        if docker_compose.exists():
            evidence.append("docker-compose.yml found")
        else:
            issues.append("docker-compose.yml not found")
        
        # Check for .dockerignore
        dockerignore = self.project_path / ".dockerignore"
        if dockerignore.exists():
            evidence.append(".dockerignore found")
        
        # Determine status
        if evidence and not issues:
            status = "completed"
        elif evidence and issues:
            status = "partial"
        else:
            status = "missing"
        
        return RequirementStatus(
            requirement="Docker containerization",
            category="infrastructure",
            status=status,
            evidence=evidence,
            issues=issues
        )
    
    def _generate_recommendations(self, statuses: List[RequirementStatus]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Count issues by category
        category_issues = {}
        for status in statuses:
            if status.status in ["missing", "failed", "partial"]:
                if status.category not in category_issues:
                    category_issues[status.category] = 0
                category_issues[status.category] += 1
        
        # Generate recommendations
        if category_issues.get("feature", 0) > 2:
            recommendations.append("Multiple features incomplete - consider running rapid-builder agent")
        
        if category_issues.get("testing", 0) > 0:
            recommendations.append("Testing gaps detected - run quality-guardian with focus on test creation")
        
        if category_issues.get("documentation", 0) > 0:
            recommendations.append("Documentation incomplete - run documentation-writer agent")
        
        if category_issues.get("infrastructure", 0) > 0:
            recommendations.append("Infrastructure setup incomplete - run devops-engineer agent")
        
        # Check for critical missing pieces
        missing_auth = any(s.status == "missing" and "auth" in s.requirement.lower() for s in statuses)
        if missing_auth:
            recommendations.append("CRITICAL: Authentication not implemented - security risk")
        
        missing_tests = any(s.status == "missing" and s.category == "testing" for s in statuses)
        if missing_tests:
            recommendations.append("WARNING: No tests found - deployment not recommended")
        
        return recommendations

class EndpointTester:
    """Test API endpoints for functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def test_endpoint(self, endpoint: str, method: str = "GET", 
                           data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        """Test a single endpoint"""
        try:
            import aiohttp
            has_aiohttp = True
        except ImportError:
            has_aiohttp = False
            import requests
        
        url = f"{self.base_url}{endpoint}"
        
        if not has_aiohttp:
            # Use requests as fallback
            try:
                if method == "GET":
                    response = requests.get(url, headers=headers)
                elif method == "POST":
                    response = requests.post(url, json=data, headers=headers)
                elif method == "PUT":
                    response = requests.put(url, json=data, headers=headers)
                elif method == "DELETE":
                    response = requests.delete(url, headers=headers)
                else:
                    response = requests.request(method, url, json=data, headers=headers)
                
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "success": 200 <= response.status_code < 300,
                    "response_time": response.elapsed.total_seconds() * 1000,
                    "body": response.text[:500]  # Limit response size
                }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Use aiohttp if available
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(method, url, json=data, headers=headers) as response:
                    return {
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status,
                        "success": 200 <= response.status < 300,
                        "response_time": response.headers.get("X-Response-Time", "N/A"),
                        "body": await response.text()
                    }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": 0,
                    "success": False,
                    "error": str(e)
                }
    
    async def test_all_endpoints(self, endpoints: List[Tuple[str, str]]) -> List[Dict]:
        """Test multiple endpoints"""
        results = []
        for endpoint, method in endpoints:
            result = await self.test_endpoint(endpoint, method)
            results.append(result)
        return results

class DockerValidator:
    """Validate Docker configuration and build"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
    
    async def validate_dockerfile(self) -> Dict:
        """Validate Dockerfile syntax and best practices"""
        dockerfile = self.project_path / "Dockerfile"
        
        if not dockerfile.exists():
            return {"valid": False, "error": "Dockerfile not found"}
        
        try:
            content = dockerfile.read_text()
            issues = []
            
            # Check for required commands
            if "FROM" not in content:
                issues.append("Missing FROM command")
            if "CMD" not in content and "ENTRYPOINT" not in content:
                issues.append("Missing CMD or ENTRYPOINT")
            
            # Check for best practices
            if "COPY . ." in content or "ADD . ." in content:
                issues.append("Copying entire directory - consider being more specific")
            if "RUN apt-get update && apt-get install" not in content.replace("\n", " "):
                if "RUN apt-get" in content:
                    issues.append("apt-get update and install should be in same RUN command")
            
            # Check for WORKDIR
            if "WORKDIR" not in content:
                issues.append("No WORKDIR set")
            
            # Check for USER (security)
            if "USER" not in content:
                issues.append("Running as root - consider adding USER command")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "lines": len(content.splitlines())
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def test_docker_build(self) -> Dict:
        """Test if Docker image can be built"""
        try:
            # Run docker build
            result = subprocess.run(
                ["docker", "build", "-t", "test-build", "."],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "build_success": result.returncode == 0,
                "stdout": result.stdout[-500:] if result.stdout else "",
                "stderr": result.stderr[-500:] if result.stderr else "",
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"build_success": False, "error": "Build timeout after 60 seconds"}
        except Exception as e:
            return {"build_success": False, "error": str(e)}

# Tool functions for agent use

async def validate_requirements_tool(requirements_file: str = None, requirements_dict: Dict = None,
                                    project_path: str = ".", reasoning: str = None,
                                    context: Any = None) -> str:
    """Validate all project requirements and generate completion report"""
    validator = RequirementValidator(project_path)
    
    # Load requirements
    requirements = requirements_dict
    if not requirements and requirements_file:
        try:
            with open(requirements_file, 'r') as f:
                import yaml
                requirements = yaml.safe_load(f)
        except:
            return "Error: Could not load requirements file"
    
    if not requirements:
        return "Error: No requirements provided"
    
    # Run validation
    report = await validator.validate_requirements(requirements, context)
    
    # Save report
    report_path = Path(project_path) / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    return f"Validation complete: {report.completion_percentage:.1f}% requirements met\n{report.get_summary()}"

async def test_endpoints_tool(endpoints: List[str], base_url: str = "http://localhost:8000",
                             reasoning: str = None) -> str:
    """Test API endpoints for availability and basic functionality"""
    tester = EndpointTester(base_url)
    
    # Parse endpoints into (path, method) tuples
    endpoint_tuples = []
    for endpoint in endpoints:
        parts = endpoint.split()
        if len(parts) >= 2:
            method = parts[0]
            path = parts[-1]
        else:
            method = "GET"
            path = endpoint
        endpoint_tuples.append((path, method))
    
    # Test endpoints
    results = await tester.test_all_endpoints(endpoint_tuples)
    
    # Format results
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    output = f"Endpoint Testing: {success_count}/{total_count} successful\n\n"
    for result in results:
        status = "✅" if result["success"] else "❌"
        output += f"{status} {result['method']} {result['endpoint']}: {result.get('status_code', 'Error')}\n"
        if not result["success"] and "error" in result:
            output += f"   Error: {result['error']}\n"
    
    return output

async def validate_docker_tool(project_path: str = ".", test_build: bool = False,
                              reasoning: str = None) -> str:
    """Validate Docker configuration and optionally test build"""
    validator = DockerValidator(project_path)
    
    # Validate Dockerfile
    dockerfile_result = await validator.validate_dockerfile()
    
    output = "Docker Validation:\n"
    if dockerfile_result["valid"]:
        output += "✅ Dockerfile valid\n"
    else:
        output += "❌ Dockerfile issues:\n"
        if "error" in dockerfile_result:
            output += f"   {dockerfile_result['error']}\n"
        else:
            for issue in dockerfile_result.get("issues", []):
                output += f"   - {issue}\n"
    
    # Test build if requested
    if test_build and dockerfile_result.get("valid", False):
        output += "\nTesting Docker build...\n"
        build_result = await validator.test_docker_build()
        
        if build_result["build_success"]:
            output += "✅ Docker build successful\n"
        else:
            output += "❌ Docker build failed\n"
            if "error" in build_result:
                output += f"   Error: {build_result['error']}\n"
            elif "stderr" in build_result:
                output += f"   stderr: {build_result['stderr'][-200:]}\n"
    
    return output

async def generate_completion_report_tool(context: Any = None, project_path: str = ".",
                                         reasoning: str = None) -> str:
    """Generate detailed completion metrics report"""
    if not context:
        return "Error: Context required for completion report"
    
    report = []
    report.append("## Project Completion Report\n")
    
    # Files created
    if hasattr(context, 'created_files'):
        total_files = len(context.get_all_files())
        report.append(f"### Files Created: {total_files}")
        
        # Group by type
        files_by_type = {}
        for agent, files in context.created_files.items():
            for file_info in files:
                file_type = file_info.get("type", "unknown")
                if file_type not in files_by_type:
                    files_by_type[file_type] = []
                files_by_type[file_type].append(file_info["path"])
        
        for ftype, files in files_by_type.items():
            report.append(f"- {ftype}: {len(files)} files")
    
    # Tasks completed
    if hasattr(context, 'completed_tasks'):
        report.append(f"\n### Tasks Completed: {len(context.completed_tasks)}")
        for task in context.completed_tasks[-10:]:
            report.append(f"- {task}")
    
    # Incomplete tasks
    if hasattr(context, 'incomplete_tasks'):
        report.append(f"\n### Incomplete Tasks: {len(context.incomplete_tasks)}")
        for task in context.incomplete_tasks:
            report.append(f"- {task['agent']}: {task['task']} ({task['reason']})")
    
    # Verification required
    if hasattr(context, 'verification_required'):
        report.append(f"\n### Critical Files Requiring Verification: {len(context.verification_required)}")
        for file in context.verification_required[:10]:
            report.append(f"- {file}")
    
    # Decisions made
    if hasattr(context, 'decisions'):
        report.append(f"\n### Architectural Decisions: {len(context.decisions)}")
        for decision in context.decisions[-5:]:
            report.append(f"- {decision.get('decision', 'Unknown')}")
    
    # Save report
    report_path = Path(project_path) / "completion_report.md"
    report_content = "\n".join(report)
    report_path.write_text(report_content)
    
    return f"Completion report generated: {report_path}\n\n{report_content}"