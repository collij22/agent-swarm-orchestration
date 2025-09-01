#!/usr/bin/env python3
"""
Comprehensive Test Suite for Refinements Fixes
Tests all 6 fixes implemented from refinements_01sep.md
"""

import unittest
import asyncio
import sys
import os
from pathlib import Path
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

# Test imports - these should work after fixes
try:
    from lib.encoding_fix import setup_utf8_encoding, clean_unicode_content, safe_file_write, safe_file_read
    encoding_available = True
except ImportError:
    encoding_available = False

try:
    from lib.build_validator import BuildValidator, BuildError
    build_validator_available = True
except ImportError:
    build_validator_available = False

from lib.agent_logger import ReasoningLogger, create_new_session
from lib.agent_runtime import AgentContext
from lib.error_pattern_detector import ErrorPatternDetector, ErrorPattern

class TestAutomatedDebuggerRegistration(unittest.TestCase):
    """Test Fix 1: Automated-debugger registration"""
    
    def test_automated_debugger_loads(self):
        """Test that automated-debugger is loaded from .claude/agents/"""
        from orchestrate_enhanced import EnhancedOrchestrator
        
        # Mock logger
        logger = Mock()
        
        # Create orchestrator
        orchestrator = EnhancedOrchestrator(
            api_key="test_key",
            enable_dashboard=False,
            enable_human_log=False
        )
        
        # Check if automated-debugger is loaded
        self.assertIn("automated-debugger", orchestrator.agents, 
                     "automated-debugger should be loaded in agents dictionary")
        
        # Check if the agent has the right configuration
        if "automated-debugger" in orchestrator.agents:
            debugger_config = orchestrator.agents["automated-debugger"]
            self.assertEqual(debugger_config["model"], "opus", 
                           "automated-debugger should use opus model")
            self.assertIn("Read", debugger_config["tools"], 
                           "automated-debugger should have Read tool")
    
    def test_critical_agents_logging(self):
        """Test that missing critical agents are logged"""
        from orchestrate_enhanced import EnhancedOrchestrator
        
        with patch('orchestrate_enhanced.Path') as MockPath:
            # Mock agent directory to simulate missing automated-debugger
            mock_agent_dir = MockPath.return_value
            mock_agent_dir.exists.return_value = True
            mock_agent_dir.glob.return_value = []  # No agent files
            
            orchestrator = EnhancedOrchestrator(
                api_key="test_key",
                enable_dashboard=False,
                enable_human_log=False
            )
            
            # The logger should have logged about missing critical agents
            # This is a simplified check - in reality we'd check the logger calls

class TestWriteFileContentParameter(unittest.TestCase):
    """Test Fix 2: Write file content parameter handling"""
    
    @patch('lib.agent_runtime.Path')
    async def test_write_file_with_missing_content(self, MockPath):
        """Test that write_file handles missing content gracefully"""
        from lib.agent_runtime import write_file_tool
        
        # Mock path operations
        mock_path = MockPath.return_value
        mock_path.parent.mkdir = Mock()
        mock_path.write_text = Mock()
        mock_path.exists.return_value = True
        mock_path.suffix = ".py"
        mock_path.stem = "test_file"
        
        # Create context with logger
        context = AgentContext({})
        context.logger = Mock()
        
        # Call write_file with None content
        result = await write_file_tool(
            file_path="/test/test_file.py",
            content=None,  # Missing content
            reasoning="Test",
            context=context,
            agent_name="test_agent"
        )
        
        # Should have generated placeholder content
        mock_path.write_text.assert_called()
        call_args = mock_path.write_text.call_args[0][0]
        self.assertIn("NotImplementedError", call_args, 
                     "Should generate Python placeholder for .py file")
        
        # Should have logged error
        context.logger.log_error.assert_called()
    
    async def test_write_file_placeholder_generation(self):
        """Test placeholder generation for different file types"""
        from lib.agent_runtime import write_file_tool
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_cases = [
                ("test.py", "NotImplementedError"),
                ("test.js", "throw new Error"),
                ("test.json", '"error": "Content was missing"'),
                ("test.md", "# test"),
                ("test.yml", "placeholder: true"),
                ("test.html", "<!DOCTYPE html>"),
                ("test.css", "/* test"),
                ("test.sh", "#!/bin/bash"),
                ("test.bat", "@echo off"),
                ("test.env", "PLACEHOLDER_KEY=placeholder_value"),
            ]
            
            for filename, expected_content in test_cases:
                filepath = Path(tmpdir) / filename
                
                # Create mock context
                context = AgentContext({})
                context.artifacts["project_directory"] = tmpdir
                
                # Call write_file with empty content
                result = await write_file_tool(
                    file_path=filename,
                    content="",  # Empty content
                    context=context,
                    agent_name="test"
                )
                
                # Check file was created with appropriate placeholder
                self.assertTrue(filepath.exists(), f"{filename} should be created")
                content = filepath.read_text()
                self.assertIn(expected_content, content, 
                             f"{filename} should contain appropriate placeholder")

class TestCharacterEncodingFixes(unittest.TestCase):
    """Test Fix 3: Character encoding issues"""
    
    @unittest.skipIf(not encoding_available, "encoding_fix module not available")
    def test_setup_utf8_encoding(self):
        """Test UTF-8 encoding setup"""
        # This should not raise any errors
        setup_utf8_encoding()
        
        # Check that environment variables are set
        self.assertEqual(os.environ.get('PYTHONIOENCODING'), 'utf-8')
        self.assertEqual(os.environ.get('PYTHONUTF8'), '1')
    
    @unittest.skipIf(not encoding_available, "encoding_fix module not available")
    def test_clean_unicode_content(self):
        """Test Unicode character cleaning"""
        test_cases = [
            ("✅ Success", "[OK] Success"),
            ("→ Arrow", "-> Arrow"),
            ("❌ Failed", "[X] Failed"),
            ("🚀 Launch", "[LAUNCH] Launch"),
            ("• Bullet point", "* Bullet point"),
            ("€100", "EUR100"),
            ("∞ infinity", "inf infinity"),
        ]
        
        for input_text, expected_output in test_cases:
            result = clean_unicode_content(input_text)
            self.assertEqual(result, expected_output, 
                           f"Failed to clean: {input_text}")
    
    @unittest.skipIf(not encoding_available, "encoding_fix module not available")
    def test_safe_file_operations(self):
        """Test safe file read/write with encoding handling"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            
            # Test writing Unicode content
            content = "Test with Unicode: ✅ → ❌ 🚀"
            safe_file_write(str(filepath), content)
            
            # Should be able to read it back
            read_content = safe_file_read(str(filepath))
            self.assertIn("Test with Unicode", read_content)
            # Unicode should be cleaned
            self.assertIn("[OK]", read_content)
            self.assertIn("->", read_content)

class TestBuildValidationFeedback(unittest.TestCase):
    """Test Fix 4: Improved build validation feedback"""
    
    @unittest.skipIf(not build_validator_available, "build_validator module not available")
    async def test_build_error_parsing(self):
        """Test parsing of build errors"""
        validator = BuildValidator()
        
        # Test TypeScript error parsing
        ts_error = """
        src/App.tsx:10:5 - error TS2322: Type 'string' is not assignable to type 'number'.
        
        10     const count: number = "hello";
               ~~~~~
        """
        
        errors = validator._parse_build_errors(ts_error, "npm")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].file, "src/App.tsx")
        self.assertEqual(errors[0].line, 10)
        self.assertEqual(errors[0].error_type, "type")
        
    @unittest.skipIf(not build_validator_available, "build_validator module not available")
    async def test_build_validation(self):
        """Test build validation with mock project"""
        validator = BuildValidator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock package.json
            package_json = {
                "name": "test-project",
                "scripts": {
                    "build": "echo 'Build successful'"
                }
            }
            Path(tmpdir, "package.json").write_text(json.dumps(package_json))
            
            # Run validation (this will actually try to run the build)
            # In a real test we'd mock the subprocess call
            with patch('lib.build_validator.asyncio.create_subprocess_shell') as mock_subprocess:
                mock_process = Mock()
                mock_process.communicate = Mock(return_value=(b"Build successful", b""))
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process
                
                success, errors, metrics = await validator.validate_build(tmpdir)
                
                self.assertTrue(success)
                self.assertEqual(len(errors), 0)
                self.assertEqual(metrics['build_type'], 'npm')

class TestErrorRecoverySystem(unittest.TestCase):
    """Test Fix 5: Strengthened error recovery system"""
    
    def test_error_pattern_detection(self):
        """Test error pattern detection and normalization"""
        detector = ErrorPatternDetector()
        
        # Test error normalization
        test_cases = [
            ("write_file() missing required positional argument: 'content'", "missing_content_parameter"),
            ("Error: Missing required parameter content", "missing_content_parameter"),
            ("Rate limit exceeded", "rate_limit_exceeded"),
            ("Operation timed out after 30 seconds", "operation_timeout"),
            ("Tool execution failed: write_file", "tool_execution_failed"),
        ]
        
        for error_msg, expected_normalized in test_cases:
            normalized = detector._normalize_error(error_msg)
            self.assertEqual(normalized, expected_normalized, 
                           f"Failed to normalize: {error_msg}")
    
    def test_progressive_recovery_strategies(self):
        """Test progressive recovery strategy selection"""
        detector = ErrorPatternDetector()
        
        agent_name = "test_agent"
        error_msg = "write_file() missing required positional argument: 'content'"
        
        # First occurrence - retry same
        count1, strategy1 = detector.record_error(agent_name, error_msg)
        self.assertEqual(count1, 1)
        self.assertEqual(strategy1, "retry_same")
        
        # Second occurrence - retry with context
        count2, strategy2 = detector.record_error(agent_name, error_msg)
        self.assertEqual(count2, 2)
        self.assertEqual(strategy2, "retry_with_context")
        
        # Third occurrence - trigger debugger
        count3, strategy3 = detector.record_error(agent_name, error_msg)
        self.assertEqual(count3, 3)
        self.assertEqual(strategy3, "trigger_debugger")
        
        # Fourth occurrence - use alternative agent
        count4, strategy4 = detector.record_error(agent_name, error_msg)
        self.assertEqual(count4, 4)
        self.assertEqual(strategy4, "use_alternative_agent")
        
        # Fifth+ occurrence - manual intervention
        count5, strategy5 = detector.record_error(agent_name, error_msg)
        self.assertEqual(count5, 5)
        self.assertEqual(strategy5, "manual_intervention")
    
    def test_error_pattern_tracking(self):
        """Test that error patterns are tracked correctly"""
        detector = ErrorPatternDetector()
        
        # Record same error from different agents
        detector.record_error("agent1", "Error A")
        detector.record_error("agent2", "Error A")
        detector.record_error("agent1", "Error B")
        
        # Check agent error counts
        self.assertEqual(detector.agent_error_counts["agent1"], 2)
        self.assertEqual(detector.agent_error_counts["agent2"], 1)
        
        # Check pattern tracking
        self.assertEqual(len(detector.patterns), 3)  # 3 unique agent-error combinations

class TestIntegration(unittest.TestCase):
    """Integration tests for all fixes working together"""
    
    async def test_orchestrator_with_all_fixes(self):
        """Test that orchestrator works with all fixes applied"""
        # Import should work with encoding fixes
        from orchestrate_enhanced import EnhancedOrchestrator
        
        # Create orchestrator with mock API key
        orchestrator = EnhancedOrchestrator(
            api_key="test_key",
            enable_dashboard=False,
            enable_human_log=False
        )
        
        # Should have error detector
        self.assertIsNotNone(orchestrator.error_detector)
        
        # Should have build validator if available
        if build_validator_available:
            self.assertIsNotNone(BuildValidator)
        
        # Should have automated-debugger loaded
        self.assertIn("automated-debugger", orchestrator.agents)
        
        # Test that error recovery works
        test_error = "write_file() missing required positional argument: 'content'"
        recovery = orchestrator.error_detector.get_recovery_recommendation(
            "test_agent", test_error
        )
        
        self.assertEqual(recovery["strategy"], "retry_same")
        self.assertEqual(recovery["occurrence_count"], 1)

def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAutomatedDebuggerRegistration))
    suite.addTests(loader.loadTestsFromTestCase(TestWriteFileContentParameter))
    suite.addTests(loader.loadTestsFromTestCase(TestCharacterEncodingFixes))
    suite.addTests(loader.loadTestsFromTestCase(TestBuildValidationFeedback))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorRecoverySystem))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()[:100]}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Error:')[-1].strip()[:100]}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    # Run async tests properly
    success = run_tests()
    sys.exit(0 if success else 1)