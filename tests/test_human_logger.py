#!/usr/bin/env python3
"""
Test suite for human-readable logger
"""

import sys
import os
from pathlib import Path
import tempfile
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.human_logger import HumanReadableLogger, SummaryLevel, AgentSummary
from lib.agent_logger import ReasoningLogger, create_new_session

def test_human_logger_creation():
    """Test creating a human logger instance"""
    print("\n=== Testing Human Logger Creation ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        session_id = str(uuid.uuid4())
        logger = HumanReadableLogger(session_id, temp_dir, SummaryLevel.CONCISE)
        
        # Check that the file was created
        assert logger.summary_file.exists()
        print(f"[PASS] Created summary file: {logger.summary_file}")
        
        # Check header content
        with open(logger.summary_file, 'r') as f:
            content = f.read()
            assert "Agent Swarm Execution Summary" in content
            assert session_id in content
            print("[PASS] Header written correctly")
        
        return True

def test_agent_lifecycle():
    """Test logging agent start and complete"""
    print("\n=== Testing Agent Lifecycle ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        session_id = str(uuid.uuid4())
        logger = HumanReadableLogger(session_id, temp_dir, SummaryLevel.CONCISE)
        
        # Log agent start
        logger.log_agent_start("test-agent", ["REQ-001", "REQ-002"])
        assert "test-agent" in logger.agents
        print("[PASS] Agent start logged")
        
        # Log some operations
        logger.log_file_operation("test-agent", "create", "main.py")
        logger.log_key_output("test-agent", "Created FastAPI application")
        logger.log_decision("test-agent", "Using PostgreSQL for database", critical=True)
        
        # Log agent complete
        logger.log_agent_complete("test-agent", True, "Successfully completed")
        
        # Check the markdown output
        with open(logger.summary_file, 'r') as f:
            content = f.read()
            assert "test-agent" in content
            assert "main.py" in content
            assert "[OK]" in content
            print("[PASS] Agent lifecycle logged correctly")
        
        return True

def test_file_operations():
    """Test file operation tracking"""
    print("\n=== Testing File Operations ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = HumanReadableLogger(str(uuid.uuid4()), temp_dir, SummaryLevel.DETAILED)
        
        logger.log_agent_start("builder", [])
        
        # Log multiple file creates
        files = ["app.py", "config.json", "models.py", "routes.py", "utils.py"]
        for file in files:
            logger.log_file_operation("builder", "create", file)
        
        # Log file modifications
        logger.log_file_operation("builder", "modify", "config.json")
        
        logger.log_agent_complete("builder", True)
        
        # Check tracking
        assert len(logger.total_files_created) == 5
        assert len(logger.total_files_modified) == 1
        print(f"[PASS] Tracked {len(logger.total_files_created)} files created")
        print(f"[PASS] Tracked {len(logger.total_files_modified)} files modified")
        
        return True

def test_error_tracking():
    """Test error logging and resolution"""
    print("\n=== Testing Error Tracking ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = HumanReadableLogger(str(uuid.uuid4()), temp_dir, SummaryLevel.VERBOSE)
        
        logger.log_agent_start("api-agent", [])
        
        # Log errors
        logger.log_error_resolution("api-agent", "Connection timeout", "Retry with backoff")
        logger.log_error_resolution("api-agent", "Rate limit exceeded", "Implement caching")
        
        logger.log_agent_complete("api-agent", False)
        
        # Check error tracking
        assert len(logger.total_errors) == 2
        assert len(logger.agents["api-agent"].errors_resolved) == 2
        print(f"[PASS] Tracked {len(logger.total_errors)} errors")
        
        return True

def test_summary_levels():
    """Test different summary levels"""
    print("\n=== Testing Summary Levels ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test each level
        for level in [SummaryLevel.CONCISE, SummaryLevel.DETAILED, SummaryLevel.VERBOSE]:
            logger = HumanReadableLogger(str(uuid.uuid4()), temp_dir, level)
            
            logger.log_agent_start("test", ["REQ-001"])
            logger.log_decision("test", "Important decision", critical=True)
            logger.log_agent_complete("test", True)
            
            logger.finalize_summary(True, {"total_duration": "10.5s"})
            
            with open(logger.summary_file, 'r') as f:
                content = f.read()
                
                # Verbose should have more content
                if level == SummaryLevel.VERBOSE:
                    assert len(content) > 500
                elif level == SummaryLevel.CONCISE:
                    assert len(content) < 1500
                    
            print(f"[PASS] {level.value} level produces appropriate output")
        
        return True

def test_integration_with_reasoning_logger():
    """Test integration with main ReasoningLogger"""
    print("\n=== Testing Integration with ReasoningLogger ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create logger with human logging enabled
        logger = create_new_session(
            session_id=str(uuid.uuid4()),
            enable_human_log=True,
            summary_level=SummaryLevel.CONCISE
        )
        
        # Override the log directory for testing
        logger.log_dir = Path(temp_dir)
        logger.human_logger.log_dir = Path(temp_dir)
        logger.human_logger.summary_file = Path(temp_dir) / f"test_human.md"
        
        # Simulate agent execution
        logger.log_agent_start("test-agent", '{"requirements": ["REQ-001"]}', "Starting test")
        logger.log_tool_call("test-agent", "write_file", {"file_path": "test.py"}, "Creating file")
        logger.log_reasoning("test-agent", "Thinking about next steps", "Using Python for implementation")
        logger.log_agent_complete("test-agent", True, "Test completed")
        
        # Close and check human log exists
        logger.close_session()
        
        assert logger.human_logger.summary_file.exists()
        
        with open(logger.human_logger.summary_file, 'r') as f:
            content = f.read()
            assert "test-agent" in content
            assert "SUCCESS" in content
            print("[PASS] Integration with ReasoningLogger working")
        
        return True

def test_agent_summary_formatting():
    """Test AgentSummary markdown formatting"""
    print("\n=== Testing AgentSummary Formatting ===")
    
    summary = AgentSummary(
        name="rapid-builder",
        start_time="10:30:00",
        end_time="10:35:00",
        status="success",
        requirements=["PORTFOLIO-001", "BLOG-001"],
        files_created=["main.py", "database.py", "config.json"],
        key_decisions=["Using FastAPI framework"],
        handoff_to=["frontend-specialist", "database-expert"]
    )
    
    markdown = summary.format_markdown()
    
    assert "rapid-builder" in markdown
    assert "[OK]" in markdown
    assert "PORTFOLIO-001" in markdown
    assert "main.py" in markdown
    assert "frontend-specialist" in markdown
    print("[PASS] AgentSummary formats correctly")
    
    # Test with many files
    summary.files_created = [f"file{i}.py" for i in range(10)]
    markdown = summary.format_markdown()
    assert "10 files" in markdown
    print("[PASS] AgentSummary handles many files correctly")
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Human-Readable Logger")
    print("=" * 60)
    
    tests = [
        test_human_logger_creation,
        test_agent_lifecycle,
        test_file_operations,
        test_error_tracking,
        test_summary_levels,
        test_integration_with_reasoning_logger,
        test_agent_summary_formatting
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
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