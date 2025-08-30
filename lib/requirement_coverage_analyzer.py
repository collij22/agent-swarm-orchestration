#!/usr/bin/env python3
"""
Requirement Coverage Analyzer - Section 9.1 Implementation

Features:
- Structured requirement ID mapping (REQ-XXX, TECH-XXX, FEATURE-XXX)
- Granular completion tracking (0-100%)
- Dependency graph analysis
- Requirement-to-agent mapping
- Traceability matrix generation
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict


class RequirementType(Enum):
    """Types of requirements"""
    FUNCTIONAL = "functional"
    TECHNICAL = "technical"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    INFRASTRUCTURE = "infrastructure"
    DOCUMENTATION = "documentation"


class RequirementPriority(Enum):
    """Priority levels for requirements"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    NICE_TO_HAVE = 5


@dataclass
class Requirement:
    """Represents a single requirement"""
    id: str
    description: str
    type: RequirementType
    priority: RequirementPriority
    acceptance_criteria: List[str]
    dependencies: List[str] = field(default_factory=list)
    assigned_agents: List[str] = field(default_factory=list)
    artifacts_expected: List[str] = field(default_factory=list)
    artifacts_created: List[str] = field(default_factory=list)
    test_cases: List[str] = field(default_factory=list)
    completion_percentage: float = 0.0
    status: str = "not_started"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)
    
    def calculate_completion(self) -> float:
        """Calculate completion percentage based on artifacts and criteria"""
        if not self.acceptance_criteria:
            return 100.0 if self.artifacts_created else 0.0
        
        criteria_met = 0
        total_weight = 0
        
        # Check each acceptance criterion
        for criterion in self.acceptance_criteria:
            weight = self._get_criterion_weight(criterion)
            total_weight += weight
            
            if self._is_criterion_met(criterion):
                criteria_met += weight
        
        # Factor in artifacts
        artifact_completion = 0
        if self.artifacts_expected:
            artifacts_found = sum(1 for a in self.artifacts_expected 
                                if any(created in a or a in created 
                                      for created in self.artifacts_created))
            artifact_completion = (artifacts_found / len(self.artifacts_expected)) * 30
        
        # Calculate weighted completion
        criteria_completion = (criteria_met / total_weight * 70) if total_weight > 0 else 0
        self.completion_percentage = min(100, criteria_completion + artifact_completion)
        
        # Update status based on completion
        if self.completion_percentage == 0:
            self.status = "not_started"
        elif self.completion_percentage < 30:
            self.status = "in_progress"
        elif self.completion_percentage < 100:
            self.status = "partially_complete"
        else:
            self.status = "complete"
        
        return self.completion_percentage
    
    def _get_criterion_weight(self, criterion: str) -> float:
        """Get weight for a specific criterion"""
        criterion_lower = criterion.lower()
        
        # Critical criteria get higher weight
        if any(term in criterion_lower for term in ['must', 'critical', 'required']):
            return 3.0
        elif any(term in criterion_lower for term in ['should', 'important']):
            return 2.0
        else:
            return 1.0
    
    def _is_criterion_met(self, criterion: str) -> bool:
        """Check if a criterion is met based on artifacts and test cases"""
        criterion_lower = criterion.lower()
        
        # Check for specific patterns
        if "api endpoint" in criterion_lower:
            return any("api" in a.lower() or "route" in a.lower() 
                      for a in self.artifacts_created)
        elif "test" in criterion_lower:
            return len(self.test_cases) > 0
        elif "documentation" in criterion_lower:
            return any(".md" in a.lower() for a in self.artifacts_created)
        elif "database" in criterion_lower:
            return any("schema" in a.lower() or ".sql" in a.lower() 
                      for a in self.artifacts_created)
        else:
            # Generic check - criterion is met if we have related artifacts
            return len(self.artifacts_created) > 0


class RequirementCoverageAnalyzer:
    """Analyzes and tracks requirement coverage across sessions"""
    
    def __init__(self):
        """Initialize the analyzer"""
        self.requirements: Dict[str, Requirement] = {}
        self.requirement_graph: Dict[str, Set[str]] = defaultdict(set)
        self.agent_assignments: Dict[str, List[str]] = defaultdict(list)
        self.traceability_matrix: Dict[str, Dict[str, any]] = {}
        
    def parse_requirements(self, requirements_data: Dict) -> None:
        """Parse requirements from project specification"""
        # Parse functional requirements from features
        if "features" in requirements_data:
            for idx, feature in enumerate(requirements_data["features"], 1):
                req_id = f"REQ-{idx:03d}"
                self._create_requirement_from_feature(req_id, feature)
        
        # Parse technical requirements
        if "technical_requirements" in requirements_data:
            for idx, tech_req in enumerate(requirements_data["technical_requirements"], 1):
                req_id = f"TECH-{idx:03d}"
                self._create_technical_requirement(req_id, tech_req)
        
        # Parse constraints as requirements
        if "constraints" in requirements_data:
            for idx, constraint in enumerate(requirements_data["constraints"], 1):
                req_id = f"CONSTRAINT-{idx:03d}"
                self._create_constraint_requirement(req_id, constraint)
        
        # Build dependency graph
        self._build_dependency_graph()
    
    def _create_requirement_from_feature(self, req_id: str, feature: str) -> None:
        """Create a requirement from a feature description"""
        # Determine type and priority from feature description
        feature_lower = feature.lower()
        
        req_type = self._determine_requirement_type(feature_lower)
        priority = self._determine_priority(feature_lower)
        criteria = self._generate_acceptance_criteria(feature, req_type)
        expected_artifacts = self._determine_expected_artifacts(feature, req_type)
        
        requirement = Requirement(
            id=req_id,
            description=feature,
            type=req_type,
            priority=priority,
            acceptance_criteria=criteria,
            artifacts_expected=expected_artifacts
        )
        
        # Assign appropriate agents
        requirement.assigned_agents = self._assign_agents_to_requirement(requirement)
        
        self.requirements[req_id] = requirement
    
    def _determine_requirement_type(self, description: str) -> RequirementType:
        """Determine requirement type from description"""
        if any(term in description for term in ['api', 'endpoint', 'service']):
            return RequirementType.FUNCTIONAL
        elif any(term in description for term in ['performance', 'speed', 'optimize']):
            return RequirementType.PERFORMANCE
        elif any(term in description for term in ['security', 'auth', 'encrypt']):
            return RequirementType.SECURITY
        elif any(term in description for term in ['ui', 'ux', 'interface']):
            return RequirementType.USABILITY
        elif any(term in description for term in ['deploy', 'docker', 'infrastructure']):
            return RequirementType.INFRASTRUCTURE
        elif any(term in description for term in ['document', 'readme', 'guide']):
            return RequirementType.DOCUMENTATION
        else:
            return RequirementType.FUNCTIONAL
    
    def _determine_priority(self, description: str) -> RequirementPriority:
        """Determine priority from description keywords"""
        if any(term in description for term in ['critical', 'must', 'essential', 'core']):
            return RequirementPriority.CRITICAL
        elif any(term in description for term in ['important', 'should', 'main']):
            return RequirementPriority.HIGH
        elif any(term in description for term in ['nice', 'could', 'optional']):
            return RequirementPriority.LOW
        else:
            return RequirementPriority.MEDIUM
    
    def _generate_acceptance_criteria(self, feature: str, req_type: RequirementType) -> List[str]:
        """Generate acceptance criteria based on feature and type"""
        criteria = []
        feature_lower = feature.lower()
        
        if req_type == RequirementType.FUNCTIONAL:
            if "api" in feature_lower:
                criteria.extend([
                    "API endpoints must be implemented and accessible",
                    "Request/response validation must be in place",
                    "API documentation must be generated",
                    "Error handling must return appropriate status codes"
                ])
            if "crud" in feature_lower:
                criteria.extend([
                    "Create operation must validate input and persist data",
                    "Read operation must support filtering and pagination",
                    "Update operation must handle partial updates",
                    "Delete operation must handle cascading deletes"
                ])
        
        elif req_type == RequirementType.SECURITY:
            criteria.extend([
                "Authentication mechanism must be implemented",
                "Authorization checks must be in place",
                "Input validation must prevent injection attacks",
                "Sensitive data must be encrypted"
            ])
        
        elif req_type == RequirementType.PERFORMANCE:
            criteria.extend([
                "Response time must be under 200ms for simple queries",
                "System must handle expected concurrent users",
                "Database queries must be optimized with indexes",
                "Caching strategy must be implemented"
            ])
        
        elif req_type == RequirementType.USABILITY:
            criteria.extend([
                "UI components must be responsive",
                "User actions must provide feedback",
                "Forms must have validation",
                "Navigation must be intuitive"
            ])
        
        # Add generic criteria if none were added
        if not criteria:
            criteria.append(f"{feature} must be fully implemented")
            criteria.append("Tests must be written")
            criteria.append("Documentation must be provided")
        
        return criteria
    
    def _determine_expected_artifacts(self, feature: str, req_type: RequirementType) -> List[str]:
        """Determine expected artifacts for a requirement"""
        artifacts = []
        feature_lower = feature.lower()
        
        if req_type == RequirementType.FUNCTIONAL:
            if "api" in feature_lower:
                artifacts.extend([
                    "routes/*.py",
                    "controllers/*.py",
                    "models/*.py",
                    "tests/test_api_*.py"
                ])
            if "frontend" in feature_lower:
                artifacts.extend([
                    "src/components/*.jsx",
                    "src/pages/*.jsx",
                    "src/hooks/*.js",
                    "src/**/*.test.js"
                ])
        
        elif req_type == RequirementType.INFRASTRUCTURE:
            artifacts.extend([
                "Dockerfile",
                "docker-compose.yml",
                ".github/workflows/*.yml",
                "scripts/deploy.sh"
            ])
        
        elif req_type == RequirementType.DOCUMENTATION:
            artifacts.extend([
                "README.md",
                "docs/*.md",
                "API.md"
            ])
        
        elif req_type == RequirementType.SECURITY:
            artifacts.extend([
                "auth/*.py",
                "middleware/security.py",
                "tests/test_security_*.py"
            ])
        
        return artifacts
    
    def _assign_agents_to_requirement(self, requirement: Requirement) -> List[str]:
        """Assign appropriate agents to a requirement"""
        agents = []
        
        type_to_agents = {
            RequirementType.FUNCTIONAL: ["rapid-builder", "api-integrator"],
            RequirementType.TECHNICAL: ["project-architect", "database-expert"],
            RequirementType.PERFORMANCE: ["performance-optimizer"],
            RequirementType.SECURITY: ["quality-guardian"],
            RequirementType.USABILITY: ["frontend-specialist"],
            RequirementType.INFRASTRUCTURE: ["devops-engineer"],
            RequirementType.DOCUMENTATION: ["documentation-writer"]
        }
        
        # Get primary agents for the type
        agents.extend(type_to_agents.get(requirement.type, ["rapid-builder"]))
        
        # Add quality-guardian for all critical requirements
        if requirement.priority == RequirementPriority.CRITICAL:
            if "quality-guardian" not in agents:
                agents.append("quality-guardian")
        
        # Update agent assignments tracking
        for agent in agents:
            self.agent_assignments[agent].append(requirement.id)
        
        return agents
    
    def _create_technical_requirement(self, req_id: str, tech_req: str) -> None:
        """Create a technical requirement"""
        requirement = Requirement(
            id=req_id,
            description=tech_req,
            type=RequirementType.TECHNICAL,
            priority=RequirementPriority.HIGH,
            acceptance_criteria=[
                f"Technical requirement '{tech_req}' must be satisfied",
                "Implementation must follow best practices",
                "Performance targets must be met"
            ],
            artifacts_expected=["technical_design.md", "implementation/*"]
        )
        
        requirement.assigned_agents = ["project-architect", "rapid-builder"]
        self.requirements[req_id] = requirement
    
    def _create_constraint_requirement(self, req_id: str, constraint: str) -> None:
        """Create a requirement from a constraint"""
        requirement = Requirement(
            id=req_id,
            description=f"Constraint: {constraint}",
            type=RequirementType.TECHNICAL,
            priority=RequirementPriority.CRITICAL,
            acceptance_criteria=[
                f"System must adhere to constraint: {constraint}",
                "Constraint must be validated in tests",
                "Documentation must explain how constraint is satisfied"
            ],
            artifacts_expected=["constraint_validation.py", "docs/constraints.md"]
        )
        
        requirement.assigned_agents = ["project-architect", "quality-guardian"]
        self.requirements[req_id] = requirement
    
    def _build_dependency_graph(self) -> None:
        """Build dependency graph between requirements"""
        # Identify dependencies based on requirement descriptions and types
        for req_id, requirement in self.requirements.items():
            desc_lower = requirement.description.lower()
            
            # Authentication typically depends on user management
            if "authentication" in desc_lower:
                for other_id, other_req in self.requirements.items():
                    if "user" in other_req.description.lower() and other_id != req_id:
                        requirement.dependencies.append(other_id)
                        self.requirement_graph[req_id].add(other_id)
            
            # Frontend depends on backend APIs
            if requirement.type == RequirementType.USABILITY:
                for other_id, other_req in self.requirements.items():
                    if other_req.type == RequirementType.FUNCTIONAL and "api" in other_req.description.lower():
                        requirement.dependencies.append(other_id)
                        self.requirement_graph[req_id].add(other_id)
            
            # Deployment depends on all functional requirements
            if requirement.type == RequirementType.INFRASTRUCTURE:
                for other_id, other_req in self.requirements.items():
                    if other_req.type in [RequirementType.FUNCTIONAL, RequirementType.SECURITY]:
                        requirement.dependencies.append(other_id)
                        self.requirement_graph[req_id].add(other_id)
    
    def update_from_session(self, session_data: Dict) -> None:
        """Update requirement coverage from session execution data"""
        if "events" in session_data:
            for event in session_data["events"]:
                self._process_event_for_requirements(event)
        
        # Recalculate completion for all requirements
        for requirement in self.requirements.values():
            requirement.calculate_completion()
    
    def _process_event_for_requirements(self, event: Dict) -> None:
        """Process a session event to update requirement tracking"""
        # Check for file creation events
        if event.get("type") == "tool_call" and event.get("tool_name") == "write_file":
            file_path = event.get("params", {}).get("file_path", "")
            agent_name = event.get("agent_name", "")
            reasoning = event.get("params", {}).get("reasoning", "")
            
            # Find matching requirements
            for req_id, requirement in self.requirements.items():
                # Check if file matches expected artifacts
                for expected in requirement.artifacts_expected:
                    if self._artifact_matches(file_path, expected):
                        if file_path not in requirement.artifacts_created:
                            requirement.artifacts_created.append(file_path)
                        
                        # Track agent involvement
                        if agent_name and agent_name not in requirement.assigned_agents:
                            requirement.assigned_agents.append(agent_name)
                        
                        # Update timing
                        if not requirement.start_time:
                            requirement.start_time = datetime.fromisoformat(
                                event.get("timestamp", datetime.now().isoformat())
                            )
                
                # Check if requirement is mentioned in reasoning
                if req_id in reasoning or requirement.description.lower() in reasoning.lower():
                    if file_path not in requirement.artifacts_created:
                        requirement.artifacts_created.append(file_path)
        
        # Check for test execution events
        elif event.get("type") == "test_execution":
            test_file = event.get("test_file", "")
            for requirement in self.requirements.values():
                if any(self._artifact_matches(test_file, expected) 
                      for expected in requirement.artifacts_expected):
                    if test_file not in requirement.test_cases:
                        requirement.test_cases.append(test_file)
    
    def _artifact_matches(self, actual: str, expected: str) -> bool:
        """Check if an actual artifact matches an expected pattern"""
        # Convert expected pattern to regex
        pattern = expected.replace("*", ".*").replace("/", r"[/\\]")
        return bool(re.search(pattern, actual, re.IGNORECASE))
    
    def generate_coverage_report(self) -> Dict:
        """Generate comprehensive coverage report"""
        total_requirements = len(self.requirements)
        
        # Calculate statistics
        completed = sum(1 for r in self.requirements.values() if r.status == "complete")
        partial = sum(1 for r in self.requirements.values() if r.status == "partially_complete")
        in_progress = sum(1 for r in self.requirements.values() if r.status == "in_progress")
        not_started = sum(1 for r in self.requirements.values() if r.status == "not_started")
        
        # Calculate overall coverage
        overall_coverage = sum(r.completion_percentage for r in self.requirements.values()) / total_requirements if total_requirements > 0 else 0
        
        # Group by type
        by_type = defaultdict(list)
        for requirement in self.requirements.values():
            by_type[requirement.type.value].append({
                "id": requirement.id,
                "description": requirement.description,
                "completion": requirement.completion_percentage,
                "status": requirement.status
            })
        
        # Group by priority
        by_priority = defaultdict(list)
        for requirement in self.requirements.values():
            by_priority[requirement.priority.value].append({
                "id": requirement.id,
                "description": requirement.description,
                "completion": requirement.completion_percentage
            })
        
        # Find critical incomplete requirements
        critical_incomplete = [
            {
                "id": r.id,
                "description": r.description,
                "completion": r.completion_percentage,
                "blocking_issues": r.notes
            }
            for r in self.requirements.values()
            if r.priority == RequirementPriority.CRITICAL and r.status != "complete"
        ]
        
        return {
            "summary": {
                "total_requirements": total_requirements,
                "completed": completed,
                "partially_complete": partial,
                "in_progress": in_progress,
                "not_started": not_started,
                "overall_coverage": overall_coverage
            },
            "by_type": dict(by_type),
            "by_priority": dict(by_priority),
            "critical_incomplete": critical_incomplete,
            "agent_workload": dict(self.agent_assignments),
            "dependency_graph": {k: list(v) for k, v in self.requirement_graph.items()}
        }
    
    def generate_traceability_matrix(self) -> Dict[str, Dict]:
        """Generate requirement traceability matrix"""
        matrix = {}
        
        for req_id, requirement in self.requirements.items():
            matrix[req_id] = {
                "description": requirement.description,
                "type": requirement.type.value,
                "priority": requirement.priority.value,
                "status": requirement.status,
                "completion": requirement.completion_percentage,
                "agents": requirement.assigned_agents,
                "artifacts": requirement.artifacts_created,
                "tests": requirement.test_cases,
                "dependencies": requirement.dependencies,
                "dependent_on_by": [
                    other_id for other_id, deps in self.requirement_graph.items()
                    if req_id in deps
                ]
            }
        
        self.traceability_matrix = matrix
        return matrix
    
    def get_implementation_order(self) -> List[str]:
        """Get optimal implementation order based on dependencies"""
        # Topological sort of requirement graph
        visited = set()
        order = []
        
        def visit(req_id: str):
            if req_id in visited:
                return
            visited.add(req_id)
            
            # Visit dependencies first
            for dep in self.requirements[req_id].dependencies:
                if dep in self.requirements:
                    visit(dep)
            
            order.append(req_id)
        
        # Start with requirements that have no dependencies
        for req_id in self.requirements:
            if not self.requirements[req_id].dependencies:
                visit(req_id)
        
        # Add any remaining requirements
        for req_id in self.requirements:
            if req_id not in visited:
                visit(req_id)
        
        return order
    
    def export_to_json(self, output_file: str) -> None:
        """Export requirement coverage to JSON file"""
        export_data = {
            "requirements": {
                req_id: {
                    "description": req.description,
                    "type": req.type.value,
                    "priority": req.priority.value,
                    "status": req.status,
                    "completion_percentage": req.completion_percentage,
                    "acceptance_criteria": req.acceptance_criteria,
                    "artifacts_expected": req.artifacts_expected,
                    "artifacts_created": req.artifacts_created,
                    "test_cases": req.test_cases,
                    "assigned_agents": req.assigned_agents,
                    "dependencies": req.dependencies,
                    "notes": req.notes
                }
                for req_id, req in self.requirements.items()
            },
            "coverage_report": self.generate_coverage_report(),
            "traceability_matrix": self.generate_traceability_matrix(),
            "implementation_order": self.get_implementation_order()
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)


def main():
    """Main function for testing"""
    analyzer = RequirementCoverageAnalyzer()
    
    # Example requirements
    sample_requirements = {
        "features": [
            "User authentication with JWT tokens",
            "RESTful API for task management",
            "Real-time notifications",
            "Admin dashboard with analytics",
            "Mobile-responsive UI"
        ],
        "technical_requirements": [
            "PostgreSQL database with migrations",
            "Redis caching layer",
            "Docker containerization"
        ],
        "constraints": [
            "Response time under 200ms",
            "Support 1000 concurrent users"
        ]
    }
    
    analyzer.parse_requirements(sample_requirements)
    
    # Generate reports
    coverage_report = analyzer.generate_coverage_report()
    print("Coverage Report:")
    print(json.dumps(coverage_report, indent=2))
    
    traceability = analyzer.generate_traceability_matrix()
    print("\nTraceability Matrix:")
    print(json.dumps(traceability, indent=2))
    
    order = analyzer.get_implementation_order()
    print("\nImplementation Order:")
    for req_id in order:
        req = analyzer.requirements[req_id]
        print(f"  {req_id}: {req.description} (Priority: {req.priority.value})")


if __name__ == "__main__":
    main()