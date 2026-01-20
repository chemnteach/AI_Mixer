"""Tests for studio.renderer module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from studio.renderer import (
    find_blender_executable,
    get_render_settings,
    estimate_render_time,
    check_render_health
)
from studio.errors import BlenderNotFoundError


def test_find_blender_executable():
    """Test finding Blender executable."""
    # May or may not find it depending on system
    exe = find_blender_executable()

    if exe:
        assert isinstance(exe, str)
        assert "blender" in exe.lower()


def test_get_render_settings_short():
    """Test getting render settings for short format."""
    settings = get_render_settings("short")

    assert settings["fps"] == 30
    assert settings["resolution"] == (1080, 1920)  # 9:16
    assert settings["render_engine"] == "EEVEE"
    assert settings["output_format"] == "MP4"


def test_get_render_settings_long():
    """Test getting render settings for long format."""
    settings = get_render_settings("long")

    assert settings["fps"] == 30
    assert settings["resolution"] == (1920, 1080)  # 16:9
    assert settings["output_format"] == "MP4"


def test_estimate_render_time_short():
    """Test render time estimation for short format."""
    duration = 30.0
    estimated = estimate_render_time(duration, "short")

    # Should be 5-10x real time
    assert 150.0 <= estimated <= 300.0


def test_estimate_render_time_long():
    """Test render time estimation for long format."""
    duration = 60.0
    estimated = estimate_render_time(duration, "long")

    # Should be slightly longer than short format
    assert 400.0 <= estimated <= 600.0


def test_check_render_health_missing():
    """Test health check on missing file."""
    health = check_render_health("/nonexistent/video.mp4")

    assert health["exists"] is False
    assert health["size_mb"] == 0.0
    assert health["is_video"] is False


def test_check_render_health_valid(tmp_path):
    """Test health check on valid-looking video file."""
    video_file = tmp_path / "test.mp4"
    # Create file >500KB
    video_file.write_bytes(b"x" * (600 * 1024))

    health = check_render_health(str(video_file))

    assert health["exists"] is True
    assert health["size_mb"] > 0.5
    assert health["is_video"] is True


@patch('studio.renderer.subprocess.run')
@patch('studio.renderer.validate_assets_strict')
@patch('studio.renderer.get_blender_config')
def test_render_video_placeholder_mode(mock_blender_config, mock_validate, mock_run, tmp_path):
    """Test rendering in placeholder mode (skips asset validation)."""
    from studio.renderer import render_video

    # Mock Blender config
    mock_blender_config.return_value = {
        "executable": "blender",
        "timeout_sec": 600,
        "background_mode": True
    }

    # Mock successful render
    output_file = tmp_path / "test.mp4"
    output_file.write_bytes(b"x" * (1024 * 1024))  # 1MB file

    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    # Placeholder mode should skip validation
    result = render_video(
        timeline_path="timeline.json",
        output_path=str(output_file),
        placeholder_mode=True
    )

    # Should NOT call validate_assets_strict in placeholder mode
    mock_validate.assert_not_called()
