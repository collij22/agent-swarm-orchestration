"""
Agent Verification Module - Ensures agents complete implementation properly
This module provides verification steps that agents must follow
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import ast
import json
import subprocess
import re

class AgentVerification:
    """Provides mandatory verification steps for all agents"""
    
    # Mandatory verification template to be added to all agent prompts
    MANDATORY_VERIFICATION_TEMPLATE = """
MANDATORY VERIFICATION STEPS:
You MUST complete these verification steps before marking any task as complete:

1. **Import Resolution**: After creating any file with imports, verify all imports resolve
   - For Python: Check that all `import` and `from ... import` statements reference existing modules
   - For JavaScript/TypeScript: Check that all `import` statements reference existing files
   - If an import doesn't resolve, CREATE the missing module/file immediately

2. **Entry Point Creation**: After creating configuration files, create the referenced entry points
   - If package.json references "src/main.tsx", CREATE src/main.tsx with working code
   - If main.py imports modules, CREATE those modules with at least placeholder implementations
   - If Dockerfile references app.py, CREATE app.py with a working application

3. **Working Implementation**: After scaffolding, implement at least one working example
   - Don't leave TODO comments without implementation
   - Include at least minimal functionality that can be tested
   - Ensure the code can actually run without immediate errors

4. **Syntax Verification**: Before marking complete, run a syntax check on created files
   - Python: The code should be valid Python syntax
   - JavaScript/TypeScript: The code should compile without syntax errors
   - JSON/YAML: The files should be valid and parseable

5. **Dependency Consistency**: Ensure all dependencies are properly declared
   - If you import a package, add it to requirements.txt or package.json
   - If you create a service, ensure its configuration is complete
   - If you reference environment variables, document them in .env.example

IMPORTANT: If any verification step fails, FIX THE ISSUE before proceeding!
"""
    
    @staticmethod
    def verify_python_imports(file_path: str) -> Tuple[bool, List[str]]:
        """
        Verify that all imports in a Python file can be resolved.
        
        Returns:
            Tuple of (success, list_of_missing_imports)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the Python file
            tree = ast.parse(content)
            missing_imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        if not AgentVerification._check_module_exists(module_name, file_path):
                            missing_imports.append(module_name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        if not AgentVerification._check_module_exists(module_name, file_path):
                            missing_imports.append(node.module)
            
            return len(missing_imports) == 0, missing_imports
            
        except SyntaxError as e:
            return False, [f"Syntax error: {str(e)}"]
        except Exception as e:
            return False, [f"Error parsing file: {str(e)}"]
    
    @staticmethod
    def _check_module_exists(module_name: str, from_file: str) -> bool:
        """Check if a Python module exists or can be imported"""
        # Standard library and common third-party modules
        standard_modules = {
            'os', 'sys', 'json', 'datetime', 'pathlib', 'typing', 'asyncio',
            'subprocess', 'time', 're', 'collections', 'itertools', 'functools',
            'fastapi', 'pydantic', 'sqlalchemy', 'requests', 'numpy', 'pandas',
            'pytest', 'unittest', 'logging', 'argparse', 'configparser', 'uuid',
            'hashlib', 'base64', 'random', 'math', 'decimal', 'io', 'threading'
        }
        
        if module_name in standard_modules:
            return True
        
        # Check if it's a local module (file exists in same directory or parent)
        file_dir = Path(from_file).parent
        
        # Check for .py file
        if (file_dir / f"{module_name}.py").exists():
            return True
        
        # Check for package directory
        if (file_dir / module_name / "__init__.py").exists():
            return True
        
        # Check parent directory
        if file_dir.parent != file_dir:
            if (file_dir.parent / f"{module_name}.py").exists():
                return True
            if (file_dir.parent / module_name / "__init__.py").exists():
                return True
        
        return False
    
    @staticmethod
    def verify_javascript_imports(file_path: str) -> Tuple[bool, List[str]]:
        """
        Verify that all imports in a JavaScript/TypeScript file can be resolved.
        
        Returns:
            Tuple of (success, list_of_missing_imports)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex patterns for imports
            import_patterns = [
                r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]',
                r'import\s+[\'"](.+?)[\'"]',
                r'require\([\'"](.+?)[\'"]\)'
            ]
            
            missing_imports = []
            file_dir = Path(file_path).parent
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if not AgentVerification._check_js_module_exists(match, file_dir):
                        missing_imports.append(match)
            
            return len(missing_imports) == 0, missing_imports
            
        except Exception as e:
            return False, [f"Error parsing file: {str(e)}"]
    
    @staticmethod
    def _check_js_module_exists(module_path: str, from_dir: Path) -> bool:
        """Check if a JavaScript module exists"""
        # Node modules and built-ins
        if module_path.startswith('@') or not module_path.startswith('.'):
            # Assume node_modules or built-in
            return True
        
        # Relative imports
        if module_path.startswith('.'):
            # Remove leading ./ or ../
            clean_path = module_path.lstrip('./')
            
            # Check various extensions
            extensions = ['.js', '.jsx', '.ts', '.tsx', '.json', '']
            for ext in extensions:
                potential_path = from_dir / f"{clean_path}{ext}"
                if potential_path.exists():
                    return True
                
                # Check for index file in directory
                potential_index = from_dir / clean_path / f"index{ext}"
                if potential_index.exists():
                    return True
        
        return False
    
    @staticmethod
    def verify_config_references(file_path: str) -> Tuple[bool, List[str]]:
        """
        Verify that files referenced in config files exist.
        
        Returns:
            Tuple of (success, list_of_missing_files)
        """
        missing_files = []
        file_dir = Path(file_path).parent
        
        try:
            if file_path.endswith('package.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Check main entry point
                if 'main' in data:
                    main_file = file_dir / data['main']
                    if not main_file.exists():
                        missing_files.append(data['main'])
                
                # Check scripts
                if 'scripts' in data:
                    for script_name, script_cmd in data['scripts'].items():
                        # Extract file references from scripts
                        if 'node ' in script_cmd or 'ts-node ' in script_cmd:
                            parts = script_cmd.split()
                            for part in parts:
                                if part.endswith(('.js', '.ts', '.jsx', '.tsx')):
                                    script_file = file_dir / part
                                    if not script_file.exists():
                                        missing_files.append(part)
            
            elif file_path.endswith('Dockerfile'):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check COPY commands
                copy_pattern = r'COPY\s+([^\s]+)\s+'
                copies = re.findall(copy_pattern, content)
                for copy_src in copies:
                    if not copy_src.startswith('--'):
                        src_path = file_dir / copy_src
                        if not src_path.exists() and '*' not in copy_src:
                            missing_files.append(copy_src)
                
                # Check CMD/ENTRYPOINT
                cmd_pattern = r'(?:CMD|ENTRYPOINT)\s+\["python",\s+"([^"]+)"\]'
                cmds = re.findall(cmd_pattern, content)
                for cmd_file in cmds:
                    cmd_path = file_dir / cmd_file
                    if not cmd_path.exists():
                        missing_files.append(cmd_file)
            
            return len(missing_files) == 0, missing_files
            
        except Exception as e:
            return False, [f"Error checking config: {str(e)}"]
    
    @staticmethod
    def verify_syntax(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Verify syntax of a file based on its extension.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if file_path.endswith('.py'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                compile(content, file_path, 'exec')
                return True, None
            
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                return True, None
            
            elif file_path.endswith(('.yaml', '.yml')):
                try:
                    import yaml
                    with open(file_path, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                    return True, None
                except ImportError:
                    # If PyYAML not installed, do basic check
                    return True, None
            
            # For other files, assume syntax is OK
            return True, None
            
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        except json.JSONDecodeError as e:
            return False, f"JSON parse error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def create_missing_module(module_name: str, file_dir: Path, 
                            language: str = "python") -> bool:
        """
        Create a missing module with minimal implementation.
        
        Args:
            module_name: Name of the module to create
            file_dir: Directory where to create the module
            language: Programming language ("python", "javascript", etc.)
        
        Returns:
            True if module was created successfully
        """
        try:
            if language == "python":
                module_file = file_dir / f"{module_name}.py"
                if not module_file.exists():
                    module_file.write_text(f'''"""
{module_name} module - Auto-generated placeholder
TODO: Implement actual functionality
"""

def placeholder_function():
    """Placeholder function to be implemented"""
    raise NotImplementedError("This module needs implementation")

class PlaceholderClass:
    """Placeholder class to be implemented"""
    
    def __init__(self):
        raise NotImplementedError("This class needs implementation")
''')
                    return True
            
            elif language in ["javascript", "typescript"]:
                ext = ".ts" if language == "typescript" else ".js"
                module_file = file_dir / f"{module_name}{ext}"
                if not module_file.exists():
                    module_file.write_text(f'''/**
 * {module_name} module - Auto-generated placeholder
 * TODO: Implement actual functionality
 */

export function placeholderFunction() {{
    throw new Error("This function needs implementation");
}}

export class PlaceholderClass {{
    constructor() {{
        throw new Error("This class needs implementation");
    }}
}}

export default {{
    placeholderFunction,
    PlaceholderClass
}};
''')
                    return True
            
            return False
            
        except Exception:
            return False
    
    @staticmethod
    def run_verification_suite(file_paths: List[str]) -> Dict[str, Dict]:
        """
        Run complete verification suite on multiple files.
        
        Args:
            file_paths: List of file paths to verify
        
        Returns:
            Dictionary with verification results for each file
        """
        results = {}
        
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                results[file_path] = {
                    "exists": False,
                    "errors": ["File does not exist"]
                }
                continue
            
            file_results = {
                "exists": True,
                "errors": [],
                "warnings": []
            }
            
            # Check syntax
            syntax_ok, syntax_error = AgentVerification.verify_syntax(file_path)
            if not syntax_ok:
                file_results["errors"].append(f"Syntax error: {syntax_error}")
            
            # Check imports based on file type
            if file_path.endswith('.py'):
                imports_ok, missing = AgentVerification.verify_python_imports(file_path)
                if not imports_ok:
                    file_results["errors"].append(f"Missing imports: {', '.join(missing)}")
            
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                imports_ok, missing = AgentVerification.verify_javascript_imports(file_path)
                if not imports_ok:
                    file_results["warnings"].append(f"Potentially missing imports: {', '.join(missing)}")
            
            # Check config references
            if file_path.endswith(('package.json', 'Dockerfile', 'docker-compose.yml')):
                refs_ok, missing = AgentVerification.verify_config_references(file_path)
                if not refs_ok:
                    file_results["errors"].append(f"Missing referenced files: {', '.join(missing)}")
            
            results[file_path] = file_results
        
        return results