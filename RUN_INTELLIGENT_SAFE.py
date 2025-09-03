#!/usr/bin/env python3
"""
Safe runner for Intelligent Orchestrator - includes error handling and diagnostics
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_environment():
    """Check environment setup"""
    issues = []
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        issues.append("ANTHROPIC_API_KEY not set")
    elif api_key.startswith("test"):
        issues.append("Using test API key - real execution will fail")
    else:
        print("[OK] API key configured")
    
    # Check required modules
    try:
        from lib.agent_runtime import AnthropicAgentRunner, AgentContext, create_standard_tools, ModelType
        print("[OK] Agent runtime imported")
    except ImportError as e:
        issues.append(f"Failed to import agent_runtime: {e}")
    
    try:
        from lib.interceptor import UniversalInterceptor
        print("[OK] Interceptor imported")
    except ImportError as e:
        issues.append(f"Failed to import interceptor: {e}")
    
    try:
        from lib.loop_breaker import LoopBreaker
        print("[OK] Loop breaker imported")
    except ImportError as e:
        issues.append(f"Failed to import loop_breaker: {e}")
    
    try:
        from lib.content_generator import ContentGenerator
        print("[OK] Content generator imported")
    except ImportError as e:
        issues.append(f"Failed to import content_generator: {e}")
    
    return issues

def run_orchestrator():
    """Run the intelligent orchestrator with error handling"""
    print("=" * 80)
    print("INTELLIGENT ORCHESTRATOR - Safe Runner")
    print("=" * 80)
    
    # Check environment
    issues = check_environment()
    if issues:
        print("\n[ERROR] Environment issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before running.")
        return False
    
    try:
        # Import and run orchestrator
        from INTELLIGENT_ORCHESTRATOR import IntelligentOrchestrator
        print("\n[OK] Orchestrator imported successfully")
        
        # Create orchestrator
        print("\nInitializing orchestrator...")
        orchestrator = IntelligentOrchestrator("QuickShop MVP")
        print("[OK] Orchestrator initialized")
        
        # Run the MVP creation
        print("\nStarting QuickShop MVP creation...")
        orchestrator.run_quickshop_mvp()
        
        print("\n[SUCCESS] Orchestrator completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Orchestrator failed: {e}")
        
        # Print detailed error information
        import traceback
        print("\nDetailed error trace:")
        print("-" * 40)
        traceback.print_exc()
        print("-" * 40)
        
        # Provide debugging suggestions
        print("\nDebugging suggestions:")
        if "Tool" in str(e) and "subscriptable" in str(e):
            print("  - Tool object access issue - this has been fixed in the latest version")
            print("  - Ensure INTELLIGENT_ORCHESTRATOR.py uses tool.function not tool['function']")
        elif "API" in str(e):
            print("  - Check your ANTHROPIC_API_KEY is valid")
            print("  - Ensure you have API credits available")
        elif "import" in str(e).lower():
            print("  - Check all required modules are in the lib/ directory")
            print("  - Ensure Python path is set correctly")
        else:
            print("  - Check the orchestrator initialization")
            print("  - Review the error trace above for specific issues")
        
        return False

def main():
    """Main entry point"""
    success = run_orchestrator()
    
    if success:
        print("\n" + "=" * 80)
        print("Execution completed successfully!")
        print("Check the projects/quickshop-mvp-intelligent/ directory for output.")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("Execution failed - see errors above")
        print("=" * 80)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())