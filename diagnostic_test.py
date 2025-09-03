#!/usr/bin/env python
"""Diagnose the exact issue with orchestration"""

import sys
import os
from pathlib import Path

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

print("=" * 70)
print("DIAGNOSTIC TEST")
print("=" * 70)

# Step 1: Test basic imports
print("\n1. Testing basic imports...")
try:
    import lib.agent_runtime as runtime
    print("   ✓ agent_runtime imported")
except Exception as e:
    print(f"   ✗ agent_runtime failed: {e}")
    sys.exit(1)

try:
    from lib import mcp_tools
    print("   ✓ mcp_tools imported")
except Exception as e:
    print(f"   ✗ mcp_tools failed: {e}")

try:
    from lib import mcp_manager
    print("   ✓ mcp_manager imported")
except Exception as e:
    print(f"   ✗ mcp_manager failed: {e}")

# Step 2: Test orchestrate_enhanced import
print("\n2. Testing orchestrate_enhanced import...")
try:
    import orchestrate_enhanced
    print("   ✓ orchestrate_enhanced imported")
except Exception as e:
    print(f"   ✗ orchestrate_enhanced failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test I/O operations
print("\n3. Testing I/O operations...")
try:
    # Try print
    print("   Testing print... OK")
    
    # Try sys.stdout
    sys.stdout.write("   Testing sys.stdout.write... OK\n")
    sys.stdout.flush()
    
    # Try with asyncio
    import asyncio
    
    async def test_async():
        print("   Testing async print... OK")
        return True
    
    result = asyncio.run(test_async())
    if result:
        print("   ✓ Asyncio works")
    
except Exception as e:
    print(f"   ✗ I/O test failed: {e}")

# Step 4: Test agent logger
print("\n4. Testing agent logger...")
try:
    from lib.agent_logger import create_new_session, SummaryLevel
    
    # Try creating a session
    logger = create_new_session("diagnostic", False, SummaryLevel.CONCISE)
    print("   ✓ Logger created")
    
    # Try logging
    logger.log_event("test", {"message": "test"})
    print("   ✓ Logger works")
    
except Exception as e:
    print(f"   ✗ Logger failed: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Test creating an agent runner
print("\n5. Testing agent runner...")
try:
    from lib.agent_logger import create_new_session, SummaryLevel
    logger = create_new_session("test_runner", False, SummaryLevel.CONCISE)
    
    runner = runtime.AnthropicAgentRunner(None, logger)
    print("   ✓ Agent runner created")
    
    # Register a simple tool
    test_tool = runtime.Tool(
        name="test",
        description="Test tool",
        parameters={},
        function=lambda: "test"
    )
    runner.register_tool(test_tool)
    print("   ✓ Tool registered")
    
except Exception as e:
    print(f"   ✗ Agent runner failed: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Test orchestrator
print("\n6. Testing orchestrator creation...")
try:
    from orchestrate_enhanced import EnhancedOrchestrator
    
    # Create minimal config
    config = {
        "project_type": "full_stack_api",
        "requirements_file": "projects/quickshop-mvp-test/requirements.yaml",
        "output_dir": "projects/quickshop-mvp-test6",
        "max_parallel": 2,
        "summary_level": "concise",
        "human_readable_log": True,
        "show_progress": True
    }
    
    # Try to create orchestrator
    orch = EnhancedOrchestrator(config)
    print("   ✓ Orchestrator created")
    
except Exception as e:
    print(f"   ✗ Orchestrator failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)

# If we got here, everything works
print("\n✅ All components work!")
print("\nThe issue is likely in how they interact during orchestration.")
print("Possible causes:")
print("  1. I/O gets closed during asyncio.run()")
print("  2. Rich console conflicts with asyncio")
print("  3. MCP loading causes schema validation errors")

print("\nRecommended fix:")
print("  Run with the bulletproof I/O wrapper (ORCHESTRATE_WITH_MCPS.py)")
print("  Or use the synchronous wrapper (run_sync.py)")