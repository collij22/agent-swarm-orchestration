#!/usr/bin/env python3
"""Test the Intelligent Orchestrator setup"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set a mock API key if not set
if not os.getenv("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = "test-key-123"

def test_basic_setup():
    """Test basic orchestrator setup"""
    print("Testing Intelligent Orchestrator setup...")
    
    try:
        from INTELLIGENT_ORCHESTRATOR import IntelligentOrchestrator
        print("[OK] Import successful")
        
        # Try to create orchestrator
        orchestrator = IntelligentOrchestrator("Test Project")
        print("[OK] Orchestrator created")
        
        # Check components
        assert orchestrator.interceptor is not None
        print("[OK] Interceptor initialized")
        
        assert orchestrator.loop_breaker is not None
        print("[OK] Loop breaker initialized")
        
        assert orchestrator.content_generator is not None
        print("[OK] Content generator initialized")
        
        print("\n[SUCCESS] All basic components working!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_setup()
    exit(0 if success else 1)