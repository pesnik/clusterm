"""
Tests for configuration management
"""

from src.core.config import Config


class TestConfig:
    """Test configuration management"""

    def test_default_config(self, temp_config_dir):
        """Test default configuration values"""
        config = Config(temp_config_dir / "config.yaml")

        assert config.get('app.theme') == 'dark'
        assert config.get('app.auto_refresh')
        assert config.get('k8s.default_namespace') == 'default'

    def test_config_get_set(self, temp_config_dir):
        """Test getting and setting configuration values"""
        config = Config(temp_config_dir / "config.yaml")

        # Test setting and getting
        config.set('test.value', 'hello')
        assert config.get('test.value') == 'hello'

        # Test nested keys
        config.set('nested.deep.value', 42)
        assert config.get('nested.deep.value') == 42

    def test_config_persistence(self, temp_config_dir):
        """Test configuration persistence"""
        config_path = temp_config_dir / "config.yaml"

        # Create and save config
        config1 = Config(config_path)
        config1.set('persistent.value', 'test')
        config1.save()

        # Load new instance and verify
        config2 = Config(config_path)
        assert config2.get('persistent.value') == 'test'

    def test_config_defaults_override(self, temp_config_dir):
        """Test that user config overrides defaults"""
        config = Config(temp_config_dir / "config.yaml")

        # Change from default
        config.set('app.theme', 'light')
        assert config.get('app.theme') == 'light'

        # Unchanged default should still work
        assert config.get('app.auto_refresh')
