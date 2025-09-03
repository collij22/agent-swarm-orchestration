#!/usr/bin/env python3
"""
DASHBOARD LAUNCHER - Best solution for viewing agent progress
Bypasses all console Unicode issues by using web interface
"""

import sys
import os
import subprocess
import time
import webbrowser
import socket
from pathlib import Path

def find_free_port(start_port=5174):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except:
                continue
    return start_port

print("=" * 80)
print("🚀 AGENT SWARM DASHBOARD LAUNCHER")
print("=" * 80)
print()
print("This launcher uses the web dashboard to show agent progress.")
print("No Unicode issues, full visualization, real-time updates!")
print()

# Find a free port for the dashboard
dashboard_port = find_free_port(5174)
print(f"Dashboard port: {dashboard_port}")

# Set up environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['DASHBOARD_PORT'] = str(dashboard_port)

# First, let's patch the dashboard port in the web server if needed
web_server_path = Path("web/start_dashboard.py")
if web_server_path.exists():
    content = web_server_path.read_text(encoding='utf-8')
    # Update port reference
    if "5173" in content:
        content = content.replace("5173", str(dashboard_port))
        web_server_path.write_text(content, encoding='utf-8')
        print(f"Updated dashboard to use port {dashboard_port}")

# Also update the frontend config if it exists
frontend_config = Path("web/frontend/vite.config.js")
if frontend_config.exists():
    content = frontend_config.read_text(encoding='utf-8')
    if "5173" in content:
        content = content.replace("5173", str(dashboard_port))
        frontend_config.write_text(content, encoding='utf-8')

# Command to run
cmd = [
    sys.executable,
    'orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
    '--output-dir', 'projects/quickshop-mvp-dashboard',
    '--dashboard',  # Enable dashboard
    '--progress',
    '--summary-level', 'detailed',  # More detail in dashboard
    '--max-parallel', '3',  # Can handle more parallel with dashboard
    '--human-log'
]

print("Starting orchestration with dashboard...")
print(f"Dashboard URL: http://localhost:{dashboard_port}")
print()
print("The dashboard will show:")
print("  ✅ Real-time agent progress")
print("  ✅ Completion percentages")
print("  ✅ Agent interactions")
print("  ✅ File creation logs")
print("  ✅ Error messages (if any)")
print()
print("Starting in 3 seconds...")
time.sleep(3)

# Open browser automatically
dashboard_url = f"http://localhost:{dashboard_port}"
print(f"Opening browser to {dashboard_url}")
webbrowser.open(dashboard_url)

print()
print("-" * 80)
print("Orchestrator output:")
print("-" * 80)
print()

# Run the orchestrator
try:
    process = subprocess.run(cmd, check=False)
    if process.returncode == 0:
        print()
        print("=" * 80)
        print("✅ SUCCESS - QuickShop MVP generated!")
        print("=" * 80)
        print()
        print("Check the output in: projects/quickshop-mvp-dashboard/")
    else:
        print()
        print("⚠️ Process ended with errors. Check the dashboard for details.")
except KeyboardInterrupt:
    print("\n\nStopped by user.")
except Exception as e:
    print(f"\nError: {e}")

print()
print("Dashboard launcher finished.")
input("Press Enter to exit...")