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
    
    CSS_PATH = [
        Path(__file__).parent / "styles" / "base.tcss", 
        Path(__file__).parent / "styles" / "components" / "status.tcss",
        Path(__file__).parent / "styles" / "components" / "context-selector.tcss",
        Path(__file__).parent / "styles" / "components" / "buttons.tcss",
        Path(__file__).parent / "styles" / "components" / "panels.tcss",
        Path(__file__).parent / "styles" / "components" / "modals.tcss",
        Path(__file__).parent / "styles" / "components" / "command-input.tcss",
        Path(__file__).parent / "styles" / "components" / "command-pad.tcss",
    ]
    
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
        self.event_bus = EventBus(self.logger)
        config_dir = Path(self.config.get("app.config_dir", "~/.clusterm")).expanduser()
        self.command_history = CommandHistoryManager(config_dir, self.logger)
        
        
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