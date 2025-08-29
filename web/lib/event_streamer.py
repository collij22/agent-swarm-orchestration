#!/usr/bin/env python3
"""
Event Streamer - WebSocket event streaming for real-time dashboard updates

Features:
- Hook event listener integration
- Event filtering and subscription management
- Automatic reconnection handling
- Event buffering for offline clients
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from collections import deque
from dataclasses import dataclass, asdict
from enum import Enum
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.hook_manager import HookManager

class EventType(Enum):
    """Event types for dashboard streaming"""
    SESSION_START = "session.started"
    SESSION_COMPLETE = "session.completed"
    SESSION_ERROR = "session.error"
    AGENT_START = "agent.started"
    AGENT_COMPLETE = "agent.completed"
    AGENT_ERROR = "agent.error"
    TOOL_EXECUTE = "tool.executed"
    MILESTONE_REACH = "milestone.reached"
    PERFORMANCE_UPDATE = "performance.update"
    COST_UPDATE = "cost.update"
    MEMORY_WARNING = "memory.warning"
    CHECKPOINT_SAVE = "checkpoint.saved"
    HOOK_TRIGGER = "hook.triggered"

@dataclass
class StreamEvent:
    """Event structure for streaming"""
    event_type: EventType
    timestamp: str
    data: Dict[str, Any]
    session_id: Optional[str] = None
    agent_name: Optional[str] = None
    severity: str = "info"  # info, warning, error, critical
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps({
            "event": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "severity": self.severity
        })

class EventStreamer:
    """Manages event streaming to WebSocket clients"""
    
    def __init__(self, max_buffer_size: int = 1000):
        self.event_buffer = deque(maxlen=max_buffer_size)
        self.event_filters: Dict[str, Callable] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.hook_manager = None
        self.is_running = False
        self._setup_hook_listeners()
    
    def _setup_hook_listeners(self):
        """Setup listeners for hook events"""
        try:
            self.hook_manager = HookManager()
            # Register as hook event listener
            self.hook_manager.register_listener(self._handle_hook_event)
        except Exception as e:
            print(f"Warning: Could not setup hook listeners: {e}")
    
    def _handle_hook_event(self, hook_name: str, event_data: Dict[str, Any]):
        """Handle events from hook system"""
        # Map hook events to stream events
        event_mapping = {
            "pre_tool_use": EventType.TOOL_EXECUTE,
            "post_tool_use": EventType.TOOL_EXECUTE,
            "checkpoint_save": EventType.CHECKPOINT_SAVE,
            "memory_check": EventType.MEMORY_WARNING,
            "progress_update": EventType.MILESTONE_REACH,
            "cost_control": EventType.COST_UPDATE
        }
        
        event_type = event_mapping.get(hook_name, EventType.HOOK_TRIGGER)
        
        # Create stream event
        event = StreamEvent(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            data={
                "hook_name": hook_name,
                **event_data
            },
            session_id=event_data.get("session_id"),
            agent_name=event_data.get("agent_name"),
            severity=self._determine_severity(hook_name, event_data)
        )
        
        # Emit the event
        asyncio.create_task(self.emit_event(event))
    
    def _determine_severity(self, hook_name: str, event_data: Dict) -> str:
        """Determine event severity based on hook and data"""
        if "error" in event_data or "exception" in event_data:
            return "error"
        elif hook_name == "memory_check" and event_data.get("memory_percent", 0) > 80:
            return "warning"
        elif hook_name == "cost_control" and event_data.get("cost_exceeded", False):
            return "critical"
        return "info"
    
    async def emit_event(self, event: StreamEvent):
        """Emit an event to all subscribers"""
        # Add to buffer
        self.event_buffer.append(event)
        
        # Apply filters
        if not self._should_emit(event):
            return
        
        # Notify subscribers
        event_type = event.event_type.value
        
        # Call global subscribers
        for callback in self.subscribers.get("*", []):
            await self._safe_callback(callback, event)
        
        # Call specific event subscribers
        for callback in self.subscribers.get(event_type, []):
            await self._safe_callback(callback, event)
    
    async def _safe_callback(self, callback: Callable, event: StreamEvent):
        """Safely execute a callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            print(f"Error in event callback: {e}")
    
    def _should_emit(self, event: StreamEvent) -> bool:
        """Check if event should be emitted based on filters"""
        for filter_name, filter_func in self.event_filters.items():
            try:
                if not filter_func(event):
                    return False
            except Exception as e:
                print(f"Error in filter {filter_name}: {e}")
        return True
    
    def add_filter(self, name: str, filter_func: Callable[[StreamEvent], bool]):
        """Add an event filter"""
        self.event_filters[name] = filter_func
    
    def remove_filter(self, name: str):
        """Remove an event filter"""
        self.event_filters.pop(name, None)
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to events of a specific type or '*' for all"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from events"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
            except ValueError:
                pass
    
    def get_recent_events(self, count: int = 100, event_type: Optional[str] = None) -> List[StreamEvent]:
        """Get recent events from buffer"""
        events = list(self.event_buffer)
        
        if event_type:
            events = [e for e in events if e.event_type.value == event_type]
        
        return events[-count:]
    
    async def emit_session_start(self, session_id: str, context: Dict[str, Any]):
        """Emit session start event"""
        event = StreamEvent(
            event_type=EventType.SESSION_START,
            timestamp=datetime.now().isoformat(),
            data=context,
            session_id=session_id
        )
        await self.emit_event(event)
    
    async def emit_session_complete(self, session_id: str, success: bool, summary: Dict[str, Any]):
        """Emit session complete event"""
        event = StreamEvent(
            event_type=EventType.SESSION_COMPLETE,
            timestamp=datetime.now().isoformat(),
            data={
                "success": success,
                **summary
            },
            session_id=session_id,
            severity="info" if success else "error"
        )
        await self.emit_event(event)
    
    async def emit_agent_start(self, session_id: str, agent_name: str, task: str):
        """Emit agent start event"""
        event = StreamEvent(
            event_type=EventType.AGENT_START,
            timestamp=datetime.now().isoformat(),
            data={"task": task},
            session_id=session_id,
            agent_name=agent_name
        )
        await self.emit_event(event)
    
    async def emit_agent_complete(self, session_id: str, agent_name: str, success: bool, result: str):
        """Emit agent complete event"""
        event = StreamEvent(
            event_type=EventType.AGENT_COMPLETE,
            timestamp=datetime.now().isoformat(),
            data={
                "success": success,
                "result": result[:500]  # Truncate large results
            },
            session_id=session_id,
            agent_name=agent_name,
            severity="info" if success else "error"
        )
        await self.emit_event(event)
    
    async def emit_performance_update(self, metrics: Dict[str, Any]):
        """Emit performance update"""
        event = StreamEvent(
            event_type=EventType.PERFORMANCE_UPDATE,
            timestamp=datetime.now().isoformat(),
            data=metrics
        )
        await self.emit_event(event)
    
    async def emit_cost_update(self, session_id: str, cost_data: Dict[str, Any]):
        """Emit cost update"""
        event = StreamEvent(
            event_type=EventType.COST_UPDATE,
            timestamp=datetime.now().isoformat(),
            data=cost_data,
            session_id=session_id,
            severity="warning" if cost_data.get("approaching_limit") else "info"
        )
        await self.emit_event(event)

# Global event streamer instance
_event_streamer = None

def get_event_streamer() -> EventStreamer:
    """Get or create the global event streamer"""
    global _event_streamer
    if _event_streamer is None:
        _event_streamer = EventStreamer()
    return _event_streamer

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        # Create event streamer
        streamer = get_event_streamer()
        
        # Add a simple subscriber
        def print_event(event: StreamEvent):
            print(f"Event: {event.event_type.value} - {event.data}")
        
        streamer.subscribe("*", print_event)
        
        # Emit some test events
        await streamer.emit_session_start("test-session-1", {"project": "TestApp"})
        await asyncio.sleep(1)
        
        await streamer.emit_agent_start("test-session-1", "project-architect", "Design system")
        await asyncio.sleep(1)
        
        await streamer.emit_performance_update({
            "cpu": 45.2,
            "memory": 62.1,
            "api_calls": 23
        })
        await asyncio.sleep(1)
        
        await streamer.emit_agent_complete("test-session-1", "project-architect", True, "System designed")
        await asyncio.sleep(1)
        
        await streamer.emit_session_complete("test-session-1", True, {
            "duration": 120.5,
            "agents_used": ["project-architect"],
            "total_cost": 0.15
        })
        
        # Show recent events
        print("\nRecent events:")
        for event in streamer.get_recent_events(5):
            print(f"  - {event.event_type.value}: {event.timestamp}")
    
    asyncio.run(demo())