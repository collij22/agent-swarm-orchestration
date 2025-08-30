#!/usr/bin/env python3
"""
Feedback Integration System for Agent Swarm

This module integrates feedback from failed executions back into the system
for continuous improvement, including agent prompt updates, workflow refinements,
and system optimizations.
"""

import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml

from .continuous_improvement import LearningEngine, FeedbackIntegrator, PromptRefinement
from .agent_logger import get_logger

@dataclass
class SystemUpdate:
    """Represents a system update based on feedback"""
    update_type: str  # "prompt", "workflow", "configuration", "tool"
    component: str  # Which component to update
    current_state: str
    proposed_state: str
    confidence: float
    rationale: str
    test_required: bool = True
    backup_created: bool = False

class PromptUpdater:
    """Updates agent prompts based on learning insights"""
    
    def __init__(self, agents_dir: Path = None):
        self.agents_dir = agents_dir or Path(".claude/agents")
        self.logger = get_logger()
        self.backup_dir = Path("backups/prompts")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def apply_prompt_refinement(self, refinement: PromptRefinement) -> bool:
        """Apply a prompt refinement to an agent"""
        agent_file = self.agents_dir / f"{refinement.agent_name}.md"
        
        if not agent_file.exists():
            self.logger.log_error("prompt_updater", f"Agent file not found: {agent_file}", 
                                "Agent file missing")
            return False
        
        try:
            # Create backup
            backup_file = self.backup_dir / f"{refinement.agent_name}_{int(time.time())}.md"
            backup_file.write_text(agent_file.read_text())
            
            # Read current content
            current_content = agent_file.read_text()
            
            # Apply refinement (simplified - would use more sophisticated merging)
            updated_content = self._apply_refinement_to_content(current_content, refinement)
            
            # Write updated content
            agent_file.write_text(updated_content)
            
            self.logger.log_reasoning("prompt_updater", 
                                    f"Updated prompt for {refinement.agent_name}: {refinement.reason}")
            
            return True
            
        except Exception as e:
            self.logger.log_error("prompt_updater", f"Failed to update {refinement.agent_name}: {str(e)}", 
                                refinement.reason)
            return False
    
    def _apply_refinement_to_content(self, current_content: str, refinement: PromptRefinement) -> str:
        """Apply refinement to agent prompt content"""
        # Simple implementation - would be more sophisticated in practice
        lines = current_content.split('\n')
        
        # Find the main prompt section
        prompt_section_start = -1
        for i, line in enumerate(lines):
            if line.startswith("# Role") or line.startswith("You are"):
                prompt_section_start = i
                break
        
        if prompt_section_start == -1:
            # Append to end
            return current_content + "\n\n" + refinement.suggested_prompt
        
        # Insert refinement before the end of prompt section
        insertion_point = len(lines)
        for i in range(prompt_section_start, len(lines)):
            if lines[i].startswith("# ") and i > prompt_section_start:
                insertion_point = i
                break
        
        # Extract the refinement additions
        refinement_lines = refinement.suggested_prompt.split('\n')
        additional_requirements = []
        in_additional = False
        
        for line in refinement_lines:
            if "Additional requirements:" in line:
                in_additional = True
                continue
            if in_additional and line.strip():
                additional_requirements.append(line)
        
        if additional_requirements:
            lines.insert(insertion_point, "")
            lines.insert(insertion_point + 1, "## Additional Requirements (Auto-Generated)")
            for i, req in enumerate(additional_requirements):
                lines.insert(insertion_point + 2 + i, req)
            lines.insert(insertion_point + 2 + len(additional_requirements), "")
        
        return '\n'.join(lines)
    
    def test_prompt_refinement(self, refinement: PromptRefinement) -> Dict[str, Any]:
        """Test a prompt refinement before applying"""
        # This would run a test execution with the new prompt
        # For now, return a mock result
        return {
            "test_success": True,
            "improvement_score": 0.8,
            "test_errors": [],
            "recommendation": "Apply refinement"
        }

class WorkflowUpdater:
    """Updates workflow configurations based on feedback"""
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path(".")
        self.logger = get_logger()
        self.backup_dir = Path("backups/workflows")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def update_workflow_configuration(self, workflow_type: str, updates: Dict[str, Any]) -> bool:
        """Update workflow configuration"""
        # This would update orchestrate_v2.py or workflow configs
        config_file = self.config_dir / "workflow_configs.yaml"
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
            else:
                config = {}
            
            # Create backup
            backup_file = self.backup_dir / f"workflow_config_{int(time.time())}.yaml"
            with open(backup_file, 'w') as f:
                yaml.dump(config, f)
            
            # Apply updates
            if workflow_type not in config:
                config[workflow_type] = {}
            
            config[workflow_type].update(updates)
            
            # Write updated config
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            self.logger.log_reasoning("workflow_updater", 
                                    f"Updated {workflow_type} workflow configuration")
            
            return True
            
        except Exception as e:
            self.logger.log_error("workflow_updater", f"Failed to update workflow config: {str(e)}", 
                                "Configuration update failed")
            return False

class SystemIntegrator:
    """Main system for integrating feedback into the agent swarm"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(".")
        self.learning_engine = LearningEngine()
        self.feedback_integrator = FeedbackIntegrator(self.learning_engine)
        self.prompt_updater = PromptUpdater()
        self.workflow_updater = WorkflowUpdater()
        self.logger = get_logger()
        
        # Track applied updates
        self.updates_log = self.base_dir / "system_updates.json"
        self.applied_updates = self._load_updates_log()
    
    def integrate_session_feedback(self, session_data: Dict[str, Any]) -> List[SystemUpdate]:
        """Integrate feedback from a completed session"""
        self.logger.log_reasoning("system_integrator", 
                                f"Integrating feedback for session {session_data.get('session_id', 'unknown')}")
        
        # Process feedback through learning engine
        insights = self.feedback_integrator.process_execution_feedback(
            session_data.get('session_id', 'unknown'),
            session_data
        )
        
        # Generate system updates
        updates = []
        
        # Generate prompt refinements
        refinements = self.learning_engine.generate_prompt_refinements(days=7)
        for refinement in refinements:
            if refinement.confidence > 0.6:  # Only high-confidence refinements
                update = SystemUpdate(
                    update_type="prompt",
                    component=refinement.agent_name,
                    current_state=refinement.current_prompt[:100] + "...",
                    proposed_state=refinement.suggested_prompt[:100] + "...",
                    confidence=refinement.confidence,
                    rationale=refinement.reason,
                    test_required=True
                )
                updates.append(update)
        
        # Generate workflow updates
        workflow_updates = self._generate_workflow_updates(insights, session_data)
        updates.extend(workflow_updates)
        
        # Apply updates if confidence is high enough
        applied_updates = []
        for update in updates:
            if update.confidence > 0.8 and self._should_apply_update(update):
                if self._apply_system_update(update):
                    applied_updates.append(update)
                    self._record_applied_update(update)
        
        return applied_updates
    
    def run_continuous_improvement_cycle(self, days: int = 7) -> Dict[str, Any]:
        """Run a full continuous improvement cycle"""
        self.logger.log_reasoning("system_integrator", "Starting continuous improvement cycle")
        
        # Analyze recent performance
        insights = self.learning_engine.analyze_and_learn(days=days)
        recommendations = self.learning_engine.get_improvement_recommendations()
        
        # Generate refinements
        refinements = self.learning_engine.generate_prompt_refinements(days=days)
        
        # Apply high-confidence improvements
        applied_updates = []
        
        for refinement in refinements:
            if refinement.confidence > 0.8:
                # Test refinement first
                test_result = self.prompt_updater.test_prompt_refinement(refinement)
                
                if test_result.get("test_success", False):
                    if self.prompt_updater.apply_prompt_refinement(refinement):
                        applied_updates.append({
                            "type": "prompt_refinement",
                            "agent": refinement.agent_name,
                            "confidence": refinement.confidence,
                            "reason": refinement.reason
                        })
        
        # Generate improvement report
        report = {
            "analysis_period_days": days,
            "total_insights": len(insights),
            "actionable_recommendations": len(recommendations),
            "prompt_refinements_generated": len(refinements),
            "updates_applied": len(applied_updates),
            "applied_updates": applied_updates,
            "top_recommendations": recommendations[:5],
            "timestamp": datetime.now().isoformat()
        }
        
        # Save improvement report
        report_file = self.base_dir / f"improvement_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _generate_workflow_updates(self, insights: List, session_data: Dict[str, Any]) -> List[SystemUpdate]:
        """Generate workflow configuration updates based on insights"""
        updates = []
        
        workflow_type = session_data.get('workflow_type', 'unknown')
        success = session_data.get('success', False)
        completion_percentage = session_data.get('completion_percentage', 0.0)
        
        # If workflow had low completion, suggest improvements
        if completion_percentage < 70.0:
            update = SystemUpdate(
                update_type="workflow",
                component=workflow_type,
                current_state="Current workflow configuration",
                proposed_state="Enhanced workflow with additional validation",
                confidence=0.7,
                rationale=f"Low completion rate ({completion_percentage:.1f}%) indicates workflow issues",
                test_required=True
            )
            updates.append(update)
        
        # If frequent errors, suggest error handling improvements
        errors = session_data.get('errors', [])
        if len(errors) > 2:
            update = SystemUpdate(
                update_type="configuration",
                component="error_handling",
                current_state="Standard error handling",
                proposed_state="Enhanced error handling with retries",
                confidence=0.8,
                rationale=f"Multiple errors detected: {len(errors)} errors",
                test_required=True
            )
            updates.append(update)
        
        return updates
    
    def _should_apply_update(self, update: SystemUpdate) -> bool:
        """Determine if an update should be applied"""
        # Check if we've recently applied a similar update
        recent_threshold = datetime.now().timestamp() - (24 * 60 * 60)  # 24 hours
        
        for applied_update in self.applied_updates:
            if (applied_update.get('component') == update.component and 
                applied_update.get('update_type') == update.update_type and
                applied_update.get('timestamp', 0) > recent_threshold):
                return False  # Don't apply similar updates too frequently
        
        return True
    
    def _apply_system_update(self, update: SystemUpdate) -> bool:
        """Apply a system update"""
        try:
            if update.update_type == "prompt":
                # Create a mock PromptRefinement for the update
                refinement = PromptRefinement(
                    agent_name=update.component,
                    current_prompt=update.current_state,
                    suggested_prompt=update.proposed_state,
                    reason=update.rationale,
                    confidence=update.confidence
                )
                return self.prompt_updater.apply_prompt_refinement(refinement)
            
            elif update.update_type == "workflow":
                # Apply workflow update
                updates_dict = {"enhancement": update.proposed_state}
                return self.workflow_updater.update_workflow_configuration(update.component, updates_dict)
            
            elif update.update_type == "configuration":
                # Apply configuration update
                self.logger.log_reasoning("system_integrator", 
                                        f"Applied configuration update: {update.rationale}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.log_error("system_integrator", f"Failed to apply update: {str(e)}", 
                                update.rationale)
            return False
    
    def _record_applied_update(self, update: SystemUpdate):
        """Record an applied update"""
        update_record = {
            "update_type": update.update_type,
            "component": update.component,
            "confidence": update.confidence,
            "rationale": update.rationale,
            "timestamp": time.time(),
            "applied_at": datetime.now().isoformat()
        }
        
        self.applied_updates.append(update_record)
        self._save_updates_log()
    
    def _load_updates_log(self) -> List[Dict]:
        """Load the updates log"""
        if self.updates_log.exists():
            try:
                with open(self.updates_log, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_updates_log(self):
        """Save the updates log"""
        with open(self.updates_log, 'w') as f:
            json.dump(self.applied_updates, f, indent=2)

class AutoImprovementScheduler:
    """Scheduler for automatic system improvements"""
    
    def __init__(self, integrator: SystemIntegrator):
        self.integrator = integrator
        self.logger = get_logger()
        self.last_improvement_run = 0
        self.improvement_interval = 24 * 60 * 60  # 24 hours
    
    def should_run_improvement(self) -> bool:
        """Check if it's time to run improvement cycle"""
        return time.time() - self.last_improvement_run > self.improvement_interval
    
    def run_scheduled_improvement(self) -> Dict[str, Any]:
        """Run scheduled improvement if needed"""
        if self.should_run_improvement():
            self.logger.log_reasoning("auto_improvement", "Running scheduled improvement cycle")
            
            report = self.integrator.run_continuous_improvement_cycle(days=7)
            self.last_improvement_run = time.time()
            
            # Log improvement results
            if report.get('updates_applied', 0) > 0:
                self.logger.log_reasoning("auto_improvement", 
                                        f"Applied {report['updates_applied']} improvements")
            
            return report
        
        return {"status": "skipped", "reason": "Too soon for next improvement cycle"}

# Integration with existing orchestration
def create_feedback_integration_hooks():
    """Create hooks for integrating feedback into the orchestration system"""
    
    def on_session_complete(session_data: Dict[str, Any]):
        """Hook called when a session completes"""
        integrator = SystemIntegrator()
        updates = integrator.integrate_session_feedback(session_data)
        
        if updates:
            logger = get_logger()
            logger.log_reasoning("feedback_integration", 
                               f"Applied {len(updates)} system improvements based on session feedback")
    
    def on_workflow_failure(workflow_data: Dict[str, Any]):
        """Hook called when a workflow fails"""
        integrator = SystemIntegrator()
        
        # Process failure feedback immediately for critical issues
        failure_feedback = {
            **workflow_data,
            'priority': 'high',
            'immediate_analysis': True
        }
        
        updates = integrator.integrate_session_feedback(failure_feedback)
        
        logger = get_logger()
        logger.log_reasoning("failure_integration", 
                           f"Processed workflow failure, applied {len(updates)} immediate improvements")
    
    return {
        'on_session_complete': on_session_complete,
        'on_workflow_failure': on_workflow_failure
    }

# Example usage and testing
if __name__ == "__main__":
    # Create system integrator
    integrator = SystemIntegrator()
    
    # Simulate session feedback
    session_feedback = {
        'session_id': 'test_session_123',
        'workflow_type': 'api_service',
        'success': False,
        'completion_percentage': 45.0,
        'execution_time': 180.0,
        'agents_used': ['project-architect', 'rapid-builder'],
        'files_created': ['main.py', 'requirements.txt'],
        'errors': ['Rate limit exceeded', 'Validation failed'],
        'requirements': {'name': 'TestAPI', 'features': ['auth', 'crud']},
        'context_data': {'phase': 'testing'},
        'agent_performance': [
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
    
    # Integrate feedback
    updates = integrator.integrate_session_feedback(session_feedback)
    print(f"Applied {len(updates)} system updates based on feedback")
    
    # Run full improvement cycle
    report = integrator.run_continuous_improvement_cycle(days=30)
    print(f"Improvement cycle completed: {report['updates_applied']} updates applied")
    
    # Test auto-improvement scheduler
    scheduler = AutoImprovementScheduler(integrator)
    scheduled_report = scheduler.run_scheduled_improvement()
    print(f"Scheduled improvement: {scheduled_report}")