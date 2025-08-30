#!/usr/bin/env python3
"""
Real-Time Progress Streaming System for Enhanced Orchestration

Features:
- WebSocket-based real-time progress streaming
- Integration with existing web dashboard
- Progress event broadcasting
- Requirement tracking dashboard updates
- Agent execution status streaming
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    # Create mock websockets module
    class MockWebSocketServer:
        def close(self):
            pass
        async def wait_closed(self):
            pass
    
    class MockWebSocketServerProtocol:
        async def send(self, data):
            pass
        async def wait_closed(self):
            pass
    
    class MockWebSocketsModule:
        WebSocketServer = MockWebSocketServer
        WebSocketServerProtocol = MockWebSocketServerProtocol
        
        async def serve(self, handler, host, port):
            return MockWebSocketServer()
        
        class exceptions:
            class ConnectionClosed(Exception):
                pass
    
    websockets = MockWebSocketsModule()

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from .orchestration_enhanced import WorkflowProgress, RequirementItem, AgentExecutionPlan
from .agent_logger import ReasoningLogger, get_logger


class ProgressEventType:
    """Progress event types for dashboard updates"""
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    REQUIREMENT_UPDATED = "requirement_updated"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    OVERALL_PROGRESS = "overall_progress"
    ERROR_OCCURRED = "error_occurred"
    CHECKPOINT_SAVED = "checkpoint_saved"
    MANUAL_INTERVENTION = "manual_intervention"


class ProgressEvent:
    """Individual progress event"""
    
    def __init__(self, event_type: str, data: Dict, timestamp: Optional[str] = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now().isoformat()
        self.event_id = f"{int(time.time() * 1000)}_{hash(str(data)) % 10000}"
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "data": self.data
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ProgressStreamer:
    """Real-time progress streaming system"""
    
    def __init__(self, logger: Optional[ReasoningLogger] = None):
        self.logger = logger or get_logger()
        
        # WebSocket connections
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.websocket_server: Optional[websockets.WebSocketServer] = None
        self.websocket_port = 8765
        
        # Redis for pub/sub (if available)
        self.redis_client: Optional[redis.Redis] = None
        if HAS_REDIS:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                self.redis_client.ping()
            except:
                self.redis_client = None
        
        # Event storage
        self.event_history: List[ProgressEvent] = []
        self.max_history = 1000
        
        # Current state
        self.current_progress: Optional[WorkflowProgress] = None
        self.current_requirements: Dict[str, RequirementItem] = {}
        self.current_agents: Dict[str, AgentExecutionPlan] = {}
        
        # Callbacks
        self.event_callbacks: List[Callable[[ProgressEvent], None]] = []
    
    def add_event_callback(self, callback: Callable[[ProgressEvent], None]):
        """Add callback for progress events"""
        self.event_callbacks.append(callback)
    
    async def start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        if not HAS_WEBSOCKETS:
            self.logger.log_reasoning(
                "progress_streamer",
                "WebSocket server disabled (websockets not installed)",
                "Install websockets for real-time progress streaming"
            )
            return
        
        try:
            self.websocket_server = await websockets.serve(
                self._handle_websocket_client,
                "localhost",
                self.websocket_port
            )
            
            self.logger.log_reasoning(
                "progress_streamer",
                f"WebSocket server started on port {self.websocket_port}",
                "Real-time progress streaming available"
            )
        except Exception as e:
            self.logger.log_error("progress_streamer", f"Failed to start WebSocket server: {e}")
    
    async def stop_websocket_server(self):
        """Stop WebSocket server"""
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
    
    async def _handle_websocket_client(self, websocket, path):
        """Handle WebSocket client connection"""
        self.websocket_clients.add(websocket)
        
        try:
            # Send current state to new client
            if self.current_progress:
                await self._send_to_client(websocket, ProgressEvent(
                    ProgressEventType.OVERALL_PROGRESS,
                    {"progress": asdict(self.current_progress)}
                ))
            
            # Send recent events
            recent_events = self.event_history[-50:]  # Last 50 events
            for event in recent_events:
                await self._send_to_client(websocket, event)
            
            # Keep connection alive
            await websocket.wait_closed()
        
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            self.logger.log_error("progress_streamer", f"WebSocket client error: {e}")
        finally:
            self.websocket_clients.discard(websocket)
    
    async def _send_to_client(self, websocket, event: ProgressEvent):
        """Send event to specific WebSocket client"""
        try:
            await websocket.send(event.to_json())
        except Exception as e:
            self.logger.log_error("progress_streamer", f"Failed to send to WebSocket client: {e}")
    
    async def broadcast_event(self, event: ProgressEvent):
        """Broadcast event to all connected clients"""
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Broadcast to WebSocket clients
        if self.websocket_clients:
            disconnected = set()
            for client in self.websocket_clients:
                try:
                    await self._send_to_client(client, event)
                except:
                    disconnected.add(client)
            
            # Remove disconnected clients
            self.websocket_clients -= disconnected
        
        # Publish to Redis if available
        if self.redis_client:
            try:
                self.redis_client.publish('orchestration_progress', event.to_json())
            except Exception as e:
                self.logger.log_error("progress_streamer", f"Redis publish failed: {e}")
        
        # Call event callbacks
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.log_error("progress_streamer", f"Event callback failed: {e}")
    
    async def update_workflow_progress(self, progress: WorkflowProgress):
        """Update overall workflow progress"""
        self.current_progress = progress
        
        await self.broadcast_event(ProgressEvent(
            ProgressEventType.OVERALL_PROGRESS,
            {
                "progress": asdict(progress),
                "completion_percentage": progress.overall_completion,
                "estimated_remaining": progress.estimated_remaining_time
            }
        ))
    
    async def update_requirement_status(self, requirement_id: str, requirement: RequirementItem):
        """Update individual requirement status"""
        self.current_requirements[requirement_id] = requirement
        
        await self.broadcast_event(ProgressEvent(
            ProgressEventType.REQUIREMENT_UPDATED,
            {
                "requirement_id": requirement_id,
                "requirement": asdict(requirement),
                "status": requirement.status.value,
                "completion_percentage": requirement.completion_percentage
            }
        ))
    
    async def update_agent_status(self, agent_name: str, plan: AgentExecutionPlan):
        """Update agent execution status"""
        self.current_agents[agent_name] = plan
        
        event_type = ProgressEventType.AGENT_STARTED
        if plan.status.value == "completed":
            event_type = ProgressEventType.AGENT_COMPLETED
        elif plan.status.value == "failed":
            event_type = ProgressEventType.AGENT_FAILED
        
        await self.broadcast_event(ProgressEvent(
            event_type,
            {
                "agent_name": agent_name,
                "plan": asdict(plan),
                "status": plan.status.value,
                "requirements": plan.requirements,
                "execution_time": plan.execution_time,
                "retry_count": plan.current_retry
            }
        ))
    
    async def notify_workflow_started(self, workflow_id: str, total_requirements: int, total_agents: int):
        """Notify workflow started"""
        await self.broadcast_event(ProgressEvent(
            ProgressEventType.WORKFLOW_STARTED,
            {
                "workflow_id": workflow_id,
                "total_requirements": total_requirements,
                "total_agents": total_agents,
                "started_at": datetime.now().isoformat()
            }
        ))
    
    async def notify_workflow_completed(self, workflow_id: str, success: bool, summary: Dict):
        """Notify workflow completed"""
        event_type = ProgressEventType.WORKFLOW_COMPLETED if success else ProgressEventType.WORKFLOW_FAILED
        
        await self.broadcast_event(ProgressEvent(
            event_type,
            {
                "workflow_id": workflow_id,
                "success": success,
                "summary": summary,
                "completed_at": datetime.now().isoformat()
            }
        ))
    
    async def notify_error(self, agent_name: str, error_message: str, context: Dict = None):
        """Notify error occurred"""
        await self.broadcast_event(ProgressEvent(
            ProgressEventType.ERROR_OCCURRED,
            {
                "agent_name": agent_name,
                "error_message": error_message,
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            }
        ))
    
    async def notify_checkpoint_saved(self, checkpoint_path: str, workflow_id: str):
        """Notify checkpoint saved"""
        await self.broadcast_event(ProgressEvent(
            ProgressEventType.CHECKPOINT_SAVED,
            {
                "checkpoint_path": checkpoint_path,
                "workflow_id": workflow_id,
                "saved_at": datetime.now().isoformat()
            }
        ))
    
    async def notify_manual_intervention(self, agent_name: str, reason: str, options: List[str]):
        """Notify manual intervention required"""
        await self.broadcast_event(ProgressEvent(
            ProgressEventType.MANUAL_INTERVENTION,
            {
                "agent_name": agent_name,
                "reason": reason,
                "options": options,
                "timestamp": datetime.now().isoformat()
            }
        ))
    
    def get_current_state(self) -> Dict:
        """Get current state for dashboard"""
        return {
            "progress": asdict(self.current_progress) if self.current_progress else None,
            "requirements": {
                req_id: asdict(req) for req_id, req in self.current_requirements.items()
            },
            "agents": {
                agent: asdict(plan) for agent, plan in self.current_agents.items()
            },
            "recent_events": [event.to_dict() for event in self.event_history[-20:]]
        }
    
    def save_progress_snapshot(self, file_path: Path):
        """Save current progress snapshot to file"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "state": self.get_current_state(),
            "event_history": [event.to_dict() for event in self.event_history]
        }
        
        with open(file_path, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        self.logger.log_reasoning(
            "progress_streamer",
            f"Progress snapshot saved: {file_path}",
            "Comprehensive progress state saved"
        )


class DashboardIntegration:
    """Integration with existing web dashboard"""
    
    def __init__(self, progress_streamer: ProgressStreamer):
        self.streamer = progress_streamer
        self.dashboard_api_base = "http://localhost:8000"  # Assuming FastAPI backend
    
    async def register_orchestration_endpoints(self, app):
        """Register orchestration endpoints with FastAPI app"""
        
        @app.get("/api/orchestration/progress")
        async def get_current_progress():
            """Get current orchestration progress"""
            return self.streamer.get_current_state()
        
        @app.get("/api/orchestration/requirements")
        async def get_requirements():
            """Get all requirements with status"""
            return {
                req_id: asdict(req) for req_id, req in self.streamer.current_requirements.items()
            }
        
        @app.get("/api/orchestration/agents")
        async def get_agent_plans():
            """Get all agent execution plans"""
            return {
                agent: asdict(plan) for agent, plan in self.streamer.current_agents.items()
            }
        
        @app.get("/api/orchestration/events")
        async def get_recent_events(limit: int = 50):
            """Get recent progress events"""
            events = self.streamer.event_history[-limit:]
            return [event.to_dict() for event in events]
        
        @app.websocket("/ws/orchestration")
        async def websocket_orchestration_progress(websocket):
            """WebSocket endpoint for real-time orchestration progress"""
            await websocket.accept()
            
            try:
                # Send current state
                current_state = self.streamer.get_current_state()
                await websocket.send_json({
                    "type": "current_state",
                    "data": current_state
                })
                
                # Keep connection alive and forward events
                while True:
                    await asyncio.sleep(1)  # Keep alive
                    
            except Exception as e:
                print(f"WebSocket error: {e}")
            finally:
                await websocket.close()


# Integration functions for use in orchestrate_v2.py
def create_progress_streamer() -> ProgressStreamer:
    """Create and configure progress streamer"""
    return ProgressStreamer()


def create_orchestration_progress_callback(streamer: ProgressStreamer):
    """Create progress callback for AdaptiveWorkflowEngine"""
    async def progress_callback(progress: WorkflowProgress):
        await streamer.update_workflow_progress(progress)
    
    return progress_callback


# Export classes and functions
__all__ = [
    "ProgressStreamer",
    "ProgressEvent", 
    "ProgressEventType",
    "DashboardIntegration",
    "create_progress_streamer",
    "create_orchestration_progress_callback"
]