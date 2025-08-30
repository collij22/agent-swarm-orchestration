#!/usr/bin/env python3
"""
Phase 4 Integration - Ties together all advanced features
Integrates Adaptive Orchestrator, Observability Platform, and Self-Healing System
"""

import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# Import Phase 4 components
try:
    from .adaptive_orchestrator import AdaptiveOrchestrator, ModelType
    from .observability_platform import ObservabilityPlatform, LogLevel
    from .self_healing_system import SelfHealingSystem
    HAS_PHASE4 = True
except ImportError:
    HAS_PHASE4 = False
    # Create dummy LogLevel for compatibility
    from enum import Enum
    class LogLevel(Enum):
        INFO = "INFO"
        WARNING = "WARNING"
        ERROR = "ERROR"
    print("Warning: Phase 4 components not fully available")

# Import existing components
try:
    from .agent_runtime import AgentContext, AnthropicAgentRunner
    from .production_monitor import ProductionMonitor
    from .recovery_manager import RecoveryManager
    from .session_manager import SessionManager
except ImportError:
    print("Warning: Some existing components not available")

@dataclass
class Phase4Config:
    """Configuration for Phase 4 features"""
    enable_adaptive_orchestration: bool = True
    enable_observability: bool = True
    enable_self_healing: bool = True
    enable_auto_fix: bool = True
    enable_auto_tune: bool = True
    ml_model_path: str = "models/agent_selector.pkl"
    knowledge_base_path: str = "data/knowledge_base.json"
    otlp_endpoint: str = "localhost:4317"
    max_parallel_agents: int = 5
    enable_distributed_tracing: bool = True

class Phase4IntegratedSystem:
    """
    Integrated system with all Phase 4 advanced features
    Provides a unified interface for:
    - Intelligent agent selection and orchestration
    - Comprehensive observability and tracing
    - Self-healing and automatic optimization
    """
    
    def __init__(self, config: Phase4Config = None):
        self.config = config or Phase4Config()
        
        # Initialize Phase 4 components
        self.adaptive_orchestrator = None
        self.observability = None
        self.self_healer = None
        
        if HAS_PHASE4:
            if self.config.enable_adaptive_orchestration:
                self.adaptive_orchestrator = AdaptiveOrchestrator(
                    ml_model_path=self.config.ml_model_path
                )
            
            if self.config.enable_observability:
                self.observability = ObservabilityPlatform(
                    enable_otel=self.config.enable_distributed_tracing,
                    otlp_endpoint=self.config.otlp_endpoint
                )
            
            if self.config.enable_self_healing:
                self.self_healer = SelfHealingSystem(
                    knowledge_base_path=self.config.knowledge_base_path,
                    enable_auto_fix=self.config.enable_auto_fix,
                    enable_auto_tune=self.config.enable_auto_tune
                )
        
        # Integration with existing components
        self.production_monitor = None
        self.recovery_manager = None
        self.session_manager = None
        
        # Workflow state
        self.current_trace_id = None
        self.current_workflow = None
        self.agent_spans = {}
        
        print(f"Phase 4 Integrated System initialized with features:")
        print(f"  - Adaptive Orchestration: {self.adaptive_orchestrator is not None}")
        print(f"  - Observability Platform: {self.observability is not None}")
        print(f"  - Self-Healing System: {self.self_healer is not None}")
    
    async def orchestrate_workflow(self, 
                                  requirements: Dict[str, Any],
                                  available_agents: List[str],
                                  agent_runner: Any = None) -> Dict[str, Any]:
        """
        Orchestrate a complete workflow with Phase 4 features
        
        Args:
            requirements: Project requirements
            available_agents: List of available agent names
            agent_runner: Agent runner instance
            
        Returns:
            Workflow execution results
        """
        workflow_start = time.time()
        
        # Start observability trace
        if self.observability:
            self.current_trace_id = self.observability.start_trace(
                "workflow_orchestration",
                {"requirements": len(requirements.get("features", [])),
                 "agents": len(available_agents)}
            )
        
        # Initialize workflow result
        result = {
            "success": False,
            "agents_executed": [],
            "errors": [],
            "metrics": {},
            "optimizations_applied": [],
            "healing_actions": []
        }
        
        try:
            # Step 1: Intelligent agent selection
            if self.adaptive_orchestrator:
                self._log("Selecting optimal agents using ML...", LogLevel.INFO)
                selected_agents = self.adaptive_orchestrator.select_optimal_agents(
                    requirements, available_agents
                )
                
                # Predict workload
                workload = self.adaptive_orchestrator.predict_workload(requirements)
                result["metrics"]["predicted_duration"] = workload.estimated_duration
                result["metrics"]["predicted_cost"] = workload.estimated_cost
                
                self._log(f"Selected {len(selected_agents)} agents", LogLevel.INFO)
            else:
                # Fallback to all available agents
                selected_agents = available_agents
            
            # Step 2: Optimize parallel execution
            if self.adaptive_orchestrator:
                execution_groups = self.adaptive_orchestrator.optimize_parallel_execution(
                    selected_agents
                )
                self._log(f"Organized into {len(execution_groups)} execution groups", LogLevel.INFO)
            else:
                # Simple sequential execution
                execution_groups = [[agent] for agent in selected_agents]
            
            # Step 3: Execute agents with monitoring
            context = AgentContext(
                project_requirements=requirements,
                completed_tasks=[],
                artifacts={},
                decisions=[],
                current_phase="execution"
            )
            
            for group_idx, agent_group in enumerate(execution_groups):
                self._log(f"Executing group {group_idx + 1}: {agent_group}", LogLevel.INFO)
                
                # Execute agents in parallel within group
                group_tasks = []
                for agent_name in agent_group:
                    task = self._execute_agent_with_monitoring(
                        agent_name, agent_runner, context, requirements
                    )
                    group_tasks.append(task)
                
                # Wait for group to complete
                group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
                
                # Process results
                for agent_name, agent_result in zip(agent_group, group_results):
                    if isinstance(agent_result, Exception):
                        result["errors"].append({
                            "agent": agent_name,
                            "error": str(agent_result)
                        })
                        
                        # Apply self-healing
                        if self.self_healer:
                            healing = self._apply_healing(agent_name, agent_result, context)
                            if healing:
                                result["healing_actions"].append(healing)
                    else:
                        result["agents_executed"].append(agent_name)
                        
                        # Update adaptive orchestrator with performance
                        if self.adaptive_orchestrator and agent_result:
                            self._update_agent_performance(agent_name, agent_result)
            
            # Step 4: Analyze and optimize
            if result["errors"]:
                # Detect error patterns
                if self.self_healer:
                    patterns = self.self_healer.detect_error_patterns(result["errors"])
                    self._log(f"Detected {len(patterns)} error patterns", LogLevel.WARNING)
                
                # Suggest optimizations
                optimizations = self._generate_optimizations(result)
                result["optimizations_applied"] = optimizations
            
            # Step 5: Update knowledge base
            if self.self_healer:
                self._update_knowledge_base(result)
            
            # Calculate final metrics
            workflow_duration = time.time() - workflow_start
            result["metrics"]["actual_duration"] = workflow_duration
            result["metrics"]["success_rate"] = len(result["agents_executed"]) / len(selected_agents) if selected_agents else 0
            result["success"] = result["metrics"]["success_rate"] > 0.8
            
            # Record workflow for learning
            if self.adaptive_orchestrator:
                self.adaptive_orchestrator.record_workflow_execution({
                    "num_requirements": len(requirements.get("features", [])),
                    "num_agents": len(selected_agents),
                    "total_duration": workflow_duration,
                    "success_rate": result["metrics"]["success_rate"],
                    "has_ai_requirements": any("ai" in str(f).lower() for f in requirements.get("features", [])),
                    "has_frontend_requirements": any("ui" in str(f).lower() or "frontend" in str(f).lower() for f in requirements.get("features", [])),
                    "has_database_requirements": any("database" in str(f).lower() or "data" in str(f).lower() for f in requirements.get("features", []))
                })
            
        except Exception as e:
            self._log(f"Workflow failed: {str(e)}", LogLevel.ERROR)
            result["errors"].append({"type": "workflow_error", "error": str(e)})
        
        finally:
            # End observability trace
            if self.observability and self.current_trace_id:
                # End any remaining spans
                for span_id in list(self.agent_spans.values()):
                    self.observability.end_span(span_id)
                
                # Get performance insights
                if self.observability:
                    insights = self.observability.get_performance_insights()
                    result["metrics"]["insights"] = insights
        
        return result
    
    async def _execute_agent_with_monitoring(self, agent_name: str, 
                                            agent_runner: Any,
                                            context: AgentContext,
                                            requirements: Dict) -> Dict[str, Any]:
        """Execute an agent with full monitoring and tracing"""
        agent_start = time.time()
        
        # Start span for agent
        span_id = None
        if self.observability and self.current_trace_id:
            span_id = self.observability.start_span(
                self.current_trace_id,
                f"agent_{agent_name}",
                tags={"agent": agent_name}
            )
            self.agent_spans[agent_name] = span_id
        
        result = {
            "agent": agent_name,
            "success": False,
            "duration": 0,
            "error": None
        }
        
        try:
            # Get dynamic timeout
            timeout = 300
            if self.adaptive_orchestrator:
                timeout = self.adaptive_orchestrator.get_dynamic_timeout(agent_name)
            
            self._log(f"Executing {agent_name} with timeout {timeout}s", LogLevel.INFO)
            
            # Execute agent (simplified - would use actual agent_runner)
            if agent_runner:
                # This would be the actual agent execution
                # For now, simulate with sleep
                await asyncio.sleep(2)
                result["success"] = True
            else:
                # Simulate execution
                await asyncio.sleep(2)
                result["success"] = True
            
            # Record metrics
            if self.observability:
                self.observability.record_metric(
                    "agent_execution_time",
                    time.time() - agent_start,
                    tags={"agent": agent_name}
                )
            
        except Exception as e:
            result["error"] = str(e)
            self._log(f"Agent {agent_name} failed: {str(e)}", LogLevel.ERROR)
            
            # Record error
            if self.observability:
                self.observability.record_metric(
                    "agent_errors",
                    1,
                    tags={"agent": agent_name, "error_type": type(e).__name__}
                )
        
        finally:
            result["duration"] = time.time() - agent_start
            
            # End span
            if self.observability and span_id:
                self.observability.end_span(
                    span_id,
                    error=result.get("error"),
                    tags={"duration": result["duration"], "success": result["success"]}
                )
                del self.agent_spans[agent_name]
        
        return result
    
    def _apply_healing(self, agent_name: str, error: Exception, 
                      context: Dict) -> Optional[Dict]:
        """Apply self-healing for agent error"""
        if not self.self_healer:
            return None
        
        error_dict = {
            "message": str(error),
            "type": type(error).__name__,
            "agent": agent_name,
            "timestamp": time.time()
        }
        
        healing = self.self_healer.apply_auto_healing(
            error_dict, agent_name, context
        )
        
        if healing:
            self._log(f"Applied healing: {healing['type']}", LogLevel.INFO)
        
        return healing
    
    def _update_agent_performance(self, agent_name: str, result: Dict):
        """Update adaptive orchestrator with agent performance"""
        if not self.adaptive_orchestrator:
            return
        
        self.adaptive_orchestrator.update_agent_performance(
            agent_name=agent_name,
            success=result.get("success", False),
            execution_time=result.get("duration", 0),
            quality_score=0.9 if result.get("success") else 0.3,
            failure_reason=result.get("error")
        )
    
    def _generate_optimizations(self, workflow_result: Dict) -> List[Dict]:
        """Generate optimization recommendations"""
        optimizations = []
        
        # Get recommendations from self-healer
        if self.self_healer:
            healing_recs = self.self_healer.get_healing_recommendations()
            
            # Convert to optimization format
            for prompt_opt in healing_recs.get("prompt_optimizations", []):
                optimizations.append({
                    "type": "prompt_optimization",
                    "agent": prompt_opt["agent"],
                    "action": prompt_opt["reason"],
                    "expected_improvement": prompt_opt["expected_improvement"]
                })
            
            for config_tune in healing_recs.get("config_tunes", []):
                optimizations.append({
                    "type": "configuration",
                    "parameter": config_tune["parameter"],
                    "recommendation": config_tune["recommended"],
                    "reason": config_tune["reason"]
                })
        
        # Get recommendations from adaptive orchestrator
        if self.adaptive_orchestrator:
            orchestrator_recs = self.adaptive_orchestrator.get_optimization_recommendations()
            
            for rec in orchestrator_recs:
                optimizations.append({
                    "type": rec["type"],
                    "action": rec["action"],
                    "reason": rec.get("reason", "")
                })
        
        return optimizations
    
    def _update_knowledge_base(self, workflow_result: Dict):
        """Update knowledge base with learnings"""
        if not self.self_healer:
            return
        
        # Add successful patterns
        if workflow_result["success"]:
            self.self_healer.update_knowledge_base(
                category="best_practice",
                title=f"Successful workflow pattern",
                description=f"Workflow with {len(workflow_result['agents_executed'])} agents",
                solution="Follow this agent execution pattern for similar requirements",
                examples=[{
                    "agents": workflow_result["agents_executed"],
                    "success_rate": workflow_result["metrics"]["success_rate"]
                }]
            )
        
        # Add error fixes
        for error in workflow_result.get("errors", []):
            if "healing_actions" in workflow_result:
                for healing in workflow_result["healing_actions"]:
                    if healing.get("confidence", 0) > 0.7:
                        self.self_healer.update_knowledge_base(
                            category="error_fix",
                            title=f"Fix for {error.get('type', 'error')}",
                            description=error.get("error", ""),
                            solution=healing.get("action", healing.get("solution", "")),
                            examples=[{"agent": error.get("agent")}]
                        )
    
    def _log(self, message: str, level: LogLevel = None):
        """Log message to observability platform"""
        if level is None:
            level = LogLevel.INFO
        
        if self.observability:
            self.observability.log(
                level=level,
                message=message,
                source="phase4_integration",
                trace_id=self.current_trace_id
            )
        else:
            print(f"[{level.value}] {message}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        health = {
            "status": "healthy",
            "components": {},
            "metrics": {},
            "recommendations": []
        }
        
        # Check adaptive orchestrator
        if self.adaptive_orchestrator:
            perf_summary = self.adaptive_orchestrator.get_performance_summary()
            health["components"]["adaptive_orchestrator"] = {
                "status": "healthy",
                "total_agents": perf_summary["total_agents"],
                "success_rate": perf_summary["overall_success_rate"],
                "optimization_opportunities": perf_summary["optimization_opportunities"]
            }
            health["metrics"]["agent_success_rate"] = perf_summary["overall_success_rate"]
        
        # Check observability
        if self.observability:
            insights = self.observability.get_performance_insights()
            health["components"]["observability"] = {
                "status": "healthy",
                "total_traces": insights["dashboard_metrics"]["total_traces"],
                "active_traces": insights["dashboard_metrics"]["active_traces"],
                "error_count": insights["dashboard_metrics"]["error_count"]
            }
            health["metrics"]["avg_response_time"] = insights["dashboard_metrics"]["avg_response_time"]
            health["recommendations"].extend(insights.get("recommendations", []))
        
        # Check self-healer
        if self.self_healer:
            healing_recs = self.self_healer.get_healing_recommendations()
            health["components"]["self_healer"] = {
                "status": "healthy",
                "error_patterns": healing_recs["summary"]["total_error_patterns"],
                "knowledge_base_size": healing_recs["summary"]["knowledge_base_size"],
                "healing_actions": healing_recs["summary"]["healing_actions_taken"]
            }
            
            # Add critical recommendations
            if healing_recs["summary"]["agents_needing_retraining"] > 0:
                health["recommendations"].append({
                    "type": "retraining",
                    "message": f"{healing_recs['summary']['agents_needing_retraining']} agents need retraining"
                })
        
        # Determine overall health
        if health["metrics"].get("agent_success_rate", 1.0) < 0.7:
            health["status"] = "degraded"
        elif health["metrics"].get("avg_response_time", 0) > 30:
            health["status"] = "slow"
        elif len(health["recommendations"]) > 5:
            health["status"] = "needs_attention"
        
        return health
    
    def export_analytics(self, output_dir: str = "analytics"):
        """Export comprehensive analytics and reports"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export traces
        if self.observability:
            self.observability.export_traces(
                output_path / f"traces_{timestamp}.json",
                format="json"
            )
        
        # Export performance data
        if self.adaptive_orchestrator:
            perf_data = {
                "summary": self.adaptive_orchestrator.get_performance_summary(),
                "recommendations": self.adaptive_orchestrator.get_optimization_recommendations(),
                "agent_metrics": {}
            }
            
            for agent_name, metrics in self.adaptive_orchestrator.agent_metrics.items():
                perf_data["agent_metrics"][agent_name] = {
                    "success_rate": metrics.success_rate,
                    "avg_execution_time": metrics.avg_execution_time,
                    "trend": metrics.get_trend()
                }
            
            with open(output_path / f"performance_{timestamp}.json", 'w') as f:
                json.dump(perf_data, f, indent=2)
        
        # Export healing data
        if self.self_healer:
            healing_data = self.self_healer.get_healing_recommendations()
            
            with open(output_path / f"healing_{timestamp}.json", 'w') as f:
                json.dump(healing_data, f, indent=2)
        
        print(f"Analytics exported to {output_path}")
    
    async def shutdown(self):
        """Gracefully shutdown Phase 4 systems"""
        self._log("Shutting down Phase 4 systems...", LogLevel.INFO)
        
        # Save adaptive orchestrator data
        if self.adaptive_orchestrator:
            self.adaptive_orchestrator._save_history()
        
        # Save self-healer data
        if self.self_healer:
            self.self_healer._save_knowledge_base()
            self.self_healer._save_healing_history()
        
        # Export final analytics
        self.export_analytics()
        
        self._log("Phase 4 shutdown complete", LogLevel.INFO)


# Example usage
if __name__ == "__main__":
    async def demo():
        # Create Phase 4 integrated system
        config = Phase4Config(
            enable_adaptive_orchestration=True,
            enable_observability=True,
            enable_self_healing=True,
            enable_auto_fix=True,
            enable_auto_tune=True
        )
        
        system = Phase4IntegratedSystem(config)
        
        # Example requirements
        requirements = {
            "project": "AI-Powered Task Manager",
            "features": [
                "User authentication",
                "Task CRUD operations",
                "AI-powered task categorization",
                "Real-time notifications",
                "Analytics dashboard"
            ]
        }
        
        # Available agents
        available_agents = [
            "project-architect",
            "rapid-builder",
            "frontend-specialist",
            "ai-specialist",
            "database-expert",
            "quality-guardian",
            "devops-engineer"
        ]
        
        # Run orchestration
        print("\nOrchestrating workflow...")
        result = await system.orchestrate_workflow(requirements, available_agents)
        
        print(f"\nWorkflow Result:")
        print(f"  Success: {result['success']}")
        print(f"  Agents Executed: {len(result['agents_executed'])}")
        print(f"  Errors: {len(result['errors'])}")
        print(f"  Success Rate: {result['metrics'].get('success_rate', 0):.1%}")
        
        # Get system health
        print("\nSystem Health:")
        health = system.get_system_health()
        print(f"  Status: {health['status']}")
        print(f"  Components: {len(health['components'])} active")
        print(f"  Recommendations: {len(health['recommendations'])}")
        
        # Export analytics
        system.export_analytics()
        
        # Shutdown
        await system.shutdown()
    
    # Run demo
    asyncio.run(demo())