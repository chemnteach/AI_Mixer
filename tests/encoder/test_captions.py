"""Tests for encoder.captions module."""

import pytest
from pathlib import Path
from encoder.captions import (
    load_caption_styles,
    get_caption_style,
    format_vtt_timestamp,
    create_simple_vtt,
    validate_vtt
)
from encoder.errors import CaptionError


def test_load_caption_styles():
    """Test loading caption styles from config."""
    styles = load_caption_styles()

    assert "tiktok" in styles
    assert "reels" in styles
    assert "youtube" in styles
    assert "default" in styles


def test_get_caption_style_tiktok():
    """Test getting TikTok caption style."""
    style = get_caption_style("tiktok")

    assert style["font"] == "Montserrat-Bold"
    assert style["size"] == 72
    assert style["position"] == "center_bottom"
    assert "color" in style


def test_get_caption_style_youtube():
    """Test getting YouTube caption style."""
    style = get_caption_style("youtube")

    assert "font" in style
    assert "size" in style


def test_get_caption_style_unknown():
    """Test getting style for unknown platform returns default."""
    style = get_caption_style("unknown_platform")

    # Should return default style
    assert "font" in style


def test_format_vtt_timestamp():
    """Test VTT timestamp formatting."""
    # 0 seconds
    assert format_vtt_timestamp(0.0) == "00:00:00.000"

    # 1 minute 30.5 seconds
    assert format_vtt_timestamp(90.5) == "00:01:30.500"

    # 1 hour 2 minutes 3.123 seconds
    assert format_vtt_timestamp(3723.123) == "01:02:03.123"


def test_create_simple_vtt(tmp_path):
    """Test creating simple VTT file."""
    output_path = tmp_path / "test.vtt"

    result = create_simple_vtt(
        text="Test caption",
        duration=30.0,
        output_path=str(output_path)
    )

    assert result.exists()

    content = result.read_text()
    assert "WEBVTT" in content
    assert "Test caption" in content
    assert "-->" in content


def test_validate_vtt_valid(tmp_path):
    """Test VTT validation on valid file."""
    vtt_file = tmp_path / "valid.vtt"
    create_simple_vtt("Test", 10.0, str(vtt_file))

    assert validate_vtt(str(vtt_file)) is True


def test_validate_vtt_invalid(tmp_path):
    """Test VTT validation on invalid file."""
    invalid_file = tmp_path / "invalid.vtt"
    invalid_file.write_text("Not a VTT file")

    assert validate_vtt(str(invalid_file)) is False


def test_validate_vtt_missing():
    """Test VTT validation on missing file."""
    assert validate_vtt("/nonexistent/file.vtt") is False
