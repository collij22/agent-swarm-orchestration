#!/usr/bin/env python3
"""
Continuous Improvement and Learning System

This module implements automated learning from workflow executions,
pattern recognition from failures, and agent prompt refinement based
on results.
"""

import json
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re

@dataclass
class ExecutionPattern:
    """Pattern extracted from execution data"""
    pattern_type: str  # "failure", "success", "performance"
    context: Dict[str, Any]
    frequency: int
    confidence: float
    first_seen: datetime
    last_seen: datetime
    suggested_action: Optional[str] = None

@dataclass
class LearningInsight:
    """Insight derived from execution patterns"""
    insight_type: str
    description: str
    evidence: List[str]
    impact_score: float  # 0-1
    actionable: bool
    proposed_changes: List[str]

@dataclass
class PromptRefinement:
    """Suggested refinement for agent prompts"""
    agent_name: str
    current_prompt: str
    suggested_prompt: str
    reason: str
    confidence: float
    test_results: Optional[Dict] = None

class ExecutionDatabase:
    """Database for storing and analyzing execution data"""
    
    def __init__(self, db_path: str = "executions.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                workflow_type TEXT,
                timestamp TEXT,
                success BOOLEAN,
                completion_percentage REAL,
                execution_time REAL,
                agents_used TEXT,  -- JSON list
                files_created TEXT,  -- JSON list
                errors TEXT,  -- JSON list
                requirements TEXT,  -- JSON dict
                context_data TEXT  -- JSON dict
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER,
                agent_name TEXT,
                success BOOLEAN,
                execution_time REAL,
                model_used TEXT,
                tools_used TEXT,  -- JSON list
                errors TEXT,  -- JSON list
                output_quality REAL,  -- 0-1 score
                FOREIGN KEY (execution_id) REFERENCES executions (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                context_hash TEXT UNIQUE,
                context TEXT,  -- JSON dict
                frequency INTEGER DEFAULT 1,
                confidence REAL,
                first_seen TEXT,
                last_seen TEXT,
                suggested_action TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT,
                description TEXT,
                evidence TEXT,  -- JSON list
                impact_score REAL,
                actionable BOOLEAN,
                proposed_changes TEXT,  -- JSON list
                created_at TEXT,
                status TEXT DEFAULT 'pending'  -- pending, applied, rejected
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_execution(self, session_id: str, workflow_type: str, success: bool,
                        completion_percentage: float, execution_time: float,
                        agents_used: List[str], files_created: List[str],
                        errors: List[str], requirements: Dict, context_data: Dict) -> int:
        """Record a workflow execution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO executions 
            (session_id, workflow_type, timestamp, success, completion_percentage,
             execution_time, agents_used, files_created, errors, requirements, context_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, workflow_type, datetime.now().isoformat(), success,
            completion_percentage, execution_time, json.dumps(agents_used),
            json.dumps(files_created), json.dumps(errors), json.dumps(requirements),
            json.dumps(context_data)
        ))
        
        execution_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return execution_id
    
    def record_agent_performance(self, execution_id: int, agent_name: str,
                               success: bool, execution_time: float, model_used: str,
                               tools_used: List[str], errors: List[str],
                               output_quality: float = 0.0):
        """Record individual agent performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO agent_performance
            (execution_id, agent_name, success, execution_time, model_used,
             tools_used, errors, output_quality)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            execution_id, agent_name, success, execution_time, model_used,
            json.dumps(tools_used), json.dumps(errors), output_quality
        ))
        
        conn.commit()
        conn.close()
    
    def get_execution_history(self, days: int = 30) -> List[Dict]:
        """Get execution history for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT * FROM executions 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC
        ''', (cutoff_date,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            # Parse JSON fields
            for field in ['agents_used', 'files_created', 'errors', 'requirements', 'context_data']:
                if record[field]:
                    record[field] = json.loads(record[field])
            results.append(record)
        
        conn.close()
        return results
    
    def get_agent_performance_history(self, agent_name: Optional[str] = None,
                                    days: int = 30) -> List[Dict]:
        """Get agent performance history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        if agent_name:
            cursor.execute('''
                SELECT ap.*, e.timestamp FROM agent_performance ap
                JOIN executions e ON ap.execution_id = e.id
                WHERE ap.agent_name = ? AND e.timestamp > ?
                ORDER BY e.timestamp DESC
            ''', (agent_name, cutoff_date))
        else:
            cursor.execute('''
                SELECT ap.*, e.timestamp FROM agent_performance ap
                JOIN executions e ON ap.execution_id = e.id
                WHERE e.timestamp > ?
                ORDER BY e.timestamp DESC
            ''', (cutoff_date,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            # Parse JSON fields
            for field in ['tools_used', 'errors']:
                if record[field]:
                    record[field] = json.loads(record[field])
            results.append(record)
        
        conn.close()
        return results

class PatternAnalyzer:
    """Analyzes execution patterns to identify improvements"""
    
    def __init__(self, db: ExecutionDatabase):
        self.db = db
    
    def analyze_failure_patterns(self, days: int = 30) -> List[ExecutionPattern]:
        """Analyze failure patterns in recent executions"""
        executions = self.db.get_execution_history(days)
        failed_executions = [e for e in executions if not e['success']]
        
        patterns = []
        
        # Group by error types
        error_groups = defaultdict(list)
        for execution in failed_executions:
            for error in execution.get('errors', []):
                error_type = self._classify_error(error)
                error_groups[error_type].append(execution)
        
        for error_type, executions_with_error in error_groups.items():
            if len(executions_with_error) >= 2:  # Pattern threshold
                pattern = ExecutionPattern(
                    pattern_type="failure",
                    context={
                        "error_type": error_type,
                        "affected_workflows": list(set(e['workflow_type'] for e in executions_with_error)),
                        "common_agents": self._find_common_agents(executions_with_error)
                    },
                    frequency=len(executions_with_error),
                    confidence=min(1.0, len(executions_with_error) / 10),
                    first_seen=datetime.fromisoformat(min(e['timestamp'] for e in executions_with_error)),
                    last_seen=datetime.fromisoformat(max(e['timestamp'] for e in executions_with_error)),
                    suggested_action=self._suggest_failure_fix(error_type, executions_with_error)
                )
                patterns.append(pattern)
        
        # Analyze workflow-specific failures
        workflow_failures = defaultdict(list)
        for execution in failed_executions:
            workflow_failures[execution['workflow_type']].append(execution)
        
        for workflow_type, failures in workflow_failures.items():
            if len(failures) >= 3:  # Workflow pattern threshold
                pattern = ExecutionPattern(
                    pattern_type="workflow_failure",
                    context={
                        "workflow_type": workflow_type,
                        "failure_rate": len(failures) / len([e for e in executions if e['workflow_type'] == workflow_type]),
                        "common_errors": self._find_common_errors(failures)
                    },
                    frequency=len(failures),
                    confidence=0.8,
                    first_seen=datetime.fromisoformat(min(f['timestamp'] for f in failures)),
                    last_seen=datetime.fromisoformat(max(f['timestamp'] for f in failures)),
                    suggested_action=f"Review and improve {workflow_type} workflow configuration"
                )
                patterns.append(pattern)
        
        return patterns
    
    def analyze_performance_patterns(self, days: int = 30) -> List[ExecutionPattern]:
        """Analyze performance patterns"""
        agent_performance = self.db.get_agent_performance_history(days=days)
        
        patterns = []
        
        # Group by agent
        agent_groups = defaultdict(list)
        for perf in agent_performance:
            agent_groups[perf['agent_name']].append(perf)
        
        for agent_name, performances in agent_groups.items():
            if len(performances) >= 5:  # Minimum data points
                avg_time = sum(p['execution_time'] for p in performances) / len(performances)
                success_rate = sum(1 for p in performances if p['success']) / len(performances)
                
                if avg_time > 60:  # Slow performance threshold
                    pattern = ExecutionPattern(
                        pattern_type="slow_performance",
                        context={
                            "agent_name": agent_name,
                            "avg_execution_time": avg_time,
                            "slowest_time": max(p['execution_time'] for p in performances),
                            "model_usage": Counter(p['model_used'] for p in performances)
                        },
                        frequency=len(performances),
                        confidence=0.7,
                        first_seen=datetime.fromisoformat(min(p['timestamp'] for p in performances)),
                        last_seen=datetime.fromisoformat(max(p['timestamp'] for p in performances)),
                        suggested_action=f"Consider optimizing {agent_name} or using a faster model"
                    )
                    patterns.append(pattern)
                
                if success_rate < 0.8:  # Low success rate threshold
                    pattern = ExecutionPattern(
                        pattern_type="low_success_rate",
                        context={
                            "agent_name": agent_name,
                            "success_rate": success_rate,
                            "common_errors": self._analyze_agent_errors(performances)
                        },
                        frequency=len(performances),
                        confidence=0.9,
                        first_seen=datetime.fromisoformat(min(p['timestamp'] for p in performances)),
                        last_seen=datetime.fromisoformat(max(p['timestamp'] for p in performances)),
                        suggested_action=f"Review and improve {agent_name} prompt and error handling"
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _classify_error(self, error: str) -> str:
        """Classify error into categories"""
        error_lower = error.lower()
        
        if "rate limit" in error_lower or "429" in error_lower:
            return "rate_limit"
        elif "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        elif "file not found" in error_lower or "no such file" in error_lower:
            return "file_not_found"
        elif "permission" in error_lower or "access denied" in error_lower:
            return "permission_error"
        elif "tool" in error_lower and "failed" in error_lower:
            return "tool_failure"
        elif "api" in error_lower and ("error" in error_lower or "failed" in error_lower):
            return "api_error"
        elif "validation" in error_lower or "invalid" in error_lower:
            return "validation_error"
        else:
            return "unknown_error"
    
    def _find_common_agents(self, executions: List[Dict]) -> List[str]:
        """Find agents common to multiple executions"""
        agent_counts = Counter()
        for execution in executions:
            for agent in execution.get('agents_used', []):
                agent_counts[agent] += 1
        
        return [agent for agent, count in agent_counts.most_common(3)]
    
    def _find_common_errors(self, executions: List[Dict]) -> List[str]:
        """Find common errors across executions"""
        error_counts = Counter()
        for execution in executions:
            for error in execution.get('errors', []):
                error_type = self._classify_error(error)
                error_counts[error_type] += 1
        
        return [error for error, count in error_counts.most_common(5)]
    
    def _analyze_agent_errors(self, performances: List[Dict]) -> List[str]:
        """Analyze common errors for an agent"""
        error_counts = Counter()
        for perf in performances:
            for error in perf.get('errors', []):
                error_type = self._classify_error(error)
                error_counts[error_type] += 1
        
        return [error for error, count in error_counts.most_common(3)]
    
    def _suggest_failure_fix(self, error_type: str, executions: List[Dict]) -> str:
        """Suggest fixes for common failure patterns"""
        suggestions = {
            "rate_limit": "Implement exponential backoff and reduce concurrent API calls",
            "timeout": "Increase timeout values and optimize agent prompts",
            "file_not_found": "Add file existence checks and improve file path handling",
            "permission_error": "Check file permissions and directory access rights",
            "tool_failure": "Add tool validation and error recovery mechanisms",
            "api_error": "Improve API error handling and add retry logic",
            "validation_error": "Enhance input validation and parameter checking",
            "unknown_error": "Add more detailed error logging and investigation"
        }
        
        return suggestions.get(error_type, "Investigate and improve error handling")

class LearningEngine:
    """Main engine for continuous improvement"""
    
    def __init__(self, db_path: str = "executions.db"):
        self.db = ExecutionDatabase(db_path)
        self.pattern_analyzer = PatternAnalyzer(self.db)
        self.insights: List[LearningInsight] = []
    
    def analyze_and_learn(self, days: int = 30) -> List[LearningInsight]:
        """Perform comprehensive analysis and generate learning insights"""
        self.insights = []
        
        # Analyze failure patterns
        failure_patterns = self.pattern_analyzer.analyze_failure_patterns(days)
        for pattern in failure_patterns:
            insight = self._pattern_to_insight(pattern)
            if insight:
                self.insights.append(insight)
        
        # Analyze performance patterns
        performance_patterns = self.pattern_analyzer.analyze_performance_patterns(days)
        for pattern in performance_patterns:
            insight = self._pattern_to_insight(pattern)
            if insight:
                self.insights.append(insight)
        
        # Analyze workflow effectiveness
        workflow_insights = self._analyze_workflow_effectiveness(days)
        self.insights.extend(workflow_insights)
        
        # Store insights
        self._store_insights()
        
        return self.insights
    
    def generate_prompt_refinements(self, days: int = 30) -> List[PromptRefinement]:
        """Generate suggested prompt refinements based on analysis"""
        refinements = []
        
        agent_performance = self.db.get_agent_performance_history(days=days)
        
        # Group by agent
        agent_groups = defaultdict(list)
        for perf in agent_performance:
            agent_groups[perf['agent_name']].append(perf)
        
        for agent_name, performances in agent_groups.items():
            if len(performances) < 3:
                continue
                
            success_rate = sum(1 for p in performances if p['success']) / len(performances)
            avg_time = sum(p['execution_time'] for p in performances) / len(performances)
            common_errors = self.pattern_analyzer._analyze_agent_errors(performances)
            
            if success_rate < 0.8 or avg_time > 120 or common_errors:
                refinement = self._generate_prompt_refinement(
                    agent_name, success_rate, avg_time, common_errors
                )
                if refinement:
                    refinements.append(refinement)
        
        return refinements
    
    def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """Get actionable improvement recommendations"""
        recommendations = []
        
        for insight in self.insights:
            if insight.actionable and insight.impact_score > 0.5:
                recommendations.append({
                    "category": insight.insight_type,
                    "description": insight.description,
                    "impact": insight.impact_score,
                    "actions": insight.proposed_changes,
                    "evidence": insight.evidence
                })
        
        # Sort by impact score
        recommendations.sort(key=lambda x: x['impact'], reverse=True)
        
        return recommendations
    
    def _pattern_to_insight(self, pattern: ExecutionPattern) -> Optional[LearningInsight]:
        """Convert execution pattern to learning insight"""
        if pattern.pattern_type == "failure":
            return LearningInsight(
                insight_type="failure_reduction",
                description=f"Frequent {pattern.context['error_type']} errors detected",
                evidence=[
                    f"Occurred {pattern.frequency} times",
                    f"Affects workflows: {', '.join(pattern.context['affected_workflows'])}",
                    f"Common agents: {', '.join(pattern.context['common_agents'])}"
                ],
                impact_score=min(1.0, pattern.frequency / 10),
                actionable=True,
                proposed_changes=[pattern.suggested_action]
            )
        
        elif pattern.pattern_type == "slow_performance":
            return LearningInsight(
                insight_type="performance_optimization",
                description=f"Agent {pattern.context['agent_name']} showing slow performance",
                evidence=[
                    f"Average execution time: {pattern.context['avg_execution_time']:.1f}s",
                    f"Slowest execution: {pattern.context['slowest_time']:.1f}s"
                ],
                impact_score=0.7,
                actionable=True,
                proposed_changes=[pattern.suggested_action]
            )
        
        elif pattern.pattern_type == "low_success_rate":
            return LearningInsight(
                insight_type="reliability_improvement",
                description=f"Agent {pattern.context['agent_name']} has low success rate",
                evidence=[
                    f"Success rate: {pattern.context['success_rate']:.1%}",
                    f"Common errors: {', '.join(pattern.context['common_errors'])}"
                ],
                impact_score=0.9,
                actionable=True,
                proposed_changes=[pattern.suggested_action]
            )
        
        return None
    
    def _analyze_workflow_effectiveness(self, days: int) -> List[LearningInsight]:
        """Analyze overall workflow effectiveness"""
        insights = []
        executions = self.db.get_execution_history(days)
        
        # Group by workflow type
        workflow_groups = defaultdict(list)
        for execution in executions:
            workflow_groups[execution['workflow_type']].append(execution)
        
        for workflow_type, workflow_executions in workflow_groups.items():
            if len(workflow_executions) < 3:
                continue
            
            success_rate = sum(1 for e in workflow_executions if e['success']) / len(workflow_executions)
            avg_completion = sum(e['completion_percentage'] for e in workflow_executions) / len(workflow_executions)
            avg_time = sum(e['execution_time'] for e in workflow_executions) / len(workflow_executions)
            
            if success_rate < 0.7:
                insights.append(LearningInsight(
                    insight_type="workflow_reliability",
                    description=f"Workflow {workflow_type} has low success rate",
                    evidence=[
                        f"Success rate: {success_rate:.1%}",
                        f"Average completion: {avg_completion:.1f}%",
                        f"Total executions: {len(workflow_executions)}"
                    ],
                    impact_score=0.8,
                    actionable=True,
                    proposed_changes=[f"Review and improve {workflow_type} workflow configuration"]
                ))
            
            if avg_completion < 75.0:
                insights.append(LearningInsight(
                    insight_type="completion_improvement",
                    description=f"Workflow {workflow_type} has low completion rates",
                    evidence=[
                        f"Average completion: {avg_completion:.1f}%",
                        f"Success rate: {success_rate:.1%}"
                    ],
                    impact_score=0.6,
                    actionable=True,
                    proposed_changes=[
                        f"Add more specific requirements validation for {workflow_type}",
                        "Improve agent coordination and handoff protocols"
                    ]
                ))
        
        return insights
    
    def _generate_prompt_refinement(self, agent_name: str, success_rate: float,
                                  avg_time: float, common_errors: List[str]) -> Optional[PromptRefinement]:
        """Generate prompt refinement suggestion"""
        current_prompt = self._get_current_prompt(agent_name)
        if not current_prompt:
            return None
        
        improvements = []
        
        if success_rate < 0.8:
            improvements.append("Add more explicit error handling instructions")
            improvements.append("Include validation steps in the workflow")
        
        if avg_time > 120:
            improvements.append("Streamline instructions to focus on essential tasks")
            improvements.append("Add time-based constraints")
        
        if "tool_failure" in common_errors:
            improvements.append("Add tool usage validation and retry logic")
        
        if "validation_error" in common_errors:
            improvements.append("Include input validation requirements")
        
        if not improvements:
            return None
        
        suggested_prompt = self._refine_prompt(current_prompt, improvements)
        
        return PromptRefinement(
            agent_name=agent_name,
            current_prompt=current_prompt,
            suggested_prompt=suggested_prompt,
            reason=f"Improve success rate ({success_rate:.1%}) and performance ({avg_time:.1f}s)",
            confidence=0.7
        )
    
    def _get_current_prompt(self, agent_name: str) -> Optional[str]:
        """Get current prompt for agent (stub - would read from agent files)"""
        # This would read from .claude/agents/{agent_name}.md
        return f"Current prompt for {agent_name} (placeholder)"
    
    def _refine_prompt(self, current_prompt: str, improvements: List[str]) -> str:
        """Generate refined prompt (simplified implementation)"""
        refinements = "\\n".join(f"- {improvement}" for improvement in improvements)
        return f"{current_prompt}\\n\\nAdditional requirements:\\n{refinements}"
    
    def _store_insights(self):
        """Store insights in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for insight in self.insights:
            cursor.execute('''
                INSERT INTO learning_insights
                (insight_type, description, evidence, impact_score, actionable, proposed_changes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                insight.insight_type,
                insight.description,
                json.dumps(insight.evidence),
                insight.impact_score,
                insight.actionable,
                json.dumps(insight.proposed_changes),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()

class FeedbackIntegrator:
    """Integrates feedback from failed executions into the system"""
    
    def __init__(self, learning_engine: LearningEngine):
        self.learning_engine = learning_engine
    
    def process_execution_feedback(self, session_id: str, feedback: Dict[str, Any]):
        """Process feedback from a completed execution"""
        # Record the execution in the database
        execution_id = self.learning_engine.db.record_execution(
            session_id=session_id,
            workflow_type=feedback.get('workflow_type', 'unknown'),
            success=feedback.get('success', False),
            completion_percentage=feedback.get('completion_percentage', 0.0),
            execution_time=feedback.get('execution_time', 0.0),
            agents_used=feedback.get('agents_used', []),
            files_created=feedback.get('files_created', []),
            errors=feedback.get('errors', []),
            requirements=feedback.get('requirements', {}),
            context_data=feedback.get('context_data', {})
        )
        
        # Record individual agent performance
        for agent_data in feedback.get('agent_performance', []):
            self.learning_engine.db.record_agent_performance(
                execution_id=execution_id,
                agent_name=agent_data.get('agent_name', ''),
                success=agent_data.get('success', False),
                execution_time=agent_data.get('execution_time', 0.0),
                model_used=agent_data.get('model_used', ''),
                tools_used=agent_data.get('tools_used', []),
                errors=agent_data.get('errors', []),
                output_quality=agent_data.get('output_quality', 0.0)
            )
        
        # Trigger immediate analysis if there are critical failures
        if not feedback.get('success', False) or feedback.get('completion_percentage', 0) < 50:
            insights = self.learning_engine.analyze_and_learn(days=7)  # Recent analysis
            return insights
        
        return []

def create_learning_system(db_path: str = "executions.db") -> Tuple[LearningEngine, FeedbackIntegrator]:
    """Create and initialize the continuous learning system"""
    learning_engine = LearningEngine(db_path)
    feedback_integrator = FeedbackIntegrator(learning_engine)
    
    return learning_engine, feedback_integrator

# Example usage
if __name__ == "__main__":
    # Create learning system
    learning_engine, feedback_integrator = create_learning_system()
    
    # Simulate some execution data
    feedback_data = {
        'workflow_type': 'api_service',
        'success': False,
        'completion_percentage': 45.0,
        'execution_time': 180.0,
        'agents_used': ['project-architect', 'rapid-builder'],
        'files_created': ['main.py', 'requirements.txt'],
        'errors': ['Rate limit exceeded', 'File not found: config.py'],
        'requirements': {'name': 'TestAPI', 'features': ['auth', 'crud']},
        'context_data': {'phase': 'testing'},
        'agent_performance': [
            {
                'agent_name': 'project-architect',
                'success': True,
                'execution_time': 60.0,
                'model_used': 'claude-opus-4',
                'tools_used': ['write_file', 'record_decision'],
                'errors': [],
                'output_quality': 0.8
            },
            {
                'agent_name': 'rapid-builder',
                'success': False,
                'execution_time': 120.0,
                'model_used': 'claude-sonnet-4',
                'tools_used': ['write_file', 'run_command'],
                'errors': ['Rate limit exceeded'],
                'output_quality': 0.4
            }
        ]
    }
    
    # Process feedback
    insights = feedback_integrator.process_execution_feedback("test_session_123", feedback_data)
    
    # Run analysis
    all_insights = learning_engine.analyze_and_learn(days=30)
    
    # Get recommendations
    recommendations = learning_engine.get_improvement_recommendations()
    
    # Generate prompt refinements
    refinements = learning_engine.generate_prompt_refinements(days=30)
    
    print(f"Generated {len(all_insights)} insights")
    print(f"Found {len(recommendations)} actionable recommendations")
    print(f"Suggested {len(refinements)} prompt refinements")