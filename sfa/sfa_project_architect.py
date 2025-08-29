#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
#   "pyyaml>=6.0",
# ]
# ///

"""
Single File Agent: Project Architect

Standalone execution of the project-architect agent with full reasoning and logging.

Example Usage:
    uv run sfa/sfa_project_architect.py --prompt "Design an e-commerce platform" --output architecture.md
    uv run sfa/sfa_project_architect.py --requirements requirements.yaml --verbose
    uv run sfa/sfa_project_architect.py --prompt "Design auth system" --output auth_design.md --compute 10
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

# Initialize console
console = Console()

# Agent prompt template
AGENT_PROMPT = """<role>
You are an expert system architect specializing in scalable, maintainable application design. 
You excel at translating business requirements into robust technical architectures following industry best practices.
</role>

<context>
Project Requirements: {{requirements}}
</context>

<instructions>
1. Analyze the requirements thoroughly
2. Consider scalability, security, and maintainability
3. Design a comprehensive system architecture
4. Make technology recommendations based on requirements
5. Create clear architectural documentation
6. Use tools to save your design and decisions
</instructions>

<tools>
    <tool>
        <name>analyze_requirements</name>
        <description>Analyze and clarify project requirements</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why this analysis is needed</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>requirements_summary</name>
                <type>string</type>
                <description>Summarized understanding of requirements</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>clarifications_needed</name>
                <type>array</type>
                <description>List of clarifications needed</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>design_architecture</name>
        <description>Create the system architecture design</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Architectural decisions reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>components</name>
                <type>array</type>
                <description>List of system components</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>data_flow</name>
                <type>string</type>
                <description>Description of data flow between components</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>technology_stack</name>
                <type>object</type>
                <description>Recommended technology stack</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>design_database</name>
        <description>Design the database schema</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Database design reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>entities</name>
                <type>array</type>
                <description>List of database entities/tables</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>relationships</name>
                <type>array</type>
                <description>Entity relationships</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>indexes</name>
                <type>array</type>
                <description>Recommended indexes for performance</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>define_api_structure</name>
        <description>Define API endpoints and structure</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>API design reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>endpoints</name>
                <type>array</type>
                <description>List of API endpoints</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>authentication</name>
                <type>string</type>
                <description>Authentication strategy</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>versioning</name>
                <type>string</type>
                <description>API versioning strategy</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>save_architecture</name>
        <description>Save the complete architecture design</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why saving in this format</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>content</name>
                <type>string</type>
                <description>Complete architecture documentation in markdown</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>filename</name>
                <type>string</type>
                <description>Output filename</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
</tools>

<task>
{{task}}
</task>

Remember to:
- Provide reasoning for every decision
- Consider scalability from day one
- Follow SOLID principles
- Design for maintainability
- Include security considerations
- Save your complete design using save_architecture tool
"""

class ProjectArchitectAgent:
    """Single File Agent for Project Architecture Design"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if HAS_ANTHROPIC and self.api_key else None
        self.architecture = {}
        self.decisions = []
        
    def analyze_requirements(self, reasoning: str, requirements_summary: str, clarifications_needed: List[str] = None) -> str:
        """Analyze project requirements"""
        console.print(Panel(
            f"[blue]Analyzing Requirements[/blue]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Summary:[/dim] {requirements_summary[:200]}...",
            border_style="blue"
        ))
        
        self.architecture['requirements'] = {
            'summary': requirements_summary,
            'clarifications': clarifications_needed or []
        }
        
        return f"Requirements analyzed. {len(clarifications_needed or [])} clarifications noted."
    
    def design_architecture(self, reasoning: str, components: List[str], data_flow: str, technology_stack: Dict) -> str:
        """Create system architecture"""
        console.print(Panel(
            f"[green]Designing Architecture[/green]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Components:[/dim] {', '.join(components[:5])}...\n"
            f"[dim]Tech Stack:[/dim] {list(technology_stack.keys())}",
            border_style="green"
        ))
        
        self.architecture['system'] = {
            'components': components,
            'data_flow': data_flow,
            'technology_stack': technology_stack
        }
        
        self.decisions.append({
            'decision': 'System Architecture',
            'reasoning': reasoning,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return f"Architecture designed with {len(components)} components"
    
    def design_database(self, reasoning: str, entities: List[str], relationships: List[str], indexes: List[str] = None) -> str:
        """Design database schema"""
        console.print(Panel(
            f"[yellow]Designing Database[/yellow]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Entities:[/dim] {', '.join(entities[:5])}...\n"
            f"[dim]Relationships:[/dim] {len(relationships)} defined",
            border_style="yellow"
        ))
        
        self.architecture['database'] = {
            'entities': entities,
            'relationships': relationships,
            'indexes': indexes or []
        }
        
        self.decisions.append({
            'decision': 'Database Design',
            'reasoning': reasoning,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return f"Database designed with {len(entities)} entities"
    
    def define_api_structure(self, reasoning: str, endpoints: List[str], authentication: str, versioning: str = "v1") -> str:
        """Define API structure"""
        console.print(Panel(
            f"[cyan]Defining API Structure[/cyan]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Endpoints:[/dim] {len(endpoints)} defined\n"
            f"[dim]Auth:[/dim] {authentication}",
            border_style="cyan"
        ))
        
        self.architecture['api'] = {
            'endpoints': endpoints,
            'authentication': authentication,
            'versioning': versioning
        }
        
        return f"API structure defined with {len(endpoints)} endpoints"
    
    def save_architecture(self, reasoning: str, content: str, filename: str) -> str:
        """Save architecture to file"""
        console.print(Panel(
            f"[green]Saving Architecture[/green]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]File:[/dim] {filename}",
            border_style="green"
        ))
        
        # Save the architecture document
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Also save decisions log
        decisions_file = Path(filename).with_suffix('.decisions.json')
        with open(decisions_file, 'w', encoding='utf-8') as f:
            json.dump({
                'architecture': self.architecture,
                'decisions': self.decisions
            }, f, indent=2, ensure_ascii=False)
        
        return f"Architecture saved to {filename} and {decisions_file}"
    
    def run(self, prompt: str, requirements: Dict, output_file: str, compute_limit: int = 10) -> bool:
        """Run the agent with Claude API or simulation"""
        
        if not self.client:
            return self._run_simulation(prompt, requirements, output_file)
        
        # Prepare the full prompt
        full_prompt = AGENT_PROMPT.replace("{{requirements}}", json.dumps(requirements, indent=2))
        full_prompt = full_prompt.replace("{{task}}", prompt)
        
        messages = [{"role": "user", "content": full_prompt}]
        
        # Tool definitions for Anthropic
        tools = [
            {
                "name": "analyze_requirements",
                "description": "Analyze and clarify project requirements",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "requirements_summary": {"type": "string"},
                        "clarifications_needed": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["reasoning", "requirements_summary"]
                }
            },
            {
                "name": "design_architecture",
                "description": "Create the system architecture design",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "components": {"type": "array", "items": {"type": "string"}},
                        "data_flow": {"type": "string"},
                        "technology_stack": {"type": "object"}
                    },
                    "required": ["reasoning", "components", "data_flow", "technology_stack"]
                }
            },
            {
                "name": "design_database",
                "description": "Design the database schema",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "entities": {"type": "array", "items": {"type": "string"}},
                        "relationships": {"type": "array", "items": {"type": "string"}},
                        "indexes": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["reasoning", "entities", "relationships"]
                }
            },
            {
                "name": "define_api_structure",
                "description": "Define API endpoints and structure",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "endpoints": {"type": "array", "items": {"type": "string"}},
                        "authentication": {"type": "string"},
                        "versioning": {"type": "string"}
                    },
                    "required": ["reasoning", "endpoints", "authentication"]
                }
            },
            {
                "name": "save_architecture",
                "description": "Save the complete architecture design",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "content": {"type": "string"},
                        "filename": {"type": "string"}
                    },
                    "required": ["reasoning", "content", "filename"]
                }
            }
        ]
        
        iterations = 0
        console.rule("[yellow]Starting Project Architect Agent[/yellow]")
        
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
                        if tool_name == "analyze_requirements":
                            result = self.analyze_requirements(**tool_args)
                        elif tool_name == "design_architecture":
                            result = self.design_architecture(**tool_args)
                        elif tool_name == "design_database":
                            result = self.design_database(**tool_args)
                        elif tool_name == "define_api_structure":
                            result = self.define_api_structure(**tool_args)
                        elif tool_name == "save_architecture":
                            tool_args['filename'] = output_file
                            result = self.save_architecture(**tool_args)
                            console.print(Panel(
                                f"[bold green]Architecture Complete![/bold green]\n"
                                f"Saved to: {output_file}",
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
    
    def _run_simulation(self, prompt: str, requirements: Dict, output_file: str) -> bool:
        """Simulate agent execution without API"""
        console.print("[yellow]Running in simulation mode (no API key)[/yellow]")
        
        # Simulate the workflow
        self.analyze_requirements(
            "Need to understand project scope",
            f"Project: {requirements.get('name', 'Unknown')} - {requirements.get('type', 'Unknown type')}",
            ["Budget constraints", "Timeline flexibility"]
        )
        
        time.sleep(1)
        
        self.design_architecture(
            "Creating scalable microservices architecture",
            ["API Gateway", "Auth Service", "Business Logic Service", "Database", "Cache Layer"],
            "Client -> API Gateway -> Services -> Database",
            {"frontend": "React", "backend": "FastAPI", "database": "PostgreSQL"}
        )
        
        time.sleep(1)
        
        self.design_database(
            "Normalized schema for data integrity",
            ["users", "sessions", "products", "orders"],
            ["users->sessions (1:many)", "users->orders (1:many)"],
            ["users.email", "orders.user_id"]
        )
        
        time.sleep(1)
        
        # Save simulated architecture
        content = f"""# System Architecture

## Project: {requirements.get('name', 'Project')}

### Requirements Summary
{json.dumps(requirements, indent=2)}

### System Components
- API Gateway
- Authentication Service
- Business Logic Service
- PostgreSQL Database
- Redis Cache

### Technology Stack
- Frontend: React + TypeScript
- Backend: FastAPI
- Database: PostgreSQL
- Cache: Redis

### API Structure
- /api/v1/auth
- /api/v1/users
- /api/v1/products

*Generated in simulation mode*
"""
        
        self.save_architecture(
            "Saving simulated architecture",
            content,
            output_file
        )
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Project Architect Agent")
    parser.add_argument("--prompt", "-p", required=True, help="Architecture design prompt")
    parser.add_argument("--output", "-o", default="architecture.md", help="Output file path")
    parser.add_argument("--requirements", "-r", help="Path to requirements.yaml file")
    parser.add_argument("--compute", "-c", type=int, default=10, help="Max compute iterations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Load requirements
    requirements = {}
    if args.requirements and Path(args.requirements).exists():
        with open(args.requirements) as f:
            requirements = yaml.safe_load(f)
    else:
        # Basic requirements from prompt
        requirements = {
            "name": "Project",
            "type": "web_app",
            "description": args.prompt
        }
    
    # Run agent
    agent = ProjectArchitectAgent()
    success = agent.run(args.prompt, requirements, args.output, args.compute)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()