#!/usr/bin/env python3
"""
Adaptive Orchestrator - Intelligent agent selection with machine learning
Analyzes historical performance to optimize agent selection and execution
"""

import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import statistics

# Try importing sklearn for ML features
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: scikit-learn not installed. ML features will use heuristics.")

@dataclass
class AgentPerformanceMetrics:
    """Historical performance metrics for an agent"""
    agent_name: str
    success_count: int = 0
    failure_count: int = 0
    total_executions: int = 0
    avg_execution_time: float = 0.0
    avg_token_usage: int = 0
    avg_cost: float = 0.0
    success_rate: float = 0.0
    failure_patterns: Dict[str, int] = field(default_factory=dict)
    requirement_types_handled: Dict[str, int] = field(default_factory=dict)
    avg_quality_score: float = 0.0
    recent_performances: List[float] = field(default_factory=list)  # Last 10 performance scores
    
    def update(self, success: bool, execution_time: float, tokens: int = 0, 
               cost: float = 0.0, quality_score: float = 1.0, 
               failure_reason: str = None, requirement_type: str = None):
        """Update metrics with new execution data"""
        self.total_executions += 1
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if failure_reason:
                self.failure_patterns[failure_reason] = self.failure_patterns.get(failure_reason, 0) + 1
        
        # Update running averages
        self.avg_execution_time = (
            (self.avg_execution_time * (self.total_executions - 1) + execution_time) 
            / self.total_executions
        )
        self.avg_token_usage = int(
            (self.avg_token_usage * (self.total_executions - 1) + tokens) 
            / self.total_executions
        )
        self.avg_cost = (
            (self.avg_cost * (self.total_executions - 1) + cost) 
            / self.total_executions
        )
        self.avg_quality_score = (
            (self.avg_quality_score * (self.total_executions - 1) + quality_score) 
            / self.total_executions
        )
        
        # Track requirement types
        if requirement_type:
            self.requirement_types_handled[requirement_type] = \
                self.requirement_types_handled.get(requirement_type, 0) + 1
        
        # Update success rate
        self.success_rate = self.success_count / self.total_executions if self.total_executions > 0 else 0
        
        # Track recent performances (keep last 10)
        self.recent_performances.append(quality_score if success else 0.0)
        if len(self.recent_performances) > 10:
            self.recent_performances.pop(0)
    
    def get_trend(self) -> str:
        """Analyze recent performance trend"""
        if len(self.recent_performances) < 3:
            return "insufficient_data"
        
        recent_avg = statistics.mean(self.recent_performances[-5:]) if len(self.recent_performances) >= 5 else statistics.mean(self.recent_performances)
        older_avg = statistics.mean(self.recent_performances[:-5]) if len(self.recent_performances) > 5 else 0
        
        if recent_avg > older_avg * 1.1:
            return "improving"
        elif recent_avg < older_avg * 0.9:
            return "degrading"
        else:
            return "stable"

@dataclass
class WorkloadPrediction:
    """Predicted workload and resource requirements"""
    estimated_agents: int
    estimated_duration: float
    estimated_cost: float
    estimated_tokens: int
    confidence: float
    parallel_opportunities: List[List[str]]
    bottleneck_agents: List[str]

class AdaptiveOrchestrator:
    """
    Intelligent orchestration with ML-based optimization
    Features:
    - Machine learning for agent selection
    - Historical performance analysis
    - Dynamic timeout adjustment
    - Resource optimization
    - Parallel execution optimizer
    """
    
    def __init__(self, history_path: str = "data/agent_history.json",
                 ml_model_path: str = "models/agent_selector.pkl"):
        self.history_path = Path(history_path)
        self.ml_model_path = Path(ml_model_path)
        self.agent_metrics: Dict[str, AgentPerformanceMetrics] = {}
        self.workflow_history: List[Dict] = []
        self.ml_model = None
        self.scaler = None
        
        # Dynamic configuration
        self.dynamic_timeouts: Dict[str, float] = {}
        self.parallel_threshold = 3  # Max parallel agents
        self.resource_limits = {
            "max_tokens_per_minute": 100000,
            "max_cost_per_hour": 10.0,
            "max_concurrent_agents": 5
        }
        
        # Load historical data
        self._load_history()
        
        # Initialize ML model if available
        if HAS_SKLEARN:
            self._initialize_ml_model()
    
    def _load_history(self):
        """Load historical performance data"""
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r') as f:
                    data = json.load(f)
                    
                # Reconstruct agent metrics
                for agent_name, metrics_data in data.get("agent_metrics", {}).items():
                    metrics = AgentPerformanceMetrics(agent_name)
                    for key, value in metrics_data.items():
                        if hasattr(metrics, key):
                            setattr(metrics, key, value)
                    self.agent_metrics[agent_name] = metrics
                
                self.workflow_history = data.get("workflow_history", [])
                self.dynamic_timeouts = data.get("dynamic_timeouts", {})
                
            except Exception as e:
                print(f"Warning: Could not load history: {e}")
    
    def _save_history(self):
        """Save historical performance data"""
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Serialize agent metrics
            metrics_data = {}
            for agent_name, metrics in self.agent_metrics.items():
                metrics_data[agent_name] = {
                    "success_count": metrics.success_count,
                    "failure_count": metrics.failure_count,
                    "total_executions": metrics.total_executions,
                    "avg_execution_time": metrics.avg_execution_time,
                    "avg_token_usage": metrics.avg_token_usage,
                    "avg_cost": metrics.avg_cost,
                    "success_rate": metrics.success_rate,
                    "failure_patterns": metrics.failure_patterns,
                    "requirement_types_handled": metrics.requirement_types_handled,
                    "avg_quality_score": metrics.avg_quality_score,
                    "recent_performances": metrics.recent_performances
                }
            
            data = {
                "agent_metrics": metrics_data,
                "workflow_history": self.workflow_history[-100:],  # Keep last 100 workflows
                "dynamic_timeouts": self.dynamic_timeouts,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.history_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save history: {e}")
    
    def _initialize_ml_model(self):
        """Initialize or load ML model for agent selection"""
        if not HAS_SKLEARN:
            return
        
        try:
            if self.ml_model_path.exists():
                import pickle
                with open(self.ml_model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.ml_model = model_data['model']
                    self.scaler = model_data['scaler']
            else:
                # Create new model
                self.ml_model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                self.scaler = StandardScaler()
                
                # Train on historical data if available
                if len(self.workflow_history) > 10:
                    self._train_ml_model()
                    
        except Exception as e:
            print(f"Warning: Could not initialize ML model: {e}")
            self.ml_model = None
    
    def _train_ml_model(self):
        """Train ML model on historical workflow data"""
        if not HAS_SKLEARN or not self.workflow_history:
            return
        
        try:
            # Prepare training data
            X = []
            y = []
            
            for workflow in self.workflow_history:
                features = self._extract_workflow_features(workflow)
                if features:
                    X.append(features)
                    # Binary classification: successful workflow or not
                    y.append(1 if workflow.get("success_rate", 0) > 0.8 else 0)
            
            if len(X) > 10:
                X = self.scaler.fit_transform(X)
                self.ml_model.fit(X, y)
                
                # Save model
                self._save_ml_model()
                
        except Exception as e:
            print(f"Warning: Could not train ML model: {e}")
    
    def _save_ml_model(self):
        """Save trained ML model"""
        if not HAS_SKLEARN or not self.ml_model:
            return
        
        try:
            import pickle
            self.ml_model_path.parent.mkdir(parents=True, exist_ok=True)
            
            model_data = {
                'model': self.ml_model,
                'scaler': self.scaler,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.ml_model_path, 'wb') as f:
                pickle.dump(model_data, f)
                
        except Exception as e:
            print(f"Warning: Could not save ML model: {e}")
    
    def _extract_workflow_features(self, workflow: Dict) -> Optional[List[float]]:
        """Extract features from workflow for ML model"""
        try:
            features = [
                workflow.get("num_requirements", 0),
                workflow.get("num_agents", 0),
                workflow.get("total_duration", 0),
                workflow.get("total_cost", 0),
                workflow.get("parallel_executions", 0),
                workflow.get("retry_count", 0),
                len(workflow.get("requirement_types", [])),
                workflow.get("complexity_score", 1),
                1 if workflow.get("has_ai_requirements", False) else 0,
                1 if workflow.get("has_frontend_requirements", False) else 0,
                1 if workflow.get("has_database_requirements", False) else 0
            ]
            return features
        except:
            return None
    
    def select_optimal_agents(self, requirements: Dict[str, Any], 
                            available_agents: List[str]) -> List[str]:
        """
        Select optimal agents for requirements using ML or heuristics
        
        Args:
            requirements: Project requirements dictionary
            available_agents: List of available agent names
            
        Returns:
            Ordered list of selected agents
        """
        # Extract requirement features
        requirement_types = self._analyze_requirement_types(requirements)
        
        if HAS_SKLEARN and self.ml_model:
            # Use ML model for selection
            selected = self._ml_agent_selection(requirements, requirement_types, available_agents)
        else:
            # Use heuristic-based selection
            selected = self._heuristic_agent_selection(requirement_types, available_agents)
        
        # Apply performance-based filtering
        selected = self._filter_by_performance(selected, requirement_types)
        
        return selected
    
    def _analyze_requirement_types(self, requirements: Dict) -> Dict[str, bool]:
        """Analyze requirement types from project requirements"""
        req_text = json.dumps(requirements).lower()
        
        return {
            "frontend": any(kw in req_text for kw in ["ui", "frontend", "react", "interface", "design"]),
            "backend": any(kw in req_text for kw in ["api", "backend", "server", "endpoint", "rest"]),
            "database": any(kw in req_text for kw in ["database", "sql", "postgres", "mongodb", "redis"]),
            "ai": any(kw in req_text for kw in ["ai", "ml", "gpt", "llm", "machine learning", "neural"]),
            "devops": any(kw in req_text for kw in ["docker", "deploy", "ci/cd", "kubernetes", "aws"]),
            "security": any(kw in req_text for kw in ["security", "auth", "encryption", "jwt", "oauth"]),
            "performance": any(kw in req_text for kw in ["performance", "optimize", "cache", "speed", "scale"]),
            "testing": any(kw in req_text for kw in ["test", "quality", "coverage", "pytest", "jest"])
        }
    
    def _ml_agent_selection(self, requirements: Dict, requirement_types: Dict, 
                           available_agents: List[str]) -> List[str]:
        """Use ML model to select agents"""
        try:
            # Create feature vector
            features = [
                len(requirements.get("features", [])),
                len(available_agents),
                0,  # Will be filled with estimated duration
                0,  # Will be filled with estimated cost
                0,  # Parallel opportunities
                0,  # Retry count
                sum(requirement_types.values()),
                requirements.get("complexity", 1),
                1 if requirement_types.get("ai") else 0,
                1 if requirement_types.get("frontend") else 0,
                1 if requirement_types.get("database") else 0
            ]
            
            # Get prediction
            X = self.scaler.transform([features])
            confidence = self.ml_model.predict_proba(X)[0][1]
            
            # Use confidence to adjust agent selection
            if confidence > 0.7:
                # High confidence - use specialized agents
                return self._select_specialized_agents(requirement_types, available_agents)
            else:
                # Low confidence - use general agents with more coverage
                return self._select_general_agents(requirement_types, available_agents)
                
        except Exception as e:
            print(f"ML selection failed: {e}, falling back to heuristics")
            return self._heuristic_agent_selection(requirement_types, available_agents)
    
    def _heuristic_agent_selection(self, requirement_types: Dict, 
                                  available_agents: List[str]) -> List[str]:
        """Heuristic-based agent selection"""
        selected = []
        
        # Core agents always included
        core_agents = ["project-architect", "rapid-builder", "quality-guardian"]
        selected.extend([a for a in core_agents if a in available_agents])
        
        # Add specialized agents based on requirements
        if requirement_types.get("frontend"):
            if "frontend-specialist" in available_agents:
                selected.append("frontend-specialist")
        
        if requirement_types.get("ai"):
            if "ai-specialist" in available_agents:
                selected.append("ai-specialist")
        
        if requirement_types.get("database"):
            if "database-expert" in available_agents:
                selected.append("database-expert")
        
        if requirement_types.get("devops"):
            if "devops-engineer" in available_agents:
                selected.append("devops-engineer")
        
        if requirement_types.get("performance"):
            if "performance-optimizer" in available_agents:
                selected.append("performance-optimizer")
        
        # Remove duplicates while preserving order
        seen = set()
        selected = [x for x in selected if not (x in seen or seen.add(x))]
        
        return selected
    
    def _select_specialized_agents(self, requirement_types: Dict, 
                                  available_agents: List[str]) -> List[str]:
        """Select specialized agents for high-confidence scenarios"""
        agent_mapping = {
            "frontend": ["frontend-specialist", "ui-designer"],
            "backend": ["rapid-builder", "api-integrator"],
            "database": ["database-expert", "data-architect"],
            "ai": ["ai-specialist", "ml-engineer"],
            "devops": ["devops-engineer", "cloud-architect"],
            "security": ["security-auditor", "quality-guardian"],
            "performance": ["performance-optimizer", "load-tester"],
            "testing": ["quality-guardian", "test-engineer"]
        }
        
        selected = ["project-architect"]  # Always start with architect
        
        for req_type, is_needed in requirement_types.items():
            if is_needed:
                for agent in agent_mapping.get(req_type, []):
                    if agent in available_agents and agent not in selected:
                        selected.append(agent)
        
        return selected
    
    def _select_general_agents(self, requirement_types: Dict, 
                              available_agents: List[str]) -> List[str]:
        """Select general agents for low-confidence scenarios"""
        # Use more general agents that can handle multiple tasks
        general_agents = [
            "project-architect",
            "rapid-builder",
            "quality-guardian",
            "documentation-writer",
            "devops-engineer"
        ]
        
        return [a for a in general_agents if a in available_agents]
    
    def _filter_by_performance(self, agents: List[str], 
                              requirement_types: Dict) -> List[str]:
        """Filter agents based on historical performance"""
        filtered = []
        
        for agent in agents:
            if agent in self.agent_metrics:
                metrics = self.agent_metrics[agent]
                
                # Skip agents with poor recent performance
                if metrics.get_trend() == "degrading" and metrics.success_rate < 0.5:
                    print(f"Skipping {agent} due to degrading performance")
                    continue
                
                # Skip agents that haven't handled these requirement types well
                for req_type in requirement_types:
                    if requirement_types[req_type]:
                        if req_type in metrics.failure_patterns and \
                           metrics.failure_patterns[req_type] > 3:
                            print(f"Skipping {agent} due to repeated failures with {req_type}")
                            continue
            
            filtered.append(agent)
        
        return filtered
    
    def get_dynamic_timeout(self, agent_name: str, default_timeout: float = 300) -> float:
        """
        Get dynamically adjusted timeout for an agent
        
        Args:
            agent_name: Name of the agent
            default_timeout: Default timeout in seconds
            
        Returns:
            Adjusted timeout value
        """
        # Check if we have historical data
        if agent_name in self.agent_metrics:
            metrics = self.agent_metrics[agent_name]
            
            # Base timeout on average execution time with buffer
            if metrics.avg_execution_time > 0:
                # Use 2x average time or 1.5x the 95th percentile
                dynamic_timeout = metrics.avg_execution_time * 2
                
                # Adjust based on recent trend
                trend = metrics.get_trend()
                if trend == "degrading":
                    dynamic_timeout *= 1.5  # Give more time if performance is degrading
                elif trend == "improving":
                    dynamic_timeout *= 0.9  # Slightly reduce if improving
                
                # Apply bounds
                dynamic_timeout = max(60, min(dynamic_timeout, 3600))  # Between 1 min and 1 hour
                
                self.dynamic_timeouts[agent_name] = dynamic_timeout
                return dynamic_timeout
        
        # Return cached timeout or default
        return self.dynamic_timeouts.get(agent_name, default_timeout)
    
    def optimize_parallel_execution(self, agents: List[str], 
                                   dependencies: Dict[str, List[str]] = None) -> List[List[str]]:
        """
        Optimize agents for parallel execution
        
        Args:
            agents: List of agents to execute
            dependencies: Optional dependency graph
            
        Returns:
            List of agent groups that can run in parallel
        """
        if not dependencies:
            # No dependencies - create groups based on resource consumption
            return self._group_by_resources(agents)
        
        # Use topological sort with parallelization
        groups = []
        remaining = set(agents)
        completed = set()
        
        while remaining:
            # Find agents that can run now (dependencies satisfied)
            ready = []
            for agent in remaining:
                agent_deps = dependencies.get(agent, [])
                if all(dep in completed for dep in agent_deps):
                    ready.append(agent)
            
            if not ready:
                # Circular dependency or error
                print(f"Warning: Circular dependency detected for agents: {remaining}")
                ready = list(remaining)
            
            # Group ready agents by resource consumption
            grouped = self._group_by_resources(ready)
            
            for group in grouped:
                groups.append(group)
                for agent in group:
                    remaining.discard(agent)
                    completed.add(agent)
            
            # Prevent infinite loop
            if len(groups) > 100:
                print("Warning: Too many execution groups, possible issue with dependencies")
                break
        
        return groups
    
    def _group_by_resources(self, agents: List[str]) -> List[List[str]]:
        """Group agents by resource consumption for parallel execution"""
        # Estimate resource usage for each agent
        heavy_agents = ["ai-specialist", "performance-optimizer", "ml-engineer"]
        medium_agents = ["rapid-builder", "frontend-specialist", "database-expert"]
        light_agents = ["documentation-writer", "api-integrator", "test-writer"]
        
        groups = []
        current_group = []
        current_weight = 0
        max_weight = self.parallel_threshold
        
        for agent in agents:
            # Assign weight based on agent type
            if agent in heavy_agents:
                weight = 3
            elif agent in medium_agents:
                weight = 2
            else:
                weight = 1
            
            if current_weight + weight <= max_weight:
                current_group.append(agent)
                current_weight += weight
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [agent]
                current_weight = weight
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def predict_workload(self, requirements: Dict) -> WorkloadPrediction:
        """
        Predict workload and resource requirements
        
        Args:
            requirements: Project requirements
            
        Returns:
            WorkloadPrediction with estimates
        """
        # Analyze requirements
        num_features = len(requirements.get("features", []))
        requirement_types = self._analyze_requirement_types(requirements)
        num_req_types = sum(requirement_types.values())
        
        # Base estimates
        agents_needed = 3 + num_req_types  # Base 3 + specialized
        
        # Estimate duration based on historical data
        if self.workflow_history:
            similar_workflows = [
                w for w in self.workflow_history 
                if abs(w.get("num_requirements", 0) - num_features) < 3
            ]
            
            if similar_workflows:
                avg_duration = statistics.mean([w.get("total_duration", 300) for w in similar_workflows])
                avg_cost = statistics.mean([w.get("total_cost", 1.0) for w in similar_workflows])
                avg_tokens = int(statistics.mean([w.get("total_tokens", 10000) for w in similar_workflows]))
            else:
                avg_duration = 300 * agents_needed
                avg_cost = 0.1 * agents_needed
                avg_tokens = 5000 * agents_needed
        else:
            avg_duration = 300 * agents_needed
            avg_cost = 0.1 * agents_needed
            avg_tokens = 5000 * agents_needed
        
        # Identify parallel opportunities
        parallel_groups = []
        if requirement_types.get("frontend") and requirement_types.get("backend"):
            parallel_groups.append(["frontend-specialist", "rapid-builder"])
        if requirement_types.get("testing"):
            parallel_groups.append(["quality-guardian", "test-writer"])
        
        # Identify potential bottlenecks
        bottlenecks = []
        if requirement_types.get("ai"):
            bottlenecks.append("ai-specialist")  # Usually takes longer
        if num_features > 10:
            bottlenecks.append("project-architect")  # Complex planning
        
        # Calculate confidence based on historical data
        confidence = min(0.9, len(self.workflow_history) / 100) if self.workflow_history else 0.5
        
        return WorkloadPrediction(
            estimated_agents=agents_needed,
            estimated_duration=avg_duration,
            estimated_cost=avg_cost,
            estimated_tokens=avg_tokens,
            confidence=confidence,
            parallel_opportunities=parallel_groups,
            bottleneck_agents=bottlenecks
        )
    
    def update_agent_performance(self, agent_name: str, success: bool,
                                execution_time: float, tokens: int = 0,
                                cost: float = 0.0, quality_score: float = 1.0,
                                failure_reason: str = None, requirement_type: str = None):
        """Update agent performance metrics after execution"""
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentPerformanceMetrics(agent_name)
        
        self.agent_metrics[agent_name].update(
            success=success,
            execution_time=execution_time,
            tokens=tokens,
            cost=cost,
            quality_score=quality_score,
            failure_reason=failure_reason,
            requirement_type=requirement_type
        )
        
        # Periodically save history
        if sum(m.total_executions for m in self.agent_metrics.values()) % 10 == 0:
            self._save_history()
    
    def record_workflow_execution(self, workflow_data: Dict):
        """Record complete workflow execution for learning"""
        self.workflow_history.append({
            **workflow_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Retrain ML model periodically
        if HAS_SKLEARN and len(self.workflow_history) % 20 == 0:
            self._train_ml_model()
        
        self._save_history()
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for system optimization"""
        recommendations = []
        
        # Analyze agent performance
        for agent_name, metrics in self.agent_metrics.items():
            if metrics.total_executions < 5:
                continue
            
            # Recommend removal of consistently failing agents
            if metrics.success_rate < 0.3:
                recommendations.append({
                    "type": "agent_replacement",
                    "agent": agent_name,
                    "reason": f"Low success rate: {metrics.success_rate:.1%}",
                    "action": f"Consider replacing {agent_name} or reviewing its implementation"
                })
            
            # Recommend timeout adjustments
            if metrics.avg_execution_time > 600:
                recommendations.append({
                    "type": "timeout_adjustment",
                    "agent": agent_name,
                    "reason": f"Long average execution time: {metrics.avg_execution_time:.1f}s",
                    "action": f"Increase timeout for {agent_name} to {metrics.avg_execution_time * 2:.0f}s"
                })
            
            # Recommend prompt optimization for degrading agents
            if metrics.get_trend() == "degrading":
                recommendations.append({
                    "type": "prompt_optimization",
                    "agent": agent_name,
                    "reason": "Performance trend is degrading",
                    "action": f"Review and optimize prompts for {agent_name}"
                })
        
        # Analyze workflow patterns
        if len(self.workflow_history) > 10:
            recent_workflows = self.workflow_history[-10:]
            avg_success = statistics.mean([w.get("success_rate", 0) for w in recent_workflows])
            
            if avg_success < 0.7:
                recommendations.append({
                    "type": "workflow_optimization",
                    "reason": f"Low recent success rate: {avg_success:.1%}",
                    "action": "Review workflow orchestration and agent dependencies"
                })
        
        # Resource optimization
        total_cost = sum(w.get("total_cost", 0) for w in self.workflow_history[-10:]) if self.workflow_history else 0
        if total_cost > 50:
            recommendations.append({
                "type": "cost_optimization",
                "reason": f"High recent costs: ${total_cost:.2f}",
                "action": "Consider using more cost-effective models or caching results"
            })
        
        return recommendations
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        summary = {
            "total_agents": len(self.agent_metrics),
            "total_executions": sum(m.total_executions for m in self.agent_metrics.values()),
            "overall_success_rate": 0.0,
            "top_performers": [],
            "worst_performers": [],
            "trends": {},
            "resource_usage": {
                "total_tokens": 0,
                "total_cost": 0.0,
                "avg_execution_time": 0.0
            },
            "optimization_opportunities": len(self.get_optimization_recommendations())
        }
        
        if self.agent_metrics:
            # Calculate overall success rate
            total_success = sum(m.success_count for m in self.agent_metrics.values())
            total_exec = sum(m.total_executions for m in self.agent_metrics.values())
            summary["overall_success_rate"] = total_success / total_exec if total_exec > 0 else 0
            
            # Top and worst performers
            sorted_agents = sorted(
                self.agent_metrics.items(),
                key=lambda x: (x[1].success_rate, x[1].avg_quality_score),
                reverse=True
            )
            
            summary["top_performers"] = [
                {"agent": name, "success_rate": m.success_rate, "quality": m.avg_quality_score}
                for name, m in sorted_agents[:3]
                if m.total_executions >= 3
            ]
            
            summary["worst_performers"] = [
                {"agent": name, "success_rate": m.success_rate, "quality": m.avg_quality_score}
                for name, m in sorted_agents[-3:]
                if m.total_executions >= 3 and m.success_rate < 0.7
            ]
            
            # Trends
            for name, metrics in self.agent_metrics.items():
                trend = metrics.get_trend()
                if trend != "insufficient_data":
                    if trend not in summary["trends"]:
                        summary["trends"][trend] = []
                    summary["trends"][trend].append(name)
            
            # Resource usage
            summary["resource_usage"]["total_tokens"] = sum(
                m.avg_token_usage * m.total_executions 
                for m in self.agent_metrics.values()
            )
            summary["resource_usage"]["total_cost"] = sum(
                m.avg_cost * m.total_executions 
                for m in self.agent_metrics.values()
            )
            summary["resource_usage"]["avg_execution_time"] = statistics.mean(
                [m.avg_execution_time for m in self.agent_metrics.values() if m.total_executions > 0]
            ) if self.agent_metrics else 0
        
        return summary


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        # Create adaptive orchestrator
        orchestrator = AdaptiveOrchestrator()
        
        # Example requirements
        requirements = {
            "project": "E-commerce Platform",
            "features": [
                "User authentication",
                "Product catalog",
                "Shopping cart",
                "Payment integration",
                "AI-powered recommendations"
            ],
            "tech_stack": {
                "frontend": "React",
                "backend": "FastAPI",
                "database": "PostgreSQL"
            }
        }
        
        # Available agents
        available_agents = [
            "project-architect",
            "rapid-builder",
            "frontend-specialist",
            "ai-specialist",
            "database-expert",
            "quality-guardian",
            "devops-engineer",
            "api-integrator",
            "performance-optimizer"
        ]
        
        # Select optimal agents
        print("Selecting optimal agents...")
        selected_agents = orchestrator.select_optimal_agents(requirements, available_agents)
        print(f"Selected agents: {selected_agents}")
        
        # Get dynamic timeouts
        print("\nDynamic timeouts:")
        for agent in selected_agents:
            timeout = orchestrator.get_dynamic_timeout(agent)
            print(f"  {agent}: {timeout:.1f}s")
        
        # Optimize parallel execution
        print("\nParallel execution plan:")
        parallel_groups = orchestrator.optimize_parallel_execution(selected_agents)
        for i, group in enumerate(parallel_groups, 1):
            print(f"  Phase {i}: {', '.join(group)}")
        
        # Predict workload
        print("\nWorkload prediction:")
        prediction = orchestrator.predict_workload(requirements)
        print(f"  Estimated agents: {prediction.estimated_agents}")
        print(f"  Estimated duration: {prediction.estimated_duration:.1f}s")
        print(f"  Estimated cost: ${prediction.estimated_cost:.2f}")
        print(f"  Confidence: {prediction.confidence:.1%}")
        
        # Simulate execution and update metrics
        print("\nSimulating execution...")
        for agent in selected_agents:
            # Simulate execution
            success = True if agent != "ai-specialist" or orchestrator.agent_metrics.get(agent, AgentPerformanceMetrics(agent)).total_executions % 3 != 2 else False
            execution_time = 120 + (hash(agent) % 180)
            tokens = 5000 + (hash(agent) % 10000)
            cost = tokens * 0.00002
            quality_score = 0.9 if success else 0.3
            
            orchestrator.update_agent_performance(
                agent_name=agent,
                success=success,
                execution_time=execution_time,
                tokens=tokens,
                cost=cost,
                quality_score=quality_score,
                failure_reason="timeout" if not success else None,
                requirement_type="ai" if "ai" in agent else "general"
            )
        
        # Record workflow
        orchestrator.record_workflow_execution({
            "num_requirements": len(requirements.get("features", [])),
            "num_agents": len(selected_agents),
            "total_duration": sum(120 + (hash(a) % 180) for a in selected_agents),
            "total_cost": sum((5000 + (hash(a) % 10000)) * 0.00002 for a in selected_agents),
            "success_rate": 0.89,
            "has_ai_requirements": True,
            "has_frontend_requirements": True,
            "has_database_requirements": True
        })
        
        # Get recommendations
        print("\nOptimization recommendations:")
        recommendations = orchestrator.get_optimization_recommendations()
        for rec in recommendations[:3]:
            print(f"  - {rec['type']}: {rec['action']}")
        
        # Get performance summary
        print("\nPerformance summary:")
        summary = orchestrator.get_performance_summary()
        print(f"  Total executions: {summary['total_executions']}")
        print(f"  Overall success rate: {summary['overall_success_rate']:.1%}")
        print(f"  Optimization opportunities: {summary['optimization_opportunities']}")
    
    # Run demo
    asyncio.run(demo())