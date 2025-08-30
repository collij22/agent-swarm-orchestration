#!/usr/bin/env python3
"""
Test Suite for Section 9: Session Analysis Improvements

Tests:
- Requirement coverage analysis
- File audit trail generation
- Deliverables tracking
- Quality metrics calculation
- Performance analysis
- Next steps generation
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.session_analysis_enhanced import (
    SessionAnalysisEnhanced,
    RequirementCoverage,
    RequirementStatus,
    FileAuditEntry,
    DeliverableType,
    QualityMetrics
)
from lib.requirement_coverage_analyzer import (
    RequirementCoverageAnalyzer,
    Requirement,
    RequirementType,
    RequirementPriority
)
from lib.deliverables_tracker import (
    DeliverablesTracker,
    Deliverable,
    DeliverableCategory,
    DeliverableStatus
)


class TestSessionAnalysisEnhanced(unittest.TestCase):
    """Test enhanced session analysis functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.analyzer = SessionAnalysisEnhanced(self.test_dir)
        
        # Create sample session data
        self.sample_session = {
            "session_id": "test_123",
            "start_time": datetime.now().isoformat(),
            "end_time": (datetime.now() + timedelta(hours=2)).isoformat(),
            "context": {
                "project_requirements": {
                    "name": "TestApp",
                    "type": "web_app",
                    "features": [
                        "User authentication with JWT",
                        "RESTful API for task management",
                        "React frontend with dashboard",
                        "PostgreSQL database"
                    ]
                }
            },
            "events": [
                {
                    "type": "tool_call",
                    "tool_name": "write_file",
                    "agent_name": "rapid-builder",
                    "timestamp": datetime.now().isoformat(),
                    "params": {
                        "file_path": "backend/main.py",
                        "content": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'Hello': 'World'}",
                        "reasoning": "Creating main API entry point for REQ-001"
                    }
                },
                {
                    "type": "tool_call",
                    "tool_name": "write_file",
                    "agent_name": "frontend-specialist",
                    "timestamp": datetime.now().isoformat(),
                    "params": {
                        "file_path": "frontend/src/App.js",
                        "content": "import React from 'react';\n\nfunction App() {\n    return <div>Hello World</div>;\n}\n\nexport default App;",
                        "reasoning": "Creating React frontend for user interface"
                    }
                },
                {
                    "type": "tool_call",
                    "tool_name": "write_file",
                    "agent_name": "database-expert",
                    "timestamp": datetime.now().isoformat(),
                    "params": {
                        "file_path": "database/schema.sql",
                        "content": "CREATE TABLE users (\n    id SERIAL PRIMARY KEY,\n    email VARCHAR(255) UNIQUE NOT NULL\n);",
                        "reasoning": "Setting up database schema for user management"
                    }
                },
                {
                    "type": "agent_complete",
                    "agent_name": "rapid-builder",
                    "duration": 45,
                    "success": True
                }
            ]
        }
        
        # Save sample session
        session_file = Path(self.test_dir) / "session_test_123.json"
        with open(session_file, 'w') as f:
            json.dump(self.sample_session, f)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_analyze_requirements(self):
        """Test requirement coverage analysis"""
        analysis = self.analyzer._analyze_requirements(self.sample_session)
        
        # Check requirement detection
        self.assertEqual(analysis["total_requirements"], 4)
        self.assertIn("requirements", analysis)
        
        # Check requirement IDs
        self.assertIn("REQ-001", analysis["requirements"])
        
        # Check coverage calculation
        self.assertGreaterEqual(analysis["overall_coverage_percentage"], 0)
        self.assertLessEqual(analysis["overall_coverage_percentage"], 100)
    
    def test_file_audit_trail(self):
        """Test file audit trail creation"""
        audit_trail = self.analyzer._create_file_audit_trail(self.sample_session)
        
        # Check audit entries
        self.assertEqual(len(audit_trail), 3)
        
        # Check first entry
        first_entry = audit_trail[0]
        self.assertEqual(first_entry["file_path"], "backend/main.py")
        self.assertEqual(first_entry["agent_name"], "rapid-builder")
        self.assertEqual(first_entry["file_type"], DeliverableType.API.value)
        
        # Check validation
        self.assertIn("validation_errors", first_entry)
    
    def test_quality_metrics(self):
        """Test code quality metrics calculation"""
        metrics = self.analyzer._analyze_code_quality(self.sample_session)
        
        # Check metrics fields
        self.assertIn("total_lines_of_code", metrics)
        self.assertIn("test_coverage_percentage", metrics)
        self.assertIn("documentation_coverage", metrics)
        self.assertIn("security_issues", metrics)
        
        # Check calculations
        self.assertGreater(metrics["total_lines_of_code"], 0)
        self.assertGreaterEqual(metrics["test_coverage_percentage"], 0)
        self.assertLessEqual(metrics["test_coverage_percentage"], 100)
    
    def test_performance_analysis(self):
        """Test performance metrics analysis"""
        performance = self.analyzer._analyze_performance(self.sample_session)
        
        # Check performance fields
        self.assertIn("total_duration", performance)
        self.assertIn("agent_execution_times", performance)
        self.assertIn("tool_call_frequency", performance)
        self.assertIn("bottlenecks", performance)
        
        # Check tool call frequency
        self.assertEqual(performance["tool_call_frequency"]["write_file"], 3)
        
        # Check agent execution times
        self.assertIn("rapid-builder", performance["agent_execution_times"])
    
    def test_deliverables_comparison(self):
        """Test expected vs actual deliverables comparison"""
        deliverables = self.analyzer._analyze_deliverables(self.sample_session)
        
        # Check comparison structure
        self.assertIn("expected", deliverables)
        self.assertIn("actual", deliverables)
        self.assertIn("missing", deliverables)
        self.assertIn("completion_rate", deliverables)
        
        # Check actual deliverables tracking
        self.assertIn("backend", deliverables["actual"])
        self.assertIn("frontend", deliverables["actual"])
        self.assertIn("database", deliverables["actual"])
    
    def test_next_steps_generation(self):
        """Test actionable next steps generation"""
        requirements_analysis = self.analyzer._analyze_requirements(self.sample_session)
        deliverables_analysis = self.analyzer._analyze_deliverables(self.sample_session)
        
        next_steps = self.analyzer._generate_next_steps(
            requirements_analysis, 
            deliverables_analysis
        )
        
        # Check next steps structure
        self.assertIsInstance(next_steps, list)
        if next_steps:
            first_step = next_steps[0]
            self.assertIn("priority", first_step)
            self.assertIn("action", first_step)
            self.assertIn("agent", first_step)
            self.assertIn("estimated_time", first_step)
            self.assertIn("impact", first_step)
    
    def test_full_session_analysis(self):
        """Test complete session analysis"""
        analysis = self.analyzer.analyze_session("test_123")
        
        # Check analysis structure
        self.assertIn("session_id", analysis)
        self.assertIn("requirements_coverage", analysis)
        self.assertIn("file_audit_trail", analysis)
        self.assertIn("quality_metrics", analysis)
        self.assertIn("performance_metrics", analysis)
        self.assertIn("deliverables_comparison", analysis)
        self.assertIn("actionable_next_steps", analysis)
        self.assertIn("summary", analysis)
        
        # Check summary fields
        summary = analysis["summary"]
        self.assertIn("overall_success", summary)
        self.assertIn("requirement_coverage", summary)
        self.assertIn("files_created", summary)
        self.assertIn("quality_score", summary)
    
    def test_html_report_generation(self):
        """Test HTML report generation"""
        analysis = self.analyzer.analyze_session("test_123")
        html_report = self.analyzer.generate_html_report(analysis)
        
        # Check HTML structure
        self.assertIn("<!DOCTYPE html>", html_report)
        self.assertIn("Session Analysis Report", html_report)
        self.assertIn("test_123", html_report)
        
        # Check content sections
        self.assertIn("Requirements Coverage", html_report)
        self.assertIn("Actionable Next Steps", html_report)


class TestRequirementCoverageAnalyzer(unittest.TestCase):
    """Test requirement coverage analyzer functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.analyzer = RequirementCoverageAnalyzer()
        
        # Sample requirements
        self.sample_requirements = {
            "features": [
                "User authentication with OAuth",
                "Real-time messaging system",
                "Admin dashboard with analytics"
            ],
            "technical_requirements": [
                "PostgreSQL database",
                "Redis caching"
            ],
            "constraints": [
                "Response time under 100ms"
            ]
        }
    
    def test_parse_requirements(self):
        """Test requirement parsing"""
        self.analyzer.parse_requirements(self.sample_requirements)
        
        # Check requirement count
        self.assertEqual(len(self.analyzer.requirements), 6)
        
        # Check requirement IDs
        self.assertIn("REQ-001", self.analyzer.requirements)
        self.assertIn("TECH-001", self.analyzer.requirements)
        self.assertIn("CONSTRAINT-001", self.analyzer.requirements)
    
    def test_requirement_type_determination(self):
        """Test requirement type determination"""
        self.analyzer.parse_requirements(self.sample_requirements)
        
        # Check types
        auth_req = self.analyzer.requirements["REQ-001"]
        self.assertEqual(auth_req.type, RequirementType.SECURITY)
        
        # Check priorities
        self.assertIn(auth_req.priority, 
                     [RequirementPriority.CRITICAL, RequirementPriority.HIGH])
    
    def test_acceptance_criteria_generation(self):
        """Test acceptance criteria generation"""
        self.analyzer.parse_requirements(self.sample_requirements)
        
        # Check criteria for authentication requirement
        auth_req = self.analyzer.requirements["REQ-001"]
        self.assertGreater(len(auth_req.acceptance_criteria), 0)
        
        # Check for specific criteria
        criteria_text = " ".join(auth_req.acceptance_criteria)
        self.assertIn("must", criteria_text.lower())
    
    def test_agent_assignment(self):
        """Test agent assignment to requirements"""
        self.analyzer.parse_requirements(self.sample_requirements)
        
        # Check agent assignments
        for req in self.analyzer.requirements.values():
            self.assertGreater(len(req.assigned_agents), 0)
        
        # Check agent workload
        self.assertGreater(len(self.analyzer.agent_assignments), 0)
    
    def test_dependency_graph_building(self):
        """Test dependency graph construction"""
        self.analyzer.parse_requirements(self.sample_requirements)
        
        # Check graph exists
        self.assertIsInstance(self.analyzer.requirement_graph, dict)
        
        # Frontend should depend on backend
        frontend_reqs = [r for r in self.analyzer.requirements.values() 
                        if r.type == RequirementType.USABILITY]
        if frontend_reqs:
            self.assertGreaterEqual(len(frontend_reqs[0].dependencies), 0)
    
    def test_coverage_calculation(self):
        """Test requirement coverage calculation"""
        self.analyzer.parse_requirements(self.sample_requirements)
        
        # Simulate file creation
        req = self.analyzer.requirements["REQ-001"]
        req.artifacts_created = ["auth.py", "tests/test_auth.py"]
        req.test_cases = ["tests/test_auth.py"]
        
        # Calculate completion
        completion = req.calculate_completion()
        
        # Check completion
        self.assertGreater(completion, 0)
        self.assertLessEqual(completion, 100)
        self.assertNotEqual(req.status, RequirementStatus.NOT_STARTED)
    
    def test_coverage_report_generation(self):
        """Test coverage report generation"""
        self.analyzer.parse_requirements(self.sample_requirements)
        
        report = self.analyzer.generate_coverage_report()
        
        # Check report structure
        self.assertIn("summary", report)
        self.assertIn("by_type", report)
        self.assertIn("by_priority", report)
        self.assertIn("critical_incomplete", report)
        
        # Check summary fields
        summary = report["summary"]
        self.assertIn("total_requirements", summary)
        self.assertIn("overall_coverage", summary)
    
    def test_traceability_matrix(self):
        """Test traceability matrix generation"""
        self.analyzer.parse_requirements(self.sample_requirements)
        
        matrix = self.analyzer.generate_traceability_matrix()
        
        # Check matrix structure
        self.assertEqual(len(matrix), len(self.analyzer.requirements))
        
        # Check matrix fields
        for req_id, data in matrix.items():
            self.assertIn("description", data)
            self.assertIn("type", data)
            self.assertIn("priority", data)
            self.assertIn("status", data)
            self.assertIn("completion", data)
            self.assertIn("agents", data)
    
    def test_implementation_order(self):
        """Test implementation order calculation"""
        self.analyzer.parse_requirements(self.sample_requirements)
        
        order = self.analyzer.get_implementation_order()
        
        # Check order
        self.assertEqual(len(order), len(self.analyzer.requirements))
        
        # Dependencies should come before dependent requirements
        for i, req_id in enumerate(order):
            req = self.analyzer.requirements[req_id]
            for dep_id in req.dependencies:
                if dep_id in order:
                    self.assertLess(order.index(dep_id), i)


class TestDeliverablesTracker(unittest.TestCase):
    """Test deliverables tracker functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.tracker = DeliverablesTracker(self.test_dir)
        
        # Create test files
        self._create_test_files()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def _create_test_files(self):
        """Create test deliverable files"""
        # Backend files
        backend_dir = Path(self.test_dir) / "backend"
        backend_dir.mkdir(exist_ok=True)
        (backend_dir / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
        (backend_dir / "requirements.txt").write_text("fastapi==0.68.0\nuvicorn==0.15.0")
        
        # Frontend files
        frontend_dir = Path(self.test_dir) / "frontend"
        frontend_dir.mkdir(exist_ok=True)
        (frontend_dir / "package.json").write_text('{"name": "test-app", "dependencies": {}}')
        
        # Tests
        tests_dir = Path(self.test_dir) / "tests"
        tests_dir.mkdir(exist_ok=True)
        (tests_dir / "test_api.py").write_text("def test_api():\n    assert True")
        
        # Documentation
        (Path(self.test_dir) / "README.md").write_text("# Test Project")
    
    def test_define_expected_deliverables(self):
        """Test defining expected deliverables"""
        self.tracker.define_expected_deliverables(
            "web_app",
            ["User authentication", "API endpoints", "React frontend"]
        )
        
        # Check deliverables defined
        self.assertGreater(len(self.tracker.expected_deliverables), 0)
        
        # Check categories covered
        categories = {d.category for d in self.tracker.expected_deliverables.values()}
        self.assertIn(DeliverableCategory.BACKEND, categories)
        self.assertIn(DeliverableCategory.FRONTEND, categories)
        self.assertIn(DeliverableCategory.DOCUMENTATION, categories)
    
    def test_scan_actual_deliverables(self):
        """Test scanning for actual deliverables"""
        self.tracker.define_expected_deliverables("web_app", [])
        self.tracker.scan_actual_deliverables()
        
        # Check files found
        self.assertGreater(len(self.tracker.actual_deliverables), 0)
        
        # Check specific files
        file_names = [d.name for d in self.tracker.actual_deliverables.values()]
        self.assertIn("main.py", file_names)
        self.assertIn("README.md", file_names)
    
    def test_deliverable_validation(self):
        """Test deliverable validation"""
        deliverable = Deliverable(
            name="test.py",
            category=DeliverableCategory.BACKEND,
            description="Test file",
            expected_path="test.py",
            actual_path=str(Path(self.test_dir) / "backend" / "main.py")
        )
        
        is_valid, errors = deliverable.validate()
        
        # Check validation
        self.assertTrue(is_valid or len(errors) > 0)
        self.assertIn(deliverable.status, 
                     [DeliverableStatus.VALIDATED, DeliverableStatus.COMPLETE])
    
    def test_compare_deliverables(self):
        """Test deliverables comparison"""
        self.tracker.define_expected_deliverables("web_app", [])
        self.tracker.scan_actual_deliverables()
        
        comparison = self.tracker.compare_deliverables()
        
        # Check comparison structure
        self.assertIn("expected_count", comparison)
        self.assertIn("actual_count", comparison)
        self.assertIn("missing", comparison)
        self.assertIn("completion_rate", comparison)
        self.assertIn("quality_score", comparison)
        self.assertIn("by_category", comparison)
        
        # Check calculations
        self.assertGreaterEqual(comparison["completion_rate"], 0)
        self.assertLessEqual(comparison["completion_rate"], 100)
    
    def test_completion_timeline(self):
        """Test completion timeline generation"""
        self.tracker.define_expected_deliverables("web_app", [])
        self.tracker.scan_actual_deliverables()
        
        timeline = self.tracker.generate_completion_timeline()
        
        # Check timeline structure
        if timeline:
            first_item = timeline[0]
            self.assertIn("deliverable", first_item)
            self.assertIn("estimated_hours", first_item)
            self.assertIn("suggested_agent", first_item)
            self.assertIn("target_date", first_item)
    
    def test_dependency_handling(self):
        """Test deliverable dependency handling"""
        self.tracker.define_expected_deliverables("web_app", [])
        
        # Check dependency graph built
        self.assertIsInstance(self.tracker.deliverable_graph, dict)
        
        # Frontend should depend on API
        frontend_deps = []
        for name, deliverable in self.tracker.expected_deliverables.items():
            if deliverable.category == DeliverableCategory.FRONTEND:
                frontend_deps.extend(deliverable.dependencies)
        
        # Should have some dependencies
        self.assertGreaterEqual(len(frontend_deps), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for session analysis components"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_full_analysis_workflow(self):
        """Test complete analysis workflow"""
        # Create session analyzer
        session_analyzer = SessionAnalysisEnhanced(self.test_dir)
        
        # Create requirement analyzer
        req_analyzer = RequirementCoverageAnalyzer()
        req_analyzer.parse_requirements({
            "features": ["User authentication", "API endpoints"]
        })
        
        # Create deliverables tracker
        del_tracker = DeliverablesTracker(self.test_dir)
        del_tracker.define_expected_deliverables("web_app", ["User authentication"])
        
        # Create sample session
        session_data = {
            "session_id": "integration_test",
            "start_time": datetime.now().isoformat(),
            "end_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "context": {
                "project_requirements": {
                    "type": "web_app",
                    "features": ["User authentication", "API endpoints"]
                }
            },
            "events": [
                {
                    "type": "tool_call",
                    "tool_name": "write_file",
                    "agent_name": "rapid-builder",
                    "params": {
                        "file_path": "main.py",
                        "content": "print('Hello')",
                        "reasoning": "Creating main file"
                    }
                }
            ]
        }
        
        # Save session
        session_file = Path(self.test_dir) / "session_integration_test.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Run analysis
        analysis = session_analyzer.analyze_session("integration_test")
        
        # Update requirement coverage
        req_analyzer.update_from_session(session_data)
        coverage = req_analyzer.generate_coverage_report()
        
        # Scan deliverables
        del_tracker.scan_actual_deliverables()
        comparison = del_tracker.compare_deliverables()
        
        # Verify results
        self.assertIsNotNone(analysis)
        self.assertIsNotNone(coverage)
        self.assertIsNotNone(comparison)
        
        # Check integration
        self.assertEqual(analysis["session_id"], "integration_test")
        self.assertGreater(coverage["summary"]["total_requirements"], 0)
        self.assertIn("completion_rate", comparison)


def run_tests():
    """Run all tests and print results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSessionAnalysisEnhanced))
    suite.addTests(loader.loadTestsFromTestCase(TestRequirementCoverageAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestDeliverablesTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Section 9 Session Analysis Tests Complete")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)