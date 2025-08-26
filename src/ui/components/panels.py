"""Panel components for the UI
"""

from datetime import datetime

from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Label, Log, Static


class LogPanel(Container):
    """Enhanced log panel with filtering and controls"""

    max_lines = reactive(5000)
    show_timestamps = reactive(True)

    def __init__(self, title: str = "System Logs", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.log_entries = []

    def compose(self):
        """Compose the log panel"""
        with Container():
            yield Label(self.title, classes="log-panel-title")
            yield Log(highlight=True, id="log-content")

    def write_log(self, message: str, level: str = "INFO"):
        """Write a log message"""
        timestamp = datetime.now().strftime("%H:%M:%S") if self.show_timestamps else ""

        if timestamp:
            formatted_message = f"[{timestamp}] [{level}] {message}"
        else:
            formatted_message = f"[{level}] {message}"

        # Store entry
        self.log_entries.append({
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "formatted": formatted_message,
        })

        # Maintain max lines
        if len(self.log_entries) > self.max_lines:
            self.log_entries = self.log_entries[-self.max_lines:]

        # Write to log widget
        try:
            log_widget = self.query_one("#log-content", Log)
            log_widget.write_line(formatted_message)
        except:
            # Widget not ready yet
            pass

    def clear_log(self):
        """Clear all log entries"""
        self.log_entries.clear()
        try:
            log_widget = self.query_one("#log-content", Log)
            log_widget.clear()
        except:
            pass

    def filter_logs(self, level: str | None = None, search: str | None = None):
        """Filter and redisplay logs"""
        try:
            log_widget = self.query_one("#log-content", Log)
            log_widget.clear()

            for entry in self.log_entries:
                # Apply filters
                if level and entry["level"] != level:
                    continue

                if search and search.lower() not in entry["message"].lower():
                    continue

                log_widget.write_line(entry["formatted"])
        except:
            pass


class StatusPanel(Container):
    """Panel for displaying system status"""

    cluster_status = reactive("Unknown")
    connection_status = reactive("Disconnected")

    def compose(self):
        """Compose the status panel"""
        with Horizontal(classes="status-panel"):
            yield Static("Cluster:", classes="status-label")
            yield Static(self.cluster_status, id="cluster-status", classes="status-value")
            yield Static("Status:", classes="status-label")
            yield Static(self.connection_status, id="connection-status", classes="status-value")

    def update_cluster_status(self, cluster_name: str, connected: bool):
        """Update cluster status display"""
        self.cluster_status = cluster_name or "No Cluster"
        self.connection_status = "Connected" if connected else "Disconnected"

        try:
            cluster_widget = self.query_one("#cluster-status", Static)
            cluster_widget.update(self.cluster_status)

            status_widget = self.query_one("#connection-status", Static)
            status_widget.update(self.connection_status)

            # Update CSS classes for styling
            if connected:
                status_widget.add_class("connected")
                status_widget.remove_class("disconnected")
            else:
                status_widget.add_class("disconnected")
                status_widget.remove_class("connected")
        except:
            pass
