# ADR-0003: Event-Driven Architecture

## Status
Accepted

## Context
In a modular application like ClusterM, components need to communicate and react to changes without tight coupling. Traditional approaches like direct method calls create dependencies that make testing difficult and reduce flexibility.

Key scenarios requiring component communication:
- Cluster changes should update UI displays
- Deployment operations should refresh resource lists
- Configuration changes should propagate to all components
- Plugin actions should notify other parts of the system

## Decision
Implement an event-driven architecture using a central event bus with the following characteristics:

### Event Bus Design
```python
class EventBus:
    def subscribe(self, event_type: EventType, callback: Callable)
    def unsubscribe(self, event_type: EventType, callback: Callable)
    def emit(self, event: Event)
    def emit_sync(self, event_type: EventType, source: str, **data)
```

### Event Structure
```python
@dataclass
class Event:
    type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: float
```

### Standard Event Types
```python
class EventType(Enum):
    CLUSTER_CHANGED = "cluster_changed"
    DEPLOYMENT_UPDATED = "deployment_updated"
    NAMESPACE_CHANGED = "namespace_changed"
    POD_STATUS_CHANGED = "pod_status_changed"
    CONFIG_UPDATED = "config_updated"
    COMMAND_EXECUTED = "command_executed"
    ERROR_OCCURRED = "error_occurred"
```

### Communication Patterns
1. **Publisher-Subscriber**: Components subscribe to events they care about
2. **Fire-and-Forget**: Publishers emit events without caring about subscribers
3. **Async Processing**: Events can trigger asynchronous operations
4. **Error Isolation**: Event handling errors don't affect publishers

## Consequences

### Positive
- **Loose Coupling**: Components don't need direct references to each other
- **Flexibility**: New components can easily integrate by subscribing to events
- **Testability**: Components can be tested in isolation using mock event buses
- **Extensibility**: Plugins can react to core application events
- **Maintainability**: Changes to one component don't require changes to others
- **Debuggability**: Central event log shows system-wide interactions

### Negative
- **Complexity**: Additional abstraction layer to understand
- **Debugging**: Event flow can be harder to trace than direct calls
- **Performance**: Small overhead for event processing
- **Event Versioning**: Need to maintain event structure compatibility

## Alternatives Considered

### 1. Direct Method Calls
- **Pros**: Simple, direct, fast
- **Cons**: Tight coupling, hard to test, inflexible

### 2. Observer Pattern
- **Pros**: Standard pattern, direct notification
- **Cons**: Still creates coupling, harder to extend

### 3. Message Queue (Redis, RabbitMQ)
- **Pros**: Very robust, persistent
- **Cons**: Over-engineered for single-process TUI, external dependency

## Implementation Details

### Event Bus Singleton
```python
# Single event bus instance shared across application
event_bus = EventBus()
```

### Event Subscription Patterns
```python
# Component initialization
class SomeComponent:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe(EventType.CLUSTER_CHANGED, self._handle_cluster_change)
    
    def _handle_cluster_change(self, event: Event):
        cluster_name = event.data.get('new_cluster')
        self.refresh_data_for_cluster(cluster_name)
```

### Event Emission
```python
# Synchronous emission (immediate processing)
self.event_bus.emit_sync(
    EventType.CLUSTER_CHANGED,
    "cluster_manager",
    old_cluster="cluster-1",
    new_cluster="cluster-2"
)

# Async emission (future enhancement)
await self.event_bus.emit_async(event)
```

### Error Handling
```python
def emit(self, event: Event):
    for callback in self._subscribers.get(event.type, []):
        try:
            callback(event)
        except Exception as e:
            # Log error but don't stop other subscribers
            logger.error(f"Error in event subscriber: {e}")
```

### Event Logging
All events are logged for debugging and monitoring:
```
[12:34:56] EVENT cluster_changed: cluster_manager -> {"old_cluster": "dev", "new_cluster": "prod"}
[12:34:57] EVENT deployment_updated: k8s_manager -> {"chart": "webapp", "status": "deployed"}
```

## Usage Patterns

### 1. UI Updates
```python
# K8s manager emits deployment update
self.event_bus.emit_sync(EventType.DEPLOYMENT_UPDATED, "k8s_manager", chart="webapp")

# UI components react automatically
def _on_deployment_updated(self, event):
    self.refresh_deployments_table()
```

### 2. Plugin Integration
```python
# Plugin subscribes to events
self.event_bus.subscribe(EventType.POD_STATUS_CHANGED, self.send_alert)

# Core system emits events
self.event_bus.emit_sync(EventType.POD_STATUS_CHANGED, "monitor", pod="webapp-123", status="Failed")
```

### 3. Configuration Changes
```python
# Config manager notifies changes
self.event_bus.emit_sync(EventType.CONFIG_UPDATED, "config", key="theme", value="light")

# UI responds to theme change
def _on_config_updated(self, event):
    if event.data['key'] == 'theme':
        self.update_theme(event.data['value'])
```

### Event Documentation
Each event type is documented with:
- Purpose and trigger conditions
- Data structure and fields
- Example usage
- Backward compatibility notes

## Testing Strategy
```python
# Mock event bus for unit tests
mock_event_bus = Mock(spec=EventBus)

# Verify event emissions
mock_event_bus.emit_sync.assert_called_with(
    EventType.CLUSTER_CHANGED,
    "test_component",
    cluster="test-cluster"
)

# Test event handling
component._handle_cluster_change(Event.create(
    EventType.CLUSTER_CHANGED,
    "test",
    cluster="test-cluster"
))
```

## Future Enhancements
- Event filtering and routing rules
- Event persistence for replay/debugging
- Event metrics and monitoring
- Cross-process events (if needed)
- Event validation and schemas

## Related ADRs
- ADR-0001: Modular Architecture
- ADR-0002: Plugin System
- ADR-0004: Configuration Management