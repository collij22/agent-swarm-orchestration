#!/usr/bin/env python3
"""
Session Analyzer - Deep analysis of agent swarm sessions

Features:
- Error pattern detection
- Reasoning quality assessment  
- Decision tree visualization
- Workflow optimization suggestions
- Agent collaboration pattern analysis
- Critical path analysis
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
from enum import Enum
import networkx as nx

from session_manager import SessionManager, SessionData, SessionStatus
from metrics_aggregator import MetricsAggregator

class AnalysisType(Enum):
    ERROR_PATTERN = "error_pattern"
    REASONING_QUALITY = "reasoning_quality"
    DECISION_FLOW = "decision_flow"
    COLLABORATION = "collaboration"
    CRITICAL_PATH = "critical_path"
    OPTIMIZATION = "optimization"

@dataclass
class ErrorPattern:
    """Detected error pattern"""
    pattern_type: str
    frequency: int
    affected_agents: List[str]
    common_context: str
    suggested_fix: str

@dataclass
class ReasoningQuality:
    """Assessment of reasoning quality"""
    agent_name: str
    clarity_score: float  # 0-100
    consistency_score: float  # 0-100
    depth_score: float  # 0-100
    overall_score: float  # 0-100
    issues: List[str]
    examples: List[str]

@dataclass
class WorkflowOptimization:
    """Suggested workflow optimization"""
    optimization_type: str
    description: str
    expected_improvement: str
    affected_agents: List[str]
    priority: int  # 1-5, 1 being highest

@dataclass
class CollaborationPattern:
    """Agent collaboration pattern"""
    agent_pair: Tuple[str, str]
    interaction_count: int
    success_rate: float
    average_duration_ms: float
    pattern_type: str  # sequential, parallel, dependent

class SessionAnalyzer:
    """Analyzes agent swarm sessions for patterns and optimizations"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.metrics_aggregator = MetricsAggregator(session_manager)
        
        # Analysis cache
        self.analysis_cache = {}
        
        # Common error patterns
        self.known_error_patterns = {
            "timeout": r"timeout|timed out|deadline exceeded",
            "rate_limit": r"rate limit|too many requests|429",
            "api_error": r"api error|request failed|500|503",
            "auth_error": r"unauthorized|forbidden|401|403",
            "validation": r"validation|invalid|malformed",
            "resource": r"out of memory|disk full|resource exhausted",
            "network": r"connection|network|unreachable",
        }
        
        # Reasoning quality indicators
        self.reasoning_indicators = {
            "clarity": {
                "positive": ["because", "therefore", "since", "due to", "in order to"],
                "negative": ["maybe", "perhaps", "might", "unsure", "unclear"]
            },
            "depth": {
                "positive": ["considering", "analyzing", "evaluating", "comparing"],
                "negative": ["simple", "basic", "obvious", "trivial"]
            },
            "consistency": {
                "positive": ["following", "based on", "according to", "as per"],
                "negative": ["however", "but actually", "changing", "different from"]
            }
        }
    
    def analyze_session(self, 
                       session_id: str,
                       analysis_types: List[AnalysisType] = None) -> Dict:
        """Perform comprehensive analysis of a session"""
        
        session = self.session_manager.load_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        if analysis_types is None:
            analysis_types = list(AnalysisType)
        
        results = {
            "session_id": session_id,
            "status": session.metadata.status.value,
            "analyses": {}
        }
        
        for analysis_type in analysis_types:
            if analysis_type == AnalysisType.ERROR_PATTERN:
                results["analyses"]["error_patterns"] = self._analyze_error_patterns(session)
            elif analysis_type == AnalysisType.REASONING_QUALITY:
                results["analyses"]["reasoning_quality"] = self._analyze_reasoning_quality(session)
            elif analysis_type == AnalysisType.DECISION_FLOW:
                results["analyses"]["decision_flow"] = self._analyze_decision_flow(session)
            elif analysis_type == AnalysisType.COLLABORATION:
                results["analyses"]["collaboration"] = self._analyze_collaboration_patterns(session)
            elif analysis_type == AnalysisType.CRITICAL_PATH:
                results["analyses"]["critical_path"] = self._analyze_critical_path(session)
            elif analysis_type == AnalysisType.OPTIMIZATION:
                results["analyses"]["optimizations"] = self._suggest_optimizations(session)
        
        return results
    
    def _analyze_error_patterns(self, session: SessionData) -> List[ErrorPattern]:
        """Analyze error patterns in session"""
        error_patterns = []
        error_contexts = defaultdict(list)
        
        for entry in session.entries:
            if isinstance(entry, dict) and entry.get("level") == "ERROR":
                error_msg = entry.get("message", "").lower()
                agent = entry.get("agent_name", "unknown")
                
                # Match against known patterns
                for pattern_type, pattern_regex in self.known_error_patterns.items():
                    if re.search(pattern_regex, error_msg):
                        error_contexts[pattern_type].append({
                            "agent": agent,
                            "message": error_msg,
                            "reasoning": entry.get("reasoning", "")
                        })
        
        # Create error pattern objects
        for pattern_type, contexts in error_contexts.items():
            affected_agents = list(set(ctx["agent"] for ctx in contexts))
            
            # Find common context
            common_words = Counter()
            for ctx in contexts:
                words = ctx["message"].split()
                common_words.update(words)
            
            common_context = " ".join([word for word, count in common_words.most_common(5)])
            
            # Suggest fixes based on pattern type
            suggested_fix = self._get_error_fix_suggestion(pattern_type)
            
            error_patterns.append(ErrorPattern(
                pattern_type=pattern_type,
                frequency=len(contexts),
                affected_agents=affected_agents,
                common_context=common_context,
                suggested_fix=suggested_fix
            ))
        
        return error_patterns
    
    def _analyze_reasoning_quality(self, session: SessionData) -> List[ReasoningQuality]:
        """Analyze the quality of reasoning in session"""
        agent_reasoning = defaultdict(list)
        
        # Collect reasoning entries per agent
        for entry in session.entries:
            if isinstance(entry, dict) and entry.get("reasoning"):
                agent = entry.get("agent_name", "unknown")
                agent_reasoning[agent].append(entry["reasoning"])
        
        quality_assessments = []
        
        for agent_name, reasoning_entries in agent_reasoning.items():
            if not reasoning_entries:
                continue
            
            clarity_score = self._assess_clarity(reasoning_entries)
            consistency_score = self._assess_consistency(reasoning_entries)
            depth_score = self._assess_depth(reasoning_entries)
            
            overall_score = (clarity_score + consistency_score + depth_score) / 3
            
            issues = []
            if clarity_score < 60:
                issues.append("Low clarity in reasoning")
            if consistency_score < 60:
                issues.append("Inconsistent reasoning patterns")
            if depth_score < 60:
                issues.append("Shallow analysis depth")
            
            quality_assessments.append(ReasoningQuality(
                agent_name=agent_name,
                clarity_score=clarity_score,
                consistency_score=consistency_score,
                depth_score=depth_score,
                overall_score=overall_score,
                issues=issues,
                examples=reasoning_entries[:3]  # Sample examples
            ))
        
        return quality_assessments
    
    def _analyze_decision_flow(self, session: SessionData) -> Dict:
        """Analyze the decision flow through the session"""
        decision_graph = nx.DiGraph()
        
        # Build decision graph
        prev_agent = None
        for i, entry in enumerate(session.entries):
            if isinstance(entry, dict) and entry.get("event_type") == "agent_start":
                agent = entry.get("agent_name", f"agent_{i}")
                decision_graph.add_node(agent, 
                                      reasoning=entry.get("reasoning", ""),
                                      timestamp=entry.get("timestamp", ""))
                
                if prev_agent:
                    decision_graph.add_edge(prev_agent, agent)
                
                prev_agent = agent
        
        # Analyze graph properties
        analysis = {
            "total_decisions": decision_graph.number_of_nodes(),
            "decision_chains": list(nx.simple_paths(decision_graph, 
                                                   list(decision_graph.nodes())[0] if decision_graph.nodes() else None,
                                                   list(decision_graph.nodes())[-1] if decision_graph.nodes() else None))[:5] if decision_graph.nodes() else [],
            "bottlenecks": [],
            "parallel_opportunities": []
        }
        
        # Find bottlenecks (nodes with high degree)
        if decision_graph.nodes():
            for node in decision_graph.nodes():
                in_degree = decision_graph.in_degree(node)
                out_degree = decision_graph.out_degree(node)
                if in_degree > 2 or out_degree > 2:
                    analysis["bottlenecks"].append({
                        "agent": node,
                        "in_degree": in_degree,
                        "out_degree": out_degree
                    })
        
        # Find parallel opportunities
        for node in decision_graph.nodes():
            successors = list(decision_graph.successors(node))
            if len(successors) > 1:
                # Check if successors could run in parallel
                independent = True
                for i in range(len(successors)):
                    for j in range(i+1, len(successors)):
                        if nx.has_path(decision_graph, successors[i], successors[j]) or \
                           nx.has_path(decision_graph, successors[j], successors[i]):
                            independent = False
                            break
                
                if independent:
                    analysis["parallel_opportunities"].append({
                        "after": node,
                        "parallel_agents": successors
                    })
        
        return analysis
    
    def _analyze_collaboration_patterns(self, session: SessionData) -> List[CollaborationPattern]:
        """Analyze how agents collaborate"""
        collaborations = defaultdict(lambda: {
            "count": 0,
            "successes": 0,
            "total_duration": 0,
            "pattern": "sequential"
        })
        
        # Track agent interactions
        agent_sequence = []
        for entry in session.entries:
            if isinstance(entry, dict) and entry.get("event_type") == "agent_complete":
                agent = entry.get("agent_name", "unknown")
                success = entry.get("level") != "ERROR"
                duration = entry.get("duration_ms", 0)
                
                if agent_sequence:
                    prev_agent = agent_sequence[-1]["agent"]
                    pair = tuple(sorted([prev_agent, agent]))
                    
                    collab = collaborations[pair]
                    collab["count"] += 1
                    if success:
                        collab["successes"] += 1
                    collab["total_duration"] += duration
                
                agent_sequence.append({
                    "agent": agent,
                    "success": success,
                    "duration": duration
                })
        
        # Create collaboration pattern objects
        patterns = []
        for pair, stats in collaborations.items():
            if stats["count"] > 0:
                patterns.append(CollaborationPattern(
                    agent_pair=pair,
                    interaction_count=stats["count"],
                    success_rate=(stats["successes"] / stats["count"] * 100),
                    average_duration_ms=(stats["total_duration"] / stats["count"]),
                    pattern_type=stats["pattern"]
                ))
        
        return patterns
    
    def _analyze_critical_path(self, session: SessionData) -> Dict:
        """Find the critical path through the session"""
        # Build execution graph with durations
        exec_graph = nx.DiGraph()
        
        agent_executions = []
        for entry in session.entries:
            if isinstance(entry, dict):
                if entry.get("event_type") == "agent_start":
                    agent_executions.append({
                        "agent": entry.get("agent_name", "unknown"),
                        "start": entry.get("timestamp", ""),
                        "duration": 0
                    })
                elif entry.get("event_type") == "agent_complete" and agent_executions:
                    agent_executions[-1]["duration"] = entry.get("duration_ms", 0)
        
        # Build graph
        for i, execution in enumerate(agent_executions):
            exec_graph.add_node(i, 
                              agent=execution["agent"],
                              duration=execution["duration"])
            if i > 0:
                exec_graph.add_edge(i-1, i, weight=execution["duration"])
        
        critical_path = []
        total_duration = 0
        
        if exec_graph.nodes():
            # Find longest path (critical path)
            try:
                path = nx.dag_longest_path(exec_graph, weight="weight")
                critical_path = [exec_graph.nodes[node]["agent"] for node in path]
                total_duration = sum(exec_graph.nodes[node]["duration"] for node in path)
            except:
                pass
        
        # Find potential optimizations
        optimizations = []
        for i in range(len(critical_path) - 1):
            current = critical_path[i]
            next_agent = critical_path[i + 1]
            
            # Check if they could run in parallel
            # (This is simplified - real check would need dependency analysis)
            optimizations.append({
                "current": current,
                "next": next_agent,
                "potential_parallel": True  # Simplified
            })
        
        return {
            "critical_path": critical_path,
            "total_duration_ms": total_duration,
            "optimization_opportunities": optimizations[:5]
        }
    
    def _suggest_optimizations(self, session: SessionData) -> List[WorkflowOptimization]:
        """Suggest workflow optimizations"""
        optimizations = []
        
        # Analyze for common optimization opportunities
        
        # 1. Check for repeated agent calls
        agent_calls = Counter()
        for entry in session.entries:
            if isinstance(entry, dict) and entry.get("event_type") == "agent_start":
                agent_calls[entry.get("agent_name", "unknown")] += 1
        
        for agent, count in agent_calls.items():
            if count > 2:
                optimizations.append(WorkflowOptimization(
                    optimization_type="reduce_repetition",
                    description=f"Agent '{agent}' called {count} times - consider caching or combining",
                    expected_improvement=f"Reduce execution time by {(count-1)*20}%",
                    affected_agents=[agent],
                    priority=2
                ))
        
        # 2. Check for slow agents
        slow_threshold = 10000  # 10 seconds
        for agent_name, metrics in session.metrics.items():
            avg_duration = metrics.get("average_duration_ms", 0)
            if avg_duration > slow_threshold:
                optimizations.append(WorkflowOptimization(
                    optimization_type="optimize_performance",
                    description=f"Agent '{agent_name}' is slow ({avg_duration:.1f}ms avg)",
                    expected_improvement="Reduce execution time by 30-50%",
                    affected_agents=[agent_name],
                    priority=1
                ))
        
        # 3. Check for high error rates
        for agent_name, metrics in session.metrics.items():
            error_rate = 100 - metrics.get("success_rate", 100)
            if error_rate > 10:
                optimizations.append(WorkflowOptimization(
                    optimization_type="improve_reliability",
                    description=f"Agent '{agent_name}' has {error_rate:.1f}% error rate",
                    expected_improvement="Increase success rate to 95%+",
                    affected_agents=[agent_name],
                    priority=1
                ))
        
        # 4. Check for parallel opportunities
        decision_flow = self._analyze_decision_flow(session)
        for opportunity in decision_flow.get("parallel_opportunities", []):
            optimizations.append(WorkflowOptimization(
                optimization_type="enable_parallel",
                description=f"Agents {opportunity['parallel_agents']} can run in parallel",
                expected_improvement="Reduce total time by 40%",
                affected_agents=opportunity['parallel_agents'],
                priority=3
            ))
        
        # Sort by priority
        optimizations.sort(key=lambda x: x.priority)
        
        return optimizations
    
    def _assess_clarity(self, reasoning_entries: List[str]) -> float:
        """Assess clarity of reasoning"""
        if not reasoning_entries:
            return 0
        
        clarity_scores = []
        for reasoning in reasoning_entries:
            score = 50  # Base score
            
            # Check for positive indicators
            for indicator in self.reasoning_indicators["clarity"]["positive"]:
                if indicator.lower() in reasoning.lower():
                    score += 10
            
            # Check for negative indicators
            for indicator in self.reasoning_indicators["clarity"]["negative"]:
                if indicator.lower() in reasoning.lower():
                    score -= 10
            
            # Check for structure (sentences, length)
            if len(reasoning) > 50:
                score += 10
            if len(reasoning.split('.')) > 1:
                score += 10
            
            clarity_scores.append(min(100, max(0, score)))
        
        return sum(clarity_scores) / len(clarity_scores)
    
    def _assess_consistency(self, reasoning_entries: List[str]) -> float:
        """Assess consistency of reasoning"""
        if len(reasoning_entries) < 2:
            return 100  # Can't assess consistency with single entry
        
        # Check for similar patterns and vocabulary
        word_sets = [set(r.lower().split()) for r in reasoning_entries]
        
        consistency_scores = []
        for i in range(len(word_sets) - 1):
            overlap = len(word_sets[i] & word_sets[i+1])
            total = len(word_sets[i] | word_sets[i+1])
            similarity = (overlap / total * 100) if total > 0 else 0
            consistency_scores.append(similarity)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 50
    
    def _assess_depth(self, reasoning_entries: List[str]) -> float:
        """Assess depth of reasoning"""
        if not reasoning_entries:
            return 0
        
        depth_scores = []
        for reasoning in reasoning_entries:
            score = 50  # Base score
            
            # Check for depth indicators
            for indicator in self.reasoning_indicators["depth"]["positive"]:
                if indicator.lower() in reasoning.lower():
                    score += 15
            
            for indicator in self.reasoning_indicators["depth"]["negative"]:
                if indicator.lower() in reasoning.lower():
                    score -= 15
            
            # Length as proxy for depth
            if len(reasoning) > 100:
                score += 20
            elif len(reasoning) < 30:
                score -= 20
            
            depth_scores.append(min(100, max(0, score)))
        
        return sum(depth_scores) / len(depth_scores)
    
    def _get_error_fix_suggestion(self, pattern_type: str) -> str:
        """Get fix suggestion for error pattern"""
        suggestions = {
            "timeout": "Increase timeout limits or optimize agent execution",
            "rate_limit": "Implement rate limiting and request queuing",
            "api_error": "Add retry logic with exponential backoff",
            "auth_error": "Verify API credentials and permissions",
            "validation": "Add input validation and error handling",
            "resource": "Optimize memory usage or increase resource limits",
            "network": "Implement connection retry and failover logic"
        }
        return suggestions.get(pattern_type, "Review error logs and add appropriate error handling")
    
    def compare_reasoning_quality(self, session_ids: List[str]) -> Dict:
        """Compare reasoning quality across multiple sessions"""
        comparison = {
            "sessions": {},
            "best_performers": [],
            "needs_improvement": []
        }
        
        all_scores = []
        
        for session_id in session_ids:
            analysis = self.analyze_session(session_id, [AnalysisType.REASONING_QUALITY])
            reasoning_quality = analysis["analyses"].get("reasoning_quality", [])
            
            session_scores = {
                "average_clarity": 0,
                "average_consistency": 0,
                "average_depth": 0,
                "average_overall": 0
            }
            
            if reasoning_quality:
                session_scores["average_clarity"] = sum(r.clarity_score for r in reasoning_quality) / len(reasoning_quality)
                session_scores["average_consistency"] = sum(r.consistency_score for r in reasoning_quality) / len(reasoning_quality)
                session_scores["average_depth"] = sum(r.depth_score for r in reasoning_quality) / len(reasoning_quality)
                session_scores["average_overall"] = sum(r.overall_score for r in reasoning_quality) / len(reasoning_quality)
                
                all_scores.extend([(r.agent_name, r.overall_score) for r in reasoning_quality])
            
            comparison["sessions"][session_id] = session_scores
        
        # Identify best and worst performers
        all_scores.sort(key=lambda x: x[1], reverse=True)
        comparison["best_performers"] = all_scores[:5]
        comparison["needs_improvement"] = all_scores[-5:] if len(all_scores) > 5 else []
        
        return comparison
    
    def generate_analysis_report(self, session_id: str, output_file: str):
        """Generate comprehensive analysis report"""
        analysis = self.analyze_session(session_id)
        
        # Format as markdown report
        report = f"""# Session Analysis Report

## Session: {session_id}
**Status**: {analysis['status']}
**Generated**: {datetime.now().isoformat()}

## Executive Summary
"""
        
        # Add error patterns
        if "error_patterns" in analysis["analyses"]:
            report += "\n### Error Patterns Detected\n"
            for pattern in analysis["analyses"]["error_patterns"]:
                report += f"- **{pattern.pattern_type}**: {pattern.frequency} occurrences\n"
                report += f"  - Affected agents: {', '.join(pattern.affected_agents)}\n"
                report += f"  - Suggested fix: {pattern.suggested_fix}\n"
        
        # Add reasoning quality
        if "reasoning_quality" in analysis["analyses"]:
            report += "\n### Reasoning Quality Assessment\n"
            for quality in analysis["analyses"]["reasoning_quality"][:5]:
                report += f"- **{quality.agent_name}**: {quality.overall_score:.1f}/100\n"
                if quality.issues:
                    report += f"  - Issues: {', '.join(quality.issues)}\n"
        
        # Add optimizations
        if "optimizations" in analysis["analyses"]:
            report += "\n### Recommended Optimizations\n"
            for opt in analysis["analyses"]["optimizations"][:5]:
                report += f"- **Priority {opt.priority}**: {opt.description}\n"
                report += f"  - Expected improvement: {opt.expected_improvement}\n"
        
        # Add critical path
        if "critical_path" in analysis["analyses"]:
            cp = analysis["analyses"]["critical_path"]
            report += f"\n### Critical Path Analysis\n"
            report += f"- Path: {' → '.join(cp['critical_path'])}\n"
            report += f"- Total duration: {cp['total_duration_ms']:.1f}ms\n"
        
        # Save report
        with open(output_file, 'w') as f:
            f.write(report)
        
        return f"Analysis report saved to {output_file}"

# Example usage
if __name__ == "__main__":
    from session_manager import SessionManager
    
    # Create analyzer
    session_manager = SessionManager()
    analyzer = SessionAnalyzer(session_manager)
    
    # Analyze a session (would need actual session ID)
    # analysis = analyzer.analyze_session("session-id")
    
    print("Session Analyzer initialized")
    print("Available analysis types:")
    for analysis_type in AnalysisType:
        print(f"  - {analysis_type.value}")