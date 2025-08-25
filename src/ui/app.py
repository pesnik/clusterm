"""
Main TUI application
"""

from pathlib import Path
from textual.app import App
from textual.binding import Binding
from ..__version__ import __version__
from ..core.config import Config
from ..core.logger import Logger
from ..core.events import EventBus
from ..core.command_history import CommandHistoryManager
from ..k8s.manager import K8sManager
from ..plugins.manager import PluginManager
from .screens import MainScreen
from .components.command_input import CommandInput


class ClustermApp(App):
    """Main Clusterm TUI Application"""
    
    CSS = """
    /* Global styles */
    .panel {
        border: solid $primary;
        margin: 1;
        padding: 1;
    }
    
    /* Status panel */
    #status-panel {
        height: 3;
        dock: top;
        margin-bottom: 1;
        background: $surface;
    }
    
    .status-label {
        color: $text-muted;
        width: auto;
        margin-right: 1;
    }
    
    .status-value {
        color: $text;
        width: auto;
        margin-right: 3;
    }
    
    .status-value.connected {
        color: $success;
    }
    
    .status-value.disconnected {
        color: $error;
    }
    
    /* Context Selector */
    .context-selector {
        border: solid $primary;
        margin: 0 0 1 0;
        padding: 1;
        background: $surface;
        height: auto;
    }
    
    .context-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }
    
    .context-selectors {
        height: auto;
    }
    
    .selector-group {
        width: 50%;
        margin: 0 1;
    }
    
    .selector-label {
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .cluster-select,
    .namespace-select {
        width: 100%;
    }
    
    /* Main content layout */
    #main-container {
        height: 100%;
        layout: vertical;
    }
    
    #top-panel {
        height: auto;
        layout: horizontal;
    }
    
    #main-content {
        height: 1fr;
        layout: horizontal;
    }
    
    #charts-panel {
        width: 30%;
        height: 100%;
    }
    
    #resources-tabs {
        width: 70%;
        height: 100%;
    }
    
    .action-buttons {
        margin-bottom: 1;
    }
    
    .action-btn {
        width: 100%;
        margin: 0 0 1 0;
        height: 3;
    }
    
    .charts-section {
        height: 1fr;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
        text-align: center;
    }
    
    .deploy-btn {
        width: 100%;
        margin-top: 1;
        height: 3;
    }
    
    /* Tables */
    DataTable {
        height: 100%;
    }
    
    /* Tab actions */
    .tab-actions {
        height: 3;
        align: center middle;
        margin-top: 1;
    }
    
    .tab-actions Button {
        margin: 0 1;
    }
    
    /* Log panel */
    #log-panel {
        height: 8;
        dock: bottom;
        margin-top: 1;
    }
    
    .log-panel-title {
        text-align: center;
        color: $primary;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }
    
    /* Modals */
    ModalScreen {
        align: center middle;
    }
    
    .modal {
        align: center middle;
        width: 60;
        height: auto;
        min-height: 20;
        max-height: 80%;
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin: 0;
    }
    
    .modal.large-modal {
        width: 80%;
        height: 80%;
    }
    
    .modal-title {
        text-align: center;
        color: $primary;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }
    
    .modal-content {
        height: auto;
        padding: 1;
        margin-bottom: 1;
    }
    
    .modal-buttons {
        align: center middle;
        height: 3;
        width: 100%;
        margin-top: 1;
    }
    
    .modal-buttons Button {
        margin: 0 1;
        min-width: 16;
    }
    
    .modal-close-btn {
        align: center middle;
        margin-top: 1;
    }
    
    .input-label {
        color: $text;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    .examples-title {
        color: $primary;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    .command-examples {
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
        height: auto;
        background: $surface-darken-1;
        padding: 1;
        border-left: solid $primary;
    }
    
    .current-cluster {
        text-style: bold;
        color: $success;
        margin-bottom: 1;
        height: 1;
    }
    
    .auto-detect-info {
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
        height: 1;
        text-align: center;
    }
    
    /* Input styling */
    Input {
        margin-bottom: 1;
    }
    
    Select {
        margin-bottom: 1;
    }
    
    Switch {
        margin-bottom: 1;
    }
    
    /* Command pad */
    .command-pad {
        height: 100%;
        padding: 1;
    }
    
    .command-pad-title {
        text-align: center;
        color: $primary;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }
    
    .command-pad-controls {
        height: 3;
        align: center middle;
        margin-bottom: 1;
    }
    
    .command-pad-controls Select {
        width: 50%;
        margin-right: 1;
    }
    
    .command-pad-controls Input {
        width: 50%;
    }
    
    .commands-table {
        height: 1fr;
        margin-bottom: 1;
    }
    
    .command-pad-buttons {
        height: 3;
        align: center middle;
    }
    
    .command-pad-buttons Button {
        margin: 0 1;
        min-width: 12;
    }
    
    /* Enhanced Command Input */
    .enhanced-command-input {
        height: auto;
        padding: 1;
        border: solid $primary;
        margin: 1;
    }
    
    .input-title {
        text-align: center;
        color: $primary;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }
    
    .input-area {
        height: auto;
        margin-bottom: 1;
    }
    
    .input-area Input {
        height: 3;
        margin-bottom: 1;
    }
    
    .suggestions {
        height: 2;
        background: $surface-lighten-1;
        border: solid $secondary;
        padding: 0 1;
    }
    
    .suggestions Static {
        color: $text-muted;
        text-style: italic;
    }
    
    .validation {
        height: 2;
        background: $surface-darken-1;
        border: solid $accent;
        padding: 0 1;
        margin-top: 1;
    }
    
    .validation Static {
        color: $warning;
        text-style: bold;
    }
    
    .input-buttons {
        height: 3;
        align: center middle;
    }
    
    .input-buttons Button {
        margin: 0 1;
        min-width: 12;
    }
    
    /* Intelligent Command Input */
    .intelligent-command-input {
        height: auto;
        padding: 1;
        border: solid $success;
        margin: 1;
        background: $surface-lighten-1;
    }
    
    .intelligent-command-input .input-title {
        text-align: center;
        color: $success;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }
    
    .input-hint {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        height: 1;
        margin-bottom: 1;
    }
    
    .intelligent-command-input .input-buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
    }
    
    .intelligent-command-input .input-buttons Button {
        margin: 0 1;
        min-width: 16;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("c", "switch_cluster", "Context Selector"),
        Binding("t", "test_connection", "Test Connection"),
        Binding("x", "execute_command", "Execute Command"),
        Binding("ctrl+i", "smart_input", "🧠 Smart Input"),
        Binding("d", "deploy", "Deploy Chart"),
        Binding("ctrl+l", "clear_logs", "Clear Logs"),
        Binding("escape", "cancel_modal", "Cancel", show=False),
    ]
    
    def __init__(self, config_path=None):
        super().__init__()
        
        # Initialize core components
        self.config = Config(config_path)
        self.logger = Logger(self.config)
        self.event_bus = EventBus()
        config_dir = Path(self.config.get("app.config_dir", "~/.clusterm")).expanduser()
        self.command_history = CommandHistoryManager(config_dir)
        
        
        # Initialize managers
        self.k8s_manager = K8sManager(self.config, self.event_bus, self.logger)
        self.plugin_manager = PluginManager(self.config, self.event_bus, self.logger)
        
        # Initialize plugins
        self._setup_plugins()
        
        # Main screen
        self.main_screen = None
    
    
    def _setup_plugins(self):
        """Setup and load plugins"""
        try:
            self.plugin_manager.discover_plugins()
            self.plugin_manager.load_enabled_plugins()
        except Exception as e:
            self.logger.error(f"Error setting up plugins: {e}")
    
    def on_mount(self):
        """Initialize the application"""
        self.title = f"Clusterm v{__version__}"
        self.main_screen = MainScreen(
            self.k8s_manager,
            self.config,
            self.event_bus,
            self.logger,
            self.command_history
        )
        self.push_screen(self.main_screen)
    
    def on_unmount(self):
        """Cleanup when application exits"""
        try:
            self.plugin_manager.shutdown()
            self.logger.info("Clusterm shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    # Actions
    async def action_quit(self):
        """Quit the application"""
        self.exit()
    
    def action_refresh(self):
        """Refresh all data"""
        if self.main_screen:
            self.main_screen._refresh_all_data()
    
    def action_switch_cluster(self):
        """Show context information"""
        if self.main_screen:
            try:
                from .components.panels import LogPanel
                log_panel = self.main_screen.query_one("#log-panel", LogPanel)
                log_panel.write_log("Context: Cluster=default, Namespace=default")
            except Exception:
                pass
    
    def action_test_connection(self):
        """Test cluster connection"""
        if self.main_screen:
            self.main_screen.test_connection()
    
    def action_execute_command(self):
        """Execute command"""
        if self.main_screen:
            self.main_screen.execute_command()
    
    def action_smart_input(self):
        """Launch smart input"""
        if self.main_screen:
            try:
                smart_input = self.main_screen.query_one("#intelligent-input", CommandInput)
                smart_input.action_launch_command_input()
            except Exception:
                # Fallback to regular execute command
                self.main_screen.execute_command()
    
    def action_deploy(self):
        """Deploy chart"""
        if self.main_screen:
            self.main_screen.deploy_chart()
    
    def action_clear_logs(self):
        """Clear system logs"""
        if self.main_screen:
            try:
                from .components.panels import LogPanel
                log_panel = self.main_screen.query_one("#log-panel", LogPanel)
                log_panel.clear_log()
            except Exception as e:
                self.logger.error(f"Error clearing logs: {e}")
    
    def action_cancel_modal(self):
        """Cancel any active modal - handled by modal itself"""
        # This will be caught by the modal's own escape binding
        pass