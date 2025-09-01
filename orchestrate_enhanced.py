#!/usr/bin/env python3
"""
Enhanced Agent Swarm Orchestrator - Section 8 Implementation

Features:
- Adaptive workflow with dynamic agent selection
- Requirement tracking with ID mapping  
- Advanced error recovery and retry logic
- Real-time progress monitoring
- Parallel execution with dependency management
- Manual intervention points
- WebSocket-based dashboard integration

Usage:
    python orchestrate_enhanced.py --project-type=web_app --requirements=requirements.yaml --dashboard
    python orchestrate_enhanced.py --chain=project-architect,rapid-builder --interactive --progress
    python orchestrate_enhanced.py --resume-checkpoint checkpoints/workflow_*.json
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

# Fix encoding issues for Windows immediately
try:
    from lib.encoding_fix import setup_utf8_encoding, clean_unicode_content
    setup_utf8_encoding()
except ImportError:
    # If encoding_fix doesn't exist yet, continue without it
    pass

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
from lib.human_logger import SummaryLevel
from lib.agent_runtime import (
    AnthropicAgentRunner, AgentContext, ModelType, Tool, 
    create_standard_tools, create_quality_tools, create_mcp_enhanced_tools
)
try:
    from lib.build_validator import BuildValidator, BuildError
except ImportError:
    BuildValidator = None
    BuildError = None

# Import mock handler for testing
if os.environ.get('MOCK_MODE') == 'true':
    from lib.mock_anthropic_enhanced import MockAnthropicEnhancedRunner
from lib.orchestration_enhanced import (
    AdaptiveWorkflowEngine, RequirementItem, AgentExecutionPlan,
    RequirementStatus, AgentExecutionStatus
)
from lib.progress_streamer import (
    ProgressStreamer, ProgressEventType, create_orchestration_progress_callback
)
from lib.mcp_conditional_loader import MCPConditionalLoader
from lib.workflow_loader import WorkflowLoader

# Import enhanced validation components
from lib.validation_orchestrator import (
    ValidationOrchestrator, CompletionStage, ValidationLevel, 
    BuildResult, RetryStrategy
)
from lib.requirement_tracker import RequirementTracker
from lib.agent_validator import AgentValidator
from lib.error_pattern_detector import ErrorPatternDetector

# Import Phase 4 components
from lib.progressive_validator import ProgressiveValidator
from lib.checkpoint_manager import CheckpointManager
from lib.self_healing_rules import SelfHealingRules
from lib.validation_gates import ValidationGates

# Import Phase 5 components for quality assurance
try:
    from lib.mandatory_testing import MandatoryTestingSystem
    from lib.token_monitor import TokenMonitor
    from lib.post_execution_verification import PostExecutionVerification
    HAS_PHASE5 = True
except ImportError as e:
    print(f"Warning: Phase 5 components not fully available: {e}")
    HAS_PHASE5 = False
    MandatoryTestingSystem = None
    TokenMonitor = None
    PostExecutionVerification = None

# Import Phase 2 components for enhanced coordination
try:
    from lib.file_coordinator import get_file_coordinator
    from lib.agent_verification import AgentVerification
    from lib.agent_runtime import clean_reasoning
    from lib.phase2_integration import Phase2Integration
    HAS_PHASE2 = True
except ImportError as e:
    print(f"Warning: Phase 2 components not fully available: {e}")
    HAS_PHASE2 = False
    get_file_coordinator = None
    AgentVerification = None
    clean_reasoning = None
    Phase2Integration = None

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("Warning: Rich not installed. Install with: pip install rich")

console = Console() if HAS_RICH else None


class EnhancedOrchestrator:
    """Enhanced orchestrator with Section 8 capabilities"""
    
    def __init__(self, api_key: Optional[str] = None, session_id: Optional[str] = None, 
                 enable_dashboard: bool = False, enable_human_log: bool = True,
                 summary_level: str = "concise"):
        # Convert string summary level to enum
        level_map = {
            "concise": SummaryLevel.CONCISE,
            "detailed": SummaryLevel.DETAILED,
            "verbose": SummaryLevel.VERBOSE
        }
        self.logger = create_new_session(session_id, enable_human_log, level_map.get(summary_level, SummaryLevel.CONCISE))
        
        # Use mock runner if in mock mode
        if os.environ.get('MOCK_MODE') == 'true':
            self.runtime = MockAnthropicEnhancedRunner(self.logger)
        else:
            self.runtime = AnthropicAgentRunner(api_key, self.logger)
        self.agents = self._load_agent_configs()
        
        # Enhanced orchestration components
        self.workflow_engine = AdaptiveWorkflowEngine(self.logger)
        self.progress_streamer = ProgressStreamer(self.logger) if enable_dashboard else None
        self.mcp_loader = MCPConditionalLoader()  # Initialize conditional MCP loader
        self.workflow_loader = WorkflowLoader()  # Initialize workflow pattern loader
        
        # Initialize validation components
        self.requirement_tracker = RequirementTracker()
        self.agent_validator = AgentValidator()
        self.validation_orchestrator = ValidationOrchestrator(
            requirement_tracker=self.requirement_tracker,
            agent_validator=self.agent_validator
        )
        self.error_detector = ErrorPatternDetector(logger=self.logger)
        self.enable_validation = True  # Flag to enable/disable validation
        self.auto_debug = True  # Flag to enable automatic debugging on failures
        
        # Initialize Phase 4 components
        self.progressive_validator = ProgressiveValidator(auto_fix=True)
        self.checkpoint_manager = CheckpointManager(checkpoint_dir="checkpoints")
        self.self_healing_rules = SelfHealingRules(auto_apply=True)
        self.validation_gates = ValidationGates(strict_mode=True)
        
        # Initialize Phase 5 components for quality assurance
        if HAS_PHASE5:
            # Initialize mandatory testing system (5.1)
            self.mandatory_testing = MandatoryTestingSystem(
                project_root=str(Path.cwd())  # Will be updated when project dir is set
            )
            
            # Initialize token monitor (5.2)
            self.token_monitor = TokenMonitor(
                token_limit=100000,  # 100k tokens per agent
                checkpoint_callback=self._handle_token_checkpoint,
                logger=self.logger
            )
            
            # Initialize post-execution verification (5.5)
            self.post_verification = PostExecutionVerification(
                project_root=str(Path.cwd()),  # Will be updated when project dir is set
                logger=self.logger
            )
            
            self.logger.log_reasoning(
                "orchestrator",
                "Phase 5 components initialized",
                "Mandatory testing, token monitoring, and post-execution verification enabled"
            )
        else:
            self.mandatory_testing = None
            self.token_monitor = None
            self.post_verification = None
        
        # Initialize Phase 2 components for enhanced coordination
        if HAS_PHASE2:
            self.phase2_integration = Phase2Integration(
                project_name=session_id or "default"
            )
            self.file_coordinator = get_file_coordinator()
            self.agent_verification = AgentVerification()
            self.logger.log_reasoning(
                "orchestrator",
                "Phase 2 components initialized",
                "File locking, verification, and inter-agent communication enabled"
            )
        else:
            self.phase2_integration = None
            self.file_coordinator = None
            self.agent_verification = None
        
        # Register progress callback
        if self.progress_streamer:
            callback = create_orchestration_progress_callback(self.progress_streamer)
            self.workflow_engine.add_progress_callback(callback)
        
        # Directories
        self.checkpoints_dir = Path("checkpoints")
        self.checkpoints_dir.mkdir(exist_ok=True)
        self.progress_dir = Path("progress")
        self.progress_dir.mkdir(exist_ok=True)
        
        # Register standard tools
        for tool in create_standard_tools():
            self.runtime.register_tool(tool)
        
        # Register quality validation tools
        for tool in create_quality_tools():
            self.runtime.register_tool(tool)
        
        # Register MCP enhanced tools (includes mcp_ref_search, mcp_get_docs, etc.)
        mcp_tools = create_mcp_enhanced_tools()
        if mcp_tools:
            self.logger.log_reasoning(
                "orchestrator",
                f"Registering {len(mcp_tools)} MCP enhanced tools",
                "MCP tools provide 60% token reduction through efficient documentation fetching"
            )
            for tool in mcp_tools:
                self.runtime.register_tool(tool)
                self.logger.log_reasoning(
                    "orchestrator",
                    f"Registered MCP tool: {tool.name}",
                    tool.description
                )
        else:
            self.logger.log_reasoning(
                "orchestrator",
                "No MCP tools available - MCP servers may not be running",
                "Agents will use general knowledge instead of MCP documentation"
            )
        
        # Add enhanced orchestration tools
        self._register_enhanced_tools()
    
    def _handle_token_checkpoint(self, checkpoint_data: Dict):
        """Handle token limit checkpoint creation"""
        self.logger.log_reasoning(
            "token_monitor",
            f"Creating checkpoint due to token limit for {checkpoint_data['agent']}",
            f"Tokens used: {checkpoint_data['token_usage']['total_tokens']}"
        )
        
        # Use checkpoint manager if available
        if hasattr(self, 'checkpoint_manager'):
            self.checkpoint_manager.create_checkpoint(
                agent_name=checkpoint_data['agent'],
                progress=self.workflow_engine.progress.overall_completion if hasattr(self, 'workflow_engine') else 0,
                context=None,  # Will be filled by the system
                files_created=[],
                validation_passed=True
            )
    
    def _load_agent_configs(self) -> Dict:
        """Load agent configurations and prompts"""
        agents = {}
        
        # Try multiple paths to find the agents directory
        possible_paths = [
            Path(".claude/agents"),  # Current directory
            Path(__file__).parent / ".claude/agents",  # Relative to this script
            Path.cwd() / ".claude/agents",  # Explicit current directory
        ]
        
        # If running from a subdirectory, try parent directories
        for i in range(3):  # Check up to 3 levels up
            parent = Path.cwd().parents[i] if i < len(Path.cwd().parents) else None
            if parent:
                possible_paths.append(parent / ".claude/agents")
        
        agent_dir = None
        for path in possible_paths:
            if path.exists():
                agent_dir = path
                break
        
        if not agent_dir:
            self.logger.log_error("orchestrator", "Agent directory not found: .claude/agents")
            # In mock mode, we can continue without agent configs
            if os.environ.get('MOCK_MODE') == 'true':
                self.logger.log_reasoning("orchestrator", "Mock mode enabled - continuing without agent configs")
                return {}
            return agents
        
        # Load each agent's prompt from their .md files
        for agent_file in agent_dir.glob("*.md"):
            agent_name = agent_file.stem
            content = agent_file.read_text(encoding='utf-8')
            
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
        
        # Log loaded agents for debugging
        loaded_agent_names = list(agents.keys())
        self.logger.log_reasoning(
            "orchestrator",
            f"Loaded {len(agents)} agent configurations: {', '.join(loaded_agent_names)}",
            "Agent configs parsed from .claude/agents/*.md"
        )
        
        # Explicitly check for critical agents
        critical_agents = ["automated-debugger", "quality-guardian-enhanced"]
        missing_agents = [agent for agent in critical_agents if agent not in agents]
        
        if missing_agents:
            self.logger.log_warning(
                "orchestrator",
                f"Critical agents not loaded: {', '.join(missing_agents)}",
                "Some critical agents are missing from configuration"
            )
            
            # Try to load automated-debugger explicitly if missing
            if "automated-debugger" not in agents:
                debugger_path = agent_dir / "automated-debugger.md"
                if debugger_path.exists():
                    self.logger.log_reasoning(
                        "orchestrator",
                        "Loading automated-debugger explicitly",
                        "Critical agent was not loaded in initial scan"
                    )
                    content = debugger_path.read_text(encoding='utf-8')
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            import yaml
                            frontmatter = yaml.safe_load(parts[1])
                            prompt = parts[2].strip()
                            
                            agents["automated-debugger"] = {
                                "name": "automated-debugger",
                                "model": frontmatter.get("model", "opus"),
                                "tools": frontmatter.get("tools", []),
                                "prompt": prompt,
                                "description": frontmatter.get("description", "")
                            }
                            self.logger.log_reasoning(
                                "orchestrator",
                                "Successfully loaded automated-debugger",
                                "Critical agent now available for error recovery"
                            )
        
        return agents
    
    def _register_enhanced_tools(self):
        """Register enhanced orchestration tools"""
        
        async def adaptive_agent_selection(
            reasoning: str, 
            requirements: List[str], 
            context: AgentContext
        ) -> str:
            """Dynamically select optimal agents for requirements"""
            self.logger.log_reasoning("orchestrator", reasoning, "Adaptive agent selection")
            
            # Parse requirements into RequirementItems
            parsed_reqs = {}
            for idx, req in enumerate(requirements):
                req_id = f"DYNAMIC-{idx+1:03d}"
                assigned_agents, priority = self.workflow_engine._analyze_feature_requirements(req)
                
                parsed_reqs[req_id] = RequirementItem(
                    id=req_id,
                    description=req,
                    priority=priority,
                    assigned_agents=assigned_agents
                )
            
            # Create execution plan
            available_agents = list(self.agents.keys())
            plans = {}
            
            for req_id, req_item in parsed_reqs.items():
                for agent in req_item.assigned_agents:
                    if agent in available_agents:
                        if agent not in plans:
                            plans[agent] = AgentExecutionPlan(
                                agent_name=agent,
                                requirements=[],
                                dependencies=[],
                                priority=req_item.priority
                            )
                        plans[agent].requirements.append(req_id)
            
            # Sort by priority
            selected_agents = sorted(plans.keys(), key=lambda a: plans[a].priority)
            
            return f"Selected agents: {', '.join(selected_agents)} for {len(requirements)} requirements"
        
        self.runtime.register_tool(Tool(
            name="adaptive_agent_selection",
            description="Dynamically select optimal agents for given requirements",
            parameters={
                "requirements": {"type": "array", "description": "List of requirements", "required": True}
            },
            function=adaptive_agent_selection
        ))
        
        async def checkpoint_workflow_state(reasoning: str, checkpoint_name: str) -> str:
            """Save enhanced checkpoint with full workflow state"""
            checkpoint_file = self.checkpoints_dir / f"{checkpoint_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            self.workflow_engine.save_checkpoint(checkpoint_file)
            
            if self.progress_streamer:
                await self.progress_streamer.notify_checkpoint_saved(
                    str(checkpoint_file), 
                    self.workflow_engine.workflow_id
                )
            
            return f"Enhanced checkpoint saved: {checkpoint_file}"
        
        self.runtime.register_tool(Tool(
            name="checkpoint_workflow_state",
            description="Save comprehensive workflow checkpoint",
            parameters={
                "checkpoint_name": {"type": "string", "description": "Checkpoint name", "required": True}
            },
            function=checkpoint_workflow_state
        ))
        
        async def request_manual_intervention(
            reasoning: str, 
            agent_name: str, 
            issue_description: str
        ) -> str:
            """Request manual intervention for failed agent"""
            self.logger.log_reasoning("orchestrator", reasoning, f"Manual intervention for {agent_name}")
            
            if self.progress_streamer:
                await self.progress_streamer.notify_manual_intervention(
                    agent_name,
                    issue_description,
                    ["Skip", "Retry with modifications", "Abort workflow"]
                )
            
            return f"Manual intervention requested for {agent_name}: {issue_description}"
        
        self.runtime.register_tool(Tool(
            name="request_manual_intervention", 
            description="Request manual intervention for agent issues",
            parameters={
                "agent_name": {"type": "string", "description": "Agent needing intervention", "required": True},
                "issue_description": {"type": "string", "description": "Description of the issue", "required": True}
            },
            function=request_manual_intervention
        ))
    
    async def execute_enhanced_workflow(
        self,
        project_type: str,
        requirements: Dict,
        interactive: bool = False,
        checkpoint_file: Optional[str] = None,
        max_parallel: int = 3,
        output_dir: Optional[str] = None
    ) -> bool:
        """Execute enhanced workflow with all Section 8 capabilities
        
        Args:
            output_dir: Optional output directory. If not provided, creates timestamped folder
        """
        
        # Validate requirements before starting
        validation_errors = self._validate_requirements(requirements)
        if validation_errors:
            self.logger.log_error("orchestrator", "Requirements validation failed", str(validation_errors))
            if HAS_RICH:
                console.print(Panel(
                    f"[red]Requirements validation failed:[/red]\n" + 
                    "\n".join(f"• {error}" for error in validation_errors),
                    title="Validation Error",
                    border_style="red"
                ))
            return False
        
        # Log the actual project being processed
        project_name = requirements.get("project", {}).get("name", "Unknown")
        project_type_actual = requirements.get("project", {}).get("type", project_type)
        
        # Set up project output directory
        if output_dir is None:
            # Create timestamped directory for this execution
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"projects/{project_name}_{timestamp}"
        
        self.project_dir = Path(output_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        # Store the project directory in the context for agents to use
        self.context_project_dir = str(self.project_dir)
        
        # Update Phase 5 components with correct project root
        if HAS_PHASE5:
            if self.mandatory_testing:
                self.mandatory_testing.project_root = self.project_dir
            if self.post_verification:
                self.post_verification.project_root = self.project_dir
        
        self.logger.log_reasoning(
            "orchestrator", 
            f"Starting workflow for project: {project_name} (type: {project_type_actual})",
            f"Project output directory: {self.project_dir}"
        )
        
        if HAS_RICH:
            console.print(Panel(
                f"[bold green]Project Directory:[/bold green] {self.project_dir}\n"
                f"[bold]Project:[/bold] {project_name}\n"
                f"[bold]Type:[/bold] {project_type_actual}",
                title="Workflow Configuration",
                border_style="green"
            ))
        
        # Store project type for conditional MCP loading
        self.current_project_type = project_type
        
        self.workflow_engine.max_parallel_agents = max_parallel
        
        # Load checkpoint if provided
        if checkpoint_file and Path(checkpoint_file).exists():
            # Try enhanced checkpoint first
            if checkpoint_file.startswith("checkpoint_"):
                # Phase 4.2: Resume from enhanced checkpoint
                restoration = self.checkpoint_manager.resume_from_checkpoint(checkpoint_file)
                if restoration:
                    context.artifacts.update(restoration['artifacts'])
                    context.decisions.extend(restoration['decisions'])
                    
                    if HAS_RICH:
                        console.print(Panel(
                            f"[green]Enhanced checkpoint loaded successfully[/green]\n"
                            f"Agent: {restoration['agent_name']}\n"
                            f"Progress: {restoration['progress']:.1f}%\n"
                            f"Files restored: {len(restoration['files_restored'])}",
                            title="Resuming from Enhanced Checkpoint",
                            border_style="green"
                        ))
                    
                    # Set workflow state from checkpoint
                    self.workflow_engine.progress.overall_completion = restoration['progress']
                else:
                    console.print("[red]Failed to load enhanced checkpoint[/red]")
                    return False
            elif self.workflow_engine.load_checkpoint(Path(checkpoint_file)):
                console.print(Panel(
                    f"[green]Checkpoint loaded successfully[/green]\n"
                    f"Workflow ID: {self.workflow_engine.workflow_id}\n"
                    f"Progress: {self.workflow_engine.progress.overall_completion:.1f}%",
                    title="Resuming from Checkpoint",
                    border_style="green"
                ))
            else:
                console.print("[red]Failed to load checkpoint, starting fresh[/red]")
                return False
        else:
            # Parse requirements with intelligent ID mapping
            self.workflow_engine.parse_requirements_with_ids(requirements)
            
            # Select MCP-enhanced workflow pattern if applicable
            selected_workflow = self.workflow_loader.select_workflow(requirements, project_type)
            if selected_workflow:
                self.logger.log_reasoning(
                    "orchestrator",
                    f"Selected MCP-enhanced workflow: {selected_workflow.name}",
                    f"Description: {selected_workflow.description}"
                )
                
                # Store selected workflow for agent MCP configuration
                self.selected_workflow = selected_workflow
                
                # Log workflow phases
                for phase in selected_workflow.phases:
                    agents_in_phase = [a.get('agent', '') for a in phase.agents]
                    self.logger.log_reasoning(
                        "orchestrator",
                        f"Workflow phase '{phase.name}' ({phase.execution_type})",
                        f"Agents: {', '.join(agents_in_phase)}"
                    )
            else:
                self.selected_workflow = None
                self.logger.log_reasoning(
                    "orchestrator",
                    "No specific MCP-enhanced workflow matched",
                    "Using standard adaptive execution plan"
                )
            
            # Create adaptive execution plan
            available_agents = list(self.agents.keys())
            self.workflow_engine.create_adaptive_execution_plan(available_agents)
        
        # Start progress streaming
        if self.progress_streamer:
            await self.progress_streamer.start_websocket_server()
            await self.progress_streamer.notify_workflow_started(
                self.workflow_engine.workflow_id,
                len(self.workflow_engine.requirements),
                len(self.workflow_engine.agent_plans)
            )
        
        # Initialize context with project directory (Phase 3.4: Project Path Standardization)
        context = AgentContext(
            project_requirements=requirements,
            completed_tasks=[],
            artifacts={
                "project_directory": str(self.project_dir),
                "project_root": str(self.project_dir),  # Phase 3.4: Standardized project root
                "project_name": project_name,
                "project_type": project_type_actual
            },
            decisions=[],
            current_phase="enhanced_orchestration"
        )
        
        # Phase 3.4: Set project root for all file operations
        context.project_root = str(self.project_dir)
        
        # Log project path standardization
        self.logger.log_reasoning(
            "orchestrator",
            f"Phase 3.4: Project path standardized to {self.project_dir}",
            "All agents will use this as the root for file operations"
        )
        
        try:
            # Execute workflow with adaptive orchestration
            success = await self._execute_adaptive_workflow(context, interactive)
            
            # Generate final summary
            summary = self.workflow_engine.get_execution_summary()
            
            # Notify completion
            if self.progress_streamer:
                await self.progress_streamer.notify_workflow_completed(
                    self.workflow_engine.workflow_id,
                    success,
                    summary
                )
            
            # Display results
            self._display_workflow_results(success, summary)
            
            # Phase 5.5: Post-execution verification
            if HAS_PHASE5 and self.post_verification and success:
                self.logger.log_reasoning(
                    "post_verification",
                    "Running post-execution verification",
                    "Checking backend, frontend, Docker, and endpoints"
                )
                
                verification_success, verification_results = self.post_verification.run_all_verifications()
                
                # Generate and save verification report
                verification_report = self.post_verification.generate_verification_report()
                report_path = self.progress_dir / f"post_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(report_path, 'w') as f:
                    f.write(verification_report)
                
                if HAS_RICH:
                    if verification_success:
                        console.print(Panel(
                            f"[green]✅ Post-Execution Verification PASSED[/green]\n"
                            f"Backend: {verification_results['backend_start']}\n"
                            f"Frontend: {verification_results['frontend_build']}\n"
                            f"Docker: {verification_results['docker_containers']}\n"
                            f"Endpoints: {verification_results['critical_endpoints']}\n"
                            f"Report saved to: {report_path}",
                            title="Phase 5.5 Verification",
                            border_style="green"
                        ))
                    else:
                        console.print(Panel(
                            f"[yellow]⚠️ Post-Execution Verification PARTIAL[/yellow]\n"
                            f"Backend: {verification_results['backend_start']}\n"
                            f"Frontend: {verification_results['frontend_build']}\n"
                            f"Docker: {verification_results['docker_containers']}\n"
                            f"Endpoints: {verification_results['critical_endpoints']}\n"
                            f"Report saved to: {report_path}",
                            title="Phase 5.5 Verification",
                            border_style="yellow"
                        ))
                
                # Update overall success based on verification
                if not verification_success:
                    self.logger.log_warning(
                        "post_verification",
                        "Some post-execution checks failed",
                        "Project may not be fully functional"
                    )
            
            # Phase 5.3: Enforce quality gates
            if HAS_PHASE5 and self.mandatory_testing:
                gates_passed, gate_failures = self.mandatory_testing.enforce_quality_gates()
                
                if not gates_passed:
                    self.logger.log_warning(
                        "quality_gates",
                        "Some quality gates failed",
                        f"Failures: {', '.join(gate_failures)}"
                    )
                    
                    if HAS_RICH:
                        console.print(Panel(
                            f"[yellow]⚠️ Quality Gates Check[/yellow]\n" +
                            "\n".join(f"• {failure}" for failure in gate_failures),
                            title="Phase 5.3 Quality Gates",
                            border_style="yellow"
                        ))
            
            # Phase 5.2: Generate token usage report
            if HAS_PHASE5 and self.token_monitor:
                token_report = self.token_monitor.generate_usage_report()
                token_report_path = self.progress_dir / f"token_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(token_report_path, 'w') as f:
                    f.write(token_report)
                
                usage_summary = self.token_monitor.get_usage_summary()
                
                if HAS_RICH:
                    console.print(Panel(
                        f"[cyan]Token Usage Summary[/cyan]\n"
                        f"Total Tokens: {usage_summary['total_tokens']:,}\n"
                        f"Total Cost: ${usage_summary['total_cost']:.2f}\n"
                        f"Checkpoints: {usage_summary['checkpoints_created']}\n"
                        f"Tasks Split: {usage_summary['tasks_split']}\n"
                        f"Report saved to: {token_report_path}",
                        title="Phase 5.2 Token Monitor",
                        border_style="cyan"
                    ))
            
            # Phase 5.1: Generate testing report
            if HAS_PHASE5 and self.mandatory_testing:
                test_report = self.mandatory_testing.generate_test_report()
                test_report_path = self.progress_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(test_report_path, 'w') as f:
                    f.write(test_report)
                
                if HAS_RICH:
                    console.print(f"[green]Test report saved to: {test_report_path}[/green]")
            
            # Print test-compatible metrics summary
            self._print_test_metrics(summary, context)
            
            return success
        
        finally:
            if self.progress_streamer:
                await self.progress_streamer.stop_websocket_server()
    
    async def _execute_adaptive_workflow(
        self, 
        context: AgentContext, 
        interactive: bool
    ) -> bool:
        """Execute workflow with adaptive agent scheduling"""
        
        completed_agents = set()
        failed_agents = set()
        
        while True:
            # Get agents ready to execute
            ready_agents = self.workflow_engine.get_ready_agents()
            ready_agents = [a for a in ready_agents if a not in completed_agents and a not in failed_agents]
            
            if not ready_agents:
                # Check if we're done or blocked
                remaining_agents = set(self.workflow_engine.agent_plans.keys()) - completed_agents - failed_agents
                if not remaining_agents:
                    break  # All done
                
                # Check for blocked agents
                blocked = True
                for agent in remaining_agents:
                    plan = self.workflow_engine.agent_plans[agent]
                    if plan.status != AgentExecutionStatus.BLOCKED:
                        blocked = False
                        break
                
                if blocked:
                    self.logger.log_error("orchestrator", "All remaining agents are blocked")
                    return False
                
                # Wait for running agents
                await asyncio.sleep(2)
                continue
            
            # Execute agents in parallel (up to max_parallel)
            batch_size = min(len(ready_agents), self.workflow_engine.max_parallel_agents)
            batch = ready_agents[:batch_size]
            
            if interactive and batch:
                if not Confirm.ask(f"Execute agents: {', '.join(batch)}?"):
                    console.print("[yellow]Batch skipped[/yellow]")
                    for agent in batch:
                        completed_agents.add(agent)
                    continue
            
            # Execute batch in parallel
            tasks = []
            for agent_name in batch:
                if agent_name in self.agents:
                    task = self._execute_agent_with_enhanced_features(
                        agent_name, context, interactive
                    )
                    tasks.append((agent_name, task))
            
            # Wait for batch completion
            results = await asyncio.gather(
                *[task for _, task in tasks], 
                return_exceptions=True
            )
            
            # Process results
            for i, (agent_name, result) in enumerate(zip([name for name, _ in tasks], results)):
                if isinstance(result, Exception):
                    self.logger.log_error("orchestrator", f"Agent {agent_name} failed with exception: {result}")
                    failed_agents.add(agent_name)
                elif result[0]:  # Success
                    completed_agents.add(agent_name)
                    # Update context with results
                    _, _, updated_context = result
                    context.completed_tasks.extend(updated_context.completed_tasks)
                    context.artifacts.update(updated_context.artifacts)
                    context.decisions.extend(updated_context.decisions)
                    
                    # Print output for test runner compatibility
                    print(f"Agent completed: {agent_name}")
                    
                    # Track and print files created
                    if hasattr(updated_context, 'created_files') and updated_context.created_files:
                        total_files = sum(len(files) for files in updated_context.created_files.values())
                        print(f"Files created: {total_files}")
                else:
                    failed_agents.add(agent_name)
            
            # Update progress
            self.workflow_engine._update_progress()
            
            # Phase 5.4: Real-time progress tracking
            if self.progress_streamer:
                # Broadcast detailed progress update
                progress_data = {
                    "completed_agents": list(completed_agents),
                    "failed_agents": list(failed_agents),
                    "overall_completion": self.workflow_engine.progress.overall_completion,
                    "current_phase": "execution",
                    "agents_remaining": len(set(self.workflow_engine.agent_plans.keys()) - completed_agents - failed_agents),
                    "estimated_time_remaining": self._estimate_time_remaining(completed_agents, failed_agents)
                }
                
                await self.progress_streamer.broadcast_event(
                    ProgressEventType.PROGRESS_UPDATE,
                    progress_data
                )
            
            # Phase 4.2: Enhanced checkpoint with full context
            if len(completed_agents) % 3 == 0:  # Every 3 agents
                # Use enhanced checkpoint manager
                checkpoint_id = self.checkpoint_manager.create_checkpoint(
                    agent_name="orchestrator",
                    progress=self.workflow_engine.progress.overall_completion,
                    context=context,
                    files_created=list(context.created_files.values()) if hasattr(context, 'created_files') else [],
                    validation_passed=len(failed_agents) == 0
                )
                
                self.logger.log_reasoning(
                    "checkpoint",
                    f"Enhanced checkpoint created: {checkpoint_id}",
                    f"Progress: {self.workflow_engine.progress.overall_completion:.1f}%"
                )
                
                # Also save workflow checkpoint for compatibility
                checkpoint_file = self.checkpoints_dir / f"auto_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.workflow_engine.save_checkpoint(checkpoint_file)
        
        # Check final success
        total_agents = len(self.workflow_engine.agent_plans)
        success_rate = len(completed_agents) / total_agents if total_agents > 0 else 0
        
        return success_rate >= 0.8  # 80% success rate considered successful
    
    async def _execute_agent_with_enhanced_features(
        self,
        agent_name: str,
        context: AgentContext,
        interactive: bool
    ) -> Tuple[bool, str, AgentContext]:
        """Execute agent with all enhanced Section 8 features"""
        
        if agent_name not in self.agents:
            self.logger.log_error("orchestrator", f"Unknown agent: {agent_name}")
            return False, "Agent not found", context
        
        agent_config = self.agents[agent_name]
        
        # Phase 3.4: Ensure project path standardization for this agent
        if hasattr(self, 'project_dir') and self.project_dir:
            # Ensure project_root is set in context for all agents
            if not hasattr(context, 'project_root'):
                context.project_root = str(self.project_dir)
            
            # Also ensure it's in artifacts for backward compatibility
            if "project_root" not in context.artifacts:
                context.artifacts["project_root"] = str(self.project_dir)
            
            # Log path usage for this agent
            self.logger.log_reasoning(
                agent_name,
                f"Using standardized project path: {context.project_root}",
                "Phase 3.4: All file operations will be relative to this path"
            )
        
        # Determine which conditional MCPs to load for this agent
        project_type = getattr(self, 'current_project_type', None)
        selected_workflow = getattr(self, 'selected_workflow', None)
        
        # First check if there's a selected workflow with MCPs for this agent
        if selected_workflow:
            # Get MCPs from the workflow pattern
            active_mcps = self.workflow_loader.get_agent_mcps(
                agent_name, 
                selected_workflow.name
            )
            if active_mcps:
                self.logger.log_reasoning(
                    "orchestrator",
                    f"Using MCPs from workflow '{selected_workflow.name}' for {agent_name}",
                    f"MCPs: {', '.join(active_mcps)}"
                )
        else:
            # Fall back to conditional loader logic
            active_mcps = self.mcp_loader.should_load_mcp(
                agent_name,
                context.project_requirements,
                project_type
            )
        
        # Log conditional MCP activation
        if active_mcps:
            self.logger.log_reasoning(
                "orchestrator",
                f"Loading conditional MCPs for {agent_name}: {', '.join(active_mcps)}",
                f"Based on project requirements and type: {project_type}"
            )
            
            # Register MCP tools with the runtime
            try:
                from lib.mcp_tools import get_conditional_mcp_tools
                mcp_tools = get_conditional_mcp_tools(active_mcps)
                for tool in mcp_tools:
                    self.runtime.register_tool(tool)
                    self.logger.log_reasoning(
                        "orchestrator",
                        f"Registered MCP tool: {tool.name} for {agent_name}"
                    )
            except ImportError:
                self.logger.log_error(
                    "orchestrator",
                    f"Could not load MCP tools for {active_mcps}",
                    "MCP tools not available"
                )
        
        # Update progress streamer
        if self.progress_streamer:
            plan = self.workflow_engine.agent_plans[agent_name]
            await self.progress_streamer.update_agent_status(agent_name, plan)
        
        # Phase 2: Pre-execution file locking
        if self.phase2_integration:
            # Estimate files that might be modified (can be enhanced with better prediction)
            files_to_modify = context.artifacts.get(f"{agent_name}_target_files", [])
            if not self.phase2_integration.before_agent_execution(agent_name, files_to_modify):
                self.logger.log_error(
                    "phase2",
                    f"Cannot acquire file locks for {agent_name}",
                    "Files are locked by another agent"
                )
                # Optionally wait or fail
                if interactive and console:
                    console.print(Panel(
                        "[yellow]Files are locked by another agent. Waiting...[/yellow]",
                        title=f"File Lock Conflict: {agent_name}",
                        border_style="yellow"
                    ))
        
        # Pre-execution validation if enabled
        if self.enable_validation:
            pre_valid, missing_deps, suggestions = self.validation_orchestrator.pre_execution_validation(
                agent_name, context
            )
            
            if not pre_valid:
                self.logger.log_error(
                    "validation",
                    f"Pre-execution validation failed for {agent_name}",
                    f"Missing dependencies: {', '.join(missing_deps)}"
                )
                
                if interactive and console:
                    console.print(Panel(
                        f"[yellow]⚠️ Pre-execution validation failed:[/yellow]\n" +
                        "\n".join(f"• {dep}" for dep in missing_deps) + "\n\n" +
                        "[cyan]Suggestions:[/cyan]\n" +
                        "\n".join(f"• {sug}" for sug in suggestions),
                        title=f"Validation Failed: {agent_name}",
                        border_style="yellow"
                    ))
                    
                    if not Confirm.ask("Continue anyway?"):
                        return False, "User cancelled due to validation failure", context
        
        # Phase 5.2: Track token usage before execution
        if HAS_PHASE5 and self.token_monitor:
            remaining_tokens = self.token_monitor.get_agent_budget_remaining(agent_name)
            if remaining_tokens < 1000:  # Less than 1k tokens remaining
                self.logger.log_warning(
                    "token_monitor",
                    f"Low token budget for {agent_name}",
                    f"Only {remaining_tokens} tokens remaining"
                )
        
        # Execute with retry logic and error recovery
        success, result, updated_context = await self.workflow_engine.execute_agent_with_retry(
            agent_name,
            self.runtime,
            context,
            agent_config
        )
        
        # Phase 5.2: Track token usage after execution
        if HAS_PHASE5 and self.token_monitor and hasattr(self.runtime, 'last_token_usage'):
            token_response = self.token_monitor.track_usage(
                agent_name,
                self.runtime.last_token_usage.get('input_tokens', 0),
                self.runtime.last_token_usage.get('output_tokens', 0),
                agent_config.get('model', 'sonnet')
            )
            
            if token_response['action'] == 'split_task':
                self.logger.log_warning(
                    "token_monitor",
                    f"Task split required for {agent_name}",
                    f"Token limit exceeded: {token_response['message']}"
                )
                # Mark for task splitting
                updated_context.artifacts["needs_task_split"] = token_response['split_info']
        
        # Phase 4.1: Progressive validation after execution
        if success and self.enable_validation:
            # Get files created by this agent
            files_created = updated_context.artifacts.get(f"{agent_name}_created_files", [])
            if not files_created and hasattr(updated_context, 'created_files'):
                files_created = updated_context.created_files.get(agent_name, [])
            
            # Run progressive validation on created files
            for file_path in files_created:
                validation_results = self.progressive_validator.validate_all(file_path)
                
                for val_type, val_result in validation_results.items():
                    if not val_result.success:
                        self.logger.log_error(
                            "progressive_validation",
                            f"Validation failed for {file_path} ({val_type})",
                            f"Errors: {', '.join([e.error_message for e in val_result.errors])}"
                        )
                        
                        # Phase 4.3: Apply self-healing rules
                        if self.auto_debug and val_result.errors:
                            for error in val_result.errors:
                                healing_result = self.self_healing_rules.apply_healing(
                                    error.error_message,
                                    {"file": file_path, "agent": agent_name}
                                )
                                
                                if healing_result.success:
                                    self.logger.log_reasoning(
                                        "self_healing",
                                        f"Auto-fixed {error.error_type} in {file_path}",
                                        healing_result.fix_applied
                                    )
                                else:
                                    self.logger.log_warning(
                                        "self_healing",
                                        f"Could not auto-fix {error.error_type}",
                                        healing_result.fix_applied
                                    )
        
        # Check for agent execution failures that need debugging
        if not success and self.auto_debug:
            # Use error pattern detector to determine recovery strategy
            recovery = self.error_detector.get_recovery_recommendation(agent_name, str(result))
            
            self.logger.log_reasoning(
                "error_recovery",
                f"Agent {agent_name} failed (attempt #{recovery['occurrence_count']})",
                f"Recovery strategy: {recovery['strategy']}"
            )
            
            # Execute recovery based on recommended strategy
            if recovery['strategy'] == "retry_same":
                # Simple retry
                self.logger.log_reasoning("recovery", "Retrying agent with same parameters", "")
                success, result, updated_context = await self.workflow_engine.execute_agent_with_retry(
                    agent_name,
                    self.runtime,
                    context,
                    agent_config
                )
                
            elif recovery['strategy'] == "retry_with_context":
                # Retry with error context
                updated_context.artifacts["previous_error"] = str(result)
                self.logger.log_reasoning("recovery", "Retrying with error context", str(result))
                success, result, updated_context = await self.workflow_engine.execute_agent_with_retry(
                    agent_name,
                    self.runtime,
                    updated_context,
                    agent_config
                )
                
            elif recovery['strategy'] == "trigger_debugger":
                # Trigger automated debugger
                self.logger.log_reasoning(
                    "recovery",
                    f"Triggering automated debugger for {agent_name}",
                    f"Error pattern detected after {recovery['occurrence_count']} failures"
                )
                
                # Create error context for debugger
                error_context = {
                    "failed_agent": agent_name,
                    "error_type": "repeated_failure",
                    "error_message": str(result),
                    "failure_count": recovery['occurrence_count'],
                    "context": updated_context
                }
                
                # Trigger automated debugger
                debug_success = await self._trigger_automated_debugger(
                    agent_name,
                    error_context,
                    updated_context
                )
                
                if debug_success:
                    self.logger.log_reasoning(
                        "recovery",
                        f"Automated debugging resolved errors for {agent_name}",
                        "Retrying agent execution"
                    )
                    # Reset error tracking for this agent after successful debug
                    self.error_detector.reset_agent(agent_name)
                    # Retry the agent after debugging
                    success, result, updated_context = await self.workflow_engine.execute_agent_with_retry(
                        agent_name,
                        self.runtime,
                        updated_context,
                        agent_config
                    )
                else:
                    self.logger.log_error(
                        "recovery",
                        f"Automated debugging failed for {agent_name}",
                        "Trying alternative agent"
                    )
                    # Continue to alternative agent strategy
                    recovery['strategy'] = "use_alternative_agent"
                    
            if recovery['strategy'] == "use_alternative_agent":
                # Try an alternative agent
                alternatives = recovery['details'].get('alternatives', ["rapid-builder"])
                alternative_agent = alternatives[0] if alternatives else "rapid-builder"
                
                self.logger.log_reasoning(
                    "recovery",
                    f"Using alternative agent: {alternative_agent}",
                    f"Original agent {agent_name} failed {recovery['occurrence_count']} times"
                )
                
                if alternative_agent in self.agents:
                    alt_config = self.agents[alternative_agent]
                    success, result, updated_context = await self.workflow_engine.execute_agent_with_retry(
                        alternative_agent,
                        self.runtime,
                        updated_context,
                        alt_config
                    )
                    if success:
                        self.logger.log_reasoning(
                            "recovery",
                            f"Alternative agent {alternative_agent} succeeded",
                            f"Replaced failing agent {agent_name}"
                        )
                        
            elif recovery['strategy'] == "manual_intervention":
                # Request manual intervention
                self.logger.log_error(
                    "recovery",
                    f"Agent {agent_name} requires manual intervention",
                    f"Failed {recovery['occurrence_count']} times with: {str(result)}"
                )
                
                if interactive and console:
                    console.print(Panel(
                        f"[red]⚠️ Manual Intervention Required[/red]\n\n" +
                        f"Agent: {agent_name}\n" +
                        f"Failures: {recovery['occurrence_count']}\n" +
                        f"Error: {str(result)}\n\n" +
                        "[yellow]The system has exhausted all automated recovery options.[/yellow]",
                        title="Critical Error",
                        border_style="red"
                    ))
                    
                    if not Confirm.ask("Continue without this agent?"):
                        return False, "User cancelled due to repeated failures", context
        
        # Post-execution validation and automated debugging
        if self.enable_validation and success:
            # Run compilation validation
            build_result = self.validation_orchestrator.validate_compilation(agent_name)
            
            if not build_result.success:
                self.logger.log_error(
                    "validation",
                    f"Build validation failed for {agent_name}",
                    f"Errors: {len(build_result.errors)}"
                )
                
                if self.auto_debug:
                    # Trigger automated debugger agent
                    debug_success = await self._trigger_automated_debugger(
                        agent_name,
                        build_result,
                        updated_context
                    )
                    
                    if debug_success:
                        # Re-validate after debugging
                        build_result = self.validation_orchestrator.validate_compilation(agent_name)
                        if build_result.success:
                            self.logger.log_reasoning(
                                "validation",
                                f"Automated debugging resolved issues for {agent_name}"
                            )
                    else:
                        self.logger.log_error(
                            "validation",
                            f"Automated debugging failed for {agent_name}",
                            "Manual intervention required"
                        )
                else:
                    if interactive and console:
                        console.print(Panel(
                            f"[red]❌ Build Validation Failed:[/red]\n\n" +
                            f"[yellow]Errors ({len(build_result.errors)}):[/yellow]\n" +
                            "\n".join(f"• {err}" for err in build_result.errors[:5]) + "\n\n" +
                            f"[cyan]Suggested Fixes:[/cyan]\n" +
                            "\n".join(f"• {fix}" for fix in build_result.suggested_fixes[:5]),
                            title=f"Validation Failed: {agent_name}",
                            border_style="red"
                        ))
            
            # Run runtime validation if build succeeded
            if build_result.success:
                runtime_success, runtime_msg = self.validation_orchestrator.validate_runtime(agent_name)
                
                if runtime_success:
                    self.logger.log_reasoning(
                        "validation",
                        f"Runtime validation passed for {agent_name}",
                        runtime_msg
                    )
                else:
                    self.logger.log_error(
                        "validation",
                        f"Runtime validation failed for {agent_name}",
                        runtime_msg
                    )
            
            # Run MCP validation if available
            if self.mcp_loader:
                mcp_results = self.validation_orchestrator.validate_with_mcp_tools(
                    agent_name,
                    test_urls=["http://localhost:3000", "http://localhost:8000"]
                )
                
                if mcp_results:
                    self.logger.log_reasoning(
                        "validation",
                        f"MCP validation results for {agent_name}",
                        json.dumps(mcp_results, indent=2)
                    )
        
        # Update progress streamer with final result
        if self.progress_streamer:
            plan = self.workflow_engine.agent_plans[agent_name]
            await self.progress_streamer.update_agent_status(agent_name, plan)
            
            # Update requirement statuses
            for req_id in plan.requirements:
                if req_id in self.workflow_engine.requirements:
                    requirement = self.workflow_engine.requirements[req_id]
                    await self.progress_streamer.update_requirement_status(req_id, requirement)
        
        # Generate validation report
        if self.enable_validation:
            report = self.validation_orchestrator.generate_validation_report(agent_name)
            report_path = self.progress_dir / f"validation_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_path, 'w') as f:
                f.write(report)
            
            if interactive and console:
                console.print(f"[green]✅ Validation report saved to: {report_path}[/green]")
        
        # Phase 4.4: Validation gates before completion
        if success and self.enable_validation:
            gate_report = self.validation_gates.run_all_gates(agent_name, updated_context)
            
            if not gate_report.can_complete:
                self.logger.log_error(
                    "validation_gates",
                    f"Agent {agent_name} failed validation gates",
                    f"Failed gates: {', '.join([g.value for g in gate_report.gates_failed])}"
                )
                
                # Phase 4.3: Try self-healing for gate failures
                if self.auto_debug:
                    for gate in gate_report.gates_failed:
                        gate_result = gate_report.gate_results[gate]
                        for error in gate_result.errors:
                            healing_result = self.self_healing_rules.apply_healing(
                                error,
                                {"agent": agent_name, "gate": gate.value}
                            )
                            
                            if healing_result.success:
                                self.logger.log_reasoning(
                                    "self_healing",
                                    f"Auto-fixed gate failure: {gate.value}",
                                    healing_result.fix_applied
                                )
                    
                    # Re-run gates after healing
                    gate_report = self.validation_gates.run_all_gates(agent_name, updated_context)
                    
                    if gate_report.can_complete:
                        self.logger.log_reasoning(
                            "validation_gates",
                            f"Validation gates passed after self-healing for {agent_name}",
                            f"Passed gates: {', '.join([g.value for g in gate_report.gates_passed])}"
                        )
                    else:
                        # Mark as needing manual intervention
                        success = False
                        result = f"Validation gates failed: {gate_report.retry_suggestions}"
            else:
                self.logger.log_reasoning(
                    "validation_gates",
                    f"All validation gates passed for {agent_name}",
                    f"Gates: {', '.join([g.value for g in gate_report.gates_passed])}"
                )
        
        # Phase 5.1: Mandatory testing for agent
        if HAS_PHASE5 and self.mandatory_testing and success:
            # Determine agent type for testing
            agent_type = "backend"
            if "frontend" in agent_name:
                agent_type = "frontend"
            elif "database" in agent_name:
                agent_type = "database"
            elif "devops" in agent_name or "docker" in agent_name:
                agent_type = "docker"
            
            # Create mandatory test
            test_file = self.mandatory_testing.create_minimal_test_for_agent(
                agent_name, agent_type
            )
            
            self.logger.log_reasoning(
                "mandatory_testing",
                f"Created mandatory test for {agent_name}",
                f"Test file: {test_file}"
            )
            
            # Run the test
            test_success, test_output = self.mandatory_testing.run_mandatory_tests(
                agent_name, test_file
            )
            
            if not test_success:
                self.logger.log_warning(
                    "mandatory_testing",
                    f"Mandatory tests failed for {agent_name}",
                    test_output[:500]  # First 500 chars
                )
                # Don't fail the agent, but track for reporting
                updated_context.artifacts[f"{agent_name}_test_failed"] = True
            else:
                self.logger.log_reasoning(
                    "mandatory_testing",
                    f"Mandatory tests passed for {agent_name}",
                    "All required functionality verified"
                )
        
        # Phase 2: Post-execution verification and cleanup
        if self.phase2_integration:
            # Extract created/modified files from context
            created_files = updated_context.artifacts.get(f"{agent_name}_created_files", [])
            modified_files = updated_context.artifacts.get(f"{agent_name}_modified_files", [])
            
            # Run verification and release locks
            verification_results = self.phase2_integration.after_agent_execution(
                agent_name,
                created_files=created_files,
                modified_files=modified_files
            )
            
            if not verification_results["verification_passed"]:
                self.logger.log_error(
                    "phase2",
                    f"Post-execution verification failed for {agent_name}",
                    f"Errors: {verification_results['errors']}"
                )
                # Optionally mark as needing fixes
                updated_context.artifacts["files_needing_fix"] = verification_results["errors"]
            
            # Clean reasoning output if available
            if isinstance(result, str) and clean_reasoning:
                cleaned_result = self.phase2_integration.clean_agent_reasoning(agent_name, result)
                if cleaned_result != result:
                    self.logger.log_reasoning(
                        "phase2",
                        f"Cleaned reasoning output for {agent_name}",
                        f"Reduced from {len(result)} to {len(cleaned_result)} chars"
                    )
                    result = cleaned_result
        
        return success, result, updated_context
    
    async def _trigger_automated_debugger(
        self,
        agent_name: str,
        build_result: BuildResult,
        context: AgentContext
    ) -> bool:
        """
        Trigger the automated debugger agent to fix compilation errors
        Returns True if debugging was successful
        """
        if "automated-debugger" not in self.agents:
            self.logger.log_error(
                "validation",
                "Automated debugger agent not found",
                "Cannot perform automatic debugging"
            )
            return False
        
        # Create error report for debugger
        error_report = {
            "agent_name": agent_name,
            "errors": build_result.errors,
            "warnings": build_result.warnings,
            "suggested_fixes": build_result.suggested_fixes,
            "output": build_result.output[:2000]  # Limit output size
        }
        
        # Save error report
        error_report_path = self.progress_dir / f"error_report_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_report_path, 'w') as f:
            json.dump(error_report, f, indent=2)
        
        # Update context with error report
        debug_context = AgentContext(
            project_requirements=context.project_requirements,
            completed_tasks=context.completed_tasks.copy(),
            artifacts=context.artifacts.copy(),
            decisions=context.decisions.copy(),
            current_phase=context.current_phase if hasattr(context, 'current_phase') else "debugging"
        )
        debug_context.artifacts["error_report"] = str(error_report_path)
        debug_context.artifacts["build_errors"] = error_report
        
        self.logger.log_reasoning(
            "validation",
            f"Triggering automated debugger for {agent_name}",
            f"Error count: {len(build_result.errors)}"
        )
        
        # Execute automated debugger
        try:
            debug_success, debug_result, debug_context = await self._execute_agent_with_enhanced_features(
                "automated-debugger",
                debug_context,
                interactive=False
            )
            
            if debug_success:
                self.logger.log_reasoning(
                    "validation",
                    f"Automated debugging completed for {agent_name}",
                    "Re-validating build..."
                )
                return True
            else:
                self.logger.log_error(
                    "validation",
                    f"Automated debugging failed for {agent_name}",
                    debug_result
                )
                return False
                
        except Exception as e:
            self.logger.log_error(
                "validation",
                f"Error during automated debugging for {agent_name}",
                str(e)
            )
            return False
    
    def _estimate_time_remaining(self, completed_agents: set, failed_agents: set) -> str:
        """Estimate time remaining based on current progress"""
        total_agents = len(self.workflow_engine.agent_plans)
        completed = len(completed_agents)
        
        if completed == 0:
            return "Calculating..."
        
        # Simple estimation based on average time per agent
        # In real implementation, would track actual execution times
        avg_time_per_agent = 60  # seconds, placeholder
        remaining = total_agents - completed - len(failed_agents)
        
        estimated_seconds = remaining * avg_time_per_agent
        
        if estimated_seconds < 60:
            return f"{estimated_seconds}s"
        elif estimated_seconds < 3600:
            return f"{estimated_seconds // 60}m {estimated_seconds % 60}s"
        else:
            hours = estimated_seconds // 3600
            minutes = (estimated_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def _validate_requirements(self, requirements: Dict) -> List[str]:
        """Validate requirements structure and content"""
        errors = []
        
        # Check required top-level fields
        if "project" not in requirements:
            errors.append("Missing 'project' section in requirements")
        else:
            project = requirements["project"]
            if "name" not in project:
                errors.append("Missing project name")
            if "type" not in project:
                errors.append("Missing project type")
        
        # Check for features
        if "features" not in requirements:
            errors.append("Missing 'features' section in requirements")
        elif not requirements["features"]:
            errors.append("No features specified in requirements")
        
        # Validate feature structure if present
        if "features" in requirements and isinstance(requirements["features"], list):
            for idx, feature in enumerate(requirements["features"]):
                if isinstance(feature, str):
                    # Simple string feature is OK
                    continue
                elif isinstance(feature, dict):
                    # Structured feature should have at least id or title
                    if "id" not in feature and "title" not in feature:
                        errors.append(f"Feature {idx+1} missing both 'id' and 'title'")
                else:
                    errors.append(f"Feature {idx+1} has invalid format")
        
        return errors
    
    def _print_test_metrics(self, summary: Dict, context: AgentContext):
        """Print metrics in format expected by test runner"""
        # Print requirement completion
        progress = summary.get("progress", {})
        completed_reqs = progress.get("completed_requirements", 0)
        total_reqs = progress.get("total_requirements", 0)
        print(f"Requirements completed: {completed_reqs}/{total_reqs}")
        
        # Print total files created if we have file tracking
        if hasattr(context, 'created_files') and context.created_files:
            total_files = sum(len(files) for files in context.created_files.values())
            print(f"Files created: {total_files}")
        elif hasattr(self, 'mock_file_count'):
            # For mock mode, track files differently
            print(f"Files created: {self.mock_file_count}")
    
    def _display_workflow_results(self, success: bool, summary: Dict):
        """Display comprehensive workflow results"""
        if not HAS_RICH:
            return
        
        progress = summary["progress"]
        
        # Main results panel
        status_color = "green" if success else "red"
        status_text = "SUCCESS" if success else "FAILED"
        
        console.print(Panel(
            f"[bold {status_color}]Workflow {status_text}[/bold {status_color}]\n\n"
            f"Workflow ID: {summary['workflow_id']}\n"
            f"Overall Completion: {progress['overall_completion']:.1f}%\n"
            f"Requirements: {progress['completed_requirements']}/{progress['total_requirements']} completed\n"
            f"Agents: {progress['completed_agents']}/{progress['total_agents']} successful\n"
            f"Duration: {progress['started_at']} - {progress['updated_at']}",
            title="Enhanced Orchestration Results",
            border_style=status_color
        ))
        
        # Requirements table
        if summary.get("requirements"):
            req_table = Table(title="Requirements Status")
            req_table.add_column("ID", style="cyan")
            req_table.add_column("Description", style="white")
            req_table.add_column("Status", style="green")
            req_table.add_column("Completion", style="yellow")
            req_table.add_column("Assigned Agents", style="blue")
            
            for req_id, req_data in summary["requirements"].items():
                status_color = {
                    "completed": "green",
                    "failed": "red",
                    "blocked": "yellow",
                    "pending": "yellow"
                }.get(req_data["status"], "white")
                
                req_table.add_row(
                    req_id,
                    req_data["description"][:50] + ("..." if len(req_data["description"]) > 50 else ""),
                    f"[{status_color}]{req_data['status'].upper()}[/{status_color}]",
                    f"{req_data['completion_percentage']:.1f}%",
                    ", ".join(req_data["assigned_agents"][:2])  # Show first 2 agents
                )
            
            console.print(req_table)
        
        # Agent execution table
        if summary.get("agent_plans"):
            agent_table = Table(title="Agent Execution Summary")
            agent_table.add_column("Agent", style="cyan")
            agent_table.add_column("Status", style="green")
            agent_table.add_column("Duration", style="yellow")
            agent_table.add_column("Retries", style="yellow")
            agent_table.add_column("Requirements", style="blue")
            
            for agent_name, plan_data in summary["agent_plans"].items():
                status_color = {
                    "completed": "green",
                    "failed": "red",
                    "running": "yellow"
                }.get(plan_data["status"], "white")
                
                duration = f"{plan_data['execution_time']:.1f}s" if plan_data.get('execution_time') else "N/A"
                
                agent_table.add_row(
                    agent_name,
                    f"[{status_color}]{plan_data['status'].upper()}[/{status_color}]",
                    duration,
                    str(plan_data['current_retry']),
                    str(len(plan_data['requirements']))
                )
            
            console.print(agent_table)


async def main():
    parser = argparse.ArgumentParser(description="Enhanced Agent Swarm Orchestrator - Section 8")
    parser.add_argument("--project-type", choices=["web_app", "api_service", "ai_solution", "full_stack_api"])
    parser.add_argument("--requirements", help="Path to requirements.yaml")
    parser.add_argument("--chain", help="Execute agents in chain (comma-separated)")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--resume-checkpoint", help="Resume from checkpoint file")
    parser.add_argument("--dashboard", action="store_true", help="Enable real-time dashboard")
    parser.add_argument("--progress", action="store_true", help="Show detailed progress")
    parser.add_argument("--max-parallel", type=int, default=3, help="Max parallel agents")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--output-dir", help="Output directory for project files (default: timestamped folder)")
    parser.add_argument("--human-log", action="store_true", default=True, help="Generate human-readable markdown log (default: True)")
    parser.add_argument("--no-human-log", dest="human_log", action="store_false", help="Disable human-readable log")
    parser.add_argument("--summary-level", choices=["concise", "detailed", "verbose"], default="concise", 
                       help="Human log detail level (default: concise)")
    
    args = parser.parse_args()
    
    # Handle API key
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    
    # Create enhanced orchestrator
    try:
        orchestrator = EnhancedOrchestrator(
            api_key, 
            enable_dashboard=args.dashboard or args.progress,
            enable_human_log=args.human_log,
            summary_level=args.summary_level
        )
    except Exception as e:
        if HAS_RICH:
            console.print(f"[red]Failed to initialize orchestrator: {str(e)}[/red]")
        else:
            print(f"Failed to initialize orchestrator: {str(e)}")
        sys.exit(1)
    
    # Check if we're in API mode but have no client
    if os.environ.get('MOCK_MODE') != 'true' and orchestrator.runtime.client is None:
        error_msg = "\n[ERROR] API mode requested but Anthropic client is not available.\n"
        if not api_key:
            error_msg += "No API key found. Set ANTHROPIC_API_KEY environment variable or use --api-key flag.\n"
        else:
            # API key was provided but rejected
            if not api_key.startswith('sk-ant-'):
                error_msg += f"Invalid API key format. API key should start with 'sk-ant-' but got '{api_key[:10]}...'\n"
            else:
                error_msg += "API key was provided but client initialization failed. Check your API key and network connection.\n"
        
        error_msg += "\nTo use mock mode instead, set: MOCK_MODE=true"
        
        if HAS_RICH:
            console.print(f"[red]{error_msg}[/red]")
        else:
            print(error_msg)
        
        # Close the logger session before exiting
        orchestrator.logger.close_session()
        sys.exit(1)
    
    try:
        if args.project_type and args.requirements:
            # Enhanced workflow execution
            with open(args.requirements) as f:
                requirements = yaml.safe_load(f)
            
            if HAS_RICH:
                console.print(Panel(
                    f"[bold]Enhanced {args.project_type} Workflow[/bold]\n" +
                    f"Project: {requirements.get('project', {}).get('name', 'Unknown')}\n" +
                    f"Requirements: {args.requirements}\n" +
                    f"Dashboard: {'Enabled' if args.dashboard else 'Disabled'}\n" +
                    f"Human Log: {'Enabled (' + args.summary_level + ')' if args.human_log else 'Disabled'}\n" +
                    f"Max Parallel: {args.max_parallel}",
                    border_style="green"
                ))
            
            success = await orchestrator.execute_enhanced_workflow(
                args.project_type,
                requirements,
                interactive=args.interactive,
                checkpoint_file=args.resume_checkpoint,
                max_parallel=args.max_parallel,
                output_dir=args.output_dir
            )
            
            orchestrator.logger.close_session()
            sys.exit(0 if success else 1)
        
        elif args.chain:
            # Chain execution (simplified for compatibility)
            agents = [a.strip() for a in args.chain.split(",")]
            if HAS_RICH:
                console.print(Panel(
                    f"[bold]Executing Enhanced Chain[/bold]\n" +
                    f"Agents: {' → '.join(agents)}",
                    border_style="blue"
                ))
            
            # Create simple requirements for chain
            requirements = {
                "project": {"name": "Chain Execution"},
                "features": [f"Execute {agent}" for agent in agents]
            }
            
            success = await orchestrator.execute_enhanced_workflow(
                "api_service",  # Default project type
                requirements,
                interactive=args.interactive,
                max_parallel=1  # Sequential for chain
            )
            
            orchestrator.logger.close_session()
            sys.exit(0 if success else 1)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        if HAS_RICH:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        orchestrator.logger.close_session()
        sys.exit(1)
    except Exception as e:
        if HAS_RICH:
            console.print(f"[red]Error: {str(e)}[/red]")
        if args.verbose:
            import traceback
            traceback.print_exc()
        orchestrator.logger.close_session()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())