#!/usr/bin/env python3
"""
Test script for the enhanced frontend-specialist agent
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sfa.sfa_frontend_specialist import FrontendSpecialist, FrontendConfig

def test_frontend_specialist():
    """Test the frontend specialist with a sample configuration"""
    
    print("Testing Enhanced Frontend Specialist...")
    print("=" * 50)
    
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "test_frontend"
        
        # Create test configuration
        config = FrontendConfig(
            project_name="Task Manager",
            api_base_url="http://localhost:8000",
            auth_enabled=True,
            resources=[
                {
                    "name": "Task",
                    "plural": "Tasks",
                    "fields": [
                        {"name": "title", "type": "string", "required": True},
                        {"name": "description", "type": "string", "required": False},
                        {"name": "priority", "type": "string", "required": True},
                        {"name": "status", "type": "string", "required": True},
                        {"name": "due_date", "type": "date", "required": False},
                        {"name": "completed", "type": "boolean", "required": False}
                    ]
                },
                {
                    "name": "Project",
                    "plural": "Projects",
                    "fields": [
                        {"name": "name", "type": "string", "required": True},
                        {"name": "description", "type": "string", "required": False},
                        {"name": "start_date", "type": "date", "required": True},
                        {"name": "end_date", "type": "date", "required": False}
                    ]
                }
            ]
        )
        
        # Initialize specialist
        specialist = FrontendSpecialist()
        
        # Test creation
        try:
            success = specialist.create_react_app(config, str(output_dir))
            
            if success:
                print("✅ React app created successfully")
                
                # Verify key files exist
                expected_files = [
                    "package.json",
                    "vite.config.ts",
                    "tsconfig.json",
                    "tailwind.config.js",
                    "src/App.tsx",
                    "src/main.tsx",
                    "src/index.css",
                    "src/api/client.ts",
                    "src/api/auth.ts",
                    "src/api/task.ts",
                    "src/api/project.ts",
                    "src/stores/authStore.ts",
                    "src/stores/appStore.ts",
                    "src/features/auth/LoginForm.tsx",
                    "src/features/auth/RegisterForm.tsx",
                    "src/features/task/TaskList.tsx",
                    "src/features/task/TaskForm.tsx",
                    "src/features/task/TaskDetail.tsx",
                    "src/features/project/ProjectList.tsx",
                    "src/features/project/ProjectForm.tsx",
                    "src/features/project/ProjectDetail.tsx",
                    "src/components/layout/Layout.tsx",
                    "src/components/auth/ProtectedRoute.tsx",
                    "src/features/dashboard/Dashboard.tsx"
                ]
                
                missing_files = []
                for file_path in expected_files:
                    full_path = output_dir / file_path
                    if not full_path.exists():
                        missing_files.append(file_path)
                    else:
                        print(f"  ✓ {file_path}")
                
                if missing_files:
                    print("\n❌ Missing files:")
                    for file_path in missing_files:
                        print(f"  ✗ {file_path}")
                    return False
                
                # Verify package.json structure
                with open(output_dir / "package.json", "r") as f:
                    package = json.load(f)
                    
                required_deps = ["react", "react-dom", "axios", "zustand", "@tanstack/react-query"]
                missing_deps = []
                
                for dep in required_deps:
                    if dep not in package.get("dependencies", {}):
                        missing_deps.append(dep)
                
                if missing_deps:
                    print(f"\n⚠️ Missing dependencies: {', '.join(missing_deps)}")
                else:
                    print("\n✅ All required dependencies present")
                
                # Check TypeScript configuration
                with open(output_dir / "tsconfig.json", "r") as f:
                    tsconfig = json.load(f)
                    if tsconfig.get("compilerOptions", {}).get("strict"):
                        print("✅ TypeScript strict mode enabled")
                    else:
                        print("⚠️ TypeScript strict mode not enabled")
                
                print("\n" + "=" * 50)
                print("Test Summary:")
                print(f"  Total files checked: {len(expected_files)}")
                print(f"  Files created: {len(expected_files) - len(missing_files)}")
                print(f"  Missing files: {len(missing_files)}")
                print(f"  Success: {'Yes' if not missing_files else 'No'}")
                
                return not missing_files
                
            else:
                print("❌ Failed to create React app")
                return False
                
        except Exception as e:
            print(f"❌ Error during test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_cli_interface():
    """Test the CLI interface"""
    print("\n\nTesting CLI Interface...")
    print("=" * 50)
    
    # Test help command
    import subprocess
    result = subprocess.run(
        [sys.executable, "sfa/sfa_frontend_specialist.py", "--help"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ CLI help command works")
        print("\nAvailable options:")
        for line in result.stdout.split("\n"):
            if line.strip().startswith("--"):
                print(f"  {line.strip()}")
    else:
        print("❌ CLI help command failed")
        return False
    
    return True

if __name__ == "__main__":
    print("Enhanced Frontend Specialist Test Suite")
    print("=" * 50)
    
    # Run tests
    test_results = []
    
    # Test 1: Frontend creation
    print("\nTest 1: Frontend Creation")
    test_results.append(("Frontend Creation", test_frontend_specialist()))
    
    # Test 2: CLI interface
    print("\nTest 2: CLI Interface")
    test_results.append(("CLI Interface", test_cli_interface()))
    
    # Summary
    print("\n\n" + "=" * 50)
    print("FINAL TEST RESULTS")
    print("=" * 50)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in test_results)
    
    if all_passed:
        print("\n🎉 All tests passed! Frontend specialist is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please review the implementation.")
    
    sys.exit(0 if all_passed else 1)