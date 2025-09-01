#!/usr/bin/env python3
"""
Validation Gates - Phase 4.4 Implementation
Comprehensive validation gates before agent completion
"""

import os
import subprocess
import socket
import time
import json
import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ValidationGate(Enum):
    """Types of validation gates"""
    SYNTAX = "syntax_validation"
    IMPORTS = "import_resolution"
    REFERENCES = "reference_validation"
    FUNCTIONALITY = "minimal_functionality"

@dataclass
class GateResult:
    """Result of a validation gate check"""
    gate: ValidationGate
    passed: bool
    message: str
    details: Dict[str, Any]
    files_checked: List[str]
    errors: List[str]
    warnings: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ValidationGateReport:
    """Complete validation gate report"""
    agent_name: str
    all_gates_passed: bool
    gates_passed: List[ValidationGate]
    gates_failed: List[ValidationGate]
    gate_results: Dict[ValidationGate, GateResult]
    can_complete: bool
    retry_suggestions: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ValidationGates:
    """
    Validation gates system for Phase 4.4
    Ensures comprehensive validation before agent completion
    """
    
    def __init__(self, project_root: str = ".", strict_mode: bool = True):
        self.project_root = Path(project_root)
        self.strict_mode = strict_mode  # If True, all gates must pass
        self.validation_cache = {}
        self.gate_history = []
        
    def run_all_gates(self, agent_name: str, context: Optional[Dict] = None) -> ValidationGateReport:
        """
        Run all validation gates before agent completion
        Phase 4.4 requirement: Comprehensive validation before marking complete
        
        Gates:
        1. Syntax validation
        2. Import resolution
        3. Reference validation
        4. Minimal functionality test
        """
        gate_results = {}
        gates_passed = []
        gates_failed = []
        retry_suggestions = []
        
        # Get files to validate from context
        files_to_validate = self._get_files_to_validate(agent_name, context)
        
        # Gate 1: Syntax Validation
        syntax_result = self._validate_syntax_gate(files_to_validate)
        gate_results[ValidationGate.SYNTAX] = syntax_result
        if syntax_result.passed:
            gates_passed.append(ValidationGate.SYNTAX)
        else:
            gates_failed.append(ValidationGate.SYNTAX)
            retry_suggestions.append("Fix syntax errors in affected files")
        
        # Gate 2: Import Resolution (only if syntax passed)
        if syntax_result.passed:
            import_result = self._validate_imports_gate(files_to_validate)
            gate_results[ValidationGate.IMPORTS] = import_result
            if import_result.passed:
                gates_passed.append(ValidationGate.IMPORTS)
            else:
                gates_failed.append(ValidationGate.IMPORTS)
                retry_suggestions.append("Resolve missing imports or create missing modules")
        else:
            gate_results[ValidationGate.IMPORTS] = GateResult(
                gate=ValidationGate.IMPORTS,
                passed=False,
                message="Skipped due to syntax errors",
                details={},
                files_checked=[],
                errors=["Syntax must be valid before checking imports"],
                warnings=[]
            )
            gates_failed.append(ValidationGate.IMPORTS)
        
        # Gate 3: Reference Validation
        reference_result = self._validate_references_gate(files_to_validate)
        gate_results[ValidationGate.REFERENCES] = reference_result
        if reference_result.passed:
            gates_passed.append(ValidationGate.REFERENCES)
        else:
            gates_failed.append(ValidationGate.REFERENCES)
            retry_suggestions.append("Create missing referenced files")
        
        # Gate 4: Minimal Functionality Test
        functionality_result = self._validate_functionality_gate(agent_name, context)
        gate_results[ValidationGate.FUNCTIONALITY] = functionality_result
        if functionality_result.passed:
            gates_passed.append(ValidationGate.FUNCTIONALITY)
        else:
            gates_failed.append(ValidationGate.FUNCTIONALITY)
            retry_suggestions.extend(functionality_result.warnings)
        
        # Determine if agent can complete
        all_gates_passed = len(gates_failed) == 0
        can_complete = all_gates_passed if self.strict_mode else len(gates_passed) >= 3
        
        # Create report
        report = ValidationGateReport(
            agent_name=agent_name,
            all_gates_passed=all_gates_passed,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            gate_results=gate_results,
            can_complete=can_complete,
            retry_suggestions=retry_suggestions
        )
        
        # Add to history
        self.gate_history.append(report)
        
        return report
    
    def _validate_syntax_gate(self, files: List[str]) -> GateResult:
        """Gate 1: Syntax validation for all files"""
        errors = []
        warnings = []
        files_checked = []
        
        for file_path in files:
            file_path = Path(file_path)
            if not file_path.exists():
                warnings.append(f"File not found: {file_path}")
                continue
            
            files_checked.append(str(file_path))
            
            # Check syntax based on file type
            if file_path.suffix == '.py':
                error = self._check_python_syntax(file_path)
                if error:
                    errors.append(f"{file_path.name}: {error}")
            elif file_path.suffix in ['.js', '.jsx']:
                error = self._check_javascript_syntax(file_path)
                if error:
                    errors.append(f"{file_path.name}: {error}")
            elif file_path.suffix in ['.ts', '.tsx']:
                error = self._check_typescript_syntax(file_path)
                if error:
                    errors.append(f"{file_path.name}: {error}")
            elif file_path.suffix == '.json':
                error = self._check_json_syntax(file_path)
                if error:
                    errors.append(f"{file_path.name}: {error}")
        
        passed = len(errors) == 0
        
        return GateResult(
            gate=ValidationGate.SYNTAX,
            passed=passed,
            message="All files have valid syntax" if passed else f"Syntax errors in {len(errors)} files",
            details={"total_files": len(files_checked), "errors_found": len(errors)},
            files_checked=files_checked,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_imports_gate(self, files: List[str]) -> GateResult:
        """Gate 2: Import resolution for all files"""
        errors = []
        warnings = []
        files_checked = []
        unresolved_imports = {}
        
        for file_path in files:
            file_path = Path(file_path)
            if not file_path.exists() or file_path.suffix not in ['.py', '.js', '.jsx', '.ts', '.tsx']:
                continue
            
            files_checked.append(str(file_path))
            
            if file_path.suffix == '.py':
                unresolved = self._check_python_imports(file_path)
                if unresolved:
                    unresolved_imports[str(file_path)] = unresolved
                    errors.append(f"{file_path.name}: Missing imports: {', '.join(unresolved)}")
            elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                unresolved = self._check_javascript_imports(file_path)
                if unresolved:
                    unresolved_imports[str(file_path)] = unresolved
                    errors.append(f"{file_path.name}: Missing imports: {', '.join(unresolved)}")
        
        passed = len(errors) == 0
        
        return GateResult(
            gate=ValidationGate.IMPORTS,
            passed=passed,
            message="All imports resolved" if passed else f"Unresolved imports in {len(unresolved_imports)} files",
            details={"unresolved_imports": unresolved_imports},
            files_checked=files_checked,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_references_gate(self, files: List[str]) -> GateResult:
        """Gate 3: Reference validation for all files"""
        errors = []
        warnings = []
        files_checked = []
        missing_references = {}
        
        import re
        
        # Patterns for file references
        patterns = [
            r"open\(['\"](.+?)['\"]\)",
            r"Path\(['\"](.+?)['\"]\)",
            r"require\(['\"]\.\.?/(.+?)['\"]\)",  # Local requires only
            r"readFile[Sync]*\(['\"](.+?)['\"]\)",
        ]
        
        for file_path in files:
            file_path = Path(file_path)
            if not file_path.exists():
                continue
            
            files_checked.append(str(file_path))
            
            try:
                content = file_path.read_text(encoding='utf-8')
                missing = []
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        ref_path = file_path.parent / match if not match.startswith('/') else Path(match)
                        
                        # Check if referenced file exists
                        if not ref_path.exists():
                            # Try with common extensions
                            found = False
                            for ext in ['', '.py', '.js', '.jsx', '.ts', '.tsx', '.json']:
                                check_path = Path(str(ref_path) + ext)
                                if check_path.exists():
                                    found = True
                                    break
                            
                            if not found:
                                missing.append(match)
                
                if missing:
                    missing_references[str(file_path)] = missing
                    errors.append(f"{file_path.name}: Missing references: {', '.join(missing)}")
                    
            except Exception as e:
                warnings.append(f"Could not check references in {file_path}: {str(e)}")
        
        passed = len(errors) == 0
        
        return GateResult(
            gate=ValidationGate.REFERENCES,
            passed=passed,
            message="All references valid" if passed else f"Missing references in {len(missing_references)} files",
            details={"missing_references": missing_references},
            files_checked=files_checked,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_functionality_gate(self, agent_name: str, context: Optional[Dict]) -> GateResult:
        """Gate 4: Minimal functionality test"""
        errors = []
        warnings = []
        functionality_tests = []
        
        # Determine tests based on agent type
        if 'backend' in agent_name.lower() or 'api' in agent_name.lower():
            # Test backend functionality
            test_result = self._test_backend_functionality(context)
            functionality_tests.append(test_result)
            if not test_result['passed']:
                errors.append(test_result['error'])
                warnings.extend(test_result.get('suggestions', []))
        
        if 'frontend' in agent_name.lower() or 'ui' in agent_name.lower():
            # Test frontend functionality
            test_result = self._test_frontend_functionality(context)
            functionality_tests.append(test_result)
            if not test_result['passed']:
                errors.append(test_result['error'])
                warnings.extend(test_result.get('suggestions', []))
        
        if 'database' in agent_name.lower():
            # Test database functionality
            test_result = self._test_database_functionality(context)
            functionality_tests.append(test_result)
            if not test_result['passed']:
                errors.append(test_result['error'])
                warnings.extend(test_result.get('suggestions', []))
        
        if 'docker' in agent_name.lower() or 'devops' in agent_name.lower():
            # Test Docker functionality
            test_result = self._test_docker_functionality(context)
            functionality_tests.append(test_result)
            if not test_result['passed']:
                errors.append(test_result['error'])
                warnings.extend(test_result.get('suggestions', []))
        
        # If no specific tests, run generic file existence test
        if not functionality_tests:
            test_result = self._test_generic_functionality(context)
            functionality_tests.append(test_result)
            if not test_result['passed']:
                errors.append(test_result['error'])
        
        passed = len(errors) == 0
        
        return GateResult(
            gate=ValidationGate.FUNCTIONALITY,
            passed=passed,
            message="Minimal functionality verified" if passed else "Functionality tests failed",
            details={"tests_run": len(functionality_tests), "tests_passed": sum(1 for t in functionality_tests if t['passed'])},
            files_checked=[],
            errors=errors,
            warnings=warnings
        )
    
    def _check_python_syntax(self, file_path: Path) -> Optional[str]:
        """Check Python file syntax"""
        try:
            content = file_path.read_text(encoding='utf-8')
            compile(content, str(file_path), 'exec')
            return None
        except SyntaxError as e:
            return f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return str(e)
    
    def _check_javascript_syntax(self, file_path: Path) -> Optional[str]:
        """Check JavaScript file syntax (basic)"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Basic checks
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces != close_braces:
                return f"Mismatched braces: {open_braces} open, {close_braces} close"
            
            open_brackets = content.count('[')
            close_brackets = content.count(']')
            if open_brackets != close_brackets:
                return f"Mismatched brackets: {open_brackets} open, {close_brackets} close"
            
            open_parens = content.count('(')
            close_parens = content.count(')')
            if open_parens != close_parens:
                return f"Mismatched parentheses: {open_parens} open, {close_parens} close"
            
            return None
        except Exception as e:
            return str(e)
    
    def _check_typescript_syntax(self, file_path: Path) -> Optional[str]:
        """Check TypeScript file syntax"""
        try:
            # Try using TypeScript compiler if available
            result = subprocess.run(
                ['npx', 'tsc', '--noEmit', '--skipLibCheck', str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                # Extract first error
                lines = result.stdout.split('\n') if result.stdout else result.stderr.split('\n')
                for line in lines:
                    if 'error' in line.lower():
                        return line.strip()
                return "TypeScript compilation failed"
            
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fall back to basic JavaScript check
            return self._check_javascript_syntax(file_path)
    
    def _check_json_syntax(self, file_path: Path) -> Optional[str]:
        """Check JSON file syntax"""
        try:
            content = file_path.read_text(encoding='utf-8')
            json.loads(content)
            return None
        except json.JSONDecodeError as e:
            return f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return str(e)
    
    def _check_python_imports(self, file_path: Path) -> List[str]:
        """Check Python imports and return unresolved ones"""
        unresolved = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._can_import_python(alias.name, file_path):
                            unresolved.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if module and not self._can_import_python(module, file_path):
                        unresolved.append(module)
        except:
            pass
        
        return unresolved
    
    def _check_javascript_imports(self, file_path: Path) -> List[str]:
        """Check JavaScript/TypeScript imports and return unresolved ones"""
        unresolved = []
        
        import re
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Find imports
            import_patterns = [
                r"import\s+.*?\s+from\s+['\"](.+?)['\"]",
                r"require\(['\"](.+?)['\"]\)",
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if match.startswith('.'):
                        # Local import
                        imported_path = file_path.parent / match
                        
                        # Check with various extensions
                        found = False
                        for ext in ['', '.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.ts']:
                            check_path = Path(str(imported_path) + ext)
                            if check_path.exists():
                                found = True
                                break
                        
                        if not found:
                            unresolved.append(match)
        except:
            pass
        
        return unresolved
    
    def _can_import_python(self, module_name: str, from_file: Path) -> bool:
        """Check if a Python module can be imported"""
        # Check local modules
        local_paths = [
            from_file.parent / f"{module_name}.py",
            from_file.parent / module_name / "__init__.py",
            self.project_root / f"{module_name}.py",
            self.project_root / module_name / "__init__.py",
            self.project_root / "lib" / f"{module_name}.py",
        ]
        
        for path in local_paths:
            if path.exists():
                return True
        
        # Check if it's a standard library or installed module
        try:
            import importlib.util
            spec = importlib.util.find_spec(module_name.split('.')[0])
            return spec is not None
        except:
            return False
    
    def _test_backend_functionality(self, context: Optional[Dict]) -> Dict[str, Any]:
        """Test backend/API functionality"""
        # Check if main.py or app.py exists and can be imported
        main_files = [
            self.project_root / "main.py",
            self.project_root / "app.py",
            self.project_root / "backend" / "main.py",
            self.project_root / "backend" / "app.py",
        ]
        
        for main_file in main_files:
            if main_file.exists():
                # Try to import it
                try:
                    content = main_file.read_text(encoding='utf-8')
                    compile(content, str(main_file), 'exec')
                    
                    # Check for basic API structure
                    if 'FastAPI' in content or 'Flask' in content or 'Express' in content:
                        return {'passed': True, 'message': 'Backend structure verified'}
                except:
                    pass
        
        return {
            'passed': False,
            'error': 'No valid backend entry point found',
            'suggestions': ['Create main.py or app.py with API initialization']
        }
    
    def _test_frontend_functionality(self, context: Optional[Dict]) -> Dict[str, Any]:
        """Test frontend functionality"""
        # Check for package.json and entry files
        package_json = self.project_root / "frontend" / "package.json"
        if not package_json.exists():
            package_json = self.project_root / "package.json"
        
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                # Check for build script
                if 'scripts' in package_data and 'build' in package_data['scripts']:
                    return {'passed': True, 'message': 'Frontend build configuration found'}
            except:
                pass
        
        # Check for entry files
        entry_files = [
            self.project_root / "frontend" / "src" / "index.tsx",
            self.project_root / "frontend" / "src" / "index.jsx",
            self.project_root / "frontend" / "src" / "main.tsx",
            self.project_root / "src" / "index.tsx",
        ]
        
        for entry_file in entry_files:
            if entry_file.exists():
                return {'passed': True, 'message': 'Frontend entry point found'}
        
        return {
            'passed': False,
            'error': 'No frontend configuration found',
            'suggestions': ['Create package.json with build scripts', 'Create src/index.tsx entry point']
        }
    
    def _test_database_functionality(self, context: Optional[Dict]) -> Dict[str, Any]:
        """Test database functionality"""
        # Check for database models or schema
        model_files = list(self.project_root.rglob("*model*.py"))
        schema_files = list(self.project_root.rglob("*schema*.sql"))
        migration_files = list(self.project_root.rglob("*migration*.py"))
        
        if model_files or schema_files or migration_files:
            return {'passed': True, 'message': 'Database structure found'}
        
        return {
            'passed': False,
            'error': 'No database models or schema found',
            'suggestions': ['Create database models', 'Add schema definitions']
        }
    
    def _test_docker_functionality(self, context: Optional[Dict]) -> Dict[str, Any]:
        """Test Docker functionality"""
        dockerfile = self.project_root / "Dockerfile"
        docker_compose = self.project_root / "docker-compose.yml"
        
        if dockerfile.exists() or docker_compose.exists():
            return {'passed': True, 'message': 'Docker configuration found'}
        
        return {
            'passed': False,
            'error': 'No Docker configuration found',
            'suggestions': ['Create Dockerfile', 'Add docker-compose.yml']
        }
    
    def _test_generic_functionality(self, context: Optional[Dict]) -> Dict[str, Any]:
        """Generic functionality test"""
        # Check if any meaningful files were created
        py_files = list(self.project_root.rglob("*.py"))
        js_files = list(self.project_root.rglob("*.js")) + list(self.project_root.rglob("*.jsx"))
        ts_files = list(self.project_root.rglob("*.ts")) + list(self.project_root.rglob("*.tsx"))
        
        total_files = len(py_files) + len(js_files) + len(ts_files)
        
        if total_files > 0:
            return {'passed': True, 'message': f'Found {total_files} code files'}
        
        return {
            'passed': False,
            'error': 'No code files found',
            'suggestions': ['Create implementation files']
        }
    
    def _get_files_to_validate(self, agent_name: str, context: Optional[Dict]) -> List[str]:
        """Get list of files to validate for an agent"""
        files = []
        
        # From context if available
        if context:
            if hasattr(context, 'created_files') and context.created_files:
                if agent_name in context.created_files:
                    files.extend(context.created_files[agent_name])
                else:
                    # All files if agent not specific
                    for agent_files in context.created_files.values():
                        files.extend(agent_files)
            
            if hasattr(context, 'artifacts') and context.artifacts:
                if f"{agent_name}_created_files" in context.artifacts:
                    files.extend(context.artifacts[f"{agent_name}_created_files"])
        
        # If no files from context, scan project directory
        if not files:
            # Get recent files (created in last hour)
            import time
            current_time = time.time()
            
            for file_path in self.project_root.rglob('*'):
                if file_path.is_file():
                    # Check if file was recently modified
                    if current_time - file_path.stat().st_mtime < 3600:  # 1 hour
                        if file_path.suffix in ['.py', '.js', '.jsx', '.ts', '.tsx', '.json']:
                            files.append(str(file_path))
        
        return files
    
    def get_gate_summary(self) -> Dict[str, Any]:
        """Get summary of validation gate checks"""
        if not self.gate_history:
            return {"message": "No validation gates have been run"}
        
        total_checks = len(self.gate_history)
        passed_checks = sum(1 for report in self.gate_history if report.all_gates_passed)
        
        gate_stats = {
            ValidationGate.SYNTAX: 0,
            ValidationGate.IMPORTS: 0,
            ValidationGate.REFERENCES: 0,
            ValidationGate.FUNCTIONALITY: 0
        }
        
        for report in self.gate_history:
            for gate in report.gates_passed:
                gate_stats[gate] += 1
        
        return {
            "total_checks": total_checks,
            "fully_passed": passed_checks,
            "pass_rate": f"{(passed_checks / total_checks * 100):.1f}%" if total_checks > 0 else "0%",
            "gate_pass_rates": {
                gate.value: f"{(count / total_checks * 100):.1f}%" 
                for gate, count in gate_stats.items()
            }
        }