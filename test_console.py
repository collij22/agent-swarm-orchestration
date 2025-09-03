import sys
import os

print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Encoding: {sys.getdefaultencoding()}")
print(f"PYTHONIOENCODING: {os.environ.get('PYTHONIOENCODING', 'not set')}")

# Test if we're in a problematic environment
print(f"\nstdout.isatty(): {sys.stdout.isatty()}")
print(f"stderr.isatty(): {sys.stderr.isatty()}")
print(f"stdout encoding: {sys.stdout.encoding}")
print(f"stderr encoding: {sys.stderr.encoding}")

# Test Rich console
try:
    from rich.console import Console
    console = Console()
    print("\nRich Console created successfully")
    console.print("Rich print works!")
except Exception as e:
    print(f"\nRich Console failed: {e}")

# Test agent_logger
try:
    from lib.agent_logger import create_new_session, SummaryLevel
    logger = create_new_session("test", True, SummaryLevel.CONCISE)
    print("\nLogger created successfully")
except Exception as e:
    print(f"\nLogger creation failed: {e}")
    import traceback
    traceback.print_exc()