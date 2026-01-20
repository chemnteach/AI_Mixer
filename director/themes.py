"""Theme loading and management for Director."""

import yaml
from pathlib import Path
from typing import Dict, Any

from director.types import ThemeConfig
from director.errors import ThemeNotFoundError


def get_theme_path(theme_name: str) -> Path:
    """Get path to theme config file.

    Args:
        theme_name: Name of theme (without .yaml extension)

    Returns:
        Path to theme config file
    """
    themes_dir = Path(__file__).parent.parent / "config" / "themes"
    theme_file = themes_dir / f"{theme_name}.yaml"
    return theme_file


def load_theme(theme_name: str) -> ThemeConfig:
    """Load theme configuration from YAML file.

    Args:
        theme_name: Name of theme to load (e.g., "sponsor_neon")

    Returns:
        ThemeConfig dictionary with lighting, avatar, camera settings

    Raises:
        ThemeNotFoundError: If theme file doesn't exist
        yaml.YAMLError: If theme file is invalid YAML
    """
    theme_path = get_theme_path(theme_name)

    if not theme_path.exists():
        available_themes = list_available_themes()
        raise ThemeNotFoundError(
            f"Theme '{theme_name}' not found at {theme_path}\n"
            f"Available themes: {', '.join(available_themes)}"
        )

    with open(theme_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def list_available_themes() -> list[str]:
    """List all available theme names.

    Returns:
        List of theme names (without .yaml extension)
    """
    themes_dir = Path(__file__).parent.parent / "config" / "themes"

    if not themes_dir.exists():
        return []

    theme_files = themes_dir.glob("*.yaml")
    return [f.stem for f in theme_files]


def get_theme_color(theme: ThemeConfig, color_key: str = "primary_color") -> list[float]:
    """Extract color from theme config.

    Args:
        theme: Theme configuration
        color_key: Which color to extract (primary_color, accent_color, etc.)

    Returns:
        RGB color as [R, G, B] in 0-1 range
    """
    return theme.get("lighting", {}).get(color_key, [1.0, 1.0, 1.0])


def get_theme_setting(theme: ThemeConfig, section: str, key: str, default: Any = None) -> Any:
    """Get a specific setting from theme config.

    Args:
        theme: Theme configuration
        section: Section name (lighting, avatar, camera)
        key: Setting key within section
        default: Default value if not found

    Returns:
        Setting value or default
    """
    return theme.get(section, {}).get(key, default)
