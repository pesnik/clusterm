"""
Event system for ClusterM - enables loose coupling between components
"""

from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """Standard event types"""
    CLUSTER_CHANGED = "cluster_changed"
    DEPLOYMENT_UPDATED = "deployment_updated"
    NAMESPACE_CHANGED = "namespace_changed"
    POD_STATUS_CHANGED = "pod_status_changed"
    CONFIG_UPDATED = "config_updated"
    COMMAND_EXECUTED = "command_executed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Event:
    """Event data structure"""
    type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: float
    
    @classmethod
    def create(cls, event_type: EventType, source: str, **data) -> 'Event':
        """Create a new event with current timestamp"""
        import time
        return cls(
            type=event_type,
            source=source,
            data=data,
            timestamp=time.time()
        )


class EventBus:
    """Central event bus for application-wide communication"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass
    
    def emit(self, event: Event):
        """Emit an event to all subscribers"""
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    # Log error but don't stop other subscribers
                    print(f"Error in event subscriber: {e}")
    
    def emit_sync(self, event_type: EventType, source: str, **data):
        """Create and emit an event synchronously"""
        event = Event.create(event_type, source, **data)
        self.emit(event)