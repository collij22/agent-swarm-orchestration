#!/usr/bin/env python3
"""
Test script to verify MCP tools registration in orchestrate_enhanced.py
"""

import sys
import os
from pathlib import Path

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.agent_runtime import create_mcp_enhanced_tools

def test_mcp_tools_available():
    """Test if MCP tools can be created"""
    print("Testing MCP tool availability...")
    
    # Try to create MCP tools
    mcp_tools = create_mcp_enhanced_tools()
    
    if mcp_tools:
        print(f"✅ Successfully created {len(mcp_tools)} MCP tools:")
        for tool in mcp_tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Check for key tools
        tool_names = [tool.name for tool in mcp_tools]
        expected_tools = ["mcp_ref_search", "mcp_get_docs", "mcp_semgrep_scan", "mcp_browser_screenshot"]
        
        for expected in expected_tools:
            if expected in tool_names:
                print(f"  ✅ {expected} is available")
            else:
                print(f"  ❌ {expected} is missing")
        
        return True
    else:
        print("❌ No MCP tools were created")
        print("   This could mean:")
        print("   1. MCP servers are not running")
        print("   2. mcp_tools.py import failed")
        print("   3. Configuration issues")
        return False

def test_orchestrator_registration():
    """Test if orchestrator registers MCP tools"""
    print("\nTesting orchestrator MCP registration...")
    
    # Set mock mode to avoid API calls
    os.environ['MOCK_MODE'] = 'true'
    
    try:
        from orchestrate_enhanced import EnhancedOrchestrator
        
        # Create orchestrator
        orchestrator = EnhancedOrchestrator()
        
        # Check registered tools
        registered_tools = list(orchestrator.runtime.tools.keys())
        print(f"Total tools registered: {len(registered_tools)}")
        
        # Check for MCP tools
        mcp_tools = [t for t in registered_tools if t.startswith('mcp_')]
        if mcp_tools:
            print(f"✅ Found {len(mcp_tools)} MCP tools registered:")
            for tool in mcp_tools:
                print(f"  - {tool}")
            return True
        else:
            print("❌ No MCP tools found in orchestrator")
            print(f"Registered tools: {registered_tools}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP Tool Registration Test")
    print("=" * 60)
    
    # Test 1: Can MCP tools be created?
    test1_passed = test_mcp_tools_available()
    
    # Test 2: Does orchestrator register them?
    test2_passed = test_orchestrator_registration()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  MCP Tools Available: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  Orchestrator Registration: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("\n✅ All tests passed! MCP tools should be available to agents.")
        print("\nTo use MCP tools, agents should call:")
        print("  - mcp_ref_search: For documentation lookups (60% token savings)")
        print("  - mcp_get_docs: For specific tech documentation")
        print("  - mcp_semgrep_scan: For security scanning")
        print("  - mcp_browser_screenshot: For visual validation")
    else:
        print("\n❌ Some tests failed. MCP tools may not be available.")
        print("\nTroubleshooting:")
        print("1. Check if MCP servers are running")
        print("2. Verify .claude/mcp/config.json exists")
        print("3. Check lib/mcp_tools.py imports correctly")

if __name__ == "__main__":
    main()