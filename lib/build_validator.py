"""
Enhanced Build Validation with Detailed Feedback
Provides comprehensive error reporting and suggested fixes
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class BuildError:
    """Represents a build error with detailed information"""
    file: str
    line: int
    column: int
    error_type: str
    message: str
    raw_error: str
    suggested_fix: Optional[str] = None
    severity: str = "error"  # error, warning, info

class BuildValidator:
    """Enhanced build validator with detailed error reporting"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.error_patterns = self._compile_error_patterns()
        self.fix_suggestions = self._load_fix_suggestions()
        
    def _compile_error_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for different error types"""
        return {
            # TypeScript/JavaScript errors
            'ts_import': re.compile(r"Cannot find module '([^']+)'|Module not found: Error: Can't resolve '([^']+)'"),
            'ts_type': re.compile(r"Type '([^']+)' is not assignable to type '([^']+)'"),
            'ts_property': re.compile(r"Property '([^']+)' does not exist on type '([^']+)'"),
            'ts_syntax': re.compile(r"(SyntaxError|Parsing error): (.+)"),
            'ts_undefined': re.compile(r"'([^']+)' is not defined|Cannot read prop.* of undefined"),
            
            # Python errors
            'py_import': re.compile(r"ImportError: cannot import name '([^']+)'|ModuleNotFoundError: No module named '([^']+)'"),
            'py_syntax': re.compile(r"SyntaxError: (.+)"),
            'py_indentation': re.compile(r"IndentationError: (.+)"),
            'py_name': re.compile(r"NameError: name '([^']+)' is not defined"),
            'py_type': re.compile(r"TypeError: (.+)"),
            
            # Docker errors
            'docker_syntax': re.compile(r"failed to process.*: (.+)"),
            'docker_file': re.compile(r"failed to compute cache key: (.+) not found"),
            
            # Generic errors with file info
            'file_line': re.compile(r"(?:File |at |in )[\"\']?([^\"'\s]+\.(?:ts|tsx|js|jsx|py|yml))[\"\']?(?::| line |:)(\d+)(?::(\d+))?"),
        }
    
    def _load_fix_suggestions(self) -> Dict[str, str]:
        """Load common fix suggestions for error patterns"""
        return {
            'missing_module': """
1. Install the missing package: npm install {module} or pip install {module}
2. Check if the import path is correct
3. Ensure the file exists at the specified path
4. For local imports, use relative paths (./component) or configure path aliases""",
            
            'type_mismatch': """
1. Check the expected type definition
2. Add type assertions if needed: value as ExpectedType
3. Update the interface or type definition
4. Use union types if multiple types are valid: string | number""",
            
            'undefined_variable': """
1. Import or define the variable/function before use
2. Check for typos in the variable name
3. Ensure the variable is in scope
4. For React components, check if props are properly destructured""",
            
            'syntax_error': """
1. Check for missing brackets, parentheses, or quotes
2. Ensure proper indentation (Python)
3. Check for missing semicolons (optional in JS/TS)
4. Verify JSX tags are properly closed""",
            
            'docker_issue': """
1. Ensure all COPY source files exist
2. Check Dockerfile syntax
3. Verify build context includes required files
4. Use .dockerignore to exclude unnecessary files""",
        }
    
    async def validate_build(
        self, 
        project_path: str, 
        build_type: str = "auto"
    ) -> Tuple[bool, List[BuildError], Dict[str, any]]:
        """
        Validate build and return detailed error information
        
        Returns:
            - success: Whether build succeeded
            - errors: List of BuildError objects with details
            - metrics: Build metrics (duration, warnings, etc.)
        """
        project_path = Path(project_path)
        errors = []
        metrics = {
            'start_time': datetime.now().isoformat(),
            'build_type': build_type,
            'project_path': str(project_path),
        }
        
        # Auto-detect build type if needed
        if build_type == "auto":
            build_type = self._detect_build_type(project_path)
            metrics['detected_type'] = build_type
        
        # Run appropriate build command
        build_cmd = self._get_build_command(project_path, build_type)
        if not build_cmd:
            return False, [BuildError(
                file="project",
                line=0,
                column=0,
                error_type="config",
                message=f"Could not determine build command for type: {build_type}",
                raw_error="No build configuration found",
                suggested_fix="Add package.json for Node.js or requirements.txt for Python"
            )], metrics
        
        # Execute build
        start_time = datetime.now()
        success, output, stderr = await self._run_build_command(build_cmd, project_path)
        duration = (datetime.now() - start_time).total_seconds()
        
        metrics.update({
            'duration': duration,
            'command': build_cmd,
            'success': success,
        })
        
        # Parse errors if build failed
        if not success:
            errors = self._parse_build_errors(output + stderr, build_type)
            metrics['error_count'] = len(errors)
            metrics['unique_files'] = len(set(e.file for e in errors if e.file != "unknown"))
            
            # Log detailed error information
            if self.logger:
                self.logger.log_error(
                    "build_validator",
                    f"Build failed with {len(errors)} errors",
                    self._format_error_summary(errors)
                )
        
        return success, errors, metrics
    
    def _detect_build_type(self, project_path: Path) -> str:
        """Auto-detect project build type"""
        # Check for Node.js/TypeScript
        if (project_path / "package.json").exists():
            pkg_json = json.loads((project_path / "package.json").read_text())
            if "scripts" in pkg_json:
                if "build" in pkg_json["scripts"]:
                    return "npm"
                elif "compile" in pkg_json["scripts"]:
                    return "npm_compile"
            return "npm"
        
        # Check for Python
        if (project_path / "requirements.txt").exists() or \
           (project_path / "setup.py").exists() or \
           (project_path / "pyproject.toml").exists():
            return "python"
        
        # Check for Docker
        if (project_path / "Dockerfile").exists():
            return "docker"
        
        # Check for Makefile
        if (project_path / "Makefile").exists():
            return "make"
        
        return "unknown"
    
    def _get_build_command(self, project_path: Path, build_type: str) -> Optional[str]:
        """Get the appropriate build command"""
        commands = {
            'npm': 'npm run build',
            'npm_compile': 'npm run compile',
            'yarn': 'yarn build',
            'python': 'python -m py_compile **/*.py',
            'docker': 'docker build .',
            'make': 'make build',
        }
        
        # Check if custom build script exists
        if build_type == "npm" and (project_path / "package.json").exists():
            pkg_json = json.loads((project_path / "package.json").read_text())
            if "scripts" in pkg_json and "build" in pkg_json["scripts"]:
                return "npm run build"
            elif "scripts" in pkg_json and "compile" in pkg_json["scripts"]:
                return "npm run compile"
        
        return commands.get(build_type)
    
    async def _run_build_command(
        self, 
        cmd: str, 
        cwd: Path
    ) -> Tuple[bool, str, str]:
        """Run build command and capture output"""
        try:
            # Use shell=True on Windows, shell=False elsewhere
            use_shell = sys.platform == 'win32'
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                shell=use_shell
            )
            
            stdout, stderr = await process.communicate()
            
            # Decode output with error handling
            try:
                stdout = stdout.decode('utf-8', errors='replace')
                stderr = stderr.decode('utf-8', errors='replace')
            except:
                stdout = str(stdout)
                stderr = str(stderr)
            
            success = process.returncode == 0
            return success, stdout, stderr
            
        except Exception as e:
            return False, "", str(e)
    
    def _parse_build_errors(self, output: str, build_type: str) -> List[BuildError]:
        """Parse build output and extract detailed error information"""
        errors = []
        lines = output.split('\n')
        
        current_file = "unknown"
        current_line = 0
        current_column = 0
        
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue
            
            # Extract file location if present
            file_match = self.error_patterns['file_line'].search(line)
            if file_match:
                current_file = file_match.group(1)
                current_line = int(file_match.group(2)) if file_match.group(2) else 0
                current_column = int(file_match.group(3)) if file_match.group(3) else 0
            
            # Check for specific error patterns
            error = None
            
            # TypeScript/JavaScript errors
            if build_type in ['npm', 'yarn']:
                if match := self.error_patterns['ts_import'].search(line):
                    module = match.group(1) or match.group(2)
                    error = BuildError(
                        file=current_file,
                        line=current_line,
                        column=current_column,
                        error_type="import",
                        message=f"Cannot find module '{module}'",
                        raw_error=line,
                        suggested_fix=self.fix_suggestions['missing_module'].format(module=module)
                    )
                elif match := self.error_patterns['ts_type'].search(line):
                    error = BuildError(
                        file=current_file,
                        line=current_line,
                        column=current_column,
                        error_type="type",
                        message=f"Type '{match.group(1)}' not assignable to '{match.group(2)}'",
                        raw_error=line,
                        suggested_fix=self.fix_suggestions['type_mismatch']
                    )
                elif match := self.error_patterns['ts_undefined'].search(line):
                    error = BuildError(
                        file=current_file,
                        line=current_line,
                        column=current_column,
                        error_type="undefined",
                        message=line.strip(),
                        raw_error=line,
                        suggested_fix=self.fix_suggestions['undefined_variable']
                    )
            
            # Python errors
            elif build_type == 'python':
                if match := self.error_patterns['py_import'].search(line):
                    module = match.group(1) or match.group(2)
                    error = BuildError(
                        file=current_file,
                        line=current_line,
                        column=0,
                        error_type="import",
                        message=f"Cannot import '{module}'",
                        raw_error=line,
                        suggested_fix=self.fix_suggestions['missing_module'].format(module=module)
                    )
                elif match := self.error_patterns['py_syntax'].search(line):
                    error = BuildError(
                        file=current_file,
                        line=current_line,
                        column=0,
                        error_type="syntax",
                        message=match.group(1),
                        raw_error=line,
                        suggested_fix=self.fix_suggestions['syntax_error']
                    )
            
            # Generic error if no specific pattern matched but line contains error keywords
            if not error and any(keyword in line.lower() for keyword in ['error', 'failed', 'exception']):
                error = BuildError(
                    file=current_file,
                    line=current_line,
                    column=current_column,
                    error_type="generic",
                    message=line.strip()[:200],  # Truncate long messages
                    raw_error=line
                )
            
            if error:
                errors.append(error)
        
        return errors
    
    def _format_error_summary(self, errors: List[BuildError]) -> str:
        """Format errors into a readable summary"""
        if not errors:
            return "No errors found"
        
        summary = []
        summary.append(f"Found {len(errors)} build errors:")
        
        # Group errors by file
        by_file = {}
        for error in errors:
            if error.file not in by_file:
                by_file[error.file] = []
            by_file[error.file].append(error)
        
        for file, file_errors in by_file.items():
            summary.append(f"\n{file}:")
            for err in file_errors[:5]:  # Limit to 5 errors per file
                summary.append(f"  Line {err.line}: {err.message}")
                if err.suggested_fix:
                    summary.append(f"    Fix: {err.suggested_fix.split('\\n')[0]}")
        
        return '\n'.join(summary)
    
    def generate_error_report(self, errors: List[BuildError], output_path: Optional[str] = None) -> Dict:
        """Generate comprehensive error report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_errors': len(errors),
            'files_affected': len(set(e.file for e in errors if e.file != "unknown")),
            'error_types': {},
            'errors': [],
            'suggested_fixes': {},
        }
        
        # Count error types
        for error in errors:
            if error.error_type not in report['error_types']:
                report['error_types'][error.error_type] = 0
            report['error_types'][error.error_type] += 1
        
        # Add detailed error information
        for error in errors:
            report['errors'].append({
                'file': error.file,
                'line': error.line,
                'column': error.column,
                'type': error.error_type,
                'message': error.message,
                'severity': error.severity,
                'suggested_fix': error.suggested_fix,
            })
            
            # Collect unique suggested fixes
            if error.suggested_fix and error.error_type not in report['suggested_fixes']:
                report['suggested_fixes'][error.error_type] = error.suggested_fix
        
        # Save report if path provided
        if output_path:
            Path(output_path).write_text(json.dumps(report, indent=2))
        
        return report

import sys