#!/usr/bin/env python
"""
RUN WITH MONITOR - Runs orchestrator and shows output in real-time
"""

import subprocess
import threading
import time
import os
import sys

# Clear old log
if os.path.exists('orchestrate_bypass.log'):
    os.remove('orchestrate_bypass.log')

print("=" * 70)
print("QUICKSHOP MVP - AGENT SWARM ORCHESTRATION")
print("=" * 70)
print("\nStarting 15-agent swarm with MCP integrations...")
print("\n" + "=" * 70)

# Start the orchestrator in a subprocess
process = subprocess.Popen(
    [sys.executable, 'fix_specific_tools.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    env={**os.environ, 'PYTHONUNBUFFERED': '1', 'PYTHONIOENCODING': 'utf-8'}
)

# Monitor the log file in a separate thread
def monitor_log():
    last_pos = 0
    while process.poll() is None:  # While process is running
        try:
            if os.path.exists('orchestrate_bypass.log'):
                with open('orchestrate_bypass.log', 'r', encoding='utf-8', errors='replace') as f:
                    f.seek(last_pos)
                    new_lines = f.read()
                    if new_lines:
                        print(new_lines, end='')
                        last_pos = f.tell()
        except:
            pass
        time.sleep(0.1)  # Check every 100ms

# Start log monitor thread
log_thread = threading.Thread(target=monitor_log)
log_thread.daemon = True
log_thread.start()

# Also capture direct output
for line in process.stdout:
    if line:
        # Show httpx messages as agent activity indicators
        if 'INFO:httpx' in line:
            print("[AGENT API CALL]", end=" ")
        elif 'INFO:' in line:
            # Show other info messages
            print(line.strip())

# Wait for process to complete
process.wait()

# Give log monitor a moment to catch up
time.sleep(1)

print("\n" + "=" * 70)
if process.returncode == 0:
    print("ORCHESTRATION COMPLETE!")
    print("Check projects/quickshop-mvp-test6 for generated application")
else:
    print("ORCHESTRATION FAILED!")
    print("Check orchestrate_bypass.log for details")
print("=" * 70)