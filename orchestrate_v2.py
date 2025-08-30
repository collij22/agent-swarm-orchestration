#!/usr/bin/env python3
"""
Agent Swarm Orchestrator V2 - Enhanced with logging and real execution

Features:
- Real Claude API integration
- Comprehensive logging with reasoning
- Session management and replay
- Interactive and checkpoint modes
- Rich console output

Usage:
    uv run orchestrate_v2.py --project-type=web_app --requirements=requirements.yaml --verbose
    uv run orchestrate_v2.py --chain=project-architect,rapid-builder --interactive
    uv run orchestrate_v2.py --replay sessions/session_*.json
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
from datetime import datetime

# Load environment variables from .env file if it exists
env_file = Path(".env")
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.agent_logger import ReasoningLogger, create_new_session
from lib.agent_runtime import AnthropicAgentRunner, AgentContext, ModelType, Tool, create_standard_tools, create_quality_tools

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("Warning: Rich not installed. Install with: pip install rich")

console = Console() if HAS_RICH else None

class EnhancedOrchestrator:
    """Enhanced orchestrator with logging and real agent execution"""
    
    def __init__(self, api_key: Optional[str] = None, session_id: Optional[str] = None):
        self.logger = create_new_session(session_id)
        self.runtime = AnthropicAgentRunner(api_key, self.logger)
        self.agents = self._load_agent_configs()
        self.workflows = self._define_workflows()
        self.checkpoints_dir = Path("checkpoints")
        self.checkpoints_dir.mkdir(exist_ok=True)
        
        # Register standard tools
        for tool in create_standard_tools():
            self.runtime.register_tool(tool)
        
        # Register quality validation tools
        for tool in create_quality_tools():
            self.runtime.register_tool(tool)
        
        # Add orchestration-specific tools
        self._register_orchestration_tools()
    
    def _load_agent_configs(self) -> Dict:
        """Load agent configurations and prompts"""
        agents = {}
        agent_dir = Path(".claude/agents")
        
        # Load each agent's prompt from their .md files
        for agent_file in agent_dir.glob("*.md"):
            agent_name = agent_file.stem
            content = agent_file.read_text()
            
            # Parse YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1])
                    prompt = parts[2].strip()
                    
                    agents[agent_name] = {
                        "name": agent_name,
                        "model": frontmatter.get("model", "sonnet"),
                        "tools": frontmatter.get("tools", []),
                        "prompt": prompt,
                        "description": frontmatter.get("description", "")
                    }
        
        return agents
    
    def _define_workflows(self) -> Dict:
        """Define orchestration patterns"""
        return {
            "web_app": [
                ["requirements-analyst"],
                ["project-architect", "database-expert"],
                ["rapid-builder"],
                ["frontend-specialist", "api-integrator", "documentation-writer"],
                ["ai-specialist"],
                ["quality-guardian"],
                ["performance-optimizer"],
                ["devops-engineer"]
            ],
            "api_service": [
                ["requirements-analyst"],
                ["project-architect", "database-expert"],
                ["rapid-builder"],
                ["api-integrator", "documentation-writer"],
                ["quality-guardian"],
                ["devops-engineer"]
            ],
            "full_stack_api": [
                ["requirements-analyst"],
                ["project-architect", "database-expert"],
                ["rapid-builder"],
                ["api-integrator", "documentation-writer"],
                ["frontend-specialist"],  # Added frontend for full-stack
                ["ai-specialist"],  # AI features if needed
                ["quality-guardian"],
                ["performance-optimizer"],
                ["devops-engineer"]
            ],
            "ai_solution": [
                ["requirements-analyst"],
                ["project-architect", "ai-specialist"],
                ["rapid-builder"],
                ["api-integrator", "performance-optimizer"],
                ["quality-guardian"],
                ["documentation-writer"]
            ]
        }
    
    def _register_orchestration_tools(self):
        """Register orchestration-specific tools"""
        
        async def invoke_agent(reasoning: str, agent_name: str, task: str, context: AgentContext) -> str:
            """Invoke another agent"""
            self.logger.log_reasoning("orchestrator", reasoning, f"Invoking {agent_name}")
            
            if agent_name in self.agents:
                success, result, _ = await self.runtime.run_agent_async(
                    agent_name,
                    self.agents[agent_name]["prompt"] + f"\n\nSpecific task: {task}",
                    context,
                    model=self._get_model(self.agents[agent_name]["model"])
                )
                return f"Agent {agent_name} {'completed' if success else 'failed'}: {result[:500]}"
            return f"Unknown agent: {agent_name}"
        
        self.runtime.register_tool(Tool(
            name="invoke_agent",
            description="Invoke another agent for a specific task",
            parameters={
                "agent_name": {"type": "string", "description": "Name of agent to invoke", "required": True},
                "task": {"type": "string", "description": "Specific task for the agent", "required": True}
            },
            function=invoke_agent
        ))
        
        async def checkpoint_progress(reasoning: str, checkpoint_name: str, state: Dict) -> str:
            """Save checkpoint of current progress"""
            checkpoint_file = self.checkpoints_dir / f"{checkpoint_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(state, f, indent=2)
            self.logger.log_reasoning("orchestrator", reasoning, f"Checkpoint saved: {checkpoint_file}")
            return f"Checkpoint saved: {checkpoint_file}"
        
        self.runtime.register_tool(Tool(
            name="checkpoint_progress",
            description="Save checkpoint of current workflow progress",
            parameters={
                "checkpoint_name": {"type": "string", "description": "Name for checkpoint", "required": True},
                "state": {"type": "object", "description": "Current state to save", "required": True}
            },
            function=checkpoint_progress
        ))
    
    def _get_model(self, model_name: str) -> ModelType:
        """Convert model name to ModelType"""
        model_map = {
            "haiku": ModelType.HAIKU,
            "sonnet": ModelType.SONNET,
            "opus": ModelType.OPUS
        }
        return model_map.get(model_name, ModelType.SONNET)
    
    def _detect_frontend_requirements(self, requirements: Dict) -> bool:
        """Detect if project requires frontend implementation"""
        frontend_indicators = [
            "frontend", "react", "vue", "angular", "ui", "interface",
            "dashboard", "webpage", "website", "client", "browser",
            "tailwind", "css", "html", "user interface", "gui"
        ]
        
        # Check in features
        features = requirements.get("features", [])
        for feature in features:
            if any(indicator in feature.lower() for indicator in frontend_indicators):
                return True
        
        # Check in tech_overrides
        tech_overrides = requirements.get("tech_overrides", {})
        if "frontend" in tech_overrides:
            return True
        
        # Check in project description
        description = requirements.get("project", {}).get("description", "")
        if any(indicator in description.lower() for indicator in frontend_indicators):
            return True
            
        return False
    
    def _detect_ai_requirements(self, requirements: Dict) -> bool:
        """Detect if project requires AI/ML features"""
        ai_indicators = [
            "ai", "ml", "machine learning", "artificial intelligence",
            "llm", "openai", "anthropic", "gpt", "claude", "neural",
            "categorization", "classification", "prediction", "recommendation",
            "intelligent", "smart", "automated analysis"
        ]
        
        # Check features
        features = requirements.get("features", [])
        for feature in features:
            if any(indicator in feature.lower() for indicator in ai_indicators):
                return True
        
        # Check tech_overrides
        if "ai" in requirements.get("tech_overrides", {}):
            return True
            
        return False
    
    def _upgrade_project_type(self, project_type: str, requirements: Dict) -> str:
        """Auto-upgrade project type based on detected requirements"""
        needs_frontend = self._detect_frontend_requirements(requirements)
        needs_ai = self._detect_ai_requirements(requirements)
        
        # Log detection results
        self.logger.log_reasoning(
            "orchestrator",
            f"Frontend detected: {needs_frontend}, AI detected: {needs_ai}",
            "Analyzing requirements for project type upgrade"
        )
        
        # Upgrade logic
        if project_type == "api_service" and needs_frontend:
            self.logger.log_reasoning(
                "orchestrator",
                "Upgrading api_service to full_stack_api due to frontend requirements",
                "Project type auto-upgrade"
            )
            return "full_stack_api"
        
        # Keep original if no upgrade needed
        return project_type
    
    def _validate_requirements_coverage(self, requirements: Dict, workflow: List) -> Dict:
        """Validate that all requirements have corresponding agents"""
        # Map requirement patterns to required agents
        requirement_agent_map = {
            "docker": ["devops-engineer"],
            "containerization": ["devops-engineer"],
            "deployment": ["devops-engineer"],
            "ci/cd": ["devops-engineer"],
            "test": ["quality-guardian"],
            "unit test": ["quality-guardian"],
            "integration test": ["quality-guardian"],
            "frontend": ["frontend-specialist"],
            "react": ["frontend-specialist"],
            "ui": ["frontend-specialist"],
            "database": ["database-expert"],
            "sql": ["database-expert"],
            "api": ["api-integrator", "rapid-builder"],
            "rest": ["api-integrator", "rapid-builder"],
            "authentication": ["rapid-builder"],
            "jwt": ["rapid-builder"],
            "ai": ["ai-specialist"],
            "categorization": ["ai-specialist"],
            "machine learning": ["ai-specialist"],
            "documentation": ["documentation-writer"],
            "openapi": ["documentation-writer"],
            "swagger": ["documentation-writer"],
            "performance": ["performance-optimizer"],
            "optimization": ["performance-optimizer"],
            "security": ["quality-guardian"],
            "rate limiting": ["api-integrator", "quality-guardian"]
        }
        
        # Flatten workflow to get all agents
        workflow_agents = set()
        for phase in workflow:
            workflow_agents.update(phase)
        
        # Check requirements
        missing_coverage = []
        features = requirements.get("features", [])
        
        for feature in features:
            feature_lower = feature.lower()
            covered = False
            
            # Check if any requirement pattern is in the feature
            for pattern, required_agents in requirement_agent_map.items():
                if pattern in feature_lower:
                    # Check if at least one required agent is in workflow
                    if any(agent in workflow_agents for agent in required_agents):
                        covered = True
                        break
            
            if not covered:
                # Check if it's a general feature that rapid-builder handles
                general_patterns = ["crud", "endpoint", "service", "system", "platform"]
                if not any(pattern in feature_lower for pattern in general_patterns):
                    missing_coverage.append(feature)
        
        # Also check testing requirements
        testing_reqs = requirements.get("testing_requirements", [])
        if testing_reqs and "quality-guardian" not in workflow_agents:
            missing_coverage.append("Testing requirements specified but quality-guardian not in workflow")
        
        # Check documentation requirements  
        doc_reqs = requirements.get("documentation_requirements", [])
        if doc_reqs and "documentation-writer" not in workflow_agents:
            missing_coverage.append("Documentation requirements specified but documentation-writer not in workflow")
        
        return {
            "workflow_agents": list(workflow_agents),
            "missing_coverage": missing_coverage,
            "coverage_complete": len(missing_coverage) == 0
        }
    
    async def execute_workflow(
        self,
        project_type: str,
        requirements: Dict,
        interactive: bool = False,
        checkpoint: Optional[str] = None
    ) -> bool:
        """Execute complete workflow with logging"""
        
        # Auto-upgrade project type based on requirements
        original_type = project_type
        project_type = self._upgrade_project_type(project_type, requirements)
        
        if original_type != project_type:
            console.print(Panel(
                f"[yellow]Project type upgraded: {original_type} → {project_type}[/yellow]\n"
                "Based on detected requirements",
                border_style="yellow"
            ))
        
        if project_type not in self.workflows:
            self.logger.log_error("orchestrator", f"Unknown project type: {project_type}")
            return False
        
        workflow = self.workflows[project_type]
        
        # Validate requirements coverage
        validation_result = self._validate_requirements_coverage(requirements, workflow)
        if validation_result["missing_coverage"]:
            console.print(Panel(
                "[yellow]Warning: Some requirements may not be fully covered:[/yellow]\n" +
                "\n".join(f"• {req}" for req in validation_result["missing_coverage"]),
                border_style="yellow"
            ))
            self.logger.log_reasoning(
                "orchestrator",
                f"Missing coverage for: {validation_result['missing_coverage']}",
                "Requirement validation warning"
            )
        
        # Initialize context
        context = AgentContext(
            project_requirements=requirements,
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="initialization"
        )
        
        # Load checkpoint if provided
        if checkpoint and Path(checkpoint).exists():
            with open(checkpoint) as f:
                checkpoint_data = json.load(f)
                context = AgentContext(**checkpoint_data.get("context", {}))
                start_phase = checkpoint_data.get("current_phase", 0)
            console.print(Panel(f"Resuming from checkpoint: Phase {start_phase}", border_style="yellow"))
        else:
            start_phase = 0
        
        # Execute workflow phases
        for phase_num, phase_agents in enumerate(workflow[start_phase:], start=start_phase+1):
            phase_name = f"Phase {phase_num}/{len(workflow)}"
            context.current_phase = phase_name
            
            self.logger.log_phase(phase_name, phase_agents, is_start=True)
            
            if interactive:
                if not Confirm.ask(f"Execute {phase_name} with agents: {', '.join(phase_agents)}?"):
                    console.print("[yellow]Phase skipped[/yellow]")
                    continue
            
            if len(phase_agents) == 1:
                # Sequential execution
                agent_name = phase_agents[0]
                success = await self._execute_single_agent(agent_name, context, interactive)
                if not success and not interactive:
                    self.logger.log_error("orchestrator", f"Workflow failed at {agent_name}")
                    return False
            else:
                # Parallel execution
                success = await self._execute_parallel_agents(phase_agents, context, interactive)
                if not success and not interactive:
                    self.logger.log_error("orchestrator", f"Workflow failed at {phase_name}")
                    return False
            
            self.logger.log_phase(phase_name, phase_agents, is_start=False)
            
            # Checkpoint after each phase
            checkpoint_file = self.checkpoints_dir / f"phase_{phase_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(checkpoint_file, 'w') as f:
                json.dump({
                    "context": context.to_dict(),
                    "current_phase": phase_num
                }, f, indent=2)
        
        # Run final validation if quality-guardian was in workflow
        workflow_agents = set()
        for phase in workflow:
            workflow_agents.update(phase)
        
        if "quality-guardian" in workflow_agents:
            # Attempt to run final validation
            try:
                from lib.quality_validation import RequirementValidator
                validator = RequirementValidator()
                validation_report = await validator.validate_requirements(requirements, context)
                
                console.print(Panel(
                    "[bold green]Workflow Complete![/bold green]\n" +
                    f"Completed tasks: {len(context.completed_tasks)}\n" +
                    f"Artifacts created: {len(context.artifacts)}\n" +
                    f"Decisions made: {len(context.decisions)}\n" +
                    f"[yellow]Requirement Completion: {validation_report.completion_percentage:.1f}%[/yellow]",
                    border_style="green"
                ))
                
                # Log validation summary
                self.logger.log_reasoning(
                    "orchestrator",
                    f"Requirements: {validation_report.completed}/{validation_report.total_requirements} completed",
                    "Final validation complete"
                )
            except:
                # Fallback to simple completion message
                console.print(Panel(
                    "[bold green]Workflow Complete![/bold green]\n" +
                    f"Completed tasks: {len(context.completed_tasks)}\n" +
                    f"Artifacts created: {len(context.artifacts)}\n" +
                    f"Decisions made: {len(context.decisions)}",
                    border_style="green"
                ))
        else:
            console.print(Panel(
                "[bold green]Workflow Complete![/bold green]\n" +
                f"Completed tasks: {len(context.completed_tasks)}\n" +
                f"Artifacts created: {len(context.artifacts)}\n" +
                f"Decisions made: {len(context.decisions)}",
                border_style="green"
            ))
        
        return True
    
    async def _execute_single_agent(
        self,
        agent_name: str,
        context: AgentContext,
        interactive: bool = False
    ) -> bool:
        """Execute a single agent"""
        
        if agent_name not in self.agents:
            self.logger.log_error("orchestrator", f"Unknown agent: {agent_name}")
            return False
        
        agent_config = self.agents[agent_name]
        
        if interactive:
            task = Prompt.ask(f"Specific task for {agent_name}", default="Execute as configured")
            agent_prompt = agent_config["prompt"] + f"\n\nSpecific task: {task}"
        else:
            agent_prompt = agent_config["prompt"]
        
        success, result, updated_context = await self.runtime.run_agent_async(
            agent_name,
            agent_prompt,
            context,
            model=self._get_model(agent_config["model"]),
            max_iterations=10
        )
        
        # Update context
        context.completed_tasks = updated_context.completed_tasks
        context.artifacts = updated_context.artifacts
        context.decisions = updated_context.decisions
        
        # Add delay between agents to prevent rate limiting
        if success:
            import asyncio
            await asyncio.sleep(self.runtime.min_delay_between_agents)
        
        return success
    
    async def _execute_parallel_agents(
        self,
        agents: List[str],
        context: AgentContext,
        interactive: bool = False
    ) -> bool:
        """Execute multiple agents in parallel"""
        
        tasks = []
        for agent_name in agents:
            if agent_name in self.agents:
                tasks.append(self._execute_single_agent(agent_name, context, interactive))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.log_error("orchestrator", f"Agent {agents[i]} failed: {str(result)}")
                return False
            elif not result:
                return False
        
        return True
    
    async def execute_chain(self, agents: List[str], prompt: str = "") -> bool:
        """Execute agents in sequential chain"""
        
        context = AgentContext(
            project_requirements={"prompt": prompt},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="chain"
        )
        
        for agent_name in agents:
            success = await self._execute_single_agent(agent_name, context)
            if not success:
                self.logger.log_error("orchestrator", f"Chain failed at {agent_name}")
                return False
        
        return True
    
    def replay_session(self, session_file: str):
        """Replay a session from logs"""
        if not Path(session_file).exists():
            console.print(f"[red]Session file not found: {session_file}[/red]")
            return
        
        console.print(Panel(f"Replaying session: {session_file}", border_style="blue"))
        
        with open(session_file) as f:
            for line in f:
                entry = json.loads(line)
                
                # Format and display entry
                timestamp = entry.get("timestamp", "")
                agent = entry.get("agent_name", "unknown")
                event = entry.get("event_type", "")
                message = entry.get("message", "")
                reasoning = entry.get("reasoning", "")
                
                if event == "agent_start":
                    console.print(f"\n[blue]▶ {agent}[/blue] - {message}")
                    if reasoning:
                        console.print(f"  [dim]Reasoning: {reasoning}[/dim]")
                elif event == "agent_complete":
                    console.print(f"[green][OK] {agent}[/green] - {message}")
                elif event == "tool_call":
                    console.print(f"  [yellow][TOOL] {message}[/yellow]")
                    if reasoning:
                        console.print(f"    [dim]{reasoning}[/dim]")
                elif event == "error":
                    console.print(f"  [red][ERROR] {message}[/red]")
        
        # Load and display summary if available
        summary_file = Path(session_file).with_suffix('.summary.json')
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
            
            console.print("\n" + Panel(
                f"[bold]Session Summary[/bold]\n" +
                f"Total Agents: {summary['summary']['total_agents']}\n" +
                f"Total Executions: {summary['summary']['total_executions']}\n" +
                f"Success Rate: {summary['summary']['overall_success_rate']:.1f}%",
                border_style="green"
            ))

async def main():
    parser = argparse.ArgumentParser(description="Enhanced Agent Swarm Orchestrator")
    parser.add_argument("--project-type", choices=["web_app", "api_service", "ai_solution"])
    parser.add_argument("--requirements", help="Path to requirements.yaml")
    parser.add_argument("--chain", help="Execute agents in chain (comma-separated)")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--checkpoint", help="Resume from checkpoint file")
    parser.add_argument("--replay", help="Replay session from log file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env)")
    
    args = parser.parse_args()
    
    # Handle API key
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    
    # Create orchestrator
    orchestrator = EnhancedOrchestrator(api_key)
    
    try:
        if args.replay:
            # Replay mode
            orchestrator.replay_session(args.replay)
        
        elif args.project_type and args.requirements:
            # Full workflow execution
            with open(args.requirements) as f:
                requirements = yaml.safe_load(f)
            
            console.print(Panel(
                f"[bold]Starting {args.project_type} Workflow[/bold]\n" +
                f"Project: {requirements.get('project', {}).get('name', 'Unknown')}\n" +
                f"Requirements: {args.requirements}",
                border_style="green"
            ))
            
            success = await orchestrator.execute_workflow(
                args.project_type,
                requirements,
                interactive=args.interactive,
                checkpoint=args.checkpoint
            )
            
            orchestrator.logger.close_session()
            sys.exit(0 if success else 1)
        
        elif args.chain:
            # Chain execution
            agents = [a.strip() for a in args.chain.split(",")]
            console.print(Panel(
                f"[bold]Executing Chain[/bold]\n" +
                f"Agents: {' → '.join(agents)}",
                border_style="blue"
            ))
            
            success = await orchestrator.execute_chain(agents)
            orchestrator.logger.close_session()
            sys.exit(0 if success else 1)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        orchestrator.logger.close_session()
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if args.verbose:
            import traceback
            traceback.print_exc()
        orchestrator.logger.close_session()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())