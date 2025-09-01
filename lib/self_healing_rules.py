#!/usr/bin/env python3
"""
Self-Healing Rules - Phase 4.3 Implementation
Auto-fix common issues based on error patterns
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HealingRule:
    """Represents a self-healing rule"""
    error_pattern: str  # Regex pattern to match error
    error_type: str  # Type of error (ModuleNotFoundError, ImportError, etc.)
    fix_function: Callable  # Function to fix the error
    description: str  # Description of the fix
    success_rate: float = 0.0  # Success rate of this fix
    usage_count: int = 0  # Number of times this rule was used

@dataclass 
class HealingResult:
    """Result of applying a healing rule"""
    success: bool
    error_type: str
    original_error: str
    fix_applied: str
    files_modified: List[str]
    additional_info: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class SelfHealingRules:
    """
    Self-healing rules system for Phase 4.3
    Automatically fixes common issues
    """
    
    def __init__(self, project_root: str = ".", auto_apply: bool = True):
        self.project_root = Path(project_root)
        self.auto_apply = auto_apply
        self.healing_history = []
        self.rules = self._initialize_rules()
        
    def _initialize_rules(self) -> Dict[str, HealingRule]:
        """
        Initialize SELF_HEALING_RULES dictionary
        Phase 4.3 requirement: Define auto-fix rules for common issues
        """
        rules = {}
        
        # ModuleNotFoundError rule
        rules['ModuleNotFoundError'] = HealingRule(
            error_pattern=r"ModuleNotFoundError.*?No module named ['\"](.+?)['\"]",
            error_type="ModuleNotFoundError",
            fix_function=self._fix_module_not_found,
            description="Creates missing module or installs package"
        )
        
        # ImportError rule
        rules['ImportError'] = HealingRule(
            error_pattern=r"ImportError.*?cannot import name ['\"](.+?)['\"].*?from ['\"](.+?)['\"]",
            error_type="ImportError",
            fix_function=self._fix_import_error,
            description="Fixes import paths or creates missing symbols"
        )
        
        # FileNotFoundError rule
        rules['FileNotFoundError'] = HealingRule(
            error_pattern=r"FileNotFoundError.*?\[Errno 2\].*?['\"](.+?)['\"]",
            error_type="FileNotFoundError",
            fix_function=self._fix_file_not_found,
            description="Creates missing files or directories"
        )
        
        # UnicodeDecodeError rule
        rules['UnicodeDecodeError'] = HealingRule(
            error_pattern=r"UnicodeDecodeError.*?codec can't decode",
            error_type="UnicodeDecodeError",
            fix_function=self._fix_unicode_error,
            description="Fixes encoding issues in files"
        )
        
        # SyntaxError rule
        rules['SyntaxError'] = HealingRule(
            error_pattern=r"SyntaxError.*?invalid syntax.*?line (\d+)",
            error_type="SyntaxError",
            fix_function=self._fix_syntax_error,
            description="Attempts to fix common syntax errors"
        )
        
        # NameError rule
        rules['NameError'] = HealingRule(
            error_pattern=r"NameError.*?name ['\"](.+?)['\"] is not defined",
            error_type="NameError",
            fix_function=self._fix_name_error,
            description="Defines missing variables or imports"
        )
        
        # AttributeError rule
        rules['AttributeError'] = HealingRule(
            error_pattern=r"AttributeError.*?['\"](.+?)['\"].*?has no attribute ['\"](.+?)['\"]",
            error_type="AttributeError",
            fix_function=self._fix_attribute_error,
            description="Adds missing attributes or methods"
        )
        
        # TypeScript compilation error
        rules['TypeScriptError'] = HealingRule(
            error_pattern=r"error TS\d+:.*?Cannot find module ['\"](.+?)['\"]",
            error_type="TypeScriptError",
            fix_function=self._fix_typescript_module_error,
            description="Creates TypeScript type definitions or modules"
        )
        
        # Docker build error
        rules['DockerBuildError'] = HealingRule(
            error_pattern=r"ERROR.*?failed to solve.*?Dockerfile",
            error_type="DockerBuildError", 
            fix_function=self._fix_docker_build_error,
            description="Fixes common Dockerfile issues"
        )
        
        # Permission denied error
        rules['PermissionError'] = HealingRule(
            error_pattern=r"PermissionError.*?\[Errno 13\]",
            error_type="PermissionError",
            fix_function=self._fix_permission_error,
            description="Fixes file permissions"
        )
        
        return rules
    
    def apply_healing(self, error_message: str, context: Optional[Dict] = None) -> HealingResult:
        """
        Apply self-healing rules to fix an error
        
        Args:
            error_message: The error message to fix
            context: Optional context information
            
        Returns:
            HealingResult with fix details
        """
        # Try to match error against rules
        for error_type, rule in self.rules.items():
            match = re.search(rule.error_pattern, error_message)
            if match:
                # Found matching rule
                rule.usage_count += 1
                
                try:
                    # Apply fix
                    result = rule.fix_function(match, error_message, context)
                    
                    # Update success rate
                    if result.success:
                        rule.success_rate = (rule.success_rate * (rule.usage_count - 1) + 1) / rule.usage_count
                    else:
                        rule.success_rate = (rule.success_rate * (rule.usage_count - 1)) / rule.usage_count
                    
                    # Add to history
                    self.healing_history.append(result)
                    
                    return result
                    
                except Exception as e:
                    # Fix failed
                    return HealingResult(
                        success=False,
                        error_type=error_type,
                        original_error=error_message,
                        fix_applied=f"Failed to apply fix: {str(e)}",
                        files_modified=[],
                        additional_info={"exception": str(e)}
                    )
        
        # No matching rule found
        return HealingResult(
            success=False,
            error_type="Unknown",
            original_error=error_message,
            fix_applied="No matching healing rule found",
            files_modified=[],
            additional_info={}
        )
    
    def _fix_module_not_found(self, match: re.Match, error_msg: str, context: Optional[Dict]) -> HealingResult:
        """Fix ModuleNotFoundError by creating module or installing package"""
        module_name = match.group(1)
        files_modified = []
        
        # First, check if it's a local module
        local_module_path = self.project_root / f"{module_name}.py"
        local_package_path = self.project_root / module_name / "__init__.py"
        
        if '.' in module_name:
            # Handle nested modules
            parts = module_name.split('.')
            base_module = parts[0]
            local_module_path = self.project_root / f"{'/'.join(parts)}.py"
            local_package_path = self.project_root / '/'.join(parts) / "__init__.py"
        
        # Try creating local module
        if not local_module_path.exists() and not local_package_path.exists():
            # Create as package
            local_package_path.parent.mkdir(parents=True, exist_ok=True)
            local_package_path.write_text(f'''"""
Auto-generated module: {module_name}
Created by SelfHealingRules to fix ModuleNotFoundError
"""

def placeholder():
    """Placeholder function - needs implementation"""
    raise NotImplementedError(f"Module {module_name} needs implementation")

__all__ = ['placeholder']
''')
            files_modified.append(str(local_package_path))
            
            return HealingResult(
                success=True,
                error_type="ModuleNotFoundError",
                original_error=error_msg,
                fix_applied=f"Created local module {module_name}",
                files_modified=files_modified,
                additional_info={"module_created": str(local_package_path)}
            )
        
        # If not a local module, try installing via pip
        if self.auto_apply:
            try:
                result = subprocess.run(
                    ['pip', 'install', module_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return HealingResult(
                        success=True,
                        error_type="ModuleNotFoundError",
                        original_error=error_msg,
                        fix_applied=f"Installed package {module_name} via pip",
                        files_modified=[],
                        additional_info={"pip_output": result.stdout}
                    )
            except subprocess.TimeoutExpired:
                pass
        
        return HealingResult(
            success=False,
            error_type="ModuleNotFoundError",
            original_error=error_msg,
            fix_applied=f"Could not fix missing module {module_name}",
            files_modified=files_modified,
            additional_info={}
        )
    
    def _fix_import_error(self, match: re.Match, error_msg: str, context: Optional[Dict]) -> HealingResult:
        """Fix ImportError by fixing import paths or creating missing symbols"""
        symbol_name = match.group(1)
        module_name = match.group(2)
        files_modified = []
        
        # Find the module file
        module_file = self._find_module_file(module_name)
        
        if module_file and module_file.exists():
            # Add the missing symbol to the module
            content = module_file.read_text(encoding='utf-8')
            
            # Check if symbol already exists
            if symbol_name not in content:
                # Add the symbol
                addition = f'''

# Auto-added by SelfHealingRules
def {symbol_name}(*args, **kwargs):
    """Auto-generated function - needs implementation"""
    raise NotImplementedError(f"Function {symbol_name} needs implementation")
'''
                
                module_file.write_text(content + addition, encoding='utf-8')
                files_modified.append(str(module_file))
                
                return HealingResult(
                    success=True,
                    error_type="ImportError",
                    original_error=error_msg,
                    fix_applied=f"Added missing symbol {symbol_name} to {module_name}",
                    files_modified=files_modified,
                    additional_info={"symbol_added": symbol_name}
                )
        
        return HealingResult(
            success=False,
            error_type="ImportError",
            original_error=error_msg,
            fix_applied=f"Could not fix import of {symbol_name} from {module_name}",
            files_modified=files_modified,
            additional_info={}
        )
    
    def _fix_file_not_found(self, match: re.Match, error_msg: str, context: Optional[Dict]) -> HealingResult:
        """Fix FileNotFoundError by creating missing files or directories"""
        file_path = match.group(1)
        files_modified = []
        
        # Create the missing file/directory
        target_path = Path(file_path)
        if not target_path.is_absolute():
            target_path = self.project_root / target_path
        
        # Determine if it's a file or directory
        if '.' in target_path.name:
            # Likely a file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create with appropriate content based on extension
            content = self._get_default_content(target_path)
            target_path.write_text(content, encoding='utf-8')
            files_modified.append(str(target_path))
            
            return HealingResult(
                success=True,
                error_type="FileNotFoundError",
                original_error=error_msg,
                fix_applied=f"Created missing file {target_path}",
                files_modified=files_modified,
                additional_info={"file_created": str(target_path)}
            )
        else:
            # Likely a directory
            target_path.mkdir(parents=True, exist_ok=True)
            
            return HealingResult(
                success=True,
                error_type="FileNotFoundError",
                original_error=error_msg,
                fix_applied=f"Created missing directory {target_path}",
                files_modified=[],
                additional_info={"directory_created": str(target_path)}
            )
    
    def _fix_unicode_error(self, match: re.Match, error_msg: str, context: Optional[Dict]) -> HealingResult:
        """Fix UnicodeDecodeError by fixing file encoding"""
        files_modified = []
        
        # Extract file path from error message if possible
        file_match = re.search(r"['\"]([^'\"]+\.(?:py|txt|json|md|yml|yaml))['\"]", error_msg)
        
        if file_match:
            file_path = Path(file_match.group(1))
            if not file_path.is_absolute():
                file_path = self.project_root / file_path
            
            if file_path.exists():
                try:
                    # Try reading with different encodings
                    content = None
                    for encoding in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
                        try:
                            content = file_path.read_text(encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if content:
                        # Re-save with UTF-8 encoding
                        file_path.write_text(content, encoding='utf-8')
                        files_modified.append(str(file_path))
                        
                        return HealingResult(
                            success=True,
                            error_type="UnicodeDecodeError",
                            original_error=error_msg,
                            fix_applied=f"Fixed encoding for {file_path}",
                            files_modified=files_modified,
                            additional_info={"encoding_fixed": "utf-8"}
                        )
                except Exception as e:
                    pass
        
        return HealingResult(
            success=False,
            error_type="UnicodeDecodeError",
            original_error=error_msg,
            fix_applied="Could not fix encoding error",
            files_modified=files_modified,
            additional_info={}
        )
    
    def _fix_syntax_error(self, match: re.Match, error_msg: str, context: Optional[Dict]) -> HealingResult:
        """Attempt to fix common syntax errors"""
        line_number = int(match.group(1)) if match.lastindex >= 1 else 0
        files_modified = []
        
        # Extract file path from error message
        file_match = re.search(r'File ["\']([^"\']+)["\']', error_msg)
        
        if file_match and line_number > 0:
            file_path = Path(file_match.group(1))
            
            if file_path.exists():
                lines = file_path.read_text(encoding='utf-8').splitlines()
                
                if 0 < line_number <= len(lines):
                    problem_line = lines[line_number - 1]
                    fixed_line = problem_line
                    
                    # Common syntax fixes
                    # Missing colon
                    if re.match(r'^\s*(if|elif|else|for|while|def|class|try|except|finally|with)\s+.*[^:]$', problem_line):
                        fixed_line = problem_line + ':'
                    # Missing closing bracket
                    elif problem_line.count('(') > problem_line.count(')'):
                        fixed_line = problem_line + ')'
                    elif problem_line.count('[') > problem_line.count(']'):
                        fixed_line = problem_line + ']'
                    elif problem_line.count('{') > problem_line.count('}'):
                        fixed_line = problem_line + '}'
                    
                    if fixed_line != problem_line:
                        lines[line_number - 1] = fixed_line
                        file_path.write_text('\n'.join(lines), encoding='utf-8')
                        files_modified.append(str(file_path))
                        
                        return HealingResult(
                            success=True,
                            error_type="SyntaxError",
                            original_error=error_msg,
                            fix_applied=f"Fixed syntax at line {line_number}",
                            files_modified=files_modified,
                            additional_info={"line_fixed": line_number}
                        )
        
        return HealingResult(
            success=False,
            error_type="SyntaxError",
            original_error=error_msg,
            fix_applied="Could not fix syntax error",
            files_modified=files_modified,
            additional_info={}
        )
    
    def _fix_name_error(self, match: re.Match, error_msg: str, context: Optional[Dict]) -> HealingResult:
        """Fix NameError by defining missing variables or imports"""
        name = match.group(1)
        files_modified = []
        
        # Extract file path from error message
        file_match = re.search(r'File ["\']([^"\']+)["\']', error_msg)
        
        if file_match:
            file_path = Path(file_match.group(1))
            
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                
                # Add common imports if missing
                additions = []
                
                if name in ['os', 'sys', 'json', 're', 'time', 'datetime', 'pathlib']:
                    if f'import {name}' not in content:
                        additions.append(f'import {name}')
                elif name == 'Path':
                    if 'from pathlib import Path' not in content:
                        additions.append('from pathlib import Path')
                elif name in ['List', 'Dict', 'Optional', 'Any']:
                    if f'from typing import' not in content or name not in content:
                        additions.append(f'from typing import {name}')
                else:
                    # Define as variable
                    additions.append(f'{name} = None  # Auto-defined by SelfHealingRules')
                
                if additions:
                    # Add imports at the beginning
                    new_content = '\n'.join(additions) + '\n\n' + content
                    file_path.write_text(new_content, encoding='utf-8')
                    files_modified.append(str(file_path))
                    
                    return HealingResult(
                        success=True,
                        error_type="NameError",
                        original_error=error_msg,
                        fix_applied=f"Defined missing name {name}",
                        files_modified=files_modified,
                        additional_info={"name_defined": name}
                    )
        
        return HealingResult(
            success=False,
            error_type="NameError",
            original_error=error_msg,
            fix_applied=f"Could not define {name}",
            files_modified=files_modified,
            additional_info={}
        )
    
    def _fix_attribute_error(self, match: re.Match, error_msg: str, context: Optional[Dict]) -> HealingResult:
        """Fix AttributeError by adding missing attributes or methods"""
        object_name = match.group(1)
        attribute_name = match.group(2)
        
        # This is complex and context-dependent
        # For now, return unsuccessful
        return HealingResult(
            success=False,
            error_type="AttributeError",
            original_error=error_msg,
            fix_applied=f"Cannot auto-fix missing attribute {attribute_name}",
            files_modified=[],
            additional_info={}
        )
    
    def _fix_typescript_module_error(self, match: re.Match, error_msg: str, context: Optional[Dict]) -> HealingResult:
        """Fix TypeScript module errors"""
        module_name = match.group(1)
        files_modified = []
        
        # Create TypeScript declaration file
        if module_name.startswith('./') or module_name.startswith('../'):
            # Local module
            module_path = Path(module_name + '.ts')
            if not module_path.exists():
                module_path.write_text(f'''// Auto-generated TypeScript module
export function placeholder(): void {{
    throw new Error("Module {module_name} needs implementation");
}}
''', encoding='utf-8')
                files_modified.append(str(module_path))
                
                return HealingResult(
                    success=True,
                    error_type="TypeScriptError",
                    original_error=error_msg,
                    fix_applied=f"Created TypeScript module {module_name}",
                    files_modified=files_modified,
                    additional_info={"module_created": str(module_path)}
                )
        
        return HealingResult(
            success=False,
            error_type="TypeScriptError",
            original_error=error_msg,
            fix_applied=f"Could not fix TypeScript module {module_name}",
            files_modified=files_modified,
            additional_info={}
        )
    
    def _fix_docker_build_error(self, match: re.Match, error_msg: str, context: Optional[Dict]) -> HealingResult:
        """Fix common Dockerfile issues"""
        # This would need specific Docker error parsing
        return HealingResult(
            success=False,
            error_type="DockerBuildError",
            original_error=error_msg,
            fix_applied="Docker build errors require manual intervention",
            files_modified=[],
            additional_info={}
        )
    
    def _fix_permission_error(self, match: re.Match, error_msg: str, context: Optional[Dict]) -> HealingResult:
        """Fix file permission errors"""
        # Extract file path
        file_match = re.search(r"['\"]([^'\"]+)['\"]", error_msg)
        
        if file_match:
            file_path = Path(file_match.group(1))
            
            if file_path.exists():
                try:
                    # Make file writable
                    os.chmod(file_path, 0o666)
                    
                    return HealingResult(
                        success=True,
                        error_type="PermissionError",
                        original_error=error_msg,
                        fix_applied=f"Fixed permissions for {file_path}",
                        files_modified=[str(file_path)],
                        additional_info={"permissions_set": "0o666"}
                    )
                except Exception as e:
                    pass
        
        return HealingResult(
            success=False,
            error_type="PermissionError",
            original_error=error_msg,
            fix_applied="Could not fix permission error",
            files_modified=[],
            additional_info={}
        )
    
    def _find_module_file(self, module_name: str) -> Optional[Path]:
        """Find the file for a module"""
        # Check various locations
        candidates = [
            self.project_root / f"{module_name}.py",
            self.project_root / module_name / "__init__.py",
            self.project_root / "lib" / f"{module_name}.py",
            self.project_root / "src" / f"{module_name}.py",
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        return None
    
    def _get_default_content(self, file_path: Path) -> str:
        """Get default content based on file extension"""
        ext = file_path.suffix.lower()
        
        if ext == '.py':
            return f'# Auto-generated file: {file_path.name}\n# Created by SelfHealingRules\n\npass\n'
        elif ext == '.json':
            return '{}'
        elif ext in ['.yml', '.yaml']:
            return f'# Auto-generated file: {file_path.name}\n'
        elif ext in ['.txt', '.md']:
            return f'# {file_path.name}\nAuto-generated file'
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            return f'// Auto-generated file: {file_path.name}\n'
        elif ext == '.html':
            return f'<!DOCTYPE html>\n<html>\n<head><title>{file_path.name}</title></head>\n<body></body>\n</html>'
        elif ext == '.css':
            return f'/* Auto-generated file: {file_path.name} */\n'
        else:
            return ''
    
    def get_healing_stats(self) -> Dict[str, Any]:
        """Get statistics about healing operations"""
        stats = {
            "total_heals": len(self.healing_history),
            "successful_heals": sum(1 for h in self.healing_history if h.success),
            "rules_by_usage": {},
            "rules_by_success": {}
        }
        
        for rule_name, rule in self.rules.items():
            if rule.usage_count > 0:
                stats["rules_by_usage"][rule_name] = rule.usage_count
                stats["rules_by_success"][rule_name] = f"{rule.success_rate * 100:.1f}%"
        
        return stats