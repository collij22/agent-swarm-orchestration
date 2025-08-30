#!/usr/bin/env python3
"""
Comprehensive Test Suite for DevPortfolio Improvements
Tests all improvements made to address the 35% completion issue
"""

import unittest
import asyncio
import json
from pathlib import Path
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools
from lib.requirement_tracker import RequirementTracker, Requirement, RequirementPriority
from lib.agent_validator import AgentValidator, ValidationCheck
from lib.agent_logger import get_logger


class TestRequirementTracker(unittest.TestCase):
    """Test requirement tracking functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.tracker = RequirementTracker()
    
    def test_add_requirement(self):
        """Test adding requirements"""
        req = Requirement(
            id="TEST-001",
            name="Test Feature",
            description="Test description",
            priority=RequirementPriority.HIGH
        )
        
        self.tracker.add_requirement(req)
        self.assertIn("TEST-001", self.tracker.requirements)
        self.assertEqual(self.tracker.requirements["TEST-001"].name, "Test Feature")
    
    def test_assign_to_agent(self):
        """Test assigning requirements to agents"""
        req = Requirement(id="TEST-001", name="Test Feature", description="Test")
        self.tracker.add_requirement(req)
        
        self.tracker.assign_to_agent("test-agent", ["TEST-001"])
        
        self.assertIn("test-agent", self.tracker.agent_assignments)
        self.assertIn("TEST-001", self.tracker.agent_assignments["test-agent"])
        self.assertIn("test-agent", self.tracker.requirements["TEST-001"].assigned_agents)
    
    def test_update_progress(self):
        """Test updating requirement progress"""
        req = Requirement(id="TEST-001", name="Test", description="Test")
        self.tracker.add_requirement(req)
        
        self.tracker.update_progress("TEST-001", 50)
        self.assertEqual(self.tracker.requirements["TEST-001"].completion_percentage, 50)
        
        self.tracker.update_progress("TEST-001", 100)
        self.assertEqual(self.tracker.requirements["TEST-001"].completion_percentage, 100)
    
    def test_deliverables_tracking(self):
        """Test tracking deliverables"""
        req = Requirement(
            id="TEST-001",
            name="Test",
            description="Test",
            deliverables=["file1.py", "file2.py", "file3.py"]
        )
        self.tracker.add_requirement(req)
        
        # Add deliverables
        self.tracker.add_deliverable("TEST-001", "file1.py")
        self.tracker.add_deliverable("TEST-001", "file2.py")
        
        # Check auto-calculated progress
        self.assertEqual(self.tracker.requirements["TEST-001"].completion_percentage, 66)
        
        # Add final deliverable
        self.tracker.add_deliverable("TEST-001", "file3.py")
        self.assertEqual(self.tracker.requirements["TEST-001"].completion_percentage, 100)
    
    def test_coverage_report(self):
        """Test coverage report generation"""
        # Add requirements
        self.tracker.add_requirement(Requirement(
            id="HIGH-001",
            name="High Priority",
            description="Test",
            priority=RequirementPriority.HIGH
        ))
        self.tracker.add_requirement(Requirement(
            id="LOW-001",
            name="Low Priority",
            description="Test",
            priority=RequirementPriority.LOW
        ))
        
        # Assign and update
        self.tracker.assign_to_agent("agent1", ["HIGH-001"])
        self.tracker.update_progress("HIGH-001", 100)
        
        # Generate report
        report = self.tracker.generate_coverage_report()
        
        self.assertEqual(report["total_requirements"], 2)
        self.assertEqual(report["overall_coverage"], 50.0)
        self.assertEqual(report["uncovered"], 1)  # LOW-001 not assigned


class TestAgentValidator(unittest.TestCase):
    """Test agent output validation"""
    
    def setUp(self):
        """Setup test environment"""
        self.validator = AgentValidator()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test context
        self.context = AgentContext(
            project_requirements={"name": "TestProject"},
            completed_tasks=[],
            artifacts={"project_directory": self.temp_dir},
            decisions=[],
            current_phase="development"
        )
    
    def tearDown(self):
        """Clean up temp directory"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_frontend_validation_failure(self):
        """Test frontend-specialist validation when no files created"""
        # No files created - should fail
        success, report = self.validator.validate_agent_output(
            "frontend-specialist",
            self.context
        )
        
        self.assertFalse(success)
        self.assertEqual(report["summary"]["failed"], 5)  # All checks should fail
    
    def test_frontend_validation_success(self):
        """Test frontend-specialist validation with proper files"""
        # Create expected files
        frontend_dir = Path(self.temp_dir) / "frontend"
        frontend_dir.mkdir(parents=True)
        
        # Create package.json
        (frontend_dir / "package.json").write_text('{"name": "test"}')
        
        # Create App component
        src_dir = frontend_dir / "src"
        src_dir.mkdir()
        (src_dir / "App.tsx").write_text("export const App = () => <div>App</div>;")
        
        # Create API client
        api_dir = src_dir / "api"
        api_dir.mkdir()
        (api_dir / "client.ts").write_text("export const apiClient = {};")
        
        # Create auth components
        auth_dir = src_dir / "components" / "auth"
        auth_dir.mkdir(parents=True)
        (auth_dir / "Login.tsx").write_text("export const Login = () => <div>Login</div>;")
        
        # Add files to context
        self.context.add_created_file("frontend-specialist", str(frontend_dir / "package.json"))
        self.context.add_created_file("frontend-specialist", str(src_dir / "App.tsx"))
        self.context.add_created_file("frontend-specialist", str(api_dir / "client.ts"))
        self.context.add_created_file("frontend-specialist", str(auth_dir / "Login.tsx"))
        self.context.add_created_file("frontend-specialist", str(auth_dir / "Register.tsx"))
        
        # Validate
        success, report = self.validator.validate_agent_output(
            "frontend-specialist",
            self.context
        )
        
        self.assertTrue(success)
        self.assertGreater(report["summary"]["passed"], 2)
    
    def test_ai_specialist_validation(self):
        """Test AI specialist validation"""
        # Create backend directory
        backend_dir = Path(self.temp_dir) / "backend" / "services"
        backend_dir.mkdir(parents=True)
        
        # Create placeholder AI service (should fail)
        ai_service_path = backend_dir / "ai_service.py"
        ai_service_path.write_text("# TODO: Implement\npass")
        
        success, report = self.validator.validate_agent_output(
            "ai-specialist",
            self.context
        )
        
        self.assertFalse(success)
        
        # Create proper AI service
        ai_service_content = """
import openai

class AIService:
    def __init__(self):
        self.client = openai.Client()
    
    async def generate_suggestions(self, content):
        return await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": content}]
        )
"""
        ai_service_path.write_text(ai_service_content)
        
        success, report = self.validator.validate_agent_output(
            "ai-specialist",
            self.context
        )
        
        self.assertTrue(success)
    
    def test_custom_validation(self):
        """Test adding custom validation checks"""
        # Add custom check
        self.validator.add_custom_validation(
            "test-agent",
            ValidationCheck(
                name="custom_check",
                description="Custom validation",
                validator=lambda ctx: True  # Always passes
            )
        )
        
        success, report = self.validator.validate_agent_output(
            "test-agent",
            self.context
        )
        
        self.assertTrue(success)
        self.assertIn("custom_check", report["checks"])


class TestAIServiceFix(unittest.TestCase):
    """Test AI service implementation fix"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_ai_service_creation(self):
        """Test that AI service is properly created"""
        # Import the fix function
        from fix_ai_service import create_proper_ai_service
        
        # Run the fix
        asyncio.run(create_proper_ai_service(Path(self.temp_dir)))
        
        # Check file exists
        ai_service_path = Path(self.temp_dir) / "backend" / "services" / "ai_service.py"
        self.assertTrue(ai_service_path.exists())
        
        # Check file size (should be substantial)
        self.assertGreater(ai_service_path.stat().st_size, 1000)
        
        # Check content has proper implementation
        content = ai_service_path.read_text()
        self.assertIn("class AIService", content)
        self.assertIn("async def generate_content_suggestions", content)
        self.assertIn("async def categorize_task", content)
        self.assertIn("OpenAI", content.lower())


class TestIntegration(unittest.TestCase):
    """Integration tests for all improvements"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = RequirementTracker()
        self.validator = AgentValidator()
        
        # Add test requirements
        self.tracker.add_requirement(Requirement(
            id="FRONTEND-001",
            name="React Frontend",
            description="Create React frontend",
            priority=RequirementPriority.HIGH,
            deliverables=["package.json", "App.tsx", "api/client.ts"]
        ))
        
        self.tracker.add_requirement(Requirement(
            id="AI-001",
            name="AI Service",
            description="Implement AI service",
            priority=RequirementPriority.HIGH,
            deliverables=["ai_service.py"]
        ))
    
    def tearDown(self):
        """Clean up"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """Test complete workflow with tracking and validation"""
        context = AgentContext(
            project_requirements={"name": "TestProject"},
            completed_tasks=[],
            artifacts={"project_directory": self.temp_dir},
            decisions=[],
            current_phase="development"
        )
        
        # Simulate frontend-specialist execution
        self.tracker.assign_to_agent("frontend-specialist", ["FRONTEND-001"])
        self.tracker.mark_in_progress("FRONTEND-001")
        
        # Create frontend files
        frontend_dir = Path(self.temp_dir) / "frontend"
        frontend_dir.mkdir(parents=True)
        
        # Create deliverables
        (frontend_dir / "package.json").write_text('{"name": "test"}')
        self.tracker.add_deliverable("FRONTEND-001", "package.json")
        
        src_dir = frontend_dir / "src"
        src_dir.mkdir()
        (src_dir / "App.tsx").write_text("export const App = () => <div>App</div>;")
        self.tracker.add_deliverable("FRONTEND-001", "App.tsx")
        
        api_dir = src_dir / "api"
        api_dir.mkdir()
        (api_dir / "client.ts").write_text("export const apiClient = {};")
        self.tracker.add_deliverable("FRONTEND-001", "api/client.ts")
        
        # Add to context
        context.add_created_file("frontend-specialist", str(frontend_dir / "package.json"))
        context.add_created_file("frontend-specialist", str(src_dir / "App.tsx"))
        context.add_created_file("frontend-specialist", str(api_dir / "client.ts"))
        
        # Validate frontend
        success, report = self.validator.validate_agent_output(
            "frontend-specialist",
            context
        )
        
        if success:
            self.tracker.mark_completed("FRONTEND-001")
        
        # Check requirement coverage
        self.assertEqual(
            self.tracker.requirements["FRONTEND-001"].completion_percentage,
            100
        )
        
        # Simulate AI specialist
        self.tracker.assign_to_agent("ai-specialist", ["AI-001"])
        self.tracker.mark_in_progress("AI-001")
        
        # Create AI service
        from fix_ai_service import create_proper_ai_service
        asyncio.run(create_proper_ai_service(Path(self.temp_dir)))
        
        self.tracker.add_deliverable("AI-001", "ai_service.py")
        self.tracker.mark_completed("AI-001")
        
        # Generate final report
        coverage_report = self.tracker.generate_coverage_report()
        
        # Both requirements should be complete
        self.assertEqual(coverage_report["overall_coverage"], 100.0)
        self.assertEqual(coverage_report["status_summary"]["completed"], 2)
        
        print("\n=== Coverage Report ===")
        print(json.dumps(coverage_report, indent=2))


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRequirementTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestAIServiceFix))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)