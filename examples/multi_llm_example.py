#!/usr/bin/env python3
"""
Example: Using Multi-LLM Provider Support in Agent Swarm
"""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from lib.llm_integration import EnhancedAgentRunner, MultiLLMAgentOrchestrator
from lib.llm_providers import LLMProvider, ModelTier

async def main():
    print("Multi-LLM Agent Swarm Example")
    print("=" * 50)
    
    # Initialize enhanced runner with multi-LLM support
    runner = EnhancedAgentRunner(
        enable_multi_llm=True,
        enable_cache=True,
        enable_fallback=True,
        cost_optimization=True
    )
    
    # Example 1: Run agent with automatic provider selection
    print("\n1. Automatic Provider Selection:")
    result = await runner.run_agent_multi_llm(
        agent_name="documentation-writer",
        requirements="Write a brief README for a Python web scraper project"
    )
    
    if result["success"]:
        print(f"   [OK] Provider: {result['provider']}")
        print(f"   Model: {result['model']}")
        print(f"   Cost: ${result['cost']:.4f}")
        print(f"   Response preview: {result['response'][:100]}...")
    
    # Example 2: Force specific provider
    print("\n2. Forced Provider (OpenAI):")
    result = await runner.run_agent_multi_llm(
        agent_name="rapid-builder",
        requirements="Create a simple FastAPI health check endpoint",
        override_provider=LLLProvider.OPENAI
    )
    
    if result["success"]:
        print(f"   [OK] Provider: {result['provider']}")
        print(f"   Model: {result['model']}")
    
    # Example 3: Orchestrate multiple agents
    print("\n3. Multi-Agent Workflow:")
    orchestrator = MultiLLMAgentOrchestrator(runner)
    
    workflow = [
        {
            "agent": "requirements-analyst",
            "requirements": "Analyze requirements for a task management API"
        },
        {
            "agent": "rapid-builder",
            "requirements": "Build the API based on analysis",
            "depends_on": ["requirements-analyst"]
        },
        {
            "agent": "quality-guardian",
            "requirements": "Review the implementation",
            "depends_on": ["rapid-builder"]
        }
    ]
    
    workflow_result = await orchestrator.execute_workflow(workflow)
    
    if workflow_result["success"]:
        print(f"   [OK] Workflow completed!")
        print(f"   Total cost: ${workflow_result['metrics']['total_cost']:.4f}")
        print(f"   Providers used: {workflow_result['metrics']['providers_used']}")
    
    # Show usage report
    print(runner.get_usage_report())
    
    # Show cost optimization recommendations
    recommendations = runner.export_cost_optimization_recommendations()
    if recommendations:
        print("\nCost Optimization Recommendations:")
        for rec in recommendations:
            print(f"  - {rec['agent']}: {rec['reason']}")

if __name__ == "__main__":
    asyncio.run(main())
