#!/usr/bin/env python3
"""
Web Dashboard Server - FastAPI application for agent swarm monitoring

Features:
- REST API endpoints for session management
- WebSocket support for real-time updates
- Integration with existing session/metrics infrastructure
- JWT authentication support
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Import existing libraries
from lib.session_manager import SessionManager
from lib.metrics_aggregator import MetricsAggregator
from lib.performance_tracker import PerformanceTracker
from lib.session_analyzer import SessionAnalyzer
from lib.agent_logger import get_logger

# Initialize app
app = FastAPI(
    title="Agent Swarm Dashboard API",
    description="Real-time monitoring and control for the agent swarm",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
session_manager = SessionManager()
metrics_aggregator = MetricsAggregator()
performance_tracker = PerformanceTracker()
session_analyzer = SessionAnalyzer()
logger = get_logger()

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        # Remove from all subscriptions
        for topic in self.subscriptions:
            if websocket in self.subscriptions[topic]:
                self.subscriptions[topic].remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: dict, topic: str = "all"):
        """Broadcast message to all connections or specific topic subscribers"""
        message_json = json.dumps(message)
        
        connections = self.active_connections if topic == "all" else self.subscriptions.get(topic, [])
        
        for connection in connections:
            try:
                await connection.send_text(message_json)
            except:
                # Connection might be closed, ignore
                pass
    
    def subscribe(self, websocket: WebSocket, topic: str):
        """Subscribe a connection to a specific topic"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        if websocket not in self.subscriptions[topic]:
            self.subscriptions[topic].append(websocket)
    
    def unsubscribe(self, websocket: WebSocket, topic: str):
        """Unsubscribe a connection from a topic"""
        if topic in self.subscriptions and websocket in self.subscriptions[topic]:
            self.subscriptions[topic].remove(websocket)

manager = ConnectionManager()

# Pydantic models
class SessionResponse(BaseModel):
    session_id: str
    status: str
    start_time: str
    end_time: Optional[str]
    duration: Optional[float]
    agents_used: List[str]
    total_tool_calls: int
    error_count: int

class MetricsResponse(BaseModel):
    period: str
    total_sessions: int
    success_rate: float
    avg_duration: float
    most_used_agents: List[Dict[str, Any]]
    error_trends: List[Dict[str, Any]]

class PerformanceSnapshot(BaseModel):
    timestamp: str
    cpu_usage: float
    memory_usage: float
    active_sessions: int
    api_calls_per_minute: float
    avg_response_time: float

# REST API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "running",
        "service": "Agent Swarm Dashboard",
        "version": "1.0.0",
        "endpoints": {
            "api": "/docs",
            "websocket": "/ws",
            "sessions": "/api/sessions",
            "metrics": "/api/metrics",
            "performance": "/api/performance"
        }
    }

@app.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of sessions to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """List all sessions with optional filtering"""
    try:
        sessions = session_manager.list_sessions()
        
        # Filter by status if provided
        if status:
            sessions = [s for s in sessions if s.get("status") == status]
        
        # Apply pagination
        sessions = sessions[offset:offset + limit]
        
        # Convert to response format
        return [
            SessionResponse(
                session_id=s["session_id"],
                status=s["status"],
                start_time=s["start_time"],
                end_time=s.get("end_time"),
                duration=s.get("duration"),
                agents_used=s.get("agents_used", []),
                total_tool_calls=s.get("total_tool_calls", 0),
                error_count=s.get("error_count", 0)
            )
            for s in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get detailed information about a specific session"""
    try:
        session = session_manager.load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/replay")
async def replay_session(session_id: str):
    """Replay a session for debugging"""
    try:
        result = session_manager.replay_session(session_id)
        
        # Broadcast replay started event
        await manager.broadcast({
            "event": "session.replay.started",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, topic="sessions")
        
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics", response_model=MetricsResponse)
async def get_metrics(
    period: str = Query("daily", description="Aggregation period: hourly, daily, weekly, monthly")
):
    """Get aggregated metrics"""
    try:
        metrics = metrics_aggregator.get_metrics(period)
        
        return MetricsResponse(
            period=period,
            total_sessions=metrics.get("total_sessions", 0),
            success_rate=metrics.get("success_rate", 0.0),
            avg_duration=metrics.get("avg_duration", 0.0),
            most_used_agents=metrics.get("most_used_agents", []),
            error_trends=metrics.get("error_trends", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance", response_model=PerformanceSnapshot)
async def get_performance():
    """Get current performance snapshot"""
    try:
        stats = performance_tracker.get_current_stats()
        
        return PerformanceSnapshot(
            timestamp=datetime.now().isoformat(),
            cpu_usage=stats.get("cpu_percent", 0.0),
            memory_usage=stats.get("memory_percent", 0.0),
            active_sessions=len([s for s in session_manager.list_sessions() if s.get("status") == "running"]),
            api_calls_per_minute=stats.get("api_calls_per_minute", 0.0),
            avg_response_time=stats.get("avg_response_time", 0.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents")
async def list_agents():
    """List all available agents and their status"""
    try:
        # Get agent list from the project structure
        agents = [
            {"name": "project-architect", "tier": 1, "model": "opus", "status": "ready"},
            {"name": "rapid-builder", "tier": 1, "model": "sonnet", "status": "ready"},
            {"name": "ai-specialist", "tier": 1, "model": "opus", "status": "ready"},
            {"name": "quality-guardian", "tier": 1, "model": "sonnet", "status": "ready"},
            {"name": "devops-engineer", "tier": 1, "model": "sonnet", "status": "ready"},
            {"name": "api-integrator", "tier": 2, "model": "haiku", "status": "ready"},
            {"name": "database-expert", "tier": 2, "model": "sonnet", "status": "ready"},
            {"name": "frontend-specialist", "tier": 2, "model": "sonnet", "status": "ready"},
            {"name": "performance-optimizer", "tier": 2, "model": "sonnet", "status": "ready"},
            {"name": "documentation-writer", "tier": 2, "model": "haiku", "status": "ready"},
            {"name": "project-orchestrator", "tier": 3, "model": "opus", "status": "ready"},
            {"name": "requirements-analyst", "tier": 3, "model": "sonnet", "status": "ready"},
            {"name": "code-migrator", "tier": 3, "model": "sonnet", "status": "ready"},
            {"name": "debug-specialist", "tier": 3, "model": "opus", "status": "ready"},
            {"name": "meta-agent", "tier": 3, "model": "opus", "status": "ready"}
        ]
        
        # Add performance metrics for each agent if available
        for agent in agents:
            agent_metrics = metrics_aggregator.get_agent_metrics(agent["name"])
            if agent_metrics:
                agent.update(agent_metrics)
        
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/errors")
async def get_errors(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(100, description="Number of errors to return")
):
    """Get error patterns and occurrences"""
    try:
        if session_id:
            analysis = session_analyzer.analyze_session(session_id, ["error_pattern"])
            errors = analysis.get("error_patterns", [])
        else:
            # Get recent errors from all sessions
            errors = []
            sessions = session_manager.list_sessions()[-10:]  # Last 10 sessions
            for session in sessions:
                if session.get("error_count", 0) > 0:
                    session_data = session_manager.load_session(session["session_id"])
                    for event in session_data.get("events", []):
                        if event.get("type") == "error":
                            errors.append({
                                "session_id": session["session_id"],
                                "timestamp": event.get("timestamp"),
                                "agent": event.get("agent"),
                                "error": event.get("message"),
                                "context": event.get("context")
                            })
        
        return errors[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/{session_id}")
async def analyze_session(
    session_id: str,
    analysis_types: List[str] = Query(["error_pattern", "performance_bottleneck"])
):
    """Analyze a specific session"""
    try:
        result = session_analyzer.analyze_session(session_id, analysis_types)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    # Send initial connection message
    await manager.send_personal_message(json.dumps({
        "event": "connection.established",
        "timestamp": datetime.now().isoformat(),
        "client_id": str(uuid.uuid4())
    }), websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle subscription requests
            if message.get("action") == "subscribe":
                topic = message.get("topic", "all")
                manager.subscribe(websocket, topic)
                await manager.send_personal_message(json.dumps({
                    "event": "subscription.confirmed",
                    "topic": topic
                }), websocket)
            
            elif message.get("action") == "unsubscribe":
                topic = message.get("topic")
                if topic:
                    manager.unsubscribe(websocket, topic)
                    await manager.send_personal_message(json.dumps({
                        "event": "subscription.removed",
                        "topic": topic
                    }), websocket)
            
            # Echo other messages (for testing)
            elif message.get("action") == "ping":
                await manager.send_personal_message(json.dumps({
                    "event": "pong",
                    "timestamp": datetime.now().isoformat()
                }), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast({
            "event": "client.disconnected",
            "timestamp": datetime.now().isoformat()
        }, topic="system")

# Background task to send periodic updates
async def send_performance_updates():
    """Send performance updates every 5 seconds"""
    while True:
        await asyncio.sleep(5)
        try:
            stats = performance_tracker.get_current_stats()
            await manager.broadcast({
                "event": "performance.update",
                "data": {
                    "cpu": stats.get("cpu_percent", 0),
                    "memory": stats.get("memory_percent", 0),
                    "timestamp": datetime.now().isoformat()
                }
            }, topic="performance")
        except Exception as e:
            print(f"Error sending performance update: {e}")

@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup"""
    asyncio.create_task(send_performance_updates())
    print("🚀 Agent Swarm Dashboard started")
    print("📊 API docs available at http://localhost:8000/docs")
    print("🔌 WebSocket endpoint at ws://localhost:8000/ws")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    # Close all WebSocket connections
    for connection in manager.active_connections:
        await connection.close()
    print("👋 Agent Swarm Dashboard stopped")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )