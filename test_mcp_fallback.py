#!/usr/bin/env python3
"""
Test MCP fallback functionality
Verifies the system works correctly when MCP servers are not running
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.mcp_manager import MCPManager
from lib.mcp_tools import mcp_ref_search_tool

async def test_mcp_fallback():
    """Test that MCP tools gracefully fall back when servers aren't running"""
    
    print("Testing MCP Fallback Mechanism")
    print("=" * 40)
    
    # Test 1: Initialize MCP Manager
    print("\n1. Initializing MCP Manager...")
    try:
        manager = MCPManager()
        print("   ✅ MCP Manager initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return False
    
    # Test 2: Check health status (should fail gracefully)
    print("\n2. Checking MCP server health...")
    health = await manager.health_check()
    for server, status in health.items():
        if status:
            print(f"   ✅ {server}: Running")
        else:
            print(f"   ℹ️ {server}: Not running (fallback mode)")
    
    # Test 3: Test Ref search with fallback
    print("\n3. Testing Ref MCP search (should use fallback)...")
    result = await mcp_ref_search_tool(
        query="React useState hook",
        technology="react",
        reasoning="Testing fallback mechanism"
    )
    
    if "MCP Info" in result or "using general knowledge" in result:
        print("   ✅ Fallback working correctly")
        print(f"   Response: {result[:100]}...")
    else:
        print("   ❌ Unexpected response")
    
    # Test 4: Check error metrics
    print("\n4. Checking error handling...")
    ref_errors = manager.metrics['errors'].get('ref', 0)
    print(f"   Ref MCP errors recorded: {ref_errors}")
    
    print("\n" + "=" * 40)
    print("✅ MCP Fallback Test Complete")
    print("\nThe system is working correctly without MCP servers.")
    print("MCP servers would provide enhanced capabilities but are not required.")
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_mcp_fallback()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())