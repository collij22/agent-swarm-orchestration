#!/usr/bin/env python3
"""
Setup Script for Multi-LLM Provider Support
Configures the agent swarm to use multiple LLM providers

This script:
1. Checks for required dependencies
2. Creates configuration files
3. Updates agent configurations
4. Tests provider connections
5. Generates cost optimization report
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess

def check_dependencies():
    """Check and install required dependencies"""
    print("Checking dependencies...")
    
    required_packages = {
        "anthropic": "Anthropic Claude SDK",
        "openai": "OpenAI GPT SDK",
        "google-generativeai": "Google Gemini SDK",
        "sentence-transformers": "Semantic caching support",
        "tiktoken": "Token counting for OpenAI"
    }
    
    missing = []
    installed = []
    
    for package, description in required_packages.items():
        try:
            __import__(package.replace("-", "_"))
            installed.append(f"[OK] {description}")
        except ImportError:
            missing.append(package)
            print(f"[!] Missing: {description}")
    
    if missing:
        print("\nInstalling missing packages...")
        install_cmd = [sys.executable, "-m", "pip", "install"] + missing
        
        try:
            subprocess.run(install_cmd, check=True)
            print("[OK] All dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("[ERROR] Failed to install some dependencies")
            print("Please run manually:")
            print(f"  pip install {' '.join(missing)}")
            return False
    else:
        print("[OK] All dependencies already installed")
    
    return True

def create_env_file():
    """Create or update .env file with multi-LLM configuration"""
    env_path = Path(".env")
    
    # Check if .env exists
    existing_config = {}
    if env_path.exists():
        print("\nFound existing .env file")
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing_config[key] = value
    
    # Multi-LLM configuration
    multi_llm_config = {
        "# Multi-LLM Provider Configuration": "",
        "ANTHROPIC_API_KEY": existing_config.get("ANTHROPIC_API_KEY", ""),
        "OPENAI_API_KEY": existing_config.get("OPENAI_API_KEY", ""),
        "GEMINI_API_KEY": existing_config.get("GEMINI_API_KEY", ""),
        "": "",
        "# Provider Settings": "",
        "LLM_MULTI_PROVIDER_ENABLED": "true",
        "LLM_FALLBACK_ENABLED": "true",
        "LLM_CACHE_ENABLED": "true",
        "LLM_COST_OPTIMIZATION": "true",
        "": "",
        "# Cost Limits": "",
        "MAX_COST_PER_HOUR": "10.00",
        "MAX_COST_PER_DAY": "100.00",
        "": "",
        "# Model Selection Strategy": "",
        "# Options: cost_optimized, performance, balanced": "",
        "LLM_STRATEGY": "balanced",
    }
    
    # Backup existing .env if it exists
    if env_path.exists():
        backup_path = Path(".env.backup")
        # If backup already exists, add timestamp
        if backup_path.exists():
            import time
            timestamp = int(time.time())
            backup_path = Path(f".env.backup.{timestamp}")
        env_path.rename(backup_path)
        print(f"Backed up existing .env to {backup_path}")
    
    # Write new configuration
    with open(env_path, 'w') as f:
        # Write existing non-LLM config first
        for key, value in existing_config.items():
            if not any(k in key for k in ["ANTHROPIC", "OPENAI", "GEMINI", "LLM_"]):
                f.write(f"{key}={value}\n")
        
        f.write("\n")
        
        # Write multi-LLM config
        for key, value in multi_llm_config.items():
            if key == "":
                f.write("\n")
            elif key.startswith("#"):
                f.write(f"{key}\n")
            else:
                f.write(f"{key}={value}\n")
    
    print("[OK] Created multi-LLM configuration in .env")
    
    # Check which API keys are configured
    configured_providers = []
    if existing_config.get("ANTHROPIC_API_KEY") and existing_config["ANTHROPIC_API_KEY"] != "":
        configured_providers.append("Anthropic")
    if existing_config.get("OPENAI_API_KEY") and existing_config["OPENAI_API_KEY"] != "":
        configured_providers.append("OpenAI")
    if existing_config.get("GEMINI_API_KEY") and existing_config["GEMINI_API_KEY"] != "":
        configured_providers.append("Gemini")
    
    if configured_providers:
        print(f"[OK] Found API keys for: {', '.join(configured_providers)}")
    else:
        print("\n[WARNING] No API keys found. Please add them to .env:")
        print("  - ANTHROPIC_API_KEY")
        print("  - OPENAI_API_KEY")
        print("  - GEMINI_API_KEY")
    
    return len(configured_providers) > 0

async def test_providers():
    """Test connectivity to configured providers"""
    print("\nTesting provider connections...")
    
    from lib.llm_providers import MultiLLMOrchestrator, LLMProvider
    
    orchestrator = MultiLLMOrchestrator()
    
    test_prompt = "Say 'Hello' in one word"
    results = {}
    
    for provider in [LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GEMINI]:
        try:
            print(f"  Testing {provider.value}...", end=" ")
            response = await orchestrator.generate(
                prompt=test_prompt,
                provider=provider,
                max_tokens=10
            )
            results[provider.value] = "[OK] Connected"
            print("[OK]")
        except Exception as e:
            results[provider.value] = f"[FAILED] {str(e)[:50]}"
            print("[FAILED]")
    
    print("\nProvider Status:")
    for provider, status in results.items():
        print(f"  {provider}: {status}")
    
    return results

def create_cost_report():
    """Generate cost comparison report"""
    print("\nCost Analysis Report")
    print("=" * 50)
    
    cost_data = {
        "Anthropic Claude": {
            "Claude 3.5 Sonnet": {"input": 3.00, "output": 15.00},
            "Claude 3.5 Haiku": {"input": 0.80, "output": 4.00},
            "Claude 3 Opus": {"input": 15.00, "output": 75.00},
        },
        "OpenAI": {
            "GPT-4 Turbo": {"input": 10.00, "output": 30.00},
            "GPT-4": {"input": 30.00, "output": 60.00},
            "GPT-3.5 Turbo": {"input": 0.50, "output": 1.50},
        },
        "Google Gemini": {
            "Gemini Pro": {"input": 0.25, "output": 0.50},
        }
    }
    
    print("\nCost per 1M tokens (USD):")
    for provider, models in cost_data.items():
        print(f"\n{provider}:")
        for model, costs in models.items():
            print(f"  {model}:")
            print(f"    Input:  ${costs['input']:.2f}")
            print(f"    Output: ${costs['output']:.2f}")
    
    print("\nCost Optimization Tips:")
    print("  1. Use Gemini Pro for simple tasks (cheapest)")
    print("  2. Use GPT-3.5 Turbo for fast responses")
    print("  3. Reserve Claude Opus for complex analysis")
    print("  4. Enable caching to reduce repeated calls")
    print("  5. Use semantic caching for similar queries")

def update_orchestrator_config():
    """Update orchestrator configuration for multi-LLM support"""
    config_path = Path("config") / "orchestrator_config.json"
    
    if not config_path.parent.exists():
        config_path.parent.mkdir(parents=True)
    
    config = {
        "multi_llm": {
            "enabled": True,
            "providers": ["anthropic", "openai", "gemini"],
            "fallback_chain": ["anthropic", "openai", "gemini"],
            "cost_optimization": True,
            "cache_settings": {
                "enabled": True,
                "ttl": 3600,
                "max_entries": 1000,
                "similarity_threshold": 0.85
            }
        },
        "agent_model_assignments": {
            "rapid-builder": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
            "frontend-specialist": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
            "documentation-writer": {"provider": "gemini", "model": "gemini-pro"},
            "quality-guardian": {"provider": "openai", "model": "gpt-4-turbo-preview"},
            "api-integrator": {"provider": "openai", "model": "gpt-4"},
            "performance-optimizer": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
            "security-auditor": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
            "devops-engineer": {"provider": "openai", "model": "gpt-4"},
            "database-expert": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
            "debug-specialist": {"provider": "anthropic", "model": "claude-3-opus-20240229"},
            "ai-specialist": {"provider": "openai", "model": "gpt-4-turbo-preview"},
            "project-orchestrator": {"provider": "anthropic", "model": "claude-3-opus-20240229"},
            "project-architect": {"provider": "anthropic", "model": "claude-3-opus-20240229"},
            "requirements-analyst": {"provider": "openai", "model": "gpt-4"},
            "code-migrator": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
            "meta-agent": {"provider": "anthropic", "model": "claude-3-opus-20240229"}
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n[OK] Created orchestrator configuration at {config_path}")

def create_example_script():
    """Create example script for using multi-LLM support"""
    example_path = Path("examples") / "multi_llm_example.py"
    
    if not example_path.parent.exists():
        example_path.parent.mkdir(parents=True)
    
    example_code = '''#!/usr/bin/env python3
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
    print("\\n1. Automatic Provider Selection:")
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
    print("\\n2. Forced Provider (OpenAI):")
    result = await runner.run_agent_multi_llm(
        agent_name="rapid-builder",
        requirements="Create a simple FastAPI health check endpoint",
        override_provider=LLLProvider.OPENAI
    )
    
    if result["success"]:
        print(f"   [OK] Provider: {result['provider']}")
        print(f"   Model: {result['model']}")
    
    # Example 3: Orchestrate multiple agents
    print("\\n3. Multi-Agent Workflow:")
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
        print("\\nCost Optimization Recommendations:")
        for rec in recommendations:
            print(f"  - {rec['agent']}: {rec['reason']}")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open(example_path, 'w', encoding='utf-8') as f:
        f.write(example_code)
    
    print(f"[OK] Created example script at {example_path}")

async def main():
    """Main setup function"""
    print("""
========================================================
     Multi-LLM Provider Setup for Agent Swarm        
========================================================
    """)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n[ERROR] Setup failed: Missing dependencies")
        return False
    
    # Step 2: Create/update .env file
    has_keys = create_env_file()
    
    # Step 3: Update orchestrator configuration
    update_orchestrator_config()
    
    # Step 4: Create example script
    create_example_script()
    
    # Step 5: Test providers if keys are available
    if has_keys:
        test_results = await test_providers()
    else:
        print("\n[WARNING] Skipping provider tests (no API keys configured)")
    
    # Step 6: Generate cost report
    create_cost_report()
    
    print("\n" + "=" * 50)
    print("[OK] Multi-LLM Provider Setup Complete!")
    print("\nNext steps:")
    print("1. Add your API keys to .env file")
    print("2. Run the example: python examples/multi_llm_example.py")
    print("3. Update orchestrator to use EnhancedAgentRunner")
    print("\nIntegration with existing system:")
    print("  - Import: from lib.llm_integration import EnhancedAgentRunner")
    print("  - Replace AnthropicAgentRunner with EnhancedAgentRunner")
    print("  - Multi-LLM support will be automatically enabled")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)