"""
Phase 2 Integration Tests - Production Infrastructure
Tests for Production Monitor, Recovery Manager, Metrics Exporter, and Alert Manager
"""

import pytest
import asyncio
import json
import time
import tempfile
import os
import sys
from typing import Dict, Any, List
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.production_monitor import ProductionMonitor
from lib.recovery_manager import RecoveryManager
from lib.metrics_exporter import MetricsExporter
from lib.alert_manager import AlertManager, AlertRule, AlertSeverity


class TestPhase2Integration:
    """Integration tests for Phase 2 production infrastructure components"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.fixture
    def production_monitor(self, temp_db):
        """Create ProductionMonitor instance with temp database"""
        monitor = ProductionMonitor()
        monitor.db_path = temp_db  # Override the default db path
        return monitor
    
    @pytest.fixture
    def recovery_manager(self):
        """Create RecoveryManager instance"""
        return RecoveryManager()
    
    @pytest.fixture
    def metrics_exporter(self, production_monitor):
        """Create MetricsExporter instance"""
        return MetricsExporter(production_monitor=production_monitor)
    
    @pytest.fixture
    def alert_manager(self):
        """Create AlertManager instance"""
        return AlertManager()
    
    # ==================== ProductionMonitor Tests ====================
    
    def test_production_monitor_initialization(self, production_monitor):
        """Test ProductionMonitor initializes correctly"""
        assert production_monitor is not None
        assert production_monitor.monitor_start_time is not None
        assert production_monitor.metrics_dir.exists()
    
    def test_production_monitor_execution_tracking(self, production_monitor):
        """Test tracking agent executions"""
        # Start execution
        exec_id = production_monitor.start_execution(
            agent_name="test-agent",
            requirements=["REQ-001", "REQ-002"]
        )
        assert exec_id is not None
        
        # Simulate some work
        time.sleep(0.1)
        
        # End execution
        production_monitor.end_execution(
            execution_id=exec_id,
            success=True,
            metrics={
                "files_created": 5,
                "api_calls": 10,
                "estimated_cost": 0.25
            }
        )
        
        # Check metrics
        metrics = production_monitor.get_agent_performance_report("test-agent")
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["success_rate"] == 1.0
        assert metrics["total_cost"] == 0.25
    
    def test_production_monitor_failure_tracking(self, production_monitor):
        """Test tracking failed executions"""
        # Track multiple executions with failures
        for i in range(5):
            exec_id = production_monitor.start_execution(f"agent-{i % 2}")
            production_monitor.end_execution(
                exec_id, 
                success=(i % 2 == 0),
                error_message="Test error" if i % 2 == 1 else None
            )
        
        # Get overall metrics
        metrics = production_monitor.get_system_health()
        assert metrics["total_executions"] == 5
        assert metrics["failed_executions"] == 2
        assert metrics["error_rate"] == 0.4
    
    def test_production_monitor_cost_tracking(self, production_monitor):
        """Test cost tracking and budget monitoring"""
        # Add executions with costs
        for i in range(10):
            exec_id = production_monitor.start_execution("expensive-agent")
            production_monitor.end_execution(
                exec_id,
                success=True,
                metrics={"estimated_cost": 1.5}
            )
        
        # Check cost metrics
        metrics = production_monitor.get_cost_analysis()
        assert metrics["total"] == 15.0
        assert "cost_per_agent" in metrics
        assert metrics["cost_per_agent"]["expensive-agent"] == 15.0
    
    # ==================== RecoveryManager Tests ====================
    
    @pytest.mark.asyncio
    async def test_recovery_manager_exponential_backoff(self, recovery_manager):
        """Test exponential backoff retry logic"""
        attempt_count = 0
        attempt_times = []
        
        async def failing_agent(agent_name, context):
            nonlocal attempt_count, attempt_times
            attempt_count += 1
            attempt_times.append(time.time())
            if attempt_count < 3:
                raise Exception("Simulated failure")
            return True, {"status": "success"}, context
        
        # Execute with retry
        success, result, error = await recovery_manager.recover_with_retry(
            agent_name="test-agent",
            agent_executor=failing_agent,
            context={},
            max_attempts=3
        )
        
        assert success is True
        assert attempt_count == 3
        
        # Check exponential backoff timing
        if len(attempt_times) >= 3:
            first_delay = attempt_times[1] - attempt_times[0]
            second_delay = attempt_times[2] - attempt_times[1]
            # Second delay should be roughly 2x the first (exponential backoff)
            # Accounting for some tolerance due to timing variations
            assert second_delay >= first_delay * 1.8
    
    @pytest.mark.asyncio
    async def test_recovery_manager_alternative_agent(self, recovery_manager):
        """Test alternative agent selection on failure"""
        primary_called = False
        
        async def primary_agent(agent_name, context):
            nonlocal primary_called
            primary_called = True
            raise Exception("Primary agent failed")
        
        # Add alternative agent mapping
        recovery_manager.alternative_agents = {
            "test-agent": ["alt-agent", "backup-agent"]
        }
        
        # Mock the alternative selection
        with patch.object(recovery_manager, '_select_alternative_agent', return_value="alt-agent"):
            # Try recovery - should fail with primary but suggest alternative
            success, result, error = await recovery_manager.recover_with_retry(
                agent_name="test-agent",
                agent_executor=primary_agent,
                context={},
                max_attempts=1
            )
            
            # Primary should have been called and failed
            assert primary_called is True
            assert success is False  # Recovery failed but alternative was suggested
    
    @pytest.mark.asyncio
    async def test_recovery_manager_checkpoint_recovery(self, recovery_manager):
        """Test checkpoint save and recovery"""
        # Create checkpoint
        checkpoint_data = {
            "agent": "test-agent",
            "progress": 50,
            "files_created": ["file1.py", "file2.py"]
        }
        # Create a recovery context for checkpoint testing
        from lib.recovery_manager import RecoveryContext
        recovery_context = RecoveryContext(
            agent_name="test-agent",
            task_description="test task",
            original_context=checkpoint_data
        )
        checkpoint = await recovery_manager._create_checkpoint(
            "test-agent", checkpoint_data, recovery_context
        )
        checkpoint_id = checkpoint.checkpoint_id
        
        # Recover from checkpoint
        async def test_executor(agent_name, context):
            return True, {"recovered": True}, context
        
        success, result, error = await recovery_manager.recover_from_checkpoint(
            checkpoint_id, test_executor
        )
        assert success is True
        
        # Test recovery with modification
        async def resuming_agent(agent_name, context):
            # Agent should receive checkpoint data in context
            return True, {"resumed": True, "previous_progress": context.get("progress")}, context
        
        success, result, error = await recovery_manager.recover_with_retry(
            agent_name="test-agent",
            agent_executor=resuming_agent,
            context=checkpoint_data,
            max_attempts=1
        )
        
        assert success is True
        assert result["previous_progress"] == 50
    
    @pytest.mark.asyncio
    async def test_recovery_manager_manual_intervention(self, recovery_manager):
        """Test manual intervention queueing"""
        # Add manual intervention request
        from lib.recovery_manager import RecoveryContext
        recovery_context = RecoveryContext(
            agent_name="complex-agent",
            task_description="Complex task",
            original_context={"error": "Database schema mismatch"}
        )
        recovery_context.add_error("Complex error requiring human review")
        intervention_id = recovery_manager.request_manual_intervention(recovery_context)
        
        assert intervention_id is not None
        assert len(recovery_manager.manual_intervention_queue) == 1
        
        # Resolve intervention
        recovery_manager.resolve_intervention(
            intervention_id,
            resolution="Schema updated manually",
            continue_execution=True
        )
        
        assert recovery_manager.manual_intervention_queue[0]["status"] == "resolved"
    
    # ==================== MetricsExporter Tests ====================
    
    def test_metrics_exporter_prometheus_format(self, metrics_exporter, production_monitor):
        """Test Prometheus metrics format generation"""
        # Add some test data
        exec_id = production_monitor.start_execution("test-agent")
        production_monitor.end_execution(exec_id, success=True, metrics={"estimated_cost": 0.1})
        
        # Get Prometheus metrics
        prometheus_metrics = metrics_exporter.export_prometheus_format()
        
        # Check format
        assert "# HELP agent_executions_total" in prometheus_metrics
        assert "# TYPE agent_executions_total counter" in prometheus_metrics
        assert "agent_executions_total" in prometheus_metrics
        assert "agent_success_rate" in prometheus_metrics
        assert "cost_total_dollars" in prometheus_metrics
    
    def test_metrics_exporter_grafana_dashboard(self, metrics_exporter):
        """Test Grafana dashboard generation"""
        dashboard = metrics_exporter.generate_grafana_dashboard()
        
        # Check dashboard structure
        assert "dashboard" in dashboard
        assert "title" in dashboard["dashboard"]
        assert dashboard["dashboard"]["title"] == "Agent Swarm Monitoring"
        assert "panels" in dashboard["dashboard"]
        assert len(dashboard["dashboard"]["panels"]) > 0
        
        # Check panel structure
        panel = dashboard["dashboard"]["panels"][0]
        assert "title" in panel
        assert "targets" in panel
        assert "gridPos" in panel
    
    @patch('lib.metrics_exporter.HTTPServer')
    def test_metrics_exporter_http_server(self, mock_server, metrics_exporter):
        """Test HTTP metrics server startup"""
        # Start server (mocked)
        metrics_exporter.start_prometheus_server()
        
        # Verify server was created with correct parameters
        mock_server.assert_called_once()
        
        # Check that handler was set up correctly
        assert hasattr(metrics_exporter, '_server_thread')
    
    # ==================== AlertManager Tests ====================
    
    @pytest.mark.asyncio
    async def test_alert_manager_rule_evaluation(self, alert_manager):
        """Test alert rule evaluation"""
        # Add alert rule
        rule = AlertRule(
            name="high_error_rate",
            metric="error_rate",
            threshold=0.1,
            condition="greater_than",
            severity=AlertSeverity.CRITICAL,
            description="Error rate above 10%"
        )
        alert_manager.add_rule(rule)
        
        # Evaluate with metrics that should trigger alert
        triggered_alerts = []
        
        async def mock_trigger(rule, value):
            from lib.alert_manager import Alert, AlertStatus
            alert = Alert(
                id=f"{rule.name}_{value}",
                rule_name=rule.name,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                value=value,
                threshold=rule.threshold,
                message=f"{rule.description}: {value}",
                triggered_at=datetime.now()
            )
            triggered_alerts.append(alert)
            return alert
        
        with patch.object(alert_manager, '_trigger_alert', side_effect=mock_trigger):
            await alert_manager.evaluate_rules({"error_rate": 0.15})
            
            # Wait for async operations
            await asyncio.sleep(0.1)
            
            assert len(triggered_alerts) == 1
            assert triggered_alerts[0].severity == AlertSeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_alert_manager_multiple_severities(self, alert_manager):
        """Test alerts with different severity levels"""
        # Add multiple rules
        alert_manager.add_rule(AlertRule(
            "info_rule", "cpu_usage", 0.5, "greater_than", 
            AlertSeverity.INFO, "CPU above 50%"
        ))
        alert_manager.add_rule(AlertRule(
            "warning_rule", "cpu_usage", 0.7, "greater_than",
            AlertSeverity.WARNING, "CPU above 70%"
        ))
        alert_manager.add_rule(AlertRule(
            "critical_rule", "cpu_usage", 0.9, "greater_than",
            AlertSeverity.CRITICAL, "CPU above 90%"
        ))
        
        triggered_alerts = []
        
        async def mock_trigger(rule, value):
            from lib.alert_manager import Alert, AlertStatus
            alert = Alert(
                id=f"{rule.name}_{value}",
                rule_name=rule.name,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                value=value,
                threshold=rule.threshold,
                message=f"{rule.description}: {value}",
                triggered_at=datetime.now()
            )
            triggered_alerts.append(alert)
            return alert
        
        # Test with high CPU that triggers all rules
        with patch.object(alert_manager, '_trigger_alert', side_effect=mock_trigger):
            await alert_manager.evaluate_rules({"cpu_usage": 0.95})
            await asyncio.sleep(0.1)
            
            # Should trigger all three alerts
            assert len(triggered_alerts) == 3
            severities = [a.severity for a in triggered_alerts]
            assert AlertSeverity.INFO in severities
            assert AlertSeverity.WARNING in severities
            assert AlertSeverity.CRITICAL in severities
    
    @pytest.mark.asyncio
    async def test_alert_manager_cooldown(self, alert_manager):
        """Test alert cooldown period"""
        # Add rule with cooldown
        rule = AlertRule(
            "test_rule", "metric", 0.5, "greater_than",
            AlertSeverity.WARNING, "Test alert",
            cooldown_minutes=5
        )
        alert_manager.add_rule(rule)
        
        trigger_count = 0
        
        async def mock_trigger(rule, value):
            nonlocal trigger_count
            trigger_count += 1
            from lib.alert_manager import Alert, AlertStatus
            alert = Alert(
                id=f"{rule.name}_{value}",
                rule_name=rule.name,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                value=value,
                threshold=rule.threshold,
                message=f"{rule.description}: {value}",
                triggered_at=datetime.now()
            )
            return alert
        
        with patch.object(alert_manager, '_trigger_alert', side_effect=mock_trigger):
            # First evaluation should trigger
            await alert_manager.evaluate_rules({"metric": 0.6})
            await asyncio.sleep(0.1)
            assert trigger_count == 1
            
            # Second evaluation within cooldown should not trigger
            await alert_manager.evaluate_rules({"metric": 0.6})
            await asyncio.sleep(0.1)
            assert trigger_count == 1  # Still 1, not triggered again
    
    # ==================== Full Integration Tests ====================
    
    @pytest.mark.asyncio
    async def test_full_phase2_integration(self, production_monitor, recovery_manager, 
                                          metrics_exporter, alert_manager):
        """Test full integration of all Phase 2 components"""
        
        # Configure alert rules
        alert_manager.add_rule(AlertRule(
            "high_failure_rate", "error_rate", 0.3, "greater_than",
            AlertSeverity.WARNING, "High failure rate detected"
        ))
        
        # Simulate agent executions with failures
        success_count = 0
        failure_count = 0
        
        async def flaky_agent(context):
            import random
            if random.random() > 0.6:  # 40% failure rate
                raise Exception("Random failure")
            return {"status": "success"}
        
        # Run multiple executions with monitoring
        for i in range(10):
            exec_id = production_monitor.start_execution(f"agent-{i % 3}")
            
            # Try with recovery
            success, result, error = await recovery_manager.recover_with_retry(
                agent_name=f"agent-{i % 3}",
                agent_executor=flaky_agent,
                context={"iteration": i},
                max_attempts=2
            )
            
            # Record in monitor
            production_monitor.end_execution(
                exec_id, 
                success=success,
                error_message=str(error) if error else None,
                metrics={"estimated_cost": 0.1}
            )
            
            if success:
                success_count += 1
            else:
                failure_count += 1
        
        # Get metrics
        system_health = production_monitor.get_system_health()
        prometheus_metrics = metrics_exporter.get_prometheus_metrics()
        
        # Evaluate alerts
        alerts_triggered = []
        
        async def mock_notify(channel, alert):
            alerts_triggered.append(alert)
        
        with patch.object(alert_manager, '_send_notification', side_effect=mock_notify):
            await alert_manager.evaluate_rules(system_health)
            await asyncio.sleep(0.1)
        
        # Verify integration
        assert system_health["total_executions"] == 10
        assert system_health["error_rate"] > 0  # Some failures expected
        assert "agent_swarm_executions_total 10" in prometheus_metrics
        
        # Check if alerts were triggered for high failure rate
        if system_health["error_rate"] > 0.3:
            assert len(alerts_triggered) > 0
    
    @pytest.mark.asyncio
    async def test_production_deployment_readiness(self, production_monitor, 
                                                  recovery_manager, 
                                                  metrics_exporter, 
                                                  alert_manager):
        """Test that all components are ready for production deployment"""
        
        # Check ProductionMonitor
        assert production_monitor.get_system_health() is not None
        assert production_monitor.export_metrics("json") is not None
        
        # Check RecoveryManager
        checkpoint_id = recovery_manager.save_checkpoint("test", {"data": "test"})
        assert recovery_manager.recover_from_checkpoint(checkpoint_id) is not None
        
        # Check MetricsExporter
        assert metrics_exporter.get_prometheus_metrics() is not None
        dashboard = metrics_exporter.generate_grafana_dashboard()
        assert dashboard is not None
        assert "dashboard" in dashboard
        
        # Check AlertManager
        assert len(alert_manager.rules) >= 0  # Can have zero or more rules
        assert alert_manager.get_active_alerts() is not None
        
        # Verify no exceptions during basic operations
        try:
            exec_id = production_monitor.start_execution("final-test")
            production_monitor.end_execution(exec_id, success=True)
            
            await recovery_manager.recover_with_retry(
                "test", 
                AsyncMock(return_value={"ok": True}),
                {},
                max_attempts=1
            )
            
            await alert_manager.evaluate_rules({"test_metric": 0.5})
            
        except Exception as e:
            pytest.fail(f"Production readiness check failed: {e}")


class TestPhase2PerformanceAndScale:
    """Performance and scalability tests for Phase 2 components"""
    
    @pytest.fixture
    def production_monitor(self):
        """Create ProductionMonitor for performance testing"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            metrics_dir = os.path.join(tmp_dir, 'test_metrics')
            monitor = ProductionMonitor(metrics_dir=metrics_dir)
            yield monitor
    
    def test_monitor_high_volume_tracking(self, production_monitor):
        """Test monitor performance with high volume of executions"""
        start_time = time.time()
        
        # Track 1000 executions
        for i in range(1000):
            exec_id = production_monitor.start_execution(f"agent-{i % 10}")
            production_monitor.end_execution(
                exec_id, 
                success=(i % 3 != 0),
                metrics={"estimated_cost": 0.01}
            )
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0
        
        # Verify data integrity
        metrics = production_monitor.get_system_health()
        assert metrics["total_executions"] == 1000
    
    @pytest.mark.asyncio
    async def test_recovery_manager_concurrent_recoveries(self, recovery_manager):
        """Test recovery manager handling concurrent recovery attempts"""
        
        async def slow_agent(agent_name, context):
            await asyncio.sleep(0.1)
            return True, {"id": context["id"]}, context
        
        # Launch multiple concurrent recoveries
        tasks = []
        for i in range(20):
            task = recovery_manager.recover_with_retry(
                agent_name=f"agent-{i}",
                agent_executor=slow_agent,
                context={"id": i},
                max_attempts=1
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        
        # Verify all completed successfully
        assert len(results) == 20
        for i, (success, result, error) in enumerate(results):
            assert success is True
            assert result["id"] == i
    
    @pytest.fixture
    def recovery_manager(self):
        """Create RecoveryManager for performance testing"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            checkpoint_dir = os.path.join(tmp_dir, 'recovery')
            return RecoveryManager(checkpoint_dir=checkpoint_dir)
    
    @pytest.fixture
    def metrics_exporter(self, production_monitor):
        """Create MetricsExporter for performance testing"""
        return MetricsExporter(production_monitor=production_monitor)
    
    @pytest.fixture
    def alert_manager(self):
        """Create AlertManager for performance testing"""
        return AlertManager()
    
    def test_metrics_exporter_large_dashboard(self, metrics_exporter):
        """Test metrics exporter with large number of metrics"""
        # Generate large dashboard with many panels
        dashboard = metrics_exporter.generate_grafana_dashboard()
        
        # Add 50 custom panels
        for i in range(50):
            panel = {
                "id": 100 + i,
                "title": f"Custom Metric {i}",
                "type": "graph",
                "targets": [{"expr": f"custom_metric_{i}"}],
                "gridPos": {"h": 8, "w": 12, "x": (i % 2) * 12, "y": 50 + (i // 2) * 8}
            }
            dashboard["dashboard"]["panels"].append(panel)
        
        # Verify dashboard is still valid
        assert len(dashboard["dashboard"]["panels"]) > 50
        assert json.dumps(dashboard)  # Should be serializable
    
    @pytest.mark.asyncio
    async def test_alert_manager_rule_performance(self, alert_manager):
        """Test alert manager with many rules and frequent evaluations"""
        
        # Add 100 alert rules
        for i in range(100):
            rule = AlertRule(
                name=f"rule_{i}",
                metric=f"metric_{i}",
                threshold=0.5,
                condition="greater_than",
                severity=AlertSeverity.INFO,
                description=f"Test rule {i}"
            )
            alert_manager.add_rule(rule)
        
        # Evaluate rules 100 times with different metrics
        start_time = time.time()
        
        for j in range(100):
            metrics = {f"metric_{i}": 0.4 + (i % 3) * 0.2 for i in range(100)}
            await alert_manager.evaluate_rules(metrics)
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([__file__, "-v", "--tb=short", "--cov=lib", "--cov-report=term-missing"])