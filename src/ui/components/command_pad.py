"""
Command pad component for displaying and selecting frequently used commands
"""

from typing import List, Optional
from textual.widgets import Button, Static, DataTable
from textual.widget import Widget
from textual.binding import Binding
from textual.message import Message
from textual import on
from ...core.command_history import CommandHistoryManager, CommandEntry


class CommandPad(Widget):
    """Command pad widget for displaying and managing frequently used commands"""
    
    BINDINGS = [
        Binding("f", "toggle_filter", "Filter"),
        Binding("r", "refresh", "Refresh"),
        Binding("delete", "delete_selected", "Delete"),
    ]
    
    class CommandSelected(Message):
        """Message sent when a command is selected"""
        def __init__(self, command: CommandEntry):
            self.command = command
            super().__init__()
    
    def __init__(self, command_history: CommandHistoryManager, logger=None, **kwargs):
        super().__init__(**kwargs)
        self.command_history = command_history
        self.logger = logger
        self.current_filter = "frequent"  # frequent, recent, all
        self.search_query = ""
        
    
    def compose(self):
        """Compose the command pad"""
        yield Static("⚡ Command Pad", classes="command-pad-title")
        yield DataTable(id="commands-table", classes="commands-table")
        yield Button("📋 Use", variant="primary", id="use-btn")
        yield Button("🗑️ Delete", variant="error", id="delete-btn")
    
    def on_mount(self):
        """Setup the command pad when mounted"""
        if self.logger:
            self.logger.debug("CommandPad.on_mount: Starting mount process")
        
        table = self.query_one("#commands-table", DataTable)
        table.add_columns("Command", "Type", "Uses")
        table.cursor_type = "row"
        
        # Force table to have minimum dimensions
        table.styles.height = "auto"
        table.styles.min_height = 10
        
        if self.logger:
            self.logger.debug("CommandPad.on_mount: Table setup complete, refreshing commands")
        
        self._refresh_commands()
    
    
    @on(Button.Pressed, "#use-btn")
    def use_command(self):
        """Use selected command"""
        table = self.query_one("#commands-table", DataTable)
        if table.cursor_row is not None:
            commands = self._get_filtered_commands()
            if table.cursor_row < len(commands):
                selected_command = commands[table.cursor_row]
                # Increment usage count
                self.command_history.add_command(selected_command.command)
                # Send message to parent
                self.post_message(self.CommandSelected(selected_command))
                self._refresh_commands()  # Refresh to update usage count
    
    
    @on(Button.Pressed, "#delete-btn")
    def delete_selected_command(self):
        """Delete selected command"""
        table = self.query_one("#commands-table", DataTable)
        if table.cursor_row is not None:
            commands = self._get_filtered_commands()
            if table.cursor_row < len(commands):
                selected_command = commands[table.cursor_row]
                self.command_history.delete_command(selected_command.command)
                self._refresh_commands()
    
    @on(DataTable.RowSelected)
    def row_selected(self, event: DataTable.RowSelected):
        """Handle row selection"""
        # Enable/disable buttons based on selection
        use_btn = self.query_one("#use-btn", Button)
        delete_btn = self.query_one("#delete-btn", Button)
        
        has_selection = event.cursor_row is not None
        use_btn.disabled = not has_selection
        delete_btn.disabled = not has_selection
    
    def _get_filtered_commands(self) -> List[CommandEntry]:
        """Get commands based on current filter and search"""
        if self.search_query:
            commands = self.command_history.search_commands(self.search_query)
        elif self.current_filter == "frequent":
            commands = self.command_history.get_frequent_commands(20)
        elif self.current_filter == "recent":
            commands = self.command_history.get_recent_commands(20)
        else:  # all
            commands = self.command_history.get_all_commands()
        
        return commands
    
    def _refresh_commands(self):
        """Refresh the commands table"""
        if self.logger:
            self.logger.debug("CommandPad._refresh_commands: Starting command refresh")
        
        table = self.query_one("#commands-table", DataTable)
        table.clear()
        
        commands = self._get_filtered_commands()
        
        if self.logger:
            self.logger.debug(f"CommandPad._refresh_commands: Found {len(commands)} commands")
        
        for cmd in commands:
            table.add_row(
                cmd.command[:50] + ("..." if len(cmd.command) > 50 else ""),
                cmd.command_type,
                str(cmd.usage_count)
            )
        
        # Update button states
        try:
            use_btn = self.query_one("#use-btn", Button)
            delete_btn = self.query_one("#delete-btn", Button)
            has_commands = len(commands) > 0
            use_btn.disabled = not has_commands
            delete_btn.disabled = not has_commands
        except Exception:
            pass  # Buttons might not exist yet
        
        if self.logger:
            self.logger.debug(f"CommandPad._refresh_commands: Completed refresh with {len(commands)} commands displayed")
    
    
    def action_refresh(self):
        """Refresh commands"""
        self.command_history._load_history()  # Reload from disk
        self._refresh_commands()
    
    def action_delete_selected(self):
        """Delete selected command"""
        self.delete_selected_command()
    
    def get_selected_command(self) -> Optional[CommandEntry]:
        """Get currently selected command"""
        table = self.query_one("#commands-table", DataTable)
        if table.cursor_row is not None:
            commands = self._get_filtered_commands()
            if table.cursor_row < len(commands):
                return commands[table.cursor_row]
        return None