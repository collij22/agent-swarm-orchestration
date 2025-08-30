#!/usr/bin/env python3
"""
Failure Injection and Recovery Tests
Tests system resilience with controlled failures and recovery mechanisms
"""

import pytest
import asyncio
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from unittest.mock import Mock, patch, AsyncMock
import json

# Import production components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.recovery_manager import RecoveryManager, RecoveryStrategy
from lib.production_monitor import ProductionMonitor
from lib.agent_runtime import AgentContext


@dataclass
class FailureScenario:
    """Represents a failure injection scenario"""
    name: str
    failure_type: str  # "exception", "timeout", "partial", "resource"
    failure_rate: float  # 0.0 to 1.0
    recovery_strategy: RecoveryStrategy
    expected_outcome: str  # "success", "partial", "failure"
    max_retries: int


class FailureInjector:
    """Injects controlled failures for testing"""
    
    def __init__(self):
        self.failure_scenarios: List[FailureScenario] = []
        self.injection_points: Dict[str, Callable] = {}
        self.failure_history: List[Dict] = []
        
    def add_scenario(self, scenario: FailureScenario):
        """Add a failure scenario"""
        self.failure_scenarios.append(scenario)
    
    def create_failing_executor(
        self,
        scenario: FailureScenario,
        base_executor: Optional[Callable] = None
    ):
        """Create an executor that fails according to scenario"""
        
        call_count = {"count": 0}
        
        async def failing_executor():
            call_count["count"] += 1
            
            # Record attempt
            self.failure_history.append({
                "scenario": scenario.name,
                "attempt": call_count["count"],
                "timestamp": time.time()
            })
            
            # Determine if this attempt should fail
            should_fail = random.random() < scenario.failure_rate
            
            if should_fail and call_count["count"] <= scenario.max_retries:
                # Inject failure based on type
                if scenario.failure_type == "exception":
                    raise Exception(f"Injected exception for {scenario.name}")
                elif scenario.failure_type == "timeout":
                    await asyncio.sleep(10)  # Simulate timeout
                    raise asyncio.TimeoutError(f"Injected timeout for {scenario.name}")
                elif scenario.failure_type == "partial":
                    return False, {"partial_result": "incomplete"}, "Partial failure"
                elif scenario.failure_type == "resource":
                    raise MemoryError(f"Injected resource exhaustion for {scenario.name}")
                else:
                    return False, None, f"Injected failure for {scenario.name}"
            else:
                # Success after retries or if not failing
                if base_executor:
                    return await base_executor()
                return True, f"Success for {scenario.name} after {call_count['count']} attempts", None
        
        return failing_executor
    
    def get_failure_stats(self) -> Dict:
        """Get statistics about injected failures"""
        stats = {
            "total_failures": len(self.failure_history),
            "scenarios_tested": len(set(f["scenario"] for f in self.failure_history)),
            "max_retries": max((f["attempt"] for f in self.failure_history), default=0),
            "failure_types": {}
        }
        
        for scenario in self.failure_scenarios:
            scenario_attempts = [
                f["attempt"] for f in self.failure_history 
                if f["scenario"] == scenario.name
            ]
            if scenario_attempts:
                stats["failure_types"][scenario.failure_type] = {
                    "count": len(scenario_attempts),
                    "max_attempts": max(scenario_attempts)
                }
        
        return stats


class RecoveryTester:
    """Tests recovery mechanisms"""
    
    def __init__(self):
        self.recovery_manager = RecoveryManager()
        self.monitor = ProductionMonitor()
        self.failure_injector = FailureInjector()
        
    async def test_recovery_scenario(
        self,
        scenario: FailureScenario,
        context: Optional[Dict] = None
    ) -> Dict:
        """Test a specific recovery scenario"""
        
        start_time = time.time()
        
        # Create failing executor
        executor = self.failure_injector.create_failing_executor(scenario)
        
        # Configure recovery manager
        self.recovery_manager.max_retries = scenario.max_retries
        self.recovery_manager.recovery_strategy = scenario.recovery_strategy
        
        # Execute with recovery
        success, result, error = await self.recovery_manager.recover_with_retry(
            agent_name=f"test_agent_{scenario.name}",
            agent_executor=executor,
            context=context or {},
            max_attempts=scenario.max_retries
        )
        
        duration = time.time() - start_time
        
        # Determine if outcome matches expectation
        outcome_matched = False
        if scenario.expected_outcome == "success" and success:
            outcome_matched = True
        elif scenario.expected_outcome == "partial" and not success and result:
            outcome_matched = True
        elif scenario.expected_outcome == "failure" and not success:
            outcome_matched = True
        
        return {
            "scenario": scenario.name,
            "success": success,
            "outcome_matched": outcome_matched,
            "recovery_attempts": len([
                f for f in self.failure_injector.failure_history 
                if f["scenario"] == scenario.name
            ]),
            "duration": duration,
            "result": result,
            "error": error
        }
    
    async def test_cascading_failures(
        self,
        agent_chain: List[str],
        failure_points: List[int]
    ) -> Dict:
        """Test cascading failures across multiple agents"""
        
        results = {}
        context = {"agents_completed": []}
        
        for i, agent_name in enumerate(agent_chain):
            # Determine if this agent should fail
            should_fail = i in failure_points
            
            if should_fail:
                # Create failing scenario
                scenario = FailureScenario(
                    name=f"{agent_name}_cascading",
                    failure_type="exception",
                    failure_rate=1.0 if i == failure_points[0] else 0.5,
                    recovery_strategy=RecoveryStrategy.RETRY_SAME,
                    expected_outcome="success" if i != failure_points[0] else "failure",
                    max_retries=3
                )
            else:
                # Create succeeding scenario
                scenario = FailureScenario(
                    name=f"{agent_name}_cascading",
                    failure_type="none",
                    failure_rate=0.0,
                    recovery_strategy=RecoveryStrategy.RETRY_SAME,
                    expected_outcome="success",
                    max_retries=1
                )
            
            # Test recovery
            result = await self.test_recovery_scenario(scenario, context)
            results[agent_name] = result
            
            if result["success"]:
                context["agents_completed"].append(agent_name)
            else:
                # Cascading failure - stop chain
                break
        
        return {
            "completed_agents": context["agents_completed"],
            "failed_at": agent_chain[len(context["agents_completed"])] 
                        if len(context["agents_completed"]) < len(agent_chain) else None,
            "individual_results": results,
            "cascade_handled": len(context["agents_completed"]) > failure_points[0]
        }


class TestFailureInjection:
    """Test cases for failure injection and recovery"""
    
    @pytest.fixture
    def recovery_tester(self):
        """Create recovery tester"""
        return RecoveryTester()
    
    @pytest.mark.asyncio
    async def test_exception_recovery(self, recovery_tester):
        """Test recovery from exceptions"""
        scenario = FailureScenario(
            name="exception_test",
            failure_type="exception",
            failure_rate=0.5,  # 50% failure rate
            recovery_strategy=RecoveryStrategy.RETRY_SAME,
            expected_outcome="success",
            max_retries=3
        )
        
        result = await recovery_tester.test_recovery_scenario(scenario)
        
        assert result["outcome_matched"], f"Outcome mismatch: {result}"
        assert result["recovery_attempts"] <= scenario.max_retries
        assert result["success"] or result["recovery_attempts"] == scenario.max_retries
    
    @pytest.mark.asyncio
    async def test_timeout_recovery(self, recovery_tester):
        """Test recovery from timeouts"""
        scenario = FailureScenario(
            name="timeout_test",
            failure_type="timeout",
            failure_rate=0.3,  # 30% timeout rate
            recovery_strategy=RecoveryStrategy.RETRY_SAME,
            expected_outcome="success",
            max_retries=2
        )
        
        with pytest.raises(asyncio.TimeoutError):
            # Use shorter timeout for testing
            with patch.object(recovery_tester.recovery_manager, 'timeout', 1):
                result = await recovery_tester.test_recovery_scenario(scenario)
    
    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, recovery_tester):
        """Test recovery from partial failures"""
        scenario = FailureScenario(
            name="partial_test",
            failure_type="partial",
            failure_rate=0.7,  # 70% partial failure rate
            recovery_strategy=RecoveryStrategy.PARTIAL_COMPLETION,
            expected_outcome="partial",
            max_retries=2
        )
        
        result = await recovery_tester.test_recovery_scenario(scenario)
        
        # Should accept partial results
        assert result["result"] is not None or result["success"]
        assert result["recovery_attempts"] <= scenario.max_retries
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_recovery(self, recovery_tester):
        """Test recovery from resource exhaustion"""
        scenario = FailureScenario(
            name="resource_test",
            failure_type="resource",
            failure_rate=0.4,  # 40% resource failure rate
            recovery_strategy=RecoveryStrategy.ALTERNATIVE_AGENT,
            expected_outcome="success",
            max_retries=2
        )
        
        result = await recovery_tester.test_recovery_scenario(scenario)
        
        # Should either succeed or exhaust retries
        assert result["recovery_attempts"] <= scenario.max_retries
        if not result["success"]:
            assert "resource" in str(result["error"]).lower()
    
    @pytest.mark.asyncio
    async def test_cascading_failure_handling(self, recovery_tester):
        """Test handling of cascading failures"""
        agent_chain = [
            "project-architect",
            "rapid-builder",
            "frontend-specialist",
            "quality-guardian",
            "devops-engineer"
        ]
        
        # Inject failures at positions 1 and 3
        failure_points = [1, 3]
        
        result = await recovery_tester.test_cascading_failures(
            agent_chain,
            failure_points
        )
        
        # Should handle first failure but might cascade
        assert len(result["completed_agents"]) >= failure_points[0]
        assert result["failed_at"] in agent_chain or result["failed_at"] is None
    
    @pytest.mark.asyncio
    async def test_recovery_with_monitoring(self, recovery_tester):
        """Test recovery with production monitoring"""
        scenario = FailureScenario(
            name="monitored_test",
            failure_type="exception",
            failure_rate=0.6,
            recovery_strategy=RecoveryStrategy.RETRY_SAME,
            expected_outcome="success",
            max_retries=3
        )
        
        # Start monitoring
        exec_id = recovery_tester.monitor.start_execution(
            "test_agent",
            requirements=["test_requirement"]
        )
        
        result = await recovery_tester.test_recovery_scenario(scenario)
        
        # End monitoring
        recovery_tester.monitor.end_execution(
            exec_id,
            success=result["success"],
            metrics={"recovery_attempts": result["recovery_attempts"]}
        )
        
        # Check monitoring captured the recovery
        health = recovery_tester.monitor.get_system_health()
        assert health["total_executions"] > 0
        
        if result["success"]:
            assert health["success_rate"] > 0
    
    @pytest.mark.asyncio
    async def test_multiple_failure_types(self, recovery_tester):
        """Test handling multiple types of failures"""
        scenarios = [
            FailureScenario(
                name="multi_exception",
                failure_type="exception",
                failure_rate=0.3,
                recovery_strategy=RecoveryStrategy.RETRY_SAME,
                expected_outcome="success",
                max_retries=2
            ),
            FailureScenario(
                name="multi_timeout",
                failure_type="timeout",
                failure_rate=0.2,
                recovery_strategy=RecoveryStrategy.RETRY_SAME,
                expected_outcome="success",
                max_retries=2
            ),
            FailureScenario(
                name="multi_partial",
                failure_type="partial",
                failure_rate=0.4,
                recovery_strategy=RecoveryStrategy.PARTIAL_COMPLETION,
                expected_outcome="partial",
                max_retries=1
            )
        ]
        
        results = []
        for scenario in scenarios:
            result = await recovery_tester.test_recovery_scenario(scenario)
            results.append(result)
        
        # Check failure statistics
        stats = recovery_tester.failure_injector.get_failure_stats()
        assert stats["scenarios_tested"] >= len(scenarios)
        assert stats["total_failures"] > 0
        
        # Most scenarios should recover
        successful = [r for r in results if r["success"] or r["outcome_matched"]]
        assert len(successful) >= len(scenarios) * 0.6  # 60% success rate
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, recovery_tester):
        """Test exponential backoff in recovery"""
        scenario = FailureScenario(
            name="backoff_test",
            failure_type="exception",
            failure_rate=0.8,  # High failure rate
            recovery_strategy=RecoveryStrategy.RETRY_SAME,
            expected_outcome="success",
            max_retries=3
        )
        
        start_time = time.time()
        result = await recovery_tester.test_recovery_scenario(scenario)
        duration = time.time() - start_time
        
        # With exponential backoff, duration should increase with retries
        if result["recovery_attempts"] > 1:
            # Expected minimum duration with backoff
            expected_min_duration = sum(
                recovery_tester.recovery_manager.base_delay * (2 ** i)
                for i in range(result["recovery_attempts"] - 1)
            )
            # Allow some tolerance
            assert duration >= expected_min_duration * 0.5


class TestRecoveryStrategies:
    """Test different recovery strategies"""
    
    @pytest.fixture
    def recovery_manager(self):
        """Create recovery manager"""
        return RecoveryManager()
    
    @pytest.mark.asyncio
    async def test_retry_strategy(self, recovery_manager):
        """Test RETRY recovery strategy"""
        recovery_manager.recovery_strategy = RecoveryStrategy.RETRY_SAME
        
        attempt_count = {"count": 0}
        
        async def failing_executor():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                return False, None, "Failure"
            return True, "Success", None
        
        success, result, error = await recovery_manager.recover_with_retry(
            "test_agent",
            failing_executor,
            {},
            max_attempts=3
        )
        
        assert success
        assert attempt_count["count"] == 3
        assert result == "Success"
    
    @pytest.mark.asyncio
    async def test_alternative_strategy(self, recovery_manager):
        """Test ALTERNATIVE recovery strategy"""
        recovery_manager.recovery_strategy = RecoveryStrategy.ALTERNATIVE_AGENT
        
        async def primary_executor():
            return False, None, "Primary failed"
        
        async def alternative_executor():
            return True, "Alternative success", None
        
        # Set alternative agent
        recovery_manager.alternative_agents = {
            "test_agent": alternative_executor
        }
        
        success, result, error = await recovery_manager.recover_with_retry(
            "test_agent",
            primary_executor,
            {},
            max_attempts=2
        )
        
        assert success
        assert "Alternative" in result
    
    @pytest.mark.asyncio
    async def test_partial_strategy(self, recovery_manager):
        """Test PARTIAL recovery strategy"""
        recovery_manager.recovery_strategy = RecoveryStrategy.PARTIAL_COMPLETION
        
        async def partial_executor():
            return False, {"partial_data": "some results"}, "Partial completion"
        
        success, result, error = await recovery_manager.recover_with_retry(
            "test_agent",
            partial_executor,
            {},
            max_attempts=1
        )
        
        # Should accept partial results
        assert not success  # Not fully successful
        assert result is not None  # But has partial results
        assert "partial_data" in result
    
    @pytest.mark.asyncio
    async def test_skip_strategy(self, recovery_manager):
        """Test SKIP recovery strategy"""
        recovery_manager.recovery_strategy = RecoveryStrategy.SKIP_TASK
        
        async def failing_executor():
            return False, None, "Failure"
        
        success, result, error = await recovery_manager.recover_with_retry(
            "test_agent",
            failing_executor,
            {},
            max_attempts=1
        )
        
        # Should skip after first failure
        assert not success
        assert error == "Agent skipped after failure"
    
    @pytest.mark.asyncio
    async def test_manual_strategy(self, recovery_manager):
        """Test MANUAL recovery strategy"""
        recovery_manager.recovery_strategy = RecoveryStrategy.MANUAL_INTERVENTION
        
        async def failing_executor():
            return False, None, "Needs manual intervention"
        
        # Queue for manual intervention
        success, result, error = await recovery_manager.recover_with_retry(
            "test_agent",
            failing_executor,
            {},
            max_attempts=1
        )
        
        assert not success
        assert "manual" in error.lower()
        
        # Check manual intervention queue
        assert len(recovery_manager.manual_intervention_queue) > 0
        queued_item = recovery_manager.manual_intervention_queue[0]
        assert queued_item["agent_name"] == "test_agent"


if __name__ == "__main__":
    # Run demonstration
    async def demo():
        print("Failure Injection and Recovery Test Demo")
        print("=" * 50)
        
        tester = RecoveryTester()
        
        # Test various failure scenarios
        scenarios = [
            FailureScenario(
                name="demo_exception",
                failure_type="exception",
                failure_rate=0.5,
                recovery_strategy=RecoveryStrategy.RETRY_SAME,
                expected_outcome="success",
                max_retries=3
            ),
            FailureScenario(
                name="demo_partial",
                failure_type="partial",
                failure_rate=0.7,
                recovery_strategy=RecoveryStrategy.PARTIAL_COMPLETION,
                expected_outcome="partial",
                max_retries=2
            )
        ]
        
        for scenario in scenarios:
            print(f"\nTesting scenario: {scenario.name}")
            print(f"  Failure type: {scenario.failure_type}")
            print(f"  Failure rate: {scenario.failure_rate * 100}%")
            print(f"  Strategy: {scenario.recovery_strategy}")
            
            result = await tester.test_recovery_scenario(scenario)
            
            print(f"  Result: {'SUCCESS' if result['success'] else 'FAILED'}")
            print(f"  Recovery attempts: {result['recovery_attempts']}")
            print(f"  Outcome matched: {result['outcome_matched']}")
        
        # Test cascading failures
        print("\n\nTesting Cascading Failures")
        print("-" * 30)
        
        cascade_result = await tester.test_cascading_failures(
            ["agent1", "agent2", "agent3", "agent4"],
            [1, 2]  # Failures at positions 1 and 2
        )
        
        print(f"Completed agents: {cascade_result['completed_agents']}")
        print(f"Failed at: {cascade_result['failed_at']}")
        print(f"Cascade handled: {cascade_result['cascade_handled']}")
        
        # Print statistics
        stats = tester.failure_injector.get_failure_stats()
        print("\n\nFailure Statistics")
        print("-" * 30)
        print(f"Total failures injected: {stats['total_failures']}")
        print(f"Scenarios tested: {stats['scenarios_tested']}")
        print(f"Max retry attempts: {stats['max_retries']}")
        print(f"Failure types: {json.dumps(stats['failure_types'], indent=2)}")
    
    asyncio.run(demo())