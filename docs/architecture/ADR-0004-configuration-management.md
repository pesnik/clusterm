# ADR-0004: Configuration Management

## Status
Accepted

## Context
ClusterM needs a robust configuration system to handle:
- User preferences and settings
- Application behavior customization
- Plugin configuration
- Environment-specific settings
- Default values and validation

The configuration system must be:
- Easy to use and understand
- Persistent across application runs
- Hierarchical with defaults and overrides
- Accessible throughout the application
- Extensible for plugins

## Decision
Implement a centralized configuration management system with the following characteristics:

### Configuration Structure
```yaml
app:
  theme: dark
  auto_refresh: true
  refresh_interval: 30
  log_level: INFO

k8s:
  base_path: /app
  default_namespace: default
  kubectl_timeout: 30
  helm_timeout: 60

ui:
  show_timestamps: true
  table_max_rows: 1000
  log_max_lines: 5000

plugins:
  enabled: []
  plugin_paths: []
```

### Configuration Class Design
```python
class Config:
    def __init__(self, config_path: Optional[Path] = None)
    def load(self)
    def save(self)
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any)
    def get_all(self) -> Dict[str, Any]
```

### Key Features
1. **YAML Format**: Human-readable and editable
2. **Dot Notation**: Hierarchical access (`app.theme`, `k8s.default_namespace`)
3. **Default Values**: Built-in defaults merged with user config
4. **Automatic Persistence**: Changes saved to disk
5. **Type Safety**: Configuration values maintain their types
6. **Plugin Support**: Plugins can read/write their own config sections

## Consequences

### Positive
- **User Control**: Easy customization of application behavior
- **Persistence**: Settings maintained across application restarts
- **Flexibility**: Hierarchical structure supports complex configurations
- **Extensibility**: Plugins can store their own configuration
- **Debugging**: Configuration issues are visible in YAML file
- **Defaults**: Sensible defaults mean app works out-of-the-box

### Negative
- **File Management**: Configuration file can become large
- **Validation**: Need to handle invalid configuration gracefully
- **Migration**: Configuration schema changes require migration logic
- **Security**: Sensitive values stored in plain text

## Alternatives Considered

### 1. Environment Variables Only
- **Pros**: Standard approach, easy to override
- **Cons**: Flat namespace, not persistent, hard for complex config

### 2. Database Storage
- **Pros**: Structured, queryable, transactional
- **Cons**: Over-engineered for TUI app, external dependency

### 3. INI Files
- **Pros**: Simple, well-supported
- **Cons**: Limited structure, no nested data

### 4. JSON Files
- **Pros**: Structured, parseable
- **Cons**: Not human-friendly, no comments

## Implementation Details

### Configuration File Location
```
~/.clusterm/config.yaml  # Default location
```

### Default Configuration
```python
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
```

### Configuration Access Patterns
```python
# Simple access
theme = config.get('app.theme')
namespace = config.get('k8s.default_namespace', 'default')

# Modification
config.set('app.theme', 'light')
config.save()  # Persist changes

# Plugin configuration
plugin_config = config.get(f'plugins.{plugin_name}.settings', {})
config.set(f'plugins.{plugin_name}.enabled', True)
```

### Configuration Validation
```python
def _validate_config(self, config: Dict) -> Dict:
    # Validate log levels
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    if config.get('app', {}).get('log_level') not in valid_log_levels:
        config['app']['log_level'] = 'INFO'
    
    # Validate numeric values
    if config.get('k8s', {}).get('kubectl_timeout', 0) <= 0:
        config['k8s']['kubectl_timeout'] = 30
    
    return config
```

### Configuration Merging
```python
def get_all(self) -> Dict[str, Any]:
    result = self._defaults.copy()
    self._deep_merge(result, self._config)
    return result

def _deep_merge(self, base: Dict, overlay: Dict):
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            self._deep_merge(base[key], value)
        else:
            base[key] = value
```

### Error Handling
```python
def load(self):
    try:
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}
            self.save()  # Create default config
    except Exception as e:
        raise ConfigError(f"Failed to load config: {e}")
```

## Configuration Examples

### User Customization
```yaml
# ~/.clusterm/config.yaml
app:
  theme: light
  log_level: DEBUG

k8s:
  base_path: /home/user/k8s
  default_namespace: production

plugins:
  enabled:
    - monitoring-integration
    - slack-notifications
```

### Plugin Configuration
```yaml
plugins:
  monitoring-integration:
    prometheus_url: http://prometheus:9090
    alert_threshold: 80
    
  slack-notifications:
    webhook_url: https://hooks.slack.com/...
    channel: "#alerts"
```

### Environment Overrides
```python
# Environment variables can override config
config_value = os.getenv('CLUSTERM_LOG_LEVEL', config.get('app.log_level'))
```

## Configuration Schema Evolution

### Version 0.1.0 → 0.2.0 Migration
```python
def migrate_config(config: Dict, from_version: str, to_version: str) -> Dict:
    if from_version == "0.1.0" and to_version == "0.2.0":
        # Rename old key
        if 'old_key' in config:
            config['new_key'] = config.pop('old_key')
        
        # Add new default sections
        if 'new_section' not in config:
            config['new_section'] = {'enabled': True}
    
    return config
```

## Security Considerations
- Sensitive values (API keys, passwords) should use environment variables
- Configuration file permissions should be user-readable only
- Validate all configuration values to prevent injection attacks
- Document security implications of configuration changes

## Testing Strategy
```python
def test_config_get_set(temp_config_dir):
    config = Config(temp_config_dir / "config.yaml")
    
    # Test setting and getting
    config.set('test.value', 'hello')
    assert config.get('test.value') == 'hello'
    
    # Test persistence
    config.save()
    config2 = Config(temp_config_dir / "config.yaml")
    assert config2.get('test.value') == 'hello'
```

## Future Enhancements
- Configuration GUI/TUI editor
- Configuration validation schemas
- Remote configuration sources
- Configuration encryption for sensitive values
- Configuration templates and profiles

## Related ADRs
- ADR-0001: Modular Architecture
- ADR-0002: Plugin System
- ADR-0005: UI Component Architecture