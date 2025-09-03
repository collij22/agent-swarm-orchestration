#!/usr/bin/env python
"""Diagnose the I/O issue"""

import sys
import os

print(f"Python version: {sys.version}")
print(f"Executable: {sys.executable}")
print(f"Working dir: {os.getcwd()}")
print(f"stdout: {sys.stdout}")
print(f"stderr: {sys.stderr}")

# Test basic operations
print("\n1. Testing basic print...")
try:
    print("Basic print works!")
except Exception as e:
    print(f"Basic print failed: {e}")

# Test imports
print("\n2. Testing imports...")
try:
    from lib.agent_logger import create_new_session, SummaryLevel
    print("agent_logger imported OK")
except Exception as e:
    print(f"agent_logger import failed: {e}")
    import traceback
    traceback.print_exc()

# Test session creation
print("\n3. Testing session creation...")
try:
    # This is where it's failing
    import uuid
    from lib.agent_logger import create_new_session, SummaryLevel
    session_id = str(uuid.uuid4())
    logger = create_new_session(session_id, True, SummaryLevel.CONCISE)
    print(f"Session created: {session_id}")
except Exception as e:
    print(f"Session creation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Testing Rich console directly...")
try:
    from rich.console import Console
    console = Console()
    console.print("Rich console works!")
except Exception as e:
    print(f"Rich console failed: {e}")

print("\nDiagnosis complete.")