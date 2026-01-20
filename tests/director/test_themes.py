"""Tests for director.themes module."""

import pytest
from director.themes import load_theme, list_available_themes, get_theme_color, get_theme_setting
from director.errors import ThemeNotFoundError


def test_load_theme_sponsor_neon():
    """Test loading sponsor_neon theme."""
    theme = load_theme("sponsor_neon")

    assert "lighting" in theme
    assert "avatar" in theme
    assert theme["lighting"]["primary_color"] == [0.0, 0.6, 1.0]
    assert theme["lighting"]["strobes_enabled"] is True


def test_load_theme_award_elegant():
    """Test loading award_elegant theme."""
    theme = load_theme("award_elegant")

    assert "lighting" in theme
    assert "avatar" in theme
    assert theme["lighting"]["strobes_enabled"] is False
    assert theme["avatar"]["reaction_intensity"] == "low"


def test_load_theme_not_found():
    """Test loading non-existent theme raises error."""
    with pytest.raises(ThemeNotFoundError):
        load_theme("nonexistent_theme")


def test_list_available_themes():
    """Test listing available themes."""
    themes = list_available_themes()

    assert "sponsor_neon" in themes
    assert "award_elegant" in themes
    assert "mashup_chaos" in themes
    assert "chill_lofi" in themes
    assert len(themes) >= 4


def test_get_theme_color():
    """Test extracting colors from theme."""
    theme = load_theme("sponsor_neon")

    primary = get_theme_color(theme, "primary_color")
    assert primary == [0.0, 0.6, 1.0]

    accent = get_theme_color(theme, "accent_color")
    assert accent == [1.0, 0.2, 0.6]


def test_get_theme_setting():
    """Test extracting specific settings from theme."""
    theme = load_theme("sponsor_neon")

    energy_mult = get_theme_setting(theme, "avatar", "energy_multiplier")
    assert energy_mult == 1.2

    zoom = get_theme_setting(theme, "camera", "zoom_on_drop")
    assert zoom is True

    # Test default value
    missing = get_theme_setting(theme, "nonexistent", "key", default=42)
    assert missing == 42
