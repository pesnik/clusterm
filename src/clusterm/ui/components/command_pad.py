"""Command pad component for displaying and selecting frequently used commands
"""

from datetime import datetime
from typing import Any

from textual import on
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, DataTable, Input, Select, Static

from ...core.command_history import CommandEntry, CommandHistoryManager


class CommandPad(Widget):
    """Command pad widget for displaying and managing frequently used commands"""

    BINDINGS = [
        Binding("ctrl+f", "focus_search", "🔍 Search", show=True),
        Binding("f1", "toggle_filter", "🏷️ Filter", show=True),
        Binding("f5", "refresh", "🔄 Refresh", show=True),
        Binding("enter", "use_selected", "▶ Execute", show=True),
        Binding("delete", "delete_selected", "🗑️ Delete", show=True),
        Binding("ctrl+a", "add_command", "➕ Add", show=True),
        Binding("ctrl+c", "copy_selected", "📋 Copy", show=True),
        Binding("ctrl+e", "edit_selected", "✏️ Edit", show=True),
        Binding("escape", "clear_search", "Clear", show=False),
    ]

    class CommandSelected(Message):
        """Message sent when a command is selected"""

        def __init__(self, command: CommandEntry):
            self.command = command
            super().__init__()

    class CommandAdded(Message):
        """Message sent when a command is added"""

        def __init__(self, command_data: dict[str, Any]) -> None:
            self.command_data = command_data
            super().__init__()

    class CommandExecuted(Message):
        """Message sent when a command is executed"""

        def __init__(self, command: str, command_type: str | None = None) -> None:
            self.command = command
            self.command_type = command_type
            super().__init__()


    def __init__(self, command_history: CommandHistoryManager, logger=None, **kwargs):
        super().__init__(**kwargs)
        self.command_history = command_history
        self.logger = logger
        self.current_filter = "frequent"  # frequent, recent, all
        self.search_query = ""


    def compose(self):
        """Compose CommandPad using component-specific classes with vertical layout"""
        # Search controls with CommandPad-specific styling - use Vertical for simpler layout
        with Vertical(classes="command-pad-search-controls"):
            yield Static("🔍 Search:", classes="command-pad-search-label")
            yield Input(
                placeholder="Search commands...",
                id="search-input",
                classes="command-pad-search-input",
            )
            yield Select([
                ("🔥 Most Used", "frequent"),
                ("🕐 Recent", "recent"),
                ("📋 All", "all"),
                ("⚡ kubectl", "kubectl"),
                ("🚢 Helm", "helm"),
            ], value="frequent", id="filter-select", classes="command-pad-filter-select")

        # Main table with CommandPad-specific styling
        yield DataTable(id="commands-table", classes="command-pad-table")

        # Action buttons with CommandPad-specific styling
        with Horizontal(classes="command-pad-actions"):
            yield Button("➕ Add", id="add-btn", classes="command-pad-button command-pad-button-secondary")
            yield Button("✏️ Edit", id="edit-btn", classes="command-pad-button command-pad-button-secondary")
            yield Button("▶ Execute", id="use-btn", classes="command-pad-button command-pad-button-primary")
            yield Button("📋 Copy", id="copy-btn", classes="command-pad-button command-pad-button-secondary")
            yield Button("🗑️ Delete", id="delete-btn", classes="command-pad-button command-pad-button-danger")

    def on_mount(self):
        """Setup the modern command pad"""
        table = self.query_one("#commands-table", DataTable)

        # Add modern columns with better spacing
        table.add_column("Command", width=40)
        table.add_column("Type", width=12)
        table.add_column("Uses", width=8)
        table.add_column("Last Used", width=12)
        table.add_column("Tags", width=20)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.show_header = True

        self._refresh_commands()
        self._update_all_stats()


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


    @on(Button.Pressed, "#copy-btn")
    def copy_selected_command(self):
        """Copy selected command to clipboard"""
        selected_cmd = self.get_selected_command()
        if selected_cmd:
            try:
                import pyperclip
                pyperclip.copy(selected_cmd.command)
                if self.logger:
                    self.logger.info(f"Copied command to clipboard: {selected_cmd.command}")
            except ImportError:
                if self.logger:
                    self.logger.warning("pyperclip not available - cannot copy to clipboard")

    @on(Button.Pressed, "#add-btn")
    async def add_new_command(self):
        """Add new command"""
        if self.logger:
            self.logger.info("CommandPad: Add button pressed, launching modal")

        from .modals import AddCommandModal

        modal = AddCommandModal(self.command_history)
        await self.app.push_screen(modal)

        # CommandPad will be refreshed via CommandAdded message from modal

    @on(Button.Pressed, "#edit-btn")
    async def edit_selected_command(self):
        """Edit selected command"""
        if self.logger:
            self.logger.info("CommandPad: Edit button pressed")

        selected_cmd = self.get_selected_command()
        if selected_cmd:
            if self.logger:
                self.logger.info(f"CommandPad: Editing command: {selected_cmd.command}")
            from .modals import EditCommandModal

            modal = EditCommandModal(selected_cmd)
            result = await self.app.push_screen(modal)

            if result and result[0] == "save":
                command_data = result[1]
                # Delete old command and add updated one
                self.command_history.delete_command(command_data["original_command"])
                self.command_history.add_command(
                    command=command_data["command"],
                    description=command_data["description"],
                    tags=command_data["tags"],
                    command_type=command_data.get("command_type"),
                )
                self._refresh_commands()
                if self.logger:
                    self.logger.info(f"Updated command: {command_data['command']}")

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

    @on(CommandAdded)
    def on_command_pad_command_added(self, event: CommandAdded):
        """Handle CommandAdded message - refresh the UI"""
        self._refresh_commands()
        if self.logger:
            self.logger.info(f"Command added via message, refreshing UI: {event.command_data['command']}")

    @on(CommandExecuted)
    def on_command_pad_command_executed(self, event: CommandExecuted):
        """Handle CommandExecuted message - refresh the UI to show executed command in history"""
        self._refresh_commands()
        if self.logger:
            self.logger.info(f"Command executed via message, refreshing UI: {event.command}")

    @on(DataTable.RowSelected)
    def row_selected(self, event: DataTable.RowSelected):
        """Handle row selection"""
        # Enable/disable buttons based on selection
        try:
            add_btn = self.query_one("#add-btn", Button)
            edit_btn = self.query_one("#edit-btn", Button)
            use_btn = self.query_one("#use-btn", Button)
            copy_btn = self.query_one("#copy-btn", Button)
            delete_btn = self.query_one("#delete-btn", Button)

            has_selection = event.cursor_row is not None
            # Add button is always enabled (doesn't require selection)
            add_btn.disabled = False
            # Other buttons require selection
            edit_btn.disabled = not has_selection
            use_btn.disabled = not has_selection
            copy_btn.disabled = not has_selection
            delete_btn.disabled = not has_selection
        except Exception:
            pass

    @on(Input.Changed, "#search-input")
    def search_changed(self, event: Input.Changed):
        """Handle real-time search"""
        self.search_query = event.value.strip()
        self._refresh_commands()

    @on(Select.Changed, "#filter-select")
    def filter_changed(self, event: Select.Changed):
        """Handle filter selection change"""
        self.current_filter = str(event.value)
        self._refresh_commands()

    def _get_filtered_commands(self) -> list[CommandEntry]:
        """Get commands based on current filter and search with enhanced filtering"""
        # First apply base filter
        if self.current_filter == "frequent":
            commands = self.command_history.get_frequent_commands(100)
        elif self.current_filter == "recent":
            commands = self.command_history.get_recent_commands(100)
        elif self.current_filter == "kubectl":
            commands = [cmd for cmd in self.command_history.get_all_commands()
                       if cmd.command_type == "kubectl" or "kubectl" in cmd.command.lower()]
        elif self.current_filter == "helm":
            commands = [cmd for cmd in self.command_history.get_all_commands()
                       if cmd.command_type == "helm" or "helm" in cmd.command.lower()]
        elif self.current_filter == "docker":
            commands = [cmd for cmd in self.command_history.get_all_commands()
                       if cmd.command_type == "docker" or "docker" in cmd.command.lower()]
        else:  # all
            commands = self.command_history.get_all_commands()

        # Enhanced search filter with fuzzy matching
        if self.search_query:
            query = self.search_query.lower()
            filtered = []
            for cmd in commands:
                score = 0
                # Exact match in command gets highest score
                if query in cmd.command.lower():
                    score += 10
                # Match in description
                if query in cmd.description.lower():
                    score += 5
                # Match in tags
                if cmd.tags and any(query in tag.lower() for tag in cmd.tags):
                    score += 3
                # Fuzzy match - check if all characters in query appear in order
                if self._fuzzy_match(query, cmd.command.lower()):
                    score += 2

                if score > 0:
                    filtered.append((score, cmd))

            # Sort by score (highest first) and extract commands
            commands = [cmd for _, cmd in sorted(filtered, key=lambda x: x[0], reverse=True)]

        return commands

    def _fuzzy_match(self, query: str, text: str) -> bool:
        """Simple fuzzy matching - check if all characters appear in order"""
        query_idx = 0
        for char in text:
            if query_idx < len(query) and char == query[query_idx]:
                query_idx += 1
        return query_idx == len(query)

    def _refresh_commands(self):
        """Refresh the commands table with modern formatting"""
        table = self.query_one("#commands-table", DataTable)
        table.clear()

        commands = self._get_filtered_commands()

        for cmd in commands:
            # Enhanced command display with better formatting
            command_display = self._format_command_modern(cmd.command)

            # Enhanced type display with better icons
            type_display = self._format_command_type(cmd.command_type)

            # Enhanced usage count with styling
            usage_display = f"✨{cmd.usage_count}" if cmd.usage_count > 10 else str(cmd.usage_count)

            # Enhanced time formatting
            last_used = self._format_time_ago_modern(cmd.last_used) if cmd.last_used else "📅 Never"

            # Enhanced tags with better formatting
            tags_display = self._format_tags_modern(cmd.tags)

            table.add_row(
                command_display,
                type_display,
                usage_display,
                last_used,
                tags_display,
            )

        self._update_action_buttons(len(commands))
        self._update_all_stats()

    def _format_command_modern(self, command: str) -> str:
        """Format command with modern styling and smart truncation"""
        if len(command) <= 38:  # Adjusted for better table fit
            return command

        # Smart truncation with emphasis on command name
        parts = command.split()
        if not parts:
            return command[:35] + "..."

        cmd_name = parts[0]
        if len(cmd_name) > 35:
            return cmd_name[:32] + "..."

        result = cmd_name
        remaining_space = 35 - len(cmd_name)

        for part in parts[1:]:
            if len(" " + part) <= remaining_space - 3:  # Reserve space for "..."
                result += " " + part
                remaining_space -= len(" " + part)
            else:
                if remaining_space > 3:
                    result += " " + part[:remaining_space-3] + "..."
                else:
                    result += "..."
                break

        return result

    def _format_command_type(self, cmd_type: str) -> str:
        """Format command type with modern icons"""
        type_icons = {
            "kubectl": "⚡ k8s",
            "helm": "🚢 helm",
            "docker": "🐳 docker",
            "git": "📦 git",
            "ssh": "🔐 ssh",
            "general": "💻 cmd",
        }
        return type_icons.get(cmd_type, f"📄 {cmd_type}")

    def _format_time_ago_modern(self, timestamp: str) -> str:
        """Format timestamp with modern icons"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                return "❓ Unknown"

            now = datetime.now(dt.tzinfo)
            diff = now - dt

            if diff.days > 7:
                return f"🗓️ {diff.days}d"
            if diff.days > 0:
                return f"📅 {diff.days}d"
            if diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"⏰ {hours}h"
            if diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"⏱️ {minutes}m"
            return "🕐 now"
        except:
            return "❓ error"

    def _format_tags_modern(self, tags) -> str:
        """Format tags with modern styling"""
        if not tags:
            return "📝 none"

        if len(tags) == 1:
            return f"🏷️ {tags[0]}"
        if len(tags) == 2:
            return f"🏷️ {tags[0]}, {tags[1]}"
        return f"🏷️ {tags[0]} +{len(tags)-1}"

    def _format_command(self, command: str) -> str:
        """Legacy format command method - keeping for compatibility"""
        return self._format_command_modern(command)

    def _format_time_ago(self, timestamp: str) -> str:
        """Format timestamp as time ago"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                return "Unknown"

            now = datetime.now(dt.tzinfo)
            diff = now - dt

            if diff.days > 0:
                return f"{diff.days}d ago"
            if diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
            if diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes}m ago"
            return "Just now"
        except:
            return "Unknown"

    def _update_action_buttons(self, command_count: int):
        """Update action button states"""
        try:
            add_btn = self.query_one("#add-btn", Button)
            edit_btn = self.query_one("#edit-btn", Button)
            use_btn = self.query_one("#use-btn", Button)
            copy_btn = self.query_one("#copy-btn", Button)
            delete_btn = self.query_one("#delete-btn", Button)

            has_commands = command_count > 0
            # Add button is always enabled
            add_btn.disabled = False
            # Other buttons require commands and selection
            edit_btn.disabled = not has_commands
            use_btn.disabled = not has_commands
            copy_btn.disabled = not has_commands
            delete_btn.disabled = not has_commands
        except Exception:
            pass  # Buttons might not exist yet

    def _update_all_stats(self):
        """Update statistics display in search label"""
        try:
            all_commands = self.command_history.get_all_commands()
            filtered_commands = self._get_filtered_commands()

            # Update search label with stats
            stats_text = f"🔍 Search ({len(filtered_commands)}/{len(all_commands)}):"
            if self.search_query:
                stats_text = f"🔍 Search '{self.search_query[:10]}' ({len(filtered_commands)}):"

            try:
                label_static = self.query_one(".command-pad-search-label", Static)
                label_static.update(stats_text)
            except:
                pass  # Label might not exist

        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error updating stats: {e}")

    def _update_stats(self):
        """Legacy stats update - redirects to modern version"""
        self._update_all_stats()


    # Keyboard action handlers
    def action_focus_search(self):
        """Focus the search input"""
        try:
            search_input = self.query_one("#search-input", Input)
            search_input.focus()
        except:
            pass

    def action_toggle_filter(self):
        """Toggle between filter modes"""
        try:
            filter_select = self.query_one("#filter-select", Select)
            current_options = ["frequent", "recent", "all", "kubectl", "helm"]
            try:
                current_index = current_options.index(self.current_filter)
                next_index = (current_index + 1) % len(current_options)
                next_value = current_options[next_index]
                filter_select.value = next_value
                self.current_filter = next_value
                self._refresh_commands()
            except ValueError:
                pass
        except:
            pass

    def action_use_selected(self):
        """Execute selected command via keyboard"""
        self.use_command()

    def action_delete_selected(self):
        """Delete selected command via keyboard"""
        self.delete_selected_command()

    def action_copy_selected(self):
        """Copy selected command via keyboard"""
        self.copy_selected_command()

    def action_edit_selected(self):
        """Edit selected command via keyboard"""
        self.run_worker(self.edit_selected_command())

    def action_add_command(self):
        """Add new command"""
        self.run_worker(self.add_new_command())

    def action_clear_search(self):
        """Clear search input"""
        try:
            search_input = self.query_one("#search-input", Input)
            search_input.value = ""
            self.search_query = ""
            self._refresh_commands()
        except:
            pass

    def action_refresh(self):
        """Refresh commands from disk"""
        self.command_history._load_history()
        self._refresh_commands()

    def get_selected_command(self) -> CommandEntry | None:
        """Get currently selected command"""
        table = self.query_one("#commands-table", DataTable)
        if table.cursor_row is not None:
            commands = self._get_filtered_commands()
            if table.cursor_row < len(commands):
                return commands[table.cursor_row]
        return None
