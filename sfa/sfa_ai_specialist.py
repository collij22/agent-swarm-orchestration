#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
#   "pyyaml>=6.0",
# ]
# ///

"""
Single File Agent: AI Specialist

Standalone execution of the ai-specialist agent for AI/ML integration and LLM implementation.

Example Usage:
    uv run sfa/sfa_ai_specialist.py --prompt "Add AI chat to app" --output ai_system/
    uv run sfa/sfa_ai_specialist.py --requirements requirements.yaml --feature rag --verbose
    uv run sfa/sfa_ai_specialist.py --prompt "Implement recommendation system" --model gpt-4 --output ml_code/
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
You are an expert AI/ML specialist focusing on LLM integration, intelligent automation, and machine learning implementation.
You excel at designing AI systems, implementing RAG pipelines, and optimizing model performance.
</role>

<context>
Project Requirements: {{requirements}}
AI Feature: {{ai_feature}}
Model Preferences: {{model_prefs}}
</context>

<instructions>
1. Analyze AI/ML requirements and constraints
2. Design optimal AI architecture for the use case
3. Implement LLM integration with proper error handling
4. Set up vector databases and embeddings if needed
5. Optimize prompts and model parameters
6. Create production-ready AI systems
</instructions>

<tools>
    <tool>
        <name>design_ai_architecture</name>
        <description>Design the AI system architecture</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Architecture design reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>components</name>
                <type>array</type>
                <description>AI system components</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>data_flow</name>
                <type>string</type>
                <description>Data flow through AI pipeline</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>models</name>
                <type>object</type>
                <description>ML/LLM models to use</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>implement_llm</name>
        <description>Implement LLM integration</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>LLM implementation approach</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>provider</name>
                <type>string</type>
                <description>LLM provider (OpenAI, Anthropic, etc)</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>implementation_files</name>
                <type>object</type>
                <description>LLM integration code files</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>config</name>
                <type>object</type>
                <description>LLM configuration settings</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>create_rag_pipeline</name>
        <description>Build Retrieval Augmented Generation pipeline</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>RAG pipeline design reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>components</name>
                <type>object</type>
                <description>RAG pipeline components</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>retrieval_strategy</name>
                <type>string</type>
                <description>Document retrieval strategy</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>chunking_config</name>
                <type>object</type>
                <description>Document chunking configuration</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>setup_embeddings</name>
        <description>Configure embeddings and vector database</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Embeddings setup reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>embedding_model</name>
                <type>string</type>
                <description>Embedding model to use</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>vector_db</name>
                <type>string</type>
                <description>Vector database (Pinecone, Chroma, etc)</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>implementation</name>
                <type>object</type>
                <description>Embeddings implementation code</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>optimize_prompts</name>
        <description>Optimize prompts for better results</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Prompt optimization strategy</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>prompts</name>
                <type>object</type>
                <description>Optimized prompt templates</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>test_cases</name>
                <type>array</type>
                <description>Test cases for validation</description>
                <required>false</required>
            </parameter>
            <parameter>
                <name>metrics</name>
                <type>object</type>
                <description>Performance metrics</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>implement_ml_model</name>
        <description>Implement traditional ML models</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>ML model selection reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>model_type</name>
                <type>string</type>
                <description>Type of ML model</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>training_code</name>
                <type>string</type>
                <description>Model training implementation</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>inference_code</name>
                <type>string</type>
                <description>Model inference implementation</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>save_ai_system</name>
        <description>Save the complete AI system implementation</description>
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
                <description>All AI system files to save</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>documentation</name>
                <type>string</type>
                <description>AI system documentation</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
</tools>

<task>
{{task}}
</task>

Remember to:
- Choose appropriate models for the use case
- Implement proper error handling and fallbacks
- Optimize for latency and cost
- Include monitoring and observability
- Follow AI safety best practices
- Document model limitations
"""

class AISpecialistAgent:
    """Single File Agent for AI/ML Integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if HAS_ANTHROPIC and self.api_key else None
        self.ai_files = {}
        self.architecture = {}
        self.prompts = {}
        
    def design_ai_architecture(self, reasoning: str, components: List[str], data_flow: str, models: Dict) -> str:
        """Design AI system architecture"""
        console.print(Panel(
            f"[blue]Designing AI Architecture[/blue]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Components:[/dim] {', '.join(components[:3])}...\n"
            f"[dim]Models:[/dim] {list(models.keys())}",
            border_style="blue"
        ))
        
        self.architecture = {
            'components': components,
            'data_flow': data_flow,
            'models': models
        }
        
        # Display architecture
        table = Table(title="AI System Components")
        table.add_column("Component", style="cyan")
        table.add_column("Purpose", style="green")
        
        for component in components[:5]:
            table.add_row(component, "AI Processing")
        
        console.print(table)
        
        return f"AI architecture designed with {len(components)} components"
    
    def implement_llm(self, reasoning: str, provider: str, implementation_files: Dict, config: Dict = None) -> str:
        """Implement LLM integration"""
        console.print(Panel(
            f"[green]Implementing LLM[/green]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Provider:[/dim] {provider}\n"
            f"[dim]Files:[/dim] {len(implementation_files)}",
            border_style="green"
        ))
        
        self.ai_files.update(implementation_files)
        
        if config:
            self.ai_files["llm_config.json"] = json.dumps(config, indent=2)
        
        return f"LLM integration implemented for {provider}"
    
    def create_rag_pipeline(self, reasoning: str, components: Dict, retrieval_strategy: str, chunking_config: Dict = None) -> str:
        """Build RAG pipeline"""
        console.print(Panel(
            f"[yellow]Creating RAG Pipeline[/yellow]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Strategy:[/dim] {retrieval_strategy}\n"
            f"[dim]Components:[/dim] {list(components.keys())}",
            border_style="yellow"
        ))
        
        # Generate RAG implementation
        rag_code = self._generate_rag_code(components, retrieval_strategy, chunking_config)
        self.ai_files["rag_pipeline.py"] = rag_code
        
        return f"RAG pipeline created with {retrieval_strategy} strategy"
    
    def setup_embeddings(self, reasoning: str, embedding_model: str, vector_db: str, implementation: Dict) -> str:
        """Set up embeddings and vector database"""
        console.print(Panel(
            f"[cyan]Setting up Embeddings[/cyan]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Model:[/dim] {embedding_model}\n"
            f"[dim]Vector DB:[/dim] {vector_db}",
            border_style="cyan"
        ))
        
        self.ai_files.update(implementation)
        
        return f"Embeddings configured with {embedding_model} and {vector_db}"
    
    def optimize_prompts(self, reasoning: str, prompts: Dict, test_cases: List = None, metrics: Dict = None) -> str:
        """Optimize prompts"""
        console.print(Panel(
            f"[magenta]Optimizing Prompts[/magenta]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Prompts:[/dim] {len(prompts)} templates",
            border_style="magenta"
        ))
        
        self.prompts = prompts
        
        # Save optimized prompts
        self.ai_files["prompts.json"] = json.dumps(prompts, indent=2)
        
        # Display metrics if available
        if metrics:
            table = Table(title="Prompt Performance Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for metric, value in metrics.items():
                table.add_row(metric, str(value))
            
            console.print(table)
        
        return f"Optimized {len(prompts)} prompt templates"
    
    def implement_ml_model(self, reasoning: str, model_type: str, training_code: str, inference_code: str) -> str:
        """Implement traditional ML model"""
        console.print(Panel(
            f"[blue]Implementing ML Model[/blue]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Model Type:[/dim] {model_type}",
            border_style="blue"
        ))
        
        self.ai_files["ml_training.py"] = training_code
        self.ai_files["ml_inference.py"] = inference_code
        
        return f"ML model ({model_type}) implemented"
    
    def save_ai_system(self, reasoning: str, output_dir: str, files: Dict, documentation: str = None) -> str:
        """Save AI system implementation"""
        console.print(Panel(
            f"[green]Saving AI System[/green]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Output:[/dim] {output_dir}",
            border_style="green"
        ))
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Merge all files
        all_files = {**self.ai_files, **files}
        
        # Save all files
        for filepath, content in all_files.items():
            file_path = output_path / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        # Save documentation
        if documentation:
            doc_path = output_path / "AI_SYSTEM_DOCS.md"
            doc_path.write_text(documentation)
        
        # Save manifest
        manifest = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "architecture": self.architecture,
            "prompts": list(self.prompts.keys()),
            "files": list(all_files.keys())
        }
        
        manifest_path = output_path / "ai_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return f"AI system saved to {output_dir} ({len(all_files)} files)"
    
    def _generate_rag_code(self, components: Dict, strategy: str, chunking_config: Dict = None) -> str:
        """Generate RAG pipeline code"""
        code = f"""# RAG Pipeline Implementation
# Strategy: {strategy}

import os
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class RAGConfig:
    chunk_size: int = {chunking_config.get('chunk_size', 500) if chunking_config else 500}
    chunk_overlap: int = {chunking_config.get('overlap', 50) if chunking_config else 50}
    top_k: int = 5
    
class RAGPipeline:
    def __init__(self):
        self.config = RAGConfig()
        
    def retrieve(self, query: str) -> List[str]:
        # Retrieval implementation
        pass
        
    def generate(self, query: str, context: List[str]) -> str:
        # Generation implementation
        pass
"""
        return code
    
    def run(self, prompt: str, requirements: Dict, output_dir: str, compute_limit: int = 10) -> bool:
        """Run the agent with Claude API or simulation"""
        
        if not self.client:
            return self._run_simulation(prompt, requirements, output_dir)
        
        # Prepare the full prompt
        full_prompt = AGENT_PROMPT.replace("{{requirements}}", json.dumps(requirements, indent=2))
        full_prompt = full_prompt.replace("{{ai_feature}}", requirements.get("feature", "general AI"))
        full_prompt = full_prompt.replace("{{model_prefs}}", json.dumps(requirements.get("models", {})))
        full_prompt = full_prompt.replace("{{task}}", prompt)
        
        messages = [{"role": "user", "content": full_prompt}]
        
        # Tool definitions for Anthropic
        tools = [
            {
                "name": "design_ai_architecture",
                "description": "Design the AI system architecture",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "components": {"type": "array", "items": {"type": "string"}},
                        "data_flow": {"type": "string"},
                        "models": {"type": "object"}
                    },
                    "required": ["reasoning", "components", "data_flow", "models"]
                }
            },
            {
                "name": "implement_llm",
                "description": "Implement LLM integration",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "provider": {"type": "string"},
                        "implementation_files": {"type": "object"},
                        "config": {"type": "object"}
                    },
                    "required": ["reasoning", "provider", "implementation_files"]
                }
            },
            {
                "name": "create_rag_pipeline",
                "description": "Build Retrieval Augmented Generation pipeline",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "components": {"type": "object"},
                        "retrieval_strategy": {"type": "string"},
                        "chunking_config": {"type": "object"}
                    },
                    "required": ["reasoning", "components", "retrieval_strategy"]
                }
            },
            {
                "name": "setup_embeddings",
                "description": "Configure embeddings and vector database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "embedding_model": {"type": "string"},
                        "vector_db": {"type": "string"},
                        "implementation": {"type": "object"}
                    },
                    "required": ["reasoning", "embedding_model", "vector_db", "implementation"]
                }
            },
            {
                "name": "optimize_prompts",
                "description": "Optimize prompts for better results",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "prompts": {"type": "object"},
                        "test_cases": {"type": "array"},
                        "metrics": {"type": "object"}
                    },
                    "required": ["reasoning", "prompts"]
                }
            },
            {
                "name": "implement_ml_model",
                "description": "Implement traditional ML models",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "model_type": {"type": "string"},
                        "training_code": {"type": "string"},
                        "inference_code": {"type": "string"}
                    },
                    "required": ["reasoning", "model_type", "training_code", "inference_code"]
                }
            },
            {
                "name": "save_ai_system",
                "description": "Save the complete AI system implementation",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "output_dir": {"type": "string"},
                        "files": {"type": "object"},
                        "documentation": {"type": "string"}
                    },
                    "required": ["reasoning", "output_dir", "files"]
                }
            }
        ]
        
        iterations = 0
        console.rule("[yellow]Starting AI Specialist Agent[/yellow]")
        
        while iterations < compute_limit:
            iterations += 1
            console.rule(f"[blue]Iteration {iterations}/{compute_limit}[/blue]")
            
            try:
                response = self.client.messages.create(
                    model="claude-3-opus-20240229",  # Use Opus for AI tasks
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
                        if tool_name == "design_ai_architecture":
                            result = self.design_ai_architecture(**tool_args)
                        elif tool_name == "implement_llm":
                            result = self.implement_llm(**tool_args)
                        elif tool_name == "create_rag_pipeline":
                            result = self.create_rag_pipeline(**tool_args)
                        elif tool_name == "setup_embeddings":
                            result = self.setup_embeddings(**tool_args)
                        elif tool_name == "optimize_prompts":
                            result = self.optimize_prompts(**tool_args)
                        elif tool_name == "implement_ml_model":
                            result = self.implement_ml_model(**tool_args)
                        elif tool_name == "save_ai_system":
                            tool_args['output_dir'] = output_dir
                            result = self.save_ai_system(**tool_args)
                            console.print(Panel(
                                f"[bold green]AI System Complete![/bold green]\n"
                                f"Implementation saved to: {output_dir}",
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
        self.design_ai_architecture(
            "Scalable AI architecture for production",
            ["LLM Gateway", "Vector Store", "Prompt Manager", "Cache Layer", "Monitor"],
            "User -> Gateway -> LLM/Vector Store -> Response",
            {"primary": "GPT-4", "fallback": "Claude", "embeddings": "text-embedding-ada-002"}
        )
        
        time.sleep(1)
        
        self.implement_llm(
            "Using OpenAI with Anthropic fallback",
            "OpenAI",
            {
                "llm_client.py": "# LLM client implementation",
                "llm_utils.py": "# LLM utility functions",
                "prompts.py": "# Prompt templates"
            },
            {"model": "gpt-4", "temperature": 0.7, "max_tokens": 2000}
        )
        
        time.sleep(1)
        
        self.create_rag_pipeline(
            "Hybrid search for better retrieval",
            {"retriever": "Vector + BM25", "reranker": "Cross-encoder"},
            "semantic_search",
            {"chunk_size": 500, "overlap": 50}
        )
        
        time.sleep(1)
        
        self.optimize_prompts(
            "Chain-of-thought for complex reasoning",
            {
                "chat": "You are a helpful assistant...",
                "summary": "Summarize the following text...",
                "analysis": "Analyze the data and provide insights..."
            },
            metrics={"accuracy": 0.92, "latency": "1.2s"}
        )
        
        time.sleep(1)
        
        # Generate documentation
        doc = """# AI System Documentation

## Architecture
- LLM Gateway with fallback
- Vector Store for RAG
- Prompt optimization
- Performance monitoring

## Models
- Primary: GPT-4
- Fallback: Claude
- Embeddings: text-embedding-ada-002

*Generated in simulation mode*
"""
        
        self.save_ai_system(
            "Production-ready AI system",
            output_dir,
            self.ai_files,
            doc
        )
        
        return True

def main():
    parser = argparse.ArgumentParser(description="AI Specialist Agent")
    parser.add_argument("--prompt", "-p", required=True, help="AI feature to implement")
    parser.add_argument("--output", "-o", default="ai_system/", help="Output directory")
    parser.add_argument("--requirements", "-r", help="Path to requirements.yaml file")
    parser.add_argument("--model", "-m", help="Preferred LLM model")
    parser.add_argument("--feature", "-f", choices=["chat", "rag", "ml", "vision"], help="AI feature type")
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
            "name": "AISystem",
            "type": "ai_integration",
            "description": args.prompt,
            "feature": args.feature or "general",
            "models": {"preferred": args.model} if args.model else {}
        }
    
    # Run agent
    agent = AISpecialistAgent()
    success = agent.run(args.prompt, requirements, args.output, args.compute)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()