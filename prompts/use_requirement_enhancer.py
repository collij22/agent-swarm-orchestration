#!/usr/bin/env python3
"""
Requirement Enhancer Usage Script

This script demonstrates how to use the requirement enhancement prompt
to transform basic project requirements into detailed specifications
optimized for the 15-agent swarm system.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


def load_prompt() -> str:
    """Load the requirement enhancer prompt"""
    prompt_path = Path(__file__).parent / "requirement_enhancer_prompt.md"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def enhance_requirement(original_requirement: str, output_file: str = None) -> Dict[str, Any]:
    """
    Enhance a basic requirement using the prompt template.
    
    Args:
        original_requirement: The basic project requirement text
        output_file: Optional path to save the enhanced requirement
        
    Returns:
        Enhanced requirement as a dictionary
    """
    prompt = load_prompt()
    
    # Combine prompt with the original requirement
    full_prompt = f"""
{prompt}

## ORIGINAL REQUIREMENT TO ENHANCE:

{original_requirement}
"""
    
    print("=" * 80)
    print("REQUIREMENT ENHANCEMENT PROMPT")
    print("=" * 80)
    print("\nUse this prompt with any LLM to generate an enhanced requirement.")
    print("\nOriginal Requirement:")
    print("-" * 40)
    print(original_requirement)
    print("-" * 40)
    
    # Here you would typically call an LLM API
    # For demonstration, we'll just show the structure
    example_output = {
        "project": {
            "name": "Enhanced Project Name",
            "type": "web_app",
            "description": "A comprehensive description based on the original requirement",
            "timeline": "2-3 weeks",
            "priority": "MVP",
            "complexity": "moderate"
        },
        "core_requirements": [
            {
                "id": "REQ-001",
                "description": "Core functionality from original requirement",
                "priority": 1,
                "acceptance_criteria": [
                    "Specific measurable criterion"
                ]
            }
        ],
        "technical_requirements": [
            {
                "id": "TECH-001",
                "description": "Technical infrastructure requirement",
                "rationale": "Needed for scalability and performance"
            }
        ],
        "features": [
            {
                "name": "Feature 1",
                "description": "Detailed feature description",
                "components": ["Component A", "Component B"]
            }
        ],
        "tech_stack": {
            "frontend": {"framework": "React + TypeScript"},
            "backend": {"framework": "FastAPI"},
            "database": {"primary": "PostgreSQL"}
        },
        "integrations": [],
        "constraints": {
            "budget": "Not specified",
            "timeline": "Flexible",
            "technical": []
        },
        "success_metrics": {
            "performance": ["<200ms API response time"],
            "business": ["User satisfaction"],
            "quality": ["90% test coverage"]
        },
        "deployment": {
            "environment": "production",
            "platform": "AWS or Vercel",
            "scaling": "Start small, scale as needed"
        }
    }
    
    if output_file:
        # Save as YAML
        output_path = Path(output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(example_output, f, default_flow_style=False, sort_keys=False)
        print(f"\nEnhanced requirement structure saved to: {output_path}")
    
    return example_output


def main():
    """Main demonstration function"""
    
    # Example 1: Simple requirement
    simple_req = """
    I need a todo list application where users can create, edit, and delete tasks.
    Tasks should have due dates and priority levels. I want it to work on mobile too.
    """
    
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Simple Todo Application")
    print("=" * 80)
    enhance_requirement(simple_req)
    
    # Example 2: Complex requirement
    complex_req = """
    Build an e-commerce platform with AI-powered product recommendations.
    It should support multiple vendors, real-time inventory tracking, and 
    integrate with Stripe for payments. We need analytics dashboards for vendors
    and admins. The platform should handle 10,000 concurrent users and include
    a mobile app. Use Next.js for the frontend and ensure GDPR compliance.
    """
    
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Complex E-commerce Platform")
    print("=" * 80)
    enhance_requirement(complex_req)
    
    # Example 3: AI-focused requirement
    ai_req = """
    Create an AI-powered content management system that automatically
    categorizes and tags articles, generates summaries, and suggests
    related content. It should integrate with OpenAI's GPT-4 and include
    a feedback mechanism to improve recommendations over time.
    """
    
    print("\n" + "=" * 80)
    print("EXAMPLE 3: AI Content Management System")
    print("=" * 80)
    enhance_requirement(ai_req, "enhanced_ai_cms_requirements.yaml")
    
    print("\n" + "=" * 80)
    print("HOW TO USE WITH THE AGENT SWARM")
    print("=" * 80)
    print("""
    1. Take your basic requirement
    2. Use the prompt with any LLM to generate enhanced requirements
    3. Save the output as 'requirements.yaml'
    4. Run the orchestrator:
       
       python orchestrate_enhanced.py --requirements requirements.yaml
       
    5. The system will:
       - Analyze requirements and select appropriate agents
       - Activate relevant MCP servers based on keywords
       - Execute agents in optimal parallel/sequential patterns
       - Track progress and handle failures automatically
       - Produce a complete, production-ready application
    """)
    
    print("\nKEY OPTIMIZATION TIPS:")
    print("-" * 40)
    print("• Mention 'payment' to activate Stripe MCP")
    print("• Mention 'real-time' to prioritize WebSocket implementation")
    print("• Mention 'AI/ML' to activate ai-specialist agent early")
    print("• Mention 'performance' to engage performance-optimizer")
    print("• Mention 'mobile' to ensure responsive design focus")
    print("• Specify tech stack only if you have strong preferences")
    print("• Include success metrics for better quality validation")
    

if __name__ == "__main__":
    main()