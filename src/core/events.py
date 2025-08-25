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
    
    def __init__(self, logger=None):
        self.logger = logger
        self._subscribers: Dict[EventType, List[Callable]] = {}
        
        if self.logger:
            self.logger.debug("EventBus.__init__: EventBus initialized")
            self.logger.info("EventBus.__init__: Event system ready for subscriptions")
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Subscribe to an event type"""
        if self.logger:
            self.logger.debug(f"EventBus.subscribe: Subscribing to event type: {event_type.value}")
        
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
            if self.logger:
                self.logger.debug(f"EventBus.subscribe: Created new subscriber list for {event_type.value}")
        
        self._subscribers[event_type].append(callback)
        
        total_subscribers = len(self._subscribers[event_type])
        if self.logger:
            self.logger.info(f"EventBus.subscribe: Added subscriber for {event_type.value} (total: {total_subscribers})")
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Unsubscribe from an event type"""
        if self.logger:
            self.logger.debug(f"EventBus.unsubscribe: Unsubscribing from event type: {event_type.value}")
        
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                remaining_subscribers = len(self._subscribers[event_type])
                if self.logger:
                    self.logger.info(f"EventBus.unsubscribe: Removed subscriber from {event_type.value} (remaining: {remaining_subscribers})")
            except ValueError:
                if self.logger:
                    self.logger.warning(f"EventBus.unsubscribe: Callback not found for {event_type.value}")
        else:
            if self.logger:
                self.logger.warning(f"EventBus.unsubscribe: No subscribers found for event type: {event_type.value}")
    
    def emit(self, event: Event):
        """Emit an event to all subscribers"""
        if self.logger:
            self.logger.debug(f"EventBus.emit: Emitting event {event.type.value} from {event.source}")
        
        if event.type in self._subscribers:
            subscribers = self._subscribers[event.type]
            if self.logger:
                self.logger.debug(f"EventBus.emit: Found {len(subscribers)} subscribers for {event.type.value}")
            
            for i, callback in enumerate(subscribers):
                try:
                    if self.logger:
                        self.logger.debug(f"EventBus.emit: Calling subscriber {i+1}/{len(subscribers)} for {event.type.value}")
                    
                    callback(event)
                    
                    if self.logger:
                        self.logger.debug(f"EventBus.emit: Subscriber {i+1} handled {event.type.value} successfully")
                        
                except Exception as e:
                    # Log error but don't stop other subscribers
                    error_msg = f"EventBus.emit: Error in event subscriber {i+1} for {event.type.value}: {e}"
                    
                    if self.logger:
                        self.logger.error(error_msg, extra={
                            "error_type": type(e).__name__,
                            "event_type": event.type.value,
                            "event_source": event.source,
                            "subscriber_index": i,
                            "event_data": event.data
                        })
                    else:
                        print(error_msg)
            
            if self.logger:
                self.logger.info(f"EventBus.emit: Event {event.type.value} processed by {len(subscribers)} subscribers")
        else:
            if self.logger:
                self.logger.debug(f"EventBus.emit: No subscribers found for event type: {event.type.value}")
    
    def emit_sync(self, event_type: EventType, source: str, **data):
        """Create and emit an event synchronously"""
        if self.logger:
            self.logger.debug(f"EventBus.emit_sync: Creating and emitting {event_type.value} from {source}")
            if data:
                self.logger.debug(f"EventBus.emit_sync: Event data keys: {list(data.keys())}")
        
        try:
            event = Event.create(event_type, source, **data)
            
            if self.logger:
                self.logger.debug(f"EventBus.emit_sync: Event created with timestamp: {event.timestamp}")
            
            self.emit(event)
            
            if self.logger:
                self.logger.info(f"EventBus.emit_sync: Successfully emitted {event_type.value} from {source}")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"EventBus.emit_sync: Error creating/emitting event {event_type.value} from {source}: {e}", extra={
                    "error_type": type(e).__name__,
                    "event_type": event_type.value,
                    "source": source,
                    "data": data
                })
            raise