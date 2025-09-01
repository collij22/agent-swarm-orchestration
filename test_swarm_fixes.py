#!/usr/bin/env python3
"""
Test script to verify all swarm error fixes
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_logger_warning():
    """Test that ReasoningLogger has log_warning method"""
    print("\n1. Testing ReasoningLogger.log_warning...")
    try:
        from lib.agent_logger import ReasoningLogger
        logger = ReasoningLogger()
        
        # Test log_warning method exists
        if not hasattr(logger, 'log_warning'):
            print("   ❌ ReasoningLogger missing log_warning method")
            return False
        
        # Test it can be called
        logger.log_warning("test_agent", "Test warning message", "Test reasoning")
        print("   ✅ ReasoningLogger.log_warning works correctly")
        return True
    except Exception as e:
        print(f"   ❌ Error testing logger: {e}")
        return False

def test_agent_context():
    """Test that AgentContext can be created with current_phase"""
    print("\n2. Testing AgentContext with current_phase...")
    try:
        from lib.agent_runtime import AgentContext
        
        # Test creating context with current_phase
        context = AgentContext(
            project_requirements={"test": "requirements"},
            completed_tasks=[],
            artifacts={},
            decisions=[],
            current_phase="testing"
        )
        
        if not hasattr(context, 'current_phase'):
            print("   ❌ AgentContext missing current_phase attribute")
            return False
        
        if context.current_phase != "testing":
            print(f"   ❌ current_phase not set correctly: {context.current_phase}")
            return False
        
        print("   ✅ AgentContext with current_phase works correctly")
        return True
    except Exception as e:
        print(f"   ❌ Error testing AgentContext: {e}")
        return False

async def test_write_file_tool():
    """Test that write_file tool handles missing content gracefully"""
    print("\n3. Testing write_file tool with missing content...")
    try:
        from lib.agent_runtime import write_file_tool, AgentContext
        from lib.agent_logger import ReasoningLogger
        
        # Create test context
        test_dir = Path("test_output")
        test_dir.mkdir(exist_ok=True)
        
        context = AgentContext(
            project_requirements={},
            completed_tasks=[],
            artifacts={"project_directory": str(test_dir)},
            decisions=[],
            current_phase="testing"
        )
        
        # Test with empty content (should generate placeholder)
        result = await write_file_tool(
            file_path="test.py",
            content="",  # Empty content
            reasoning="Testing empty content handling",
            context=context,
            agent_name="test_agent"
        )
        
        # Check if file was created with placeholder content
        test_file = test_dir / "test.py"
        if not test_file.exists():
            print("   ❌ File not created")
            return False
        
        content = test_file.read_text()
        if "NotImplementedError" not in content:
            print("   ❌ Placeholder content not generated")
            return False
        
        # Clean up
        test_file.unlink()
        # Only remove directory if it's empty
        try:
            test_dir.rmdir()
        except:
            pass  # Directory might not be empty, that's ok
        
        print("   ✅ write_file tool handles missing content correctly")
        return True
    except Exception as e:
        print(f"   ❌ Error testing write_file: {e}")
        # Clean up on error
        try:
            test_dir = Path("test_output")
            if test_dir.exists():
                for file in test_dir.glob("*"):
                    file.unlink()
                test_dir.rmdir()
        except:
            pass
        return False

def test_orchestrator_imports():
    """Test that orchestrate_enhanced.py can be imported without errors"""
    print("\n4. Testing orchestrate_enhanced.py imports...")
    try:
        # This will fail if there are syntax errors or missing imports
        import orchestrate_enhanced
        print("   ✅ orchestrate_enhanced.py imports successfully")
        return True
    except Exception as e:
        print(f"   ❌ Error importing orchestrate_enhanced: {e}")
        return False

async def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("Testing Swarm Error Fixes")
    print("=" * 60)
    
    results = []
    
    # Test 1: Logger warning method
    results.append(test_logger_warning())
    
    # Test 2: AgentContext with current_phase
    results.append(test_agent_context())
    
    # Test 3: write_file tool
    results.append(await test_write_file_tool())
    
    # Test 4: Orchestrator imports
    results.append(test_orchestrator_imports())
    
    # Summary
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\nThe swarm errors have been successfully fixed!")
        print("You can now run:")
        print("  python orchestrate_enhanced.py --project-type full_stack_api \\")
        print("    --requirements projects/quickshop-mvp-test/requirements.yaml \\")
        print("    --output-dir projects/quickshop-mvp-test3")
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        print("\nPlease review the errors above and fix any remaining issues.")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)