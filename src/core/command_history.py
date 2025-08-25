"""
Command history management for storing and retrieving frequently used commands
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class CommandEntry:
    """Represents a stored command"""
    command: str
    command_type: str  # 'kubectl' or 'helm'
    description: str
    cluster: str
    namespace: str
    usage_count: int = 0
    last_used: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class CommandHistoryManager:
    """Manages command history and frequently used commands with cluster/namespace context"""
    
    def __init__(self, config_dir: Path, logger):
        self.config_dir = config_dir
        self.logger = logger
        self.history_file = config_dir / "command_history.json"
        # Commands organized by cluster -> namespace -> commands
        self.commands_by_context: Dict[str, Dict[str, List[CommandEntry]]] = defaultdict(lambda: defaultdict(list))
        self._load_history()
        
        # Current context
        self.current_cluster = "default"
        self.current_namespace = "default"
    
    def _load_history(self):
        """Load command history from file"""
        self.logger.debug(f"Loading command history from {self.history_file}")
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load commands organized by context
                    commands_data = data.get('commands_by_context', {})
                    for cluster, namespaces in commands_data.items():
                        for namespace, commands in namespaces.items():
                            self.commands_by_context[cluster][namespace] = [
                                CommandEntry(**cmd) for cmd in commands
                            ]
                    
                    # Handle legacy format migration
                    legacy_commands = data.get('commands', [])
                    if legacy_commands:
                        for cmd_data in legacy_commands:
                            # Migrate old commands to default context
                            if 'cluster' not in cmd_data:
                                cmd_data['cluster'] = 'default'
                            if 'namespace' not in cmd_data:
                                cmd_data['namespace'] = 'default'
                            cmd = CommandEntry(**cmd_data)
                            self.commands_by_context[cmd.cluster][cmd.namespace].append(cmd)
                        # Save migrated data and remove legacy
                        self.logger.info("Migrated legacy command history format")
                        self._save_history()
                        
            except Exception as e:
                self.logger.error(f"Error loading command history: {e}")
                self.commands_by_context = defaultdict(lambda: defaultdict(list))
        else:
            self.logger.debug("No existing command history file found, creating new one")
            self.commands_by_context = defaultdict(lambda: defaultdict(list))
            self._save_history()
    
    def _save_history(self):
        """Save command history to file"""
        self.logger.debug(f"Saving command history to {self.history_file}")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert nested defaultdict structure to regular dict for JSON
        commands_data = {}
        for cluster, namespaces in self.commands_by_context.items():
            commands_data[cluster] = {}
            for namespace, commands in namespaces.items():
                commands_data[cluster][namespace] = [asdict(cmd) for cmd in commands]
        
        data = {
            'commands_by_context': commands_data,
            'last_updated': datetime.now().isoformat()
        }
        try:
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug("Command history saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving command history: {e}")
    
    def set_context(self, cluster: str, namespace: str):
        """Set current cluster and namespace context"""
        self.current_cluster = cluster or "default"
        self.current_namespace = namespace or "default"
        self.logger.debug(f"Context set to cluster={self.current_cluster}, namespace={self.current_namespace}")
    
    def add_command(self, command: str, description: str = "", tags: List[str] = None, cluster: str = None, namespace: str = None):
        """Add a command to history or increment usage if exists in current context"""
        # Use provided context or current context
        context_cluster = cluster or self.current_cluster
        context_namespace = namespace or self.current_namespace
        
        # Auto-detect command type
        command_type = self._detect_command_type(command)
        
        # Check if command already exists in current context
        existing_cmd = self._find_command(command, context_cluster, context_namespace)
        if existing_cmd:
            existing_cmd.usage_count += 1
            existing_cmd.last_used = datetime.now().isoformat()
            if description and not existing_cmd.description:
                existing_cmd.description = description
            if tags:
                existing_cmd.tags.extend([tag for tag in tags if tag not in existing_cmd.tags])
        else:
            # Create new command entry
            new_cmd = CommandEntry(
                command=command,
                command_type=command_type,
                description=description,
                cluster=context_cluster,
                namespace=context_namespace,
                usage_count=1,
                last_used=datetime.now().isoformat(),
                tags=tags or []
            )
            self.commands_by_context[context_cluster][context_namespace].append(new_cmd)
            self.logger.info(f"Added new command to history: {command} (cluster={context_cluster}, namespace={context_namespace})")
        
        self._save_history()
    
    def _detect_command_type(self, command: str) -> str:
        """Auto-detect if command is kubectl or helm"""
        command_lower = command.lower().strip()
        if command_lower.startswith('kubectl'):
            return 'kubectl'
        elif command_lower.startswith('helm'):
            return 'helm'
        else:
            # Try to infer from common patterns
            if any(keyword in command_lower for keyword in ['get pods', 'get services', 'describe', 'logs', 'exec']):
                return 'kubectl'
            elif any(keyword in command_lower for keyword in ['install', 'upgrade', 'list', 'status', 'uninstall']):
                return 'helm'
            return 'kubectl'  # default
    
    def _find_command(self, command: str, cluster: str = None, namespace: str = None) -> Optional[CommandEntry]:
        """Find existing command in current context"""
        context_cluster = cluster or self.current_cluster
        context_namespace = namespace or self.current_namespace
        
        for cmd in self.commands_by_context[context_cluster][context_namespace]:
            if cmd.command == command:
                return cmd
        return None
    
    def get_current_context_commands(self) -> List[CommandEntry]:
        """Get commands for current cluster/namespace context"""
        return self.commands_by_context[self.current_cluster][self.current_namespace].copy()
    
    def get_frequent_commands(self, limit: int = 10) -> List[CommandEntry]:
        """Get most frequently used commands in current context"""
        current_commands = self.get_current_context_commands()
        return sorted(current_commands, key=lambda x: x.usage_count, reverse=True)[:limit]
    
    def get_recent_commands(self, limit: int = 10) -> List[CommandEntry]:
        """Get most recently used commands in current context"""
        current_commands = self.get_current_context_commands()
        return sorted(
            [cmd for cmd in current_commands if cmd.last_used],
            key=lambda x: x.last_used or "",
            reverse=True
        )[:limit]
    
    def get_commands_by_type(self, command_type: str) -> List[CommandEntry]:
        """Get commands filtered by type in current context"""
        current_commands = self.get_current_context_commands()
        return [cmd for cmd in current_commands if cmd.command_type == command_type]
    
    def search_commands(self, query: str) -> List[CommandEntry]:
        """Search commands by query in command text or description in current context"""
        query_lower = query.lower()
        results = []
        current_commands = self.get_current_context_commands()
        for cmd in current_commands:
            if (query_lower in cmd.command.lower() or 
                query_lower in cmd.description.lower() or
                any(query_lower in tag.lower() for tag in cmd.tags)):
                results.append(cmd)
        return results
    
    def delete_command(self, command: str):
        """Delete a command from current context"""
        current_commands = self.commands_by_context[self.current_cluster][self.current_namespace]
        self.commands_by_context[self.current_cluster][self.current_namespace] = [
            cmd for cmd in current_commands if cmd.command != command
        ]
        self._save_history()
    
    def get_all_commands(self) -> List[CommandEntry]:
        """Get all commands in current context"""
        return self.get_current_context_commands()
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of all contexts and command counts"""
        summary = {}
        for cluster, namespaces in self.commands_by_context.items():
            summary[cluster] = {}
            for namespace, commands in namespaces.items():
                summary[cluster][namespace] = len(commands)
        return summary