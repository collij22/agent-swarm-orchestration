#!/usr/bin/env python3
"""
Requirement Validator for Agent Swarm

Validates that an enhanced requirement document is properly formatted
and optimized for the 15-agent swarm system.
"""

import yaml
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple


class RequirementValidator:
    """Validates enhanced requirement documents"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.optimizations = []
        
    def validate_file(self, file_path: str) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate a requirement YAML file.
        
        Returns:
            Tuple of (is_valid, {errors, warnings, optimizations})
        """
        path = Path(file_path)
        if not path.exists():
            self.errors.append(f"File not found: {file_path}")
            return False, self._get_results()
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML format: {e}")
            return False, self._get_results()
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            return False, self._get_results()
            
        # Validate structure
        self._validate_structure(data)
        
        # Check for optimizations
        self._check_optimizations(data)
        
        is_valid = len(self.errors) == 0
        return is_valid, self._get_results()
    
    def _validate_structure(self, data: Dict[str, Any]):
        """Validate the requirement structure"""
        
        # Required top-level keys
        required_keys = ['project', 'core_requirements', 'features']
        for key in required_keys:
            if key not in data:
                self.errors.append(f"Missing required section: {key}")
        
        # Validate project section
        if 'project' in data:
            project = data['project']
            if 'type' not in project:
                self.errors.append("Project must have 'type' field")
            elif project['type'] not in ['web_app', 'mobile_app', 'api_service', 'ai_solution', 'data_pipeline']:
                self.warnings.append(f"Unusual project type: {project['type']}")
            
            if 'name' not in project:
                self.errors.append("Project must have 'name' field")
            
            if 'complexity' in project:
                if project['complexity'] not in ['simple', 'moderate', 'complex']:
                    self.warnings.append(f"Invalid complexity: {project['complexity']}")
        
        # Validate core requirements
        if 'core_requirements' in data:
            reqs = data['core_requirements']
            if not isinstance(reqs, list):
                self.errors.append("core_requirements must be a list")
            elif len(reqs) == 0:
                self.errors.append("Must have at least one core requirement")
            else:
                for i, req in enumerate(reqs):
                    if 'id' not in req:
                        self.errors.append(f"Requirement {i+1} missing 'id' field")
                    elif not req['id'].startswith('REQ-'):
                        self.warnings.append(f"Requirement ID should start with 'REQ-': {req['id']}")
                    
                    if 'description' not in req:
                        self.errors.append(f"Requirement {req.get('id', i+1)} missing 'description'")
                    
                    if 'acceptance_criteria' in req:
                        if not isinstance(req['acceptance_criteria'], list):
                            self.warnings.append(f"Acceptance criteria should be a list for {req.get('id', i+1)}")
        
        # Validate features
        if 'features' in data:
            features = data['features']
            if not isinstance(features, list):
                self.errors.append("features must be a list")
            elif len(features) == 0:
                self.warnings.append("No features specified")
    
    def _check_optimizations(self, data: Dict[str, Any]):
        """Check for optimization opportunities"""
        
        # Check for trigger keywords
        all_text = str(data).lower()
        
        # Payment optimization
        if any(word in all_text for word in ['payment', 'billing', 'subscription', 'stripe']):
            if 'integrations' not in data or not any(
                'stripe' in str(i).lower() for i in data.get('integrations', [])
            ):
                self.optimizations.append(
                    "Detected payment features - consider explicitly adding Stripe to integrations"
                )
        
        # AI/ML optimization
        if any(word in all_text for word in ['ai', 'ml', 'gpt', 'openai', 'anthropic', 'recommendation']):
            self.optimizations.append(
                "AI features detected - ai-specialist agent will be prioritized"
            )
        
        # Real-time optimization
        if any(word in all_text for word in ['real-time', 'realtime', 'websocket', 'live', 'instant']):
            self.optimizations.append(
                "Real-time features detected - WebSocket infrastructure will be included"
            )
        
        # Performance optimization
        if any(word in all_text for word in ['performance', 'scale', 'concurrent', 'load']):
            if 'success_metrics' not in data or 'performance' not in data.get('success_metrics', {}):
                self.optimizations.append(
                    "Performance requirements detected - consider adding specific performance metrics"
                )
        
        # Data processing optimization
        if any(word in all_text for word in ['csv', 'excel', 'data processing', 'etl', 'analytics']):
            self.optimizations.append(
                "Data processing detected - quick-data MCP will be activated"
            )
        
        # Check for missing helpful sections
        if 'technical_requirements' not in data:
            self.warnings.append("Consider adding 'technical_requirements' for infrastructure needs")
        
        if 'success_metrics' not in data:
            self.warnings.append("Consider adding 'success_metrics' for quality validation")
        
        if 'data_requirements' not in data and 'database' in all_text:
            self.warnings.append("Consider adding 'data_requirements' for data model clarity")
        
        if 'security_requirements' not in data:
            self.warnings.append("Consider adding 'security_requirements' for production readiness")
    
    def _get_results(self) -> Dict[str, List[str]]:
        """Get validation results"""
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'optimizations': self.optimizations
        }


def print_results(is_valid: bool, results: Dict[str, List[str]]):
    """Pretty print validation results"""
    print("\n" + "=" * 60)
    print("REQUIREMENT VALIDATION RESULTS")
    print("=" * 60)
    
    if is_valid:
        print("\n[VALID] Requirement is properly formatted!")
    else:
        print("\n[INVALID] Requirement has errors that must be fixed.")
    
    if results['errors']:
        print("\n[!] ERRORS (Must Fix):")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['warnings']:
        print("\n[?] WARNINGS (Should Consider):")
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    if results['optimizations']:
        print("\n[*] OPTIMIZATIONS (Will Be Applied):")
        for opt in results['optimizations']:
            print(f"  - {opt}")
    
    if not any(results.values()):
        print("\n[PERFECT] No issues found.")
    
    print("\n" + "=" * 60)


def main():
    """Main validation function"""
    if len(sys.argv) < 2:
        print("Usage: python validate_requirement.py <requirements.yaml>")
        print("\nExample: python validate_requirement.py requirements.yaml")
        sys.exit(1)
    
    file_path = sys.argv[1]
    validator = RequirementValidator()
    is_valid, results = validator.validate_file(file_path)
    
    print_results(is_valid, results)
    
    # Return appropriate exit code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()