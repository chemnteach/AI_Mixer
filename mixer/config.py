"""Configuration management for The Mixer."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict
from mixer.types import Config


class ConfigError(Exception):
    """Configuration-related errors."""
    pass


class ConfigManager:
    """Manages system configuration from config.yaml."""

    DEFAULT_CONFIG_PATH = Path("config.yaml")

    # Fallback configuration if config.yaml is missing
    DEFAULT_CONFIG: Config = {
        "paths": {
            "library_cache": "./library_cache",
            "mashup_output": "./mashups",
            "chroma_db": "./chroma_db",
            "failed_files": "./library_cache/failed",
        },
        "audio": {
            "sample_rate": 44100,
            "bit_depth": 16,
            "channels": 2,
            "default_format": "wav",
        },
        "models": {
            "whisper_size": "base",
            "demucs_model": "htdemucs",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        },
        "llm": {
            "primary_provider": "anthropic",
            "fallback_provider": "openai",
            "anthropic_model": "claude-3-5-sonnet-20241022",
            "openai_model": "gpt-4-turbo-preview",
            "max_retries": 3,
            "timeout": 30,
        },
        "curator": {
            "bpm_tolerance": 0.05,
            "max_stretch_ratio": 1.2,
            "default_match_criteria": "hybrid",
            "max_candidates": 5,
        },
        "engineer": {
            "default_quality": "high",
            "vocal_attenuation_db": -2.0,
            "fade_duration_sec": 4.0,
            "normalize_lufs": -14,
        },
        "performance": {
            "max_concurrent_downloads": 4,
            "enable_gpu": True,
            "fallback_to_cpu": True,
            "max_cache_size_gb": 50,
        },
        "logging": {
            "level": "INFO",
            "file": "mixer.log",
            "max_file_size_mb": 100,
            "backup_count": 5,
        },
    }

    def __init__(self, config_path: Path | None = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to config.yaml. If None, uses default location.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        self._ensure_directories()

    def _load_config(self) -> Config:
        """Load configuration from YAML file with fallback to defaults.

        Returns:
            Loaded configuration dictionary.

        Raises:
            ConfigError: If config file exists but is invalid.
        """
        if not self.config_path.exists():
            print(f"Warning: Config file not found at {self.config_path}. Using defaults.")
            return self.DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)

            if not loaded_config:
                print(f"Warning: Empty config file at {self.config_path}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()

            # Merge with defaults (loaded config overrides defaults)
            merged_config = self._deep_merge(self.DEFAULT_CONFIG, loaded_config)
            return merged_config

        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load config: {e}")

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary (defaults).
            override: Dictionary with overriding values.

        Returns:
            Merged dictionary.
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        paths = self.config["paths"]

        for path_key, path_value in paths.items():
            path = Path(path_value)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., "llm.primary_provider").
            default: Default value if key not found.

        Returns:
            Configuration value.

        Examples:
            >>> config.get("audio.sample_rate")
            44100
            >>> config.get("llm.anthropic_model")
            'claude-3-5-sonnet-20241022'
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., "logging.level").
            value: Value to set.
        """
        keys = key_path.split(".")
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def get_path(self, path_key: str) -> Path:
        """Get an absolute path from configuration.

        Args:
            path_key: Key in paths section (e.g., "library_cache").

        Returns:
            Absolute Path object.
        """
        relative_path = self.config["paths"].get(path_key)
        if not relative_path:
            raise ConfigError(f"Path '{path_key}' not found in configuration")

        return Path(relative_path).resolve()

    def save(self, path: Path | None = None) -> None:
        """Save current configuration to YAML file.

        Args:
            path: Path to save to. If None, uses loaded config path.
        """
        save_path = path or self.config_path

        try:
            with open(save_path, 'w') as f:
                yaml.safe_dump(self.config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}")


# Global configuration instance
_config_instance: ConfigManager | None = None


def get_config(config_path: Path | None = None) -> ConfigManager:
    """Get or create global configuration instance.

    Args:
        config_path: Path to config file. Only used on first call.

    Returns:
        Global ConfigManager instance.
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = ConfigManager(config_path)

    return _config_instance


def reset_config() -> None:
    """Reset global configuration instance. Useful for testing."""
    global _config_instance
    _config_instance = None
