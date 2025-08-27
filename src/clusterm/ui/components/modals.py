"""Modal dialog components
"""

from typing import Any

from textual import on
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Log, Select, Static, Switch


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
                    id="command-input",
                )

                yield Static("💡 Examples:", classes="examples-title")
                yield Static(
                    "kubectl get pods, kubectl get services, kubectl describe pod <podname>\n"
                    "helm list, helm status <release-name>, helm history <release-name>",
                    classes="command-examples",
                )

                yield Static("ℹ️ Command type (kubectl/helm) will be auto-detected", classes="auto-detect-info")

            with Horizontal(classes="modal-buttons"):
                yield Button("⚡ Execute", variant="primary", id="execute-btn")
                yield Button("❌ Cancel (Esc)", variant="default", id="cancel-btn")

    @on(Button.Pressed, "#execute-btn")
    def execute_pressed(self):
        """Handle execute button press"""
        full_command = self.query_one("#command-input", Input).value.strip()

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

        if command_lower.startswith("kubectl"):
            # Remove 'kubectl' from the beginning and return the rest as args
            cmd_args = full_command[7:].strip()  # Remove 'kubectl'
            return "kubectl", cmd_args
        if command_lower.startswith("helm"):
            # Remove 'helm' from the beginning and return the rest as args
            cmd_args = full_command[4:].strip()  # Remove 'helm'
            return "helm", cmd_args
        # Try to infer from common patterns, default to kubectl
        if any(keyword in command_lower for keyword in ["get pods", "get services", "describe", "logs", "exec"]):
            return "kubectl", full_command
        if any(keyword in command_lower for keyword in ["install", "upgrade", "list", "status", "uninstall"]):
            return "helm", full_command
        # Default to kubectl and let user prefix with kubectl if needed
        return "kubectl", full_command

    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self):
        """Handle cancel button press"""
        self.result = ("cancel", None, None)
        self.dismiss(self.result)

    async def action_dismiss(self, result=None):
        """Handle escape key - same as cancel"""
        self.result = ("cancel", None, None)
        await self.dismiss(self.result)


class ConfigModal(ModalScreen):
    """Modal for configuring deployment parameters"""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]

    def __init__(self, chart_name: str, chart_values: dict | None = None):
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
                    id="namespace-input",
                )

                yield Label("Replicas:")
                yield Input(
                    value=str(self.chart_values.get("replicas", "1")),
                    placeholder="1",
                    id="replicas-input",
                )

                yield Label("Environment:")
                yield Select([
                    ("development", "dev"),
                    ("staging", "staging"),
                    ("production", "prod"),
                ], value=self.chart_values.get("environment", "development"), id="env-select")

                yield Label("Enable Monitoring:")
                yield Switch(
                    value=self.chart_values.get("monitoring", False),
                    id="monitoring-switch",
                )

            with Horizontal(classes="modal-buttons"):
                yield Button("Deploy", variant="primary", id="deploy-btn")
                yield Button("Cancel (Esc)", variant="default", id="cancel-btn")

    @on(Button.Pressed, "#deploy-btn")
    def deploy_pressed(self):
        """Handle deploy button press"""
        config = {
            "namespace": self.query_one("#namespace-input", Input).value or "default",
            "replicas": self.query_one("#replicas-input", Input).value or "1",
            "environment": self.query_one("#env-select", Select).value,
            "monitoring": self.query_one("#monitoring-switch", Switch).value,
        }
        self.result = ("deploy", self.chart_name, config)
        self.dismiss(self.result)

    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self):
        """Handle cancel button press"""
        self.result = ("cancel", None, None)
        self.dismiss(self.result)

    async def action_dismiss(self, result=None):
        """Handle escape key - same as cancel"""
        self.result = ("cancel", None, None)
        await self.dismiss(self.result)


class LogModal(ModalScreen):
    """Modal for displaying logs and command output"""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", priority=True),
        Binding("enter", "dismiss", "Close", priority=True),
    ]

    def __init__(self, title: str, content: str | None = None, syntax: str | None = None):
        super().__init__()
        self.title = title
        self.content = content
        self.syntax = syntax

    def compose(self):
        """Compose the log modal"""
        with Container(classes="modal large-modal"):
            yield Static(self.title or "Log", classes="modal-title")
            yield Log(highlight=True, id="log-content")
            yield Button("Close (Esc)", id="close-btn", classes="modal-close-btn")

    def on_mount(self):
        """Populate log content when modal mounts"""
        log_widget = self.query_one("#log-content", Log)
        if self.content:
            for line in self.content.split("\n"):
                log_widget.write_line(line)

    @on(Button.Pressed, "#close-btn")
    def close_pressed(self):
        """Handle close button press"""
        self.dismiss()

    async def action_dismiss(self, result=None):
        """Handle escape/enter key - close modal"""
        await self.dismiss()


class AddCommandModal(ModalScreen):
    """Modal for adding new commands to CommandPad"""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]

    def __init__(self, command_history=None):
        super().__init__()
        self.result = None
        self.command_history = command_history

    def compose(self):
        """Compose the add command modal"""
        with Container(classes="modal"):
            yield Static("➕ Add New Command", classes="modal-title")

            with Vertical(classes="modal-content"):
                yield Label("Command:", classes="input-label")
                yield Input(
                    placeholder="e.g., kubectl get pods -n production",
                    id="command-input",
                )

                yield Label("Description:", classes="input-label")
                yield Input(
                    placeholder="e.g., Get all pods in production namespace",
                    id="description-input",
                )

                yield Label("Tags (comma separated):", classes="input-label")
                yield Input(
                    placeholder="e.g., kubectl, pods, production",
                    id="tags-input",
                )

                yield Label("Command Type:", classes="input-label")
                yield Select([
                    ("⚡ kubectl", "kubectl"),
                    ("🚢 Helm", "helm"),
                    ("🐳 Docker", "docker"),
                    ("📦 Git", "git"),
                    ("💻 General", "general"),
                ], value="kubectl", id="type-select")

            with Horizontal(classes="modal-buttons"):
                yield Button("➕ Add Command", variant="primary", id="add-btn")
                yield Button("❌ Cancel (Esc)", variant="default", id="cancel-btn")

    @on(Button.Pressed, "#add-btn")
    def add_pressed(self):
        """Handle add button press"""
        command = self.query_one("#command-input", Input).value.strip()
        description = self.query_one("#description-input", Input).value.strip()
        tags_input = self.query_one("#tags-input", Input).value.strip()
        command_type = self.query_one("#type-select", Select).value

        if command:
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []

            # Persist the command directly
            if self.command_history:
                self.command_history.add_command(
                    command=command,
                    description=description or f"Execute {command}",
                    tags=tags,
                    command_type=command_type,
                )

                # Notify CommandPad of the new command via message system
                self._notify_command_added({
                    "command": command,
                    "description": description or f"Execute {command}",
                    "tags": tags,
                    "command_type": command_type,
                })

            self.result = ("add", {
                "command": command,
                "description": description or f"Execute {command}",
                "tags": tags,
                "command_type": command_type,
            })
        else:
            self.result = ("cancel", None)

        self.dismiss(self.result)

    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self):
        """Handle cancel button press"""
        self.result = ("cancel", None)
        self.dismiss(self.result)

    async def action_dismiss(self, result=None):
        """Handle escape key - same as cancel"""
        self.result = ("cancel", None)
        await self.dismiss(self.result)

    def _notify_command_added(self, command_data: dict[str, Any]) -> None:
        """Notify CommandPad widgets of newly added command via message system.

        Uses Textual's screen stack to locate CommandPad widgets in the parent screen
        and posts a CommandAdded message to trigger UI refresh.

        Args:
            command_data: Dictionary containing command information (command, description, tags, type)

        """
        try:
            from .command_pad import CommandPad

            # Access the parent screen containing CommandPad widgets
            if len(self.app.screen_stack) > 1:
                parent_screen = self.app.screen_stack[-2]
                command_pads = list(parent_screen.query(CommandPad))

                if command_pads:
                    message = CommandPad.CommandAdded(command_data)
                    for command_pad in command_pads:
                        command_pad.post_message(message)

        except Exception:
            # Silently fail - UI refresh isn't critical enough to crash the modal
            pass


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
                    id="command-input",
                )

                yield Label("Description:", classes="input-label")
                yield Input(
                    value=self.command_entry.description,
                    id="description-input",
                )

                yield Label("Tags (comma separated):", classes="input-label")
                tags_value = ", ".join(self.command_entry.tags) if self.command_entry.tags else ""
                yield Input(
                    value=tags_value,
                    id="tags-input",
                )

                yield Label("Command Type:", classes="input-label")
                yield Select([
                    ("⚡ kubectl", "kubectl"),
                    ("🚢 Helm", "helm"),
                    ("🐳 Docker", "docker"),
                    ("📦 Git", "git"),
                    ("💻 General", "general"),
                ], value=self.command_entry.command_type or "kubectl", id="type-select")

            with Horizontal(classes="modal-buttons"):
                yield Button("💾 Save Changes", variant="primary", id="save-btn")
                yield Button("❌ Cancel (Esc)", variant="default", id="cancel-btn")

    @on(Button.Pressed, "#save-btn")
    def save_pressed(self):
        """Handle save button press"""
        command = self.query_one("#command-input", Input).value.strip()
        description = self.query_one("#description-input", Input).value.strip()
        tags_input = self.query_one("#tags-input", Input).value.strip()
        command_type = self.query_one("#type-select", Select).value

        if command:
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
            self.result = ("save", {
                "original_command": self.command_entry.command,
                "command": command,
                "description": description or f"Execute {command}",
                "tags": tags,
                "command_type": command_type,
            })
        else:
            self.result = ("cancel", None)

        self.dismiss(self.result)

    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self):
        """Handle cancel button press"""
        self.result = ("cancel", None)
        self.dismiss(self.result)

    async def action_dismiss(self, result=None):
        """Handle escape key - same as cancel"""
        self.result = ("cancel", None)
        await self.dismiss(self.result)


class ClusterSwitchModal(ModalScreen):
    """Modal for switching between clusters"""

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", priority=True),
    ]

    def __init__(self, clusters: list[dict[str, Any]], current_cluster: str | None = None):
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
        selected_cluster = self.query_one("#cluster-select", Select).value
        self.result = ("switch", selected_cluster)
        self.dismiss(self.result)

    @on(Button.Pressed, "#test-btn")
    def test_pressed(self):
        """Handle test connection button press"""
        selected_cluster = self.query_one("#cluster-select", Select).value
        self.result = ("test", selected_cluster)
        self.dismiss(self.result)

    @on(Button.Pressed, "#cancel-btn")
    def cancel_pressed(self):
        """Handle cancel button press"""
        self.result = ("cancel", None)
        self.dismiss(self.result)

    async def action_dismiss(self, result=None):
        """Handle escape key - same as cancel"""
        self.result = ("cancel", None)
        await self.dismiss(self.result)
