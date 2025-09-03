#!/usr/bin/env python3
"""
Quick check of run_agent signature
"""

import sys
from pathlib import Path
import inspect

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from lib.agent_runtime import AnthropicAgentRunner

# Check method signature without creating instance
print("Checking AnthropicAgentRunner.run_agent signature:")
sig = inspect.signature(AnthropicAgentRunner.run_agent)
print(f"Parameters: {list(sig.parameters.keys())}")
print(f"Return type: {sig.return_annotation}")

# Check for correct parameter
if 'agent_prompt' in sig.parameters:
    print("✓ agent_prompt parameter exists")
else:
    print("✗ agent_prompt parameter missing")
    
if 'prompt' in sig.parameters:
    print("✗ 'prompt' parameter found (should be agent_prompt)")
else:
    print("✓ 'prompt' parameter not found (correct)")

print("\nExpected call format:")
print("  success, response, updated_context = runner.run_agent(")
print("      agent_name='agent-name',")
print("      agent_prompt='prompt text',")
print("      context=context_object")
print("  )")