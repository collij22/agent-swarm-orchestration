#!/usr/bin/env python3
"""
Safe Orchestrator - Prevents response truncation issues
Enforces single file operations and comprehensive content generation
"""

import os
import sys
import subprocess
from pathlib import Path

# Set encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Add safety flags
os.environ['SINGLE_FILE_MODE'] = '1'  # Enforce single file operations
os.environ['TRUNCATION_DETECTION'] = '1'  # Enable truncation detection
os.environ['COMPREHENSIVE_PLACEHOLDERS'] = '1'  # Generate full placeholders

def main():
    """Run orchestration with safety measures"""
    
    print("=" * 60)
    print("SAFE ORCHESTRATION WITH TRUNCATION PREVENTION")
    print("=" * 60)
    print()
    print("Safety features enabled:")
    print("[OK] Single file mode - one file per response")
    print("[OK] Truncation detection - monitors for incomplete content")
    print("[OK] Comprehensive placeholders - full content generation")
    print("[OK] Retry loop prevention - max 3 attempts per file")
    print()
    
    cmd = [
        sys.executable,
        "orchestrate_enhanced.py",
        "--project-type", "full_stack_api",
        "--requirements", "projects/quickshop-mvp-test/requirements.yaml",
        "--output-dir", "projects/quickshop-mvp-test6",
        "--progress",
        "--summary-level", "concise",
        "--max-parallel", "2",
        "--human-log"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode == 0:
        print()
        print("=" * 60)
        print("[SUCCESS] ORCHESTRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("[FAILED] ORCHESTRATION FAILED - Check logs above")
        print("=" * 60)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
