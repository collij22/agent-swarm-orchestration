#!/usr/bin/env python3
"""
Start the Agent Swarm Web Dashboard

This script starts both the backend server and frontend development server.
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Python packages
    try:
        import fastapi
        import uvicorn
        print("✅ Backend dependencies installed")
    except ImportError:
        print("❌ Backend dependencies missing. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Check if Node.js is installed
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        print("✅ Node.js installed")
    except:
        print("❌ Node.js not found. Please install Node.js from https://nodejs.org")
        return False
    
    # Check if frontend dependencies are installed
    dashboard_path = Path(__file__).parent / "dashboard"
    node_modules = dashboard_path / "node_modules"
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=dashboard_path)
    
    return True

def start_backend():
    """Start the FastAPI backend server"""
    print("\n🚀 Starting backend server on http://localhost:8000")
    
    # Start the backend server
    backend_process = subprocess.Popen(
        [sys.executable, "web_server.py"],
        cwd=Path(__file__).parent
    )
    
    return backend_process

def start_frontend():
    """Start the React frontend development server"""
    print("\n⚛️ Starting frontend on http://localhost:5173")
    
    dashboard_path = Path(__file__).parent / "dashboard"
    
    # Start the frontend dev server
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=dashboard_path
    )
    
    return frontend_process

def main():
    """Main function to start the dashboard"""
    print("="*50)
    print("🎯 Agent Swarm Web Dashboard Launcher")
    print("="*50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Failed to setup dependencies. Please install requirements manually.")
        sys.exit(1)
    
    try:
        # Start backend
        backend = start_backend()
        time.sleep(3)  # Give backend time to start
        
        # Start frontend
        frontend = start_frontend()
        time.sleep(5)  # Give frontend time to start
        
        # Open browser
        print("\n🌐 Opening dashboard in browser...")
        webbrowser.open("http://localhost:5173")
        
        print("\n" + "="*50)
        print("✅ Dashboard is running!")
        print("="*50)
        print("\nAccess points:")
        print("  📊 Dashboard: http://localhost:5173")
        print("  📡 API Docs:  http://localhost:8000/docs")
        print("  🔌 WebSocket: ws://localhost:8000/ws")
        print("\nPress Ctrl+C to stop all services")
        print("="*50)
        
        # Keep running until interrupted
        backend.wait()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Shutting down services...")
        backend.terminate()
        frontend.terminate()
        print("✅ Services stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()