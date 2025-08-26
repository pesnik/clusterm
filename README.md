# Clusterm - Kubernetes Deployment Manager TUI

A robust, modular, and extensible Terminal User Interface (TUI) application for managing Kubernetes deployments. Built with Python and Textual, Clusterm provides an intuitive interface for cluster management, resource monitoring, and Helm chart deployments.

## Features

### 🚀 Core Features
- **Multi-Cluster Management**: Switch between multiple Kubernetes clusters seamlessly
- **Resource Monitoring**: Real-time viewing of deployments, pods, services, and namespaces
- **Helm Integration**: Deploy and manage Helm charts with interactive configuration
- **Interactive Command Input**: Production-grade prompt_toolkit integration with real-time auto-completion
- **Smart Command Execution**: Execute kubectl and helm commands with auto-detection
- **Command Pad**: Context-aware command history that learns from your usage patterns
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

### Dependencies
- **textual**: Modern TUI framework
- **prompt-toolkit**: Advanced command-line interface
- **pyyaml**: YAML configuration support

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

### Quick Demo

Try the intelligent command input features:

```bash
# Run the interactive demo
python examples/intelligent_input_demo.py

# Or launch Clusterm and press Ctrl+I for Smart Input
python main.py
```

## First-Time Setup

Clusterm automatically handles initial setup for you:

### 1. **Automatic Directory Creation**
On first launch, Clusterm creates:
- `~/.clusterm/config.yaml` - Configuration file
- `~/.clusterm/k8s/` - Kubernetes resources directory
- Example configurations and help files

### 2. **Configure Your Clusters**
```bash
# Option 1: Copy existing kubeconfig
mkdir -p ~/.clusterm/k8s/clusters/my-cluster
cp ~/.kube/config ~/.clusterm/k8s/clusters/my-cluster/kubeconfig

# Option 2: Create symlink to existing config
mkdir -p ~/.clusterm/k8s/clusters/my-cluster
ln -s ~/.kube/config ~/.clusterm/k8s/clusters/my-cluster/kubeconfig

# Option 3: Multiple clusters with project organization
mkdir -p ~/.clusterm/k8s/clusters/production/projects/{default,monitoring,ingress}
mkdir -p ~/.clusterm/k8s/clusters/staging/projects/{default,development}
# Copy respective kubeconfig files to each cluster directory
cp ~/.kube/prod-config ~/.clusterm/k8s/clusters/production/kubeconfig  
cp ~/.kube/staging-config ~/.clusterm/k8s/clusters/staging/kubeconfig
```

### 3. **Tool Installation**
Clusterm automatically finds kubectl and helm from your system PATH:
```bash
# Install tools normally (recommended)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Clusterm will find them automatically
```

### 4. **Custom Path Configuration** (Optional)
Edit `~/.clusterm/config.yaml`:
```yaml
k8s:
  base_path: "/your/preferred/path"  # Default: ~/.clusterm/k8s
```

## Project Structure

```
clusterm/
├── src/
│   ├── core/                 # Core infrastructure
│   │   ├── config.py        # Configuration management
│   │   ├── events.py        # Event system
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── logger.py        # Logging infrastructure
│   │   ├── command_history.py # Command pad functionality
│   │   └── live_completions.py # Real-time completion provider
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
│           ├── modals.py    # Modal dialogs
│           ├── command_pad.py # Command pad component
│           └── interactive_command_input.py # Interactive input with prompt_toolkit
├── examples/                # Demo and example scripts
│   └── interactive_input_demo.py # Demo of interactive command input
├── tests/                   # Test suite
├── main.py                  # Application entry point
└── pyproject.toml          # Project configuration
```

## Usage

### Basic Usage

Run Clusterm with default configuration:
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
- `x` - Execute command (with smart auto-detection)
- `Ctrl+I` - Open intelligent command input (Smart Input tab)
- `d` - Deploy selected chart
- `Ctrl+L` - Clear logs

### Command Pad

The **Command Pad** is a revolutionary feature that learns from your kubectl and helm usage patterns:

- **Context-Aware**: Commands are stored per cluster and namespace combination
- **Smart Storage**: Only successful commands are saved to your history
- **Usage Tracking**: See which commands you use most frequently
- **Instant Reuse**: Click any command in your pad to execute it again
- **Real-time Search**: Quickly find commands with built-in search
- **Multiple Views**: Browse by Most Frequent, Recent, or All Commands

**Benefits:**
- ✅ **Zero Noise**: Only see commands relevant to your current cluster/namespace
- ✅ **Learn Your Patterns**: Commands adapt to your actual workflow
- ✅ **Save Time**: No more retyping complex commands
- ✅ **Context Switching**: Separate command histories for different environments

### Intelligent Command Input

The **Smart Input** feature provides a production-grade command-line experience with advanced auto-completion:

**🧠 Key Features:**
- **Real-time Auto-completion**: Live suggestions based on current cluster state
- **Context-Aware Completions**: Resource names, namespaces, and options from your actual cluster
- **Syntax Highlighting**: Color-coded commands for better readability
- **Command History Navigation**: Use ↑/↓ arrows to browse previous commands
- **Real-time Validation**: Instant feedback on command syntax and validity
- **Background Data Fetching**: Non-blocking updates of cluster resources (30s cache)
- **Hybrid Architecture**: Seamlessly integrated with Textual UI

**🚀 Supported Completions:**
- **kubectl**: All resources, namespaces, pod names, service names, output formats
- **helm**: Release names, chart repositories, common flags and values
- **Field Selectors**: metadata.name, status.phase, spec.nodeName, etc.
- **Output Formats**: json, yaml, wide, custom-columns, go-template
- **Common Flags**: --namespace, --all-namespaces, --watch, --follow

**💡 Usage:**
1. Press `Ctrl+I` or navigate to "Smart Input" tab
2. Start typing any kubectl or helm command
3. Use Tab for completions, ↑/↓ for history
4. Press Enter to execute the command
5. Results appear in the main interface

**Benefits:**
- ✅ **Production-Grade**: Built on prompt_toolkit with robust error handling
- ✅ **Live Data**: Completions reflect your actual cluster state
- ✅ **Non-blocking**: Background updates don't interrupt your workflow
- ✅ **Smart Caching**: Efficient resource fetching with TTL-based refresh
- ✅ **Graceful Degradation**: Works even when cluster is unreachable

### Directory Structure

Clusterm automatically creates and manages a directory structure for Kubernetes resources. By default, this is located at `~/.clusterm/k8s/`, but can be configured in your config file.

**Automatic Setup:**
- On first run, Clusterm creates all necessary directories
- Example configurations and README files are generated
- Directory structure is fully customizable via configuration

**Cluster-Aware Structure:**
```
~/.clusterm/k8s/             # Base K8s directory (configurable)
├── clusters/                # Cluster configurations  
│   ├── example-cluster/     # Auto-created example
│   │   ├── kubeconfig.example  # Instructions for setup
│   │   ├── projects/           # Namespace-organized projects
│   │   │   ├── default/       # Default namespace projects
│   │   │   │   └── nginx-app/ # Example web application
│   │   │   └── monitoring/    # Monitoring namespace projects  
│   │   │       └── prometheus-stack/ # Monitoring infrastructure
│   │   └── README.md          # Cluster-specific documentation
│   ├── production/          # Production cluster
│   │   ├── kubeconfig       # Production kubeconfig
│   │   └── projects/        # Production projects
│   │       ├── default/     # Production default namespace
│   │       │   ├── api-gateway/
│   │       │   └── web-frontend/
│   │       ├── monitoring/  # Production monitoring
│   │       │   ├── prometheus/
│   │       │   └── grafana/
│   │       └── ingress/     # Production ingress
│   │           └── nginx-ingress/
│   └── staging/             # Staging cluster
│       ├── kubeconfig       # Staging kubeconfig  
│       └── projects/        # Staging projects
│           ├── default/     # Staging default namespace
│           │   └── test-app/
│           └── development/ # Development namespace
│               └── debug-tools/
└── tools/                   # Optional: Local binary tools
    ├── kubectl              # Falls back to system PATH
    ├── helm                 # Falls back to system PATH  
    └── README.md            # Setup instructions
```

**Benefits of Cluster-Aware Structure:**

✅ **Context Filtering**: Only show projects relevant to current cluster/namespace selection  
✅ **Reduced Noise**: No irrelevant projects cluttering your workspace  
✅ **Environment Safety**: Prevents accidental cross-environment deployments  
✅ **Team Organization**: Clear separation of responsibilities and environments  
✅ **Professional Structure**: Industry-standard cluster/namespace organization  

**Path Configuration:**
```yaml
k8s:
  base_path: "/your/custom/path"  # Default: ~/.clusterm/k8s
```

### Working with Projects

**Adding Projects to Specific Contexts:**
```bash
# Add a chart to production/default namespace
mkdir -p ~/.clusterm/k8s/clusters/production/projects/default/my-api
# Copy your Helm chart files here

# Add monitoring stack to production/monitoring namespace  
mkdir -p ~/.clusterm/k8s/clusters/production/projects/monitoring/prometheus
# Copy monitoring charts here

# Development projects in staging cluster
mkdir -p ~/.clusterm/k8s/clusters/staging/projects/development/test-service
```

**Context-Aware Project Discovery:**
- Select `production` cluster + `default` namespace → see only production default projects
- Select `staging` cluster + `development` namespace → see only staging development projects  
- No more scrolling through irrelevant charts for other environments

## Configuration

Clusterm uses a YAML configuration file located at `~/.clusterm/config.yaml` by default.

### Default Configuration

```yaml
app:
  theme: dark
  auto_refresh: true
  refresh_interval: 30
  log_level: INFO

k8s:
  base_path: ~/.clusterm/k8s    # Fully configurable path
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

You can customize Clusterm behavior by:

1. **Configuration File**: Modify `~/.clusterm/config.yaml`
2. **Environment Variables**: Override specific settings
3. **Command Line Arguments**: Pass custom config path
4. **Plugins**: Extend functionality with custom plugins

## Plugin Development

Clusterm supports custom plugins for extending functionality. Create a plugin by:

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

1. **kubectl not found**: 
   - kubectl will be automatically found in system PATH
   - Alternatively, place binary at `~/.clusterm/k8s/tools/kubectl`
   - Configure custom path in `k8s.base_path`

2. **No clusters found**: 
   - Check cluster directories in `~/.clusterm/k8s/clusters/`
   - Each cluster needs a `kubeconfig` file
   - Use example files for setup guidance

3. **Connection failed**: 
   - Verify kubeconfig files are valid
   - Check cluster connectivity: `kubectl cluster-info`

4. **Charts not showing**: 
   - Charts are now organized by cluster and namespace: `~/.clusterm/k8s/clusters/{cluster}/projects/{namespace}/{chart}/`
   - Each chart needs `Chart.yaml` and `values.yaml`
   - Charts only appear when the matching cluster/namespace is selected

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

### Version 0.2.0 ✅ Released
- [x] **Command Pad** - Context-aware command history and reuse
- [x] **Smart Command Execution** - Auto-detection of kubectl/helm commands

### Version 0.3.0 ✅ Released
- [x] **Intelligent Command Input** - Production-grade prompt_toolkit integration
- [x] **Real-time Auto-completion** - Live cluster data with smart caching
- [x] **Context-Aware Completions** - Resource names and command suggestions
- [x] **Syntax Highlighting & Validation** - Enhanced command experience

### Version 0.4.0 🚧 In Progress
- [x] **Cluster-Aware Project Structure** - Context-based project organization
- [x] **Environment Safety** - Prevent cross-environment deployment accidents
- [ ] **Project Migration Tools** - Migrate existing projects to new structure
- [ ] **Enhanced Project Management** - Create, edit, and organize projects within app

### Version 0.5.0 (Planned)
- [ ] Resource editing capabilities
- [ ] Custom resource definitions (CRDs) support
- [ ] Enhanced filtering and searching
- [ ] Metrics and monitoring integration
- [ ] Multi-context support
- [ ] Backup and restore functionality
- [ ] Advanced Helm operations
- [ ] Resource templates

## Support

For support, issues, or feature requests, please open an issue on the GitHub repository.