#!/usr/bin/env python3
"""
Standalone Security Auditor Agent (SFA)
Comprehensive security scanning and vulnerability detection

This agent performs security audits, identifies vulnerabilities,
and ensures compliance with security best practices.
"""

import os
import sys
import json
import yaml
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import hashlib
import base64

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.agent_logger import get_logger
from lib.agent_runtime import AnthropicAgentRunner, AgentContext, ModelType

class SeverityLevel(Enum):
    """Security issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class SecurityFinding:
    """Represents a security finding"""
    severity: SeverityLevel
    category: str
    title: str
    description: str
    file_path: Optional[str]
    line_number: Optional[int]
    remediation: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "severity": self.severity.value,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "remediation": self.remediation,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category
        }

class SecurityAuditor:
    """
    Security Auditor Agent
    Performs comprehensive security audits and vulnerability detection
    """
    
    VULNERABILITY_PATTERNS = {
        "sql_injection": [
            r"f['\"].*SELECT.*{.*}['\"]",  # f-string SQL
            r"['\"].*SELECT.*['\"].*\+.*",  # String concatenation SQL
            r"execute\(['\"].*%s.*['\"]",  # Non-parameterized query
            r"raw\(['\"].*SELECT.*['\"]",  # Django raw SQL
        ],
        "xss": [
            r"innerHTML\s*=\s*[^'\"]*\+",  # Direct innerHTML assignment
            r"document\.write\(",  # document.write usage
            r"eval\(",  # eval usage
            r"dangerouslySetInnerHTML",  # React dangerous HTML without sanitization
        ],
        "hardcoded_secrets": [
            r"['\"].*(?:api[_-]?key|secret|password|token)['\"].*[:=].*['\"][^'\"]{20,}['\"]",
            r"(?:AWS|aws)[_]?(?:ACCESS|SECRET).*=.*['\"][^'\"]+['\"]",
            r"(?:PRIVATE|private)[_-]?(?:KEY|key).*=.*['\"][^'\"]+['\"]",
        ],
        "weak_crypto": [
            r"md5|MD5",
            r"sha1|SHA1",
            r"DES|des",
            r"Random\(\)",  # Weak random
        ],
        "path_traversal": [
            r"\.\.\/",  # Directory traversal
            r"os\.path\.join.*request\.",  # Unsanitized path join
            r"open\(.*request\.",  # Direct file open from request
        ]
    }
    
    SECURE_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    def __init__(self, project_path: str = ".", verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
        self.logger = get_logger()
        self.findings: List[SecurityFinding] = []
        self.files_scanned = 0
        self.runner = None
        
        # Try to initialize API runner
        try:
            self.runner = AnthropicAgentRunner(logger=self.logger)
        except Exception as e:
            print(f"Note: Running in offline mode - {e}")
    
    def scan_project(self) -> Dict[str, Any]:
        """
        Perform comprehensive security scan of the project
        """
        print("🔍 Starting Security Audit...")
        print("=" * 60)
        
        # Phase 1: Static code analysis
        print("\n📝 Phase 1: Static Code Analysis")
        self._scan_source_code()
        
        # Phase 2: Dependency scanning
        print("\n📦 Phase 2: Dependency Scanning")
        self._scan_dependencies()
        
        # Phase 3: Configuration review
        print("\n⚙️ Phase 3: Configuration Review")
        self._review_configurations()
        
        # Phase 4: Docker/Container security
        print("\n🐳 Phase 4: Container Security")
        self._scan_containers()
        
        # Phase 5: Infrastructure as Code
        print("\n☁️ Phase 5: Infrastructure Security")
        self._scan_infrastructure()
        
        # Generate report
        report = self._generate_report()
        
        return report
    
    def _scan_source_code(self):
        """Scan source code for vulnerabilities"""
        extensions = {
            ".py": self._scan_python_file,
            ".js": self._scan_javascript_file,
            ".jsx": self._scan_javascript_file,
            ".ts": self._scan_javascript_file,
            ".tsx": self._scan_javascript_file,
            ".php": self._scan_php_file,
            ".java": self._scan_java_file,
            ".cs": self._scan_csharp_file,
            ".rb": self._scan_ruby_file,
            ".go": self._scan_go_file
        }
        
        for ext, scanner in extensions.items():
            for file_path in self.project_path.rglob(f"*{ext}"):
                # Skip node_modules, venv, etc.
                if any(skip in str(file_path) for skip in ["node_modules", "venv", ".git", "__pycache__"]):
                    continue
                
                self.files_scanned += 1
                if self.verbose:
                    print(f"  Scanning: {file_path}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        scanner(file_path, content)
                except Exception as e:
                    if self.verbose:
                        print(f"    Error scanning {file_path}: {e}")
    
    def _scan_python_file(self, file_path: Path, content: str):
        """Scan Python file for vulnerabilities"""
        lines = content.split('\n')
        
        # Check for SQL injection
        for i, line in enumerate(lines, 1):
            for pattern in self.VULNERABILITY_PATTERNS["sql_injection"]:
                if re.search(pattern, line, re.IGNORECASE):
                    self.findings.append(SecurityFinding(
                        severity=SeverityLevel.CRITICAL,
                        category="Injection",
                        title="Potential SQL Injection",
                        description=f"Possible SQL injection vulnerability detected. Use parameterized queries.",
                        file_path=str(file_path),
                        line_number=i,
                        remediation="Use parameterized queries or an ORM with proper escaping",
                        cwe_id="CWE-89",
                        owasp_category="A03:2021 – Injection"
                    ))
        
        # Check for hardcoded secrets
        for i, line in enumerate(lines, 1):
            for pattern in self.VULNERABILITY_PATTERNS["hardcoded_secrets"]:
                if re.search(pattern, line, re.IGNORECASE):
                    self.findings.append(SecurityFinding(
                        severity=SeverityLevel.HIGH,
                        category="Security Misconfiguration",
                        title="Hardcoded Secret Detected",
                        description="Hardcoded credentials or API keys found in source code",
                        file_path=str(file_path),
                        line_number=i,
                        remediation="Use environment variables or secure secret management service",
                        cwe_id="CWE-798",
                        owasp_category="A05:2021 – Security Misconfiguration"
                    ))
        
        # Check for weak cryptography
        if any(re.search(pattern, content, re.IGNORECASE) for pattern in self.VULNERABILITY_PATTERNS["weak_crypto"]):
            self.findings.append(SecurityFinding(
                severity=SeverityLevel.MEDIUM,
                category="Cryptographic Failures",
                title="Weak Cryptographic Algorithm",
                description="Usage of weak or deprecated cryptographic algorithms detected",
                file_path=str(file_path),
                line_number=None,
                remediation="Use strong algorithms like SHA-256, bcrypt, or argon2",
                cwe_id="CWE-327",
                owasp_category="A02:2021 – Cryptographic Failures"
            ))
        
        # Check for insecure random
        if re.search(r"random\.random\(|random\.randint\(", content):
            self.findings.append(SecurityFinding(
                severity=SeverityLevel.MEDIUM,
                category="Cryptographic Failures",
                title="Insecure Random Number Generator",
                description="Using non-cryptographic random for security purposes",
                file_path=str(file_path),
                line_number=None,
                remediation="Use secrets.SystemRandom() or os.urandom() for security-sensitive operations",
                cwe_id="CWE-330"
            ))
    
    def _scan_javascript_file(self, file_path: Path, content: str):
        """Scan JavaScript/TypeScript file for vulnerabilities"""
        lines = content.split('\n')
        
        # Check for XSS vulnerabilities
        for i, line in enumerate(lines, 1):
            for pattern in self.VULNERABILITY_PATTERNS["xss"]:
                if re.search(pattern, line):
                    self.findings.append(SecurityFinding(
                        severity=SeverityLevel.HIGH,
                        category="Cross-Site Scripting",
                        title="Potential XSS Vulnerability",
                        description="Possible XSS vulnerability through unsafe DOM manipulation",
                        file_path=str(file_path),
                        line_number=i,
                        remediation="Sanitize user input and use safe DOM manipulation methods",
                        cwe_id="CWE-79",
                        owasp_category="A03:2021 – Injection"
                    ))
        
        # Check for eval usage
        if "eval(" in content:
            self.findings.append(SecurityFinding(
                severity=SeverityLevel.HIGH,
                category="Code Injection",
                title="Dangerous eval() Usage",
                description="eval() can execute arbitrary code and should be avoided",
                file_path=str(file_path),
                line_number=None,
                remediation="Use JSON.parse() for JSON or safer alternatives",
                cwe_id="CWE-95"
            ))
    
    def _scan_php_file(self, file_path: Path, content: str):
        """Scan PHP file for vulnerabilities"""
        # PHP-specific vulnerability checks
        if "mysql_query" in content or "mysqli_query" in content:
            if "$_GET" in content or "$_POST" in content or "$_REQUEST" in content:
                self.findings.append(SecurityFinding(
                    severity=SeverityLevel.CRITICAL,
                    category="Injection",
                    title="Potential SQL Injection in PHP",
                    description="Direct use of user input in SQL queries",
                    file_path=str(file_path),
                    line_number=None,
                    remediation="Use prepared statements with PDO or mysqli",
                    cwe_id="CWE-89",
                    owasp_category="A03:2021 – Injection"
                ))
    
    def _scan_java_file(self, file_path: Path, content: str):
        """Scan Java file for vulnerabilities"""
        # Java-specific checks
        if "Statement" in content and "execute" in content:
            self.findings.append(SecurityFinding(
                severity=SeverityLevel.HIGH,
                category="Injection",
                title="Potential SQL Injection in Java",
                description="Use of Statement instead of PreparedStatement",
                file_path=str(file_path),
                line_number=None,
                remediation="Use PreparedStatement for all database queries",
                cwe_id="CWE-89"
            ))
    
    def _scan_csharp_file(self, file_path: Path, content: str):
        """Scan C# file for vulnerabilities"""
        # C#-specific checks
        if "SqlCommand" in content and "CommandText" in content:
            if not "SqlParameter" in content:
                self.findings.append(SecurityFinding(
                    severity=SeverityLevel.HIGH,
                    category="Injection",
                    title="Potential SQL Injection in C#",
                    description="SqlCommand without parameters detected",
                    file_path=str(file_path),
                    line_number=None,
                    remediation="Use SqlParameter for all user inputs",
                    cwe_id="CWE-89"
                ))
    
    def _scan_ruby_file(self, file_path: Path, content: str):
        """Scan Ruby file for vulnerabilities"""
        # Ruby-specific checks
        if "find_by_sql" in content or "execute" in content:
            self.findings.append(SecurityFinding(
                severity=SeverityLevel.MEDIUM,
                category="Injection",
                title="Potential SQL Injection in Ruby",
                description="Direct SQL execution detected",
                file_path=str(file_path),
                line_number=None,
                remediation="Use ActiveRecord query interface or sanitize inputs",
                cwe_id="CWE-89"
            ))
    
    def _scan_go_file(self, file_path: Path, content: str):
        """Scan Go file for vulnerabilities"""
        # Go-specific checks
        if "fmt.Sprintf" in content and ("SELECT" in content or "INSERT" in content):
            self.findings.append(SecurityFinding(
                severity=SeverityLevel.HIGH,
                category="Injection",
                title="Potential SQL Injection in Go",
                description="String formatting in SQL queries",
                file_path=str(file_path),
                line_number=None,
                remediation="Use parameterized queries with database/sql package",
                cwe_id="CWE-89"
            ))
    
    def _scan_dependencies(self):
        """Scan project dependencies for vulnerabilities"""
        # Python dependencies
        requirements_files = list(self.project_path.glob("**/requirements*.txt"))
        for req_file in requirements_files:
            self._check_python_dependencies(req_file)
        
        # Node.js dependencies
        package_files = list(self.project_path.glob("**/package.json"))
        for pkg_file in package_files:
            self._check_node_dependencies(pkg_file)
        
        # Check for Dockerfile
        dockerfiles = list(self.project_path.glob("**/Dockerfile*"))
        for dockerfile in dockerfiles:
            self._check_dockerfile(dockerfile)
    
    def _check_python_dependencies(self, req_file: Path):
        """Check Python dependencies for vulnerabilities"""
        try:
            # Try to use safety if available
            result = subprocess.run(
                ["safety", "check", "-r", str(req_file), "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0 and result.stdout:
                vulnerabilities = json.loads(result.stdout)
                for vuln in vulnerabilities:
                    self.findings.append(SecurityFinding(
                        severity=SeverityLevel.HIGH,
                        category="Vulnerable Dependencies",
                        title=f"Vulnerable Package: {vuln.get('package', 'Unknown')}",
                        description=vuln.get('description', 'Known vulnerability in dependency'),
                        file_path=str(req_file),
                        line_number=None,
                        remediation=f"Update to version {vuln.get('safe_version', 'latest')}",
                        cwe_id=vuln.get('cve')
                    ))
        except (subprocess.SubprocessError, FileNotFoundError):
            # Safety not installed, do basic checks
            if self.verbose:
                print("    Note: Install 'safety' for detailed dependency scanning")
    
    def _check_node_dependencies(self, pkg_file: Path):
        """Check Node.js dependencies for vulnerabilities"""
        try:
            # Try npm audit
            pkg_dir = pkg_file.parent
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=pkg_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                audit_data = json.loads(result.stdout)
                if "vulnerabilities" in audit_data:
                    vulns = audit_data["vulnerabilities"]
                    for severity in ["critical", "high", "moderate", "low"]:
                        count = vulns.get(severity, 0)
                        if count > 0:
                            self.findings.append(SecurityFinding(
                                severity=SeverityLevel[severity.upper()] if severity != "moderate" else SeverityLevel.MEDIUM,
                                category="Vulnerable Dependencies",
                                title=f"{count} {severity} severity npm vulnerabilities",
                                description=f"Run 'npm audit' for details",
                                file_path=str(pkg_file),
                                line_number=None,
                                remediation="Run 'npm audit fix' to update vulnerable packages"
                            ))
        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
            if self.verbose:
                print("    Note: npm not available for dependency scanning")
    
    def _review_configurations(self):
        """Review security configurations"""
        # Check for .env files
        env_files = list(self.project_path.glob("**/.env*"))
        for env_file in env_files:
            if ".example" not in str(env_file) and ".template" not in str(env_file):
                self.findings.append(SecurityFinding(
                    severity=SeverityLevel.HIGH,
                    category="Security Misconfiguration",
                    title="Environment File in Repository",
                    description=".env file found - should not be committed to repository",
                    file_path=str(env_file),
                    line_number=None,
                    remediation="Add .env to .gitignore and use .env.example for templates",
                    owasp_category="A05:2021 – Security Misconfiguration"
                ))
        
        # Check for CORS configuration
        self._check_cors_config()
        
        # Check for security headers
        self._check_security_headers()
    
    def _check_cors_config(self):
        """Check CORS configuration"""
        # Look for CORS misconfigurations
        for file_path in self.project_path.rglob("*.py"):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if "allow_origins=['*']" in content or 'allow_origins=["*"]' in content:
                        self.findings.append(SecurityFinding(
                            severity=SeverityLevel.MEDIUM,
                            category="Security Misconfiguration",
                            title="Overly Permissive CORS",
                            description="CORS configured to allow all origins",
                            file_path=str(file_path),
                            line_number=None,
                            remediation="Specify allowed origins explicitly",
                            owasp_category="A05:2021 – Security Misconfiguration"
                        ))
            except:
                pass
    
    def _check_security_headers(self):
        """Check for security headers implementation"""
        # This would need actual server testing, so we check for configuration
        config_files = list(self.project_path.glob("**/*config*"))
        headers_found = False
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for header in self.SECURE_HEADERS:
                        if header in content:
                            headers_found = True
                            break
            except:
                pass
        
        if not headers_found:
            self.findings.append(SecurityFinding(
                severity=SeverityLevel.MEDIUM,
                category="Security Misconfiguration",
                title="Missing Security Headers",
                description="Security headers not configured",
                file_path=None,
                line_number=None,
                remediation="Implement security headers: " + ", ".join(self.SECURE_HEADERS.keys()),
                owasp_category="A05:2021 – Security Misconfiguration"
            ))
    
    def _check_dockerfile(self, dockerfile: Path):
        """Check Dockerfile for security issues"""
        try:
            with open(dockerfile, 'r') as f:
                content = f.read()
                
                # Check for running as root
                if "USER" not in content:
                    self.findings.append(SecurityFinding(
                        severity=SeverityLevel.MEDIUM,
                        category="Container Security",
                        title="Container Running as Root",
                        description="No USER instruction found in Dockerfile",
                        file_path=str(dockerfile),
                        line_number=None,
                        remediation="Add 'USER' instruction to run as non-root user",
                        cwe_id="CWE-250"
                    ))
                
                # Check for latest tags
                if ":latest" in content:
                    self.findings.append(SecurityFinding(
                        severity=SeverityLevel.LOW,
                        category="Container Security",
                        title="Using 'latest' Tag",
                        description="Using 'latest' tag can lead to unpredictable builds",
                        file_path=str(dockerfile),
                        line_number=None,
                        remediation="Use specific version tags for base images"
                    ))
                
                # Check for secret exposure
                if "ENV" in content and any(secret in content.upper() for secret in ["PASSWORD", "SECRET", "KEY", "TOKEN"]):
                    self.findings.append(SecurityFinding(
                        severity=SeverityLevel.HIGH,
                        category="Container Security",
                        title="Potential Secret in Dockerfile",
                        description="Possible secrets exposed in ENV instructions",
                        file_path=str(dockerfile),
                        line_number=None,
                        remediation="Use build secrets or runtime environment variables",
                        cwe_id="CWE-798"
                    ))
        except Exception as e:
            if self.verbose:
                print(f"Error checking Dockerfile: {e}")
    
    def _scan_containers(self):
        """Scan container configurations"""
        # Check docker-compose files
        compose_files = list(self.project_path.glob("**/docker-compose*.yml"))
        for compose_file in compose_files:
            self._check_docker_compose(compose_file)
    
    def _check_docker_compose(self, compose_file: Path):
        """Check docker-compose configuration"""
        try:
            with open(compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
                
                if "services" in compose_data:
                    for service_name, service_config in compose_data["services"].items():
                        # Check for privileged mode
                        if service_config.get("privileged", False):
                            self.findings.append(SecurityFinding(
                                severity=SeverityLevel.HIGH,
                                category="Container Security",
                                title=f"Privileged Container: {service_name}",
                                description="Container running in privileged mode",
                                file_path=str(compose_file),
                                line_number=None,
                                remediation="Remove privileged mode unless absolutely necessary",
                                cwe_id="CWE-250"
                            ))
                        
                        # Check for exposed ports
                        if "ports" in service_config:
                            for port in service_config["ports"]:
                                if isinstance(port, str) and port.startswith("0.0.0.0:"):
                                    self.findings.append(SecurityFinding(
                                        severity=SeverityLevel.MEDIUM,
                                        category="Container Security",
                                        title=f"Port Exposed to All Interfaces: {service_name}",
                                        description=f"Port {port} exposed to all network interfaces",
                                        file_path=str(compose_file),
                                        line_number=None,
                                        remediation="Bind to specific interface or use internal networks"
                                    ))
        except Exception as e:
            if self.verbose:
                print(f"Error checking docker-compose: {e}")
    
    def _scan_infrastructure(self):
        """Scan infrastructure as code"""
        # Check for Terraform files
        tf_files = list(self.project_path.glob("**/*.tf"))
        for tf_file in tf_files:
            self._check_terraform(tf_file)
        
        # Check for CloudFormation
        cf_files = list(self.project_path.glob("**/*template*.yml")) + \
                   list(self.project_path.glob("**/*template*.yaml"))
        for cf_file in cf_files:
            self._check_cloudformation(cf_file)
    
    def _check_terraform(self, tf_file: Path):
        """Check Terraform configuration"""
        try:
            with open(tf_file, 'r') as f:
                content = f.read()
                
                # Check for hardcoded credentials
                if "access_key" in content or "secret_key" in content:
                    self.findings.append(SecurityFinding(
                        severity=SeverityLevel.CRITICAL,
                        category="Infrastructure Security",
                        title="Hardcoded AWS Credentials",
                        description="AWS credentials found in Terraform file",
                        file_path=str(tf_file),
                        line_number=None,
                        remediation="Use environment variables or AWS IAM roles",
                        cwe_id="CWE-798"
                    ))
                
                # Check for public S3 buckets
                if 'acl = "public-read"' in content:
                    self.findings.append(SecurityFinding(
                        severity=SeverityLevel.HIGH,
                        category="Infrastructure Security",
                        title="Public S3 Bucket",
                        description="S3 bucket configured with public access",
                        file_path=str(tf_file),
                        line_number=None,
                        remediation="Use private ACL and configure bucket policies explicitly"
                    ))
        except Exception as e:
            if self.verbose:
                print(f"Error checking Terraform: {e}")
    
    def _check_cloudformation(self, cf_file: Path):
        """Check CloudFormation template"""
        try:
            with open(cf_file, 'r') as f:
                template = yaml.safe_load(f)
                
                if "Resources" in template:
                    for resource_name, resource in template["Resources"].items():
                        # Check for security group rules
                        if resource.get("Type") == "AWS::EC2::SecurityGroup":
                            self._check_security_group(resource, cf_file, resource_name)
        except Exception as e:
            if self.verbose:
                print(f"Error checking CloudFormation: {e}")
    
    def _check_security_group(self, sg_resource: Dict, file_path: Path, resource_name: str):
        """Check security group configuration"""
        properties = sg_resource.get("Properties", {})
        
        # Check ingress rules
        for rule in properties.get("SecurityGroupIngress", []):
            if rule.get("CidrIp") == "0.0.0.0/0":
                port = rule.get("FromPort", "unknown")
                self.findings.append(SecurityFinding(
                    severity=SeverityLevel.HIGH,
                    category="Infrastructure Security",
                    title=f"Open Security Group: {resource_name}",
                    description=f"Port {port} open to the internet (0.0.0.0/0)",
                    file_path=str(file_path),
                    line_number=None,
                    remediation="Restrict access to specific IP ranges"
                ))
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate security audit report"""
        # Count findings by severity
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for finding in self.findings:
            severity_counts[finding.severity.value] += 1
        
        # Generate report
        report = {
            "scan_date": datetime.now().isoformat(),
            "project_path": str(self.project_path),
            "files_scanned": self.files_scanned,
            "total_findings": len(self.findings),
            "severity_summary": severity_counts,
            "findings": [f.to_dict() for f in self.findings],
            "compliance": self._check_compliance()
        }
        
        # Save reports
        self._save_json_report(report)
        self._save_markdown_report(report)
        self._save_html_report(report)
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _check_compliance(self) -> Dict[str, str]:
        """Check compliance with various standards"""
        compliance = {
            "OWASP_Top_10": "Unknown",
            "PCI_DSS": "Unknown",
            "GDPR": "Unknown",
            "HIPAA": "Unknown"
        }
        
        # Basic compliance checks based on findings
        owasp_issues = sum(1 for f in self.findings if f.owasp_category)
        
        if owasp_issues == 0:
            compliance["OWASP_Top_10"] = "Compliant"
        elif any(f.severity == SeverityLevel.CRITICAL for f in self.findings):
            compliance["OWASP_Top_10"] = "Non-Compliant"
        else:
            compliance["OWASP_Top_10"] = "Partial"
        
        # Check for PCI DSS relevant issues
        if any("payment" in str(f.file_path).lower() or "card" in f.description.lower() 
               for f in self.findings if f.file_path):
            if any(f.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH] for f in self.findings):
                compliance["PCI_DSS"] = "Non-Compliant"
            else:
                compliance["PCI_DSS"] = "Review Required"
        
        return compliance
    
    def _save_json_report(self, report: Dict):
        """Save JSON report"""
        report_file = self.project_path / "security_audit_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n📄 JSON report saved to: {report_file}")
    
    def _save_markdown_report(self, report: Dict):
        """Save Markdown report"""
        report_file = self.project_path / "security_audit_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Security Audit Report\n\n")
            f.write(f"**Date**: {report['scan_date']}\n")
            f.write(f"**Project**: {report['project_path']}\n")
            f.write(f"**Files Scanned**: {report['files_scanned']}\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write(f"Total findings: {report['total_findings']}\n\n")
            
            f.write("### Severity Distribution\n")
            for severity, count in report['severity_summary'].items():
                f.write(f"- **{severity.upper()}**: {count}\n")
            
            f.write("\n## Compliance Status\n\n")
            for standard, status in report['compliance'].items():
                f.write(f"- **{standard}**: {status}\n")
            
            # Group findings by severity
            f.write("\n## Findings\n\n")
            
            for severity in ["critical", "high", "medium", "low", "info"]:
                severity_findings = [f for f in self.findings if f.severity.value == severity]
                if severity_findings:
                    f.write(f"### {severity.upper()} Severity\n\n")
                    for finding in severity_findings:
                        f.write(f"#### {finding.title}\n")
                        f.write(f"- **Category**: {finding.category}\n")
                        f.write(f"- **Description**: {finding.description}\n")
                        if finding.file_path:
                            f.write(f"- **File**: {finding.file_path}\n")
                        if finding.line_number:
                            f.write(f"- **Line**: {finding.line_number}\n")
                        f.write(f"- **Remediation**: {finding.remediation}\n")
                        if finding.cwe_id:
                            f.write(f"- **CWE**: {finding.cwe_id}\n")
                        if finding.owasp_category:
                            f.write(f"- **OWASP**: {finding.owasp_category}\n")
                        f.write("\n")
            
            f.write("\n## Recommendations\n\n")
            f.write("1. Address all CRITICAL and HIGH severity findings immediately\n")
            f.write("2. Implement security testing in CI/CD pipeline\n")
            f.write("3. Conduct regular security audits\n")
            f.write("4. Keep dependencies up to date\n")
            f.write("5. Implement security training for development team\n")
        
        print(f"📄 Markdown report saved to: {report_file}")
    
    def _save_html_report(self, report: Dict):
        """Save HTML report"""
        report_file = self.project_path / "security_audit_report.html"
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Security Audit Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .critical {{ background: #e74c3c; color: white; padding: 5px 10px; border-radius: 3px; }}
        .high {{ background: #e67e22; color: white; padding: 5px 10px; border-radius: 3px; }}
        .medium {{ background: #f39c12; color: white; padding: 5px 10px; border-radius: 3px; }}
        .low {{ background: #3498db; color: white; padding: 5px 10px; border-radius: 3px; }}
        .info {{ background: #95a5a6; color: white; padding: 5px 10px; border-radius: 3px; }}
        .finding {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }}
        .finding.critical {{ border-left-color: #e74c3c; }}
        .finding.high {{ border-left-color: #e67e22; }}
        .finding.medium {{ border-left-color: #f39c12; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Audit Report</h1>
        <p>Generated: {report['scan_date']}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Files Scanned</td><td>{report['files_scanned']}</td></tr>
            <tr><td>Total Findings</td><td>{report['total_findings']}</td></tr>
            <tr><td>Critical</td><td><span class="critical">{report['severity_summary']['critical']}</span></td></tr>
            <tr><td>High</td><td><span class="high">{report['severity_summary']['high']}</span></td></tr>
            <tr><td>Medium</td><td><span class="medium">{report['severity_summary']['medium']}</span></td></tr>
            <tr><td>Low</td><td><span class="low">{report['severity_summary']['low']}</span></td></tr>
        </table>
    </div>
    
    <div class="summary">
        <h2>Findings</h2>
"""
        
        for finding in self.findings:
            html_content += f"""
        <div class="finding {finding.severity.value}">
            <h3>{finding.title}</h3>
            <p><strong>Severity:</strong> <span class="{finding.severity.value}">{finding.severity.value.upper()}</span></p>
            <p><strong>Category:</strong> {finding.category}</p>
            <p><strong>Description:</strong> {finding.description}</p>
            {f'<p><strong>File:</strong> {finding.file_path}</p>' if finding.file_path else ''}
            {f'<p><strong>Line:</strong> {finding.line_number}</p>' if finding.line_number else ''}
            <p><strong>Remediation:</strong> {finding.remediation}</p>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>"""
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        print(f"📄 HTML report saved to: {report_file}")
    
    def _print_summary(self, report: Dict):
        """Print summary to console"""
        print("\n" + "="*60)
        print("SECURITY AUDIT SUMMARY")
        print("="*60)
        
        print(f"\nFiles Scanned: {report['files_scanned']}")
        print(f"Total Findings: {report['total_findings']}")
        
        print("\nSeverity Distribution:")
        for severity, count in report['severity_summary'].items():
            symbol = "🔴" if severity == "critical" else "🟠" if severity == "high" else "🟡" if severity == "medium" else "🔵" if severity == "low" else "⚪"
            print(f"  {symbol} {severity.upper()}: {count}")
        
        print("\nCompliance Status:")
        for standard, status in report['compliance'].items():
            symbol = "✅" if status == "Compliant" else "❌" if status == "Non-Compliant" else "⚠️"
            print(f"  {symbol} {standard}: {status}")
        
        if report['severity_summary']['critical'] > 0:
            print("\n⚠️ CRITICAL VULNERABILITIES FOUND - IMMEDIATE ACTION REQUIRED!")
        elif report['severity_summary']['high'] > 0:
            print("\n⚠️ High severity issues found - please review and remediate")
        else:
            print("\n✅ No critical or high severity issues found")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Auditor Agent")
    parser.add_argument("--project-path", default=".", help="Project path to scan")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--output-format", choices=["json", "markdown", "html", "all"], 
                       default="all", help="Report output format")
    
    args = parser.parse_args()
    
    # Create auditor
    auditor = SecurityAuditor(
        project_path=args.project_path,
        verbose=args.verbose
    )
    
    # Run scan
    report = auditor.scan_project()
    
    return 0 if report['severity_summary']['critical'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())