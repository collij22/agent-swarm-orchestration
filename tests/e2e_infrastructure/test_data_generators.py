#!/usr/bin/env python3
"""
Test Data Generators for Realistic E2E Scenarios

Features:
- Generate realistic project requirements
- Create test scenarios with varying complexity
- Generate mock agent responses
- Create conflict scenarios
- Generate performance test data
"""

import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.e2e_infrastructure.workflow_engine import (
    Requirement, RequirementPriority, WorkflowPhase, ConflictType, FailureInjection
)
from tests.e2e_infrastructure.interaction_validator import InteractionType, CommunicationProtocol
from tests.e2e_infrastructure.metrics_collector import MetricType, QualityDimension

class ProjectType(Enum):
    """Types of projects for testing"""
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    API_SERVICE = "api_service"
    AI_SOLUTION = "ai_solution"
    MICROSERVICES = "microservices"
    ENTERPRISE_SYSTEM = "enterprise_system"
    LEGACY_MIGRATION = "legacy_migration"
    DATA_PIPELINE = "data_pipeline"

class ComplexityLevel(Enum):
    """Complexity levels for test scenarios"""
    SIMPLE = "simple"      # 3-5 requirements, 2-3 agents
    MEDIUM = "medium"      # 6-10 requirements, 4-6 agents
    COMPLEX = "complex"    # 11-20 requirements, 7-10 agents
    ENTERPRISE = "enterprise"  # 20+ requirements, 10+ agents

class TestDataGenerator:
    """Generates realistic test data for E2E testing"""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the generator
        
        Args:
            seed: Random seed for reproducible test data
        """
        if seed:
            random.seed(seed)
            
        # Template data
        self.feature_templates = {
            ProjectType.WEB_APP: [
                "User authentication and authorization",
                "Real-time notifications",
                "File upload and management",
                "Search functionality",
                "User dashboard",
                "Admin panel",
                "Payment integration",
                "Email notifications",
                "Social media integration",
                "Analytics dashboard"
            ],
            ProjectType.API_SERVICE: [
                "RESTful API endpoints",
                "Authentication middleware",
                "Rate limiting",
                "Data validation",
                "Error handling",
                "API documentation",
                "Webhook support",
                "Batch operations",
                "GraphQL support",
                "API versioning"
            ],
            ProjectType.AI_SOLUTION: [
                "Model training pipeline",
                "Data preprocessing",
                "Feature engineering",
                "Model serving API",
                "Real-time predictions",
                "Batch predictions",
                "Model monitoring",
                "A/B testing framework",
                "Data versioning",
                "Experiment tracking"
            ],
            ProjectType.MICROSERVICES: [
                "Service discovery",
                "API gateway",
                "Message queue integration",
                "Circuit breaker pattern",
                "Distributed tracing",
                "Service mesh",
                "Configuration management",
                "Health checks",
                "Load balancing",
                "Event sourcing"
            ],
            ProjectType.ENTERPRISE_SYSTEM: [
                "Multi-tenant architecture",
                "Role-based access control",
                "Audit logging",
                "Compliance reporting",
                "Data encryption",
                "SSO integration",
                "Workflow automation",
                "Business intelligence",
                "Document management",
                "Integration with ERP systems"
            ]
        }
        
        self.agent_templates = [
            "project-architect",
            "rapid-builder",
            "ai-specialist",
            "quality-guardian",
            "devops-engineer",
            "api-integrator",
            "database-expert",
            "frontend-specialist",
            "performance-optimizer",
            "documentation-writer",
            "project-orchestrator",
            "requirements-analyst",
            "code-migrator",
            "debug-specialist",
            "meta-agent"
        ]
        
        self.conflict_templates = {
            ConflictType.TECHNICAL: [
                ("Use React", "Use Vue.js"),
                ("REST API", "GraphQL API"),
                ("Microservices", "Monolithic"),
                ("SQL database", "NoSQL database"),
                ("Serverless", "Traditional hosting")
            ],
            ConflictType.PERFORMANCE: [
                ("Real-time updates", "Battery efficiency"),
                ("High resolution images", "Fast loading"),
                ("Complex animations", "Smooth performance"),
                ("Large dataset processing", "Quick response time"),
                ("Feature-rich", "Lightweight")
            ],
            ConflictType.RESOURCE: [
                ("Full test coverage", "Quick delivery"),
                ("Comprehensive documentation", "Rapid development"),
                ("Multiple integrations", "Limited budget"),
                ("High availability", "Cost optimization"),
                ("Premium features", "Free tier support")
            ]
        }
        
    def generate_project_requirements(self,
                                     project_type: ProjectType,
                                     complexity: ComplexityLevel) -> Dict[str, Any]:
        """Generate realistic project requirements"""
        
        # Determine number of requirements based on complexity
        num_requirements = {
            ComplexityLevel.SIMPLE: random.randint(3, 5),
            ComplexityLevel.MEDIUM: random.randint(6, 10),
            ComplexityLevel.COMPLEX: random.randint(11, 20),
            ComplexityLevel.ENTERPRISE: random.randint(20, 30)
        }[complexity]
        
        # Select features for the project
        available_features = self.feature_templates.get(
            project_type,
            self.feature_templates[ProjectType.WEB_APP]
        )
        
        selected_features = random.sample(
            available_features,
            min(num_requirements, len(available_features))
        )
        
        # Generate project metadata
        project = {
            "name": f"Test{project_type.value.title().replace('_', '')}",
            "type": project_type.value,
            "complexity": complexity.value,
            "timeline": f"{random.randint(2, 12)} weeks",
            "priority": random.choice(["MVP", "full_feature", "enterprise"]),
            "budget": f"${random.randint(5, 100) * 1000}",
            "features": selected_features,
            "tech_stack": self._generate_tech_stack(project_type),
            "constraints": self._generate_constraints(complexity),
            "success_metrics": self._generate_success_metrics(project_type)
        }
        
        return project
        
    def generate_requirements_list(self,
                                  project: Dict[str, Any],
                                  include_conflicts: bool = False) -> List[Requirement]:
        """Generate a list of Requirement objects from project specification"""
        requirements = []
        
        # Map features to requirements
        for i, feature in enumerate(project["features"]):
            req_id = f"REQ-{i+1:03d}"
            
            # Determine priority
            if i < len(project["features"]) // 3:
                priority = RequirementPriority.CRITICAL
            elif i < 2 * len(project["features"]) // 3:
                priority = RequirementPriority.HIGH
            else:
                priority = random.choice([RequirementPriority.MEDIUM, RequirementPriority.LOW])
                
            # Determine phase
            if "auth" in feature.lower() or "security" in feature.lower():
                phase = WorkflowPhase.PLANNING
            elif "api" in feature.lower() or "endpoint" in feature.lower():
                phase = WorkflowPhase.DEVELOPMENT
            elif "integration" in feature.lower():
                phase = WorkflowPhase.INTEGRATION
            elif "test" in feature.lower():
                phase = WorkflowPhase.TESTING
            elif "deploy" in feature.lower():
                phase = WorkflowPhase.DEPLOYMENT
            else:
                phase = random.choice(list(WorkflowPhase))
                
            # Generate dependencies
            dependencies = []
            if i > 0 and random.random() < 0.3:  # 30% chance of dependency
                dep_idx = random.randint(0, i-1)
                dependencies.append(f"REQ-{dep_idx+1:03d}")
                
            # Generate conflicts if requested
            conflicts = []
            if include_conflicts and random.random() < 0.2:  # 20% chance of conflict
                if i < len(project["features"]) - 1:
                    conflict_idx = random.randint(i+1, len(project["features"])-1)
                    conflicts.append(f"REQ-{conflict_idx+1:03d}")
                    
            # Select agents
            num_agents = random.randint(1, 3)
            agents = random.sample(self.agent_templates, num_agents)
            
            # Create acceptance criteria
            acceptance_criteria = self._generate_acceptance_criteria(feature)
            
            requirement = Requirement(
                id=req_id,
                description=feature,
                priority=priority,
                phase=phase,
                dependencies=dependencies,
                conflicts_with=conflicts,
                agents_required=agents,
                acceptance_criteria=acceptance_criteria
            )
            
            requirements.append(requirement)
            
        return requirements
        
    def generate_failure_injection_config(self,
                                         failure_rate: float = 0.1,
                                         targeted_agents: Optional[List[str]] = None) -> FailureInjection:
        """Generate failure injection configuration for testing"""
        
        config = FailureInjection(
            enabled=True,
            network_failure_rate=failure_rate * 0.5,  # Network failures less common
            checkpoint_failure_rate=failure_rate * 0.2,  # Checkpoint failures rare
            recovery_strategy=random.choice(["exponential_backoff", "linear_backoff", "immediate_retry"]),
            max_retries=random.randint(2, 5)
        )
        
        # Set agent-specific failure rates
        for agent in self.agent_templates:
            if targeted_agents and agent in targeted_agents:
                config.agent_failure_rates[agent] = failure_rate * 2  # Higher rate for targeted agents
            else:
                config.agent_failure_rates[agent] = failure_rate * random.uniform(0.5, 1.5)
                
        # Set tool-specific failure rates
        tools = ["write_file", "run_command", "record_decision", "complete_task"]
        for tool in tools:
            config.tool_failure_rates[tool] = failure_rate * random.uniform(0.3, 1.0)
            
        # Add failure patterns
        config.failure_patterns = [
            "intermittent",  # Failures come and go
            "cascading",     # One failure causes others
            "persistent",    # Failures persist until fixed
            "random"        # Completely random failures
        ]
        
        return config
        
    def generate_mock_agent_response(self,
                                    agent_name: str,
                                    requirement: str,
                                    success: bool = True) -> Dict[str, Any]:
        """Generate realistic mock agent response"""
        
        response = {
            "agent": agent_name,
            "requirement": requirement,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "execution_time_ms": random.randint(100, 5000),
            "artifacts": [],
            "decisions": [],
            "files_created": [],
            "tools_used": []
        }
        
        if success:
            # Generate successful response data
            if agent_name == "project-architect":
                response["artifacts"] = ["architecture.md", "database_schema.sql"]
                response["decisions"] = [
                    {"decision": "Use microservices architecture", "rationale": "Scalability requirements"},
                    {"decision": "PostgreSQL for primary database", "rationale": "ACID compliance needed"}
                ]
                
            elif agent_name == "rapid-builder":
                response["files_created"] = [
                    "src/main.py",
                    "src/api/endpoints.py",
                    "src/models/user.py",
                    "requirements.txt"
                ]
                response["tools_used"] = ["write_file", "run_command"]
                
            elif agent_name == "frontend-specialist":
                response["files_created"] = [
                    "frontend/src/App.tsx",
                    "frontend/src/components/Dashboard.tsx",
                    "frontend/package.json"
                ]
                response["artifacts"] = ["ui_mockups.figma"]
                
            elif agent_name == "quality-guardian":
                response["files_created"] = [
                    "tests/test_api.py",
                    "tests/test_models.py",
                    ".github/workflows/ci.yml"
                ]
                response["artifacts"] = ["test_report.html", "coverage_report.xml"]
                
            elif agent_name == "devops-engineer":
                response["files_created"] = [
                    "Dockerfile",
                    "docker-compose.yml",
                    "kubernetes/deployment.yaml"
                ]
                response["decisions"] = [
                    {"decision": "Use Docker for containerization", "rationale": "Platform independence"},
                    {"decision": "Deploy to AWS EKS", "rationale": "Managed Kubernetes"}
                ]
                
            # Common tools used
            response["tools_used"].extend(["record_decision", "complete_task"])
            
        else:
            # Generate failure response
            response["error"] = random.choice([
                "Dependency not found",
                "API rate limit exceeded",
                "Compilation error",
                "Test failure",
                "Connection timeout",
                "Invalid configuration",
                "Permission denied"
            ])
            response["error_details"] = f"Failed to complete {requirement}: {response['error']}"
            
        return response
        
    def generate_interaction_data(self,
                                 source_agent: str,
                                 target_agent: str,
                                 interaction_type: Optional[InteractionType] = None) -> Dict[str, Any]:
        """Generate agent interaction data"""
        
        if not interaction_type:
            interaction_type = random.choice(list(InteractionType))
            
        protocol = random.choice(list(CommunicationProtocol))
        
        interaction = {
            "id": f"interaction_{random.randint(1000, 9999)}",
            "source_agent": source_agent,
            "target_agent": target_agent,
            "interaction_type": interaction_type.value,
            "protocol": protocol.value,
            "timestamp": datetime.now().isoformat(),
            "latency_ms": random.randint(10, 1000)
        }
        
        # Add protocol-specific data
        if protocol == CommunicationProtocol.CONTEXT_PASSING:
            interaction["data_transferred"] = {
                "completed_tasks": [source_agent],
                "artifacts": {f"{source_agent}_output": "data"},
                "decisions": []
            }
            
        elif protocol == CommunicationProtocol.ARTIFACT_SHARING:
            interaction["artifacts_shared"] = [
                f"{source_agent}_artifact_{i}.json" 
                for i in range(random.randint(1, 3))
            ]
            
        elif protocol == CommunicationProtocol.TOOL_MEDIATED:
            interaction["tools_used"] = ["request_artifact", "dependency_check"]
            
        elif protocol == CommunicationProtocol.FILE_BASED:
            interaction["data_transferred"] = {
                "file_paths": [f"/tmp/{source_agent}_to_{target_agent}.json"]
            }
            
        return interaction
        
    def generate_performance_data(self,
                                 operation: str,
                                 success_rate: float = 0.95) -> Dict[str, Any]:
        """Generate performance benchmark data"""
        
        is_success = random.random() < success_rate
        
        perf_data = {
            "operation": operation,
            "execution_time_ms": random.gauss(200, 50) if is_success else random.gauss(5000, 1000),
            "memory_usage_mb": random.gauss(100, 20),
            "cpu_usage_percent": random.gauss(30, 10),
            "throughput": random.gauss(100, 20) if is_success else random.gauss(10, 5),
            "latency_p50": random.gauss(150, 30),
            "latency_p95": random.gauss(500, 100),
            "latency_p99": random.gauss(1000, 200),
            "error_rate": (1 - success_rate) if not is_success else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return perf_data
        
    def generate_quality_metrics(self,
                                requirement_id: str,
                                completion_level: float = 0.8) -> Dict[str, Any]:
        """Generate quality metrics data"""
        
        metrics = {
            "requirement_id": requirement_id,
            "completion_percentage": min(100, max(0, completion_level * 100 + random.gauss(0, 10))),
            "code_quality_score": min(100, max(0, 75 + random.gauss(0, 15))),
            "test_coverage": min(100, max(0, 60 + random.gauss(0, 20))),
            "security_score": min(100, max(0, 85 + random.gauss(0, 10))),
            "documentation_score": min(100, max(0, 70 + random.gauss(0, 15))),
            "files_created": random.randint(1, 10),
            "tests_created": random.randint(0, 5),
            "issues_found": random.randint(0, 3) if completion_level < 0.9 else 0
        }
        
        return metrics
        
    def _generate_tech_stack(self, project_type: ProjectType) -> Dict[str, str]:
        """Generate technology stack based on project type"""
        
        stacks = {
            ProjectType.WEB_APP: {
                "frontend": random.choice(["React + TypeScript", "Vue.js", "Angular"]),
                "backend": random.choice(["FastAPI", "Express + TypeScript", "Django"]),
                "database": random.choice(["PostgreSQL", "MySQL", "MongoDB"]),
                "cache": "Redis",
                "hosting": random.choice(["AWS", "Vercel", "Heroku"])
            },
            ProjectType.API_SERVICE: {
                "language": random.choice(["Python", "Node.js", "Go"]),
                "framework": random.choice(["FastAPI", "Express", "Gin"]),
                "database": random.choice(["PostgreSQL", "MongoDB"]),
                "cache": "Redis",
                "api_gateway": random.choice(["Kong", "AWS API Gateway", "Nginx"])
            },
            ProjectType.AI_SOLUTION: {
                "language": "Python",
                "ml_framework": random.choice(["TensorFlow", "PyTorch", "scikit-learn"]),
                "serving": random.choice(["FastAPI", "TensorFlow Serving", "Modal"]),
                "vector_db": random.choice(["Pinecone", "Chroma", "Weaviate"]),
                "llm_provider": random.choice(["OpenAI", "Anthropic", "Hugging Face"])
            },
            ProjectType.MICROSERVICES: {
                "languages": ["Python", "Go", "Node.js"],
                "orchestration": random.choice(["Kubernetes", "Docker Swarm"]),
                "service_mesh": random.choice(["Istio", "Linkerd", "Consul"]),
                "message_queue": random.choice(["RabbitMQ", "Kafka", "Redis Pub/Sub"]),
                "monitoring": random.choice(["Prometheus + Grafana", "DataDog", "New Relic"])
            },
            ProjectType.ENTERPRISE_SYSTEM: {
                "backend": random.choice(["Java Spring", ".NET Core", "Python Django"]),
                "frontend": random.choice(["React", "Angular"]),
                "database": random.choice(["Oracle", "SQL Server", "PostgreSQL"]),
                "integration": random.choice(["MuleSoft", "Apache Camel", "custom"]),
                "identity": random.choice(["Okta", "Auth0", "Active Directory"])
            }
        }
        
        return stacks.get(project_type, stacks[ProjectType.WEB_APP])
        
    def _generate_constraints(self, complexity: ComplexityLevel) -> List[str]:
        """Generate project constraints based on complexity"""
        
        base_constraints = [
            "Must be GDPR compliant",
            "Support 1000+ concurrent users",
            "99.9% uptime SLA",
            "Mobile responsive",
            "Accessibility compliant (WCAG 2.1)"
        ]
        
        if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.ENTERPRISE]:
            base_constraints.extend([
                "Multi-region deployment",
                "SOC 2 compliance required",
                "Support for 10+ languages",
                "Zero-downtime deployments",
                "Disaster recovery plan"
            ])
            
        return random.sample(base_constraints, random.randint(2, min(5, len(base_constraints))))
        
    def _generate_success_metrics(self, project_type: ProjectType) -> List[str]:
        """Generate success metrics for the project"""
        
        metrics = {
            ProjectType.WEB_APP: [
                "Page load time < 3 seconds",
                "1000+ daily active users",
                "< 1% error rate",
                "95% user satisfaction score",
                "< 200ms API response time"
            ],
            ProjectType.API_SERVICE: [
                "< 100ms average latency",
                "10,000 requests per second",
                "99.99% availability",
                "< 0.1% error rate",
                "Comprehensive API documentation"
            ],
            ProjectType.AI_SOLUTION: [
                "Model accuracy > 90%",
                "< 500ms inference time",
                "Support for batch processing",
                "Model drift monitoring",
                "A/B testing capability"
            ],
            ProjectType.MICROSERVICES: [
                "Service discovery < 50ms",
                "Inter-service latency < 10ms",
                "Automatic scaling",
                "Circuit breaker implementation",
                "Distributed tracing"
            ],
            ProjectType.ENTERPRISE_SYSTEM: [
                "Support for 10,000+ users",
                "Data encryption at rest and in transit",
                "Audit trail for all actions",
                "Role-based access control",
                "Integration with existing systems"
            ]
        }
        
        project_metrics = metrics.get(project_type, metrics[ProjectType.WEB_APP])
        return random.sample(project_metrics, random.randint(3, len(project_metrics)))
        
    def _generate_acceptance_criteria(self, feature: str) -> Dict[str, Any]:
        """Generate acceptance criteria for a feature"""
        
        criteria = {}
        
        # Common criteria
        criteria["implemented"] = False
        criteria["tested"] = False
        criteria["documented"] = False
        
        # Feature-specific criteria
        if "auth" in feature.lower():
            criteria["secure_password_storage"] = False
            criteria["jwt_implementation"] = False
            criteria["role_based_access"] = False
            
        elif "api" in feature.lower():
            criteria["endpoints_created"] = False
            criteria["input_validation"] = False
            criteria["error_handling"] = False
            
        elif "dashboard" in feature.lower():
            criteria["responsive_design"] = False
            criteria["real_time_updates"] = False
            criteria["data_visualization"] = False
            
        elif "payment" in feature.lower():
            criteria["pci_compliance"] = False
            criteria["multiple_payment_methods"] = False
            criteria["refund_capability"] = False
            
        return criteria