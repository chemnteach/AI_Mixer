"""Tests for encoder.thumbnail module."""

import pytest
from encoder.thumbnail import get_thumbnail_settings


def test_get_thumbnail_settings_tiktok():
    """Test TikTok thumbnail settings."""
    settings = get_thumbnail_settings("tiktok")

    assert settings["width"] == 1080
    assert settings["height"] == 1920  # 9:16
    assert settings["quality"] >= 80


def test_get_thumbnail_settings_youtube():
    """Test YouTube thumbnail settings."""
    settings = get_thumbnail_settings("youtube")

    assert settings["width"] == 1280
    assert settings["height"] == 720  # 16:9
    assert settings["quality"] >= 80


def test_get_thumbnail_settings_unknown():
    """Test unknown platform returns YouTube default."""
    settings = get_thumbnail_settings("unknown_platform")

    # Should return YouTube defaults
    assert settings["width"] == 1280
    assert settings["height"] == 720


def test_all_platforms_have_settings():
    """Test all standard platforms have thumbnail settings."""
    platforms = ["tiktok", "reels", "shorts", "youtube"]

    for platform in platforms:
        settings = get_thumbnail_settings(platform)
        assert "width" in settings
        assert "height" in settings
        assert "quality" in settings
        assert settings["quality"] > 0
