"""Tests for encoder.platform module."""

import pytest
from encoder.platform import (
    PLATFORM_SETTINGS,
    find_ffmpeg_executable,
    check_codec_support,
    get_video_info
)
from encoder.errors import PlatformError


def test_platform_settings_structure():
    """Test that all platforms have required settings."""
    required_keys = ["resolution", "video_bitrate", "audio_bitrate", "burn_captions", "fps"]

    for platform, settings in PLATFORM_SETTINGS.items():
        for key in required_keys:
            assert key in settings, f"Platform {platform} missing {key}"


def test_platform_settings_tiktok():
    """Test TikTok platform settings."""
    settings = PLATFORM_SETTINGS["tiktok"]

    assert settings["resolution"] == (1080, 1920)  # 9:16
    assert settings["burn_captions"] is True
    assert settings["fps"] == 30
    assert settings["max_duration"] == 180


def test_platform_settings_youtube():
    """Test YouTube platform settings."""
    settings = PLATFORM_SETTINGS["youtube"]

    assert settings["resolution"] == (1920, 1080)  # 16:9
    assert settings["burn_captions"] is False  # Soft subtitles
    assert settings["max_duration"] is None  # Unlimited


def test_find_ffmpeg_executable():
    """Test finding FFmpeg executable."""
    # May or may not find it depending on system
    exe = find_ffmpeg_executable()

    if exe:
        assert isinstance(exe, str)
        assert "ffmpeg" in exe.lower()


def test_check_codec_support():
    """Test codec support checking."""
    codecs = check_codec_support()

    assert isinstance(codecs, dict)
    assert "h264" in codecs
    assert "aac" in codecs
    assert isinstance(codecs["h264"], bool)


def test_get_video_info_missing():
    """Test video info on missing file."""
    info = get_video_info("/nonexistent/video.mp4")

    assert info["exists"] is False
    assert info["duration"] == 0.0
    assert info["size_mb"] == 0.0


def test_get_video_info_invalid(tmp_path):
    """Test video info on non-video file."""
    fake_video = tmp_path / "fake.mp4"
    fake_video.write_bytes(b"not a video")

    info = get_video_info(str(fake_video))

    # Should handle gracefully (may return exists=False or zero values)
    assert "exists" in info
    assert "size_mb" in info
    assert "duration" in info
