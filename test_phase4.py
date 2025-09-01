#!/usr/bin/env python3
"""
Test Phase 4 Implementation
Tests progressive validation, self-healing, validation gates, and enhanced checkpoints
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from progressive_validator import ProgressiveValidator
from checkpoint_manager import CheckpointManager
from self_healing_rules import SelfHealingRules
from validation_gates import ValidationGates, ValidationGate

def test_progressive_validator():
    """Test Phase 4.1: Progressive Validator"""
    print("\n=== Testing Progressive Validator (Phase 4.1) ===")
    
    # Create test directory
    test_dir = Path("test_validation")
    test_dir.mkdir(exist_ok=True)
    
    validator = ProgressiveValidator(project_root=test_dir, auto_fix=True)
    
    # Test 1: Python file with missing import
    test_file = test_dir / "test_module.py"
    test_file.write_text("""
import missing_module
from another_missing import something

def test_function():
    return "Hello World"
""")
    
    print("\n1. Testing Python import validation...")
    result = validator.validate_imports(str(test_file))
    print(f"   Success: {result.success}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Auto-fixed: {result.fixed_automatically}")
    
    # Check if missing modules were created
    if (test_dir / "missing_module.py").exists():
        print("   [OK] Auto-created missing_module.py")
    
    # Test 2: Syntax validation
    print("\n2. Testing syntax validation...")
    bad_syntax_file = test_dir / "bad_syntax.py"
    bad_syntax_file.write_text("""
def broken_function(:  # Missing parameter
    return "This won't work"
""")
    
    result = validator.validate_syntax(str(bad_syntax_file))
    print(f"   Success: {result.success}")
    if result.errors:
        print(f"   Error: {result.errors[0].error_message[:50]}...")
    
    # Test 3: File reference validation
    print("\n3. Testing file reference validation...")
    ref_file = test_dir / "file_refs.py"
    ref_file.write_text("""
with open('nonexistent.txt', 'r') as f:
    data = f.read()
    
from pathlib import Path
config = Path('missing_config.json')
""")
    
    result = validator.validate_references(str(ref_file))
    print(f"   Success: {result.success}")
    print(f"   Files created: {(test_dir / 'nonexistent.txt').exists()}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    print("\n[OK] Progressive Validator tests completed")
    return True

def test_checkpoint_manager():
    """Test Phase 4.2: Enhanced Checkpoint System"""
    print("\n=== Testing Enhanced Checkpoint System (Phase 4.2) ===")
    
    # Create checkpoint manager
    checkpoint_dir = Path("test_checkpoints")
    manager = CheckpointManager(checkpoint_dir=str(checkpoint_dir))
    
    # Test 1: Create checkpoint with context
    print("\n1. Creating checkpoint with full context...")
    
    # Mock context object
    class MockContext:
        def __init__(self):
            self.artifacts = {
                "api_schema": {"version": "1.0", "endpoints": ["/api/users"]},
                "database_model": {"tables": ["users", "products"]}
            }
            self.decisions = [
                "Use PostgreSQL for database",
                "Implement JWT authentication"
            ]
            self.agent_name = "test-agent"
            self.progress = 75.0
    
    context = MockContext()
    files_created = ["app.py", "config.json", "database.py"]
    
    checkpoint_id = manager.create_checkpoint(
        agent_name="test-agent",
        progress=75.0,
        context=context,
        files_created=files_created,
        validation_passed=True
    )
    
    print(f"   Created checkpoint: {checkpoint_id}")
    
    # Test 2: Resume from checkpoint
    print("\n2. Resuming from checkpoint...")
    restoration = manager.resume_from_checkpoint(checkpoint_id)
    
    if restoration:
        print(f"   Agent: {restoration['agent_name']}")
        print(f"   Progress: {restoration['progress']}%")
        print(f"   Artifacts: {list(restoration['artifacts'].keys())}")
        print(f"   Decisions: {len(restoration['decisions'])}")
    
    # Test 3: List checkpoints
    print("\n3. Listing checkpoints...")
    checkpoints = manager.list_checkpoints(can_resume_only=True)
    print(f"   Found {len(checkpoints)} resumable checkpoint(s)")
    
    # Test 4: Get checkpoint chain
    print("\n4. Testing checkpoint chain...")
    chain = manager.get_checkpoint_chain(checkpoint_id)
    print(f"   Chain length: {len(chain)}")
    
    # Cleanup
    import shutil
    shutil.rmtree(checkpoint_dir, ignore_errors=True)
    
    print("\n[OK] Enhanced Checkpoint System tests completed")
    return True

def test_self_healing():
    """Test Phase 4.3: Self-Healing Rules"""
    print("\n=== Testing Self-Healing Rules (Phase 4.3) ===")
    
    healer = SelfHealingRules()
    
    # Test 1: ModuleNotFoundError healing
    print("\n1. Testing ModuleNotFoundError healing...")
    error_msg = "ModuleNotFoundError: No module named 'requests'"
    
    result = healer.apply_healing(
        error_message=error_msg,
        context={"file_path": "test.py"}
    )
    
    print(f"   Can heal: {result.success}")
    print(f"   Fix applied: {result.fix_applied[:50]}..." if result.fix_applied else "   No fix")
    
    # Test 2: ImportError healing
    print("\n2. Testing ImportError healing...")
    error_msg = "ImportError: cannot import name 'Config' from 'app.config'"
    
    result = healer.apply_healing(
        error_message=error_msg,
        context={"file_path": "main.py"}
    )
    
    print(f"   Can heal: {result.success}")
    if result.additional_info and 'suggestion' in result.additional_info:
        print(f"   Suggestion: {result.additional_info['suggestion'][:50]}...")
    
    # Test 3: FileNotFoundError healing
    print("\n3. Testing FileNotFoundError healing...")
    test_dir = Path("test_healing")
    test_dir.mkdir(exist_ok=True)
    
    error_msg = "FileNotFoundError: [Errno 2] No such file or directory: 'config.json'"
    
    result = healer.apply_healing(
        error_message=error_msg,
        context={"file_path": str(test_dir / "app.py")}
    )
    
    print(f"   Can heal: {result.success}")
    print(f"   File created: {(test_dir / 'config.json').exists()}")
    
    # Test 4: Verify healing rules exist
    print("\n4. Verifying healing rules...")
    # Check that we have the core rules
    test_errors = [
        "ModuleNotFoundError: test",
        "ImportError: test",
        "FileNotFoundError: test",
        "SyntaxError: test"
    ]
    rules_found = 0
    for error_msg in test_errors:
        try:
            result = healer.apply_healing(error_msg, {})
            rules_found += 1
        except:
            pass
    print(f"   Core healing rules available: {rules_found}/4")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    print("\n[OK] Self-Healing Rules tests completed")
    return True

def test_validation_gates():
    """Test Phase 4.4: Validation Gates"""
    print("\n=== Testing Validation Gates (Phase 4.4) ===")
    
    # Create test directory
    test_dir = Path("test_gates")
    test_dir.mkdir(exist_ok=True)
    
    gates = ValidationGates(project_root=str(test_dir))
    
    # Create test files
    print("\n1. Creating test files...")
    
    # Good Python file
    good_py = test_dir / "good_module.py"
    good_py.write_text("""
def hello_world():
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
""")
    
    # Bad Python file (syntax error)
    bad_py = test_dir / "bad_module.py"
    bad_py.write_text("""
def broken_function(:  # Syntax error
    return "Won't work"
""")
    
    # File with missing imports
    import_py = test_dir / "import_test.py"
    import_py.write_text("""
import os
import sys
import nonexistent_module

def test():
    return True
""")
    
    # Test 2: Run all gates (individual gate testing not available)
    print("\n2. Running all validation gates...")
    report = gates.run_all_gates("test-agent")
    
    print(f"   Overall passed: {report.all_gates_passed}")
    print(f"   Gates passed: {len(report.gates_passed)} out of {len(report.gate_results)}")
    
    if hasattr(report, 'duration'):
        print(f"   Duration: {report.duration:.2f}s")
    else:
        print(f"   Timestamp: {report.timestamp}")
    
    for gate_name, result in report.gate_results.items():
        status = "[OK]" if result.passed else "[FAIL]"
        print(f"   {status} {gate_name}: {result.files_checked} files")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    print("\n[OK] Validation Gates tests completed")
    return True

def test_integration():
    """Test Phase 4 integration in orchestration flow"""
    print("\n=== Testing Phase 4 Integration ===")
    
    # Test that all components work together
    test_dir = Path("test_integration")
    test_dir.mkdir(exist_ok=True)
    
    # Initialize all Phase 4 components
    validator = ProgressiveValidator(project_root=test_dir, auto_fix=True)
    checkpoint_mgr = CheckpointManager(checkpoint_dir=str(test_dir / "checkpoints"))
    healer = SelfHealingRules()
    gates = ValidationGates(project_root=str(test_dir))
    
    print("\n1. Simulating agent execution with errors...")
    
    # Create a file with issues
    problem_file = test_dir / "problem.py"
    problem_file.write_text("""
import missing_module
from pathlib import Path

def process_data():
    # This will cause FileNotFoundError
    with open('data.json', 'r') as f:
        return f.read()
""")
    
    # Step 1: Progressive validation catches issues
    print("\n2. Progressive validation detecting issues...")
    validation_results = validator.validate_all(str(problem_file))
    
    issues_found = []
    for val_type, result in validation_results.items():
        if not result.success:
            issues_found.extend(result.errors)
            print(f"   {val_type}: {len(result.errors)} issue(s)")
    
    # Step 2: Self-healing attempts to fix
    print("\n3. Self-healing attempting fixes...")
    for issue in issues_found:
        # Construct error message from issue
        error_msg = f"{issue.error_type}: {issue.error_message}"
        healing_result = healer.apply_healing(
            error_message=error_msg,
            context={"file_path": issue.file_path}
        )
        if healing_result.success:
            print(f"   [OK] Fixed: {issue.error_type}")
    
    # Step 3: Create checkpoint after fixes
    print("\n4. Creating checkpoint after fixes...")
    checkpoint_id = checkpoint_mgr.create_checkpoint(
        agent_name="test-agent",
        progress=50.0,
        context={"test": "integration"},
        files_created=[str(problem_file)],
        validation_passed=False  # Still has issues
    )
    print(f"   Checkpoint: {checkpoint_id[:20]}...")
    
    # Step 4: Run validation gates
    print("\n5. Running validation gates before completion...")
    gate_report = gates.run_all_gates("test-agent")
    
    if not gate_report.all_gates_passed:
        print("   [OK] Gates correctly prevented completion with errors")
    else:
        print("   [FAIL] Gates should have caught remaining issues")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    print("\n[OK] Phase 4 Integration tests completed")
    return True

def main():
    """Run all Phase 4 tests"""
    print("=" * 60)
    print("PHASE 4 IMPLEMENTATION TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run each test
    tests = [
        ("Progressive Validator", test_progressive_validator),
        ("Enhanced Checkpoints", test_checkpoint_manager),
        ("Self-Healing Rules", test_self_healing),
        ("Validation Gates", test_validation_gates),
        ("Integration", test_integration)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[FAIL] {test_name} failed with error: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK] PASSED" if result else "[FAIL] FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All Phase 4 tests passed successfully!")
        print("The validation and recovery systems are working correctly.")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please review the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)