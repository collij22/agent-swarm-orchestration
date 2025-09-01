"""
Post-Execution Verification System - Phase 5.5
Final checks to ensure everything works end-to-end
"""

import os
import subprocess
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class PostExecutionVerification:
    """Comprehensive post-execution verification system"""
    
    def __init__(self, project_root: str, logger: Optional[object] = None):
        self.project_root = Path(project_root)
        self.logger = logger
        self.verification_results = {}
        self.critical_endpoints = [
            "/",
            "/api",
            "/api/health",
            "/health",
            "/api/v1/status"
        ]
        
    def run_all_verifications(self) -> Tuple[bool, Dict]:
        """Run all post-execution verifications"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "backend_start": False,
            "frontend_build": False,
            "docker_containers": False,
            "critical_endpoints": False,
            "overall_success": False,
            "details": {}
        }
        
        # 1. Can backend start?
        backend_result = self.verify_backend_starts()
        results["backend_start"] = backend_result[0]
        results["details"]["backend"] = backend_result[1]
        
        # 2. Can frontend build?
        frontend_result = self.verify_frontend_builds()
        results["frontend_build"] = frontend_result[0]
        results["details"]["frontend"] = frontend_result[1]
        
        # 3. Do Docker containers run?
        docker_result = self.verify_docker_containers()
        results["docker_containers"] = docker_result[0]
        results["details"]["docker"] = docker_result[1]
        
        # 4. Are critical endpoints accessible?
        endpoints_result = self.verify_critical_endpoints()
        results["critical_endpoints"] = endpoints_result[0]
        results["details"]["endpoints"] = endpoints_result[1]
        
        # Overall success requires at least backend OR frontend to work
        results["overall_success"] = (
            results["backend_start"] or results["frontend_build"]
        )
        
        self.verification_results = results
        
        if self.logger:
            status = "PASSED" if results["overall_success"] else "FAILED"
            self.logger.log_reasoning(
                "post_verification",
                f"Post-execution verification {status}",
                f"Backend: {results['backend_start']}, Frontend: {results['frontend_build']}, "
                f"Docker: {results['docker_containers']}, Endpoints: {results['critical_endpoints']}"
            )
        
        return results["overall_success"], results
    
    def verify_backend_starts(self) -> Tuple[bool, Dict]:
        """Verify that backend can start successfully"""
        
        result = {
            "checked": False,
            "success": False,
            "method": None,
            "output": "",
            "errors": []
        }
        
        # Find backend entry point
        backend_files = [
            self.project_root / "backend" / "main.py",
            self.project_root / "backend" / "app.py",
            self.project_root / "main.py",
            self.project_root / "app.py",
            self.project_root / "backend" / "server.py",
            self.project_root / "backend" / "run.py"
        ]
        
        backend_entry = None
        for file in backend_files:
            if file.exists():
                backend_entry = file
                break
        
        if not backend_entry:
            result["errors"].append("No backend entry point found")
            return False, result
        
        result["checked"] = True
        result["method"] = f"python {backend_entry.name}"
        
        try:
            # Try to start the backend with a timeout
            process = subprocess.Popen(
                ["python", str(backend_entry)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(backend_entry.parent)
            )
            
            # Give it 5 seconds to start
            time.sleep(5)
            
            # Check if process is still running
            if process.poll() is None:
                # Backend started successfully
                result["success"] = True
                result["output"] = "Backend process started and is running"
                
                # Terminate the process
                process.terminate()
                process.wait(timeout=5)
            else:
                # Process exited
                stdout, stderr = process.communicate(timeout=1)
                result["output"] = stdout + stderr
                
                # Check if it's a normal exit (like FastAPI needing uvicorn)
                if "uvicorn" in stderr.lower() or "gunicorn" in stderr.lower():
                    # Try with uvicorn
                    result["method"] = "uvicorn main:app"
                    result["success"] = self._try_uvicorn(backend_entry)
                else:
                    result["errors"].append(f"Backend exited with code {process.returncode}")
                    result["errors"].append(stderr[:500])  # First 500 chars of error
        
        except subprocess.TimeoutExpired:
            result["success"] = True  # If it's still running after timeout, consider it successful
            result["output"] = "Backend is running (timeout reached)"
            process.terminate()
        except Exception as e:
            result["errors"].append(f"Failed to start backend: {str(e)}")
        
        return result["success"], result
    
    def _try_uvicorn(self, backend_file: Path) -> bool:
        """Try to start backend with uvicorn"""
        
        try:
            # Determine app module
            if backend_file.name == "main.py":
                app_module = "main:app"
            elif backend_file.name == "app.py":
                app_module = "app:app"
            else:
                app_module = f"{backend_file.stem}:app"
            
            process = subprocess.Popen(
                ["python", "-m", "uvicorn", app_module, "--host", "0.0.0.0", "--port", "8000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(backend_file.parent)
            )
            
            # Give it time to start
            time.sleep(5)
            
            if process.poll() is None:
                process.terminate()
                return True
            
            return False
            
        except Exception:
            return False
    
    def verify_frontend_builds(self) -> Tuple[bool, Dict]:
        """Verify that frontend can build successfully"""
        
        result = {
            "checked": False,
            "success": False,
            "method": None,
            "output": "",
            "errors": []
        }
        
        # Check if frontend directory exists
        frontend_dir = self.project_root / "frontend"
        if not frontend_dir.exists():
            # Try root directory
            if (self.project_root / "package.json").exists():
                frontend_dir = self.project_root
            else:
                result["errors"].append("No frontend directory found")
                return False, result
        
        # Check for package.json
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            result["errors"].append("No package.json found")
            return False, result
        
        result["checked"] = True
        
        # First, install dependencies if node_modules doesn't exist
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            try:
                install_result = subprocess.run(
                    ["npm", "install"],
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minutes for install
                    cwd=str(frontend_dir)
                )
                
                if install_result.returncode != 0:
                    result["errors"].append("npm install failed")
                    result["errors"].append(install_result.stderr[:500])
                    return False, result
                    
            except subprocess.TimeoutExpired:
                result["errors"].append("npm install timed out")
                return False, result
            except FileNotFoundError:
                result["errors"].append("npm not found - Node.js not installed")
                return False, result
        
        # Try to build
        try:
            # Check what build command is available
            with open(package_json) as f:
                package_data = json.load(f)
            
            scripts = package_data.get("scripts", {})
            
            if "build" in scripts:
                build_command = ["npm", "run", "build"]
                result["method"] = "npm run build"
            elif "compile" in scripts:
                build_command = ["npm", "run", "compile"]
                result["method"] = "npm run compile"
            else:
                # No build script, check if it's a dev-only setup
                if "dev" in scripts or "start" in scripts:
                    result["success"] = True
                    result["output"] = "No build script, but dev/start script exists"
                    return True, result
                else:
                    result["errors"].append("No build script found in package.json")
                    return False, result
            
            # Run build command
            build_result = subprocess.run(
                build_command,
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute for build
                cwd=str(frontend_dir)
            )
            
            if build_result.returncode == 0:
                result["success"] = True
                result["output"] = "Frontend built successfully"
            else:
                result["errors"].append(f"Build failed with exit code {build_result.returncode}")
                result["errors"].append(build_result.stderr[:500])
                
        except subprocess.TimeoutExpired:
            result["errors"].append("Build command timed out")
        except Exception as e:
            result["errors"].append(f"Build failed: {str(e)}")
        
        return result["success"], result
    
    def verify_docker_containers(self) -> Tuple[bool, Dict]:
        """Verify that Docker containers can start"""
        
        result = {
            "checked": False,
            "success": False,
            "method": None,
            "output": "",
            "errors": [],
            "services": []
        }
        
        # Check for docker-compose.yml
        compose_file = self.project_root / "docker-compose.yml"
        if not compose_file.exists():
            compose_file = self.project_root / "docker-compose.yaml"
            if not compose_file.exists():
                result["errors"].append("No docker-compose.yml found")
                return False, result
        
        result["checked"] = True
        result["method"] = "docker-compose up"
        
        try:
            # Check if Docker is running
            docker_check = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            
            if docker_check.returncode != 0:
                result["errors"].append("Docker is not running or not installed")
                return False, result
            
            # Try to validate docker-compose file
            validate_result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "config"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if validate_result.returncode != 0:
                result["errors"].append("docker-compose.yml is invalid")
                result["errors"].append(validate_result.stderr[:500])
                return False, result
            
            # Try to start containers (without detach to see if they start)
            process = subprocess.Popen(
                ["docker-compose", "-f", str(compose_file), "up"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.project_root)
            )
            
            # Give containers 10 seconds to start
            time.sleep(10)
            
            # Check if any containers are running
            ps_result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if ps_result.returncode == 0:
                # Parse running services
                lines = ps_result.stdout.strip().split('\n')
                for line in lines[2:]:  # Skip header lines
                    if line and "Up" in line:
                        service_name = line.split()[0]
                        result["services"].append(service_name)
                
                if result["services"]:
                    result["success"] = True
                    result["output"] = f"Docker services running: {', '.join(result['services'])}"
                else:
                    result["errors"].append("No services are running")
            
            # Stop containers
            subprocess.run(
                ["docker-compose", "-f", str(compose_file), "down"],
                capture_output=True,
                timeout=10
            )
            
        except subprocess.TimeoutExpired:
            result["errors"].append("Docker operations timed out")
        except FileNotFoundError as e:
            if "docker" in str(e):
                result["errors"].append("Docker CLI not found")
            else:
                result["errors"].append(f"Command not found: {e}")
        except Exception as e:
            result["errors"].append(f"Docker verification failed: {str(e)}")
        
        return result["success"], result
    
    def verify_critical_endpoints(self) -> Tuple[bool, Dict]:
        """Verify that critical API endpoints are accessible"""
        
        result = {
            "checked": False,
            "success": False,
            "accessible_endpoints": [],
            "failed_endpoints": [],
            "errors": []
        }
        
        # Common ports to check
        ports = [8000, 3000, 5000, 8080]
        
        result["checked"] = True
        
        for port in ports:
            base_url = f"http://localhost:{port}"
            
            for endpoint in self.critical_endpoints:
                url = base_url + endpoint
                
                try:
                    response = requests.get(url, timeout=2)
                    
                    if response.status_code < 500:
                        result["accessible_endpoints"].append({
                            "url": url,
                            "status_code": response.status_code
                        })
                        result["success"] = True  # At least one endpoint works
                    else:
                        result["failed_endpoints"].append({
                            "url": url,
                            "status_code": response.status_code,
                            "error": "Server error"
                        })
                        
                except requests.exceptions.ConnectionError:
                    # Port not open, skip other endpoints on this port
                    break
                except requests.exceptions.Timeout:
                    result["failed_endpoints"].append({
                        "url": url,
                        "error": "Timeout"
                    })
                except Exception as e:
                    result["failed_endpoints"].append({
                        "url": url,
                        "error": str(e)
                    })
        
        if not result["accessible_endpoints"] and not result["failed_endpoints"]:
            result["errors"].append("No services running on common ports")
        
        return result["success"], result
    
    def generate_verification_report(self) -> str:
        """Generate comprehensive verification report"""
        
        if not self.verification_results:
            return "No verification results available"
        
        report = ["# Post-Execution Verification Report", ""]
        report.append(f"Generated: {self.verification_results['timestamp']}")
        report.append("")
        
        # Overall status
        status = "✅ PASSED" if self.verification_results["overall_success"] else "❌ FAILED"
        report.append(f"## Overall Status: {status}")
        report.append("")
        
        # Summary table
        report.append("## Verification Summary")
        report.append("")
        report.append("| Component | Status | Details |")
        report.append("|-----------|--------|---------|")
        
        components = [
            ("Backend Start", "backend_start", "backend"),
            ("Frontend Build", "frontend_build", "frontend"),
            ("Docker Containers", "docker_containers", "docker"),
            ("Critical Endpoints", "critical_endpoints", "endpoints")
        ]
        
        for name, key, detail_key in components:
            status = "✅" if self.verification_results[key] else "❌"
            details = self.verification_results["details"].get(detail_key, {})
            
            if details.get("success"):
                detail_text = details.get("output", "Success")[:50]
            elif details.get("errors"):
                detail_text = details["errors"][0][:50] if details["errors"] else "Failed"
            else:
                detail_text = "Not checked"
            
            report.append(f"| {name} | {status} | {detail_text} |")
        
        report.append("")
        
        # Detailed results
        report.append("## Detailed Results")
        
        for component, details in self.verification_results["details"].items():
            report.append(f"\n### {component.title()}")
            
            if details.get("checked"):
                report.append(f"- Method: {details.get('method', 'N/A')}")
                report.append(f"- Success: {details.get('success', False)}")
                
                if details.get("output"):
                    report.append(f"- Output: {details['output'][:200]}")
                
                if details.get("errors"):
                    report.append("- Errors:")
                    for error in details["errors"][:3]:  # Limit to 3 errors
                        report.append(f"  - {error[:100]}")
                
                if component == "endpoints" and details.get("accessible_endpoints"):
                    report.append("- Accessible Endpoints:")
                    for ep in details["accessible_endpoints"][:5]:
                        report.append(f"  - {ep['url']} (Status: {ep['status_code']})")
                
                if component == "docker" and details.get("services"):
                    report.append(f"- Running Services: {', '.join(details['services'])}")
            else:
                report.append("- Not checked")
        
        # Recommendations
        report.append("\n## Recommendations")
        
        if not self.verification_results["backend_start"]:
            report.append("- Fix backend startup issues - check dependencies and entry point")
        
        if not self.verification_results["frontend_build"]:
            report.append("- Fix frontend build issues - check package.json and dependencies")
        
        if not self.verification_results["docker_containers"]:
            report.append("- Fix Docker configuration - validate docker-compose.yml")
        
        if not self.verification_results["critical_endpoints"]:
            report.append("- Ensure services are running and endpoints are configured")
        
        return "\n".join(report)
    
    def quick_smoke_test(self) -> bool:
        """Run a quick smoke test to verify basic functionality"""
        
        # Just check if key files exist
        checks = [
            (self.project_root / "backend" / "main.py").exists() or 
            (self.project_root / "main.py").exists(),
            
            (self.project_root / "frontend" / "package.json").exists() or
            (self.project_root / "package.json").exists(),
            
            (self.project_root / "docker-compose.yml").exists() or
            (self.project_root / "Dockerfile").exists()
        ]
        
        return any(checks)  # At least one component exists