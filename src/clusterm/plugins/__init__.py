"""Plugin system for ClusterM - enables extensible functionality
"""

from .base import BasePlugin, PluginMetadata
from .manager import PluginManager

__all__ = ["BasePlugin", "PluginManager", "PluginMetadata"]
