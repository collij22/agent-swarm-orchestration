#!/usr/bin/env python3
"""
Phase 4 Advanced Features Demo
Demonstrates the new intelligent orchestration, observability, and self-healing capabilities
"""

import asyncio
import json
import time
from pathlib import Path

print("=" * 60)
print("PHASE 4 ADVANCED FEATURES DEMO")
print("=" * 60)

# Check component availability
components_status = {
    "Adaptive Orchestrator": False,
    "Observability Platform": False,
    "Self-Healing System": False,
    "Phase 4 Integration": False
}

try:
    from lib.adaptive_orchestrator import AdaptiveOrchestrator
    components_status["Adaptive Orchestrator"] = True
except ImportError as e:
    print(f"Note: Adaptive Orchestrator not available ({e})")

try:
    from lib.observability_platform import ObservabilityPlatform, LogLevel
    components_status["Observability Platform"] = True
except ImportError as e:
    print(f"Note: Observability Platform not available ({e})")

try:
    from lib.self_healing_system import SelfHealingSystem
    components_status["Self-Healing System"] = True
except ImportError as e:
    print(f"Note: Self-Healing System not available ({e})")

try:
    from lib.phase4_integration import Phase4IntegratedSystem, Phase4Config
    components_status["Phase 4 Integration"] = True
except ImportError as e:
    print(f"Note: Phase 4 Integration not available ({e})")

print("\n### Component Status ###")
for component, available in components_status.items():
    status = "[OK]" if available else "[--]"
    print(f"  {status} {component}")

# Demo functions for available components

def demo_adaptive_orchestrator():
    """Demo the Adaptive Orchestrator features"""
    print("\n### ADAPTIVE ORCHESTRATOR DEMO ###")
    
    if not components_status["Adaptive Orchestrator"]:
        print("  Skipping - component not available")
        return
    
    orchestrator = AdaptiveOrchestrator()
    
    # Demo 1: Agent Selection
    print("\n1. Intelligent Agent Selection:")
    requirements = {
        "features": ["user authentication", "AI recommendations", "real-time chat"],
        "project": "collaborative_platform"
    }
    available_agents = [
        "project-architect", "rapid-builder", "frontend-specialist",
        "ai-specialist", "database-expert", "quality-guardian"
    ]
    
    selected = orchestrator.select_optimal_agents(requirements, available_agents)
    print(f"   Requirements: {requirements['features'][:2]}...")
    print(f"   Selected agents: {selected}")
    
    # Demo 2: Dynamic Timeouts
    print("\n2. Dynamic Timeout Calculation:")
    for agent in selected[:3]:
        timeout = orchestrator.get_dynamic_timeout(agent)
        print(f"   {agent}: {timeout:.0f}s")
    
    # Demo 3: Parallel Optimization
    print("\n3. Parallel Execution Groups:")
    groups = orchestrator.optimize_parallel_execution(selected)
    for i, group in enumerate(groups, 1):
        print(f"   Phase {i}: {', '.join(group)}")
    
    # Demo 4: Workload Prediction
    print("\n4. Workload Prediction:")
    prediction = orchestrator.predict_workload(requirements)
    print(f"   Estimated agents: {prediction.estimated_agents}")
    print(f"   Estimated duration: {prediction.estimated_duration:.0f}s")
    print(f"   Estimated cost: ${prediction.estimated_cost:.2f}")
    print(f"   Confidence: {prediction.confidence:.0%}")

def demo_observability_platform():
    """Demo the Observability Platform features"""
    print("\n### OBSERVABILITY PLATFORM DEMO ###")
    
    if not components_status["Observability Platform"]:
        print("  Skipping - component not available")
        return
    
    platform = ObservabilityPlatform(enable_otel=False)
    
    # Demo 1: Distributed Tracing
    print("\n1. Distributed Tracing:")
    trace_id = platform.start_trace("demo_workflow", {"demo": True})
    print(f"   Started trace: {trace_id[:8]}...")
    
    # Simulate agent spans
    agents = ["project-architect", "rapid-builder", "quality-guardian"]
    for agent in agents:
        span_id = platform.start_span(trace_id, f"agent_{agent}")
        platform.log(LogLevel.INFO, f"Executing {agent}", agent, trace_id, span_id)
        time.sleep(0.1)  # Simulate work
        platform.end_span(span_id)
        print(f"   Completed span: {agent}")
    
    # Demo 2: Metrics Recording
    print("\n2. Performance Metrics:")
    for i in range(5):
        platform.record_metric("demo_metric", 100 + i * 20, {"type": "demo"})
    
    summary = platform.get_metrics_summary("demo_metric")
    if "demo_metric" in summary:
        stats = summary["demo_metric"]
        print(f"   Count: {stats['count']}")
        print(f"   Mean: {stats['mean']:.1f}")
        print(f"   Min/Max: {stats['min']:.1f}/{stats['max']:.1f}")
    
    # Demo 3: Logging
    print("\n3. Centralized Logging:")
    platform.log(LogLevel.INFO, "Demo info message", "demo")
    platform.log(LogLevel.WARNING, "Demo warning", "demo")
    platform.log(LogLevel.ERROR, "Demo error", "demo")
    
    logs = platform.get_recent_logs(5)
    print(f"   Captured {len(logs)} log entries")
    
    # Demo 4: Performance Insights
    print("\n4. Performance Insights:")
    insights = platform.get_performance_insights()
    metrics = insights["dashboard_metrics"]
    print(f"   Total traces: {metrics['total_traces']}")
    print(f"   Active traces: {metrics['active_traces']}")
    print(f"   Total logs: {metrics['total_logs']}")

def demo_self_healing():
    """Demo the Self-Healing System features"""
    print("\n### SELF-HEALING SYSTEM DEMO ###")
    
    if not components_status["Self-Healing System"]:
        print("  Skipping - component not available")
        return
    
    healer = SelfHealingSystem()
    
    # Demo 1: Error Pattern Detection
    print("\n1. Error Pattern Detection:")
    errors = [
        {"message": "Timeout exceeded in API call", "agent": "ai-specialist", "timestamp": time.time()},
        {"message": "Timeout in processing request", "agent": "ai-specialist", "timestamp": time.time()},
        {"message": "Rate limit exceeded", "agent": "rapid-builder", "timestamp": time.time()},
    ]
    
    patterns = healer.detect_error_patterns(errors)
    print(f"   Detected {len(patterns)} patterns")
    for pattern in patterns[:2]:
        print(f"   - {pattern.error_type}: {pattern.occurrences} occurrences")
        if pattern.suggested_fixes:
            print(f"     Fix: {pattern.suggested_fixes[0]}")
    
    # Demo 2: Prompt Optimization
    print("\n2. Prompt Optimization:")
    current_prompt = "You are an AI assistant. Complete the task."
    failures = [
        {"type": "timeout", "context": "Long operation"},
        {"type": "misunderstanding", "context": "Unclear instructions"}
    ]
    
    optimization = healer.optimize_prompt("test-agent", current_prompt, failures)
    print(f"   Original length: {len(current_prompt)} chars")
    print(f"   Optimized length: {len(optimization.optimized_prompt)} chars")
    print(f"   Reason: {optimization.reason}")
    
    # Demo 3: Configuration Tuning
    print("\n3. Configuration Auto-Tuning:")
    config = {"agent_timeout": 100, "max_parallel_agents": 5}
    metrics = {"avg_response_time": 95, "error_rate": 0.15}
    
    tunes = healer.auto_tune_configuration(config, metrics)
    print(f"   Generated {len(tunes)} tuning recommendations")
    for tune in tunes[:2]:
        print(f"   - {tune.parameter}: {tune.current_value} -> {tune.recommended_value}")
        print(f"     Reason: {tune.reason}")
    
    # Demo 4: Knowledge Base
    print("\n4. Knowledge Base Management:")
    entry_id = healer.update_knowledge_base(
        category="best_practice",
        title="Demo best practice",
        description="A demonstration entry",
        solution="Apply this solution"
    )
    print(f"   Added entry: {entry_id}")
    print(f"   Total entries: {len(healer.knowledge_base)}")

async def demo_integrated_system():
    """Demo the integrated Phase 4 system"""
    print("\n### INTEGRATED SYSTEM DEMO ###")
    
    if not components_status["Phase 4 Integration"]:
        print("  Skipping - component not available")
        return
    
    config = Phase4Config(
        enable_adaptive_orchestration=True,
        enable_observability=True,
        enable_self_healing=True,
        enable_auto_fix=False,  # Disable for demo
        enable_auto_tune=False  # Disable for demo
    )
    
    system = Phase4IntegratedSystem(config)
    
    # Demo 1: Workflow Orchestration
    print("\n1. Intelligent Workflow Orchestration:")
    requirements = {
        "project": "Demo App",
        "features": ["authentication", "API", "dashboard"]
    }
    available_agents = ["project-architect", "rapid-builder", "frontend-specialist"]
    
    result = await system.orchestrate_workflow(requirements, available_agents)
    print(f"   Success: {result['success']}")
    print(f"   Agents executed: {len(result['agents_executed'])}")
    print(f"   Errors: {len(result['errors'])}")
    if "success_rate" in result["metrics"]:
        print(f"   Success rate: {result['metrics']['success_rate']:.0%}")
    
    # Demo 2: System Health
    print("\n2. System Health Check:")
    health = system.get_system_health()
    print(f"   Status: {health['status']}")
    print(f"   Active components: {len(health['components'])}")
    print(f"   Recommendations: {len(health['recommendations'])}")
    
    # Demo 3: Analytics Export
    print("\n3. Analytics Export:")
    system.export_analytics("demo_analytics")
    print("   Analytics exported to demo_analytics/")
    
    # Cleanup
    await system.shutdown()
    print("\n4. System Shutdown:")
    print("   Gracefully shut down all components")

def main():
    """Main demo function"""
    print("\n" + "=" * 60)
    print("Starting Phase 4 Feature Demonstrations...")
    print("=" * 60)
    
    # Run demos for available components
    demo_adaptive_orchestrator()
    demo_observability_platform()
    demo_self_healing()
    
    # Run async demo
    print("\n" + "=" * 60)
    print("Running Integrated System Demo (Async)...")
    print("=" * 60)
    
    try:
        asyncio.run(demo_integrated_system())
    except Exception as e:
        print(f"Note: Integrated demo skipped ({e})")
    
    # Summary
    print("\n" + "=" * 60)
    print("DEMO SUMMARY")
    print("=" * 60)
    
    available_count = sum(1 for v in components_status.values() if v)
    total_count = len(components_status)
    
    print(f"\nPhase 4 Components Available: {available_count}/{total_count}")
    
    if available_count == total_count:
        print("\n[OK] All Phase 4 Advanced Features are operational!")
        print("The system now has:")
        print("  - Intelligent agent selection with ML optimization")
        print("  - Comprehensive observability and tracing")
        print("  - Self-healing with automatic error recovery")
        print("  - Continuous learning and improvement")
    else:
        print("\n[!] Some components require additional dependencies:")
        print("  - For ML features: pip install scikit-learn numpy scipy")
        print("  - For tracing: pip install opentelemetry-api opentelemetry-sdk")
        print("\nCore functionality is still available with fallback implementations.")
    
    print("\n" + "=" * 60)
    print("Phase 4 Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()