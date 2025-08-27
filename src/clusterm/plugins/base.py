"""Base plugin interface and metadata
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..core.config import Config
from ..core.events import EventBus
from ..core.logger import Logger


@dataclass
class PluginMetadata:
    """Plugin metadata"""

    name: str
    version: str
    description: str
    author: str
    dependencies: list[str] = None
    ui_extensions: list[str] = None
    event_handlers: list[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.ui_extensions is None:
            self.ui_extensions = []
        if self.event_handlers is None:
            self.event_handlers = []


class BasePlugin(ABC):
    """Base class for all plugins"""

    def __init__(self, config: Config, event_bus: EventBus, logger: Logger):
        self.config = config
        self.event_bus = event_bus
        self.logger = logger
        self._enabled = False

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata"""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""

    @abstractmethod
    def cleanup(self):
        """Clean up plugin resources"""

    def enable(self) -> bool:
        """Enable the plugin"""
        if not self._enabled:
            try:
                if self.initialize():
                    self._enabled = True
                    self.logger.info(f"Plugin {self.metadata.name} enabled")
                    return True
                self.logger.error(f"Failed to initialize plugin {self.metadata.name}")
                return False
            except Exception as e:
                self.logger.error(f"Error enabling plugin {self.metadata.name}: {e}")
                return False
        return True

    def disable(self):
        """Disable the plugin"""
        if self._enabled:
            try:
                self.cleanup()
                self._enabled = False
                self.logger.info(f"Plugin {self.metadata.name} disabled")
            except Exception as e:
                self.logger.error(f"Error disabling plugin {self.metadata.name}: {e}")

    @property
    def enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self._enabled

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get plugin-specific configuration"""
        plugin_key = f"plugins.{self.metadata.name}.{key}"
        return self.config.get(plugin_key, default)

    def set_config(self, key: str, value: Any):
        """Set plugin-specific configuration"""
        plugin_key = f"plugins.{self.metadata.name}.{key}"
        self.config.set(plugin_key, value)
