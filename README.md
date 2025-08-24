# ClusterM - Kubernetes Deployment Manager TUI

A robust, modular, and extensible Terminal User Interface (TUI) application for managing Kubernetes deployments. Built with Python and Textual, ClusterM provides an intuitive interface for cluster management, resource monitoring, and Helm chart deployments.

## Features

### 🚀 Core Features
- **Multi-Cluster Management**: Switch between multiple Kubernetes clusters seamlessly
- **Resource Monitoring**: Real-time viewing of deployments, pods, services, and namespaces
- **Helm Integration**: Deploy and manage Helm charts with interactive configuration
- **Command Execution**: Execute kubectl and helm commands directly from the interface
- **Log Viewing**: Access pod logs and command output in dedicated viewers

### 🏗️ Architecture Features
- **Modular Design**: Clean separation of concerns with dedicated modules
- **Plugin System**: Extensible architecture for custom functionality
- **Event-Driven**: Reactive updates through a central event bus
- **Configuration Management**: Centralized, persistent configuration system
- **Comprehensive Logging**: Structured logging with multiple output targets
- **Testing Framework**: Built-in testing infrastructure with pytest

## Installation

### Prerequisites
- Python 3.11 or higher
- kubectl binary
- helm binary (optional, for Helm functionality)

### Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -r requirements.txt
```

For development:
```bash
pip install -e .[dev]
```

## Project Structure

```
clusterm/
├── src/
│   ├── core/                 # Core infrastructure
│   │   ├── config.py        # Configuration management
│   │   ├── events.py        # Event system
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── logger.py        # Logging infrastructure
│   ├── k8s/                 # Kubernetes operations
│   │   ├── manager.py       # Main K8s manager
│   │   ├── cluster.py       # Cluster management
│   │   ├── resources.py     # Resource operations
│   │   └── commands.py      # Command execution
│   ├── plugins/             # Plugin system
│   │   ├── manager.py       # Plugin manager
│   │   ├── base.py          # Plugin base classes
│   │   └── builtin/         # Built-in plugins
│   └── ui/                  # User interface
│       ├── app.py           # Main application
│       ├── screens.py       # Screen components
│       └── components/      # Reusable UI components
│           ├── tables.py    # Resource tables
│           ├── panels.py    # UI panels
│           └── modals.py    # Modal dialogs
├── tests/                   # Test suite
├── main.py                  # Application entry point
└── pyproject.toml          # Project configuration
```

## Usage

### Basic Usage

Run ClusterM with default configuration:
```bash
python main.py
```

Run with custom configuration:
```bash
python main.py /path/to/config.yaml
```

### Keyboard Shortcuts

- `q` - Quit application
- `r` - Refresh all data
- `c` - Switch cluster
- `t` - Test cluster connection
- `x` - Execute command
- `d` - Deploy selected chart
- `Ctrl+L` - Clear logs

### Directory Structure

ClusterM expects the following directory structure for Kubernetes resources:

```
/app/k8s/                    # Base K8s directory (configurable)
├── clusters/                # Cluster configurations
│   ├── cluster1/
│   │   └── kubeconfig.yaml
│   └── cluster2/
│       └── config
├── tools/                   # Binary tools
│   ├── kubectl
│   └── helm
└── projects/
    └── helm-charts/         # Helm charts
        ├── app1/
        │   ├── Chart.yaml
        │   └── values.yaml
        └── app2/
            ├── Chart.yaml
            └── values.yaml
```

## Configuration

ClusterM uses a YAML configuration file located at `~/.clusterm/config.yaml` by default.

### Default Configuration

```yaml
app:
  theme: dark
  auto_refresh: true
  refresh_interval: 30
  log_level: INFO

k8s:
  base_path: /app
  default_namespace: default
  kubectl_timeout: 30
  helm_timeout: 60

ui:
  show_timestamps: true
  table_max_rows: 1000
  log_max_lines: 5000

plugins:
  enabled: []
  plugin_paths: []
```

### Customization

You can customize ClusterM behavior by:

1. **Configuration File**: Modify `~/.clusterm/config.yaml`
2. **Environment Variables**: Override specific settings
3. **Command Line Arguments**: Pass custom config path
4. **Plugins**: Extend functionality with custom plugins

## Plugin Development

ClusterM supports custom plugins for extending functionality. Create a plugin by:

1. Create a plugin directory: `~/.clusterm/plugins/my-plugin/`
2. Add a `plugin.py` file with your plugin class:

```python
from src.plugins.base import BasePlugin, PluginMetadata

class Plugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            description="My custom plugin",
            author="Your Name"
        )
    
    def initialize(self) -> bool:
        # Plugin initialization logic
        return True
    
    def cleanup(self):
        # Plugin cleanup logic
        pass
```

3. Enable the plugin in your config:

```yaml
plugins:
  enabled:
    - my-plugin
```

## Development

### Running Tests

```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src
```

### Code Quality

Format code:
```bash
ruff format
```

Lint code:
```bash
ruff check
```

Type checking:
```bash
mypy src
```

### Development Setup

1. Clone the repository
2. Install dependencies: `uv sync`
3. Install pre-commit hooks: `pre-commit install`
4. Run tests: `pytest`

## Architecture

### Core Principles

1. **Modularity**: Each component has a single responsibility
2. **Extensibility**: Plugin system allows custom functionality
3. **Reactive**: Event-driven architecture for real-time updates
4. **Configuration**: Centralized, persistent configuration management
5. **Testing**: Comprehensive test coverage with isolated components

### Component Interaction

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│     UI      │    │    Core     │    │     K8s     │
│  ┌───────┐  │    │ ┌─────────┐ │    │ ┌─────────┐ │
│  │Screen │  │◄──►│ │EventBus │ │◄──►│ │Manager  │ │
│  │       │  │    │ │         │ │    │ │         │ │
│  └───────┘  │    │ │Config   │ │    │ │Cluster  │ │
│  ┌───────┐  │    │ │         │ │    │ │         │ │
│  │Modal  │  │    │ │Logger   │ │    │ │Commands │ │
│  └───────┘  │    │ └─────────┘ │    │ └─────────┘ │
└─────────────┘    └─────────────┘    └─────────────┘
       ▲                   ▲                   ▲
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                   ┌─────────────┐
                   │   Plugins   │
                   │ ┌─────────┐ │
                   │ │Manager  │ │
                   │ │         │ │
                   │ │Plugin1  │ │
                   │ │         │ │
                   │ │Plugin2  │ │
                   │ └─────────┘ │
                   └─────────────┘
```

## Troubleshooting

### Common Issues

1. **kubectl not found**: Ensure kubectl is in `/app/k8s/tools/kubectl`
2. **No clusters found**: Check cluster directories in `/app/k8s/clusters/`
3. **Connection failed**: Verify kubeconfig files are valid
4. **Charts not showing**: Ensure Helm charts are in `/app/k8s/projects/helm-charts/`

### Debug Mode

Enable debug logging in your config:

```yaml
app:
  log_level: DEBUG
```

### Logs Location

- Application logs: `~/.clusterm/logs/clusterm.log`
- Configuration: `~/.clusterm/config.yaml`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

### Version 0.2.0
- [ ] Resource editing capabilities
- [ ] Custom resource definitions (CRDs) support
- [ ] Enhanced filtering and searching
- [ ] Metrics and monitoring integration

### Version 0.3.0
- [ ] Multi-context support
- [ ] Backup and restore functionality
- [ ] Advanced Helm operations
- [ ] Resource templates

## Support

For support, issues, or feature requests, please open an issue on the GitHub repository.