#!/usr/bin/env python3
"""
Simple test to see if we can import and run the orchestrator
"""

import sys
import os

# Setup
os.environ['PYTHONIOENCODING'] = 'utf-8'
print("Testing orchestrator import...")

try:
    # Test import
    print("1. Importing orchestrate_enhanced...")
    import orchestrate_enhanced
    print("   [OK] Import successful")
    
    # Test orchestration_enhanced
    print("2. Importing lib.orchestration_enhanced...")
    from lib.orchestration_enhanced import EnhancedOrchestrator
    print("   [OK] Import successful")
    
    # Test agent_runtime
    print("3. Importing lib.agent_runtime...")
    from lib.agent_runtime import AgentContext, ModelType
    print("   [OK] Import successful")
    
    # Test creating context
    print("4. Creating AgentContext...")
    context = AgentContext(
        project_requirements={"name": "test"}
    )
    print("   [OK] Context created")
    
    print()
    print("=" * 60)
    print("[SUCCESS] All imports work!")
    print("=" * 60)
    print()
    print("The system is ready to run.")
    print("The issue is likely with Rich console I/O.")
    print()
    print("Solutions:")
    print("1. Run without Rich console (disable it)")
    print("2. Use mock mode to bypass API calls")
    print("3. Run in a different terminal")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()