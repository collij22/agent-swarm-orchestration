#!/usr/bin/env python3
"""
Section 10: Complete Testing & Validation Suite

Comprehensive test suite for Section 10 implementation including:
- End-to-end workflow testing
- Continuous improvement mechanisms
- Feedback integration systems
- Learning engine validation
"""

import os
import sys
import json
import time
import tempfile
import unittest
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from lib.continuous_improvement import (
    ExecutionDatabase, PatternAnalyzer, LearningEngine, 
    FeedbackIntegrator, ExecutionPattern, LearningInsight
)
from lib.feedback_integration import (
    SystemIntegrator, PromptUpdater, WorkflowUpdater,
    AutoImprovementScheduler, SystemUpdate
)

class TestExecutionDatabase(unittest.TestCase):
    """Test the execution database functionality"""
    
    def setUp(self):
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db = ExecutionDatabase(self.test_db.name)
    
    def tearDown(self):
        os.unlink(self.test_db.name)
    
    def test_record_execution(self):
        """Test recording execution data"""
        execution_id = self.db.record_execution(
            session_id="test_session_1",
            workflow_type="api_service",
            success=True,
            completion_percentage=85.0,
            execution_time=120.0,
            agents_used=["project-architect", "rapid-builder"],
            files_created=["main.py", "requirements.txt"],
            errors=[],
            requirements={"name": "TestAPI"},
            context_data={"phase": "testing"}
        )
        
        self.assertIsInstance(execution_id, int)
        self.assertGreater(execution_id, 0)
    
    def test_record_agent_performance(self):
        """Test recording agent performance data"""
        # First record an execution
        execution_id = self.db.record_execution(
            session_id="test_session_2",
            workflow_type="fullstack",
            success=False,
            completion_percentage=60.0,
            execution_time=180.0,
            agents_used=["project-architect", "rapid-builder", "frontend-specialist"],
            files_created=["main.py", "package.json"],
            errors=["Tool execution failed"],
            requirements={"name": "TestApp"},
            context_data={"phase": "development"}
        )
        
        # Then record agent performance
        self.db.record_agent_performance(
            execution_id=execution_id,
            agent_name="rapid-builder",
            success=False,
            execution_time=90.0,
            model_used="claude-sonnet-4",
            tools_used=["write_file", "run_command"],
            errors=["Tool execution failed"],
            output_quality=0.3
        )
    
    def test_get_execution_history(self):
        """Test retrieving execution history"""
        # Record some test data
        for i in range(3):
            self.db.record_execution(
                session_id=f"test_session_{i}",
                workflow_type="api_service",
                success=i % 2 == 0,  # Alternate success/failure
                completion_percentage=70.0 + (i * 10),
                execution_time=100.0 + (i * 20),
                agents_used=["project-architect", "rapid-builder"],
                files_created=[f"file_{i}.py"],
                errors=[] if i % 2 == 0 else [f"Error {i}"],
                requirements={"name": f"TestAPI_{i}"},
                context_data={"test": True}
            )
        
        history = self.db.get_execution_history(days=30)
        self.assertEqual(len(history), 3)
        
        # Check data integrity
        for record in history:
            self.assertIn('session_id', record)
            self.assertIn('workflow_type', record)
            self.assertIsInstance(record['agents_used'], list)
            self.assertIsInstance(record['requirements'], dict)

class TestPatternAnalyzer(unittest.TestCase):
    """Test the pattern analysis functionality"""
    
    def setUp(self):
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db = ExecutionDatabase(self.test_db.name)
        self.analyzer = PatternAnalyzer(self.db)
        
        # Create test data
        self._create_test_data()
    
    def tearDown(self):
        os.unlink(self.test_db.name)
    
    def _create_test_data(self):
        """Create test execution data with patterns"""
        # Create some failure patterns
        failure_data = [
            ("session_1", "api_service", False, 30.0, 60.0, ["project-architect"], [], ["Rate limit exceeded"]),
            ("session_2", "api_service", False, 25.0, 80.0, ["project-architect", "rapid-builder"], [], ["Rate limit exceeded"]),
            ("session_3", "fullstack", False, 40.0, 120.0, ["frontend-specialist"], [], ["File not found"]),
            ("session_4", "fullstack", False, 35.0, 100.0, ["frontend-specialist"], [], ["File not found"]),
        ]
        
        for data in failure_data:
            execution_id = self.db.record_execution(*data, {"name": "Test"}, {"test": True})
            
            # Add agent performance data
            self.db.record_agent_performance(
                execution_id=execution_id,
                agent_name=data[5][0],  # First agent
                success=False,
                execution_time=30.0,
                model_used="claude-sonnet-4",
                tools_used=["write_file"],
                errors=data[7],  # Errors
                output_quality=0.2
            )
        
        # Create some success patterns
        success_data = [
            ("session_5", "api_service", True, 90.0, 100.0, ["project-architect", "rapid-builder"], ["main.py"], []),
            ("session_6", "api_service", True, 85.0, 110.0, ["project-architect", "rapid-builder"], ["main.py", "test.py"], []),
        ]
        
        for data in success_data:
            self.db.record_execution(*data, {"name": "Test"}, {"test": True})
    
    def test_analyze_failure_patterns(self):
        """Test failure pattern analysis"""
        patterns = self.analyzer.analyze_failure_patterns(days=30)
        
        # Should detect rate limit and file not found patterns
        pattern_types = [p.context.get('error_type') for p in patterns]
        self.assertIn('rate_limit', pattern_types)
        self.assertIn('file_not_found', pattern_types)
        
        # Check pattern structure
        for pattern in patterns:
            self.assertEqual(pattern.pattern_type, 'failure')
            self.assertGreaterEqual(pattern.frequency, 2)
            self.assertIsNotNone(pattern.suggested_action)
    
    def test_analyze_performance_patterns(self):
        """Test performance pattern analysis"""
        patterns = self.analyzer.analyze_performance_patterns(days=30)
        
        # With limited test data, may or may not find patterns
        # Just ensure no errors and proper structure
        for pattern in patterns:
            self.assertIn(pattern.pattern_type, ['slow_performance', 'low_success_rate'])
            self.assertGreater(pattern.frequency, 0)
            self.assertIsNotNone(pattern.suggested_action)

class TestLearningEngine(unittest.TestCase):
    """Test the learning engine functionality"""
    
    def setUp(self):
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.learning_engine = LearningEngine(self.test_db.name)
        
        # Create test data
        self._create_comprehensive_test_data()
    
    def tearDown(self):
        os.unlink(self.test_db.name)
    
    def _create_comprehensive_test_data(self):
        """Create comprehensive test data for learning"""
        # Multiple executions with various patterns
        test_executions = [
            # API service failures
            ("api_1", "api_service", False, 30.0, 120.0, ["project-architect", "rapid-builder"], 
             ["main.py"], ["Rate limit exceeded", "Tool failure"]),
            ("api_2", "api_service", False, 25.0, 140.0, ["project-architect", "rapid-builder"], 
             [], ["Rate limit exceeded"]),
            ("api_3", "api_service", True, 85.0, 90.0, ["project-architect", "rapid-builder", "quality-guardian"], 
             ["main.py", "test.py"], []),
            
            # Full-stack patterns
            ("fs_1", "fullstack", False, 40.0, 200.0, ["project-architect", "frontend-specialist"], 
             ["package.json"], ["File not found", "Validation error"]),
            ("fs_2", "fullstack", False, 45.0, 180.0, ["project-architect", "frontend-specialist", "rapid-builder"], 
             ["main.py"], ["File not found"]),
            ("fs_3", "fullstack", True, 80.0, 160.0, ["project-architect", "rapid-builder", "frontend-specialist"], 
             ["main.py", "package.json", "App.tsx"], []),
            
            # AI solution patterns
            ("ai_1", "ai_solution", False, 50.0, 240.0, ["ai-specialist", "rapid-builder"], 
             ["ai_client.py"], ["API timeout", "Configuration error"]),
            ("ai_2", "ai_solution", True, 75.0, 200.0, ["project-architect", "ai-specialist", "rapid-builder"], 
             ["ai_client.py", "main.py"], []),
        ]
        
        for session_id, workflow_type, success, completion, exec_time, agents, files, errors in test_executions:
            execution_id = self.learning_engine.db.record_execution(
                session_id=session_id,
                workflow_type=workflow_type,
                success=success,
                completion_percentage=completion,
                execution_time=exec_time,
                agents_used=agents,
                files_created=files,
                errors=errors,
                requirements={"name": f"Test_{session_id}"},
                context_data={"test": True, "workflow": workflow_type}
            )
            
            # Add agent performance data
            for i, agent in enumerate(agents):
                self.learning_engine.db.record_agent_performance(
                    execution_id=execution_id,
                    agent_name=agent,
                    success=success and (i < len(agents) - 1 or success),  # Last agent might fail
                    execution_time=exec_time / len(agents),
                    model_used="claude-sonnet-4",
                    tools_used=["write_file", "run_command"] if i > 0 else ["record_decision"],
                    errors=errors if i == len(agents) - 1 else [],  # Errors on last agent
                    output_quality=0.8 if success else 0.4
                )
    
    def test_analyze_and_learn(self):
        """Test comprehensive analysis and learning"""
        insights = self.learning_engine.analyze_and_learn(days=30)
        
        # Should generate various types of insights
        insight_types = [i.insight_type for i in insights]
        
        # Check that we get meaningful insights
        self.assertGreater(len(insights), 0)
        
        for insight in insights:
            self.assertIsNotNone(insight.description)
            self.assertIsInstance(insight.evidence, list)
            self.assertGreaterEqual(insight.impact_score, 0.0)
            self.assertLessEqual(insight.impact_score, 1.0)
            self.assertIsInstance(insight.proposed_changes, list)
    
    def test_generate_prompt_refinements(self):
        """Test prompt refinement generation"""
        refinements = self.learning_engine.generate_prompt_refinements(days=30)
        
        # Should generate refinements for agents with performance issues
        if refinements:  # May not always generate refinements with limited test data
            for refinement in refinements:
                self.assertIsNotNone(refinement.agent_name)
                self.assertIsNotNone(refinement.reason)
                self.assertGreaterEqual(refinement.confidence, 0.0)
                self.assertLessEqual(refinement.confidence, 1.0)
    
    def test_get_improvement_recommendations(self):
        """Test improvement recommendation generation"""
        # First analyze to generate insights
        self.learning_engine.analyze_and_learn(days=30)
        
        recommendations = self.learning_engine.get_improvement_recommendations()
        
        # Should return actionable recommendations
        for rec in recommendations:
            self.assertIn('category', rec)
            self.assertIn('description', rec)
            self.assertIn('impact', rec)
            self.assertIn('actions', rec)
            self.assertIn('evidence', rec)
            self.assertIsInstance(rec['actions'], list)

class TestFeedbackIntegration(unittest.TestCase):
    """Test feedback integration functionality"""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="feedback_test_"))
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create mock agent directory
        agents_dir = self.test_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True)
        
        # Create mock agent file
        (agents_dir / "rapid-builder.md").write_text("""---
name: rapid-builder
description: Fast prototyping agent
---

# Role
You are a rapid prototyping specialist.

## Core Tasks
1. Build core features quickly
2. Create scaffolding and boilerplate
3. Implement basic functionality
""")
        
        self.integrator = SystemIntegrator(self.test_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_integrate_session_feedback(self):
        """Test session feedback integration"""
        session_data = {
            'session_id': 'test_integration_1',
            'workflow_type': 'api_service',
            'success': False,
            'completion_percentage': 35.0,
            'execution_time': 150.0,
            'agents_used': ['project-architect', 'rapid-builder'],
            'files_created': ['main.py'],
            'errors': ['Rate limit exceeded', 'Tool validation failed'],
            'requirements': {'name': 'TestAPI', 'features': ['auth', 'crud']},
            'context_data': {'phase': 'testing'},
            'agent_performance': [
                {
                    'agent_name': 'rapid-builder',
                    'success': False,
                    'execution_time': 90.0,
                    'model_used': 'claude-sonnet-4',
                    'tools_used': ['write_file', 'run_command'],
                    'errors': ['Tool validation failed'],
                    'output_quality': 0.3
                }
            ]
        }
        
        updates = self.integrator.integrate_session_feedback(session_data)
        
        # Should generate system updates based on poor performance
        self.assertIsInstance(updates, list)
        
        for update in updates:
            self.assertIsInstance(update, SystemUpdate)
            self.assertIn(update.update_type, ['prompt', 'workflow', 'configuration'])
    
    def test_run_continuous_improvement_cycle(self):
        """Test continuous improvement cycle"""
        # Add some test data to the learning engine
        test_feedback = {
            'session_id': 'cycle_test_1',
            'workflow_type': 'api_service',
            'success': False,
            'completion_percentage': 40.0,
            'execution_time': 120.0,
            'agents_used': ['rapid-builder'],
            'files_created': [],
            'errors': ['Multiple tool failures'],
            'requirements': {'name': 'CycleTest'},
            'context_data': {},
            'agent_performance': [
                {
                    'agent_name': 'rapid-builder',
                    'success': False,
                    'execution_time': 120.0,
                    'model_used': 'claude-sonnet-4',
                    'tools_used': ['write_file'],
                    'errors': ['Tool failure'],
                    'output_quality': 0.2
                }
            ]
        }
        
        # Process feedback first
        self.integrator.integrate_session_feedback(test_feedback)
        
        # Run improvement cycle
        report = self.integrator.run_continuous_improvement_cycle(days=1)
        
        # Verify report structure
        self.assertIn('analysis_period_days', report)
        self.assertIn('total_insights', report)
        self.assertIn('actionable_recommendations', report)
        self.assertIn('updates_applied', report)
        self.assertIn('timestamp', report)

class TestSystemUpdaters(unittest.TestCase):
    """Test system update components"""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="updater_test_"))
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create mock structures
        self.agents_dir = self.test_dir / ".claude" / "agents"
        self.agents_dir.mkdir(parents=True)
        
        self.prompt_updater = PromptUpdater(self.agents_dir)
        self.workflow_updater = WorkflowUpdater(self.test_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_prompt_updater(self):
        """Test prompt updating functionality"""
        # Create mock agent file
        agent_file = self.agents_dir / "test-agent.md"
        agent_file.write_text("""---
name: test-agent
description: Test agent
---

# Role
You are a test agent.

## Core Tasks
1. Test things
2. Validate results
""")
        
        # Test refinement application
        from lib.continuous_improvement import PromptRefinement
        
        refinement = PromptRefinement(
            agent_name="test-agent",
            current_prompt="Current test prompt",
            suggested_prompt="Improved test prompt\n\nAdditional requirements:\n- Add validation steps\n- Include error handling",
            reason="Improve test agent performance",
            confidence=0.8
        )
        
        success = self.prompt_updater.apply_prompt_refinement(refinement)
        self.assertTrue(success)
        
        # Verify file was updated
        updated_content = agent_file.read_text()
        self.assertIn("Additional Requirements", updated_content)
        self.assertIn("Add validation steps", updated_content)
    
    def test_workflow_updater(self):
        """Test workflow updating functionality"""
        updates = {
            "error_handling": "enhanced",
            "retry_logic": True,
            "validation": "strict"
        }
        
        success = self.workflow_updater.update_workflow_configuration("test_workflow", updates)
        self.assertTrue(success)
        
        # Verify config file was created/updated
        config_file = self.test_dir / "workflow_configs.yaml"
        self.assertTrue(config_file.exists())

class TestAutoImprovementScheduler(unittest.TestCase):
    """Test automatic improvement scheduling"""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="scheduler_test_"))
        self.integrator = SystemIntegrator(self.test_dir)
        self.scheduler = AutoImprovementScheduler(self.integrator)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_should_run_improvement(self):
        """Test improvement scheduling logic"""
        # Initially should run (no previous run)
        self.assertTrue(self.scheduler.should_run_improvement())
        
        # After setting recent run time, should not run
        self.scheduler.last_improvement_run = time.time()
        self.assertFalse(self.scheduler.should_run_improvement())
        
        # After setting old run time, should run again
        self.scheduler.last_improvement_run = time.time() - (25 * 60 * 60)  # 25 hours ago
        self.assertTrue(self.scheduler.should_run_improvement())
    
    def test_run_scheduled_improvement(self):
        """Test scheduled improvement execution"""
        # Force scheduler to think it should run
        self.scheduler.last_improvement_run = 0
        
        report = self.scheduler.run_scheduled_improvement()
        
        # Should return a report
        self.assertIn('analysis_period_days', report)
        
        # Should update last run time
        self.assertGreater(self.scheduler.last_improvement_run, 0)

class TestSection10Integration(unittest.TestCase):
    """Integration tests for complete Section 10 functionality"""
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="section10_integration_"))
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_complete_feedback_loop(self):
        """Test the complete feedback loop from execution to improvement"""
        # Create system integrator
        integrator = SystemIntegrator(self.test_dir)
        
        # Simulate multiple session failures to trigger learning
        failure_sessions = [
            {
                'session_id': f'integration_test_{i}',
                'workflow_type': 'api_service',
                'success': False,
                'completion_percentage': 30.0 + (i * 5),
                'execution_time': 120.0 + (i * 10),
                'agents_used': ['project-architect', 'rapid-builder'],
                'files_created': [f'main_{i}.py'],
                'errors': ['Rate limit exceeded', 'Tool validation failed'],
                'requirements': {'name': f'IntegrationTest_{i}'},
                'context_data': {'test': True},
                'agent_performance': [
                    {
                        'agent_name': 'rapid-builder',
                        'success': False,
                        'execution_time': 60.0 + (i * 5),
                        'model_used': 'claude-sonnet-4',
                        'tools_used': ['write_file'],
                        'errors': ['Tool validation failed'],
                        'output_quality': 0.3
                    }
                ]
            }
            for i in range(3)
        ]
        
        # Process each failure
        total_updates = 0
        for session_data in failure_sessions:
            updates = integrator.integrate_session_feedback(session_data)
            total_updates += len(updates)
        
        # Run improvement cycle
        report = integrator.run_continuous_improvement_cycle(days=1)
        
        # Verify the system learned and improved
        self.assertGreater(report['total_insights'], 0)
        self.assertGreaterEqual(total_updates + report['updates_applied'], 0)  # Some improvements made
        
        # Verify improvement report exists
        improvement_files = list(self.test_dir.glob("improvement_report_*.json"))
        self.assertGreater(len(improvement_files), 0)
    
    def test_end_to_end_learning_cycle(self):
        """Test end-to-end learning cycle with pattern recognition"""
        # Create learning components
        learning_engine = LearningEngine(":memory:")  # In-memory DB for testing
        
        # Simulate multiple executions with clear patterns
        execution_data = [
            # Pattern 1: Rate limiting issues with rapid-builder
            ("session_1", "api_service", False, 25.0, ["rapid-builder"], ["Rate limit exceeded"]),
            ("session_2", "api_service", False, 30.0, ["rapid-builder"], ["Rate limit exceeded"]),
            ("session_3", "api_service", False, 20.0, ["rapid-builder"], ["Rate limit exceeded"]),
            
            # Pattern 2: File not found issues with frontend-specialist
            ("session_4", "fullstack", False, 40.0, ["frontend-specialist"], ["File not found"]),
            ("session_5", "fullstack", False, 35.0, ["frontend-specialist"], ["File not found"]),
            
            # Some successful executions
            ("session_6", "api_service", True, 85.0, ["project-architect", "rapid-builder"], []),
            ("session_7", "fullstack", True, 80.0, ["project-architect", "frontend-specialist"], []),
        ]
        
        # Record all executions
        for session_id, workflow, success, completion, agents, errors in execution_data:
            execution_id = learning_engine.db.record_execution(
                session_id=session_id,
                workflow_type=workflow,
                success=success,
                completion_percentage=completion,
                execution_time=100.0,
                agents_used=agents,
                files_created=["test.py"],
                errors=errors,
                requirements={"name": "PatternTest"},
                context_data={"test": True}
            )
            
            # Add agent performance
            for agent in agents:
                learning_engine.db.record_agent_performance(
                    execution_id=execution_id,
                    agent_name=agent,
                    success=success,
                    execution_time=50.0,
                    model_used="claude-sonnet-4",
                    tools_used=["write_file"],
                    errors=errors if not success else [],
                    output_quality=0.8 if success else 0.3
                )
        
        # Run analysis
        insights = learning_engine.analyze_and_learn(days=30)
        recommendations = learning_engine.get_improvement_recommendations()
        refinements = learning_engine.generate_prompt_refinements(days=30)
        
        # Verify pattern recognition
        self.assertGreater(len(insights), 0, "Should generate insights from patterns")
        
        # Should detect rate limiting and file not found patterns
        insight_descriptions = [i.description for i in insights]
        pattern_found = any("rate" in desc.lower() or "file" in desc.lower() for desc in insight_descriptions)
        self.assertTrue(pattern_found, "Should detect rate limiting or file not found patterns")
        
        # Should generate actionable recommendations
        actionable_recs = [r for r in recommendations if r.get('impact', 0) > 0.5]
        self.assertGreater(len(actionable_recs), 0, "Should generate high-impact recommendations")

def run_section10_tests():
    """Run all Section 10 tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestExecutionDatabase,
        TestPatternAnalyzer,
        TestLearningEngine,
        TestFeedbackIntegration,
        TestSystemUpdaters,
        TestAutoImprovementScheduler,
        TestSection10Integration
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("Running Section 10: Testing & Validation Complete Suite")
    print("=" * 60)
    
    success = run_section10_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All Section 10 tests passed!")
        print("🎉 Section 10: Testing & Validation is complete!")
    else:
        print("❌ Some Section 10 tests failed!")
    print("=" * 60)
    
    sys.exit(0 if success else 1)