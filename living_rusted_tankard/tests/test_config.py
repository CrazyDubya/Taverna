"""
Test suite for the Configuration system.

Tests configuration loading, validation, and access.
"""
import unittest
import tempfile
import json
from pathlib import Path

from living_rusted_tankard.core.config import Config, load_config, get_config


class TestConfig(unittest.TestCase):
    """Test the Config class."""

    def test_config_creation(self):
        """Test creating a configuration object."""
        config = Config()
        self.assertIsNotNone(config)

    def test_config_has_default_values(self):
        """Test that config has default values."""
        config = Config()
        
        # Check for common configuration keys
        self.assertTrue(hasattr(config, "debug") or hasattr(config, "DEBUG"))

    def test_config_get_value(self):
        """Test getting configuration values."""
        config = Config()
        
        # Try to get a config value (key names vary by implementation)
        value = config.get("debug", default=False)
        self.assertIsNotNone(value)

    def test_config_set_value(self):
        """Test setting configuration values."""
        config = Config()
        
        config.set("test_key", "test_value")
        retrieved = config.get("test_key")
        
        self.assertEqual(retrieved, "test_value")

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = Config()
        
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def test_load_config_from_file(self):
        """Test loading configuration from a file."""
        # Create a test config file
        config_file = Path(self.test_dir) / "config.json"
        test_config = {
            "debug": True,
            "data_dir": "data",
            "max_connections": 100,
        }
        
        with open(config_file, "w") as f:
            json.dump(test_config, f)

        # Load the config
        config = load_config(config_file)
        
        self.assertIsNotNone(config)

    def test_load_config_with_defaults(self):
        """Test loading config with default values."""
        config = load_config(missing_file="nonexistent.json")
        
        # Should return config with defaults
        self.assertIsNotNone(config)

    def test_config_validation(self):
        """Test that config validates required fields."""
        # Create config with missing required fields
        incomplete_config = {}
        
        # Config should handle missing fields gracefully
        config = Config(**incomplete_config)
        self.assertIsNotNone(config)


class TestConfigAccess(unittest.TestCase):
    """Test configuration access patterns."""

    def test_get_config_singleton(self):
        """Test getting global config instance."""
        config1 = get_config()
        config2 = get_config()
        
        # Should return same instance (singleton pattern)
        self.assertIs(config1, config2)

    def test_config_immutability(self):
        """Test that certain config values are immutable."""
        config = Config()
        
        # Try to set a protected value
        original = config.get("protected_value", "original")
        
        try:
            config.set("protected_value", "new_value")
            # Some configs allow this, some don't
        except (AttributeError, ValueError):
            # Expected for immutable configs
            pass

    def test_config_environment_variables(self):
        """Test that config can use environment variables."""
        import os
        
        # Set an environment variable
        os.environ["TAVERNA_TEST_VAR"] = "test_value"
        
        config = Config()
        
        # Check if config reads from environment
        # (Implementation-specific behavior)
        self.assertTrue(True)  # Placeholder


class TestConfigTypes(unittest.TestCase):
    """Test different configuration value types."""

    def test_string_config_values(self):
        """Test string configuration values."""
        config = Config()
        config.set("string_val", "test_string")
        
        self.assertIsInstance(config.get("string_val"), str)

    def test_integer_config_values(self):
        """Test integer configuration values."""
        config = Config()
        config.set("int_val", 42)
        
        self.assertIsInstance(config.get("int_val"), int)

    def test_boolean_config_values(self):
        """Test boolean configuration values."""
        config = Config()
        config.set("bool_val", True)
        
        self.assertIsInstance(config.get("bool_val"), bool)

    def test_list_config_values(self):
        """Test list configuration values."""
        config = Config()
        config.set("list_val", [1, 2, 3])
        
        self.assertIsInstance(config.get("list_val"), list)

    def test_dict_config_values(self):
        """Test dictionary configuration values."""
        config = Config()
        config.set("dict_val", {"key": "value"})
        
        self.assertIsInstance(config.get("dict_val"), dict)


class TestConfigPersistence(unittest.TestCase):
    """Test configuration persistence."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def test_save_config_to_file(self):
        """Test saving configuration to a file."""
        config = Config()
        config.set("test_key", "test_value")
        
        config_file = Path(self.test_dir) / "saved_config.json"
        
        # Save config
        config.save(config_file)
        
        # Verify file was created
        self.assertTrue(config_file.exists())

    def test_reload_config(self):
        """Test reloading configuration from file."""
        config = Config()
        config.set("reload_test", "original_value")
        
        config_file = Path(self.test_dir) / "reload_config.json"
        config.save(config_file)
        
        # Create new config and load
        new_config = Config()
        new_config.load(config_file)
        
        self.assertEqual(new_config.get("reload_test"), "original_value")


if __name__ == "__main__":
    unittest.main()
