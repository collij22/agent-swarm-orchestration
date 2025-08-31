#!/usr/bin/env python3
"""
Interactive CLI Wizard for Agent Swarm Project Setup
Provides guided project configuration and requirements gathering

Features:
- Interactive prompts for project configuration
- Template selection for common project types
- Requirements validation and enhancement
- Automatic YAML generation
- Cost estimation before execution
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import re

# Rich for beautiful CLI interface
try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("Install rich for better UI: pip install rich")
    # Fallback to basic input
    Prompt = input
    Confirm = lambda x, default=False: input(f"{x} (y/n): ").lower() == 'y'
    IntPrompt = lambda x, default=1: int(input(f"{x} [{default}]: ") or default)

console = Console() if HAS_RICH else None

class ProjectType(Enum):
    """Supported project types"""
    WEB_APP = "web_app"
    API_SERVICE = "api_service"
    MOBILE_APP = "mobile_app"
    AI_SOLUTION = "ai_solution"
    E_COMMERCE = "e_commerce"
    SAAS_PLATFORM = "saas_platform"
    DATA_PIPELINE = "data_pipeline"
    MICROSERVICES = "microservices"
    CUSTOM = "custom"

class ProjectTemplate:
    """Project templates with pre-configured settings"""
    
    TEMPLATES = {
        ProjectType.E_COMMERCE: {
            "name": "E-Commerce Platform",
            "description": "Full-featured online store with payments",
            "features": [
                "Product catalog with categories",
                "Shopping cart and checkout",
                "User authentication and profiles",
                "Order management system",
                "Payment integration (Stripe)",
                "Admin dashboard",
                "Email notifications",
                "Product search and filters",
                "Reviews and ratings",
                "Inventory management"
            ],
            "tech_stack": {
                "frontend": {
                    "framework": "React + TypeScript",
                    "styling": "Tailwind CSS",
                    "state": "Redux Toolkit"
                },
                "backend": {
                    "framework": "FastAPI",
                    "database": "PostgreSQL",
                    "cache": "Redis"
                },
                "payments": "Stripe",
                "deployment": "Docker + AWS/Vercel"
            },
            "estimated_cost": "$2-5",
            "estimated_time": "2-3 weeks"
        },
        ProjectType.SAAS_PLATFORM: {
            "name": "SaaS Platform",
            "description": "Multi-tenant SaaS application with subscriptions",
            "features": [
                "Multi-tenant architecture",
                "User authentication with SSO",
                "Subscription management",
                "Billing and invoicing",
                "Team collaboration features",
                "API with rate limiting",
                "Admin super-panel",
                "Analytics dashboard",
                "Webhook system",
                "Email automation"
            ],
            "tech_stack": {
                "frontend": {
                    "framework": "Next.js",
                    "styling": "Tailwind CSS",
                    "ui": "shadcn/ui"
                },
                "backend": {
                    "framework": "FastAPI",
                    "database": "PostgreSQL",
                    "queue": "Celery + Redis"
                },
                "auth": "Auth0/Clerk",
                "payments": "Stripe",
                "deployment": "Vercel + Railway"
            },
            "estimated_cost": "$3-7",
            "estimated_time": "3-4 weeks"
        },
        ProjectType.AI_SOLUTION: {
            "name": "AI-Powered Application",
            "description": "Application with integrated AI capabilities",
            "features": [
                "LLM integration (GPT-4/Claude)",
                "Custom prompt engineering",
                "Vector database for RAG",
                "Document processing",
                "Conversational interface",
                "Fine-tuning capabilities",
                "Usage tracking and limits",
                "Caching for cost optimization",
                "Fallback providers",
                "API endpoints for AI features"
            ],
            "tech_stack": {
                "frontend": {
                    "framework": "React + TypeScript",
                    "styling": "Tailwind CSS"
                },
                "backend": {
                    "framework": "FastAPI",
                    "database": "PostgreSQL",
                    "vector_db": "Pinecone/Chroma"
                },
                "ai": {
                    "llm": "OpenAI/Anthropic",
                    "embeddings": "OpenAI",
                    "framework": "LangChain"
                },
                "deployment": "Docker + AWS"
            },
            "estimated_cost": "$4-8",
            "estimated_time": "2-3 weeks"
        },
        ProjectType.MOBILE_APP: {
            "name": "Mobile Application",
            "description": "Cross-platform mobile app",
            "features": [
                "Cross-platform (iOS/Android)",
                "User authentication",
                "Push notifications",
                "Offline capabilities",
                "Camera and media access",
                "Location services",
                "In-app purchases",
                "Social sharing",
                "Analytics integration",
                "Deep linking"
            ],
            "tech_stack": {
                "mobile": {
                    "framework": "React Native/Flutter",
                    "state": "Redux/Riverpod",
                    "navigation": "React Navigation/GoRouter"
                },
                "backend": {
                    "framework": "FastAPI/Node.js",
                    "database": "PostgreSQL",
                    "realtime": "WebSocket/Firebase"
                },
                "services": {
                    "push": "Firebase FCM",
                    "analytics": "Firebase Analytics"
                }
            },
            "estimated_cost": "$3-6",
            "estimated_time": "3-4 weeks"
        }
    }

class ProjectWizard:
    """Interactive CLI wizard for project setup"""
    
    def __init__(self):
        self.console = console
        self.project_config = {}
        self.requirements = {}
        
    def run(self) -> Dict[str, Any]:
        """Run the interactive wizard"""
        self._show_welcome()
        
        # Step 1: Choose project type or template
        project_type = self._select_project_type()
        
        # Step 2: Load template or create custom
        if project_type != ProjectType.CUSTOM:
            self.project_config = self._load_template(project_type)
            self._customize_template()
        else:
            self.project_config = self._create_custom_project()
        
        # Step 3: Gather additional requirements
        self._gather_requirements()
        
        # Step 4: Configure technical details
        self._configure_tech_stack()
        
        # Step 5: Set constraints and priorities
        self._set_constraints()
        
        # Step 6: Review and confirm
        if self._review_configuration():
            # Step 7: Generate YAML file
            output_file = self._save_configuration()
            self._show_next_steps(output_file)
            return self.project_config
        else:
            if Confirm.ask("Would you like to start over?", default=True):
                return self.run()
            else:
                self._print_error("Configuration cancelled")
                return {}
    
    def _show_welcome(self):
        """Display welcome message"""
        if HAS_RICH:
            welcome = Panel.fit(
                "[bold cyan]Agent Swarm Project Wizard[/bold cyan]\n\n"
                "This wizard will help you configure your project and generate\n"
                "a requirements.yaml file for the agent swarm to build your application.\n\n"
                "[dim]Press Ctrl+C at any time to exit[/dim]",
                border_style="cyan"
            )
            self.console.print(welcome)
        else:
            print("\n" + "="*60)
            print("AGENT SWARM PROJECT WIZARD")
            print("="*60)
            print("This wizard will help you configure your project.")
            print()
    
    def _select_project_type(self) -> ProjectType:
        """Select project type or template"""
        self._print_header("Select Project Type")
        
        if HAS_RICH:
            table = Table(title="Available Templates", show_header=True)
            table.add_column("Option", style="cyan", width=15)
            table.add_column("Type", style="yellow")
            table.add_column("Description", style="white")
            table.add_column("Est. Cost", style="green")
            
            for i, (ptype, template) in enumerate(ProjectTemplate.TEMPLATES.items(), 1):
                table.add_row(
                    str(i),
                    template["name"],
                    template["description"],
                    template["estimated_cost"]
                )
            
            table.add_row(
                str(len(ProjectTemplate.TEMPLATES) + 1),
                "Custom Project",
                "Start from scratch with custom configuration",
                "Varies"
            )
            
            self.console.print(table)
        else:
            print("\nAvailable Templates:")
            for i, (ptype, template) in enumerate(ProjectTemplate.TEMPLATES.items(), 1):
                print(f"{i}. {template['name']} - {template['description']}")
            print(f"{len(ProjectTemplate.TEMPLATES) + 1}. Custom Project")
        
        choice = IntPrompt.ask(
            "\nSelect option",
            default=1,
            choices=[str(i) for i in range(1, len(ProjectTemplate.TEMPLATES) + 2)]
        ) if HAS_RICH else int(input("\nSelect option (number): "))
        
        if choice <= len(ProjectTemplate.TEMPLATES):
            return list(ProjectTemplate.TEMPLATES.keys())[choice - 1]
        else:
            return ProjectType.CUSTOM
    
    def _load_template(self, project_type: ProjectType) -> Dict:
        """Load and configure template"""
        template = ProjectTemplate.TEMPLATES[project_type].copy()
        
        self._print_success(f"Loading {template['name']} template...")
        
        # Convert to project config format
        config = {
            "project": {
                "name": Prompt.ask("Project name", default=template["name"].replace(" ", "")) if HAS_RICH else input(f"Project name [{template['name'].replace(' ', '')}]: ") or template["name"].replace(" ", ""),
                "type": project_type.value,
                "description": template["description"],
                "timeline": template["estimated_time"],
                "priority": "MVP"
            },
            "features": template["features"],
            "tech_overrides": template["tech_stack"]
        }
        
        return config
    
    def _customize_template(self):
        """Allow customization of loaded template"""
        self._print_header("Customize Template")
        
        # Show current features
        self._print_info("Current features:")
        for i, feature in enumerate(self.project_config["features"], 1):
            self._print_item(f"{i}. {feature}")
        
        # Add/remove features
        if Confirm.ask("\nWould you like to modify features?", default=False):
            while True:
                action = Prompt.ask(
                    "Action",
                    choices=["add", "remove", "done"],
                    default="done"
                ) if HAS_RICH else input("Action (add/remove/done): ")
                
                if action == "done":
                    break
                elif action == "add":
                    feature = Prompt.ask("New feature") if HAS_RICH else input("New feature: ")
                    self.project_config["features"].append(feature)
                    self._print_success(f"Added: {feature}")
                elif action == "remove":
                    idx = IntPrompt.ask(
                        "Feature number to remove",
                        default=1
                    ) if HAS_RICH else int(input("Feature number to remove: "))
                    if 1 <= idx <= len(self.project_config["features"]):
                        removed = self.project_config["features"].pop(idx - 1)
                        self._print_warning(f"Removed: {removed}")
    
    def _create_custom_project(self) -> Dict:
        """Create custom project from scratch"""
        self._print_header("Custom Project Configuration")
        
        config = {
            "project": {
                "name": Prompt.ask("Project name") if HAS_RICH else input("Project name: "),
                "type": "custom",
                "description": Prompt.ask("Project description") if HAS_RICH else input("Project description: "),
                "timeline": Prompt.ask("Timeline", default="2 weeks") if HAS_RICH else input("Timeline [2 weeks]: ") or "2 weeks",
                "priority": Prompt.ask("Priority", choices=["MVP", "full_feature", "enterprise"], default="MVP") if HAS_RICH else input("Priority (MVP/full_feature/enterprise) [MVP]: ") or "MVP"
            },
            "features": [],
            "tech_overrides": {}
        }
        
        # Gather features
        self._print_info("Enter project features (empty line to finish):")
        while True:
            feature = Prompt.ask("Feature", default="") if HAS_RICH else input("Feature: ")
            if not feature:
                break
            config["features"].append(feature)
        
        return config
    
    def _gather_requirements(self):
        """Gather additional requirements"""
        self._print_header("Additional Requirements")
        
        # Performance requirements
        if Confirm.ask("Add performance requirements?", default=False):
            self.project_config["performance"] = {
                "response_time": Prompt.ask("Max API response time", default="200ms") if HAS_RICH else input("Max API response time [200ms]: ") or "200ms",
                "concurrent_users": IntPrompt.ask("Expected concurrent users", default=100) if HAS_RICH else int(input("Expected concurrent users [100]: ") or 100),
                "uptime": Prompt.ask("Required uptime", default="99.9%") if HAS_RICH else input("Required uptime [99.9%]: ") or "99.9%"
            }
        
        # Security requirements
        if Confirm.ask("Add security requirements?", default=False):
            security_features = []
            security_options = [
                "OWASP compliance",
                "PCI DSS compliance",
                "GDPR compliance",
                "SOC2 compliance",
                "End-to-end encryption",
                "Multi-factor authentication",
                "API rate limiting",
                "DDoS protection"
            ]
            
            self._print_info("Select security requirements:")
            for i, option in enumerate(security_options, 1):
                if Confirm.ask(f"  {option}?", default=False):
                    security_features.append(option)
            
            if security_features:
                self.project_config["security"] = security_features
        
        # Integration requirements
        if Confirm.ask("Add third-party integrations?", default=False):
            integrations = []
            self._print_info("Enter integrations (empty line to finish):")
            while True:
                integration = Prompt.ask("Integration", default="") if HAS_RICH else input("Integration: ")
                if not integration:
                    break
                integrations.append(integration)
            
            if integrations:
                self.project_config["integrations"] = integrations
    
    def _configure_tech_stack(self):
        """Configure technology stack"""
        self._print_header("Technology Configuration")
        
        # Only ask if not already configured
        if "tech_overrides" not in self.project_config or not self.project_config["tech_overrides"]:
            self.project_config["tech_overrides"] = {}
        
        if Confirm.ask("Customize technology stack?", default=False):
            # Frontend
            if Confirm.ask("Configure frontend?", default=True):
                self.project_config["tech_overrides"]["frontend"] = {
                    "framework": Prompt.ask("Frontend framework", default="React + TypeScript") if HAS_RICH else input("Frontend framework [React + TypeScript]: ") or "React + TypeScript",
                    "styling": Prompt.ask("Styling solution", default="Tailwind CSS") if HAS_RICH else input("Styling [Tailwind CSS]: ") or "Tailwind CSS"
                }
            
            # Backend
            if Confirm.ask("Configure backend?", default=True):
                self.project_config["tech_overrides"]["backend"] = {
                    "framework": Prompt.ask("Backend framework", default="FastAPI") if HAS_RICH else input("Backend framework [FastAPI]: ") or "FastAPI",
                    "database": Prompt.ask("Database", default="PostgreSQL") if HAS_RICH else input("Database [PostgreSQL]: ") or "PostgreSQL"
                }
            
            # Deployment
            if Confirm.ask("Configure deployment?", default=True):
                self.project_config["tech_overrides"]["deployment"] = Prompt.ask(
                    "Deployment platform",
                    default="Docker + AWS"
                ) if HAS_RICH else input("Deployment [Docker + AWS]: ") or "Docker + AWS"
    
    def _set_constraints(self):
        """Set project constraints"""
        self._print_header("Project Constraints")
        
        constraints = {}
        
        # Budget
        budget = Prompt.ask("Budget (or 'unlimited')", default="unlimited") if HAS_RICH else input("Budget (or 'unlimited') [unlimited]: ") or "unlimited"
        if budget != "unlimited":
            constraints["budget"] = budget
        
        # Team size
        team_size = IntPrompt.ask("Team size", default=1) if HAS_RICH else int(input("Team size [1]: ") or 1)
        constraints["team_size"] = team_size
        
        # Deployment target
        if "deployment" not in self.project_config.get("tech_overrides", {}):
            deployment = Prompt.ask(
                "Deployment target",
                choices=["AWS", "Azure", "GCP", "Vercel", "Heroku", "Self-hosted"],
                default="AWS"
            ) if HAS_RICH else input("Deployment target [AWS]: ") or "AWS"
            constraints["deployment"] = deployment
        
        self.project_config["constraints"] = constraints
        
        # Success metrics
        self._print_header("Success Metrics")
        metrics = []
        
        self._print_info("Define success metrics (empty line to finish):")
        while True:
            metric = Prompt.ask("Success metric", default="") if HAS_RICH else input("Success metric: ")
            if not metric:
                break
            metrics.append(metric)
        
        if metrics:
            self.project_config["success_metrics"] = metrics
    
    def _review_configuration(self) -> bool:
        """Review and confirm configuration"""
        self._print_header("Review Configuration")
        
        # Generate YAML preview
        yaml_content = yaml.dump(self.project_config, default_flow_style=False, sort_keys=False)
        
        if HAS_RICH:
            # Create a syntax-highlighted preview
            from rich.syntax import Syntax
            syntax = Syntax(yaml_content, "yaml", theme="monokai", line_numbers=True)
            
            panel = Panel(
                syntax,
                title="[bold]Requirements Configuration[/bold]",
                border_style="green"
            )
            self.console.print(panel)
            
            # Cost estimation
            self._show_cost_estimate()
            
        else:
            print("\n" + "="*60)
            print("Requirements Configuration:")
            print("="*60)
            print(yaml_content)
        
        return Confirm.ask("\nProceed with this configuration?", default=True)
    
    def _show_cost_estimate(self):
        """Show estimated costs"""
        if not HAS_RICH:
            return
        
        # Calculate rough estimates
        feature_count = len(self.project_config.get("features", []))
        complexity = "high" if feature_count > 15 else "medium" if feature_count > 8 else "low"
        
        estimates = {
            "low": {"api_calls": "50-100", "cost": "$1-3", "time": "1-2 hours"},
            "medium": {"api_calls": "100-200", "cost": "$3-7", "time": "2-4 hours"},
            "high": {"api_calls": "200-500", "cost": "$7-15", "time": "4-8 hours"}
        }
        
        est = estimates[complexity]
        
        table = Table(title="Estimated Resource Usage", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Estimate", style="yellow")
        
        table.add_row("Complexity", complexity.capitalize())
        table.add_row("API Calls", est["api_calls"])
        table.add_row("Estimated Cost", est["cost"])
        table.add_row("Execution Time", est["time"])
        table.add_row("Features", str(feature_count))
        
        self.console.print(table)
    
    def _save_configuration(self) -> Path:
        """Save configuration to YAML file"""
        # Generate filename
        project_name = self.project_config["project"]["name"].lower().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"requirements_{project_name}_{timestamp}.yaml"
        
        output_path = Path(filename)
        
        # Save file
        with open(output_path, 'w') as f:
            yaml.dump(self.project_config, f, default_flow_style=False, sort_keys=False)
        
        self._print_success(f"Configuration saved to: {output_path}")
        return output_path
    
    def _show_next_steps(self, config_file: Path):
        """Show next steps to the user"""
        self._print_header("Next Steps")
        
        if HAS_RICH:
            steps = f"""
[bold cyan]Your project configuration is ready![/bold cyan]

To build your project with the agent swarm, run:

[bold yellow]python orchestrate_enhanced.py --requirements={config_file}[/bold yellow]

Or with monitoring dashboard:

[bold yellow]python orchestrate_enhanced.py --requirements={config_file} --dashboard[/bold yellow]

Additional options:
• Add [cyan]--interactive[/cyan] for step-by-step execution
• Add [cyan]--mock[/cyan] to test without API costs
• Add [cyan]--progress[/cyan] for real-time progress tracking
            """
            
            panel = Panel(steps, title="[bold green]Ready to Build![/bold green]", border_style="green")
            self.console.print(panel)
        else:
            print("\n" + "="*60)
            print("Next Steps:")
            print("="*60)
            print(f"Run: python orchestrate_enhanced.py --requirements={config_file}")
            print()
    
    # Helper methods for consistent output
    def _print_header(self, text: str):
        if HAS_RICH:
            self.console.print(f"\n[bold cyan]── {text} ──[/bold cyan]")
        else:
            print(f"\n--- {text} ---")
    
    def _print_info(self, text: str):
        if HAS_RICH:
            self.console.print(f"[dim]{text}[/dim]")
        else:
            print(text)
    
    def _print_success(self, text: str):
        if HAS_RICH:
            self.console.print(f"[green]✓[/green] {text}")
        else:
            print(f"✓ {text}")
    
    def _print_warning(self, text: str):
        if HAS_RICH:
            self.console.print(f"[yellow]⚠[/yellow] {text}")
        else:
            print(f"⚠ {text}")
    
    def _print_error(self, text: str):
        if HAS_RICH:
            self.console.print(f"[red]✗[/red] {text}")
        else:
            print(f"✗ {text}")
    
    def _print_item(self, text: str):
        if HAS_RICH:
            self.console.print(f"  • {text}")
        else:
            print(f"  • {text}")

def main():
    """Main entry point"""
    try:
        wizard = ProjectWizard()
        config = wizard.run()
        
        if config:
            if HAS_RICH:
                console.print("\n[bold green]Project configuration complete![/bold green]")
            else:
                print("\nProject configuration complete!")
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        if HAS_RICH:
            console.print("\n[yellow]Wizard cancelled by user[/yellow]")
        else:
            print("\nWizard cancelled")
        return 1
    except Exception as e:
        if HAS_RICH:
            console.print(f"\n[red]Error: {e}[/red]")
        else:
            print(f"\nError: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())