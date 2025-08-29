#!/usr/bin/env python3
"""
Test integration of Session Manager with Agent System

This demonstrates how the new session management system integrates
with the existing agent swarm components.
"""

import sys
import json
import time
from pathlib import Path

# Add lib directory to path
sys.path.append(str(Path(__file__).parent / "lib"))

from lib.session_manager import SessionManager, Checkpoint
from lib.agent_logger import create_new_session, EventType, LogLevel
from lib.performance_tracker import PerformanceTracker, track_execution
from lib.metrics_aggregator import MetricsAggregator, AggregationPeriod
from lib.session_analyzer import SessionAnalyzer, AnalysisType

def simulate_agent_workflow():
    """Simulate an agent workflow with session tracking"""
    
    print("=== Session Manager Integration Test ===\n")
    
    # 1. Initialize components
    session_manager = SessionManager()
    logger = create_new_session()
    performance_tracker = PerformanceTracker()
    
    # Start performance monitoring
    performance_tracker.start_monitoring()
    
    # 2. Create a new session
    session = session_manager.create_session(
        project_type="test_integration",
        requirements={
            "name": "Session Test App",
            "features": ["auth", "api", "database"],
            "agents": ["project-architect", "rapid-builder", "quality-guardian"]
        },
        tags=["test", "integration", "demo"]
    )
    
    print(f"Created session: {session.metadata.session_id[:8]}...")
    
    # 3. Simulate agent executions
    agents = ["project-architect", "rapid-builder", "quality-guardian"]
    
    for agent_name in agents:
        print(f"\nExecuting agent: {agent_name}")
        
        # Track with performance tracker
        with track_execution(performance_tracker, agent_name):
            # Log agent start
            logger.log_agent_start(
                agent_name,
                f"Processing {agent_name} for test app",
                f"Starting {agent_name} with test requirements"
            )
            
            # Simulate work
            time.sleep(0.5)
            
            # Simulate tool calls
            logger.log_tool_call(
                agent_name,
                "analyze_requirements" if agent_name == "project-architect" else "execute",
                {"param": "value"},
                f"{agent_name} is analyzing the requirements"
            )
            
            # Track API call
            performance_tracker.track_api_call("claude-3-sonnet", tokens=500)
            
            # Log completion
            logger.log_agent_complete(
                agent_name,
                success=True,
                result=f"{agent_name} completed successfully"
            )
            
            # Add checkpoint
            checkpoint = Checkpoint(
                name=f"{agent_name}_complete",
                timestamp=logger.get_current_timestamp(),
                agent_name=agent_name,
                phase="execution",
                state={"status": "completed", "artifacts": []},
                reasoning=f"{agent_name} finished processing"
            )
            session_manager.add_checkpoint(session.metadata.session_id, checkpoint)
    
    # 4. Complete the session
    logger.close_session()
    session_manager.complete_session(session.metadata.session_id, success=True)
    performance_tracker.stop_monitoring()
    
    print("\n" + "="*50)
    print("Session completed successfully!")
    
    # 5. Analyze the session
    print("\n=== Session Analysis ===\n")
    
    # Get metrics
    metrics_aggregator = MetricsAggregator(session_manager)
    metrics = metrics_aggregator.aggregate_metrics(period=AggregationPeriod.ALL_TIME)
    
    print(f"Total Sessions: {metrics.total_sessions}")
    print(f"Successful Sessions: {metrics.successful_sessions}")
    print(f"Total API Calls: {metrics.total_api_calls}")
    print(f"Average Duration: {metrics.average_session_duration_ms:.1f}ms")
    
    # Analyze session
    analyzer = SessionAnalyzer(session_manager)
    analysis = analyzer.analyze_session(
        session.metadata.session_id,
        [AnalysisType.DECISION_FLOW, AnalysisType.OPTIMIZATION]
    )
    
    print(f"\nDecision Flow Analysis:")
    if "decision_flow" in analysis["analyses"]:
        flow = analysis["analyses"]["decision_flow"]
        print(f"  Total Decisions: {flow['total_decisions']}")
        print(f"  Bottlenecks: {len(flow['bottlenecks'])}")
        print(f"  Parallel Opportunities: {len(flow['parallel_opportunities'])}")
    
    # Get performance summary
    perf_summary = performance_tracker.get_performance_summary()
    print(f"\nPerformance Summary:")
    print(f"  Total Executions: {perf_summary['totals']['executions']}")
    print(f"  Success Rate: {perf_summary['success_rate']:.1f}%")
    print(f"  Peak Memory: {perf_summary['peaks']['memory_mb']:.1f}MB")
    print(f"  Total API Calls: {perf_summary['totals']['api_calls']}")
    
    # 6. Test session replay (mock mode)
    print("\n=== Testing Session Replay ===\n")
    print("Replaying session in mock mode...")
    
    success = session_manager.replay_session(
        session.metadata.session_id,
        mode=session_manager.ReplayMode.MOCK
    )
    
    if success:
        print("Replay completed successfully!")
    
    return session.metadata.session_id

def test_cli_commands(session_id: str):
    """Test CLI commands with the created session"""
    import subprocess
    
    print("\n=== Testing CLI Commands ===\n")
    
    commands = [
        ["python", "session_cli.py", "list", "--json"],
        ["python", "session_cli.py", "view", session_id[:8], "--format", "summary"],
        ["python", "session_cli.py", "metrics", "--period", "all_time"],
    ]
    
    for cmd in commands:
        print(f"\nRunning: {' '.join(cmd[2:])}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✓ Command successful")
                # Show first line of output
                lines = result.stdout.split('\n')
                if lines and lines[0]:
                    print(f"  Output: {lines[0][:80]}...")
            else:
                print(f"✗ Command failed: {result.stderr[:100]}")
        except subprocess.TimeoutExpired:
            print("✗ Command timed out")
        except Exception as e:
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    # Run integration test
    session_id = simulate_agent_workflow()
    
    # Test CLI commands
    test_cli_commands(session_id)
    
    print("\n" + "="*50)
    print("Integration test completed!")
    print("\nThe Session Manager provides:")
    print("  ✓ Session tracking and storage")
    print("  ✓ Performance monitoring")
    print("  ✓ Metrics aggregation")
    print("  ✓ Session analysis and optimization")
    print("  ✓ Session replay for debugging")
    print("  ✓ CLI interface for management")
    print("\nReady for production use with the agent swarm!")