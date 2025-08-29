#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
#   "pyyaml>=6.0",
# ]
# ///

"""
Single File Agent: DevOps Engineer

Standalone execution of the devops-engineer agent for CI/CD, deployment, and infrastructure.

Example Usage:
    uv run sfa/sfa_devops_engineer.py --prompt "Deploy to AWS" --output deployment/
    uv run sfa/sfa_devops_engineer.py --requirements requirements.yaml --platform aws --verbose
    uv run sfa/sfa_devops_engineer.py --prompt "Set up CI/CD" --provider github-actions --output .github/
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: Anthropic not installed. Running in simulation mode.")

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

# Initialize console
console = Console()

# Agent prompt template
AGENT_PROMPT = """<role>
You are an expert DevOps engineer specializing in CI/CD pipelines, cloud infrastructure, and deployment automation.
You excel at setting up scalable, secure, and efficient deployment systems with proper monitoring and observability.
</role>

<context>
Project Requirements: {{requirements}}
Platform: {{platform}}
Environment: {{environment}}
</context>

<instructions>
1. Analyze infrastructure requirements
2. Set up CI/CD pipelines with best practices
3. Configure cloud infrastructure (IaC)
4. Implement monitoring and alerting
5. Create containerization strategies
6. Ensure security and compliance
</instructions>

<tools>
    <tool>
        <name>setup_cicd</name>
        <description>Configure CI/CD pipelines</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>CI/CD strategy reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>provider</name>
                <type>string</type>
                <description>CI/CD provider (github-actions, gitlab-ci, jenkins)</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>pipeline_config</name>
                <type>object</type>
                <description>Pipeline configuration files</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>stages</name>
                <type>array</type>
                <description>Pipeline stages</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>deploy_infrastructure</name>
        <description>Set up cloud infrastructure</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Infrastructure design reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>cloud_provider</name>
                <type>string</type>
                <description>Cloud provider (AWS, GCP, Azure)</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>iac_files</name>
                <type>object</type>
                <description>Infrastructure as Code files</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>resources</name>
                <type>object</type>
                <description>Cloud resources to provision</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>configure_monitoring</name>
        <description>Set up monitoring and alerting</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Monitoring strategy reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>monitoring_tools</name>
                <type>array</type>
                <description>Monitoring tools to use</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>alerts</name>
                <type>array</type>
                <description>Alert configurations</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>dashboards</name>
                <type>object</type>
                <description>Dashboard configurations</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>create_docker</name>
        <description>Create Docker configurations</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Containerization strategy</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>dockerfiles</name>
                <type>object</type>
                <description>Dockerfile contents by service</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>compose_config</name>
                <type>string</type>
                <description>Docker Compose configuration</description>
                <required>false</required>
            </parameter>
            <parameter>
                <name>registry</name>
                <type>string</type>
                <description>Container registry configuration</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>setup_kubernetes</name>
        <description>Configure Kubernetes deployments</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>K8s deployment strategy</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>manifests</name>
                <type>object</type>
                <description>Kubernetes manifest files</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>helm_charts</name>
                <type>object</type>
                <description>Helm chart configurations</description>
                <required>false</required>
            </parameter>
            <parameter>
                <name>scaling_config</name>
                <type>object</type>
                <description>Auto-scaling configuration</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>configure_security</name>
        <description>Set up security configurations</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Security strategy reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>security_policies</name>
                <type>object</type>
                <description>Security policies and rules</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>secrets_management</name>
                <type>object</type>
                <description>Secrets management configuration</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>compliance</name>
                <type>array</type>
                <description>Compliance requirements</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>save_deployment</name>
        <description>Save deployment configurations</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Save strategy reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>output_dir</name>
                <type>string</type>
                <description>Output directory path</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>files</name>
                <type>object</type>
                <description>All deployment files to save</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>deployment_docs</name>
                <type>string</type>
                <description>Deployment documentation</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
</tools>

<task>
{{task}}
</task>

Remember to:
- Follow infrastructure as code best practices
- Implement proper security at every layer
- Set up comprehensive monitoring
- Create rollback strategies
- Document deployment procedures
- Optimize for cost and performance
"""

class DevOpsEngineerAgent:
    """Single File Agent for DevOps and Infrastructure"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if HAS_ANTHROPIC and self.api_key else None
        self.deployment_files = {}
        self.infrastructure = {}
        self.monitoring_config = {}
        
    def setup_cicd(self, reasoning: str, provider: str, pipeline_config: Dict, stages: List[str]) -> str:
        """Configure CI/CD pipelines"""
        console.print(Panel(
            f"[blue]Setting up CI/CD[/blue]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Provider:[/dim] {provider}\n"
            f"[dim]Stages:[/dim] {', '.join(stages)}",
            border_style="blue"
        ))
        
        self.deployment_files.update(pipeline_config)
        
        # Display pipeline stages
        table = Table(title="CI/CD Pipeline Stages")
        table.add_column("Stage", style="cyan")
        table.add_column("Action", style="green")
        
        for stage in stages:
            table.add_row(stage, "Configured")
        
        console.print(table)
        
        return f"CI/CD pipeline configured with {len(stages)} stages"
    
    def deploy_infrastructure(self, reasoning: str, cloud_provider: str, iac_files: Dict, resources: Dict) -> str:
        """Set up cloud infrastructure"""
        console.print(Panel(
            f"[green]Deploying Infrastructure[/green]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Provider:[/dim] {cloud_provider}\n"
            f"[dim]Resources:[/dim] {list(resources.keys())}",
            border_style="green"
        ))
        
        self.deployment_files.update(iac_files)
        self.infrastructure = resources
        
        # Display resources
        table = Table(title="Cloud Resources")
        table.add_column("Resource", style="cyan")
        table.add_column("Type", style="yellow")
        
        for resource, config in list(resources.items())[:5]:
            table.add_row(resource, str(config)[:30])
        
        console.print(table)
        
        return f"Infrastructure deployed on {cloud_provider}"
    
    def configure_monitoring(self, reasoning: str, monitoring_tools: List[str], alerts: List, dashboards: Dict = None) -> str:
        """Set up monitoring and alerting"""
        console.print(Panel(
            f"[yellow]Configuring Monitoring[/yellow]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Tools:[/dim] {', '.join(monitoring_tools)}\n"
            f"[dim]Alerts:[/dim] {len(alerts)} configured",
            border_style="yellow"
        ))
        
        self.monitoring_config = {
            'tools': monitoring_tools,
            'alerts': alerts,
            'dashboards': dashboards or {}
        }
        
        # Save monitoring configs
        if dashboards:
            for name, config in dashboards.items():
                self.deployment_files[f"monitoring/{name}.json"] = json.dumps(config, indent=2)
        
        return f"Monitoring configured with {len(monitoring_tools)} tools"
    
    def create_docker(self, reasoning: str, dockerfiles: Dict, compose_config: str = None, registry: str = None) -> str:
        """Create Docker configurations"""
        console.print(Panel(
            f"[cyan]Creating Docker Config[/cyan]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Services:[/dim] {list(dockerfiles.keys())}\n"
            f"[dim]Registry:[/dim] {registry or 'Local'}",
            border_style="cyan"
        ))
        
        # Save Dockerfiles
        for service, dockerfile in dockerfiles.items():
            self.deployment_files[f"docker/{service}/Dockerfile"] = dockerfile
        
        # Save docker-compose if provided
        if compose_config:
            self.deployment_files["docker-compose.yml"] = compose_config
        
        return f"Docker configuration created for {len(dockerfiles)} services"
    
    def setup_kubernetes(self, reasoning: str, manifests: Dict, helm_charts: Dict = None, scaling_config: Dict = None) -> str:
        """Configure Kubernetes deployments"""
        console.print(Panel(
            f"[magenta]Setting up Kubernetes[/magenta]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Manifests:[/dim] {len(manifests)} files\n"
            f"[dim]Helm:[/dim] {'Configured' if helm_charts else 'Not used'}",
            border_style="magenta"
        ))
        
        # Save K8s manifests
        for name, manifest in manifests.items():
            self.deployment_files[f"k8s/{name}"] = manifest
        
        # Save Helm charts
        if helm_charts:
            for chart, config in helm_charts.items():
                self.deployment_files[f"helm/{chart}/values.yaml"] = yaml.dump(config)
        
        return f"Kubernetes configured with {len(manifests)} manifests"
    
    def configure_security(self, reasoning: str, security_policies: Dict, secrets_management: Dict, compliance: List = None) -> str:
        """Set up security configurations"""
        console.print(Panel(
            f"[red]Configuring Security[/red]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Policies:[/dim] {len(security_policies)} defined\n"
            f"[dim]Compliance:[/dim] {', '.join(compliance) if compliance else 'Standard'}",
            border_style="red"
        ))
        
        # Save security configurations
        self.deployment_files["security/policies.yaml"] = yaml.dump(security_policies)
        self.deployment_files["security/secrets.yaml"] = yaml.dump(secrets_management)
        
        if compliance:
            self.deployment_files["security/compliance.md"] = f"# Compliance Requirements\n\n" + "\n".join(f"- {c}" for c in compliance)
        
        return f"Security configured with {len(security_policies)} policies"
    
    def save_deployment(self, reasoning: str, output_dir: str, files: Dict, deployment_docs: str = None) -> str:
        """Save deployment configurations"""
        console.print(Panel(
            f"[green]Saving Deployment[/green]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Output:[/dim] {output_dir}",
            border_style="green"
        ))
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Merge all files
        all_files = {**self.deployment_files, **files}
        
        # Save all files
        for filepath, content in all_files.items():
            file_path = output_path / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        # Save deployment documentation
        if deployment_docs:
            doc_path = output_path / "DEPLOYMENT.md"
            doc_path.write_text(deployment_docs)
        
        # Save deployment manifest
        manifest = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "infrastructure": self.infrastructure,
            "monitoring": self.monitoring_config,
            "files": list(all_files.keys())
        }
        
        manifest_path = output_path / "deployment_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return f"Deployment configuration saved to {output_dir} ({len(all_files)} files)"
    
    def run(self, prompt: str, requirements: Dict, output_dir: str, compute_limit: int = 10) -> bool:
        """Run the agent with Claude API or simulation"""
        
        if not self.client:
            return self._run_simulation(prompt, requirements, output_dir)
        
        # Prepare the full prompt
        full_prompt = AGENT_PROMPT.replace("{{requirements}}", json.dumps(requirements, indent=2))
        full_prompt = full_prompt.replace("{{platform}}", requirements.get("platform", "aws"))
        full_prompt = full_prompt.replace("{{environment}}", requirements.get("environment", "production"))
        full_prompt = full_prompt.replace("{{task}}", prompt)
        
        messages = [{"role": "user", "content": full_prompt}]
        
        # Tool definitions for Anthropic
        tools = [
            {
                "name": "setup_cicd",
                "description": "Configure CI/CD pipelines",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "provider": {"type": "string"},
                        "pipeline_config": {"type": "object"},
                        "stages": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["reasoning", "provider", "pipeline_config", "stages"]
                }
            },
            {
                "name": "deploy_infrastructure",
                "description": "Set up cloud infrastructure",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "cloud_provider": {"type": "string"},
                        "iac_files": {"type": "object"},
                        "resources": {"type": "object"}
                    },
                    "required": ["reasoning", "cloud_provider", "iac_files", "resources"]
                }
            },
            {
                "name": "configure_monitoring",
                "description": "Set up monitoring and alerting",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "monitoring_tools": {"type": "array", "items": {"type": "string"}},
                        "alerts": {"type": "array"},
                        "dashboards": {"type": "object"}
                    },
                    "required": ["reasoning", "monitoring_tools", "alerts"]
                }
            },
            {
                "name": "create_docker",
                "description": "Create Docker configurations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "dockerfiles": {"type": "object"},
                        "compose_config": {"type": "string"},
                        "registry": {"type": "string"}
                    },
                    "required": ["reasoning", "dockerfiles"]
                }
            },
            {
                "name": "setup_kubernetes",
                "description": "Configure Kubernetes deployments",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "manifests": {"type": "object"},
                        "helm_charts": {"type": "object"},
                        "scaling_config": {"type": "object"}
                    },
                    "required": ["reasoning", "manifests"]
                }
            },
            {
                "name": "configure_security",
                "description": "Set up security configurations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "security_policies": {"type": "object"},
                        "secrets_management": {"type": "object"},
                        "compliance": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["reasoning", "security_policies", "secrets_management"]
                }
            },
            {
                "name": "save_deployment",
                "description": "Save deployment configurations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "output_dir": {"type": "string"},
                        "files": {"type": "object"},
                        "deployment_docs": {"type": "string"}
                    },
                    "required": ["reasoning", "output_dir", "files"]
                }
            }
        ]
        
        iterations = 0
        console.rule("[yellow]Starting DevOps Engineer Agent[/yellow]")
        
        while iterations < compute_limit:
            iterations += 1
            console.rule(f"[blue]Iteration {iterations}/{compute_limit}[/blue]")
            
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=messages,
                    tools=tools,
                    tool_choice={"type": "auto"}
                )
                
                # Process response
                assistant_content = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        assistant_content += block.text
                        console.print(Panel(block.text, title="Assistant"))
                    
                    elif hasattr(block, 'type') and block.type == 'tool_use':
                        tool_name = block.name
                        tool_args = block.input
                        tool_id = block.id
                        
                        console.print(f"[yellow]Tool Call:[/yellow] {tool_name}")
                        
                        # Execute tool
                        if tool_name == "setup_cicd":
                            result = self.setup_cicd(**tool_args)
                        elif tool_name == "deploy_infrastructure":
                            result = self.deploy_infrastructure(**tool_args)
                        elif tool_name == "configure_monitoring":
                            result = self.configure_monitoring(**tool_args)
                        elif tool_name == "create_docker":
                            result = self.create_docker(**tool_args)
                        elif tool_name == "setup_kubernetes":
                            result = self.setup_kubernetes(**tool_args)
                        elif tool_name == "configure_security":
                            result = self.configure_security(**tool_args)
                        elif tool_name == "save_deployment":
                            tool_args['output_dir'] = output_dir
                            result = self.save_deployment(**tool_args)
                            console.print(Panel(
                                f"[bold green]Deployment Complete![/bold green]\n"
                                f"Configuration saved to: {output_dir}",
                                border_style="green"
                            ))
                            return True
                        else:
                            result = f"Unknown tool: {tool_name}"
                        
                        # Add messages for next iteration
                        messages.append({"role": "assistant", "content": response.content})
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": result
                                }
                            ]
                        })
                
                if assistant_content and not any(hasattr(b, 'type') and b.type == 'tool_use' for b in response.content):
                    # No tool calls, agent is done
                    break
                    
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                return False
        
        console.print("[yellow]Maximum iterations reached[/yellow]")
        return False
    
    def _run_simulation(self, prompt: str, requirements: Dict, output_dir: str) -> bool:
        """Simulate agent execution without API"""
        console.print("[yellow]Running in simulation mode (no API key)[/yellow]")
        
        # Simulate workflow
        self.setup_cicd(
            "Automated testing and deployment pipeline",
            "github-actions",
            {
                ".github/workflows/deploy.yml": "# GitHub Actions deployment workflow",
                ".github/workflows/test.yml": "# Testing workflow"
            },
            ["lint", "test", "build", "deploy"]
        )
        
        time.sleep(1)
        
        self.deploy_infrastructure(
            "Scalable cloud infrastructure with auto-scaling",
            "AWS",
            {
                "terraform/main.tf": "# Main Terraform configuration",
                "terraform/variables.tf": "# Terraform variables",
                "terraform/outputs.tf": "# Terraform outputs"
            },
            {
                "vpc": "Virtual Private Cloud",
                "ecs": "Container Service",
                "rds": "PostgreSQL Database",
                "elasticache": "Redis Cache",
                "cloudfront": "CDN"
            }
        )
        
        time.sleep(1)
        
        self.create_docker(
            "Multi-stage builds for optimization",
            {
                "api": "FROM python:3.11-slim\n# API Dockerfile",
                "frontend": "FROM node:18-alpine\n# Frontend Dockerfile"
            },
            "version: '3.8'\nservices:\n  api:\n    build: ./api\n  frontend:\n    build: ./frontend",
            "AWS ECR"
        )
        
        time.sleep(1)
        
        self.configure_monitoring(
            "Comprehensive observability stack",
            ["DataDog", "Sentry", "CloudWatch"],
            [
                {"name": "High Error Rate", "threshold": "5%"},
                {"name": "Response Time", "threshold": "3s"},
                {"name": "CPU Usage", "threshold": "80%"}
            ]
        )
        
        time.sleep(1)
        
        # Generate deployment documentation
        doc = """# Deployment Guide

## Infrastructure
- Cloud Provider: AWS
- Container Orchestration: ECS
- Database: RDS PostgreSQL
- Cache: ElastiCache Redis
- CDN: CloudFront

## CI/CD Pipeline
- Provider: GitHub Actions
- Stages: Lint -> Test -> Build -> Deploy

## Monitoring
- Application: DataDog
- Errors: Sentry  
- Infrastructure: CloudWatch

## Deployment Steps
1. Push to main branch
2. CI/CD pipeline triggers
3. Tests run automatically
4. Docker images built and pushed
5. ECS service updated
6. Health checks verify deployment

*Generated in simulation mode*
"""
        
        self.save_deployment(
            "Production-ready deployment configuration",
            output_dir,
            self.deployment_files,
            doc
        )
        
        return True

def main():
    parser = argparse.ArgumentParser(description="DevOps Engineer Agent")
    parser.add_argument("--prompt", "-p", required=True, help="Deployment task description")
    parser.add_argument("--output", "-o", default="deployment/", help="Output directory")
    parser.add_argument("--requirements", "-r", help="Path to requirements.yaml file")
    parser.add_argument("--platform", choices=["aws", "gcp", "azure", "vercel"], help="Cloud platform")
    parser.add_argument("--provider", choices=["github-actions", "gitlab-ci", "jenkins"], help="CI/CD provider")
    parser.add_argument("--environment", "-e", choices=["dev", "staging", "production"], default="production", help="Environment")
    parser.add_argument("--compute", "-c", type=int, default=10, help="Max compute iterations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Load requirements
    requirements = {}
    if args.requirements and Path(args.requirements).exists():
        with open(args.requirements) as f:
            requirements = yaml.safe_load(f)
    else:
        requirements = {
            "name": "Deployment",
            "type": "infrastructure",
            "description": args.prompt,
            "platform": args.platform or "aws",
            "provider": args.provider or "github-actions",
            "environment": args.environment
        }
    
    # Run agent
    agent = DevOpsEngineerAgent()
    success = agent.run(args.prompt, requirements, args.output, args.compute)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()