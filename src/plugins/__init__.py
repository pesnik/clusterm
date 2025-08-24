"""
Plugin system for ClusterM - enables extensible functionality
"""

from .manager import PluginManager
from .base import BasePlugin, PluginMetadata

__all__ = ["PluginManager", "BasePlugin", "PluginMetadata"]