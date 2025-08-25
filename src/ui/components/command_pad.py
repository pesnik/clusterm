"""
Command pad component for displaying and selecting frequently used commands
"""

from typing import List, Optional, Callable
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Static, DataTable, Input, Select
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
    
    def __init__(self, command_history: CommandHistoryManager, **kwargs):
        super().__init__(**kwargs)
        self.command_history = command_history
        self.current_filter = "frequent"  # frequent, recent, all
        self.search_query = ""
    
    def compose(self):
        """Compose the command pad"""
        with Container(classes="command-pad"):
            yield Static("⚡ Command Pad", classes="command-pad-title")
            
            with Horizontal(classes="command-pad-controls"):
                yield Select([
                    ("Most Frequent", "frequent"),
                    ("Recent", "recent"), 
                    ("All Commands", "all")
                ], value="frequent", id="filter-select")
                
                yield Input(
                    placeholder="Search commands...",
                    id="search-input"
                )
            
            yield DataTable(id="commands-table", classes="commands-table")
            
            with Horizontal(classes="command-pad-buttons"):
                yield Button("📋 Use", variant="primary", id="use-btn")
                yield Button("⭐ Add Current", variant="default", id="add-btn")
                yield Button("🗑️ Delete", variant="error", id="delete-btn")
    
    def on_mount(self):
        """Setup the command pad when mounted"""
        table = self.query_one("#commands-table", DataTable)
        table.add_columns("Command", "Type", "Uses", "Description")
        table.cursor_type = "row"
        self._refresh_commands()
    
    @on(Select.Changed, "#filter-select")
    def filter_changed(self, event: Select.Changed):
        """Handle filter selection change"""
        self.current_filter = event.value
        self._refresh_commands()
    
    @on(Input.Submitted, "#search-input")
    def search_submitted(self, event: Input.Submitted):
        """Handle search input"""
        self.search_query = event.value.strip()
        self._refresh_commands()
    
    @on(Input.Changed, "#search-input")
    def search_changed(self, event: Input.Changed):
        """Handle search input change (real-time search)"""
        if not event.value.strip():  # Clear search
            self.search_query = ""
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
    
    @on(Button.Pressed, "#add-btn")
    def add_current_command(self):
        """Add current command from execute modal"""
        # This will be handled by parent to get current command from execute modal
        self.post_message(self.CommandSelected(None))  # Signal to show add dialog
    
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
        table = self.query_one("#commands-table", DataTable)
        table.clear()
        
        commands = self._get_filtered_commands()
        
        for cmd in commands:
            table.add_row(
                cmd.command[:50] + ("..." if len(cmd.command) > 50 else ""),
                cmd.command_type,
                str(cmd.usage_count),
                cmd.description[:30] + ("..." if len(cmd.description) > 30 else "")
            )
        
        # Update button states
        use_btn = self.query_one("#use-btn", Button)
        delete_btn = self.query_one("#delete-btn", Button)
        has_commands = len(commands) > 0
        use_btn.disabled = not has_commands
        delete_btn.disabled = not has_commands
    
    def action_toggle_filter(self):
        """Toggle between filter modes"""
        select = self.query_one("#filter-select", Select)
        current_index = 0
        options = ["frequent", "recent", "all"]
        try:
            current_index = options.index(self.current_filter)
        except ValueError:
            pass
        
        next_index = (current_index + 1) % len(options)
        next_value = options[next_index]
        select.value = next_value
        self.current_filter = next_value
        self._refresh_commands()
    
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