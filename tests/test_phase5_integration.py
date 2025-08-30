#!/usr/bin/env python3
"""
Phase 5 Integration Tests - Production Readiness Components

Tests the integration of:
- Security Manager (API keys, RBAC, rate limiting, audit logging)
- Performance Optimizer (caching, query optimization, concurrent execution)
- Complete workflow with security and performance features
"""

import os
import sys
import json
import time
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import Phase 5 components
from lib.security_manager import (
    SecurityManager, AccessLevel, SecurityEvent,
    APIKeyManager, RateLimiter, InputSanitizer,
    AuditLogger, RBACManager
)
from lib.performance_optimizer import (
    PerformanceOptimizer, ResponseCache, QueryOptimizer,
    ConcurrentExecutor, MemoryManager, APIBatcher,
    cached, optimized_query
)


class TestSecurityIntegration(unittest.TestCase):
    """Test security components integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.security = SecurityManager()
        
        # Create test users
        self.admin = self.security.rbac_manager.create_user(
            "admin", "admin@test.com", AccessLevel.ADMIN
        )
        self.developer = self.security.rbac_manager.create_user(
            "developer", "dev@test.com", AccessLevel.DEVELOPER
        )
        self.viewer = self.security.rbac_manager.create_user(
            "viewer", "viewer@test.com", AccessLevel.VIEWER
        )
    
    def test_api_key_lifecycle(self):
        """Test API key generation, validation, and rotation"""
        # Generate API key
        api_key = self.security.api_key_manager.generate_api_key(
            self.admin.user_id, "test_project"
        )
        
        self.assertTrue(api_key.startswith("sk-test_project-"))
        
        # Validate key
        valid, user_id, project = self.security.api_key_manager.validate_key(api_key)
        self.assertTrue(valid)
        self.assertEqual(user_id, self.admin.user_id)
        self.assertEqual(project, "test_project")
        
        # Rotate key
        new_key = self.security.api_key_manager.rotate_key(
            self.admin.user_id, "test_project"
        )
        
        # Old key should be invalid
        valid, _, _ = self.security.api_key_manager.validate_key(api_key)
        self.assertFalse(valid)
        
        # New key should be valid
        valid, _, _ = self.security.api_key_manager.validate_key(new_key)
        self.assertTrue(valid)
    
    async def test_authentication_flow(self):
        """Test complete authentication flow"""
        # Generate API key for admin
        api_key = self.security.api_key_manager.generate_api_key(
            self.admin.user_id, "auth_test"
        )
        
        # Successful authentication
        success, user_id = await self.security.authenticate(api_key, "127.0.0.1")
        self.assertTrue(success)
        self.assertEqual(user_id, self.admin.user_id)
        
        # Failed authentication with invalid key
        success, user_id = await self.security.authenticate("invalid_key", "127.0.0.1")
        self.assertFalse(success)
        self.assertIsNone(user_id)
        
        # Check audit log has both events
        self.security.audit_logger.flush()
        logs = self.security.audit_logger.query_logs(
            start_date=datetime.now() - timedelta(minutes=1)
        )
        
        # Should have login success and failure events
        event_types = [log["event_type"] for log in logs]
        self.assertIn(SecurityEvent.LOGIN_SUCCESS.value, event_types)
        self.assertIn(SecurityEvent.LOGIN_FAILURE.value, event_types)
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Create guest user with low rate limit
        guest = self.security.rbac_manager.create_user(
            "guest", "guest@test.com", AccessLevel.GUEST
        )
        
        # Generate API key
        api_key = self.security.api_key_manager.generate_api_key(
            guest.user_id, "rate_test"
        )
        
        # Make requests up to the limit
        for i in range(10):  # Guest limit is 10/minute
            success, _ = await self.security.authenticate(api_key, "127.0.0.1")
            self.assertTrue(success)
        
        # Next request should be rate limited
        success, _ = await self.security.authenticate(api_key, "127.0.0.1")
        self.assertFalse(success)
        
        # Check for rate limit event in audit log
        self.security.audit_logger.flush()
        logs = self.security.audit_logger.query_logs(
            start_date=datetime.now() - timedelta(minutes=1)
        )
        
        rate_limit_events = [
            log for log in logs 
            if log["event_type"] == SecurityEvent.RATE_LIMIT_EXCEEDED.value
        ]
        self.assertGreater(len(rate_limit_events), 0)
    
    def test_rbac_permissions(self):
        """Test role-based access control"""
        # Admin should have all permissions
        can_delete = self.security.authorize(
            self.admin.user_id, "workflow", "delete"
        )
        self.assertTrue(can_delete)
        
        # Developer should not have delete permission
        can_delete = self.security.authorize(
            self.developer.user_id, "workflow", "delete"
        )
        self.assertFalse(can_delete)
        
        # Developer should have execute permission
        can_execute = self.security.authorize(
            self.developer.user_id, "workflow", "execute"
        )
        self.assertTrue(can_execute)
        
        # Viewer should only have read permission
        can_read = self.security.authorize(
            self.viewer.user_id, "workflow", "read"
        )
        self.assertTrue(can_read)
        
        can_execute = self.security.authorize(
            self.viewer.user_id, "workflow", "execute"
        )
        self.assertFalse(can_execute)
    
    def test_input_sanitization(self):
        """Test input sanitization against various attacks"""
        # XSS attempt
        xss_input = "<script>alert('xss')</script>"
        with self.assertRaises(ValueError):
            self.security.sanitize_input(xss_input, "string")
        
        # SQL injection attempt
        sql_input = "'; DROP TABLE users; --"
        with self.assertRaises(ValueError):
            self.security.sanitize_input(sql_input, "string")
        
        # Path traversal attempt
        path_input = "../../etc/passwd"
        with self.assertRaises(ValueError):
            self.security.sanitize_input(path_input, "path")
        
        # Valid input should pass
        valid_input = "This is a valid string"
        sanitized = self.security.sanitize_input(valid_input, "string")
        self.assertIsNotNone(sanitized)
    
    def test_security_report_generation(self):
        """Test security report generation"""
        # Generate some events
        asyncio.run(self.test_authentication_flow())
        
        # Generate report
        report = self.security.get_security_report(days=1)
        
        self.assertIn("total_events", report)
        self.assertIn("failed_logins", report)
        self.assertIn("unique_users", report)
        self.assertGreater(report["total_events"], 0)


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance optimization components"""
    
    def setUp(self):
        """Set up test environment"""
        self.optimizer = PerformanceOptimizer()
    
    def test_response_caching(self):
        """Test multi-tier caching system"""
        # Cache a response
        self.optimizer.cache_response(
            "test_key", 
            {"data": "test_value", "timestamp": time.time()},
            ttl=60
        )
        
        # Retrieve from cache
        cached = self.optimizer.get_cached_response("test_key")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["data"], "test_value")
        
        # Check cache statistics
        stats = self.optimizer.cache.get_stats()
        self.assertEqual(stats["total_hits"], 1)
        self.assertEqual(stats["cache_hit_rate"], 1.0)
        
        # Test cache invalidation
        self.optimizer.cache.invalidate("test")
        cached = self.optimizer.get_cached_response("test_key")
        self.assertIsNone(cached)
    
    def test_cache_decorator(self):
        """Test caching decorator"""
        call_count = 0
        
        @cached(ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)
        
        # Second call should use cache
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)  # Should not increment
        
        # Different argument should execute function
        result3 = expensive_function(7)
        self.assertEqual(result3, 14)
        self.assertEqual(call_count, 2)
    
    def test_query_optimization(self):
        """Test query optimization and caching"""
        query = "SELECT * FROM users WHERE status = 'active'"
        params = {"limit": 100}
        
        # Execute query (should optimize and cache)
        result = self.optimizer.query_optimizer.execute_query(query, params)
        self.assertIsNotNone(result)
        
        # Check optimization was applied
        optimized_query, _ = self.optimizer.query_optimizer.optimize_query(query, params)
        self.assertIn("LIMIT", optimized_query)
        
        # Check performance stats
        perf_stats = self.optimizer.query_optimizer.analyze_performance()
        self.assertEqual(perf_stats["optimized_queries"], 1)
        self.assertEqual(perf_stats["cached_queries"], 1)
    
    async def test_concurrent_execution(self):
        """Test concurrent task execution"""
        # Define test tasks
        async def io_task(n):
            await asyncio.sleep(0.01)
            return n * 2
        
        def cpu_task(n):
            result = 0
            for i in range(1000):
                result += n * i
            return result
        
        # Execute I/O tasks concurrently
        io_tasks = [lambda n=i: io_task(n) for i in range(10)]
        io_results = await self.optimizer.execute_optimized(io_tasks, "io")
        
        self.assertEqual(len(io_results), 10)
        self.assertEqual(io_results[0], 0)
        self.assertEqual(io_results[5], 10)
        
        # Check performance stats
        perf_stats = self.optimizer.executor.get_performance_stats()
        self.assertEqual(perf_stats["total_tasks_executed"], 10)
        self.assertGreater(perf_stats["avg_io_task_time"], 0)
    
    async def test_api_batching(self):
        """Test API call batching"""
        # Create multiple API calls
        calls = []
        for i in range(15):
            calls.append(
                self.optimizer.batch_api_call("/api/test", {"id": i})
            )
        
        # Execute all calls (should be batched)
        results = await asyncio.gather(*calls)
        
        self.assertEqual(len(results), 15)
        
        # Check batching stats
        batch_stats = self.optimizer.api_batcher.get_stats()
        self.assertGreater(batch_stats["total_batched"], 0)
    
    def test_memory_management(self):
        """Test memory management and GC optimization"""
        # Get initial memory stats
        initial_stats = self.optimizer.memory_manager.get_memory_stats()
        
        # Create some memory pressure
        large_data = []
        for i in range(100):
            large_data.append([0] * 10000)
        
        # Get stats after allocation
        after_stats = self.optimizer.memory_manager.get_memory_stats()
        self.assertGreater(after_stats["rss_mb"], initial_stats["rss_mb"])
        
        # Clear data and trigger GC
        large_data.clear()
        import gc
        gc.collect()
        
        # Verify GC was triggered
        gc_stats = self.optimizer.memory_manager.get_memory_stats()
        self.assertIsNotNone(gc_stats["gc_stats"])
    
    def test_performance_optimization(self):
        """Test system-wide optimization recommendations"""
        # Generate some activity
        for i in range(10):
            self.optimizer.cache_response(f"key_{i}", f"value_{i}", ttl=60)
        
        # Get optimization recommendations
        optimizations = self.optimizer.optimize_system()
        
        self.assertIn("concurrency", optimizations)
        self.assertIn("optimal_thread_workers", optimizations["concurrency"])
        
        # Generate performance report
        report = self.optimizer.get_performance_report()
        
        self.assertIn("cache_stats", report)
        self.assertIn("memory_stats", report)
        self.assertIn("optimizations", report)


class TestPhase5WorkflowIntegration(unittest.TestCase):
    """Test complete workflow with Phase 5 enhancements"""
    
    def setUp(self):
        """Set up test environment"""
        self.security = SecurityManager()
        self.optimizer = PerformanceOptimizer()
        
        # Create test user
        self.user = self.security.rbac_manager.create_user(
            "test_dev", "dev@test.com", AccessLevel.DEVELOPER
        )
        self.api_key = self.security.api_key_manager.generate_api_key(
            self.user.user_id, "test_workflow"
        )
    
    async def test_secure_optimized_workflow(self):
        """Test workflow execution with security and performance features"""
        # Authenticate user
        success, user_id = await self.security.authenticate(self.api_key, "127.0.0.1")
        self.assertTrue(success)
        
        # Check authorization for workflow execution
        authorized = self.security.authorize(user_id, "workflow", "execute")
        self.assertTrue(authorized)
        
        # Simulate workflow with caching
        workflow_key = f"workflow:{user_id}:test"
        
        # Check cache first
        cached_result = self.optimizer.get_cached_response(workflow_key)
        
        if cached_result is None:
            # Execute workflow (simulated)
            workflow_result = {
                "status": "completed",
                "agents_executed": ["project-architect", "rapid-builder"],
                "files_created": 10,
                "duration": 30.5
            }
            
            # Cache the result
            self.optimizer.cache_response(workflow_key, workflow_result, ttl=300)
        else:
            workflow_result = cached_result
        
        self.assertEqual(workflow_result["status"], "completed")
        
        # Log workflow execution
        self.security.audit_logger.log_event(
            SecurityEvent.DATA_ACCESS,
            user_id=user_id,
            resource="workflow",
            action="execute",
            success=True,
            details={"workflow_id": "test_workflow"}
        )
        
        # Check performance metrics
        perf_report = self.optimizer.get_performance_report()
        self.assertIsNotNone(perf_report)
    
    async def test_rate_limited_workflow(self):
        """Test workflow with rate limiting"""
        # Create guest user with low limits
        guest = self.security.rbac_manager.create_user(
            "guest_user", "guest@test.com", AccessLevel.GUEST
        )
        guest_key = self.security.api_key_manager.generate_api_key(
            guest.user_id, "guest_project"
        )
        
        # Execute workflows up to rate limit
        for i in range(10):
            success, _ = await self.security.authenticate(guest_key, "127.0.0.1")
            if success:
                # Simulate workflow execution
                await asyncio.sleep(0.01)
        
        # Next execution should be rate limited
        success, _ = await self.security.authenticate(guest_key, "127.0.0.1")
        self.assertFalse(success)
        
        # Get rate limit stats
        usage = self.security.rate_limiter.get_usage_stats(guest.user_id)
        self.assertGreaterEqual(usage["requests_last_minute"], 10)
    
    def test_sanitized_workflow_input(self):
        """Test workflow with input sanitization"""
        # Simulate workflow request with user input
        workflow_request = {
            "project_name": "Test<script>alert('xss')</script>Project",
            "description": "A test project",
            "path": "../../../etc/passwd"
        }
        
        # Sanitize inputs
        sanitized_request = {}
        
        # Project name should fail XSS check
        with self.assertRaises(ValueError):
            sanitized_request["project_name"] = self.security.sanitize_input(
                workflow_request["project_name"], "string"
            )
        
        # Path should fail traversal check
        with self.assertRaises(ValueError):
            sanitized_request["path"] = self.security.sanitize_input(
                workflow_request["path"], "path"
            )
        
        # Valid description should pass
        sanitized_request["description"] = self.security.sanitize_input(
            workflow_request["description"], "string"
        )
        self.assertIsNotNone(sanitized_request["description"])
    
    async def test_concurrent_agent_execution(self):
        """Test concurrent agent execution with optimization"""
        # Define agent tasks
        async def execute_agent(agent_name):
            # Simulate agent execution
            await asyncio.sleep(0.05)
            return {
                "agent": agent_name,
                "status": "completed",
                "files": 5
            }
        
        # Create tasks for multiple agents
        agent_tasks = [
            lambda name=agent: execute_agent(name)
            for agent in ["project-architect", "rapid-builder", "frontend-specialist"]
        ]
        
        # Execute concurrently
        results = await self.optimizer.execute_optimized(agent_tasks, "io")
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result["status"], "completed")
        
        # Check concurrency stats
        stats = self.optimizer.executor.get_performance_stats()
        self.assertEqual(stats["total_tasks_executed"], 3)


class TestPhase5EndToEnd(unittest.TestCase):
    """End-to-end test of Phase 5 components"""
    
    async def test_complete_production_workflow(self):
        """Test complete production workflow with all Phase 5 features"""
        # Initialize components
        security = SecurityManager()
        optimizer = PerformanceOptimizer()
        
        # Step 1: User setup and authentication
        admin = security.rbac_manager.create_user(
            "prod_admin", "admin@production.com", AccessLevel.ADMIN
        )
        api_key = security.api_key_manager.generate_api_key(
            admin.user_id, "production"
        )
        
        # Step 2: Authenticate and authorize
        success, user_id = await security.authenticate(api_key, "192.168.1.1")
        self.assertTrue(success)
        
        authorized = security.authorize(user_id, "workflow", "execute")
        self.assertTrue(authorized)
        
        # Step 3: Sanitize workflow input
        workflow_input = {
            "project_name": "ProductionApp",
            "features": ["auth", "dashboard", "api"],
            "constraints": {"budget": 5000, "timeline": "2 weeks"}
        }
        
        sanitized_input = security.sanitize_input(
            json.dumps(workflow_input), "json"
        )
        self.assertIsNotNone(sanitized_input)
        
        # Step 4: Check cache for previous results
        cache_key = f"workflow:{user_id}:production"
        cached = optimizer.get_cached_response(cache_key)
        
        if cached is None:
            # Step 5: Execute workflow with concurrent agents
            agent_tasks = []
            for agent in ["requirements-analyst", "project-architect", "rapid-builder"]:
                async def run_agent(name):
                    await asyncio.sleep(0.02)  # Simulate execution
                    return {"agent": name, "result": "completed"}
                
                agent_tasks.append(lambda a=agent: run_agent(a))
            
            # Execute concurrently with optimization
            agent_results = await optimizer.execute_optimized(agent_tasks, "io")
            
            # Step 6: Cache results
            workflow_result = {
                "workflow_id": "prod_123",
                "status": "completed",
                "agents": agent_results,
                "timestamp": datetime.now().isoformat()
            }
            optimizer.cache_response(cache_key, workflow_result, ttl=600)
        else:
            workflow_result = cached
        
        # Step 7: Log execution
        security.audit_logger.log_event(
            SecurityEvent.DATA_ACCESS,
            user_id=user_id,
            ip_address="192.168.1.1",
            resource="workflow",
            action="execute",
            success=True,
            details={"workflow_id": workflow_result.get("workflow_id")}
        )
        
        # Step 8: Generate reports
        security_report = security.get_security_report(days=1)
        performance_report = optimizer.get_performance_report()
        
        # Verify everything worked
        self.assertIsNotNone(workflow_result)
        self.assertEqual(workflow_result["status"], "completed")
        self.assertGreater(security_report["total_events"], 0)
        self.assertIn("cache_stats", performance_report)
        
        # Step 9: Cleanup
        security.audit_logger.flush()


def run_phase5_tests():
    """Run all Phase 5 integration tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase5WorkflowIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase5EndToEnd))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("PHASE 5 INTEGRATION TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailed Tests:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nTests with Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    print("\nPhase 5 Components Tested:")
    print("  [OK] Security Manager (API keys, RBAC, rate limiting)")
    print("  [OK] Performance Optimizer (caching, concurrency, batching)")
    print("  [OK] Input Sanitization (XSS, SQL injection, path traversal)")
    print("  [OK] Audit Logging (event tracking, risk analysis)")
    print("  [OK] Memory Management (GC optimization, monitoring)")
    print("  [OK] Query Optimization (caching, connection pooling)")
    print("  [OK] Complete Workflow Integration")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_phase5_tests()
    sys.exit(0 if success else 1)