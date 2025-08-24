"""
Configuration management for ClusterM
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .exceptions import ConfigError


class Config:
    """Central configuration manager"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".clusterm" / "config.yaml"
        self._config: Dict[str, Any] = {}
        self._defaults = {
            "app": {
                "theme": "dark",
                "auto_refresh": True,
                "refresh_interval": 30,
                "log_level": "INFO"
            },
            "k8s": {
                "base_path": "/app",
                "default_namespace": "default",
                "kubectl_timeout": 30,
                "helm_timeout": 60
            },
            "ui": {
                "show_timestamps": True,
                "table_max_rows": 1000,
                "log_max_lines": 5000
            },
            "plugins": {
                "enabled": [],
                "plugin_paths": []
            }
        }
        self.load()
    
    def load(self):
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self._config = yaml.safe_load(f) or {}
            else:
                self._config = {}
                self.save()  # Create default config
        except Exception as e:
            raise ConfigError(f"Failed to load config: {e}")
    
    def save(self):
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.get_all(), f, default_flow_style=False)
        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (dot notation supported)"""
        keys = key.split('.')
        value = self._config
        
        # Try user config first
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                value = None
                break
        
        # Fall back to defaults
        if value is None:
            value = self._defaults
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by key (dot notation supported)"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration with defaults merged"""
        result = self._defaults.copy()
        self._deep_merge(result, self._config)
        return result
    
    def _deep_merge(self, base: Dict, overlay: Dict):
        """Recursively merge two dictionaries"""
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value