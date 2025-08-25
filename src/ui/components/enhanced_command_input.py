"""
Enhanced command input component with advanced features
This demonstrates the enhanced input capabilities we want to achieve
"""

import asyncio
import subprocess
import tempfile
from typing import List, Dict, Optional, Tuple
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Static, Input
from textual.widget import Widget
from textual.message import Message
from textual.binding import Binding
from textual import on


class EnhancedCommandInput(Widget):
    """
    Enhanced command input widget that provides:
    - Command history navigation (↑/↓ arrows)
    - Basic auto-completion suggestions
    - Command validation and syntax hints
    - Multi-line command support
    """
    
    BINDINGS = [
        Binding("up", "history_up", "Previous Command"),
        Binding("down", "history_down", "Next Command"),
        Binding("tab", "show_completions", "Show Completions"),
        Binding("ctrl+space", "trigger_autocomplete", "Auto-complete"),
    ]
    
    class CommandEntered(Message):
        """Message sent when a command is entered"""
        def __init__(self, command: str, command_type: str):
            self.command = command
            self.command_type = command_type
            super().__init__()
    
    def __init__(self, command_history_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.command_history_manager = command_history_manager
        self.history_index = -1
        self.current_command = ""
        self.completion_suggestions = []
        self.show_suggestions = False
        
        # kubectl and helm command patterns for basic completion
        self.kubectl_commands = [
            "get", "describe", "logs", "exec", "apply", "delete", "create",
            "edit", "patch", "scale", "rollout", "top", "port-forward"
        ]
        
        self.kubectl_resources = [
            "pods", "services", "deployments", "configmaps", "secrets",
            "namespaces", "nodes", "persistentvolumes", "persistentvolumeclaims",
            "ingresses", "networkpolicies", "serviceaccounts", "roles", "rolebindings"
        ]
        
        self.helm_commands = [
            "install", "upgrade", "uninstall", "list", "status", "history",
            "rollback", "test", "package", "dependency", "template", "get"
        ]
        
        # Common kubectl flags
        self.common_flags = [
            "--all-namespaces", "--namespace", "--output", "--selector",
            "--dry-run", "--force", "--grace-period", "--timeout"
        ]
    
    def compose(self):
        """Compose the enhanced input widget"""
        with Container(classes="enhanced-command-input"):
            yield Static("💻 Enhanced Command Input", classes="input-title")
            
            with Vertical(classes="input-area"):
                yield Input(
                    placeholder="Type kubectl or helm command... (↑↓ for history, Tab for completions)",
                    id="command-input"
                )
                
                with Container(id="suggestions-container", classes="suggestions"):
                    yield Static("", id="suggestions-display")
                
                with Container(id="validation-container", classes="validation"):
                    yield Static("", id="validation-display")
            
            with Horizontal(classes="input-buttons"):
                yield Button("⚡ Execute", variant="primary", id="execute-btn")
                yield Button("📋 From Pad", variant="default", id="pad-btn")
                yield Button("🔄 Clear", variant="default", id="clear-btn")
    
    def on_mount(self):
        """Initialize the widget"""
        self._update_suggestions("")
    
    @on(Input.Changed, "#command-input")
    def command_changed(self, event: Input.Changed):
        """Handle command input changes"""
        self.current_command = event.value
        self._update_suggestions(event.value)
        self._validate_command(event.value)
        self.history_index = -1  # Reset history navigation
    
    @on(Input.Submitted, "#command-input")
    def command_submitted(self, event: Input.Submitted):
        """Handle command submission"""
        command = event.value.strip()
        if command:
            command_type = self._detect_command_type(command)
            self.post_message(self.CommandEntered(command, command_type))
            
            # Add to history if we have a history manager
            if self.command_history_manager:
                self.command_history_manager.add_command(command)
            
            self._clear_input()
    
    @on(Button.Pressed, "#execute-btn")
    def execute_pressed(self):
        """Handle execute button press"""
        command_input = self.query_one("#command-input", Input)
        command = command_input.value.strip()
        if command:
            command_type = self._detect_command_type(command)
            self.post_message(self.CommandEntered(command, command_type))
            self._clear_input()
    
    @on(Button.Pressed, "#clear-btn")
    def clear_pressed(self):
        """Handle clear button press"""
        self._clear_input()
    
    @on(Button.Pressed, "#pad-btn")
    def pad_pressed(self):
        """Handle command pad button press - show available commands"""
        if self.command_history_manager:
            recent_commands = self.command_history_manager.get_recent_commands(5)
            if recent_commands:
                suggestions = [f"Recent: {cmd.command}" for cmd in recent_commands]
                self._show_suggestions(suggestions)
    
    def action_history_up(self):
        """Navigate to previous command in history"""
        if not self.command_history_manager:
            return
        
        commands = self.command_history_manager.get_all_commands()
        if not commands:
            return
        
        if self.history_index < len(commands) - 1:
            self.history_index += 1
            command = commands[-(self.history_index + 1)]
            self._set_input_value(command.command)
    
    def action_history_down(self):
        """Navigate to next command in history"""
        if not self.command_history_manager:
            return
        
        commands = self.command_history_manager.get_all_commands()
        if not commands:
            return
        
        if self.history_index > 0:
            self.history_index -= 1
            command = commands[-(self.history_index + 1)]
            self._set_input_value(command.command)
        elif self.history_index == 0:
            self.history_index = -1
            self._set_input_value("")
    
    def action_show_completions(self):
        """Show available completions"""
        command_input = self.query_one("#command-input", Input)
        current_value = command_input.value
        suggestions = self._get_completions(current_value)
        self._show_suggestions(suggestions)
    
    def action_trigger_autocomplete(self):
        """Trigger auto-completion"""
        command_input = self.query_one("#command-input", Input)
        current_value = command_input.value
        completion = self._get_best_completion(current_value)
        if completion:
            self._set_input_value(completion)
    
    def _detect_command_type(self, command: str) -> str:
        """Auto-detect command type"""
        command_lower = command.lower().strip()
        if command_lower.startswith('kubectl'):
            return 'kubectl'
        elif command_lower.startswith('helm'):
            return 'helm'
        else:
            # Infer from patterns
            if any(kw in command_lower for kw in ['get', 'describe', 'logs', 'exec']):
                return 'kubectl'
            elif any(kw in command_lower for kw in ['install', 'upgrade', 'list', 'status']):
                return 'helm'
            return 'kubectl'  # default
    
    def _update_suggestions(self, command: str):
        """Update auto-completion suggestions"""
        suggestions = self._get_completions(command)
        self._show_suggestions(suggestions[:5])  # Show top 5 suggestions
    
    def _get_completions(self, command: str) -> List[str]:
        """Get completion suggestions for current command"""
        if not command:
            return ["kubectl get pods", "helm list", "kubectl get services", "kubectl logs"]
        
        command_lower = command.lower()
        suggestions = []
        
        # If starts with kubectl
        if command_lower.startswith('kubectl'):
            parts = command.split()
            if len(parts) == 1:
                # Suggest kubectl subcommands
                suggestions.extend([f"kubectl {cmd}" for cmd in self.kubectl_commands])
            elif len(parts) == 2:
                # Suggest resources for kubectl commands
                if parts[1] in ['get', 'describe', 'delete', 'edit']:
                    suggestions.extend([f"{command} {resource}" for resource in self.kubectl_resources])
            else:
                # Suggest flags
                suggestions.extend([f"{command} {flag}" for flag in self.common_flags 
                                 if flag not in command])
        
        # If starts with helm
        elif command_lower.startswith('helm'):
            parts = command.split()
            if len(parts) == 1:
                # Suggest helm subcommands
                suggestions.extend([f"helm {cmd}" for cmd in self.helm_commands])
        
        # Partial matching for any command
        else:
            # Match kubectl commands
            for cmd in self.kubectl_commands:
                if cmd.startswith(command_lower):
                    suggestions.append(f"kubectl {cmd}")
            
            # Match helm commands
            for cmd in self.helm_commands:
                if cmd.startswith(command_lower):
                    suggestions.append(f"helm {cmd}")
        
        # Add commands from history if available
        if self.command_history_manager:
            matching_commands = self.command_history_manager.search_commands(command)
            suggestions.extend([cmd.command for cmd in matching_commands[:3]])
        
        return list(dict.fromkeys(suggestions))  # Remove duplicates while preserving order
    
    def _get_best_completion(self, command: str) -> Optional[str]:
        """Get the best completion for the current command"""
        completions = self._get_completions(command)
        return completions[0] if completions else None
    
    def _show_suggestions(self, suggestions: List[str]):
        """Display completion suggestions"""
        suggestions_display = self.query_one("#suggestions-display", Static)
        if suggestions:
            suggestion_text = "💡 Suggestions: " + " | ".join(suggestions[:3])
        else:
            suggestion_text = ""
        suggestions_display.update(suggestion_text)
    
    def _validate_command(self, command: str):
        """Validate command and show hints"""
        validation_display = self.query_one("#validation-display", Static)
        
        if not command:
            validation_display.update("")
            return
        
        command_type = self._detect_command_type(command)
        parts = command.split()
        
        if len(parts) == 1 and not command.endswith(' '):
            validation_display.update(f"ℹ️ Detected: {command_type} command")
        elif command_type == 'kubectl' and len(parts) >= 2:
            if parts[1] in self.kubectl_commands:
                validation_display.update(f"✅ Valid kubectl {parts[1]} command")
            else:
                validation_display.update(f"⚠️ Unknown kubectl subcommand: {parts[1]}")
        elif command_type == 'helm' and len(parts) >= 2:
            if parts[1] in self.helm_commands:
                validation_display.update(f"✅ Valid helm {parts[1]} command")
            else:
                validation_display.update(f"⚠️ Unknown helm subcommand: {parts[1]}")
        else:
            validation_display.update(f"ℹ️ {command_type} command ready")
    
    def _set_input_value(self, value: str):
        """Set the input field value"""
        command_input = self.query_one("#command-input", Input)
        command_input.value = value
        self.current_command = value
        self._update_suggestions(value)
        self._validate_command(value)
    
    def _clear_input(self):
        """Clear the input field"""
        self._set_input_value("")
        self.history_index = -1