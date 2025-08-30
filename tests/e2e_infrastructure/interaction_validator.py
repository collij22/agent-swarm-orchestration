#!/usr/bin/env python3
"""
Agent Interaction Validator for E2E Testing

Features:
- Inter-agent communication testing
- Context passing validation  
- Artifact dependency verification
- Tool usage pattern analysis
- Communication protocol validation
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import sys

# Optional imports for visualization
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False
    # Create dummy classes if not available
    class nx:
        @staticmethod
        def DiGraph():
            return DummyGraph()
    
    class DummyGraph:
        def add_edge(self, *args, **kwargs): pass
        def nodes(self): return []
        def edges(self, data=False): return []
        def get_edge_data(self, *args): return {}
        def degree(self, node): return 0
        def in_degree(self, node): return 0
        def out_degree(self, node): return 0
        def predecessors(self, node): return []

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.agent_runtime import AgentContext

class InteractionType(Enum):
    """Types of agent interactions"""
    SEQUENTIAL = "sequential"      # Agent B depends on Agent A completion
    PARALLEL = "parallel"          # Agents work simultaneously
    CONDITIONAL = "conditional"    # Agent B executes based on Agent A result
    FEEDBACK = "feedback"          # Agent B provides feedback to Agent A
    COLLABORATIVE = "collaborative" # Agents work together on same task

class CommunicationProtocol(Enum):
    """Communication protocols between agents"""
    CONTEXT_PASSING = "context_passing"    # Via shared context
    ARTIFACT_SHARING = "artifact_sharing"  # Via created artifacts
    TOOL_MEDIATED = "tool_mediated"       # Via inter-agent tools
    FILE_BASED = "file_based"             # Via file system
    MESSAGE_BASED = "message_based"       # Via message queue

@dataclass
class AgentInteraction:
    """Represents an interaction between agents"""
    id: str
    source_agent: str
    target_agent: str
    interaction_type: InteractionType
    protocol: CommunicationProtocol
    timestamp: datetime
    data_transferred: Dict[str, Any] = field(default_factory=dict)
    artifacts_shared: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    success: bool = False
    validation_errors: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the interaction"""
        errors = []
        
        # Check if source and target are different
        if self.source_agent == self.target_agent:
            errors.append(f"Self-interaction detected: {self.source_agent}")
            
        # Check if data was transferred for non-parallel interactions
        if self.interaction_type != InteractionType.PARALLEL and not self.data_transferred:
            errors.append(f"No data transferred in {self.interaction_type.value} interaction")
            
        # Check protocol-specific requirements
        if self.protocol == CommunicationProtocol.ARTIFACT_SHARING and not self.artifacts_shared:
            errors.append("Artifact sharing protocol used but no artifacts shared")
            
        if self.protocol == CommunicationProtocol.TOOL_MEDIATED and not self.tools_used:
            errors.append("Tool-mediated protocol used but no tools invoked")
            
        # Check latency
        if self.latency_ms > 5000:  # 5 second threshold
            errors.append(f"High latency detected: {self.latency_ms}ms")
            
        self.validation_errors = errors
        self.success = len(errors) == 0
        
        return self.success, errors

@dataclass 
class DependencyChain:
    """Represents a chain of dependencies between agents"""
    id: str
    agents: List[str]
    artifacts: List[str]
    critical_path: List[str]
    total_latency_ms: float = 0.0
    broken_links: List[Tuple[str, str]] = field(default_factory=list)
    
    def is_complete(self) -> bool:
        """Check if dependency chain is complete"""
        return len(self.broken_links) == 0
        
    def get_bottlenecks(self) -> List[str]:
        """Identify bottleneck agents in the chain"""
        # Agents that appear multiple times in critical path
        from collections import Counter
        agent_counts = Counter(self.critical_path)
        return [agent for agent, count in agent_counts.items() if count > 1]

@dataclass
class ToolUsagePattern:
    """Pattern of tool usage by agents"""
    agent_name: str
    tool_name: str
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_execution_time_ms: float = 0.0
    common_parameters: Dict[str, Any] = field(default_factory=dict)
    error_patterns: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate tool success rate"""
        total = self.success_count + self.failure_count
        return (self.success_count / total * 100) if total > 0 else 0

class AgentInteractionValidator:
    """Validates agent interactions and communication patterns"""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize the validator
        
        Args:
            session_id: Optional session ID for tracking
        """
        self.session_id = session_id or f"session_{int(time.time())}"
        self.interactions: List[AgentInteraction] = []
        self.dependency_chains: List[DependencyChain] = []
        self.tool_patterns: Dict[str, ToolUsagePattern] = {}
        self.interaction_graph = nx.DiGraph()
        
        # Validation rules
        self.max_chain_depth = 10  # Maximum dependency chain depth
        self.max_parallel_agents = 5  # Maximum parallel agents
        self.required_tools = ["write_file", "record_decision", "complete_task"]
        
        # Metrics
        self.metrics = {
            "total_interactions": 0,
            "successful_interactions": 0,
            "failed_interactions": 0,
            "avg_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "context_size_bytes": 0,
            "artifacts_created": 0,
            "tools_invoked": 0,
            "validation_errors": [],
            "dependency_violations": 0,
            "protocol_distribution": {},
            "interaction_type_distribution": {}
        }
        
    def track_interaction(self, interaction: AgentInteraction):
        """Track an agent interaction"""
        # Validate interaction
        success, errors = interaction.validate()
        
        # Record interaction
        self.interactions.append(interaction)
        self.metrics["total_interactions"] += 1
        
        if success:
            self.metrics["successful_interactions"] += 1
        else:
            self.metrics["failed_interactions"] += 1
            self.metrics["validation_errors"].extend(errors)
            
        # Update graph
        self.interaction_graph.add_edge(
            interaction.source_agent,
            interaction.target_agent,
            interaction_type=interaction.interaction_type.value,
            timestamp=interaction.timestamp.isoformat(),
            success=success
        )
        
        # Update metrics
        self._update_metrics(interaction)
        
    def validate_context_passing(self, 
                                context_before: AgentContext,
                                context_after: AgentContext,
                                agent_name: str) -> Tuple[bool, List[str]]:
        """Validate context passing between agents"""
        errors = []
        
        # Check context integrity
        if not context_after:
            errors.append(f"{agent_name}: Context lost after execution")
            return False, errors
            
        # Check if completed tasks were updated
        if agent_name not in context_after.completed_tasks:
            errors.append(f"{agent_name}: Agent not added to completed tasks")
            
        # Check if artifacts were preserved
        before_artifacts = set(context_before.artifacts.keys())
        after_artifacts = set(context_after.artifacts.keys())
        
        if not before_artifacts.issubset(after_artifacts):
            lost_artifacts = before_artifacts - after_artifacts
            errors.append(f"{agent_name}: Lost artifacts: {lost_artifacts}")
            
        # Check if decisions were preserved
        before_decisions = len(context_before.decisions)
        after_decisions = len(context_after.decisions)
        
        if after_decisions < before_decisions:
            errors.append(f"{agent_name}: Lost decisions during execution")
            
        # Check context size growth
        import sys
        context_size = sys.getsizeof(json.dumps(context_after.to_dict()))
        if context_size > 1024 * 1024:  # 1MB limit
            errors.append(f"{agent_name}: Context size exceeds 1MB: {context_size} bytes")
            
        self.metrics["context_size_bytes"] = context_size
        
        return len(errors) == 0, errors
        
    def validate_artifact_dependencies(self,
                                      agent_name: str,
                                      required_artifacts: List[str],
                                      available_artifacts: List[str]) -> Tuple[bool, List[str]]:
        """Validate artifact dependencies for an agent"""
        errors = []
        missing_artifacts = []
        
        for artifact in required_artifacts:
            if artifact not in available_artifacts:
                missing_artifacts.append(artifact)
                
        if missing_artifacts:
            errors.append(f"{agent_name}: Missing required artifacts: {missing_artifacts}")
            self.metrics["dependency_violations"] += 1
            
        return len(errors) == 0, errors
        
    def analyze_tool_usage(self,
                          agent_name: str,
                          tool_name: str,
                          parameters: Dict[str, Any],
                          execution_time_ms: float,
                          success: bool):
        """Analyze tool usage patterns"""
        pattern_key = f"{agent_name}_{tool_name}"
        
        if pattern_key not in self.tool_patterns:
            self.tool_patterns[pattern_key] = ToolUsagePattern(
                agent_name=agent_name,
                tool_name=tool_name
            )
            
        pattern = self.tool_patterns[pattern_key]
        pattern.usage_count += 1
        
        if success:
            pattern.success_count += 1
        else:
            pattern.failure_count += 1
            
        # Update average execution time
        pattern.avg_execution_time_ms = (
            (pattern.avg_execution_time_ms * (pattern.usage_count - 1) + execution_time_ms) /
            pattern.usage_count
        )
        
        # Track common parameters
        for param, value in parameters.items():
            if param not in pattern.common_parameters:
                pattern.common_parameters[param] = []
            pattern.common_parameters[param].append(value)
            
        self.metrics["tools_invoked"] += 1
        
    def build_dependency_chain(self, 
                              start_agent: str,
                              end_agent: str,
                              context: AgentContext) -> DependencyChain:
        """Build a dependency chain between agents"""
        chain_id = f"chain_{start_agent}_{end_agent}"
        
        # Find path in interaction graph
        if HAS_VISUALIZATION:
            try:
                path = nx.shortest_path(self.interaction_graph, start_agent, end_agent)
            except:
                # No path exists
                return DependencyChain(
                    id=chain_id,
                    agents=[start_agent, end_agent],
                    artifacts=[],
                    critical_path=[],
                    broken_links=[(start_agent, end_agent)]
                )
        else:
            # Simplified path finding without networkx
            path = [start_agent, end_agent]
            
        # Collect artifacts along the path
        artifacts = []
        for i in range(len(path) - 1):
            edge_data = self.interaction_graph.get_edge_data(path[i], path[i + 1])
            if edge_data:
                # Find corresponding interaction
                interaction = next(
                    (inter for inter in self.interactions 
                     if inter.source_agent == path[i] and inter.target_agent == path[i + 1]),
                    None
                )
                if interaction:
                    artifacts.extend(interaction.artifacts_shared)
                    
        chain = DependencyChain(
            id=chain_id,
            agents=path,
            artifacts=list(set(artifacts)),
            critical_path=path
        )
        
        self.dependency_chains.append(chain)
        return chain
        
    def validate_communication_protocol(self,
                                       protocol: CommunicationProtocol,
                                       data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate communication protocol usage"""
        errors = []
        
        if protocol == CommunicationProtocol.CONTEXT_PASSING:
            # Validate context structure
            required_fields = ["completed_tasks", "artifacts", "decisions"]
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required context field: {field}")
                    
        elif protocol == CommunicationProtocol.ARTIFACT_SHARING:
            # Validate artifact format
            if "artifacts" not in data or not isinstance(data["artifacts"], list):
                errors.append("Invalid artifact sharing format")
                
        elif protocol == CommunicationProtocol.TOOL_MEDIATED:
            # Validate tool invocation
            if "tool_name" not in data:
                errors.append("Tool name not specified in tool-mediated communication")
                
        elif protocol == CommunicationProtocol.FILE_BASED:
            # Validate file paths
            if "file_paths" not in data:
                errors.append("File paths not specified in file-based communication")
            else:
                for path in data.get("file_paths", []):
                    if not Path(path).exists():
                        errors.append(f"File not found: {path}")
                        
        return len(errors) == 0, errors
        
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in agent interactions"""
        if HAS_VISUALIZATION:
            try:
                cycles = list(nx.simple_cycles(self.interaction_graph))
                return cycles
            except:
                return []
        return []
            
    def identify_isolated_agents(self) -> List[str]:
        """Identify agents that don't interact with others"""
        all_agents = set()
        connected_agents = set()
        
        for interaction in self.interactions:
            all_agents.add(interaction.source_agent)
            all_agents.add(interaction.target_agent)
            connected_agents.add(interaction.source_agent)
            connected_agents.add(interaction.target_agent)
            
        # Find nodes with no edges
        isolated = []
        for node in self.interaction_graph.nodes():
            if self.interaction_graph.degree(node) == 0:
                isolated.append(node)
                
        return isolated
        
    def analyze_interaction_patterns(self) -> Dict[str, Any]:
        """Analyze overall interaction patterns"""
        patterns = {
            "sequential_chains": [],
            "parallel_groups": [],
            "feedback_loops": [],
            "bottleneck_agents": [],
            "isolated_agents": [],
            "circular_dependencies": []
        }
        
        # Sequential chains
        for chain in self.dependency_chains:
            if len(chain.agents) > 2:
                patterns["sequential_chains"].append(chain.agents)
                
        # Parallel groups (agents with same predecessors)
        predecessor_groups = {}
        for node in self.interaction_graph.nodes():
            predecessors = tuple(sorted(self.interaction_graph.predecessors(node)))
            if predecessors:
                if predecessors not in predecessor_groups:
                    predecessor_groups[predecessors] = []
                predecessor_groups[predecessors].append(node)
                
        for group in predecessor_groups.values():
            if len(group) > 1:
                patterns["parallel_groups"].append(group)
                
        # Feedback loops
        for interaction in self.interactions:
            if interaction.interaction_type == InteractionType.FEEDBACK:
                patterns["feedback_loops"].append([interaction.source_agent, interaction.target_agent])
                
        # Bottleneck agents (high in-degree or out-degree)
        for node in self.interaction_graph.nodes():
            in_degree = self.interaction_graph.in_degree(node)
            out_degree = self.interaction_graph.out_degree(node)
            
            if in_degree > 3 or out_degree > 3:
                patterns["bottleneck_agents"].append({
                    "agent": node,
                    "in_degree": in_degree,
                    "out_degree": out_degree
                })
                
        # Isolated agents
        patterns["isolated_agents"] = self.identify_isolated_agents()
        
        # Circular dependencies
        patterns["circular_dependencies"] = self.detect_circular_dependencies()
        
        return patterns
        
    def visualize_interaction_graph(self, output_path: Optional[Path] = None):
        """Visualize the agent interaction graph"""
        if not HAS_VISUALIZATION:
            return  # Skip if visualization libraries not available
            
        if not self.interaction_graph.nodes():
            return
            
        plt.figure(figsize=(12, 8))
        
        # Layout
        pos = nx.spring_layout(self.interaction_graph, k=2, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.interaction_graph,
            pos,
            node_color='lightblue',
            node_size=1000,
            alpha=0.9
        )
        
        # Draw edges with different styles for interaction types
        edge_colors = {
            InteractionType.SEQUENTIAL.value: 'blue',
            InteractionType.PARALLEL.value: 'green',
            InteractionType.CONDITIONAL.value: 'orange',
            InteractionType.FEEDBACK.value: 'red',
            InteractionType.COLLABORATIVE.value: 'purple'
        }
        
        for interaction_type, color in edge_colors.items():
            edges = [(u, v) for u, v, d in self.interaction_graph.edges(data=True)
                    if d.get('interaction_type') == interaction_type]
            nx.draw_networkx_edges(
                self.interaction_graph,
                pos,
                edgelist=edges,
                edge_color=color,
                alpha=0.6,
                arrows=True,
                arrowsize=20
            )
            
        # Draw labels
        nx.draw_networkx_labels(self.interaction_graph, pos)
        
        plt.title("Agent Interaction Graph")
        plt.axis('off')
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
        plt.close()
        
    def _update_metrics(self, interaction: AgentInteraction):
        """Update internal metrics"""
        # Update latency metrics
        all_latencies = [i.latency_ms for i in self.interactions]
        self.metrics["avg_latency_ms"] = sum(all_latencies) / len(all_latencies) if all_latencies else 0
        self.metrics["max_latency_ms"] = max(all_latencies) if all_latencies else 0
        
        # Update protocol distribution
        protocol = interaction.protocol.value
        if protocol not in self.metrics["protocol_distribution"]:
            self.metrics["protocol_distribution"][protocol] = 0
        self.metrics["protocol_distribution"][protocol] += 1
        
        # Update interaction type distribution
        int_type = interaction.interaction_type.value
        if int_type not in self.metrics["interaction_type_distribution"]:
            self.metrics["interaction_type_distribution"][int_type] = 0
        self.metrics["interaction_type_distribution"][int_type] += 1
        
        # Update artifact count
        self.metrics["artifacts_created"] += len(interaction.artifacts_shared)
        
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        patterns = self.analyze_interaction_patterns()
        
        # Calculate success rate
        success_rate = (
            self.metrics["successful_interactions"] / self.metrics["total_interactions"] * 100
            if self.metrics["total_interactions"] > 0 else 0
        )
        
        # Find most used tools
        top_tools = sorted(
            self.tool_patterns.values(),
            key=lambda x: x.usage_count,
            reverse=True
        )[:5]
        
        # Find problematic agents
        problematic_agents = []
        for pattern in self.tool_patterns.values():
            if pattern.success_rate < 50:
                problematic_agents.append({
                    "agent": pattern.agent_name,
                    "tool": pattern.tool_name,
                    "success_rate": pattern.success_rate
                })
                
        return {
            "session_id": self.session_id,
            "summary": {
                "total_interactions": self.metrics["total_interactions"],
                "success_rate": success_rate,
                "avg_latency_ms": self.metrics["avg_latency_ms"],
                "max_latency_ms": self.metrics["max_latency_ms"],
                "context_size_bytes": self.metrics["context_size_bytes"],
                "artifacts_created": self.metrics["artifacts_created"],
                "tools_invoked": self.metrics["tools_invoked"]
            },
            "validation": {
                "dependency_violations": self.metrics["dependency_violations"],
                "validation_errors": self.metrics["validation_errors"][:10],  # Top 10 errors
                "circular_dependencies": patterns["circular_dependencies"],
                "isolated_agents": patterns["isolated_agents"]
            },
            "patterns": {
                "sequential_chains": patterns["sequential_chains"],
                "parallel_groups": patterns["parallel_groups"],
                "feedback_loops": patterns["feedback_loops"],
                "bottleneck_agents": patterns["bottleneck_agents"]
            },
            "tool_usage": {
                "top_tools": [
                    {
                        "agent": t.agent_name,
                        "tool": t.tool_name,
                        "usage_count": t.usage_count,
                        "success_rate": t.success_rate
                    }
                    for t in top_tools
                ],
                "problematic_agents": problematic_agents
            },
            "distributions": {
                "protocol": self.metrics["protocol_distribution"],
                "interaction_type": self.metrics["interaction_type_distribution"]
            }
        }