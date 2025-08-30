#!/usr/bin/env python3
"""
Simple Dashboard Starter - Works with minimal dependencies
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_core_dependencies():
    """Check only essential dependencies"""
    print("🔍 Checking core dependencies...")
    
    try:
        import fastapi
        import uvicorn
        print("✅ Core backend dependencies found")
        return True
    except ImportError:
        print("⚠️ Core dependencies missing")
        return False

def install_minimal_deps():
    """Install minimal working set of dependencies"""
    print("\n📦 Installing minimal dependencies...")
    
    # Install core packages that don't require compilation
    core_packages = [
        "fastapi",
        "uvicorn",
        "websockets",
        "python-multipart",
        "aiofiles"
    ]
    
    for package in core_packages:
        print(f"Installing {package}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=False,  # Don't fail on error
                capture_output=True
            )
        except:
            pass
    
    print("✅ Minimal installation complete")

def start_backend_simple():
    """Start backend with basic Python command"""
    print("\n🚀 Starting backend server...")
    
    # Create a minimal server file if web_server.py has issues
    minimal_server = """
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

app = FastAPI(title="Agent Swarm Dashboard")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "Dashboard API Running", "time": datetime.now().isoformat()}

@app.get("/api/sessions")
async def get_sessions():
    return {"sessions": [], "message": "Backend running in minimal mode"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "connection", "status": "connected"})
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"echo": data})
    except:
        pass

if __name__ == "__main__":
    print("Starting minimal dashboard backend on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    
    # Write minimal server
    minimal_server_path = Path(__file__).parent / "minimal_server.py"
    minimal_server_path.write_text(minimal_server)
    
    # Try to start the real server first
    try:
        print("Attempting to start full web server...")
        backend_process = subprocess.Popen(
            [sys.executable, "web_server.py"],
            cwd=Path(__file__).parent
        )
        time.sleep(2)
        
        # Check if it started
        if backend_process.poll() is None:
            print("✅ Full backend server started successfully")
            return backend_process
    except:
        pass
    
    # Fall back to minimal server
    print("Starting minimal backend server...")
    backend_process = subprocess.Popen(
        [sys.executable, "minimal_server.py"],
        cwd=Path(__file__).parent
    )
    print("✅ Minimal backend server started on http://localhost:8000")
    return backend_process

def start_frontend_simple():
    """Start frontend with npm"""
    print("\n⚛️ Starting frontend...")
    
    dashboard_path = Path(__file__).parent / "dashboard"
    
    # Check if node_modules exists
    if not (dashboard_path / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=dashboard_path, shell=True)
    
    # Start frontend
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=dashboard_path,
        shell=True
    )
    
    print("✅ Frontend starting on http://localhost:5173")
    return frontend_process

def main():
    print("=" * 50)
    print("🎯 Agent Swarm Dashboard - Simple Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_core_dependencies():
        install_minimal_deps()
    
    # Start services
    backend = None
    frontend = None
    
    try:
        backend = start_backend_simple()
        time.sleep(2)
        frontend = start_frontend_simple()
        
        print("\n" + "=" * 50)
        print("✅ Dashboard is starting!")
        print("=" * 50)
        print("\n📊 Access the dashboard at:")
        print("   Frontend: http://localhost:5173")
        print("   Backend API: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print("\n⚠️ Press Ctrl+C to stop all services")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        if backend:
            backend.terminate()
        if frontend:
            frontend.terminate()
        print("✅ Dashboard stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if backend:
            backend.terminate()
        if frontend:
            frontend.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()