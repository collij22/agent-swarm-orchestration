#!/usr/bin/env python3
"""
Validation Orchestrator Layer
Provides pre-execution dependency checks, post-execution validation, and automatic retry logic
"""

import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from pathlib import Path

# Import existing components
try:
    from .agent_validator import AgentValidator, ValidationResult, ValidationCheck
    from .requirement_tracker import RequirementTracker, RequirementStatus
    from .agent_runtime import AgentContext
except ImportError:
    # For standalone imports
    from agent_validator import AgentValidator, ValidationResult, ValidationCheck
    from requirement_tracker import RequirementTracker, RequirementStatus
    from agent_runtime import AgentContext


class RetryStrategy(Enum):
    """Retry strategies for failed validations"""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    WITH_SUGGESTIONS = "with_suggestions"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ValidationCheckpoint:
    """Checkpoint for validation state"""
    agent_name: str
    timestamp: datetime
    pre_validation_passed: bool
    post_validation_passed: Optional[bool] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_suggestions: List[str] = None
    validation_errors: List[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "pre_validation_passed": self.pre_validation_passed,
            "post_validation_passed": self.post_validation_passed,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "retry_suggestions": self.retry_suggestions or [],
            "validation_errors": self.validation_errors or []
        }


class ValidationOrchestrator:
    """
    Orchestrates validation before and after agent execution with retry logic
    """
    
    def __init__(self, requirement_tracker: RequirementTracker = None, 
                 agent_validator: AgentValidator = None):
        """Initialize with optional requirement tracker and validator"""
        self.requirement_tracker = requirement_tracker or RequirementTracker()
        self.agent_validator = agent_validator or AgentValidator()
        self.checkpoints: List[ValidationCheckpoint] = []
        self.validation_history: Dict[str, List[ValidationCheckpoint]] = {}
        
    def pre_execution_validation(self, agent_name: str, context: AgentContext) -> Tuple[bool, List[str], List[str]]:
        """
        Validate dependencies before agent execution
        
        Returns:
            Tuple of (validation_passed, missing_dependencies, suggestions)
        """
        missing_deps = []
        suggestions = []
        
        # Check agent dependencies from context
        deps_met, missing = context.check_dependencies(agent_name)
        if not deps_met:
            missing_deps.extend(missing)
            
        # Check requirement dependencies
        agent_reqs = self.requirement_tracker.agent_assignments.get(agent_name, [])
        for req_id in agent_reqs:
            req = self.requirement_tracker.requirements.get(req_id)
            if req and req.dependencies:
                for dep_id in req.dependencies:
                    dep_req = self.requirement_tracker.requirements.get(dep_id)
                    if dep_req and dep_req.status != RequirementStatus.COMPLETED:
                        missing_deps.append(f"Requirement {dep_id} not completed")
                        
        # Generate suggestions based on missing dependencies
        if missing_deps:
            suggestions = self._generate_dependency_suggestions(agent_name, missing_deps)
            
        # Create checkpoint
        checkpoint = ValidationCheckpoint(
            agent_name=agent_name,
            timestamp=datetime.now(),
            pre_validation_passed=len(missing_deps) == 0,
            validation_errors=missing_deps,
            retry_suggestions=suggestions
        )
        self.checkpoints.append(checkpoint)
        
        return len(missing_deps) == 0, missing_deps, suggestions
    
    def post_execution_validation(self, agent_name: str, context: AgentContext,
                                 output: Any = None) -> Tuple[bool, List[str], List[str]]:
        """
        Validate agent output after execution
        
        Returns:
            Tuple of (validation_passed, validation_errors, retry_suggestions)
        """
        validation_errors = []
        retry_suggestions = []
        
        # Run agent-specific validations
        if agent_name in self.agent_validator.validation_rules:
            for check in self.agent_validator.validation_rules[agent_name]:
                result, message = check.execute(context)
                if result == ValidationResult.FAILED:
                    validation_errors.append(f"{check.name}: {check.description} - {message}")
                    if check.retry_on_fail:
                        retry_suggestions.append(f"Retry {check.name} with: {message}")
        
        # Check if agent completed its assigned requirements
        agent_reqs = self.requirement_tracker.agent_assignments.get(agent_name, [])
        for req_id in agent_reqs:
            req = self.requirement_tracker.requirements.get(req_id)
            if req:
                # Check if expected deliverables were created
                missing_deliverables = []
                for deliverable in req.deliverables:
                    if deliverable not in req.actual_deliverables:
                        # Check if file exists in context
                        if not self._check_deliverable_exists(deliverable, context):
                            missing_deliverables.append(deliverable)
                
                if missing_deliverables:
                    validation_errors.append(
                        f"Requirement {req_id}: Missing deliverables: {', '.join(missing_deliverables)}"
                    )
                    retry_suggestions.append(
                        f"Create missing deliverables for {req_id}: {', '.join(missing_deliverables)}"
                    )
        
        # Update checkpoint
        if self.checkpoints:
            checkpoint = self.checkpoints[-1]
            if checkpoint.agent_name == agent_name:
                checkpoint.post_validation_passed = len(validation_errors) == 0
                checkpoint.validation_errors = validation_errors
                checkpoint.retry_suggestions = retry_suggestions
        
        # Store in history
        if agent_name not in self.validation_history:
            self.validation_history[agent_name] = []
        self.validation_history[agent_name].append(checkpoint)
        
        return len(validation_errors) == 0, validation_errors, retry_suggestions
    
    async def execute_with_validation_and_retry(self, agent_name: str, 
                                               agent_executor: Callable,
                                               context: AgentContext,
                                               max_retries: int = 3,
                                               retry_strategy: RetryStrategy = RetryStrategy.WITH_SUGGESTIONS) -> Tuple[bool, Any, AgentContext]:
        """
        Execute agent with validation and automatic retry logic
        
        Args:
            agent_name: Name of the agent
            agent_executor: Async function to execute the agent
            context: Agent context
            max_retries: Maximum number of retry attempts
            retry_strategy: Strategy for retrying
            
        Returns:
            Tuple of (success, result, updated_context)
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= max_retries:
            # Pre-execution validation
            pre_valid, missing_deps, suggestions = self.pre_execution_validation(agent_name, context)
            
            if not pre_valid:
                if retry_strategy == RetryStrategy.MANUAL_INTERVENTION:
                    print(f"\n⚠️  Agent {agent_name} requires manual intervention:")
                    print(f"   Missing dependencies: {', '.join(missing_deps)}")
                    print(f"   Suggestions: {', '.join(suggestions)}")
                    return False, f"Manual intervention required: {missing_deps}", context
                
                # Try to resolve dependencies automatically
                if retry_count < max_retries:
                    await self._attempt_dependency_resolution(agent_name, missing_deps, context)
                    retry_count += 1
                    continue
                else:
                    return False, f"Failed to resolve dependencies after {max_retries} attempts", context
            
            # Execute agent
            try:
                success, result, updated_context = await agent_executor(agent_name, context)
                
                if not success:
                    last_error = result
                    if retry_count < max_retries:
                        retry_count += 1
                        await self._apply_retry_strategy(retry_strategy, retry_count)
                        continue
                    else:
                        return False, f"Agent execution failed after {max_retries} attempts: {last_error}", context
                
                # Post-execution validation
                post_valid, validation_errors, retry_suggestions = self.post_execution_validation(
                    agent_name, updated_context, result
                )
                
                if not post_valid:
                    if retry_count < max_retries:
                        # Apply suggestions and retry
                        if retry_suggestions:
                            print(f"\n🔄 Retrying {agent_name} with suggestions:")
                            for suggestion in retry_suggestions:
                                print(f"   - {suggestion}")
                        
                        retry_count += 1
                        await self._apply_retry_strategy(retry_strategy, retry_count)
                        
                        # Update context with suggestions for next attempt
                        if "retry_suggestions" not in updated_context.artifacts:
                            updated_context.artifacts["retry_suggestions"] = {}
                        updated_context.artifacts["retry_suggestions"][agent_name] = retry_suggestions
                        
                        context = updated_context
                        continue
                    else:
                        # Max retries reached, but execution was successful
                        # Return with warnings
                        print(f"\n⚠️  {agent_name} completed with validation warnings:")
                        for error in validation_errors:
                            print(f"   - {error}")
                        return True, result, updated_context
                
                # Success!
                return True, result, updated_context
                
            except Exception as e:
                last_error = str(e)
                if retry_count < max_retries:
                    retry_count += 1
                    await self._apply_retry_strategy(retry_strategy, retry_count)
                    continue
                else:
                    return False, f"Agent execution failed with exception: {last_error}", context
        
        return False, f"Max retries ({max_retries}) exceeded", context
    
    async def _apply_retry_strategy(self, strategy: RetryStrategy, retry_count: int):
        """Apply retry strategy with appropriate delays"""
        if strategy == RetryStrategy.IMMEDIATE:
            await asyncio.sleep(1)  # Brief pause
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(30, 2 ** retry_count)  # Max 30 seconds
            print(f"   Waiting {delay} seconds before retry...")
            await asyncio.sleep(delay)
        elif strategy == RetryStrategy.WITH_SUGGESTIONS:
            # Pause to allow suggestions to be processed
            await asyncio.sleep(3)
    
    async def _attempt_dependency_resolution(self, agent_name: str, 
                                            missing_deps: List[str], 
                                            context: AgentContext):
        """Attempt to automatically resolve missing dependencies"""
        print(f"\n🔧 Attempting to resolve dependencies for {agent_name}:")
        for dep in missing_deps:
            print(f"   - Resolving: {dep}")
            # Add logic here to attempt resolution
            # For now, just log the attempt
            await asyncio.sleep(1)
    
    def _generate_dependency_suggestions(self, agent_name: str, 
                                        missing_deps: List[str]) -> List[str]:
        """Generate suggestions for resolving missing dependencies"""
        suggestions = []
        
        for dep in missing_deps:
            if "File not found" in dep:
                suggestions.append(f"Ensure previous agents created required files")
            elif "Requirement" in dep and "not completed" in dep:
                req_id = dep.split()[1]
                suggestions.append(f"Complete requirement {req_id} before proceeding")
            elif "artifact" in dep.lower():
                suggestions.append(f"Request artifact using request_artifact tool")
            else:
                suggestions.append(f"Verify {dep} is available in context")
        
        return suggestions
    
    def _check_deliverable_exists(self, deliverable: str, context: AgentContext) -> bool:
        """Check if a deliverable exists in the context or file system"""
        # Check in created files
        all_files = context.get_all_files()
        for file_path in all_files:
            if deliverable in file_path or Path(file_path).name == deliverable:
                return True
        
        # Check in artifacts
        if deliverable in context.artifacts:
            return True
        
        # Check file system
        if Path(deliverable).exists():
            return True
        
        return False
    
    def generate_validation_report(self) -> Dict:
        """Generate a comprehensive validation report"""
        report = {
            "total_validations": len(self.checkpoints),
            "passed_pre_validation": sum(1 for c in self.checkpoints if c.pre_validation_passed),
            "passed_post_validation": sum(1 for c in self.checkpoints if c.post_validation_passed),
            "agents_with_retries": {},
            "validation_errors_summary": [],
            "suggestions_applied": []
        }
        
        # Analyze retry patterns
        for agent_name, history in self.validation_history.items():
            retries = sum(c.retry_count for c in history)
            if retries > 0:
                report["agents_with_retries"][agent_name] = {
                    "total_retries": retries,
                    "max_retries": max(c.retry_count for c in history),
                    "final_status": "passed" if history[-1].post_validation_passed else "failed"
                }
        
        # Collect all validation errors
        for checkpoint in self.checkpoints:
            if checkpoint.validation_errors:
                report["validation_errors_summary"].extend(checkpoint.validation_errors)
        
        return report
    
    def save_checkpoint(self, filepath: str):
        """Save current validation state to file"""
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "validation_history": {
                agent: [c.to_dict() for c in history]
                for agent, history in self.validation_history.items()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
    
    def load_checkpoint(self, filepath: str):
        """Load validation state from file"""
        with open(filepath, 'r') as f:
            checkpoint_data = json.load(f)
        
        # Restore checkpoints
        self.checkpoints = []
        for cp_data in checkpoint_data.get("checkpoints", []):
            checkpoint = ValidationCheckpoint(
                agent_name=cp_data["agent_name"],
                timestamp=datetime.fromisoformat(cp_data["timestamp"]),
                pre_validation_passed=cp_data["pre_validation_passed"],
                post_validation_passed=cp_data.get("post_validation_passed"),
                retry_count=cp_data.get("retry_count", 0),
                max_retries=cp_data.get("max_retries", 3),
                retry_suggestions=cp_data.get("retry_suggestions", []),
                validation_errors=cp_data.get("validation_errors", [])
            )
            self.checkpoints.append(checkpoint)
        
        # Restore history
        self.validation_history = {}
        for agent, history in checkpoint_data.get("validation_history", {}).items():
            self.validation_history[agent] = []
            for cp_data in history:
                checkpoint = ValidationCheckpoint(
                    agent_name=cp_data["agent_name"],
                    timestamp=datetime.fromisoformat(cp_data["timestamp"]),
                    pre_validation_passed=cp_data["pre_validation_passed"],
                    post_validation_passed=cp_data.get("post_validation_passed"),
                    retry_count=cp_data.get("retry_count", 0),
                    max_retries=cp_data.get("max_retries", 3),
                    retry_suggestions=cp_data.get("retry_suggestions", []),
                    validation_errors=cp_data.get("validation_errors", [])
                )
                self.validation_history[agent].append(checkpoint)


def create_validation_rules_for_agent(agent_name: str, requirements: List[str]) -> List[ValidationCheck]:
    """
    Create dynamic validation rules based on agent and requirements
    """
    rules = []
    
    # Add requirement-specific validations
    for req in requirements:
        if "authentication" in req.lower():
            rules.append(ValidationCheck(
                name=f"auth_requirement_{req}",
                description=f"Validate authentication implementation for {req}",
                validator=lambda ctx: _validate_auth_implementation(ctx),
                required=True,
                retry_on_fail=True
            ))
        
        if "api" in req.lower():
            rules.append(ValidationCheck(
                name=f"api_requirement_{req}",
                description=f"Validate API implementation for {req}",
                validator=lambda ctx: _validate_api_implementation(ctx),
                required=True,
                retry_on_fail=True
            ))
        
        if "database" in req.lower():
            rules.append(ValidationCheck(
                name=f"db_requirement_{req}",
                description=f"Validate database implementation for {req}",
                validator=lambda ctx: _validate_database_implementation(ctx),
                required=True,
                retry_on_fail=True
            ))
    
    return rules


def _validate_auth_implementation(context: AgentContext) -> Tuple[ValidationResult, str]:
    """Validate authentication implementation"""
    auth_files = ["auth.py", "authentication.py", "jwt_handler.py", "login.py"]
    found = False
    
    for file in context.get_all_files():
        if any(auth_file in file.lower() for auth_file in auth_files):
            found = True
            break
    
    if found:
        return ValidationResult.PASSED, "Authentication files found"
    else:
        return ValidationResult.FAILED, "No authentication implementation found"


def _validate_api_implementation(context: AgentContext) -> Tuple[ValidationResult, str]:
    """Validate API implementation"""
    api_patterns = ["routes", "endpoints", "api", "controllers"]
    found = False
    
    for file in context.get_all_files():
        if any(pattern in file.lower() for pattern in api_patterns):
            found = True
            break
    
    if found:
        return ValidationResult.PASSED, "API implementation found"
    else:
        return ValidationResult.FAILED, "No API routes or endpoints found"


def _validate_database_implementation(context: AgentContext) -> Tuple[ValidationResult, str]:
    """Validate database implementation"""
    db_patterns = ["models", "schema", "database", "migrations"]
    found = False
    
    for file in context.get_all_files():
        if any(pattern in file.lower() for pattern in db_patterns):
            found = True
            break
    
    if found:
        return ValidationResult.PASSED, "Database implementation found"
    else:
        return ValidationResult.FAILED, "No database models or schema found"