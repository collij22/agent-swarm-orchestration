#!/usr/bin/env python
"""
RUN AND MONITOR - Runs the working version and monitors progress
"""

import subprocess
import threading
import time
import os
import sys
from pathlib import Path

print("=" * 70)
print("QUICKSHOP MVP - AGENT SWARM MONITOR")
print("=" * 70)
print()
print("This will run the agent swarm and show progress.")
print("The agents ARE working even if output is limited.")
print()
print("-" * 70)

# Clear old log
if os.path.exists('orchestrate_bypass.log'):
    try:
        os.remove('orchestrate_bypass.log')
    except:
        pass

# Function to monitor file creation
def monitor_files():
    """Monitor files being created"""
    output_dir = Path('projects/quickshop-mvp-test6')
    last_count = 0
    
    while True:
        try:
            if output_dir.exists():
                # Count files
                file_count = sum(1 for _ in output_dir.rglob('*') if _.is_file())
                
                if file_count > last_count:
                    new_files = file_count - last_count
                    print(f"\n[PROGRESS] {new_files} new file(s) created - Total: {file_count} files")
                    
                    # Show recent files
                    recent_files = sorted(output_dir.rglob('*'), key=lambda x: x.stat().st_mtime)[-3:]
                    for f in recent_files:
                        if f.is_file():
                            rel_path = f.relative_to(output_dir)
                            print(f"  - {rel_path}")
                    
                    last_count = file_count
        except:
            pass
        
        time.sleep(5)  # Check every 5 seconds

# Function to monitor log for agent names
def monitor_log():
    """Monitor log for agent activity"""
    log_file = 'orchestrate_bypass.log'
    last_pos = 0
    agents_seen = set()
    
    while True:
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_pos)
                    new_content = f.read()
                    
                    # Look for agent indicators
                    if 'requirements-analyst' in new_content and 'requirements-analyst' not in agents_seen:
                        print("\n[AGENT] Requirements Analyst started")
                        agents_seen.add('requirements-analyst')
                    if 'rapid-builder' in new_content and 'rapid-builder' not in agents_seen:
                        print("\n[AGENT] Rapid Builder started")
                        agents_seen.add('rapid-builder')
                    if 'frontend-specialist' in new_content and 'frontend-specialist' not in agents_seen:
                        print("\n[AGENT] Frontend Specialist started")
                        agents_seen.add('frontend-specialist')
                    if 'database-expert' in new_content and 'database-expert' not in agents_seen:
                        print("\n[AGENT] Database Expert started")
                        agents_seen.add('database-expert')
                    if 'api-integrator' in new_content and 'api-integrator' not in agents_seen:
                        print("\n[AGENT] API Integrator started")
                        agents_seen.add('api-integrator')
                    
                    last_pos = f.tell()
        except:
            pass
        
        time.sleep(2)  # Check every 2 seconds

# Function to count API calls
api_call_count = 0
def monitor_output(line):
    """Monitor process output"""
    global api_call_count
    
    # Strip whitespace
    line = line.strip()
    
    # Count API calls but don't show them all
    if 'INFO:httpx:HTTP Request' in line:
        api_call_count += 1
        if api_call_count % 10 == 0:
            print(f"[API] {api_call_count} API calls made...")
    # Show important messages
    elif 'Enhanced full_stack_api Workflow' in line:
        print("\n[SYSTEM] Workflow initialized")
    elif 'WebSocket' in line:
        print("[SYSTEM] WebSocket server started")
    elif 'workflow' in line.lower():
        print(f"[WORKFLOW] {line}")
    elif 'error' in line.lower() and 'ERRORLEVEL' not in line:
        # Show errors but strip Unicode
        safe_line = line.encode('ascii', 'replace').decode('ascii')
        print(f"[ERROR] {safe_line[:100]}")
    elif 'success' in line.lower():
        print(f"[SUCCESS] {line}")

print("\nStarting agent swarm...")
print("-" * 70)

# Start monitoring threads
file_thread = threading.Thread(target=monitor_files)
file_thread.daemon = True
file_thread.start()

log_thread = threading.Thread(target=monitor_log)
log_thread.daemon = True
log_thread.start()

# Run the orchestrator
try:
    process = subprocess.Popen(
        [sys.executable, 'fix_specific_tools.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={**os.environ, 'PYTHONUNBUFFERED': '1', 'PYTHONIOENCODING': 'utf-8'}
    )
    
    print("\n[SYSTEM] Orchestrator started - monitoring progress...\n")
    
    # Monitor output
    for line in process.stdout:
        if line:
            monitor_output(line)
    
    # Wait for completion
    process.wait()
    
    if process.returncode == 0:
        print("\n" + "=" * 70)
        print("SUCCESS! QuickShop MVP has been generated!")
        print("=" * 70)
        print("\nLocation: projects/quickshop-mvp-test6")
        print("\nTo run the application:")
        print("  cd projects\\quickshop-mvp-test6")
        print("  docker-compose up")
        print("\nAccess at:")
        print("  - Frontend: http://localhost:3000")
        print("  - Backend: http://localhost:8000")
    else:
        print("\n" + "=" * 70)
        print("FAILED - Check orchestrate_bypass.log for details")
        print("=" * 70)
        
except KeyboardInterrupt:
    print("\n\n[!] Interrupted by user")
    if process:
        process.terminate()
except Exception as e:
    print(f"\n[!] Error: {e}")

print("\nMonitoring complete.")
print("=" * 70)