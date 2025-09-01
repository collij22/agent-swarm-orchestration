#!/usr/bin/env python3
"""
Launch the agent swarm for Countdown game development
"""

import os
import sys
import subprocess

# Set mock mode
os.environ['MOCK_MODE'] = 'true'

# Run the orchestrator
command = [
    sys.executable,
    'orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'countdown_requirements.yaml',
    '--human-log',
    '--summary-level', 'detailed',
    '--max-parallel', '3',
    '--output-dir', 'countdown_game'
]

print("=" * 60)
print("Starting Countdown Game Development with Agent Swarm")
print("=" * 60)
print(f"Mock Mode: {os.environ.get('MOCK_MODE', 'false')}")
print(f"Requirements: countdown_requirements.yaml")
print(f"Output Directory: countdown_game/")
print("=" * 60)
print()

# Run the command
result = subprocess.run(command, capture_output=False, text=True)

if result.returncode == 0:
    print("\n" + "=" * 60)
    print("Orchestration completed successfully!")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print(f"Orchestration failed with return code: {result.returncode}")
    print("=" * 60)

sys.exit(result.returncode)