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
        self.logger = logger
        self.logger.debug("PluginManager.__init__: Entry - Initializing PluginManager")
        
        self.config = config
        self.event_bus = event_bus
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}
        
        self.logger.debug("PluginManager.__init__: Core components initialized")
        
        # Default plugin paths
        self.plugin_paths = [
            Path(__file__).parent / "builtin",  # Built-in plugins
            Path.home() / ".clusterm" / "plugins",  # User plugins
        ]
        
        self.logger.debug(f"PluginManager.__init__: Default plugin paths: {[str(p) for p in self.plugin_paths]}")
        
        # Add configured plugin paths
        configured_paths = self.config.get('plugins.plugin_paths', [])
        self.logger.debug(f"PluginManager.__init__: Configured plugin paths: {configured_paths}")
        
        for path_str in configured_paths:
            self.plugin_paths.append(Path(path_str))
            
        self.logger.info(f"PluginManager.__init__: PluginManager initialized with {len(self.plugin_paths)} plugin paths")
    
    def discover_plugins(self):
        """Discover all available plugins"""
        self.logger.debug("PluginManager.discover_plugins: Entry - Starting plugin discovery")
        discovered_plugins = {}
        
        for i, plugin_path in enumerate(self.plugin_paths):
            self.logger.debug(f"PluginManager.discover_plugins: Scanning path {i+1}/{len(self.plugin_paths)}: {plugin_path}")
            
            if not plugin_path.exists():
                self.logger.debug(f"PluginManager.discover_plugins: Plugin path does not exist: {plugin_path}")
                continue
            
            plugin_dirs = list(plugin_path.iterdir())
            self.logger.debug(f"PluginManager.discover_plugins: Found {len(plugin_dirs)} items in {plugin_path}")
            
            for j, plugin_dir in enumerate(plugin_dirs):
                if not plugin_dir.is_dir() or plugin_dir.name.startswith('.'):
                    self.logger.debug(f"PluginManager.discover_plugins: Skipping {plugin_dir.name} - not a valid plugin directory")
                    continue
                
                plugin_file = plugin_dir / "plugin.py"
                if not plugin_file.exists():
                    self.logger.debug(f"PluginManager.discover_plugins: Skipping {plugin_dir.name} - no plugin.py file found")
                    continue
                
                self.logger.debug(f"PluginManager.discover_plugins: Processing plugin {j+1}/{len(plugin_dirs)}: {plugin_dir.name}")
                
                try:
                    self.logger.debug(f"PluginManager.discover_plugins: Loading plugin class for: {plugin_dir.name}")
                    plugin_class = self._load_plugin_class(plugin_dir.name, plugin_file)
                    
                    if plugin_class:
                        discovered_plugins[plugin_dir.name] = plugin_class
                        self.logger.info(f"PluginManager.discover_plugins: Discovered plugin: {plugin_dir.name}")
                    else:
                        self.logger.warning(f"PluginManager.discover_plugins: Plugin class not found for: {plugin_dir.name}")
                
                except Exception as e:
                    self.logger.error(f"PluginManager.discover_plugins: Failed to load plugin {plugin_dir.name}: {e}", extra={
                        "error_type": type(e).__name__,
                        "plugin_name": plugin_dir.name,
                        "plugin_file": str(plugin_file)
                    })
        
        self.plugin_classes.update(discovered_plugins)
        self.logger.info(f"PluginManager.discover_plugins: Discovery complete - discovered {len(discovered_plugins)} plugins: {list(discovered_plugins.keys())}")
        return discovered_plugins
    
    def _load_plugin_class(self, plugin_name: str, plugin_file: Path) -> Optional[Type[BasePlugin]]:
        """Load a plugin class from file"""
        self.logger.debug(f"PluginManager._load_plugin_class: Entry - Loading {plugin_name} from {plugin_file}")
        
        module_name = f"clusterm_plugin_{plugin_name}"
        self.logger.debug(f"PluginManager._load_plugin_class: Module name: {module_name}")
        
        try:
            self.logger.debug(f"PluginManager._load_plugin_class: Creating module spec for {plugin_name}")
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            
            if spec is None or spec.loader is None:
                raise PluginError(f"Could not load spec for plugin: {plugin_name}")
            
            self.logger.debug(f"PluginManager._load_plugin_class: Module spec created successfully")
        
            self.logger.debug(f"PluginManager._load_plugin_class: Creating module from spec")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            
            self.logger.debug(f"PluginManager._load_plugin_class: Executing module")
            spec.loader.exec_module(module)
        
            # Look for plugin class
            self.logger.debug(f"PluginManager._load_plugin_class: Looking for Plugin class in {plugin_name}")
            plugin_class = getattr(module, 'Plugin', None)
            
            if plugin_class is None:
                raise PluginError(f"Plugin {plugin_name} must define a 'Plugin' class")
            
            self.logger.debug(f"PluginManager._load_plugin_class: Validating Plugin class inheritance")
            if not issubclass(plugin_class, BasePlugin):
                raise PluginError(f"Plugin {plugin_name} must inherit from BasePlugin")
            
            self.logger.info(f"PluginManager._load_plugin_class: Successfully loaded plugin class: {plugin_name}")
            return plugin_class
            
        except Exception as e:
            self.logger.error(f"PluginManager._load_plugin_class: Error loading plugin class {plugin_name}: {e}", extra={
                "error_type": type(e).__name__,
                "plugin_name": plugin_name,
                "plugin_file": str(plugin_file)
            })
            raise
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Load and initialize a plugin"""
        self.logger.debug(f"PluginManager.load_plugin: Entry - Loading plugin: {plugin_name}")
        
        if plugin_name in self.plugins:
            self.logger.warning(f"PluginManager.load_plugin: Plugin {plugin_name} already loaded")
            return True
        
        if plugin_name not in self.plugin_classes:
            self.logger.error(f"PluginManager.load_plugin: Plugin {plugin_name} not found in discovered classes")
            return False
        
        try:
            self.logger.debug(f"PluginManager.load_plugin: Getting plugin class for {plugin_name}")
            plugin_class = self.plugin_classes[plugin_name]
            
            self.logger.debug(f"PluginManager.load_plugin: Creating plugin instance for {plugin_name}")
            plugin_instance = plugin_class(self.config, self.event_bus, self.logger)
            
            # Check dependencies
            self.logger.debug(f"PluginManager.load_plugin: Checking dependencies for {plugin_name}")
            if not self._check_dependencies(plugin_instance):
                self.logger.error(f"PluginManager.load_plugin: Dependency check failed for {plugin_name}")
                return False
            
            self.plugins[plugin_name] = plugin_instance
            self.logger.info(f"PluginManager.load_plugin: Successfully loaded plugin: {plugin_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"PluginManager.load_plugin: Failed to load plugin {plugin_name}: {e}", extra={
                "error_type": type(e).__name__,
                "plugin_name": plugin_name
            })
            return False
    
    def _check_dependencies(self, plugin: BasePlugin) -> bool:
        """Check if plugin dependencies are satisfied"""
        self.logger.debug(f"PluginManager._check_dependencies: Entry - Checking dependencies for {plugin.metadata.name}")
        
        dependencies = plugin.metadata.dependencies
        self.logger.debug(f"PluginManager._check_dependencies: Plugin {plugin.metadata.name} has {len(dependencies)} dependencies: {dependencies}")
        
        for i, dep in enumerate(dependencies):
            self.logger.debug(f"PluginManager._check_dependencies: Checking dependency {i+1}/{len(dependencies)}: {dep}")
            
            if dep not in self.plugins:
                self.logger.error(f"PluginManager._check_dependencies: Plugin {plugin.metadata.name} requires {dep}, but it's not loaded")
                return False
                
            if not self.plugins[dep].enabled:
                self.logger.error(f"PluginManager._check_dependencies: Plugin {plugin.metadata.name} requires {dep}, but it's not enabled")
                return False
                
            self.logger.debug(f"PluginManager._check_dependencies: Dependency {dep} satisfied")
        
        self.logger.info(f"PluginManager._check_dependencies: All dependencies satisfied for {plugin.metadata.name}")
        return True
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin"""
        self.logger.debug(f"PluginManager.enable_plugin: Entry - Enabling plugin: {plugin_name}")
        
        if plugin_name not in self.plugins:
            self.logger.debug(f"PluginManager.enable_plugin: Plugin {plugin_name} not loaded, attempting to load")
            if not self.load_plugin(plugin_name):
                self.logger.error(f"PluginManager.enable_plugin: Failed to load plugin {plugin_name}")
                return False
        
        try:
            self.logger.debug(f"PluginManager.enable_plugin: Calling enable() on plugin {plugin_name}")
            result = self.plugins[plugin_name].enable()
            
            if result:
                self.logger.info(f"PluginManager.enable_plugin: Successfully enabled plugin: {plugin_name}")
            else:
                self.logger.warning(f"PluginManager.enable_plugin: Plugin {plugin_name} enable() returned False")
                
            return result
            
        except Exception as e:
            self.logger.error(f"PluginManager.enable_plugin: Error enabling plugin {plugin_name}: {e}", extra={
                "error_type": type(e).__name__,
                "plugin_name": plugin_name
            })
            return False
    
    def disable_plugin(self, plugin_name: str):
        """Disable a plugin"""
        self.logger.debug(f"PluginManager.disable_plugin: Entry - Disabling plugin: {plugin_name}")
        
        if plugin_name in self.plugins:
            try:
                self.logger.debug(f"PluginManager.disable_plugin: Calling disable() on plugin {plugin_name}")
                self.plugins[plugin_name].disable()
                self.logger.info(f"PluginManager.disable_plugin: Successfully disabled plugin: {plugin_name}")
                
            except Exception as e:
                self.logger.error(f"PluginManager.disable_plugin: Error disabling plugin {plugin_name}: {e}", extra={
                    "error_type": type(e).__name__,
                    "plugin_name": plugin_name
                })
        else:
            self.logger.warning(f"PluginManager.disable_plugin: Plugin {plugin_name} not found in loaded plugins")
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a plugin instance"""
        self.logger.debug(f"PluginManager.get_plugin: Getting plugin: {plugin_name}")
        
        plugin = self.plugins.get(plugin_name)
        if plugin:
            self.logger.debug(f"PluginManager.get_plugin: Found plugin {plugin_name}, enabled: {plugin.enabled}")
        else:
            self.logger.debug(f"PluginManager.get_plugin: Plugin {plugin_name} not found")
            
        return plugin
    
    def get_enabled_plugins(self) -> Dict[str, BasePlugin]:
        """Get all enabled plugins"""
        self.logger.debug("PluginManager.get_enabled_plugins: Entry")
        
        enabled_plugins = {name: plugin for name, plugin in self.plugins.items() if plugin.enabled}
        
        self.logger.debug(f"PluginManager.get_enabled_plugins: Found {len(enabled_plugins)} enabled plugins: {list(enabled_plugins.keys())}")
        return enabled_plugins
    
    def load_enabled_plugins(self):
        """Load and enable plugins specified in configuration"""
        self.logger.debug("PluginManager.load_enabled_plugins: Entry - Loading configured plugins")
        
        enabled_plugins = self.config.get('plugins.enabled', [])
        self.logger.debug(f"PluginManager.load_enabled_plugins: Configuration specifies {len(enabled_plugins)} plugins to enable: {enabled_plugins}")
        
        for i, plugin_name in enumerate(enabled_plugins):
            self.logger.debug(f"PluginManager.load_enabled_plugins: Enabling plugin {i+1}/{len(enabled_plugins)}: {plugin_name}")
            
            if self.enable_plugin(plugin_name):
                self.logger.info(f"PluginManager.load_enabled_plugins: Auto-enabled plugin: {plugin_name}")
            else:
                self.logger.error(f"PluginManager.load_enabled_plugins: Failed to auto-enable plugin: {plugin_name}")
                
        enabled_count = len(self.get_enabled_plugins())
        self.logger.info(f"PluginManager.load_enabled_plugins: Plugin loading complete - {enabled_count} plugins enabled")
    
    def shutdown(self):
        """Shutdown all plugins"""
        self.logger.debug(f"PluginManager.shutdown: Entry - Shutting down {len(self.plugins)} plugins")
        
        for i, (plugin_name, plugin) in enumerate(self.plugins.items()):
            self.logger.debug(f"PluginManager.shutdown: Shutting down plugin {i+1}/{len(self.plugins)}: {plugin_name}")
            
            try:
                plugin.disable()
                self.logger.debug(f"PluginManager.shutdown: Successfully shutdown plugin: {plugin_name}")
                
            except Exception as e:
                self.logger.error(f"PluginManager.shutdown: Error shutting down plugin {plugin.metadata.name}: {e}", extra={
                    "error_type": type(e).__name__,
                    "plugin_name": plugin_name
                })
                
        self.logger.info("PluginManager.shutdown: All plugins shutdown complete")