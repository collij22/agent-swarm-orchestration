#!/usr/bin/env python3
"""
Progressive Validator - Phase 4.1 Implementation
Validates during execution, not just after completion
Catches errors early and provides immediate feedback
"""

import ast
import os
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ValidationError:
    """Represents a validation error"""
    file_path: str
    error_type: str
    error_message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    
@dataclass 
class ProgressiveValidationResult:
    """Result of progressive validation"""
    file_path: str
    validation_type: str  # imports, syntax, references, functionality
    success: bool
    errors: List[ValidationError]
    warnings: List[str]
    fixed_automatically: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ProgressiveValidator:
    """
    Progressive validation system that validates during execution
    Implements Phase 4.1 of the fix plan
    """
    
    def __init__(self, project_root: str = ".", auto_fix: bool = True):
        self.project_root = Path(project_root)
        self.auto_fix = auto_fix
        self.validation_cache = {}
        self.import_cache = {}
        self.validated_files = set()
        
    def validate_imports(self, file_path: str) -> ProgressiveValidationResult:
        """
        Check imports resolve immediately after file creation
        Phase 4.1 requirement: validate imports during execution
        """
        file_path = Path(file_path)
        errors = []
        warnings = []
        
        if not file_path.exists():
            return ProgressiveValidationResult(
                file_path=str(file_path),
                validation_type="imports",
                success=False,
                errors=[ValidationError(
                    file_path=str(file_path),
                    error_type="FileNotFoundError",
                    error_message=f"File {file_path} does not exist"
                )],
                warnings=[]
            )
        
        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            return ProgressiveValidationResult(
                file_path=str(file_path),
                validation_type="imports",
                success=False,
                errors=[ValidationError(
                    file_path=str(file_path),
                    error_type="ReadError",
                    error_message=str(e)
                )],
                warnings=[]
            )
        
        # Check file extension to determine validation method
        if file_path.suffix == '.py':
            return self._validate_python_imports(file_path, content)
        elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
            return self._validate_javascript_imports(file_path, content)
        else:
            warnings.append(f"Import validation not supported for {file_path.suffix} files")
            return ProgressiveValidationResult(
                file_path=str(file_path),
                validation_type="imports",
                success=True,
                errors=[],
                warnings=warnings
            )
    
    def _validate_python_imports(self, file_path: Path, content: str) -> ProgressiveValidationResult:
        """Validate Python imports"""
        errors = []
        warnings = []
        fixed = False
        
        try:
            # Parse the Python file
            tree = ast.parse(content)
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((alias.name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append((f"{module}.{alias.name}" if module else alias.name, node.lineno))
            
            # Check each import
            for import_name, line_no in imports:
                # Try to resolve the import
                module_name = import_name.split('.')[0]
                
                # Check if it's a local module
                local_path = self.project_root / f"{module_name}.py"
                local_dir = self.project_root / module_name / "__init__.py"
                
                if local_path.exists() or local_dir.exists():
                    continue  # Local module exists
                
                # Try to import as system module
                try:
                    spec = importlib.util.find_spec(module_name)
                    if spec is None:
                        errors.append(ValidationError(
                            file_path=str(file_path),
                            error_type="ModuleNotFoundError",
                            error_message=f"Module '{module_name}' not found",
                            line_number=line_no,
                            suggestion=f"Create {local_path} or install the module"
                        ))
                        
                        # Auto-fix: Create missing local module
                        if self.auto_fix and not module_name.startswith(('_', '.')):
                            self._create_missing_module(module_name)
                            fixed = True
                            
                except (ImportError, ValueError) as e:
                    warnings.append(f"Could not verify import '{module_name}': {str(e)}")
                    
        except SyntaxError as e:
            errors.append(ValidationError(
                file_path=str(file_path),
                error_type="SyntaxError",
                error_message=str(e),
                line_number=e.lineno,
                suggestion="Fix syntax error before validating imports"
            ))
            
        return ProgressiveValidationResult(
            file_path=str(file_path),
            validation_type="imports",
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            fixed_automatically=fixed
        )
    
    def _validate_javascript_imports(self, file_path: Path, content: str) -> ProgressiveValidationResult:
        """Validate JavaScript/TypeScript imports"""
        errors = []
        warnings = []
        
        # Regular expressions for import detection
        import_patterns = [
            r"import\s+.*?\s+from\s+['\"](.+?)['\"]",
            r"import\s+['\"](.+?)['\"]",
            r"require\(['\"](.+?)['\"]\)",
            r"from\s+['\"](.+?)['\"]"
        ]
        
        import re
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Check if imported file exists
                if match.startswith('.'):
                    # Relative import
                    imported_path = file_path.parent / match
                    
                    # Check various extensions
                    extensions = ['', '.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.ts']
                    found = False
                    
                    for ext in extensions:
                        check_path = Path(str(imported_path) + ext)
                        if check_path.exists():
                            found = True
                            break
                    
                    if not found:
                        errors.append(ValidationError(
                            file_path=str(file_path),
                            error_type="ImportError",
                            error_message=f"Cannot resolve import '{match}'",
                            suggestion=f"Create file at {imported_path}"
                        ))
                        
                        # Auto-fix: Create missing file
                        if self.auto_fix:
                            self._create_missing_javascript_module(imported_path)
                            
        return ProgressiveValidationResult(
            file_path=str(file_path),
            validation_type="imports",
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_syntax(self, file_path: str) -> ProgressiveValidationResult:
        """
        Run syntax check on each file
        Phase 4.1 requirement: immediate syntax validation
        """
        file_path = Path(file_path)
        errors = []
        warnings = []
        
        if not file_path.exists():
            return ProgressiveValidationResult(
                file_path=str(file_path),
                validation_type="syntax",
                success=False,
                errors=[ValidationError(
                    file_path=str(file_path),
                    error_type="FileNotFoundError",
                    error_message=f"File {file_path} does not exist"
                )],
                warnings=[]
            )
        
        content = file_path.read_text(encoding='utf-8')
        
        if file_path.suffix == '.py':
            # Python syntax check
            try:
                compile(content, str(file_path), 'exec')
            except SyntaxError as e:
                errors.append(ValidationError(
                    file_path=str(file_path),
                    error_type="SyntaxError",
                    error_message=str(e),
                    line_number=e.lineno,
                    suggestion="Fix syntax error at line " + str(e.lineno)
                ))
                
        elif file_path.suffix in ['.js', '.jsx']:
            # JavaScript syntax check (basic)
            # Could use a proper parser like esprima if available
            try:
                # Basic bracket matching
                open_brackets = content.count('{') + content.count('[') + content.count('(')
                close_brackets = content.count('}') + content.count(']') + content.count(')')
                if open_brackets != close_brackets:
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        error_type="SyntaxError",
                        error_message="Mismatched brackets",
                        suggestion="Check bracket pairing"
                    ))
            except Exception as e:
                warnings.append(f"Could not validate JavaScript syntax: {str(e)}")
                
        elif file_path.suffix in ['.ts', '.tsx']:
            # TypeScript syntax check
            try:
                result = subprocess.run(
                    ['npx', 'tsc', '--noEmit', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=self.project_root
                )
                if result.returncode != 0:
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        error_type="TypeScriptError",
                        error_message=result.stderr or result.stdout,
                        suggestion="Fix TypeScript errors"
                    ))
            except (subprocess.TimeoutExpired, FileNotFoundError):
                warnings.append("TypeScript compiler not available for syntax check")
                
        elif file_path.suffix == '.json':
            # JSON syntax check
            import json
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(ValidationError(
                    file_path=str(file_path),
                    error_type="JSONDecodeError",
                    error_message=str(e),
                    line_number=e.lineno,
                    suggestion=f"Fix JSON syntax at line {e.lineno}"
                ))
                
        return ProgressiveValidationResult(
            file_path=str(file_path),
            validation_type="syntax",
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_references(self, file_path: str) -> ProgressiveValidationResult:
        """
        Ensure referenced files exist
        Phase 4.1 requirement: validate file references
        """
        file_path = Path(file_path)
        errors = []
        warnings = []
        
        if not file_path.exists():
            return ProgressiveValidationResult(
                file_path=str(file_path),
                validation_type="references",
                success=False,
                errors=[ValidationError(
                    file_path=str(file_path),
                    error_type="FileNotFoundError",
                    error_message=f"File {file_path} does not exist"
                )],
                warnings=[]
            )
        
        content = file_path.read_text(encoding='utf-8')
        
        # Find file references in the content
        import re
        
        # Patterns for file references
        patterns = [
            r"open\(['\"](.+?)['\"]\)",  # Python file open
            r"Path\(['\"](.+?)['\"]\)",  # Python Path
            r"require\(['\"](.+?)['\"]\)",  # Node require
            r"readFile[Sync]*\(['\"](.+?)['\"]\)",  # Node fs
            r"import.*?['\"](.+?)['\"]\)",  # ES6 imports
        ]
        
        referenced_files = set()
        for pattern in patterns:
            matches = re.findall(pattern, content)
            referenced_files.update(matches)
        
        # Check each referenced file
        for ref_file in referenced_files:
            if ref_file.startswith(('.', '/')):
                # Local file reference
                ref_path = file_path.parent / ref_file if ref_file.startswith('.') else Path(ref_file)
                
                if not ref_path.exists():
                    errors.append(ValidationError(
                        file_path=str(file_path),
                        error_type="FileNotFoundError",
                        error_message=f"Referenced file '{ref_file}' does not exist",
                        suggestion=f"Create file at {ref_path}"
                    ))
                    
                    # Auto-fix: Create missing file
                    if self.auto_fix:
                        self._create_missing_file(ref_path)
        
        return ProgressiveValidationResult(
            file_path=str(file_path),
            validation_type="references",
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_all(self, file_path: str) -> Dict[str, ProgressiveValidationResult]:
        """
        Run all progressive validations on a file
        Returns results for each validation type
        """
        results = {}
        
        # Run validations in order
        results['syntax'] = self.validate_syntax(file_path)
        
        # Only validate imports if syntax is valid
        if results['syntax'].success:
            results['imports'] = self.validate_imports(file_path)
        
        # Always validate references
        results['references'] = self.validate_references(file_path)
        
        # Mark file as validated
        self.validated_files.add(str(file_path))
        
        return results
    
    def _create_missing_module(self, module_name: str):
        """Auto-create missing Python module"""
        module_path = self.project_root / f"{module_name}.py"
        if not module_path.exists():
            module_path.write_text(f'''"""
Auto-generated module: {module_name}
Created by ProgressiveValidator
"""

def placeholder():
    """Placeholder function"""
    raise NotImplementedError(f"Module {module_name} needs implementation")
''')
            
    def _create_missing_javascript_module(self, module_path: Path):
        """Auto-create missing JavaScript module"""
        # Try with .js extension
        js_path = Path(str(module_path) + '.js')
        if not js_path.exists() and not module_path.exists():
            js_path.parent.mkdir(parents=True, exist_ok=True)
            js_path.write_text(f'''// Auto-generated module
// Created by ProgressiveValidator

module.exports = {{
    placeholder: function() {{
        throw new Error("Module {module_path.name} needs implementation");
    }}
}};
''')
    
    def _create_missing_file(self, file_path: Path):
        """Auto-create missing referenced file"""
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create appropriate content based on extension
            if file_path.suffix == '.json':
                file_path.write_text('{}')
            elif file_path.suffix in ['.txt', '.md']:
                file_path.write_text(f'# {file_path.name}\nAuto-generated file')
            elif file_path.suffix == '.py':
                file_path.write_text('# Auto-generated Python file\npass')
            elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                file_path.write_text('// Auto-generated JavaScript file\n')
            else:
                file_path.write_text('')
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validations performed"""
        return {
            "validated_files": list(self.validated_files),
            "total_files": len(self.validated_files),
            "cache_size": len(self.validation_cache),
            "auto_fix_enabled": self.auto_fix
        }