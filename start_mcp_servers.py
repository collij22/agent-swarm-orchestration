#!/usr/bin/env python3
"""
Start MCP Servers for Agent Swarm
Cross-platform script to start all MCP servers
"""

import subprocess
import time
import sys
import os
import signal
import requests
from pathlib import Path

def kill_existing_servers():
    """Kill any existing MCP server processes"""
    print("Cleaning up any existing MCP servers...")
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/IM", "node.exe", "/FI", "WINDOWTITLE eq MCP*"], 
                      capture_output=True, shell=True)
    else:
        # On Unix-like systems, find and kill node processes on MCP ports
        for port in [3101, 3102, 3103]:
            try:
                result = subprocess.run(f"lsof -ti:{port}", shell=True, capture_output=True, text=True)
                if result.stdout.strip():
                    pid = result.stdout.strip()
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"Killed process on port {port}")
            except:
                pass

def start_server(name, command, port):
    """Start an MCP server in the background"""
    print(f"\nStarting {name} (Port {port})...")
    
    if sys.platform == "win32":
        # Windows: Use START command to run in new window
        cmd = f'start "{name}" /min cmd /c "{command}"'
        subprocess.Popen(cmd, shell=True)
    else:
        # Unix-like: Run in background
        subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
    
    # Give it time to start
    time.sleep(2)

def check_server_health(name, port):
    """Check if a server is responding"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        if response.status_code == 200:
            print(f"[OK] {name} is running on port {port}")
            return True
    except:
        pass
    
    print(f"[WARNING] {name} may not be running properly on port {port}")
    return False

def main():
    """Main function to start all MCP servers"""
    print("Starting MCP Servers for Agent Swarm...")
    print("=" * 40)
    
    # Kill existing servers
    kill_existing_servers()
    
    # Define servers to start
    servers = [
        {
            "name": "Semgrep MCP Server",
            "command": "npx @anthropic/mcp-server-semgrep --port 3101",
            "port": 3101
        },
        {
            "name": "Ref MCP Server", 
            "command": "npx @anthropic/mcp-server-ref --port 3102",
            "port": 3102
        },
        {
            "name": "Browser MCP Server",
            "command": "npx @anthropic/mcp-server-browser --port 3103",
            "port": 3103
        }
    ]
    
    # Start each server
    for server in servers:
        start_server(server["name"], server["command"], server["port"])
    
    # Wait a bit for all servers to fully start
    print("\nWaiting for servers to initialize...")
    time.sleep(3)
    
    # Check health of all servers
    print("\nChecking server health...")
    all_healthy = True
    for server in servers:
        if not check_server_health(server["name"], server["port"]):
            all_healthy = False
    
    print("\n" + "=" * 40)
    if all_healthy:
        print("✅ All MCP Servers started successfully!")
    else:
        print("⚠️ Some MCP servers may not be running properly.")
        print("The orchestrator will use fallback mode for unavailable servers.")
    
    print("\nMCP Servers are running in the background.")
    print("To stop them:")
    if sys.platform == "win32":
        print("  - Close the command windows or run: taskkill /F /IM node.exe")
    else:
        print("  - Run: pkill -f mcp-server")
    
    print("\nYou can now run: python orchestrate_enhanced.py")
    print("=" * 40)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)