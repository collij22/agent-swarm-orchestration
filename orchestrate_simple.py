#!/usr/bin/env python
"""Simplified orchestrator without Rich console"""

import sys
import os
import asyncio
import yaml
import argparse
from pathlib import Path
from datetime import datetime

# Disable Rich entirely
os.environ['DISABLE_RICH_CONSOLE'] = '1'

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import without Rich
from lib.agent_runtime import AnthropicAgentRunner, AgentContext
from lib.orchestration_enhanced import AdaptiveWorkflowEngine
from lib.progress_streamer import ProgressStreamer

def simple_print(msg):
    """Simple print that always works"""
    try:
        print(msg)
    except:
        # Write directly to file if print fails
        with open('orchestrate_output.txt', 'a') as f:
            f.write(msg + '\n')

async def run_orchestration(args):
    """Run orchestration without Rich console"""
    
    simple_print(f"\n{'='*60}")
    simple_print(f"Starting Orchestration")
    simple_print(f"Time: {datetime.now()}")
    simple_print(f"Project Type: {args.project_type}")
    simple_print(f"Requirements: {args.requirements}")
    simple_print(f"Output Dir: {args.output_dir}")
    simple_print(f"{'='*60}\n")
    
    # Load requirements
    with open(args.requirements) as f:
        requirements = yaml.safe_load(f)
    
    # Initialize components
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        simple_print("ERROR: ANTHROPIC_API_KEY not set")
        return False
    
    # Create context
    context = AgentContext()
    context.project_requirements = requirements
    context.project_path = args.output_dir
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize runtime
    runtime = AnthropicAgentRunner(
        api_key=api_key,
        session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # Initialize workflow engine
    engine = AdaptiveWorkflowEngine()
    
    # Determine workflow
    workflow = engine.determine_workflow(args.project_type, requirements)
    
    simple_print(f"Workflow phases: {len(workflow['phases'])}")
    for i, phase in enumerate(workflow['phases'], 1):
        simple_print(f"  Phase {i}: {phase['name']} - {len(phase['agents'])} agents")
    
    # Execute phases
    for phase_num, phase in enumerate(workflow['phases'], 1):
        simple_print(f"\n{'='*40}")
        simple_print(f"Phase {phase_num}: {phase['name']}")
        simple_print(f"{'='*40}")
        
        for agent_name in phase['agents']:
            simple_print(f"\nRunning agent: {agent_name}")
            
            try:
                # Run agent
                result = await runtime.run_agent_async(
                    agent_name=agent_name,
                    context=context
                )
                
                if result and result.get('success'):
                    simple_print(f"  ✓ {agent_name} completed successfully")
                else:
                    simple_print(f"  ✗ {agent_name} failed")
                    
            except Exception as e:
                simple_print(f"  ✗ {agent_name} error: {str(e)}")
    
    simple_print(f"\n{'='*60}")
    simple_print(f"Orchestration Complete")
    simple_print(f"Output saved to: {args.output_dir}")
    simple_print(f"{'='*60}\n")
    
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Simple Orchestrator')
    parser.add_argument('--project-type', required=True, help='Project type')
    parser.add_argument('--requirements', required=True, help='Requirements YAML file')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--max-parallel', type=int, default=2, help='Max parallel agents')
    parser.add_argument('--progress', action='store_true', help='Show progress')
    parser.add_argument('--human-log', action='store_true', help='Enable human log')
    parser.add_argument('--summary-level', default='concise', help='Summary level')
    
    args = parser.parse_args()
    
    # Run orchestration
    try:
        success = asyncio.run(run_orchestration(args))
        sys.exit(0 if success else 1)
    except Exception as e:
        simple_print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()