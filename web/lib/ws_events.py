#!/usr/bin/env python3
"""
WebSocket Events Handler - Bridges hook events with WebSocket connections

Features:
- Subscribe to HookManager events
- Transform hook events to WebSocket messages
- Maintain client connection state
- Handle reconnection logic
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from web.lib.event_streamer import get_event_streamer, StreamEvent

class WebSocketEventHandler:
    """Handles WebSocket event broadcasting from hook events"""
    
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.event_streamer = get_event_streamer()
        self.active_sessions: Set[str] = set()
        self.event_queue = asyncio.Queue()
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self):
        """Subscribe to all event types from the event streamer"""
        # Subscribe to all events
        self.event_streamer.subscribe("*", self._handle_stream_event)
    
    def _handle_stream_event(self, event: StreamEvent):
        """Handle events from the event streamer"""
        # Queue the event for async processing
        asyncio.create_task(self._queue_event(event))
    
    async def _queue_event(self, event: StreamEvent):
        """Queue event for processing"""
        await self.event_queue.put(event)
    
    async def process_events(self):
        """Process events from the queue and broadcast to clients"""
        while True:
            try:
                # Get event from queue
                event = await self.event_queue.get()
                
                # Transform event for WebSocket clients
                ws_message = self._transform_event(event)
                
                # Determine broadcast topic based on event type
                topic = self._get_topic_for_event(event)
                
                # Broadcast to relevant clients
                await self.connection_manager.broadcast(ws_message, topic)
                
                # Track active sessions
                if event.session_id:
                    if event.event_type.value == "session.started":
                        self.active_sessions.add(event.session_id)
                    elif event.event_type.value == "session.completed":
                        self.active_sessions.discard(event.session_id)
                
            except Exception as e:
                print(f"Error processing event: {e}")
    
    def _transform_event(self, event: StreamEvent) -> dict:
        """Transform StreamEvent to WebSocket message format"""
        return {
            "event": event.event_type.value,
            "timestamp": event.timestamp,
            "data": event.data,
            "metadata": {
                "session_id": event.session_id,
                "agent_name": event.agent_name,
                "severity": event.severity
            }
        }
    
    def _get_topic_for_event(self, event: StreamEvent) -> str:
        """Determine the broadcast topic for an event"""
        event_type = event.event_type.value
        
        # Map event types to topics
        if event_type.startswith("session."):
            return "sessions"
        elif event_type.startswith("agent."):
            return "agents"
        elif event_type.startswith("performance."):
            return "performance"
        elif event_type.startswith("cost."):
            return "costs"
        elif event_type in ["memory.warning", "checkpoint.saved"]:
            return "system"
        else:
            return "all"
    
    async def send_heartbeat(self):
        """Send periodic heartbeat to all connected clients"""
        while True:
            await asyncio.sleep(30)  # Every 30 seconds
            
            heartbeat = {
                "event": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "active_sessions": list(self.active_sessions),
                    "server_time": datetime.now().isoformat()
                }
            }
            
            await self.connection_manager.broadcast(heartbeat, "all")
    
    async def handle_client_request(self, websocket, request: dict) -> dict:
        """Handle specific client requests"""
        action = request.get("action")
        
        if action == "get_active_sessions":
            return {
                "response": "active_sessions",
                "data": list(self.active_sessions)
            }
        
        elif action == "get_recent_events":
            count = request.get("count", 50)
            event_type = request.get("event_type")
            
            recent_events = self.event_streamer.get_recent_events(count, event_type)
            
            return {
                "response": "recent_events",
                "data": [self._transform_event(e) for e in recent_events]
            }
        
        elif action == "subscribe_to_session":
            session_id = request.get("session_id")
            if session_id:
                # Add custom filter for this session
                self.connection_manager.subscribe(websocket, f"session_{session_id}")
                return {
                    "response": "subscribed",
                    "session_id": session_id
                }
        
        elif action == "unsubscribe_from_session":
            session_id = request.get("session_id")
            if session_id:
                self.connection_manager.unsubscribe(websocket, f"session_{session_id}")
                return {
                    "response": "unsubscribed",
                    "session_id": session_id
                }
        
        return {
            "response": "unknown_action",
            "error": f"Unknown action: {action}"
        }
    
    async def start(self):
        """Start the event handler"""
        # Start event processing
        asyncio.create_task(self.process_events())
        
        # Start heartbeat
        asyncio.create_task(self.send_heartbeat())
        
        print("🔌 WebSocket event handler started")

# Integration helpers for the web server
def create_ws_handler(connection_manager):
    """Create and return a WebSocket event handler"""
    handler = WebSocketEventHandler(connection_manager)
    return handler

async def emit_custom_event(event_type: str, data: dict, session_id: Optional[str] = None):
    """Helper to emit custom events to the dashboard"""
    streamer = get_event_streamer()
    
    from web.lib.event_streamer import StreamEvent, EventType
    
    # Map string to EventType or use HOOK_TRIGGER as default
    try:
        event_type_enum = EventType[event_type.upper().replace(".", "_")]
    except:
        event_type_enum = EventType.HOOK_TRIGGER
    
    event = StreamEvent(
        event_type=event_type_enum,
        timestamp=datetime.now().isoformat(),
        data=data,
        session_id=session_id
    )
    
    await streamer.emit_event(event)

# Example usage
if __name__ == "__main__":
    class MockConnectionManager:
        async def broadcast(self, message, topic):
            print(f"Broadcasting to {topic}: {message}")
        
        def subscribe(self, websocket, topic):
            print(f"Subscribed to {topic}")
        
        def unsubscribe(self, websocket, topic):
            print(f"Unsubscribed from {topic}")
    
    async def demo():
        # Create mock connection manager
        mock_cm = MockConnectionManager()
        
        # Create handler
        handler = create_ws_handler(mock_cm)
        await handler.start()
        
        # Emit some test events
        await emit_custom_event("session_start", {"project": "TestApp"}, "test-session-1")
        await asyncio.sleep(1)
        
        await emit_custom_event("agent_start", {"agent": "project-architect"}, "test-session-1")
        await asyncio.sleep(1)
        
        # Let events process
        await asyncio.sleep(2)
    
    asyncio.run(demo())