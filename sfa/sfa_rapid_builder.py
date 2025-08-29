#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
#   "pyyaml>=6.0",
# ]
# ///

"""
Single File Agent: Rapid Builder

Standalone execution of the rapid-builder agent for fast prototyping and scaffolding.

Example Usage:
    uv run sfa/sfa_rapid_builder.py --prompt "Build a REST API" --output api_code/
    uv run sfa/sfa_rapid_builder.py --requirements requirements.yaml --scaffold full
    uv run sfa/sfa_rapid_builder.py --prompt "Create auth system" --feature auth --verbose
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
You are an expert rapid prototyper specializing in quickly building robust, scalable applications.
You excel at scaffolding projects, generating boilerplate code, and implementing core features rapidly.
</role>

<context>
Project Requirements: {{requirements}}
Feature to Build: {{feature}}
</context>

<instructions>
1. Analyze requirements and determine optimal structure
2. Generate clean, maintainable boilerplate code
3. Implement core features with best practices
4. Set up proper project scaffolding
5. Create working prototypes quickly
6. Use tools to save generated code and structure
</instructions>

<tools>
    <tool>
        <name>create_scaffold</name>
        <description>Generate project structure and directories</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why this structure is optimal</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>structure</name>
                <type>object</type>
                <description>Directory structure to create</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>tech_stack</name>
                <type>object</type>
                <description>Technology choices for the project</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>implement_feature</name>
        <description>Implement a specific feature with code</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Implementation approach reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>feature_name</name>
                <type>string</type>
                <description>Name of the feature</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>code_files</name>
                <type>object</type>
                <description>Dictionary of filename to code content</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>dependencies</name>
                <type>array</type>
                <description>Required dependencies</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>setup_database</name>
        <description>Set up database models and migrations</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Database design reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>models</name>
                <type>object</type>
                <description>Database models definition</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>migrations</name>
                <type>array</type>
                <description>Migration scripts</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>create_api_endpoints</name>
        <description>Generate REST API endpoints</description>
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
                <description>List of endpoint definitions</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>middleware</name>
                <type>array</type>
                <description>Required middleware</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>generate_config</name>
        <description>Generate configuration files</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Configuration choices reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>configs</name>
                <type>object</type>
                <description>Configuration files to generate</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>save_codebase</name>
        <description>Save all generated code to disk</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why saving in this structure</description>
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
                <description>All files to save (path: content)</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
</tools>

<task>
{{task}}
</task>

Remember to:
- Generate production-ready boilerplate
- Follow best practices for chosen tech stack
- Include proper error handling
- Set up testing infrastructure
- Create clear, maintainable code
- Save all generated code using save_codebase tool
"""

class RapidBuilderAgent:
    """Single File Agent for Rapid Prototyping and Scaffolding"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if HAS_ANTHROPIC and self.api_key else None
        self.generated_files = {}
        self.project_structure = {}
        
    def create_scaffold(self, reasoning: str, structure: Dict, tech_stack: Dict) -> str:
        """Generate project structure"""
        console.print(Panel(
            f"[blue]Creating Scaffold[/blue]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Tech Stack:[/dim] {list(tech_stack.keys())}",
            border_style="blue"
        ))
        
        self.project_structure = structure
        
        # Generate base structure files
        if "frontend" in tech_stack and tech_stack["frontend"] == "React":
            self._generate_react_scaffold()
        if "backend" in tech_stack and tech_stack["backend"] in ["FastAPI", "Express"]:
            self._generate_backend_scaffold(tech_stack["backend"])
        
        return f"Scaffold created with {len(structure)} directories"
    
    def implement_feature(self, reasoning: str, feature_name: str, code_files: Dict, dependencies: List[str] = None) -> str:
        """Implement a specific feature"""
        console.print(Panel(
            f"[green]Implementing Feature[/green]\n"
            f"[bold]Feature:[/bold] {feature_name}\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Files:[/dim] {len(code_files)} files",
            border_style="green"
        ))
        
        # Store generated code
        for filepath, content in code_files.items():
            self.generated_files[filepath] = content
        
        return f"Feature '{feature_name}' implemented with {len(code_files)} files"
    
    def setup_database(self, reasoning: str, models: Dict, migrations: List[str] = None) -> str:
        """Set up database models"""
        console.print(Panel(
            f"[yellow]Setting up Database[/yellow]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Models:[/dim] {list(models.keys())}",
            border_style="yellow"
        ))
        
        # Generate model files
        for model_name, model_def in models.items():
            self.generated_files[f"models/{model_name}.py"] = model_def
        
        return f"Database setup with {len(models)} models"
    
    def create_api_endpoints(self, reasoning: str, endpoints: List, middleware: List[str] = None) -> str:
        """Generate API endpoints"""
        console.print(Panel(
            f"[cyan]Creating API Endpoints[/cyan]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Endpoints:[/dim] {len(endpoints)} defined",
            border_style="cyan"
        ))
        
        # Generate endpoint code
        api_code = self._generate_api_code(endpoints, middleware)
        self.generated_files["api/endpoints.py"] = api_code
        
        return f"Created {len(endpoints)} API endpoints"
    
    def generate_config(self, reasoning: str, configs: Dict) -> str:
        """Generate configuration files"""
        console.print(Panel(
            f"[magenta]Generating Config[/magenta]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Configs:[/dim] {list(configs.keys())}",
            border_style="magenta"
        ))
        
        for config_name, config_content in configs.items():
            self.generated_files[config_name] = config_content
        
        return f"Generated {len(configs)} config files"
    
    def save_codebase(self, reasoning: str, output_dir: str, files: Dict) -> str:
        """Save all generated code"""
        console.print(Panel(
            f"[green]Saving Codebase[/green]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Output:[/dim] {output_dir}",
            border_style="green"
        ))
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save all files
        for filepath, content in files.items():
            file_path = output_path / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        # Save project manifest
        manifest = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "files": list(files.keys()),
            "structure": self.project_structure
        }
        
        manifest_path = output_path / "project_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return f"Codebase saved to {output_dir} ({len(files)} files)"
    
    def _generate_react_scaffold(self):
        """Generate React boilerplate"""
        self.generated_files["package.json"] = json.dumps({
            "name": "app-frontend",
            "version": "1.0.0",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "test": "jest"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            }
        }, indent=2)
        
        self.generated_files["src/App.tsx"] = """import React from 'react';

function App() {
  return (
    <div className="App">
      <h1>Rapid Builder App</h1>
    </div>
  );
}

export default App;"""
    
    def _generate_backend_scaffold(self, framework: str):
        """Generate backend boilerplate"""
        if framework == "FastAPI":
            self.generated_files["main.py"] = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Rapid Builder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Rapid Builder API"}"""
    
    def _generate_api_code(self, endpoints: List, middleware: List = None) -> str:
        """Generate API endpoint code"""
        code = "# Generated API Endpoints\n\n"
        for endpoint in endpoints:
            code += f"# {endpoint}\n"
        return code
    
    def run(self, prompt: str, requirements: Dict, output_dir: str, compute_limit: int = 10) -> bool:
        """Run the agent with Claude API or simulation"""
        
        if not self.client:
            return self._run_simulation(prompt, requirements, output_dir)
        
        # Prepare the full prompt
        full_prompt = AGENT_PROMPT.replace("{{requirements}}", json.dumps(requirements, indent=2))
        full_prompt = full_prompt.replace("{{feature}}", prompt)
        full_prompt = full_prompt.replace("{{task}}", prompt)
        
        messages = [{"role": "user", "content": full_prompt}]
        
        # Tool definitions for Anthropic
        tools = [
            {
                "name": "create_scaffold",
                "description": "Generate project structure and directories",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "structure": {"type": "object"},
                        "tech_stack": {"type": "object"}
                    },
                    "required": ["reasoning", "structure", "tech_stack"]
                }
            },
            {
                "name": "implement_feature",
                "description": "Implement a specific feature with code",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "feature_name": {"type": "string"},
                        "code_files": {"type": "object"},
                        "dependencies": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["reasoning", "feature_name", "code_files"]
                }
            },
            {
                "name": "setup_database",
                "description": "Set up database models and migrations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "models": {"type": "object"},
                        "migrations": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["reasoning", "models"]
                }
            },
            {
                "name": "create_api_endpoints",
                "description": "Generate REST API endpoints",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "endpoints": {"type": "array"},
                        "middleware": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["reasoning", "endpoints"]
                }
            },
            {
                "name": "generate_config",
                "description": "Generate configuration files",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "configs": {"type": "object"}
                    },
                    "required": ["reasoning", "configs"]
                }
            },
            {
                "name": "save_codebase",
                "description": "Save all generated code to disk",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "output_dir": {"type": "string"},
                        "files": {"type": "object"}
                    },
                    "required": ["reasoning", "output_dir", "files"]
                }
            }
        ]
        
        iterations = 0
        console.rule("[yellow]Starting Rapid Builder Agent[/yellow]")
        
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
                        if tool_name == "create_scaffold":
                            result = self.create_scaffold(**tool_args)
                        elif tool_name == "implement_feature":
                            result = self.implement_feature(**tool_args)
                        elif tool_name == "setup_database":
                            result = self.setup_database(**tool_args)
                        elif tool_name == "create_api_endpoints":
                            result = self.create_api_endpoints(**tool_args)
                        elif tool_name == "generate_config":
                            result = self.generate_config(**tool_args)
                        elif tool_name == "save_codebase":
                            tool_args['output_dir'] = output_dir
                            tool_args['files'] = {**self.generated_files, **tool_args.get('files', {})}
                            result = self.save_codebase(**tool_args)
                            console.print(Panel(
                                f"[bold green]Rapid Build Complete![/bold green]\n"
                                f"Generated code saved to: {output_dir}",
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
        self.create_scaffold(
            "Using modern web stack for scalability",
            {"src": {}, "api": {}, "tests": {}, "docs": {}},
            {"frontend": "React", "backend": "FastAPI", "database": "PostgreSQL"}
        )
        
        time.sleep(1)
        
        self.implement_feature(
            "Core authentication with JWT",
            "Authentication",
            {
                "api/auth.py": "# Authentication endpoints",
                "models/user.py": "# User model",
                "utils/jwt.py": "# JWT utilities"
            }
        )
        
        time.sleep(1)
        
        self.setup_database(
            "Normalized schema for scalability",
            {
                "user": "# User model definition",
                "session": "# Session model definition"
            }
        )
        
        time.sleep(1)
        
        self.save_codebase(
            "Saving complete prototype",
            output_dir,
            self.generated_files
        )
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Rapid Builder Agent")
    parser.add_argument("--prompt", "-p", required=True, help="Build prompt or feature description")
    parser.add_argument("--output", "-o", default="generated_code/", help="Output directory")
    parser.add_argument("--requirements", "-r", help="Path to requirements.yaml file")
    parser.add_argument("--scaffold", "-s", choices=["minimal", "full"], default="minimal", help="Scaffold type")
    parser.add_argument("--feature", "-f", help="Specific feature to implement")
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
            "name": "RapidBuild",
            "type": "web_app",
            "description": args.prompt,
            "scaffold": args.scaffold,
            "feature": args.feature
        }
    
    # Run agent
    agent = RapidBuilderAgent()
    success = agent.run(args.prompt, requirements, args.output, args.compute)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()