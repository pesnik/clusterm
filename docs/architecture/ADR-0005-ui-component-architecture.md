# ADR-0005: UI Component Architecture

## Status
Accepted

## Context
The original ClusterM UI was implemented as a single large class with all components mixed together. This approach creates several problems:

- **Reusability**: UI components cannot be reused in different contexts
- **Testing**: UI components are difficult to test in isolation
- **Maintainability**: Large UI classes are hard to understand and modify
- **Consistency**: No standard patterns for similar UI elements
- **Extensibility**: Adding new UI features requires modifying existing code

A modular UI component architecture is needed to create maintainable, reusable, and testable interface elements.

## Decision
Implement a modular UI component architecture using Textual with the following structure:

### Component Hierarchy
```
src/ui/
├── app.py              # Main application
├── screens.py          # Screen containers
└── components/         # Reusable components
    ├── tables.py       # Resource tables
    ├── panels.py       # Information panels
    └── modals.py       # Dialog boxes
```

### Component Types

#### 1. Tables (Specialized DataTables)
```python
class ResourceTable(DataTable):
    """Base class for all resource tables"""
    resource_type = reactive("", recompute=False)
    selected_resource = reactive(None, recompute=False)
    
    def update_data(self, resources: List[Dict[str, Any]])
    def _extract_row_data(self, resource: Dict[str, Any]) -> List[str]
```

#### 2. Panels (Information Display)
```python
class LogPanel(Container):
    """Enhanced log panel with filtering and controls"""
    max_lines = reactive(5000, recompute=False)
    show_timestamps = reactive(True, recompute=False)
    
    def write_log(self, message: str, level: str = "INFO")
    def filter_logs(self, level: Optional[str] = None)
```

#### 3. Modals (Dialog Interactions)
```python
class CommandModal(ModalScreen):
    """Modal for executing kubectl/helm commands"""
    def compose(self) -> ComposeResult
    def handle_result(self) -> Tuple[str, Any]
```

### Design Principles
1. **Single Responsibility**: Each component handles one specific UI concern
2. **Reusability**: Components can be used in multiple contexts
3. **Composition**: Complex interfaces built from simple components
4. **Event-Driven**: Components communicate through events, not direct calls
5. **Reactive**: Components automatically update when data changes
6. **Testable**: Components can be tested independently

## Consequences

### Positive
- **Maintainability**: Smaller, focused components are easier to understand
- **Reusability**: Components can be used in multiple screens and contexts
- **Testability**: Components can be unit tested in isolation
- **Consistency**: Standard patterns ensure consistent user experience
- **Extensibility**: New components follow established patterns
- **Performance**: Components only update when their data changes

### Negative
- **Complexity**: More files and classes to manage
- **Learning Curve**: Developers need to understand component architecture
- **Over-abstraction**: Risk of creating unnecessary component layers

## Alternatives Considered

### 1. Monolithic UI Classes
- **Pros**: Simple, everything in one place
- **Cons**: Poor maintainability, not reusable, hard to test

### 2. Function-based Components
- **Pros**: Simple, lightweight
- **Cons**: No state management, limited reusability

### 3. External UI Framework
- **Pros**: Rich features, mature ecosystem
- **Cons**: Additional complexity, learning curve, dependencies

## Implementation Details

### Component Base Classes

#### ResourceTable Specializations
```python
class DeploymentTable(ResourceTable):
    def __init__(self, **kwargs):
        columns = ["Name", "Status", "Replicas", "Age", "Namespace"]
        super().__init__("deployment", columns, **kwargs)
    
    def _extract_row_data(self, deployment: Dict[str, Any]) -> List[str]:
        # Extract deployment-specific data for table display
        return [name, status, replicas, age, namespace]

class PodTable(ResourceTable):
    # Similar pattern for pods
    
class ServiceTable(ResourceTable):
    # Similar pattern for services
```

#### Panel Components
```python
class StatusPanel(Container):
    cluster_status = reactive("Unknown", recompute=False)
    connection_status = reactive("Disconnected", recompute=False)
    
    def update_cluster_status(self, cluster_name: str, connected: bool):
        self.cluster_status = cluster_name or "No Cluster"
        self.connection_status = "Connected" if connected else "Disconnected"
        # Update UI elements automatically
```

#### Modal Components
```python
class ConfigModal(ModalScreen):
    def __init__(self, chart_name: str, chart_values: Optional[Dict] = None):
        super().__init__()
        self.chart_name = chart_name
        self.chart_values = chart_values or {}
    
    def compose(self) -> ComposeResult:
        # Build modal UI
        yield Container(
            Static(f"Configure {self.chart_name}"),
            # ... configuration inputs
            Button("Deploy", id="deploy-btn"),
            Button("Cancel", id="cancel-btn")
        )
```

### Component Communication

#### Event-Based Updates
```python
class MainScreen(Screen):
    def _on_cluster_changed(self, event):
        # Update all components that care about cluster changes
        self._refresh_all_data()
        self._update_status_panel()
```

#### Reactive Properties
```python
class ResourceTable(DataTable):
    selected_resource = reactive(None, recompute=False)
    
    def watch_selected_resource(self, old_value, new_value):
        # Automatically called when selection changes
        if new_value:
            self.emit_selection_event(new_value)
```

### Component Styling

#### CSS Organization
```css
/* Global component styles */
.panel {
    border: solid $primary;
    margin: 1;
    padding: 1;
}

/* Specific component styles */
#status-panel {
    height: 3;
    dock: top;
    background: $surface;
}

.status-value.connected {
    color: $success;
}

.status-value.disconnected {
    color: $error;
}
```

### Component Testing

#### Unit Tests
```python
def test_deployment_table_data_extraction():
    table = DeploymentTable()
    deployment_data = {
        "metadata": {"name": "test-app", "namespace": "default"},
        "status": {"replicas": 3, "readyReplicas": 2}
    }
    
    row_data = table._extract_row_data(deployment_data)
    
    assert row_data[0] == "test-app"  # name
    assert "2/3" in row_data[2]       # replicas
```

#### Integration Tests
```python
def test_screen_component_interaction():
    screen = MainScreen(mock_k8s_manager, mock_config, mock_event_bus, mock_logger)
    
    # Simulate cluster change
    screen._on_cluster_changed(Event.create(
        EventType.CLUSTER_CHANGED,
        "test",
        new_cluster="test-cluster"
    ))
    
    # Verify components updated
    status_panel = screen.query_one("#status-panel")
    assert "test-cluster" in status_panel.cluster_status
```

### Component Documentation

#### Component API
Each component documents:
- Purpose and use cases
- Required and optional parameters
- Events emitted and consumed
- CSS classes and styling hooks
- Example usage

#### Style Guide
- Component naming conventions
- CSS class naming patterns
- Event naming standards
- File organization rules

## Usage Patterns

### 1. Screen Composition
```python
class MainScreen(Screen):
    def compose(self):
        yield Header(show_clock=True)
        yield StatusPanel(id="status-panel")
        
        with TabbedContent():
            with TabPane("Deployments"):
                yield DeploymentTable(
                    id="deployments-table",
                    on_selection=self._on_resource_selected
                )
        
        yield LogPanel(id="log-panel")
        yield Footer()
```

### 2. Dynamic Component Creation
```python
def create_resource_table(resource_type: str) -> ResourceTable:
    table_classes = {
        "deployment": DeploymentTable,
        "pod": PodTable,
        "service": ServiceTable
    }
    
    table_class = table_classes.get(resource_type, ResourceTable)
    return table_class(id=f"{resource_type}-table")
```

### 3. Component Extension
```python
class CustomResourceTable(ResourceTable):
    """Extended table for custom resources"""
    
    def __init__(self, crd_definition: Dict, **kwargs):
        self.crd_definition = crd_definition
        columns = self._extract_columns_from_crd(crd_definition)
        super().__init__("custom", columns, **kwargs)
    
    def _extract_row_data(self, resource: Dict[str, Any]) -> List[str]:
        # Custom extraction logic based on CRD
        return self._extract_crd_data(resource, self.crd_definition)
```

## Future Enhancements
- Component library documentation
- Component visual testing
- Theme system integration
- Animation and transition support
- Accessibility features
- Component performance optimization

## Related ADRs
- ADR-0001: Modular Architecture
- ADR-0003: Event-Driven Architecture
- ADR-0004: Configuration Management