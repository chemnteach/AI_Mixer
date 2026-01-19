"""Tests for configuration management."""

import pytest
from pathlib import Path
from mixer.config import ConfigManager, ConfigError, reset_config


def test_config_loads_from_file(test_config_path):
    """Test loading configuration from YAML file."""
    config = ConfigManager(test_config_path)

    assert config.get("audio.sample_rate") == 44100
    assert config.get("llm.primary_provider") == "anthropic"
    assert config.get("curator.bpm_tolerance") == 0.05


def test_config_defaults_when_file_missing(tmp_path):
    """Test that defaults are used when config file is missing."""
    non_existent = tmp_path / "nonexistent.yaml"
    config = ConfigManager(non_existent)

    # Should use defaults
    assert config.get("audio.sample_rate") == 44100
    assert config.get("models.whisper_size") == "base"


def test_config_get_with_dot_notation(test_config_path):
    """Test getting values with dot notation."""
    config = ConfigManager(test_config_path)

    assert config.get("llm.anthropic_model") == "claude-3-5-sonnet-20241022"
    assert config.get("performance.enable_gpu") is False  # Set to false in test config
    assert config.get("nonexistent.key", "default") == "default"


def test_config_set_value(test_config_path):
    """Test setting configuration values."""
    config = ConfigManager(test_config_path)

    config.set("logging.level", "DEBUG")
    assert config.get("logging.level") == "DEBUG"


def test_config_get_path(test_config_path):
    """Test getting absolute paths."""
    config = ConfigManager(test_config_path)

    library_path = config.get_path("library_cache")
    assert isinstance(library_path, Path)
    assert library_path.is_absolute()


def test_config_creates_directories(tmp_path, test_config_path):
    """Test that configuration creates necessary directories."""
    config = ConfigManager(test_config_path)

    # Directories should be created
    expected_paths = [
        "./test_library_cache",
        "./test_mashups",
        "./test_chroma_db",
        "./test_library_cache/failed"
    ]

    for path_str in expected_paths:
        path = Path(path_str)
        assert path.exists()


def test_config_save(tmp_path, test_config_path):
    """Test saving configuration to file."""
    config = ConfigManager(test_config_path)

    config.set("logging.level", "DEBUG")

    save_path = tmp_path / "saved_config.yaml"
    config.save(save_path)

    assert save_path.exists()

    # Load saved config and verify
    new_config = ConfigManager(save_path)
    assert new_config.get("logging.level") == "DEBUG"


def test_config_invalid_yaml(tmp_path):
    """Test handling of invalid YAML."""
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("invalid: yaml: content: [[[")

    with pytest.raises(ConfigError):
        ConfigManager(invalid_yaml)


def test_config_deep_merge(test_config_path):
    """Test deep merging of configuration."""
    config = ConfigManager(test_config_path)

    # Partial override should preserve other values
    assert config.get("llm.primary_provider") == "anthropic"
    assert config.get("llm.timeout") == 30  # Should have default even if not in file
