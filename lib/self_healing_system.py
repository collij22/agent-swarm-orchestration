#!/usr/bin/env python3
"""
Self-Healing System - Advanced automatic system optimization and recovery
Builds upon continuous improvement with ML-based pattern detection and auto-tuning
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import difflib
import statistics

# Try importing ML libraries
try:
    from sklearn.cluster import DBSCAN
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: scikit-learn not installed. Pattern detection will use heuristics.")

@dataclass
class ErrorPattern:
    """Represents a detected error pattern"""
    pattern_id: str
    error_type: str
    pattern_text: str
    occurrences: int
    first_seen: float
    last_seen: float
    affected_agents: List[str]
    suggested_fixes: List[str]
    auto_fixed: bool = False
    fix_success_rate: float = 0.0

@dataclass
class PromptOptimization:
    """Suggested prompt optimization"""
    agent_name: str
    original_prompt: str
    optimized_prompt: str
    reason: str
    expected_improvement: float
    applied: bool = False
    validation_score: float = 0.0

@dataclass
class ConfigurationTune:
    """Configuration tuning recommendation"""
    parameter: str
    current_value: Any
    recommended_value: Any
    reason: str
    impact: str  # low, medium, high
    risk: str    # low, medium, high
    applied: bool = False

@dataclass
class KnowledgeEntry:
    """Knowledge base entry for learned patterns"""
    entry_id: str
    category: str  # error_fix, optimization, best_practice
    title: str
    description: str
    solution: str
    examples: List[Dict]
    success_rate: float
    usage_count: int
    created: float
    last_updated: float

class SelfHealingSystem:
    """
    Advanced self-healing system with ML-based optimization
    Features:
    - Automatic error pattern detection
    - Prompt optimization based on failures
    - Agent retraining suggestions
    - Configuration auto-tuning
    - Knowledge base updates
    """
    
    def __init__(self, 
                 data_dir: str = "data/self_healing",
                 knowledge_base_path: str = "data/knowledge_base.json",
                 enable_auto_fix: bool = True,
                 enable_auto_tune: bool = True):
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.knowledge_base_path = Path(knowledge_base_path)
        
        # Pattern detection
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.error_history: List[Dict] = []
        self.pattern_vectorizer = None
        
        # Prompt optimization
        self.prompt_optimizations: Dict[str, List[PromptOptimization]] = defaultdict(list)
        self.prompt_performance: Dict[str, Dict] = {}  # Track prompt performance
        
        # Configuration tuning
        self.config_tunes: List[ConfigurationTune] = []
        self.config_history: Dict[str, List] = defaultdict(list)
        self.optimal_configs: Dict[str, Any] = {}
        
        # Knowledge base
        self.knowledge_base: Dict[str, KnowledgeEntry] = {}
        
        # Agent retraining suggestions
        self.retraining_queue: Dict[str, Dict] = {}
        
        # Auto-healing settings
        self.enable_auto_fix = enable_auto_fix
        self.enable_auto_tune = enable_auto_tune
        self.healing_history: List[Dict] = []
        
        # Performance baselines
        self.performance_baselines: Dict[str, Dict] = {}
        
        # Load existing data
        self._load_knowledge_base()
        self._load_healing_history()
        
        # Initialize ML components if available
        if HAS_SKLEARN:
            self._initialize_ml_components()
    
    def _initialize_ml_components(self):
        """Initialize ML components for pattern detection"""
        if HAS_SKLEARN:
            self.pattern_vectorizer = TfidfVectorizer(
                max_features=100,
                ngram_range=(1, 3),
                stop_words='english'
            )
    
    def _load_knowledge_base(self):
        """Load knowledge base from file"""
        if self.knowledge_base_path.exists():
            try:
                with open(self.knowledge_base_path, 'r') as f:
                    data = json.load(f)
                    
                for entry_id, entry_data in data.items():
                    self.knowledge_base[entry_id] = KnowledgeEntry(**entry_data)
                    
                print(f"Loaded {len(self.knowledge_base)} knowledge base entries")
                
            except Exception as e:
                print(f"Failed to load knowledge base: {e}")
    
    def _save_knowledge_base(self):
        """Save knowledge base to file"""
        try:
            self.knowledge_base_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            for entry_id, entry in self.knowledge_base.items():
                data[entry_id] = {
                    "entry_id": entry.entry_id,
                    "category": entry.category,
                    "title": entry.title,
                    "description": entry.description,
                    "solution": entry.solution,
                    "examples": entry.examples,
                    "success_rate": entry.success_rate,
                    "usage_count": entry.usage_count,
                    "created": entry.created,
                    "last_updated": entry.last_updated
                }
            
            with open(self.knowledge_base_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save knowledge base: {e}")
    
    def _load_healing_history(self):
        """Load healing history"""
        history_file = self.data_dir / "healing_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    self.healing_history = json.load(f)
            except Exception as e:
                print(f"Failed to load healing history: {e}")
    
    def _save_healing_history(self):
        """Save healing history"""
        try:
            history_file = self.data_dir / "healing_history.json"
            with open(history_file, 'w') as f:
                json.dump(self.healing_history[-1000:], f, indent=2)  # Keep last 1000 entries
        except Exception as e:
            print(f"Failed to save healing history: {e}")
    
    def detect_error_patterns(self, errors: List[Dict]) -> List[ErrorPattern]:
        """
        Detect patterns in errors using clustering
        
        Args:
            errors: List of error dictionaries with 'message', 'agent', 'timestamp'
            
        Returns:
            List of detected error patterns
        """
        if not errors:
            return []
        
        # Add to error history
        self.error_history.extend(errors)
        
        # Extract error messages
        error_messages = [e.get("message", "") for e in errors]
        
        if HAS_SKLEARN and len(error_messages) > 5:
            # Use ML clustering
            patterns = self._ml_pattern_detection(errors, error_messages)
        else:
            # Use heuristic pattern detection
            patterns = self._heuristic_pattern_detection(errors, error_messages)
        
        # Update error patterns
        for pattern in patterns:
            if pattern.pattern_id not in self.error_patterns:
                self.error_patterns[pattern.pattern_id] = pattern
                
                # Add to knowledge base if significant
                if pattern.occurrences > 3:
                    self._add_error_to_knowledge_base(pattern)
            else:
                # Update existing pattern
                existing = self.error_patterns[pattern.pattern_id]
                existing.occurrences += pattern.occurrences
                existing.last_seen = pattern.last_seen
                existing.affected_agents.extend(pattern.affected_agents)
                existing.affected_agents = list(set(existing.affected_agents))
        
        return patterns
    
    def _ml_pattern_detection(self, errors: List[Dict], error_messages: List[str]) -> List[ErrorPattern]:
        """Use ML clustering to detect error patterns"""
        patterns = []
        
        try:
            # Vectorize error messages
            if not self.pattern_vectorizer:
                self.pattern_vectorizer = TfidfVectorizer(
                    max_features=100,
                    ngram_range=(1, 3),
                    stop_words='english'
                )
                vectors = self.pattern_vectorizer.fit_transform(error_messages)
            else:
                vectors = self.pattern_vectorizer.transform(error_messages)
            
            # Cluster similar errors
            clustering = DBSCAN(eps=0.3, min_samples=2)
            labels = clustering.fit_predict(vectors.toarray())
            
            # Create patterns from clusters
            clusters = defaultdict(list)
            for i, label in enumerate(labels):
                if label != -1:  # Not noise
                    clusters[label].append(i)
            
            for cluster_id, indices in clusters.items():
                cluster_errors = [errors[i] for i in indices]
                cluster_messages = [error_messages[i] for i in indices]
                
                # Find common pattern
                common_words = self._find_common_words(cluster_messages)
                pattern_text = " ".join(common_words[:10])
                
                # Extract pattern details
                pattern = ErrorPattern(
                    pattern_id=f"pattern_{hash(pattern_text) % 10000}",
                    error_type=self._classify_error_type(pattern_text),
                    pattern_text=pattern_text,
                    occurrences=len(cluster_errors),
                    first_seen=min(e.get("timestamp", time.time()) for e in cluster_errors),
                    last_seen=max(e.get("timestamp", time.time()) for e in cluster_errors),
                    affected_agents=list(set(e.get("agent", "unknown") for e in cluster_errors)),
                    suggested_fixes=self._generate_fixes(pattern_text, cluster_messages)
                )
                
                patterns.append(pattern)
                
        except Exception as e:
            print(f"ML pattern detection failed: {e}, falling back to heuristics")
            patterns = self._heuristic_pattern_detection(errors, error_messages)
        
        return patterns
    
    def _heuristic_pattern_detection(self, errors: List[Dict], error_messages: List[str]) -> List[ErrorPattern]:
        """Heuristic-based error pattern detection"""
        patterns = []
        
        # Group by error type keywords
        error_groups = defaultdict(list)
        
        for i, msg in enumerate(error_messages):
            msg_lower = msg.lower()
            
            # Classify error
            if "timeout" in msg_lower:
                error_type = "timeout"
            elif "rate limit" in msg_lower:
                error_type = "rate_limit"
            elif "file not found" in msg_lower or "no such file" in msg_lower:
                error_type = "file_not_found"
            elif "syntax error" in msg_lower or "parse error" in msg_lower:
                error_type = "syntax_error"
            elif "connection" in msg_lower or "network" in msg_lower:
                error_type = "network_error"
            elif "permission" in msg_lower or "access denied" in msg_lower:
                error_type = "permission_error"
            elif "memory" in msg_lower or "out of memory" in msg_lower:
                error_type = "memory_error"
            else:
                error_type = "general_error"
            
            error_groups[error_type].append(i)
        
        # Create patterns from groups
        for error_type, indices in error_groups.items():
            if len(indices) >= 2:  # At least 2 occurrences
                group_errors = [errors[i] for i in indices]
                group_messages = [error_messages[i] for i in indices]
                
                # Find common substring
                common_text = self._find_common_substring(group_messages)
                
                pattern = ErrorPattern(
                    pattern_id=f"{error_type}_{hash(common_text) % 10000}",
                    error_type=error_type,
                    pattern_text=common_text or error_type,
                    occurrences=len(group_errors),
                    first_seen=min(e.get("timestamp", time.time()) for e in group_errors),
                    last_seen=max(e.get("timestamp", time.time()) for e in group_errors),
                    affected_agents=list(set(e.get("agent", "unknown") for e in group_errors)),
                    suggested_fixes=self._generate_fixes_for_type(error_type)
                )
                
                patterns.append(pattern)
        
        return patterns
    
    def _find_common_words(self, messages: List[str]) -> List[str]:
        """Find common words across messages"""
        word_counts = Counter()
        
        for msg in messages:
            words = msg.lower().split()
            word_counts.update(words)
        
        # Return words that appear in at least half the messages
        threshold = len(messages) / 2
        common_words = [word for word, count in word_counts.items() if count >= threshold]
        
        return common_words
    
    def _find_common_substring(self, messages: List[str]) -> str:
        """Find longest common substring"""
        if not messages:
            return ""
        
        if len(messages) == 1:
            return messages[0][:50]  # First 50 chars
        
        # Use first two messages to find initial common substring
        s1, s2 = messages[0], messages[1]
        match = difflib.SequenceMatcher(None, s1, s2).find_longest_match(0, len(s1), 0, len(s2))
        common = s1[match.a:match.a + match.size]
        
        # Verify with other messages
        for msg in messages[2:]:
            if common not in msg:
                # Shorten common substring
                common = common[:len(common)//2]
                if len(common) < 10:
                    break
        
        return common.strip()
    
    def _classify_error_type(self, text: str) -> str:
        """Classify error type from text"""
        text_lower = text.lower()
        
        error_types = {
            "timeout": ["timeout", "timed out", "deadline exceeded"],
            "rate_limit": ["rate limit", "too many requests", "429"],
            "file_error": ["file not found", "no such file", "cannot open"],
            "syntax_error": ["syntax error", "parse error", "invalid syntax"],
            "network_error": ["connection", "network", "socket", "refused"],
            "permission_error": ["permission denied", "access denied", "unauthorized"],
            "memory_error": ["memory", "heap", "stack overflow"],
            "api_error": ["api error", "endpoint", "response code"]
        }
        
        for error_type, keywords in error_types.items():
            if any(kw in text_lower for kw in keywords):
                return error_type
        
        return "general_error"
    
    def _generate_fixes(self, pattern_text: str, messages: List[str]) -> List[str]:
        """Generate suggested fixes based on pattern"""
        fixes = []
        pattern_lower = pattern_text.lower()
        
        # Check knowledge base for similar patterns
        for entry in self.knowledge_base.values():
            if entry.category == "error_fix":
                similarity = self._calculate_similarity(pattern_text, entry.title)
                if similarity > 0.7:
                    fixes.append(entry.solution)
        
        # Generate type-specific fixes
        if "timeout" in pattern_lower:
            fixes.extend([
                "Increase timeout duration",
                "Optimize agent prompts for faster execution",
                "Add retry logic with exponential backoff"
            ])
        elif "rate limit" in pattern_lower:
            fixes.extend([
                "Implement rate limiting with token bucket",
                "Add request queuing and batching",
                "Use caching to reduce API calls"
            ])
        elif "file" in pattern_lower and "not found" in pattern_lower:
            fixes.extend([
                "Verify file paths before operations",
                "Create parent directories if missing",
                "Add file existence checks"
            ])
        elif "syntax" in pattern_lower:
            fixes.extend([
                "Validate generated code before execution",
                "Add syntax checking in prompts",
                "Use code formatting tools"
            ])
        
        return fixes[:5]  # Return top 5 fixes
    
    def _generate_fixes_for_type(self, error_type: str) -> List[str]:
        """Generate fixes for specific error type"""
        fixes_map = {
            "timeout": [
                "Increase timeout to 2x current value",
                "Break down complex operations",
                "Add progress monitoring"
            ],
            "rate_limit": [
                "Implement exponential backoff",
                "Reduce API call frequency",
                "Add request caching"
            ],
            "file_not_found": [
                "Create missing directories",
                "Validate paths before use",
                "Add fallback paths"
            ],
            "syntax_error": [
                "Add code validation",
                "Use linting tools",
                "Simplify generated code"
            ],
            "network_error": [
                "Add retry mechanism",
                "Implement circuit breaker",
                "Add connection pooling"
            ],
            "permission_error": [
                "Check permissions before operations",
                "Run with appropriate privileges",
                "Add permission fallbacks"
            ],
            "memory_error": [
                "Increase memory limits",
                "Optimize data structures",
                "Add memory monitoring"
            ],
            "general_error": [
                "Add comprehensive error handling",
                "Implement logging",
                "Add monitoring"
            ]
        }
        
        return fixes_map.get(error_type, fixes_map["general_error"])
    
    def optimize_prompt(self, agent_name: str, current_prompt: str,
                       failure_history: List[Dict]) -> PromptOptimization:
        """
        Optimize agent prompt based on failure history
        
        Args:
            agent_name: Name of the agent
            current_prompt: Current prompt text
            failure_history: List of failure incidents
            
        Returns:
            PromptOptimization with suggested improvements
        """
        # Analyze failure patterns
        failure_types = Counter()
        failure_contexts = []
        
        for failure in failure_history:
            failure_types[failure.get("type", "unknown")] += 1
            failure_contexts.append(failure.get("context", ""))
        
        # Generate optimization based on failures
        optimized_prompt = current_prompt
        reasons = []
        
        # Add clarity improvements
        if failure_types.get("misunderstanding", 0) > 2:
            optimized_prompt = self._add_clarity_instructions(optimized_prompt)
            reasons.append("Added clarity instructions to reduce misunderstandings")
        
        # Add error handling
        if failure_types.get("error", 0) > 3:
            optimized_prompt = self._add_error_handling(optimized_prompt)
            reasons.append("Enhanced error handling instructions")
        
        # Add constraints
        if failure_types.get("timeout", 0) > 2:
            optimized_prompt = self._add_performance_constraints(optimized_prompt)
            reasons.append("Added performance constraints to prevent timeouts")
        
        # Add examples if many failures
        if len(failure_history) > 5:
            optimized_prompt = self._add_examples(optimized_prompt, failure_contexts)
            reasons.append("Added examples based on common failure patterns")
        
        # Calculate expected improvement
        baseline_failure_rate = len(failure_history) / max(len(failure_history) + 10, 20)
        expected_improvement = min(0.3, baseline_failure_rate * 0.5)  # Expect 50% reduction
        
        optimization = PromptOptimization(
            agent_name=agent_name,
            original_prompt=current_prompt,
            optimized_prompt=optimized_prompt,
            reason="; ".join(reasons) if reasons else "No optimization needed",
            expected_improvement=expected_improvement
        )
        
        self.prompt_optimizations[agent_name].append(optimization)
        
        return optimization
    
    def _add_clarity_instructions(self, prompt: str) -> str:
        """Add clarity instructions to prompt"""
        clarity_section = """
# Important Instructions for Clarity:
1. Break down complex tasks into clear, sequential steps
2. Validate understanding of requirements before proceeding
3. Ask for clarification if any requirement is ambiguous
4. Provide clear status updates during execution
5. Document all assumptions made during execution
"""
        return prompt + "\n" + clarity_section
    
    def _add_error_handling(self, prompt: str) -> str:
        """Add error handling instructions"""
        error_section = """
# Error Handling Requirements:
1. Implement try-catch blocks for all critical operations
2. Provide meaningful error messages with context
3. Attempt recovery before failing completely
4. Log all errors with sufficient detail for debugging
5. Return partial results when complete failure occurs
"""
        return prompt + "\n" + error_section
    
    def _add_performance_constraints(self, prompt: str) -> str:
        """Add performance constraints"""
        performance_section = """
# Performance Constraints:
1. Optimize for execution speed - avoid unnecessary operations
2. Limit response length to essential information
3. Use efficient algorithms and data structures
4. Avoid infinite loops or recursive operations
5. Complete execution within reasonable time limits
"""
        return prompt + "\n" + performance_section
    
    def _add_examples(self, prompt: str, contexts: List[str]) -> str:
        """Add examples based on failure contexts"""
        # Extract common patterns from contexts
        common_issues = []
        
        for context in contexts[:5]:  # Use first 5 contexts
            if "file" in context.lower():
                common_issues.append("- File operations: Always verify paths exist")
            elif "api" in context.lower():
                common_issues.append("- API calls: Include proper error handling")
            elif "timeout" in context.lower():
                common_issues.append("- Long operations: Add progress indicators")
        
        if common_issues:
            examples_section = f"""
# Common Issues to Avoid:
{chr(10).join(set(common_issues))}
"""
            return prompt + "\n" + examples_section
        
        return prompt
    
    def suggest_agent_retraining(self, agent_name: str, 
                                performance_data: Dict) -> Dict[str, Any]:
        """
        Suggest retraining for an agent based on performance
        
        Args:
            agent_name: Name of the agent
            performance_data: Performance metrics and history
            
        Returns:
            Retraining suggestions
        """
        suggestion = {
            "agent": agent_name,
            "needs_retraining": False,
            "urgency": "low",  # low, medium, high, critical
            "reasons": [],
            "recommended_actions": [],
            "expected_improvement": 0.0
        }
        
        # Check performance thresholds
        success_rate = performance_data.get("success_rate", 1.0)
        avg_quality = performance_data.get("avg_quality_score", 1.0)
        recent_trend = performance_data.get("trend", "stable")
        
        # Determine if retraining needed
        if success_rate < 0.5:
            suggestion["needs_retraining"] = True
            suggestion["urgency"] = "critical"
            suggestion["reasons"].append(f"Very low success rate: {success_rate:.1%}")
            
        elif success_rate < 0.7:
            suggestion["needs_retraining"] = True
            suggestion["urgency"] = "high"
            suggestion["reasons"].append(f"Low success rate: {success_rate:.1%}")
            
        elif success_rate < 0.85 and recent_trend == "degrading":
            suggestion["needs_retraining"] = True
            suggestion["urgency"] = "medium"
            suggestion["reasons"].append(f"Degrading performance: {success_rate:.1%}")
        
        if avg_quality < 0.6:
            suggestion["needs_retraining"] = True
            if suggestion["urgency"] == "low":
                suggestion["urgency"] = "medium"
            suggestion["reasons"].append(f"Low quality score: {avg_quality:.1f}")
        
        # Generate recommended actions
        if suggestion["needs_retraining"]:
            # Prompt optimization
            suggestion["recommended_actions"].append({
                "action": "optimize_prompt",
                "description": "Refine and clarify agent prompts based on failure patterns"
            })
            
            # Model upgrade
            if success_rate < 0.6:
                suggestion["recommended_actions"].append({
                    "action": "upgrade_model",
                    "description": "Consider using a more capable model (e.g., Opus instead of Sonnet)"
                })
            
            # Context enhancement
            suggestion["recommended_actions"].append({
                "action": "enhance_context",
                "description": "Provide more detailed context and examples in prompts"
            })
            
            # Tool enhancement
            if "tool_failures" in performance_data and performance_data["tool_failures"] > 5:
                suggestion["recommended_actions"].append({
                    "action": "fix_tools",
                    "description": "Debug and fix tool execution issues"
                })
            
            # Calculate expected improvement
            if suggestion["urgency"] == "critical":
                suggestion["expected_improvement"] = 0.4  # 40% improvement expected
            elif suggestion["urgency"] == "high":
                suggestion["expected_improvement"] = 0.3
            elif suggestion["urgency"] == "medium":
                suggestion["expected_improvement"] = 0.2
            else:
                suggestion["expected_improvement"] = 0.1
        
        # Add to retraining queue if needed
        if suggestion["needs_retraining"]:
            self.retraining_queue[agent_name] = suggestion
        
        return suggestion
    
    def auto_tune_configuration(self, current_config: Dict[str, Any],
                               performance_metrics: Dict[str, float]) -> List[ConfigurationTune]:
        """
        Auto-tune system configuration based on performance
        
        Args:
            current_config: Current configuration parameters
            performance_metrics: Recent performance metrics
            
        Returns:
            List of configuration tuning recommendations
        """
        tunes = []
        
        # Analyze performance metrics
        avg_response_time = performance_metrics.get("avg_response_time", 0)
        error_rate = performance_metrics.get("error_rate", 0)
        cost_per_hour = performance_metrics.get("cost_per_hour", 0)
        throughput = performance_metrics.get("throughput", 0)
        
        # Timeout tuning
        if avg_response_time > 0 and "agent_timeout" in current_config:
            current_timeout = current_config["agent_timeout"]
            
            if avg_response_time > current_timeout * 0.8:
                # Increase timeout
                tunes.append(ConfigurationTune(
                    parameter="agent_timeout",
                    current_value=current_timeout,
                    recommended_value=int(avg_response_time * 1.5),
                    reason=f"Average response time ({avg_response_time:.1f}s) approaching timeout",
                    impact="medium",
                    risk="low"
                ))
            elif avg_response_time < current_timeout * 0.3:
                # Decrease timeout for faster failure detection
                tunes.append(ConfigurationTune(
                    parameter="agent_timeout",
                    current_value=current_timeout,
                    recommended_value=max(60, int(avg_response_time * 3)),
                    reason="Timeout too high for actual response times",
                    impact="low",
                    risk="medium"
                ))
        
        # Parallelism tuning
        if "max_parallel_agents" in current_config:
            current_parallel = current_config["max_parallel_agents"]
            
            if error_rate > 0.1 and current_parallel > 3:
                # Reduce parallelism if high error rate
                tunes.append(ConfigurationTune(
                    parameter="max_parallel_agents",
                    current_value=current_parallel,
                    recommended_value=max(1, current_parallel - 1),
                    reason=f"High error rate ({error_rate:.1%}) may be due to resource contention",
                    impact="high",
                    risk="low"
                ))
            elif error_rate < 0.05 and throughput < current_parallel * 0.7:
                # Increase parallelism if underutilized
                tunes.append(ConfigurationTune(
                    parameter="max_parallel_agents",
                    current_value=current_parallel,
                    recommended_value=min(10, current_parallel + 1),
                    reason="System underutilized, can handle more parallel agents",
                    impact="high",
                    risk="medium"
                ))
        
        # Retry configuration
        if error_rate > 0.05 and "max_retries" in current_config:
            current_retries = current_config["max_retries"]
            
            if current_retries < 3:
                tunes.append(ConfigurationTune(
                    parameter="max_retries",
                    current_value=current_retries,
                    recommended_value=3,
                    reason=f"Error rate {error_rate:.1%} warrants more retry attempts",
                    impact="medium",
                    risk="low"
                ))
        
        # Cost optimization
        if cost_per_hour > 5.0 and "model_selection_strategy" in current_config:
            tunes.append(ConfigurationTune(
                parameter="model_selection_strategy",
                current_value=current_config["model_selection_strategy"],
                recommended_value="cost_optimized",
                reason=f"High cost (${cost_per_hour:.2f}/hour) - use cheaper models where possible",
                impact="high",
                risk="medium"
            ))
        
        # Cache configuration
        if "cache_ttl" in current_config:
            current_ttl = current_config["cache_ttl"]
            
            if cost_per_hour > 2.0 and current_ttl < 3600:
                tunes.append(ConfigurationTune(
                    parameter="cache_ttl",
                    current_value=current_ttl,
                    recommended_value=3600,
                    reason="Increase cache TTL to reduce API costs",
                    impact="medium",
                    risk="low"
                ))
        
        # Apply auto-tuning if enabled
        if self.enable_auto_tune:
            for tune in tunes:
                if tune.risk == "low" and tune.impact in ["high", "medium"]:
                    tune.applied = True
                    self._apply_configuration_tune(tune)
        
        # Store tuning recommendations
        self.config_tunes.extend(tunes)
        
        return tunes
    
    def _apply_configuration_tune(self, tune: ConfigurationTune):
        """Apply a configuration tune"""
        # Log the tuning action
        self.healing_history.append({
            "timestamp": time.time(),
            "action": "config_tune",
            "parameter": tune.parameter,
            "old_value": tune.current_value,
            "new_value": tune.recommended_value,
            "reason": tune.reason
        })
        
        # Track configuration history
        self.config_history[tune.parameter].append({
            "timestamp": time.time(),
            "value": tune.recommended_value,
            "reason": tune.reason
        })
        
        # Save healing history
        self._save_healing_history()
    
    def update_knowledge_base(self, category: str, title: str,
                             description: str, solution: str,
                             examples: List[Dict] = None) -> str:
        """
        Add or update knowledge base entry
        
        Args:
            category: Category of knowledge (error_fix, optimization, best_practice)
            title: Title of the entry
            description: Detailed description
            solution: Solution or recommendation
            examples: Optional examples
            
        Returns:
            Entry ID
        """
        entry_id = f"{category}_{hash(title) % 10000}"
        
        if entry_id in self.knowledge_base:
            # Update existing entry
            entry = self.knowledge_base[entry_id]
            entry.description = description
            entry.solution = solution
            if examples:
                entry.examples.extend(examples)
            entry.last_updated = time.time()
        else:
            # Create new entry
            entry = KnowledgeEntry(
                entry_id=entry_id,
                category=category,
                title=title,
                description=description,
                solution=solution,
                examples=examples or [],
                success_rate=0.0,
                usage_count=0,
                created=time.time(),
                last_updated=time.time()
            )
            self.knowledge_base[entry_id] = entry
        
        # Save knowledge base
        self._save_knowledge_base()
        
        return entry_id
    
    def _add_error_to_knowledge_base(self, pattern: ErrorPattern):
        """Add error pattern to knowledge base"""
        self.update_knowledge_base(
            category="error_fix",
            title=f"Error: {pattern.error_type}",
            description=f"Pattern: {pattern.pattern_text}",
            solution="\n".join(pattern.suggested_fixes),
            examples=[{
                "pattern_id": pattern.pattern_id,
                "occurrences": pattern.occurrences,
                "affected_agents": pattern.affected_agents
            }]
        )
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (0-1)"""
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def apply_auto_healing(self, error: Dict, agent_name: str,
                          context: Dict) -> Optional[Dict[str, Any]]:
        """
        Apply automatic healing for an error
        
        Args:
            error: Error information
            agent_name: Agent that encountered the error
            context: Execution context
            
        Returns:
            Healing action taken, or None if no action
        """
        if not self.enable_auto_fix:
            return None
        
        healing_action = None
        error_msg = error.get("message", "").lower()
        
        # Check knowledge base for solutions
        for entry in self.knowledge_base.values():
            if entry.category == "error_fix":
                if self._calculate_similarity(error_msg, entry.description) > 0.7:
                    # Apply known solution
                    healing_action = {
                        "type": "apply_knowledge",
                        "entry_id": entry.entry_id,
                        "solution": entry.solution,
                        "confidence": entry.success_rate
                    }
                    
                    # Update usage count
                    entry.usage_count += 1
                    break
        
        # If no knowledge base solution, try heuristic fixes
        if not healing_action:
            if "timeout" in error_msg:
                healing_action = {
                    "type": "increase_timeout",
                    "action": "Increasing timeout by 50%",
                    "confidence": 0.7
                }
            elif "rate limit" in error_msg:
                healing_action = {
                    "type": "add_delay",
                    "action": "Adding 5 second delay before retry",
                    "confidence": 0.8
                }
            elif "file not found" in error_msg:
                healing_action = {
                    "type": "create_directory",
                    "action": "Creating missing directories",
                    "confidence": 0.6
                }
        
        # Log healing action
        if healing_action:
            self.healing_history.append({
                "timestamp": time.time(),
                "error": error_msg,
                "agent": agent_name,
                "action": healing_action,
                "context": context
            })
            
            # Save history periodically
            if len(self.healing_history) % 10 == 0:
                self._save_healing_history()
        
        return healing_action
    
    def get_healing_recommendations(self) -> Dict[str, Any]:
        """Get comprehensive healing recommendations"""
        recommendations = {
            "error_patterns": [],
            "prompt_optimizations": [],
            "retraining_needed": [],
            "config_tunes": [],
            "knowledge_updates": [],
            "summary": {}
        }
        
        # Error patterns with high occurrence
        for pattern_id, pattern in self.error_patterns.items():
            if pattern.occurrences > 5 and not pattern.auto_fixed:
                recommendations["error_patterns"].append({
                    "pattern_id": pattern_id,
                    "type": pattern.error_type,
                    "occurrences": pattern.occurrences,
                    "affected_agents": pattern.affected_agents,
                    "suggested_fixes": pattern.suggested_fixes
                })
        
        # Recent prompt optimizations
        for agent_name, optimizations in self.prompt_optimizations.items():
            if optimizations:
                latest = optimizations[-1]
                if not latest.applied:
                    recommendations["prompt_optimizations"].append({
                        "agent": agent_name,
                        "reason": latest.reason,
                        "expected_improvement": latest.expected_improvement
                    })
        
        # Agents needing retraining
        for agent_name, suggestion in self.retraining_queue.items():
            if suggestion["needs_retraining"]:
                recommendations["retraining_needed"].append({
                    "agent": agent_name,
                    "urgency": suggestion["urgency"],
                    "reasons": suggestion["reasons"],
                    "actions": suggestion["recommended_actions"]
                })
        
        # Configuration tunes
        for tune in self.config_tunes:
            if not tune.applied:
                recommendations["config_tunes"].append({
                    "parameter": tune.parameter,
                    "current": tune.current_value,
                    "recommended": tune.recommended_value,
                    "reason": tune.reason,
                    "impact": tune.impact,
                    "risk": tune.risk
                })
        
        # Knowledge base updates
        recent_entries = sorted(
            self.knowledge_base.values(),
            key=lambda x: x.last_updated,
            reverse=True
        )[:5]
        
        for entry in recent_entries:
            recommendations["knowledge_updates"].append({
                "category": entry.category,
                "title": entry.title,
                "usage_count": entry.usage_count,
                "success_rate": entry.success_rate
            })
        
        # Summary statistics
        recommendations["summary"] = {
            "total_error_patterns": len(self.error_patterns),
            "active_patterns": sum(1 for p in self.error_patterns.values() if not p.auto_fixed),
            "agents_needing_retraining": len(self.retraining_queue),
            "pending_config_tunes": sum(1 for t in self.config_tunes if not t.applied),
            "knowledge_base_size": len(self.knowledge_base),
            "healing_actions_taken": len(self.healing_history)
        }
        
        return recommendations


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Create self-healing system
    healer = SelfHealingSystem()
    
    # Simulate errors
    print("Simulating errors...")
    errors = [
        {"message": "Timeout exceeded while executing agent", "agent": "ai-specialist", "timestamp": time.time()},
        {"message": "Timeout error in processing", "agent": "ai-specialist", "timestamp": time.time()},
        {"message": "Rate limit exceeded for API calls", "agent": "rapid-builder", "timestamp": time.time()},
        {"message": "File not found: /project/config.json", "agent": "frontend-specialist", "timestamp": time.time()},
        {"message": "File not found: /project/data.csv", "agent": "database-expert", "timestamp": time.time()},
        {"message": "Syntax error in generated code", "agent": "rapid-builder", "timestamp": time.time()}
    ]
    
    # Detect patterns
    patterns = healer.detect_error_patterns(errors)
    print(f"\nDetected {len(patterns)} error patterns:")
    for pattern in patterns:
        print(f"  - {pattern.error_type}: {pattern.pattern_text[:50]}... ({pattern.occurrences} occurrences)")
        print(f"    Suggested fixes: {pattern.suggested_fixes[:2]}")
    
    # Test prompt optimization
    print("\nTesting prompt optimization...")
    current_prompt = "You are an AI specialist. Generate AI integration code."
    failure_history = [
        {"type": "timeout", "context": "Complex model training"},
        {"type": "error", "context": "API rate limit"},
        {"type": "misunderstanding", "context": "Unclear requirements"}
    ]
    
    optimization = healer.optimize_prompt("ai-specialist", current_prompt, failure_history)
    print(f"  Original prompt length: {len(current_prompt)}")
    print(f"  Optimized prompt length: {len(optimization.optimized_prompt)}")
    print(f"  Reason: {optimization.reason}")
    print(f"  Expected improvement: {optimization.expected_improvement:.1%}")
    
    # Test agent retraining suggestion
    print("\nTesting retraining suggestions...")
    performance_data = {
        "success_rate": 0.65,
        "avg_quality_score": 0.7,
        "trend": "degrading",
        "tool_failures": 8
    }
    
    suggestion = healer.suggest_agent_retraining("rapid-builder", performance_data)
    if suggestion["needs_retraining"]:
        print(f"  Agent: {suggestion['agent']}")
        print(f"  Urgency: {suggestion['urgency']}")
        print(f"  Reasons: {suggestion['reasons']}")
        print(f"  Recommended actions: {len(suggestion['recommended_actions'])} actions")
    
    # Test configuration auto-tuning
    print("\nTesting configuration auto-tuning...")
    current_config = {
        "agent_timeout": 300,
        "max_parallel_agents": 5,
        "max_retries": 2,
        "model_selection_strategy": "performance",
        "cache_ttl": 600
    }
    
    performance_metrics = {
        "avg_response_time": 280,
        "error_rate": 0.12,
        "cost_per_hour": 6.5,
        "throughput": 2.5
    }
    
    tunes = healer.auto_tune_configuration(current_config, performance_metrics)
    print(f"  Generated {len(tunes)} tuning recommendations:")
    for tune in tunes[:3]:
        print(f"    - {tune.parameter}: {tune.current_value} → {tune.recommended_value}")
        print(f"      Reason: {tune.reason}")
        print(f"      Impact: {tune.impact}, Risk: {tune.risk}")
    
    # Test auto-healing
    print("\nTesting auto-healing...")
    error = {"message": "Timeout exceeded while executing agent"}
    healing = healer.apply_auto_healing(error, "ai-specialist", {"task": "training"})
    if healing:
        print(f"  Healing action: {healing['type']}")
        print(f"  Details: {healing.get('action', healing.get('solution', 'N/A'))}")
        print(f"  Confidence: {healing.get('confidence', 0):.1%}")
    
    # Get comprehensive recommendations
    print("\n=== Healing Recommendations ===")
    recommendations = healer.get_healing_recommendations()
    print(f"Summary:")
    for key, value in recommendations["summary"].items():
        print(f"  {key}: {value}")
    
    # Update knowledge base
    print("\nUpdating knowledge base...")
    entry_id = healer.update_knowledge_base(
        category="best_practice",
        title="Optimal timeout configuration",
        description="Set timeouts based on historical execution times",
        solution="Use 2x average execution time with minimum of 60 seconds",
        examples=[{"config": "timeout = max(60, avg_time * 2)"}]
    )
    print(f"  Added knowledge entry: {entry_id}")
    
    print("\nSelf-healing system demonstration complete!")