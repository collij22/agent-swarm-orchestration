import sys
print(f"Python version: {sys.version}")
print(f"stdout: {sys.stdout}")
print(f"stdout.closed: {sys.stdout.closed if hasattr(sys.stdout, 'closed') else 'N/A'}")
print(f"stderr: {sys.stderr}")
print(f"stderr.closed: {sys.stderr.closed if hasattr(sys.stderr, 'closed') else 'N/A'}")
print("Test print works!")