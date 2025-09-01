#!/usr/bin/env python3
"""
Enhanced Validation Orchestrator Layer
Provides comprehensive multi-stage validation, build testing, runtime verification,
and automated debugging workflows
"""

import json
import asyncio
import subprocess
import time
import re
import socket
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
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


class CompletionStage(Enum):
    """Multi-stage completion tracking for requirements"""
    NOT_STARTED = 0
    FILES_CREATED = 25  # Files created with proper structure
    COMPILATION_SUCCESS = 50  # Code compiles without errors
    BASIC_FUNCTIONALITY = 75  # Basic functionality works
    FULLY_VERIFIED = 100  # All features verified with tests


class ValidationLevel(Enum):
    """Validation depth levels"""
    BASIC = "basic"  # File existence checks
    COMPILATION = "compilation"  # Build and syntax checks
    RUNTIME = "runtime"  # Application startup checks
    FUNCTIONAL = "functional"  # Feature and integration tests
    COMPREHENSIVE = "comprehensive"  # All validations including MCP tools


class RetryStrategy(Enum):
    """Retry strategies for failed validations"""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    WITH_SUGGESTIONS = "with_suggestions"
    ALTERNATIVE_AGENT = "alternative_agent"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class BuildResult:
    """Result of a build validation"""
    success: bool
    output: str
    errors: List[str]
    warnings: List[str]
    suggested_fixes: List[str]


@dataclass
class ValidationCheckpoint:
    """Enhanced checkpoint for validation state with multi-stage tracking"""
    agent_name: str
    timestamp: datetime
    completion_stage: CompletionStage
    pre_validation_passed: bool
    post_validation_passed: Optional[bool] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_suggestions: List[str] = None
    validation_errors: List[str] = None
    build_results: Optional[BuildResult] = None
    runtime_verified: bool = False
    functional_tests_passed: int = 0
    functional_tests_total: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "completion_stage": self.completion_stage.value,
            "pre_validation_passed": self.pre_validation_passed,
            "post_validation_passed": self.post_validation_passed,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "retry_suggestions": self.retry_suggestions or [],
            "validation_errors": self.validation_errors or [],
            "build_results": asdict(self.build_results) if self.build_results else None,
            "runtime_verified": self.runtime_verified,
            "functional_tests": f"{self.functional_tests_passed}/{self.functional_tests_total}"
        }
    
    def get_completion_percentage(self) -> int:
        """Get the completion percentage based on current stage"""
        return self.completion_stage.value


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
            
        # Create checkpoint with completion stage
        checkpoint = ValidationCheckpoint(
            agent_name=agent_name,
            timestamp=datetime.now(),
            completion_stage=CompletionStage.NOT_STARTED,
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
    
    def validate_compilation(self, agent_name: str, project_type: str = "auto") -> BuildResult:
        """
        Validate that code compiles without errors
        Returns BuildResult with success status and error details
        """
        errors = []
        warnings = []
        suggested_fixes = []
        output = ""
        
        # Auto-detect project type
        if project_type == "auto":
            if Path("package.json").exists() or Path("frontend/package.json").exists():
                project_type = "frontend"
            elif Path("requirements.txt").exists() or Path("backend/requirements.txt").exists():
                project_type = "backend"
            else:
                project_type = "unknown"
        
        if project_type in ["frontend", "fullstack"]:
            # Validate frontend build
            build_result = self._validate_frontend_compilation()
            errors.extend(build_result.errors)
            warnings.extend(build_result.warnings)
            suggested_fixes.extend(build_result.suggested_fixes)
            output += build_result.output
        
        if project_type in ["backend", "fullstack", "api"]:
            # Validate backend build
            build_result = self._validate_backend_compilation()
            errors.extend(build_result.errors)
            warnings.extend(build_result.warnings)
            suggested_fixes.extend(build_result.suggested_fixes)
            output += "\n" + build_result.output if output else build_result.output
        
        success = len(errors) == 0
        
        # Update checkpoint with build results
        if self.checkpoints:
            latest_checkpoint = self.checkpoints[-1]
            latest_checkpoint.build_results = BuildResult(
                success=success,
                output=output[:1000],  # Limit output size
                errors=errors[:10],  # Limit to first 10 errors
                warnings=warnings[:10],
                suggested_fixes=suggested_fixes[:10]
            )
            
            # Update completion stage based on build results
            if success:
                latest_checkpoint.completion_stage = CompletionStage.COMPILATION_SUCCESS
            elif latest_checkpoint.completion_stage == CompletionStage.NOT_STARTED:
                latest_checkpoint.completion_stage = CompletionStage.FILES_CREATED
        
        return BuildResult(success, output, errors, warnings, suggested_fixes)
    
    def _validate_frontend_compilation(self) -> BuildResult:
        """Validate frontend compilation (npm/yarn build)"""
        errors = []
        warnings = []
        suggested_fixes = []
        output = ""
        
        # Find package.json location
        package_json_path = None
        if Path("package.json").exists():
            package_json_path = Path(".")
        elif Path("frontend/package.json").exists():
            package_json_path = Path("frontend")
        else:
            return BuildResult(
                success=False,
                output="No package.json found",
                errors=["No frontend project detected"],
                warnings=[],
                suggested_fixes=["Create package.json with dependencies"]
            )
        
        try:
            # Install dependencies
            result = subprocess.run(
                ["npm", "install"],
                cwd=str(package_json_path),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                errors.append("Failed to install dependencies")
                output += f"npm install failed:\n{result.stderr}"
                suggested_fixes.append("Fix package.json dependencies")
                return BuildResult(False, output, errors, warnings, suggested_fixes)
            
            # Run build
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(package_json_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output += result.stdout + "\n" + result.stderr
            
            if result.returncode != 0:
                # Parse common frontend errors
                error_lines = result.stderr.split('\n') if result.stderr else []
                error_lines.extend(result.stdout.split('\n') if result.stdout else [])
                
                for line in error_lines:
                    if "Cannot find module" in line:
                        match = re.search(r"Cannot find module '([^']+)'", line)
                        if match:
                            module = match.group(1)
                            errors.append(f"Missing module: {module}")
                            if module.startswith('./'):
                                suggested_fixes.append(f"Create {module}.tsx or fix import path")
                            else:
                                suggested_fixes.append(f"npm install {module}")
                    elif "error TS" in line:
                        errors.append(line.strip())
                        suggested_fixes.append("Fix TypeScript errors")
                    elif "SyntaxError" in line:
                        errors.append(line.strip())
                        suggested_fixes.append("Fix JavaScript syntax errors")
                
                return BuildResult(False, output, errors, warnings, suggested_fixes)
            
            return BuildResult(True, output, [], warnings, [])
            
        except subprocess.TimeoutExpired:
            return BuildResult(
                False,
                "Build timeout",
                ["Build process timed out"],
                [],
                ["Check for infinite loops or hanging processes"]
            )
        except Exception as e:
            return BuildResult(
                False,
                str(e),
                [f"Build exception: {str(e)}"],
                [],
                ["Check Node.js installation"]
            )
    
    def _validate_backend_compilation(self) -> BuildResult:
        """Validate backend compilation (Python/Node)"""
        # Check for Python backend
        if Path("requirements.txt").exists() or Path("backend/requirements.txt").exists():
            return self._validate_python_compilation()
        # Check for Node backend
        elif Path("server/package.json").exists() or Path("backend/package.json").exists():
            return self._validate_node_backend_compilation()
        else:
            return BuildResult(
                True,  # No clear backend, pass by default
                "No backend detected",
                [],
                ["No backend configuration found"],
                []
            )
    
    def _validate_python_compilation(self) -> BuildResult:
        """Validate Python code compilation"""
        errors = []
        warnings = []
        suggested_fixes = []
        output = ""
        
        # Find Python files
        python_files = list(Path(".").glob("**/*.py"))
        if not python_files:
            return BuildResult(True, "No Python files found", [], [], [])
        
        # Check syntax for each file
        for py_file in python_files[:20]:  # Check first 20 files
            if "__pycache__" in str(py_file):
                continue
                
            result = subprocess.run(
                ["python", "-m", "py_compile", str(py_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                errors.append(f"Syntax error in {py_file}")
                output += result.stderr
                suggested_fixes.append(f"Fix syntax errors in {py_file}")
        
        return BuildResult(
            len(errors) == 0,
            output,
            errors,
            warnings,
            suggested_fixes
        )
    
    def _validate_node_backend_compilation(self) -> BuildResult:
        """Validate Node.js backend compilation"""
        # Similar to frontend validation but for backend
        return self._validate_frontend_compilation()
    
    def validate_runtime(self, agent_name: str, timeout: int = 10) -> Tuple[bool, str]:
        """
        Validate that application starts and runs without crashing
        Returns (success, message)
        """
        # Try to start the application
        start_commands = [
            ("npm", ["npm", "run", "dev"]),
            ("npm", ["npm", "start"]),
            ("python", ["python", "main.py"]),
            ("python", ["python", "app.py"]),
            ("python", ["python", "server.py"])
        ]
        
        for cmd_name, cmd_args in start_commands:
            if cmd_name == "npm" and not Path("package.json").exists():
                continue
            if cmd_name == "python" and not any(Path(f).exists() for f in ["main.py", "app.py", "server.py"]):
                continue
            
            try:
                # Start process
                process = subprocess.Popen(
                    cmd_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for startup
                time.sleep(5)
                
                # Check if process is still running
                if process.poll() is None:
                    # Process is running, test succeeded
                    process.terminate()
                    
                    # Update checkpoint
                    if self.checkpoints:
                        latest_checkpoint = self.checkpoints[-1]
                        latest_checkpoint.runtime_verified = True
                        if latest_checkpoint.completion_stage < CompletionStage.BASIC_FUNCTIONALITY:
                            latest_checkpoint.completion_stage = CompletionStage.BASIC_FUNCTIONALITY
                    
                    return True, f"Application started successfully with {cmd_name}"
                else:
                    # Process crashed
                    stderr = process.stderr.read() if process.stderr else ""
                    continue
                    
            except Exception as e:
                continue
        
        return False, "Failed to start application with any method"
    
    def validate_with_mcp_tools(self, agent_name: str, test_urls: List[str] = None) -> Dict[str, Any]:
        """
        Use MCP tools for comprehensive validation
        Returns dictionary with validation results from each MCP tool
        """
        results = {}
        
        # Check MCP availability
        mcp_ports = {
            "browser": 3103,
            "fetch": 3110,
            "semgrep": 3101
        }
        
        available_mcps = {}
        for mcp_name, port in mcp_ports.items():
            available_mcps[mcp_name] = self._check_mcp_port(port)
        
        # Browser validation
        if available_mcps.get("browser") and test_urls:
            results["browser"] = self._validate_with_browser_mcp(test_urls)
        
        # API validation with fetch
        if available_mcps.get("fetch"):
            results["api"] = self._validate_with_fetch_mcp()
        
        # Security validation with semgrep
        if available_mcps.get("semgrep"):
            results["security"] = self._validate_with_semgrep_mcp()
        
        # Update checkpoint with MCP results
        if self.checkpoints and any(r.get("success") for r in results.values()):
            latest_checkpoint = self.checkpoints[-1]
            tests_passed = sum(1 for r in results.values() if r.get("success"))
            tests_total = len(results)
            latest_checkpoint.functional_tests_passed = tests_passed
            latest_checkpoint.functional_tests_total = tests_total
            
            if tests_passed == tests_total:
                latest_checkpoint.completion_stage = CompletionStage.FULLY_VERIFIED
        
        return results
    
    def _check_mcp_port(self, port: int) -> bool:
        """Check if an MCP service port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _validate_with_browser_mcp(self, urls: List[str]) -> Dict:
        """Validate UI with browser MCP"""
        # This would integrate with actual MCP browser tool
        return {
            "success": False,
            "message": "Browser MCP validation not yet implemented",
            "urls_tested": urls
        }
    
    def _validate_with_fetch_mcp(self) -> Dict:
        """Validate API endpoints with fetch MCP"""
        # This would integrate with actual MCP fetch tool
        return {
            "success": False,
            "message": "Fetch MCP validation not yet implemented"
        }
    
    def _validate_with_semgrep_mcp(self) -> Dict:
        """Run security scan with semgrep MCP"""
        # This would integrate with actual MCP semgrep tool
        return {
            "success": False,
            "message": "Semgrep MCP validation not yet implemented"
        }
    
    def generate_validation_report(self, agent_name: str) -> str:
        """
        Generate comprehensive validation report for an agent
        Returns markdown-formatted report
        """
        report = f"# Validation Report for {agent_name}\n\n"
        report += f"Generated: {datetime.now().isoformat()}\n\n"
        
        # Find latest checkpoint for this agent
        agent_checkpoints = [cp for cp in self.checkpoints if cp.agent_name == agent_name]
        if not agent_checkpoints:
            return report + "No validation data available.\n"
        
        latest = agent_checkpoints[-1]
        
        # Completion status
        report += f"## Completion Status: {latest.get_completion_percentage()}%\n\n"
        report += f"- Stage: {latest.completion_stage.name}\n"
        report += f"- Pre-validation: {'✅ Passed' if latest.pre_validation_passed else '❌ Failed'}\n"
        if latest.post_validation_passed is not None:
            report += f"- Post-validation: {'✅ Passed' if latest.post_validation_passed else '❌ Failed'}\n"
        report += f"- Runtime verified: {'✅' if latest.runtime_verified else '❌'}\n"
        if latest.functional_tests_total > 0:
            report += f"- Functional tests: {latest.functional_tests_passed}/{latest.functional_tests_total}\n"
        report += "\n"
        
        # Build results
        if latest.build_results:
            report += "## Build Results\n\n"
            if latest.build_results.success:
                report += "✅ **Build Successful**\n\n"
            else:
                report += "❌ **Build Failed**\n\n"
                
                if latest.build_results.errors:
                    report += "### Errors:\n"
                    for error in latest.build_results.errors[:5]:
                        report += f"- {error}\n"
                    report += "\n"
                
                if latest.build_results.suggested_fixes:
                    report += "### Suggested Fixes:\n"
                    for fix in latest.build_results.suggested_fixes[:5]:
                        report += f"- {fix}\n"
                    report += "\n"
        
        # Validation errors
        if latest.validation_errors:
            report += "## Validation Issues\n\n"
            for error in latest.validation_errors[:10]:
                report += f"- {error}\n"
            report += "\n"
        
        # Retry suggestions
        if latest.retry_suggestions:
            report += "## Recommended Actions\n\n"
            for suggestion in latest.retry_suggestions[:5]:
                report += f"- {suggestion}\n"
            report += "\n"
        
        return report


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