"""
Main TUI application
"""

from textual.app import App
from textual.binding import Binding
from ..core.config import Config
from ..core.logger import Logger
from ..core.events import EventBus
from ..k8s.manager import K8sManager
from ..plugins.manager import PluginManager
from .screens import MainScreen


class ClusterMApp(App):
    """Main ClusterM TUI Application"""
    
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
    
    /* Main content layout */
    #main-content {
        height: 100%;
    }
    
    #charts-panel {
        width: 30%;
        height: 100%;
    }
    
    #resources-tabs {
        width: 70%;
        height: 100%;
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
    .modal {
        align: center middle;
        width: 60;
        height: 20;
        background: $surface;
        border: solid $primary;
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
    }
    
    .modal-buttons Button {
        margin: 0 1;
    }
    
    .modal-close-btn {
        align: center middle;
        margin-top: 1;
    }
    
    .command-examples {
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
        height: 3;
    }
    
    .current-cluster {
        text-style: bold;
        color: $success;
        margin-bottom: 1;
        height: 1;
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
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("c", "switch_cluster", "Switch Cluster"),
        Binding("t", "test_connection", "Test Connection"),
        Binding("x", "execute_command", "Execute Command"),
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
        self.main_screen = MainScreen(
            self.k8s_manager,
            self.config,
            self.event_bus,
            self.logger
        )
        self.push_screen(self.main_screen)
    
    def on_unmount(self):
        """Cleanup when application exits"""
        try:
            self.plugin_manager.shutdown()
            self.logger.info("ClusterM shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    # Actions
    def action_quit(self):
        """Quit the application"""
        self.exit()
    
    def action_refresh(self):
        """Refresh all data"""
        if self.main_screen:
            self.main_screen._refresh_all_data()
    
    def action_switch_cluster(self):
        """Switch cluster"""
        if self.main_screen:
            self.main_screen.switch_cluster()
    
    def action_test_connection(self):
        """Test cluster connection"""
        if self.main_screen:
            self.main_screen.test_connection()
    
    def action_execute_command(self):
        """Execute command"""
        if self.main_screen:
            self.main_screen.execute_command()
    
    def action_deploy(self):
        """Deploy chart"""
        if self.main_screen:
            self.main_screen.deploy_chart()
    
    def action_clear_logs(self):
        """Clear system logs"""
        if self.main_screen:
            log_panel = self.main_screen.query_one("#log-panel")
            log_panel.clear_log()
    
    def action_cancel_modal(self):
        """Cancel any active modal - handled by modal itself"""
        # This will be caught by the modal's own escape binding
        pass