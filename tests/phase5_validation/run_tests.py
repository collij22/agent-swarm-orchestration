#!/usr/bin/env python3
"""
Phase 5 Validation Test Suite
Comprehensive testing of the upgraded agent swarm system
Tests all 5 phases of improvements with medium complexity scenarios

Usage:
    # Mock Mode (default - no API costs, simulated responses):
    python run_tests.py --test ecommerce
    python run_tests.py --all
    
    # API Mode (real Claude API - requires ANTHROPIC_API_KEY):
    set ANTHROPIC_API_KEY=your-key-here  # Windows
    export ANTHROPIC_API_KEY=your-key-here  # Linux/Mac
    python run_tests.py --test ecommerce --api-mode
    python run_tests.py --all --api-mode
    
Mock Mode vs API Mode:
    - Mock Mode: Fast (0.5-1s), no costs, simulated agent responses, good for testing
    - API Mode: Slower (30-300s), uses API credits, real Claude intelligence, production validation
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configuration
TEST_DIR = Path(__file__).parent
REQUIREMENTS_DIR = TEST_DIR / "requirements"
RESULTS_DIR = TEST_DIR / "results"
PROJECT_ROOT = Path(__file__).parent.parent.parent
ORCHESTRATE_SCRIPT = PROJECT_ROOT / "orchestrate_enhanced.py"
SESSION_DIR = PROJECT_ROOT / "sessions"

# Test scenarios
TEST_SCENARIOS = {
    "simple": {
        "name": "Simple API Test",
        "requirements": "simple_api_test.yaml",
        "project_type": "api",
        "agents_expected": ["rapid-builder", "api-integrator", "quality-guardian"],
        "complexity": "simple",
        "estimated_time": 60
    },
    "ecommerce": {
        "name": "E-Commerce Platform MVP",
        "requirements": "ecommerce_platform.yaml",
        "project_type": "full_stack_api",
        "agents_expected": ["requirements-analyst", "project-architect", "database-expert", 
                           "rapid-builder", "frontend-specialist", "api-integrator", 
                           "quality-guardian", "devops-engineer"],
        "complexity": "medium",
        "estimated_time": 180
    },
    "analytics": {
        "name": "Real-Time Analytics Dashboard",
        "requirements": "analytics_dashboard.yaml",
        "project_type": "ai_solution",
        "agents_expected": ["requirements-analyst", "project-architect", "ai-specialist",
                           "rapid-builder", "frontend-specialist", "performance-optimizer",
                           "quality-guardian"],
        "complexity": "medium",
        "estimated_time": 150
    },
    "microservices": {
        "name": "Microservices Migration",
        "requirements": "microservices_migration.yaml",
        "project_type": "api_service",
        "agents_expected": ["requirements-analyst", "code-migrator", "project-architect",
                           "rapid-builder", "api-integrator", "database-expert",
                           "devops-engineer", "quality-guardian"],
        "complexity": "medium",
        "estimated_time": 200
    },
    "mobile": {
        "name": "Mobile-First Social App",
        "requirements": "social_mobile_app.yaml",
        "project_type": "full_stack_api",
        "agents_expected": ["requirements-analyst", "project-architect", "frontend-specialist",
                           "rapid-builder", "api-integrator", "performance-optimizer",
                           "quality-guardian"],
        "complexity": "medium",
        "estimated_time": 160
    },
    "ai_cms": {
        "name": "AI-Powered Content Management",
        "requirements": "ai_content_cms.yaml",
        "project_type": "ai_solution",
        "agents_expected": ["requirements-analyst", "project-architect", "ai-specialist",
                           "rapid-builder", "database-expert", "frontend-specialist",
                           "api-integrator", "quality-guardian"],
        "complexity": "medium",
        "estimated_time": 170
    }
}

class TestRunner:
    """Manages test execution and result collection"""
    
    def __init__(self, verbose: bool = False, parallel: bool = False, api_mode: bool = False):
        self.verbose = verbose
        self.parallel = parallel
        self.api_mode = api_mode  # If True, use real API instead of mock
        self.results = {}
        self.start_time = None
        self.end_time = None
        
        # Create results directory
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def run_test(self, test_key: str) -> Dict:
        """Execute a single test scenario"""
        test_config = TEST_SCENARIOS[test_key]
        print(f"\n{'='*60}")
        print(f"Running Test: {test_config['name']}")
        print(f"Project Type: {test_config['project_type']}")
        print(f"Complexity: {test_config['complexity']}")
        print(f"Mode: {'API (Real Claude)' if self.api_mode else 'Mock (Simulated)'}")
        print(f"{'='*60}")
        
        # Set mock mode environment variable based on api_mode flag
        if not self.api_mode:
            os.environ['MOCK_MODE'] = 'true'
        else:
            # Ensure mock mode is disabled for API mode
            if 'MOCK_MODE' in os.environ:
                del os.environ['MOCK_MODE']
            
            # Check for API key in API mode
            if not os.environ.get('ANTHROPIC_API_KEY'):
                print("WARNING: No ANTHROPIC_API_KEY found. API mode requires a valid API key.")
                print("Set it with: set ANTHROPIC_API_KEY=your-key-here (Windows)")
                print("           or: export ANTHROPIC_API_KEY=your-key-here (Linux/Mac)")
        
        # Prepare command
        requirements_file = REQUIREMENTS_DIR / test_config["requirements"]
        
        cmd = [
            sys.executable,
            str(ORCHESTRATE_SCRIPT),
            "--project-type", test_config["project_type"],
            "--requirements", str(requirements_file),
            "--human-log",  # Enable human-readable logs
            "--summary-level", "detailed",  # Detailed summaries
            "--verbose"  # Verbose output for debugging
        ]
        
        # Add test-specific output directory
        output_dir = RESULTS_DIR / f"test_{test_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--output-dir", str(output_dir)])
        
        # Execute test
        start_time = time.time()
        result = {
            "test_key": test_key,
            "name": test_config["name"],
            "start_time": datetime.now().isoformat(),
            "output_dir": str(output_dir),
            "command": " ".join(cmd)
        }
        
        try:
            if self.verbose:
                print(f"Executing: {' '.join(cmd)}")
            
            # Run orchestrator with explicit environment
            # Pass the current environment to subprocess
            env = os.environ.copy()
            
            # Skip API validation for tests to prevent hanging
            if self.api_mode:
                # In API mode, we want to validate but with a shorter timeout
                env['SKIP_API_VALIDATION'] = 'false'
            else:
                # In mock mode, no validation needed
                env['SKIP_API_VALIDATION'] = 'true'
            
            # Use longer timeout for API mode since real Claude API calls take time
            if self.api_mode:
                # API mode needs MUCH more time - ecommerce test runs 7-8 agents
                # Each agent can take 5-10 minutes with real Claude API calls
                # Total time needed: 7 agents * 8 minutes = ~45-60 minutes
                # Use a very generous timeout to handle all agents
                timeout_seconds = 2700  # 45 minutes for API mode
                print(f"[INFO] Using {timeout_seconds}s timeout ({timeout_seconds/60:.0f} minutes) for API mode")
            else:
                timeout_seconds = test_config.get("estimated_time", 300)
            
            # Use Popen for better process control
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env  # Pass environment explicitly
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout_seconds)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                # Try to terminate gracefully first
                process.terminate()
                try:
                    stdout, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    process.kill()
                    stdout, stderr = process.communicate()
                raise subprocess.TimeoutExpired(cmd, timeout_seconds)
            
            execution_time = time.time() - start_time
            
            # Parse results
            result.update({
                "success": return_code == 0,
                "execution_time": execution_time,
                "stdout": stdout if self.verbose else stdout[-1000:] if stdout else "",
                "stderr": stderr,
                "return_code": return_code
            })
            
            # Extract metrics from output
            result["metrics"] = self._extract_metrics(stdout)
            
            # Find session files
            result["session_files"] = self._find_session_files(start_time)
            
            # Calculate quality score
            result["quality_score"] = self._calculate_quality_score(result)
            
            print(f"[OK] Test completed in {execution_time:.2f}s - Quality Score: {result['quality_score']:.1f}%")
            
        except subprocess.TimeoutExpired:
            # Use the actual timeout value, not the estimated time
            actual_timeout = timeout_seconds
            result.update({
                "success": False,
                "execution_time": actual_timeout,
                "error": "Test timeout exceeded",
                "quality_score": 0
            })
            print(f"[FAIL] Test timeout after {actual_timeout}s")
            
        except Exception as e:
            result.update({
                "success": False,
                "execution_time": time.time() - start_time,
                "error": str(e),
                "quality_score": 0
            })
            print(f"[FAIL] Test failed with error: {str(e)}")
        
        return result
    
    def _extract_metrics(self, output: str) -> Dict:
        """Extract metrics from orchestrator output"""
        metrics = {
            "agents_executed": [],
            "files_created": 0,
            "requirements_completed": 0,
            "total_requirements": 0,
            "errors": 0,
            "warnings": 0
        }
        
        lines = output.split('\n')
        for line in lines:
            # Extract agent executions
            if "Agent completed:" in line:
                agent_name = line.split("Agent completed:")[1].split()[0].strip()
                metrics["agents_executed"].append(agent_name)
            
            # Extract file counts
            elif "Files created:" in line:
                try:
                    metrics["files_created"] = int(line.split("Files created:")[1].strip())
                except:
                    pass
            
            # Extract requirement completion
            elif "Requirements completed:" in line:
                try:
                    parts = line.split("Requirements completed:")[1].strip().split("/")
                    metrics["requirements_completed"] = int(parts[0])
                    metrics["total_requirements"] = int(parts[1])
                except:
                    pass
            
            # Count errors and warnings
            elif "ERROR" in line:
                metrics["errors"] += 1
            elif "WARNING" in line:
                metrics["warnings"] += 1
        
        return metrics
    
    def _find_session_files(self, start_time: float) -> Dict:
        """Find session files created during test"""
        session_files = {
            "json": None,
            "human_readable": None
        }
        
        try:
            # Look for files created after test start
            for file in SESSION_DIR.glob("session_*.json"):
                if file.stat().st_mtime >= start_time:
                    session_files["json"] = str(file)
                    # Look for corresponding human-readable log
                    human_file = file.with_suffix("").parent / f"{file.stem}_human.md"
                    if human_file.exists():
                        session_files["human_readable"] = str(human_file)
                    break
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not find session files: {e}")
        
        return session_files
    
    def _calculate_quality_score(self, result: Dict) -> float:
        """Calculate quality score based on test results"""
        if not result.get("success"):
            return 0.0
        
        score = 0.0
        metrics = result.get("metrics", {})
        
        # Success bonus (30 points)
        score += 30
        
        # Agent execution (20 points)
        agents_executed = len(metrics.get("agents_executed", []))
        expected_agents = len(TEST_SCENARIOS[result["test_key"]].get("agents_expected", []))
        if expected_agents > 0:
            score += min(20, (agents_executed / expected_agents) * 20)
        
        # Files created (15 points)
        files_created = metrics.get("files_created", 0)
        score += min(15, files_created * 1.5)
        
        # Requirement completion (25 points)
        total_reqs = metrics.get("total_requirements", 0)
        completed_reqs = metrics.get("requirements_completed", 0)
        if total_reqs > 0:
            score += (completed_reqs / total_reqs) * 25
        
        # Error penalty (up to -10 points)
        errors = metrics.get("errors", 0)
        score -= min(10, errors * 2)
        
        # Warning penalty (up to -5 points)
        warnings = metrics.get("warnings", 0)
        score -= min(5, warnings * 0.5)
        
        # Time bonus (10 points if under estimated time)
        estimated_time = TEST_SCENARIOS[result["test_key"]].get("estimated_time", 300)
        if result.get("execution_time", 0) < estimated_time:
            score += 10
        
        return max(0, min(100, score))
    
    def run_all_tests(self, test_keys: Optional[List[str]] = None):
        """Run all or specified tests"""
        self.start_time = time.time()
        
        if test_keys is None:
            test_keys = list(TEST_SCENARIOS.keys())
        
        print(f"\n{'-'*60}")
        print(f"Phase 5 Validation Test Suite")
        print(f"Running {len(test_keys)} tests in {'parallel' if self.parallel else 'sequential'} mode")
        print(f"Execution Mode: {'API (Real Claude)' if self.api_mode else 'Mock (Simulated)'}")
        if self.api_mode:
            print(f"API Key: {'Found' if os.environ.get('ANTHROPIC_API_KEY') else 'NOT FOUND - Tests will fail!'}")
        print(f"Human Logs: Enabled (detailed)")
        print(f"{'-'*60}")
        
        if self.parallel:
            # Run tests in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(self.run_test, key): key for key in test_keys}
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        self.results[key] = future.result()
                    except Exception as e:
                        print(f"Error running test {key}: {e}")
                        self.results[key] = {
                            "test_key": key,
                            "success": False,
                            "error": str(e),
                            "quality_score": 0
                        }
        else:
            # Run tests sequentially
            for key in test_keys:
                self.results[key] = self.run_test(key)
        
        self.end_time = time.time()
        self._print_summary()
        self._save_results()
    
    def _print_summary(self):
        """Print test execution summary"""
        print(f"\n{'='*60}")
        print("TEST EXECUTION SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results.values() if r.get("success"))
        total_time = self.end_time - self.start_time
        avg_quality = sum(r.get("quality_score", 0) for r in self.results.values()) / max(1, total_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}/{total_tests} ({successful_tests/max(1,total_tests)*100:.1f}%)")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Average Quality Score: {avg_quality:.1f}%")
        
        print(f"\n{'-'*60}")
        print("Individual Test Results:")
        print(f"{'-'*60}")
        
        for key, result in self.results.items():
            status = "[OK]" if result.get("success") else "[FAIL]"
            quality = result.get("quality_score", 0)
            time_taken = result.get("execution_time", 0)
            print(f"{status} {result.get('name', key):<30} Quality: {quality:5.1f}% Time: {time_taken:6.2f}s")
            
            if self.verbose and not result.get("success"):
                print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print(f"\n{'-'*60}")
        print("Agent Utilization:")
        print(f"{'-'*60}")
        
        agent_counts = {}
        for result in self.results.values():
            for agent in result.get("metrics", {}).get("agents_executed", []):
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        for agent, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {agent:<25} executed {count} times")
        
        # Print session file locations
        print(f"\n{'-'*60}")
        print("Session Logs:")
        print(f"{'-'*60}")
        
        for key, result in self.results.items():
            session_files = result.get("session_files", {})
            if session_files.get("human_readable"):
                print(f"{result.get('name', key)}:")
                print(f"  Human Log: {session_files['human_readable']}")
    
    def _save_results(self):
        """Save test results to JSON file"""
        results_file = RESULTS_DIR / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                "test_suite": "Phase 5 Validation",
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.end_time).isoformat(),
                "total_duration": self.end_time - self.start_time,
                "results": self.results
            }, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Phase 5 Validation Test Suite",
        epilog="""
Examples:
  # Run in mock mode (default, no API costs):
  python run_tests.py --test ecommerce
  
  # Run in API mode (uses real Claude API, requires ANTHROPIC_API_KEY):
  python run_tests.py --test ecommerce --api-mode
  
  # Run all tests in API mode:
  python run_tests.py --all --api-mode
        """
    )
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--test", nargs="+", choices=list(TEST_SCENARIOS.keys()),
                       help="Run specific tests")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--api-mode", action="store_true", 
                       help="Use real Claude API instead of mock (requires ANTHROPIC_API_KEY)")
    parser.add_argument("--list", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable Tests:")
        print("-" * 40)
        for key, config in TEST_SCENARIOS.items():
            print(f"{key:<15} - {config['name']}")
        return
    
    # Determine which tests to run
    if args.all:
        test_keys = None
    elif args.test:
        test_keys = args.test
    else:
        print("Please specify --all or --test <test_names>")
        print("Use --list to see available tests")
        return
    
    # Check for API key if in API mode (warn but don't block - let agent_runtime handle validation)
    if args.api_mode and not os.environ.get('ANTHROPIC_API_KEY'):
        print("\nWARNING: API mode selected but ANTHROPIC_API_KEY not found.")
        print("The test will likely fail. To set your API key:")
        print("  Windows:   set ANTHROPIC_API_KEY=your-key-here")
        print("  Linux/Mac: export ANTHROPIC_API_KEY=your-key-here")
        print("\nContinuing anyway to test error handling...")
        print("-" * 60)
    
    # Run tests
    runner = TestRunner(verbose=args.verbose, parallel=args.parallel, api_mode=args.api_mode)
    runner.run_all_tests(test_keys)

if __name__ == "__main__":
    main()