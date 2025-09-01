#!/usr/bin/env python3
"""
Run the orchestrator with API key from command line argument
"""

import os
import sys
import subprocess

def main():
    # Check if API key is provided as argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        # Try to get from environment
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        if not api_key:
            print("Please provide your API key:")
            print("  python run_with_api_key.py sk-ant-YOUR-KEY-HERE")
            print("Or set it in the environment:")
            print("  set ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE")
            return 1
    
    # Set the API key in environment for this process
    os.environ['ANTHROPIC_API_KEY'] = api_key
    
    # Verify it's set
    if api_key.startswith('sk-ant-'):
        print(f"✓ API key set (starts with {api_key[:10]}...)")
    else:
        print("⚠ Warning: API key doesn't start with 'sk-ant-'")
    
    print("\n" + "="*60)
    print("Starting Countdown Game Development with Agent Swarm")
    print("="*60)
    
    # Run the orchestrator
    cmd = [
        sys.executable,
        'orchestrate_enhanced.py',
        '--project-type', 'full_stack_api',
        '--requirements', 'countdown_requirements.yaml',
        '--human-log',
        '--summary-level', 'detailed',
        '--max-parallel', '3',
        '--output-dir', 'countdown_game',
        '--verbose'
    ]
    
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())