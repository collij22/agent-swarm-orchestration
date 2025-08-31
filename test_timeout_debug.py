#!/usr/bin/env python3
"""
Test orchestrate_enhanced.py directly with invalid API key
"""

import os
import sys

# Set invalid API key
os.environ['ANTHROPIC_API_KEY'] = 'invalid-key-123'
os.environ.pop('MOCK_MODE', None)

# Import orchestrate_enhanced
print("[TEST] Starting import...")
sys.path.insert(0, '.')

try:
    # Parse arguments
    class Args:
        project_type = 'api_service'
        requirements = 'tests/phase5_validation/requirements/ecommerce_platform.yaml'
        chain = None
        interactive = False
        resume_checkpoint = None
        dashboard = False
        progress = False
        max_parallel = 3
        api_key = None
        verbose = True
        output_dir = None
        human_log = True
        summary_level = 'concise'
    
    args = Args()
    
    # Get API key
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    
    print(f"[TEST] API key provided: {'yes' if api_key else 'no'}")
    print(f"[TEST] Mock mode: {os.environ.get('MOCK_MODE', 'false')}")
    print("[TEST] Creating EnhancedOrchestrator...")
    
    # Import after setting environment
    from orchestrate_enhanced import EnhancedOrchestrator
    
    # Try to create orchestrator
    orchestrator = EnhancedOrchestrator(
        api_key, 
        enable_dashboard=False,
        enable_human_log=True,
        summary_level='concise'
    )
    
    print("[TEST] Orchestrator created successfully!")
    print(f"[TEST] Runtime client available: {orchestrator.runtime.client is not None}")
    
except Exception as e:
    print(f"[TEST] Error: {str(e)}")
    import traceback
    traceback.print_exc()
    
print("[TEST] Test complete")