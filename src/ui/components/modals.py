"""
Modal dialog components
"""

from typing import Dict, Any, Optional, List
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Static, Label, Input, Select, Switch, Log
from textual.binding import Binding
from textual import on


class CommandModal(ModalScreen):
    """Modal for executing kubectl/helm commands"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.result = None
    
    def compose(self):
        """Compose the command modal"""
        with Container(classes="modal"):
            yield Static("⚡ Execute Command", classes="modal-title")
            
            with Vertical(classes="modal-content"):
                yield Label("Command:", classes="input-label")
                yield Input(
                    placeholder="e.g., kubectl get pods --all-namespaces, helm list", 
                    id="command-input"
                )
                
                yield Static("💡 Examples:", classes="examples-title")
                yield Static(
                    "kubectl get pods, kubectl get services, kubectl describe pod <podname>\n"
                    "helm list, helm status <release-name>, helm history <release-name>",
                    classes="command-examples"
                )
                
                yield Static("ℹ️ Command type (kubectl/helm) will be auto-detected", classes="auto-detect-info")
            
            with Horizontal(classes="modal-buttons"):
                yield Button("⚡ Execute", variant="primary", id="execute-btn")
                yield Button("❌ Cancel (Esc)", variant="default", id="cancel-btn")
    
    @on(Button.Pressed, "#execute-btn")
    def execute_pressed(self):
        """Handle execute button press"""
        full_command = self.query_one("#command-input").value.strip()
        
        if full_command:
            # Auto-detect command type and extract args
            cmd_type, cmd_args = self._parse_command(full_command)
            self.result = ("execute", cmd_type, cmd_args)
        else:
            self.result = ("cancel", None, None)
        
        self.dismiss(self.result)
    
    def _parse_command(self, full_command: str):
        """Parse full command to detect type and extract arguments"""
        command_lower = full_command.lower().strip()
        
        if command_lower.startswith('kubectl'):
            # Remove 'kubectl' from the beginning and return the rest as args
            cmd_args = full_command[7:].strip()  # Remove 'kubectl'
            return "kubectl", cmd_args
        elif command_lower.startswith('helm'):
            # Remove 'helm' from the beginning and return the rest as args
            cmd_args = full_command[4:].strip()  # Remove 'helm'
            return "helm", cmd_args
        else:
            # Try to infer from common patterns, default to kubectl
            if any(keyword in command_lower for keyword in ['get pods', 'get services', 'describe', 'logs', 'exec']):
                return "kubectl", full_command
            elif any(keyword in command_lower for keyword in ['install', 'upgrade', 'list', 'status', 'uninstall']):
                return "helm", full_command
            else:
                # Default to kubectl and let user prefix with kubectl if needed
                return "kubectl", full_command
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self):
        """Handle cancel button press"""
        self.result = ("cancel", None, None)
        self.dismiss(self.result)
    
    def action_dismiss(self):
        """Handle escape key - same as cancel"""
        self.result = ("cancel", None, None)
        self.dismiss(self.result)


class ConfigModal(ModalScreen):
    """Modal for configuring deployment parameters"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]
    
    def __init__(self, chart_name: str, chart_values: Optional[Dict] = None):
        super().__init__()
        self.chart_name = chart_name
        self.chart_values = chart_values or {}
        self.result = None
    
    def compose(self):
        """Compose the configuration modal"""
        with Container(classes="modal"):
            yield Static(f"⚙️ Configure {self.chart_name}", classes="modal-title")
            
            with Vertical(classes="modal-content"):
                yield Label("Namespace:")
                yield Input(
                    value=self.chart_values.get("namespace", "default"),
                    placeholder="default", 
                    id="namespace-input"
                )
                
                yield Label("Replicas:")
                yield Input(
                    value=str(self.chart_values.get("replicas", "1")),
                    placeholder="1", 
                    id="replicas-input"
                )
                
                yield Label("Environment:")
                yield Select([
                    ("development", "dev"), 
                    ("staging", "staging"), 
                    ("production", "prod")
                ], value=self.chart_values.get("environment", "development"), id="env-select")
                
                yield Label("Enable Monitoring:")
                yield Switch(
                    value=self.chart_values.get("monitoring", False),
                    id="monitoring-switch"
                )
            
            with Horizontal(classes="modal-buttons"):
                yield Button("Deploy", variant="primary", id="deploy-btn")
                yield Button("Cancel (Esc)", variant="default", id="cancel-btn")
    
    @on(Button.Pressed, "#deploy-btn")
    def deploy_pressed(self):
        """Handle deploy button press"""
        config = {
            "namespace": self.query_one("#namespace-input").value or "default",
            "replicas": self.query_one("#replicas-input").value or "1",
            "environment": self.query_one("#env-select").value,
            "monitoring": self.query_one("#monitoring-switch").value
        }
        self.result = ("deploy", self.chart_name, config)
        self.dismiss(self.result)
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self):
        """Handle cancel button press"""
        self.result = ("cancel", None, None)
        self.dismiss(self.result)
    
    def action_dismiss(self):
        """Handle escape key - same as cancel"""
        self.result = ("cancel", None, None)
        self.dismiss(self.result)


class LogModal(ModalScreen):
    """Modal for displaying logs and command output"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close", priority=True),
        Binding("enter", "dismiss", "Close", priority=True),
    ]
    
    def __init__(self, title: str, content: str, syntax: Optional[str] = None):
        super().__init__()
        self.title = title
        self.content = content
        self.syntax = syntax
    
    def compose(self):
        """Compose the log modal"""
        with Container(classes="modal large-modal"):
            yield Static(self.title, classes="modal-title")
            yield Log(highlight=True, id="log-content")
            yield Button("Close (Esc)", id="close-btn", classes="modal-close-btn")
    
    def on_mount(self):
        """Populate log content when modal mounts"""
        log_widget = self.query_one("#log-content", Log)
        for line in self.content.split('\n'):
            log_widget.write_line(line)
    
    @on(Button.Pressed, "#close-btn")
    def close_pressed(self):
        """Handle close button press"""
        self.dismiss()
    
    def action_dismiss(self):
        """Handle escape/enter key - close modal"""
        self.dismiss()


class AddCommandModal(ModalScreen):
    """Modal for adding new commands to CommandPad"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.result = None
    
    def compose(self):
        """Compose the add command modal"""
        with Container(classes="modal"):
            yield Static("➕ Add New Command", classes="modal-title")
            
            with Vertical(classes="modal-content"):
                yield Label("Command:", classes="input-label")
                yield Input(
                    placeholder="e.g., kubectl get pods -n production",
                    id="command-input"
                )
                
                yield Label("Description:", classes="input-label")
                yield Input(
                    placeholder="e.g., Get all pods in production namespace",
                    id="description-input"
                )
                
                yield Label("Tags (comma separated):", classes="input-label")
                yield Input(
                    placeholder="e.g., kubectl, pods, production",
                    id="tags-input"
                )
                
                yield Label("Command Type:", classes="input-label")
                yield Select([
                    ("⚡ kubectl", "kubectl"),
                    ("🚢 Helm", "helm"),
                    ("🐳 Docker", "docker"),
                    ("📦 Git", "git"),
                    ("💻 General", "general")
                ], value="kubectl", id="type-select")
            
            with Horizontal(classes="modal-buttons"):
                yield Button("➕ Add Command", variant="primary", id="add-btn")
                yield Button("❌ Cancel (Esc)", variant="default", id="cancel-btn")
    
    @on(Button.Pressed, "#add-btn")
    def add_pressed(self):
        """Handle add button press"""
        command = self.query_one("#command-input").value.strip()
        description = self.query_one("#description-input").value.strip()
        tags_input = self.query_one("#tags-input").value.strip()
        command_type = self.query_one("#type-select").value
        
        if command:
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
            self.result = ("add", {
                "command": command,
                "description": description or f"Execute {command}",
                "tags": tags,
                "command_type": command_type
            })
        else:
            self.result = ("cancel", None)
        
        self.dismiss(self.result)
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self):
        """Handle cancel button press"""
        self.result = ("cancel", None)
        self.dismiss(self.result)
    
    def action_dismiss(self):
        """Handle escape key - same as cancel"""
        self.result = ("cancel", None)
        self.dismiss(self.result)


class EditCommandModal(ModalScreen):
    """Modal for editing existing commands in CommandPad"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]
    
    def __init__(self, command_entry):
        super().__init__()
        self.command_entry = command_entry
        self.result = None
    
    def compose(self):
        """Compose the edit command modal"""
        with Container(classes="modal"):
            yield Static("✏️ Edit Command", classes="modal-title")
            
            with Vertical(classes="modal-content"):
                yield Label("Command:", classes="input-label")
                yield Input(
                    value=self.command_entry.command,
                    id="command-input"
                )
                
                yield Label("Description:", classes="input-label")
                yield Input(
                    value=self.command_entry.description,
                    id="description-input"
                )
                
                yield Label("Tags (comma separated):", classes="input-label")
                tags_value = ", ".join(self.command_entry.tags) if self.command_entry.tags else ""
                yield Input(
                    value=tags_value,
                    id="tags-input"
                )
                
                yield Label("Command Type:", classes="input-label")
                yield Select([
                    ("⚡ kubectl", "kubectl"),
                    ("🚢 Helm", "helm"),
                    ("🐳 Docker", "docker"),
                    ("📦 Git", "git"),
                    ("💻 General", "general")
                ], value=self.command_entry.command_type or "kubectl", id="type-select")
            
            with Horizontal(classes="modal-buttons"):
                yield Button("💾 Save Changes", variant="primary", id="save-btn")
                yield Button("❌ Cancel (Esc)", variant="default", id="cancel-btn")
    
    @on(Button.Pressed, "#save-btn")
    def save_pressed(self):
        """Handle save button press"""
        command = self.query_one("#command-input").value.strip()
        description = self.query_one("#description-input").value.strip()
        tags_input = self.query_one("#tags-input").value.strip()
        command_type = self.query_one("#type-select").value
        
        if command:
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
            self.result = ("save", {
                "original_command": self.command_entry.command,
                "command": command,
                "description": description or f"Execute {command}",
                "tags": tags,
                "command_type": command_type
            })
        else:
            self.result = ("cancel", None)
        
        self.dismiss(self.result)
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self):
        """Handle cancel button press"""
        self.result = ("cancel", None)
        self.dismiss(self.result)
    
    def action_dismiss(self):
        """Handle escape key - same as cancel"""
        self.result = ("cancel", None)
        self.dismiss(self.result)


class ClusterSwitchModal(ModalScreen):
    """Modal for switching between clusters"""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]
    
    def __init__(self, clusters: List[Dict[str, Any]], current_cluster: Optional[str] = None):
        super().__init__()
        self.clusters = clusters
        self.current_cluster = current_cluster
        self.result = None
    
    def compose(self):
        """Compose the cluster switch modal"""
        with Container(classes="modal"):
            yield Static("🔄 Switch Cluster", classes="modal-title")
            
            with Vertical(classes="modal-content"):
                if self.current_cluster:
                    yield Static(f"Current: {self.current_cluster}", classes="current-cluster")
                
                yield Label("Available Clusters:")
                
                cluster_options = [
                    (cluster["name"], cluster["name"]) 
                    for cluster in self.clusters
                ]
                yield Select(cluster_options, id="cluster-select")
            
            with Horizontal(classes="modal-buttons"):
                yield Button("Switch", variant="primary", id="switch-btn")
                yield Button("Test Connection", variant="default", id="test-btn")
                yield Button("Cancel (Esc)", variant="default", id="cancel-btn")
    
    @on(Button.Pressed, "#switch-btn")
    def switch_pressed(self):
        """Handle switch button press"""
        selected_cluster = self.query_one("#cluster-select").value
        self.result = ("switch", selected_cluster)
        self.dismiss(self.result)
    
    @on(Button.Pressed, "#test-btn")
    def test_pressed(self):
        """Handle test connection button press"""
        selected_cluster = self.query_one("#cluster-select").value
        self.result = ("test", selected_cluster)
        self.dismiss(self.result)
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self):
        """Handle cancel button press"""
        self.result = ("cancel", None)
        self.dismiss(self.result)
    
    def action_dismiss(self):
        """Handle escape key - same as cancel"""
        self.result = ("cancel", None)
        self.dismiss(self.result)