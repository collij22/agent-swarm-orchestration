#!/usr/bin/env python3
"""
LLM Provider Integration for Agent Swarm
Integrates multi-LLM support into the existing agent runtime

Features:
- Seamless integration with existing AnthropicAgentRunner
- Automatic provider selection based on agent requirements
- Cost optimization through intelligent model selection
- Fallback chains for improved reliability
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

# Import existing components
try:
    from agent_runtime import AnthropicAgentRunner
except ImportError:
    AnthropicAgentRunner = None

try:
    from llm_providers import (
        MultiLLMOrchestrator,
        LLMProvider,
        ModelTier,
        select_model_for_task,
        LLMResponse
    )
except ImportError:
    print("Error: llm_providers module not found")
    MultiLLMOrchestrator = None

logger = logging.getLogger(__name__)

@dataclass
class AgentModelMapping:
    """Maps agents to optimal models and tiers"""
    agent_name: str
    preferred_provider: LLMProvider
    preferred_model: str
    tier: ModelTier
    fallback_tier: ModelTier
    task_type: str

# Agent to model mapping configuration
AGENT_MODEL_MAPPINGS = {
    # Core Development Agents (Tier 1)
    "rapid-builder": AgentModelMapping(
        agent_name="rapid-builder",
        preferred_provider=LLMProvider.ANTHROPIC,
        preferred_model="claude-3-5-sonnet-20241022",
        tier=ModelTier.STANDARD,
        fallback_tier=ModelTier.FAST,
        task_type="code_generation"
    ),
    "frontend-specialist": AgentModelMapping(
        agent_name="frontend-specialist",
        preferred_provider=LLMProvider.ANTHROPIC,
        preferred_model="claude-3-5-sonnet-20241022",
        tier=ModelTier.STANDARD,
        fallback_tier=ModelTier.FAST,
        task_type="code_generation"
    ),
    "quality-guardian": AgentModelMapping(
        agent_name="quality-guardian",
        preferred_provider=LLMProvider.OPENAI,
        preferred_model="gpt-4-turbo-preview",
        tier=ModelTier.PREMIUM,
        fallback_tier=ModelTier.STANDARD,
        task_type="complex_analysis"
    ),
    
    # Specialized Technical Agents (Tier 2)
    "database-expert": AgentModelMapping(
        agent_name="database-expert",
        preferred_provider=LLMProvider.ANTHROPIC,
        preferred_model="claude-3-5-sonnet-20241022",
        tier=ModelTier.STANDARD,
        fallback_tier=ModelTier.FAST,
        task_type="code_generation"
    ),
    "devops-engineer": AgentModelMapping(
        agent_name="devops-engineer",
        preferred_provider=LLMProvider.OPENAI,
        preferred_model="gpt-4",
        tier=ModelTier.STANDARD,
        fallback_tier=ModelTier.FAST,
        task_type="code_generation"
    ),
    "api-integrator": AgentModelMapping(
        agent_name="api-integrator",
        preferred_provider=LLMProvider.OPENAI,
        preferred_model="gpt-4-turbo-preview",
        tier=ModelTier.STANDARD,
        fallback_tier=ModelTier.FAST,
        task_type="code_generation"
    ),
    "performance-optimizer": AgentModelMapping(
        agent_name="performance-optimizer",
        preferred_provider=LLMProvider.ANTHROPIC,
        preferred_model="claude-3-5-sonnet-20241022",
        tier=ModelTier.PREMIUM,
        fallback_tier=ModelTier.STANDARD,
        task_type="complex_analysis"
    ),
    "debug-specialist": AgentModelMapping(
        agent_name="debug-specialist",
        preferred_provider=LLMProvider.ANTHROPIC,
        preferred_model="claude-3-opus-20240229",
        tier=ModelTier.PREMIUM,
        fallback_tier=ModelTier.STANDARD,
        task_type="complex_analysis"
    ),
    "documentation-writer": AgentModelMapping(
        agent_name="documentation-writer",
        preferred_provider=LLMProvider.GEMINI,
        preferred_model="gemini-pro",
        tier=ModelTier.FAST,
        fallback_tier=ModelTier.FAST,
        task_type="simple_qa"
    ),
    "ai-specialist": AgentModelMapping(
        agent_name="ai-specialist",
        preferred_provider=LLMProvider.OPENAI,
        preferred_model="gpt-4-turbo-preview",
        tier=ModelTier.PREMIUM,
        fallback_tier=ModelTier.STANDARD,
        task_type="code_generation"
    ),
    "security-auditor": AgentModelMapping(
        agent_name="security-auditor",
        preferred_provider=LLMProvider.ANTHROPIC,
        preferred_model="claude-3-5-sonnet-20241022",
        tier=ModelTier.STANDARD,
        fallback_tier=ModelTier.STANDARD,
        task_type="complex_analysis"
    ),
    
    # Orchestration Agents (Tier 3)
    "project-orchestrator": AgentModelMapping(
        agent_name="project-orchestrator",
        preferred_provider=LLMProvider.ANTHROPIC,
        preferred_model="claude-3-opus-20240229",
        tier=ModelTier.PREMIUM,
        fallback_tier=ModelTier.STANDARD,
        task_type="complex_analysis"
    ),
    "project-architect": AgentModelMapping(
        agent_name="project-architect",
        preferred_provider=LLMProvider.ANTHROPIC,
        preferred_model="claude-3-opus-20240229",
        tier=ModelTier.PREMIUM,
        fallback_tier=ModelTier.STANDARD,
        task_type="complex_analysis"
    ),
    "requirements-analyst": AgentModelMapping(
        agent_name="requirements-analyst",
        preferred_provider=LLMProvider.OPENAI,
        preferred_model="gpt-4",
        tier=ModelTier.STANDARD,
        fallback_tier=ModelTier.STANDARD,
        task_type="complex_analysis"
    ),
    "code-migrator": AgentModelMapping(
        agent_name="code-migrator",
        preferred_provider=LLMProvider.ANTHROPIC,
        preferred_model="claude-3-5-sonnet-20241022",
        tier=ModelTier.STANDARD,
        fallback_tier=ModelTier.FAST,
        task_type="code_generation"
    ),
    "meta-agent": AgentModelMapping(
        agent_name="meta-agent",
        preferred_provider=LLMProvider.ANTHROPIC,
        preferred_model="claude-3-opus-20240229",
        tier=ModelTier.PREMIUM,
        fallback_tier=ModelTier.STANDARD,
        task_type="complex_analysis"
    ),
}

class EnhancedAgentRunner:
    """
    Enhanced agent runner with multi-LLM support
    Extends the existing AnthropicAgentRunner with provider flexibility
    """
    
    def __init__(
        self,
        agent_dir: str = ".claude/agents",
        sfa_dir: str = "sfa",
        enable_multi_llm: bool = True,
        enable_cache: bool = True,
        enable_fallback: bool = True,
        cost_optimization: bool = True
    ):
        """
        Initialize enhanced agent runner
        
        Args:
            agent_dir: Directory containing agent definitions
            sfa_dir: Directory for standalone agents
            enable_multi_llm: Use multi-LLM support
            enable_cache: Enable response caching
            enable_fallback: Enable provider fallback
            cost_optimization: Optimize for cost when possible
        """
        self.agent_dir = Path(agent_dir)
        self.sfa_dir = Path(sfa_dir)
        self.enable_multi_llm = enable_multi_llm
        self.cost_optimization = cost_optimization
        
        # Initialize base runner if available
        if AnthropicAgentRunner:
            self.base_runner = AnthropicAgentRunner(agent_dir, sfa_dir)
        else:
            self.base_runner = None
            logger.warning("Base AnthropicAgentRunner not available")
        
        # Initialize multi-LLM orchestrator
        if enable_multi_llm and MultiLLMOrchestrator:
            self.orchestrator = MultiLLMOrchestrator(
                enable_cache=enable_cache,
                enable_fallback=enable_fallback
            )
        else:
            self.orchestrator = None
        
        # Track usage per agent
        self.agent_usage = {}
    
    async def run_agent_multi_llm(
        self,
        agent_name: str,
        requirements: str,
        context: Optional[Dict[str, Any]] = None,
        override_provider: Optional[LLMProvider] = None,
        override_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run an agent using multi-LLM support
        
        Args:
            agent_name: Name of the agent to run
            requirements: Requirements/prompt for the agent
            context: Additional context for the agent
            override_provider: Override the default provider
            override_model: Override the default model
            
        Returns:
            Agent execution result
        """
        if not self.orchestrator:
            # Fallback to base runner
            if self.base_runner:
                return await self.base_runner.run_agent(agent_name, requirements, context)
            else:
                raise ValueError("No LLM runner available")
        
        # Get agent configuration
        agent_config = AGENT_MODEL_MAPPINGS.get(agent_name)
        if not agent_config:
            # Use default configuration
            agent_config = AgentModelMapping(
                agent_name=agent_name,
                preferred_provider=LLMProvider.ANTHROPIC,
                preferred_model="claude-3-5-sonnet-20241022",
                tier=ModelTier.STANDARD,
                fallback_tier=ModelTier.FAST,
                task_type="code_generation"
            )
        
        # Prepare system prompt from agent definition
        system_prompt = self._load_agent_definition(agent_name)
        
        # Build full prompt
        full_prompt = self._build_agent_prompt(requirements, context, agent_name)
        
        # Determine model and provider
        if override_model:
            model = override_model
            provider = override_provider
        elif override_provider:
            provider = override_provider
            model = None  # Let orchestrator select
        elif self.cost_optimization and self._is_simple_task(requirements):
            # Use cheaper model for simple tasks
            tier = agent_config.fallback_tier
            provider = None
            model = None
        else:
            # Use preferred configuration
            provider = agent_config.preferred_provider
            model = agent_config.preferred_model
            tier = agent_config.tier
        
        try:
            # Generate response
            response = await self.orchestrator.generate(
                prompt=full_prompt,
                model=model,
                provider=provider,
                tier=tier if not model else None,
                system=system_prompt,
                max_tokens=4000,
                temperature=0.7
            )
            
            # Track usage
            if agent_name not in self.agent_usage:
                self.agent_usage[agent_name] = {
                    "requests": 0,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "providers_used": {}
                }
            
            self.agent_usage[agent_name]["requests"] += 1
            self.agent_usage[agent_name]["total_cost"] += response.cost
            self.agent_usage[agent_name]["total_tokens"] += response.usage.get("total_tokens", 0)
            
            provider_name = response.provider.value
            if provider_name not in self.agent_usage[agent_name]["providers_used"]:
                self.agent_usage[agent_name]["providers_used"][provider_name] = 0
            self.agent_usage[agent_name]["providers_used"][provider_name] += 1
            
            # Parse and return result
            return {
                "success": True,
                "agent": agent_name,
                "response": response.content,
                "provider": response.provider.value,
                "model": response.model,
                "cost": response.cost,
                "cached": response.cached,
                "usage": response.usage
            }
            
        except Exception as e:
            logger.error(f"Error running agent {agent_name}: {e}")
            return {
                "success": False,
                "agent": agent_name,
                "error": str(e)
            }
    
    def _load_agent_definition(self, agent_name: str) -> str:
        """Load agent definition as system prompt"""
        agent_file = self.agent_dir / f"{agent_name}.md"
        
        if agent_file.exists():
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract the main content after frontmatter
                if '---' in content:
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        return parts[2].strip()
                return content
        
        # Default system prompt
        return f"You are {agent_name}, a specialized AI agent focused on technical tasks."
    
    def _build_agent_prompt(
        self,
        requirements: str,
        context: Optional[Dict[str, Any]],
        agent_name: str
    ) -> str:
        """Build the full prompt for the agent"""
        prompt_parts = []
        
        # Add context if provided
        if context:
            prompt_parts.append("Context:")
            for key, value in context.items():
                prompt_parts.append(f"- {key}: {value}")
            prompt_parts.append("")
        
        # Add requirements
        prompt_parts.append("Requirements:")
        prompt_parts.append(requirements)
        
        # Add instruction
        prompt_parts.append("")
        prompt_parts.append(f"As {agent_name}, complete the above requirements following your specialized expertise and best practices.")
        
        return "\n".join(prompt_parts)
    
    def _is_simple_task(self, requirements: str) -> bool:
        """Determine if a task is simple enough for a cheaper model"""
        simple_indicators = [
            "list", "explain", "describe", "what is", "how to",
            "documentation", "readme", "comments", "format"
        ]
        
        requirements_lower = requirements.lower()
        
        # Check word count (simple tasks are usually shorter)
        if len(requirements.split()) < 20:
            return True
        
        # Check for simple task indicators
        for indicator in simple_indicators:
            if indicator in requirements_lower:
                return True
        
        return False
    
    def get_usage_report(self) -> str:
        """Get detailed usage report for all agents"""
        if not self.agent_usage:
            return "No agent usage recorded yet."
        
        report = """
═══════════════════════════════════════════════════════
                 AGENT USAGE REPORT
═══════════════════════════════════════════════════════
"""
        
        total_cost = 0.0
        total_requests = 0
        
        for agent_name, usage in self.agent_usage.items():
            report += f"""
  {agent_name.upper()}:
    Requests: {usage['requests']:,}
    Total Cost: ${usage['total_cost']:.4f}
    Total Tokens: {usage['total_tokens']:,}
    Providers Used: {', '.join(usage['providers_used'].keys())}
"""
            total_cost += usage['total_cost']
            total_requests += usage['requests']
        
        report += f"""
  ─────────────────────────────────────────────────────
  TOTAL:
    All Requests: {total_requests:,}
    Total Cost: ${total_cost:.4f}
    Average Cost per Request: ${total_cost/total_requests if total_requests > 0 else 0:.4f}
═══════════════════════════════════════════════════════
"""
        return report
    
    def export_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations based on usage"""
        recommendations = []
        
        for agent_name, usage in self.agent_usage.items():
            if usage['requests'] > 10:  # Only analyze agents with sufficient data
                avg_cost = usage['total_cost'] / usage['requests']
                
                # Check if agent is using expensive models for simple tasks
                agent_config = AGENT_MODEL_MAPPINGS.get(agent_name)
                if agent_config and agent_config.tier == ModelTier.PREMIUM:
                    if avg_cost > 0.01:  # More than 1 cent per request
                        recommendations.append({
                            "agent": agent_name,
                            "current_tier": agent_config.tier.value,
                            "recommended_tier": ModelTier.STANDARD.value,
                            "potential_savings": f"${(avg_cost - 0.005) * usage['requests']:.2f}",
                            "reason": "Consider using standard tier for routine tasks"
                        })
        
        return recommendations

class MultiLLMAgentOrchestrator:
    """
    Orchestrates multiple agents with intelligent LLM provider selection
    """
    
    def __init__(
        self,
        agent_runner: Optional[EnhancedAgentRunner] = None,
        parallel_execution: bool = True,
        max_parallel: int = 3
    ):
        """
        Initialize the orchestrator
        
        Args:
            agent_runner: Enhanced agent runner instance
            parallel_execution: Enable parallel agent execution
            max_parallel: Maximum parallel agents
        """
        self.agent_runner = agent_runner or EnhancedAgentRunner()
        self.parallel_execution = parallel_execution
        self.max_parallel = max_parallel
        
        # Track orchestration metrics
        self.metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "total_agents_run": 0,
            "parallel_executions": 0
        }
    
    async def execute_workflow(
        self,
        workflow: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow with multiple agents
        
        Args:
            workflow: List of agent tasks
            context: Shared context for all agents
            
        Returns:
            Workflow execution results
        """
        self.metrics["total_workflows"] += 1
        results = []
        shared_context = context or {}
        
        try:
            # Group tasks by dependencies
            task_groups = self._group_tasks_by_dependencies(workflow)
            
            for group in task_groups:
                if len(group) > 1 and self.parallel_execution:
                    # Execute group in parallel
                    group_results = await self._execute_parallel(group, shared_context)
                    self.metrics["parallel_executions"] += 1
                else:
                    # Execute sequentially
                    group_results = await self._execute_sequential(group, shared_context)
                
                results.extend(group_results)
                
                # Update shared context with results
                for result in group_results:
                    if result.get("success"):
                        shared_context[f"{result['agent']}_output"] = result.get("response", "")
            
            self.metrics["successful_workflows"] += 1
            
            return {
                "success": True,
                "results": results,
                "context": shared_context,
                "metrics": self._calculate_workflow_metrics(results)
            }
            
        except Exception as e:
            self.metrics["failed_workflows"] += 1
            logger.error(f"Workflow execution failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "results": results
            }
    
    async def _execute_parallel(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute tasks in parallel"""
        # Limit parallel execution
        tasks_to_run = tasks[:self.max_parallel]
        
        coroutines = []
        for task in tasks_to_run:
            coroutines.append(
                self.agent_runner.run_agent_multi_llm(
                    agent_name=task["agent"],
                    requirements=task["requirements"],
                    context=context,
                    override_provider=task.get("provider"),
                    override_model=task.get("model")
                )
            )
        
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "agent": tasks_to_run[i]["agent"],
                    "error": str(result)
                })
            else:
                processed_results.append(result)
            
            self.metrics["total_agents_run"] += 1
        
        return processed_results
    
    async def _execute_sequential(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute tasks sequentially"""
        results = []
        
        for task in tasks:
            result = await self.agent_runner.run_agent_multi_llm(
                agent_name=task["agent"],
                requirements=task["requirements"],
                context=context,
                override_provider=task.get("provider"),
                override_model=task.get("model")
            )
            
            results.append(result)
            self.metrics["total_agents_run"] += 1
            
            # Stop on failure if required
            if not result.get("success") and task.get("critical", False):
                break
        
        return results
    
    def _group_tasks_by_dependencies(
        self,
        workflow: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Group tasks by dependencies for parallel execution"""
        # Simple grouping - tasks with no dependencies can run in parallel
        groups = []
        current_group = []
        
        for task in workflow:
            if task.get("depends_on"):
                # Task has dependencies, start new group
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([task])
            else:
                # No dependencies, can run in parallel
                current_group.append(task)
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _calculate_workflow_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for the workflow"""
        total_cost = sum(r.get("cost", 0) for r in results if r.get("success"))
        total_tokens = sum(r.get("usage", {}).get("total_tokens", 0) for r in results if r.get("success"))
        cache_hits = sum(1 for r in results if r.get("cached", False))
        
        providers_used = {}
        for r in results:
            if r.get("success"):
                provider = r.get("provider", "unknown")
                providers_used[provider] = providers_used.get(provider, 0) + 1
        
        return {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "cache_hits": cache_hits,
            "success_rate": sum(1 for r in results if r.get("success")) / len(results) if results else 0,
            "providers_used": providers_used
        }

# Update configuration helper
def update_env_for_multi_llm():
    """Helper to update .env file with multi-LLM configuration"""
    env_template = """
# Multi-LLM Provider Configuration
# Add your API keys here to enable different providers

# Anthropic Claude (Primary)
ANTHROPIC_API_KEY=your_anthropic_key_here

# OpenAI GPT (Fallback and specialized tasks)
OPENAI_API_KEY=your_openai_key_here

# Google Gemini (Fast and cheap tasks)
GEMINI_API_KEY=your_gemini_key_here

# Provider Selection Strategy
LLM_STRATEGY=cost_optimized  # Options: cost_optimized, performance, balanced
LLM_FALLBACK_ENABLED=true
LLM_CACHE_ENABLED=true

# Cost Limits (optional)
MAX_COST_PER_HOUR=10.00
MAX_COST_PER_DAY=100.00
"""
    
    env_file = Path(".env.multi_llm_template")
    env_file.write_text(env_template)
    print(f"Multi-LLM configuration template created at: {env_file}")
    print("Please add your API keys to enable multi-provider support")

if __name__ == "__main__":
    # Create configuration template
    update_env_for_multi_llm()
    
    # Demo
    async def demo():
        print("Multi-LLM Agent Integration - Demo")
        print("=" * 50)
        
        # Initialize enhanced runner
        runner = EnhancedAgentRunner(
            enable_multi_llm=True,
            cost_optimization=True
        )
        
        # Test with different agents
        test_cases = [
            ("documentation-writer", "Write a README for a Python project"),
            ("rapid-builder", "Create a FastAPI endpoint"),
            ("security-auditor", "Review this code for vulnerabilities"),
        ]
        
        for agent, requirements in test_cases:
            print(f"\n🤖 Running {agent}...")
            result = await runner.run_agent_multi_llm(agent, requirements)
            
            if result["success"]:
                print(f"✅ Success!")
                print(f"   Provider: {result.get('provider')}")
                print(f"   Model: {result.get('model')}")
                print(f"   Cost: ${result.get('cost', 0):.4f}")
                print(f"   Cached: {result.get('cached', False)}")
            else:
                print(f"❌ Failed: {result.get('error')}")
        
        # Show usage report
        print(runner.get_usage_report())
        
        # Show optimization recommendations
        recommendations = runner.export_cost_optimization_recommendations()
        if recommendations:
            print("\n💡 Cost Optimization Recommendations:")
            for rec in recommendations:
                print(f"  - {rec['agent']}: {rec['reason']}")
                print(f"    Potential savings: {rec['potential_savings']}")
    
    # Run demo
    asyncio.run(demo())