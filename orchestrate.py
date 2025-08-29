#!/usr/bin/env python3
"""
Agent Swarm Orchestrator

Automates project execution using the optimized 15-agent swarm.
Supports parallel execution, sequential chains, and custom workflows.

Usage:
    uv run orchestrate.py --project-type=web_app --requirements=requirements.yaml
    uv run orchestrate.py --chain=project-architect,rapid-builder,quality-guardian
    uv run orchestrate.py --parallel=frontend-specialist,api-integrator,documentation-writer
"""

import argparse
import asyncio
import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml

@dataclass
class AgentConfig:
    """Configuration for a single agent"""
    name: str
    model: str
    tools: List[str]
    color: str
    parallel_group: Optional[str] = None
    dependencies: List[str] = None

@dataclass  
class ProjectRequirements:
    """Project requirements structure"""
    project: Dict
    features: List[str] 
    tech_overrides: Dict = None
    constraints: Dict = None
    success_metrics: List[str] = None

class AgentOrchestrator:
    """Main orchestrator for agent workflow automation"""
    
    def __init__(self, config_path: str = ".claude/agents"):
        self.config_path = Path(config_path)
        self.agents = self._load_agent_configs()
        self.workflows = self._define_workflows()
        
    def _load_agent_configs(self) -> Dict[str, AgentConfig]:
        """Load agent configurations from .md files"""
        agents = {}
        
        # Core Development Agents (Tier 1)
        agents.update({
            "project-architect": AgentConfig("project-architect", "opus", ["Write", "Read", "Glob", "Grep", "Task"], "blue"),
            "rapid-builder": AgentConfig("rapid-builder", "sonnet", ["Write", "Read", "MultiEdit", "Bash", "Glob", "Task"], "green"),
            "ai-specialist": AgentConfig("ai-specialist", "opus", ["Write", "Read", "MultiEdit", "Bash", "WebFetch", "Task"], "cyan"),
            "quality-guardian": AgentConfig("quality-guardian", "sonnet", ["Read", "Write", "Bash", "Grep", "Glob", "Task"], "red"),
            "devops-engineer": AgentConfig("devops-engineer", "sonnet", ["Bash", "Write", "Read", "Task"], "orange"),
        })
        
        # Specialized Technical Agents (Tier 2)  
        agents.update({
            "api-integrator": AgentConfig("api-integrator", "haiku", ["Write", "Read", "Bash", "WebFetch", "Task"], "yellow"),
            "database-expert": AgentConfig("database-expert", "sonnet", ["Write", "Read", "Bash", "Grep", "Task"], "purple"),
            "frontend-specialist": AgentConfig("frontend-specialist", "sonnet", ["Write", "Read", "MultiEdit", "Bash", "Task"], "pink"),
            "performance-optimizer": AgentConfig("performance-optimizer", "sonnet", ["Read", "Bash", "Grep", "Task"], "indigo"),
            "documentation-writer": AgentConfig("documentation-writer", "haiku", ["Write", "Read", "Grep", "Task"], "green"),
        })
        
        # Orchestration & Support Agents (Tier 3)
        agents.update({
            "project-orchestrator": AgentConfig("project-orchestrator", "opus", ["Task", "Write", "Read"], "gold"),
            "requirements-analyst": AgentConfig("requirements-analyst", "sonnet", ["Write", "Read", "Task"], "blue"),
            "code-migrator": AgentConfig("code-migrator", "sonnet", ["Read", "Write", "MultiEdit", "Grep", "Bash", "Task"], "orange"),
            "debug-specialist": AgentConfig("debug-specialist", "opus", ["Read", "Bash", "Grep", "Glob", "Task"], "red"),
            "meta-agent": AgentConfig("meta-agent", "opus", ["Write", "MultiEdit", "WebFetch", "Task"], "cyan"),
        })
        
        return agents
    
    def _define_workflows(self) -> Dict[str, List]:
        """Define orchestration patterns for different project types"""
        return {
            "web_app": [
                ["requirements-analyst"],  # Phase 1: Analysis
                ["project-architect", "database-expert"],  # Phase 2: Architecture (parallel)
                ["rapid-builder"],  # Phase 3: Scaffolding
                ["frontend-specialist", "api-integrator", "documentation-writer"],  # Phase 4: Development (parallel)
                ["ai-specialist"],  # Phase 5: AI features (if needed)
                ["quality-guardian"],  # Phase 6: Testing
                ["performance-optimizer"],  # Phase 7: Optimization
                ["devops-engineer"]  # Phase 8: Deployment
            ],
            "api_service": [
                ["requirements-analyst"],
                ["project-architect", "database-expert"],
                ["rapid-builder"],
                ["api-integrator", "documentation-writer"],
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
                ["documentation-writer"],
                ["devops-engineer"]
            ],
            "mobile_app": [
                ["requirements-analyst"],
                ["project-architect"],
                ["rapid-builder"],
                ["frontend-specialist", "api-integrator"],
                ["quality-guardian"],
                ["performance-optimizer"],
                ["documentation-writer"]
            ]
        }
    
    def load_requirements(self, requirements_file: str) -> ProjectRequirements:
        """Load project requirements from YAML file"""
        with open(requirements_file, 'r') as f:
            data = yaml.safe_load(f)
        return ProjectRequirements(**data)
    
    async def execute_agent(self, agent_name: str, context: str = "") -> Tuple[bool, str]:
        """Execute a single agent using Claude Code Task tool"""
        try:
            print(f"🤖 Executing {agent_name}...")
            
            # Simulate agent execution (in real implementation, this would call Claude Code)
            # For demonstration, we'll simulate different execution times
            execution_time = {
                "requirements-analyst": 2,
                "project-architect": 5,
                "rapid-builder": 8,
                "ai-specialist": 6,
                "quality-guardian": 4,
                "devops-engineer": 3,
                "frontend-specialist": 6,
                "api-integrator": 3,
                "database-expert": 4,
                "performance-optimizer": 3,
                "documentation-writer": 2,
                "project-orchestrator": 1,
                "code-migrator": 5,
                "debug-specialist": 4,
                "meta-agent": 3
            }
            
            await asyncio.sleep(execution_time.get(agent_name, 3))
            
            print(f"✅ {agent_name} completed successfully")
            return True, f"{agent_name} execution completed"
            
        except Exception as e:
            print(f"❌ {agent_name} failed: {str(e)}")
            return False, str(e)
    
    async def execute_parallel_group(self, agents: List[str], context: str = "") -> Dict[str, Tuple[bool, str]]:
        """Execute multiple agents in parallel"""
        print(f"🔀 Executing parallel group: {', '.join(agents)}")
        
        tasks = []
        for agent in agents:
            if agent in self.agents:
                tasks.append(self.execute_agent(agent, context))
            else:
                print(f"⚠️  Unknown agent: {agent}")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            agent: result if not isinstance(result, Exception) else (False, str(result))
            for agent, result in zip(agents, results)
        }
    
    async def execute_workflow(self, project_type: str, requirements: ProjectRequirements) -> bool:
        """Execute complete workflow for project type"""
        if project_type not in self.workflows:
            print(f"❌ Unknown project type: {project_type}")
            return False
        
        workflow = self.workflows[project_type]
        print(f"🚀 Starting {project_type} workflow with {len(workflow)} phases")
        
        context = f"Project: {requirements.project.get('name', 'Unknown')}\nType: {project_type}\nFeatures: {', '.join(requirements.features)}"
        
        # Execute project-orchestrator first to coordinate
        await self.execute_agent("project-orchestrator", context)
        
        for phase_num, phase_agents in enumerate(workflow, 1):
            print(f"\n📋 Phase {phase_num}/{len(workflow)}: {', '.join(phase_agents)}")
            
            if len(phase_agents) == 1:
                # Sequential execution
                success, result = await self.execute_agent(phase_agents[0], context)
                if not success:
                    print(f"❌ Workflow failed in phase {phase_num}")
                    return False
            else:
                # Parallel execution
                results = await self.execute_parallel_group(phase_agents, context)
                if not all(success for success, _ in results.values()):
                    print(f"❌ Workflow failed in phase {phase_num}")
                    return False
        
        print(f"\n🎉 {project_type} workflow completed successfully!")
        return True
    
    async def execute_chain(self, agents: List[str], context: str = "") -> bool:
        """Execute agents in sequential chain"""
        print(f"⛓️  Executing agent chain: {' → '.join(agents)}")
        
        for agent in agents:
            if agent not in self.agents:
                print(f"❌ Unknown agent: {agent}")
                return False
            
            success, result = await self.execute_agent(agent, context)
            if not success:
                print(f"❌ Chain failed at {agent}")
                return False
        
        print("✅ Agent chain completed successfully!")
        return True
    
    def generate_requirements_template(self, output_file: str = "requirements.yaml"):
        """Generate requirements.yaml template"""
        template = {
            "project": {
                "name": "MyApp",
                "type": "web_app",  # web_app, mobile_app, api_service, ai_solution
                "timeline": "2 weeks",
                "priority": "MVP"  # MVP, full_feature, enterprise
            },
            "features": [
                "User authentication",
                "Real-time messaging", 
                "AI-powered recommendations"
            ],
            "tech_overrides": {
                "frontend": {
                    "framework": "Next.js"
                },
                "backend": {
                    "language": "Python",
                    "framework": "Django"
                }
            },
            "constraints": {
                "budget": "$5000",
                "team_size": 1,
                "deployment": "Heroku"
            },
            "success_metrics": [
                "1000+ users in month 1",
                "<200ms API response time",
                "99.9% uptime"
            ]
        }
        
        with open(output_file, 'w') as f:
            yaml.dump(template, f, default_flow_style=False, indent=2)
        
        print(f"📝 Requirements template created: {output_file}")

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Agent Swarm Orchestrator")
    parser.add_argument("--project-type", choices=["web_app", "mobile_app", "api_service", "ai_solution"], help="Project type for workflow execution")
    parser.add_argument("--requirements", help="Path to requirements.yaml file")
    parser.add_argument("--chain", help="Execute agents in sequential chain (comma-separated)")
    parser.add_argument("--parallel", help="Execute agents in parallel (comma-separated)")
    parser.add_argument("--generate-template", action="store_true", help="Generate requirements.yaml template")
    parser.add_argument("--list-agents", action="store_true", help="List available agents")
    
    args = parser.parse_args()
    
    orchestrator = AgentOrchestrator()
    
    if args.generate_template:
        orchestrator.generate_requirements_template()
        return
    
    if args.list_agents:
        print("Available Agents:")
        for name, config in orchestrator.agents.items():
            print(f"  • {name} ({config.model}) - {config.color}")
        return
    
    if args.project_type and args.requirements:
        # Full workflow execution
        requirements = orchestrator.load_requirements(args.requirements)
        success = await orchestrator.execute_workflow(args.project_type, requirements)
        sys.exit(0 if success else 1)
    
    elif args.chain:
        # Sequential chain execution
        agents = [agent.strip() for agent in args.chain.split(",")]
        success = await orchestrator.execute_chain(agents)
        sys.exit(0 if success else 1)
    
    elif args.parallel:
        # Parallel execution
        agents = [agent.strip() for agent in args.parallel.split(",")]
        results = await orchestrator.execute_parallel_group(agents)
        success = all(success for success, _ in results.values())
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())