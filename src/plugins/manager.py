"""
Plugin manager for loading and managing plugins
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type
from ..core.config import Config
from ..core.logger import Logger
from ..core.events import EventBus
from ..core.exceptions import PluginError
from .base import BasePlugin


class PluginManager:
    """Manages plugin loading, enabling, and lifecycle"""
    
    def __init__(self, config: Config, event_bus: EventBus, logger: Logger):
        self.config = config
        self.event_bus = event_bus
        self.logger = logger
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}
        
        # Default plugin paths
        self.plugin_paths = [
            Path(__file__).parent / "builtin",  # Built-in plugins
            Path.home() / ".clusterm" / "plugins",  # User plugins
        ]
        
        # Add configured plugin paths
        configured_paths = self.config.get('plugins.plugin_paths', [])
        for path_str in configured_paths:
            self.plugin_paths.append(Path(path_str))
    
    def discover_plugins(self):
        """Discover all available plugins"""
        discovered_plugins = {}
        
        for plugin_path in self.plugin_paths:
            if not plugin_path.exists():
                continue
            
            self.logger.debug(f"Scanning for plugins in: {plugin_path}")
            
            for plugin_dir in plugin_path.iterdir():
                if not plugin_dir.is_dir() or plugin_dir.name.startswith('.'):
                    continue
                
                plugin_file = plugin_dir / "plugin.py"
                if not plugin_file.exists():
                    continue
                
                try:
                    plugin_class = self._load_plugin_class(plugin_dir.name, plugin_file)
                    if plugin_class:
                        discovered_plugins[plugin_dir.name] = plugin_class
                        self.logger.debug(f"Discovered plugin: {plugin_dir.name}")
                
                except Exception as e:
                    self.logger.error(f"Failed to load plugin {plugin_dir.name}: {e}")
        
        self.plugin_classes.update(discovered_plugins)
        self.logger.info(f"Discovered {len(discovered_plugins)} plugins")
        return discovered_plugins
    
    def _load_plugin_class(self, plugin_name: str, plugin_file: Path) -> Optional[Type[BasePlugin]]:
        """Load a plugin class from file"""
        module_name = f"clusterm_plugin_{plugin_name}"
        
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        if spec is None or spec.loader is None:
            raise PluginError(f"Could not load spec for plugin: {plugin_name}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Look for plugin class
        plugin_class = getattr(module, 'Plugin', None)
        if plugin_class is None:
            raise PluginError(f"Plugin {plugin_name} must define a 'Plugin' class")
        
        if not issubclass(plugin_class, BasePlugin):
            raise PluginError(f"Plugin {plugin_name} must inherit from BasePlugin")
        
        return plugin_class
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Load and initialize a plugin"""
        if plugin_name in self.plugins:
            self.logger.warning(f"Plugin {plugin_name} already loaded")
            return True
        
        if plugin_name not in self.plugin_classes:
            self.logger.error(f"Plugin {plugin_name} not found")
            return False
        
        try:
            plugin_class = self.plugin_classes[plugin_name]
            plugin_instance = plugin_class(self.config, self.event_bus, self.logger)
            
            # Check dependencies
            if not self._check_dependencies(plugin_instance):
                return False
            
            self.plugins[plugin_name] = plugin_instance
            self.logger.info(f"Loaded plugin: {plugin_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def _check_dependencies(self, plugin: BasePlugin) -> bool:
        """Check if plugin dependencies are satisfied"""
        for dep in plugin.metadata.dependencies:
            if dep not in self.plugins or not self.plugins[dep].enabled:
                self.logger.error(f"Plugin {plugin.metadata.name} requires {dep}")
                return False
        return True
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin"""
        if plugin_name not in self.plugins:
            if not self.load_plugin(plugin_name):
                return False
        
        return self.plugins[plugin_name].enable()
    
    def disable_plugin(self, plugin_name: str):
        """Disable a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].disable()
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a plugin instance"""
        return self.plugins.get(plugin_name)
    
    def get_enabled_plugins(self) -> Dict[str, BasePlugin]:
        """Get all enabled plugins"""
        return {name: plugin for name, plugin in self.plugins.items() if plugin.enabled}
    
    def load_enabled_plugins(self):
        """Load and enable plugins specified in configuration"""
        enabled_plugins = self.config.get('plugins.enabled', [])
        
        for plugin_name in enabled_plugins:
            if self.enable_plugin(plugin_name):
                self.logger.info(f"Auto-enabled plugin: {plugin_name}")
            else:
                self.logger.error(f"Failed to auto-enable plugin: {plugin_name}")
    
    def shutdown(self):
        """Shutdown all plugins"""
        for plugin in self.plugins.values():
            try:
                plugin.disable()
            except Exception as e:
                self.logger.error(f"Error shutting down plugin {plugin.metadata.name}: {e}")