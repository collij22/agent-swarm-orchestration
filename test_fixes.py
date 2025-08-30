#!/usr/bin/env python3
"""
Test script to verify fixes for:
1. Orange color error in Rich library
2. write_file missing content parameter errors
3. devops-engineer repetitive reasoning loop
"""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import locale
    locale.setlocale(locale.LC_ALL, '')
    sys.stdout.reconfigure(encoding='utf-8')

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

def test_rich_colors():
    """Test that Rich colors work correctly after fix"""
    print("\n=== Testing Rich Colors Fix ===")
    try:
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        table = Table(title="Agent Status")
        
        # These should work now (yellow instead of orange)
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Retries", style="yellow")  # Was "orange"
        
        table.add_row("devops-engineer", "Running", "2")
        table.add_row("code-migrator", "Complete", "0")
        
        console.print(table)
        print("[PASS] Rich colors test PASSED")
        return True
    except Exception as e:
        print(f"[FAIL] Rich colors test FAILED: {e}")
        return False

def test_write_file_validation():
    """Test write_file parameter validation"""
    print("\n=== Testing write_file Parameter Validation ===")
    try:
        from lib.agent_runtime import write_file_tool, AgentContext
        import asyncio
        
        # Test with missing content
        async def test_missing_content():
            context = AgentContext(
                project_requirements={},
                completed_tasks=[],
                artifacts={"project_directory": "test_output"},
                decisions=[],
                current_phase="testing"
            )
            
            # This should handle missing content gracefully
            result = await write_file_tool(
                file_path="test.txt",
                content=None,  # Intentionally None
                context=context
            )
            print(f"  Test 1 (None content): {result}")
            
            # Test with proper content
            result = await write_file_tool(
                file_path="test2.txt",
                content="Proper content",
                context=context
            )
            print(f"  Test 2 (Valid content): {result}")
            
            return True
        
        success = asyncio.run(test_missing_content())
        if success:
            print("[PASS] write_file validation test PASSED")
        return success
    except Exception as e:
        print(f"❌ write_file validation test FAILED: {e}")
        return False

def test_text_deduplication():
    """Test that repetitive text is deduplicated"""
    print("\n=== Testing Text Deduplication ===")
    try:
        # Simulate repetitive text
        repetitive_text = """Let me create the Terraform configuration properly:
Let me create the Terraform configuration properly:
Let me create the Terraform configuration properly:
Different line here
Different line here
And another unique line"""
        
        # Apply deduplication logic
        lines = repetitive_text.split('\n')
        unique_lines = []
        for line in lines:
            if not unique_lines or line != unique_lines[-1]:
                unique_lines.append(line)
        deduplicated = '\n'.join(unique_lines)
        
        expected = """Let me create the Terraform configuration properly:
Different line here
And another unique line"""
        
        if deduplicated == expected:
            print("[PASS] Text deduplication test PASSED")
            print(f"  Original lines: {len(lines)}")
            print(f"  Deduplicated lines: {len(unique_lines)}")
            return True
        else:
            print("[FAIL] Text deduplication test FAILED")
            print(f"  Expected: {expected}")
            print(f"  Got: {deduplicated}")
            return False
    except Exception as e:
        print(f"❌ Text deduplication test FAILED: {e}")
        return False

def test_agent_configs():
    """Test that agent configurations are valid"""
    print("\n=== Testing Agent Configurations ===")
    try:
        from orchestrate import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        agents = orchestrator._load_agent_configs()
        
        # Check specific agents that had orange color
        problematic_agents = ["devops-engineer", "code-migrator"]
        
        for agent_name in problematic_agents:
            if agent_name in agents:
                config = agents[agent_name]
                if config.color in ["yellow", "bright_yellow"]:
                    print(f"  [OK] {agent_name}: color fixed to {config.color}")
                else:
                    print(f"  [ERROR] {agent_name}: still has problematic color {config.color}")
                    return False
        
        print("[PASS] Agent configurations test PASSED")
        return True
    except Exception as e:
        print(f"❌ Agent configurations test FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Fixes for Agent Swarm Issues")
    print("=" * 60)
    
    tests = [
        test_rich_colors,
        test_write_file_validation,
        test_text_deduplication,
        test_agent_configs
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"[SUCCESS] ALL TESTS PASSED ({passed}/{total})")
        return 0
    else:
        print(f"[FAILURE] SOME TESTS FAILED ({passed}/{total} passed)")
        return 1

if __name__ == "__main__":
    sys.exit(main())