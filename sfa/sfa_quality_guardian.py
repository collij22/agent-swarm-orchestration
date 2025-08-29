#!/usr/bin/env python3

# /// script
# dependencies = [
#   "anthropic>=0.45.2",
#   "rich>=13.7.0",
#   "pyyaml>=6.0",
# ]
# ///

"""
Single File Agent: Quality Guardian

Standalone execution of the quality-guardian agent for testing, security, and code quality.

Example Usage:
    uv run sfa/sfa_quality_guardian.py --prompt "Test the authentication system" --codebase ./src
    uv run sfa/sfa_quality_guardian.py --audit security --path ./api --output report.md
    uv run sfa/sfa_quality_guardian.py --prompt "Set up CI/CD testing" --framework jest --verbose
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: Anthropic not installed. Running in simulation mode.")

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

# Initialize console
console = Console()

# Agent prompt template
AGENT_PROMPT = """<role>
You are an expert quality assurance specialist focusing on testing, security, and code quality.
You excel at creating comprehensive test suites, identifying security vulnerabilities, and ensuring code meets the highest standards.
</role>

<context>
Project Requirements: {{requirements}}
Code Path: {{code_path}}
Quality Focus: {{focus}}
</context>

<instructions>
1. Analyze the codebase for quality issues
2. Create comprehensive test coverage
3. Identify and fix security vulnerabilities
4. Ensure code follows best practices
5. Set up continuous quality checks
6. Generate detailed quality reports
</instructions>

<tools>
    <tool>
        <name>create_tests</name>
        <description>Generate comprehensive test suites</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Why these tests are needed</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>test_type</name>
                <type>string</type>
                <description>Type of tests (unit, integration, e2e)</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>test_files</name>
                <type>object</type>
                <description>Test files to create (path: content)</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>coverage_target</name>
                <type>number</type>
                <description>Target test coverage percentage</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>security_audit</name>
        <description>Perform security audit and vulnerability scanning</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Security concerns and focus areas</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>vulnerabilities</name>
                <type>array</type>
                <description>List of identified vulnerabilities</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>fixes</name>
                <type>object</type>
                <description>Recommended fixes for vulnerabilities</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>severity_levels</name>
                <type>object</type>
                <description>Severity classification of issues</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>code_review</name>
        <description>Review code quality and standards compliance</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Review focus and criteria</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>issues</name>
                <type>array</type>
                <description>Code quality issues found</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>improvements</name>
                <type>object</type>
                <description>Suggested improvements</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>metrics</name>
                <type>object</type>
                <description>Code quality metrics</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>setup_ci</name>
        <description>Configure CI/CD testing pipelines</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>CI/CD strategy reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>platform</name>
                <type>string</type>
                <description>CI platform (github-actions, gitlab-ci, etc)</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>config_files</name>
                <type>object</type>
                <description>CI configuration files</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>test_stages</name>
                <type>array</type>
                <description>Testing stages in pipeline</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>performance_test</name>
        <description>Create and run performance tests</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Performance testing approach</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>test_scenarios</name>
                <type>array</type>
                <description>Performance test scenarios</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>benchmarks</name>
                <type>object</type>
                <description>Performance benchmarks to meet</description>
                <required>true</required>
            </parameter>
        </parameters>
    </tool>
    
    <tool>
        <name>generate_report</name>
        <description>Generate comprehensive quality report</description>
        <parameters>
            <parameter>
                <name>reasoning</name>
                <type>string</type>
                <description>Report generation reasoning</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>report_content</name>
                <type>string</type>
                <description>Full quality report in markdown</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>filename</name>
                <type>string</type>
                <description>Output filename for report</description>
                <required>true</required>
            </parameter>
            <parameter>
                <name>summary</name>
                <type>object</type>
                <description>Executive summary of findings</description>
                <required>false</required>
            </parameter>
        </parameters>
    </tool>
</tools>

<task>
{{task}}
</task>

Remember to:
- Ensure comprehensive test coverage (90%+ for critical code)
- Follow security best practices (OWASP Top 10)
- Check for code smells and anti-patterns
- Verify performance benchmarks
- Create actionable recommendations
- Generate detailed quality reports
"""

class QualityGuardianAgent:
    """Single File Agent for Testing, Security, and Code Quality"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if HAS_ANTHROPIC and self.api_key else None
        self.test_files = {}
        self.quality_metrics = {}
        self.vulnerabilities = []
        
    def create_tests(self, reasoning: str, test_type: str, test_files: Dict, coverage_target: float = 90) -> str:
        """Generate test suites"""
        console.print(Panel(
            f"[blue]Creating Tests[/blue]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Type:[/dim] {test_type}\n"
            f"[dim]Coverage Target:[/dim] {coverage_target}%",
            border_style="blue"
        ))
        
        self.test_files.update(test_files)
        self.quality_metrics['test_coverage'] = coverage_target
        
        # Display test summary
        table = Table(title="Generated Tests")
        table.add_column("File", style="cyan")
        table.add_column("Type", style="green")
        
        for file_path in test_files.keys():
            table.add_row(file_path, test_type)
        
        console.print(table)
        
        return f"Created {len(test_files)} {test_type} test files"
    
    def security_audit(self, reasoning: str, vulnerabilities: List, fixes: Dict, severity_levels: Dict = None) -> str:
        """Perform security audit"""
        console.print(Panel(
            f"[red]Security Audit[/red]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Issues Found:[/dim] {len(vulnerabilities)}",
            border_style="red"
        ))
        
        self.vulnerabilities = vulnerabilities
        
        # Display security issues
        if vulnerabilities:
            table = Table(title="Security Vulnerabilities", show_header=True)
            table.add_column("Issue", style="red")
            table.add_column("Severity", style="yellow")
            table.add_column("Fix", style="green")
            
            for vuln in vulnerabilities[:5]:  # Show first 5
                severity = severity_levels.get(vuln, "Medium") if severity_levels else "Medium"
                fix = fixes.get(vuln, "See report")
                table.add_row(vuln, severity, fix)
            
            console.print(table)
        
        return f"Security audit found {len(vulnerabilities)} issues"
    
    def code_review(self, reasoning: str, issues: List, improvements: Dict, metrics: Dict = None) -> str:
        """Review code quality"""
        console.print(Panel(
            f"[yellow]Code Review[/yellow]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Issues:[/dim] {len(issues)}",
            border_style="yellow"
        ))
        
        if metrics:
            self.quality_metrics.update(metrics)
        
        # Display code metrics
        if metrics:
            table = Table(title="Code Quality Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for metric, value in metrics.items():
                table.add_row(metric, str(value))
            
            console.print(table)
        
        return f"Code review found {len(issues)} issues"
    
    def setup_ci(self, reasoning: str, platform: str, config_files: Dict, test_stages: List = None) -> str:
        """Set up CI/CD testing"""
        console.print(Panel(
            f"[green]Setting up CI/CD[/green]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Platform:[/dim] {platform}\n"
            f"[dim]Stages:[/dim] {', '.join(test_stages) if test_stages else 'Standard'}",
            border_style="green"
        ))
        
        self.test_files.update(config_files)
        
        return f"CI/CD configured for {platform}"
    
    def performance_test(self, reasoning: str, test_scenarios: List, benchmarks: Dict) -> str:
        """Create performance tests"""
        console.print(Panel(
            f"[cyan]Performance Testing[/cyan]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]Scenarios:[/dim] {len(test_scenarios)}",
            border_style="cyan"
        ))
        
        self.quality_metrics['performance_benchmarks'] = benchmarks
        
        return f"Created {len(test_scenarios)} performance test scenarios"
    
    def generate_report(self, reasoning: str, report_content: str, filename: str, summary: Dict = None) -> str:
        """Generate quality report"""
        console.print(Panel(
            f"[green]Generating Report[/green]\n"
            f"[bold]Reasoning:[/bold] {reasoning}\n"
            f"[dim]File:[/dim] {filename}",
            border_style="green"
        ))
        
        # Save report
        with open(filename, 'w') as f:
            f.write(report_content)
        
        # Save metrics
        metrics_file = Path(filename).with_suffix('.metrics.json')
        with open(metrics_file, 'w') as f:
            json.dump({
                'metrics': self.quality_metrics,
                'vulnerabilities': self.vulnerabilities,
                'summary': summary or {},
                'generated_at': time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
        
        # Save test files
        for file_path, content in self.test_files.items():
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        
        return f"Quality report saved to {filename}"
    
    def run(self, prompt: str, requirements: Dict, code_path: str, output_file: str, compute_limit: int = 10) -> bool:
        """Run the agent with Claude API or simulation"""
        
        if not self.client:
            return self._run_simulation(prompt, requirements, output_file)
        
        # Prepare the full prompt
        full_prompt = AGENT_PROMPT.replace("{{requirements}}", json.dumps(requirements, indent=2))
        full_prompt = full_prompt.replace("{{code_path}}", code_path)
        full_prompt = full_prompt.replace("{{focus}}", requirements.get("focus", "all"))
        full_prompt = full_prompt.replace("{{task}}", prompt)
        
        messages = [{"role": "user", "content": full_prompt}]
        
        # Tool definitions for Anthropic
        tools = [
            {
                "name": "create_tests",
                "description": "Generate comprehensive test suites",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "test_type": {"type": "string"},
                        "test_files": {"type": "object"},
                        "coverage_target": {"type": "number"}
                    },
                    "required": ["reasoning", "test_type", "test_files"]
                }
            },
            {
                "name": "security_audit",
                "description": "Perform security audit and vulnerability scanning",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "vulnerabilities": {"type": "array"},
                        "fixes": {"type": "object"},
                        "severity_levels": {"type": "object"}
                    },
                    "required": ["reasoning", "vulnerabilities", "fixes"]
                }
            },
            {
                "name": "code_review",
                "description": "Review code quality and standards compliance",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "issues": {"type": "array"},
                        "improvements": {"type": "object"},
                        "metrics": {"type": "object"}
                    },
                    "required": ["reasoning", "issues", "improvements"]
                }
            },
            {
                "name": "setup_ci",
                "description": "Configure CI/CD testing pipelines",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "platform": {"type": "string"},
                        "config_files": {"type": "object"},
                        "test_stages": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["reasoning", "platform", "config_files"]
                }
            },
            {
                "name": "performance_test",
                "description": "Create and run performance tests",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "test_scenarios": {"type": "array"},
                        "benchmarks": {"type": "object"}
                    },
                    "required": ["reasoning", "test_scenarios", "benchmarks"]
                }
            },
            {
                "name": "generate_report",
                "description": "Generate comprehensive quality report",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string"},
                        "report_content": {"type": "string"},
                        "filename": {"type": "string"},
                        "summary": {"type": "object"}
                    },
                    "required": ["reasoning", "report_content", "filename"]
                }
            }
        ]
        
        iterations = 0
        console.rule("[yellow]Starting Quality Guardian Agent[/yellow]")
        
        while iterations < compute_limit:
            iterations += 1
            console.rule(f"[blue]Iteration {iterations}/{compute_limit}[/blue]")
            
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=messages,
                    tools=tools,
                    tool_choice={"type": "auto"}
                )
                
                # Process response
                assistant_content = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        assistant_content += block.text
                        console.print(Panel(block.text, title="Assistant"))
                    
                    elif hasattr(block, 'type') and block.type == 'tool_use':
                        tool_name = block.name
                        tool_args = block.input
                        tool_id = block.id
                        
                        console.print(f"[yellow]Tool Call:[/yellow] {tool_name}")
                        
                        # Execute tool
                        if tool_name == "create_tests":
                            result = self.create_tests(**tool_args)
                        elif tool_name == "security_audit":
                            result = self.security_audit(**tool_args)
                        elif tool_name == "code_review":
                            result = self.code_review(**tool_args)
                        elif tool_name == "setup_ci":
                            result = self.setup_ci(**tool_args)
                        elif tool_name == "performance_test":
                            result = self.performance_test(**tool_args)
                        elif tool_name == "generate_report":
                            tool_args['filename'] = output_file
                            result = self.generate_report(**tool_args)
                            console.print(Panel(
                                f"[bold green]Quality Check Complete![/bold green]\n"
                                f"Report saved to: {output_file}",
                                border_style="green"
                            ))
                            return True
                        else:
                            result = f"Unknown tool: {tool_name}"
                        
                        # Add messages for next iteration
                        messages.append({"role": "assistant", "content": response.content})
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": result
                                }
                            ]
                        })
                
                if assistant_content and not any(hasattr(b, 'type') and b.type == 'tool_use' for b in response.content):
                    # No tool calls, agent is done
                    break
                    
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                return False
        
        console.print("[yellow]Maximum iterations reached[/yellow]")
        return False
    
    def _run_simulation(self, prompt: str, requirements: Dict, output_file: str) -> bool:
        """Simulate agent execution without API"""
        console.print("[yellow]Running in simulation mode (no API key)[/yellow]")
        
        # Simulate workflow
        self.create_tests(
            "Need comprehensive test coverage",
            "unit",
            {
                "tests/test_auth.py": "# Authentication tests",
                "tests/test_api.py": "# API endpoint tests",
                "tests/test_models.py": "# Model tests"
            },
            95
        )
        
        time.sleep(1)
        
        self.security_audit(
            "OWASP Top 10 security check",
            ["SQL Injection risk", "Missing CSRF protection", "Weak password policy"],
            {
                "SQL Injection risk": "Use parameterized queries",
                "Missing CSRF protection": "Add CSRF tokens",
                "Weak password policy": "Enforce strong passwords"
            },
            {"SQL Injection risk": "Critical", "Missing CSRF protection": "High", "Weak password policy": "Medium"}
        )
        
        time.sleep(1)
        
        self.code_review(
            "SOLID principles and best practices",
            ["Long methods", "Duplicate code", "Missing error handling"],
            {"refactoring": "Extract methods", "DRY": "Create utilities"},
            {"complexity": 15, "duplication": "5%", "test_coverage": "85%"}
        )
        
        time.sleep(1)
        
        self.setup_ci(
            "Automated testing on every commit",
            "github-actions",
            {
                ".github/workflows/test.yml": "# GitHub Actions test workflow",
                ".github/workflows/security.yml": "# Security scanning workflow"
            },
            ["lint", "test", "security", "deploy"]
        )
        
        time.sleep(1)
        
        # Generate simulated report
        report_content = f"""# Quality Assurance Report

## Executive Summary
- Test Coverage: 95%
- Security Issues: 3 (1 Critical, 1 High, 1 Medium)
- Code Quality Score: B+

## Test Coverage
- Unit Tests: 95%
- Integration Tests: 85%
- E2E Tests: 70%

## Security Findings
1. **Critical**: SQL Injection vulnerability
2. **High**: Missing CSRF protection
3. **Medium**: Weak password policy

## Code Quality
- Complexity: 15 (Target: <10)
- Duplication: 5% (Target: <3%)
- Test Coverage: 85% (Target: >90%)

## Recommendations
1. Fix critical security issues immediately
2. Increase test coverage to 90%+
3. Refactor complex methods

*Generated in simulation mode*
"""
        
        self.generate_report(
            "Comprehensive quality assessment",
            report_content,
            output_file,
            {"status": "Needs Improvement", "priority_fixes": 3}
        )
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Quality Guardian Agent")
    parser.add_argument("--prompt", "-p", required=True, help="Quality check prompt")
    parser.add_argument("--codebase", "-c", default="./src", help="Path to codebase")
    parser.add_argument("--output", "-o", default="quality_report.md", help="Output report file")
    parser.add_argument("--requirements", "-r", help="Path to requirements.yaml file")
    parser.add_argument("--audit", "-a", choices=["security", "performance", "all"], help="Audit type")
    parser.add_argument("--framework", "-f", help="Test framework to use")
    parser.add_argument("--compute", type=int, default=10, help="Max compute iterations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Load requirements
    requirements = {}
    if args.requirements and Path(args.requirements).exists():
        with open(args.requirements) as f:
            requirements = yaml.safe_load(f)
    else:
        requirements = {
            "name": "QualityCheck",
            "type": "quality_audit",
            "description": args.prompt,
            "focus": args.audit or "all",
            "framework": args.framework
        }
    
    # Run agent
    agent = QualityGuardianAgent()
    success = agent.run(args.prompt, requirements, args.codebase, args.output, args.compute)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()