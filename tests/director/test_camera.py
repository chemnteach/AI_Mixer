"""Tests for director.camera module."""

import pytest
from director.camera import (
    generate_zoom_on_drop,
    generate_retention_nudges,
    generate_camera_paths,
    optimize_camera_movements
)
from director.themes import load_theme


def test_generate_zoom_on_drop():
    """Test zoom generation for drop events."""
    events = [
        {"t": 10.0, "type": "drop", "intensity": "high", "visual_trigger": "drop_reaction", "reason": "test"},
        {"t": 20.0, "type": "drop", "intensity": "medium", "visual_trigger": "drop_reaction", "reason": "test"},
        {"t": 30.0, "type": "drop", "intensity": "low", "visual_trigger": "drop_reaction", "reason": "test"}
    ]

    movements = generate_zoom_on_drop(events, zoom_duration=2.0)

    # Should have zoom in + zoom out for high and medium intensity (4 movements total)
    assert len(movements) == 4

    # Check first zoom pair
    assert movements[0]["action"] == "zoom_in"
    assert movements[0]["t"] == 10.0
    assert movements[1]["action"] == "zoom_out"
    assert movements[1]["t"] == 12.0  # After 2s zoom


def test_generate_retention_nudges_camera():
    """Test camera nudge generation for retention."""
    events = [
        {"t": 25.0, "type": "retention_nudge", "intensity": "low", "visual_trigger": "test", "reason": "test"},
        {"t": 50.0, "type": "retention_nudge", "intensity": "low", "visual_trigger": "test", "reason": "test"}
    ]

    movements = generate_retention_nudges(events)

    assert len(movements) == 2
    assert movements[0]["action"] == "nudge_left"
    assert movements[1]["action"] == "nudge_right"  # Alternates


def test_generate_camera_paths():
    """Test complete camera path generation."""
    events = [
        {"t": 10.0, "type": "drop", "intensity": "high", "visual_trigger": "drop_reaction", "reason": "test"},
        {"t": 25.0, "type": "retention_nudge", "intensity": "low", "visual_trigger": "test", "reason": "test"}
    ]

    theme = load_theme("sponsor_neon")
    camera_data = generate_camera_paths(events, theme)

    assert "base_shot" in camera_data
    assert "movements" in camera_data
    assert camera_data["base_shot"] == "medium"
    assert len(camera_data["movements"]) > 0


def test_generate_camera_paths_theme_disabled():
    """Test camera paths when theme disables features."""
    events = [
        {"t": 10.0, "type": "drop", "intensity": "high", "visual_trigger": "drop_reaction", "reason": "test"}
    ]

    theme = load_theme("award_elegant")  # Has zoom_on_drop: false
    camera_data = generate_camera_paths(events, theme)

    # Should have no zoom movements
    zoom_movements = [m for m in camera_data["movements"] if "zoom" in m["action"]]
    assert len(zoom_movements) == 0


def test_optimize_camera_movements():
    """Test optimization removes overlapping movements."""
    movements = [
        {"t": 0.0, "action": "zoom_in", "duration": 2.0},
        {"t": 1.0, "action": "nudge_left", "duration": 1.0},  # Overlaps
        {"t": 3.0, "action": "zoom_out", "duration": 1.0}     # Doesn't overlap
    ]

    optimized = optimize_camera_movements(movements)

    # Should remove the overlapping nudge
    assert len(optimized) == 2
    assert optimized[0]["action"] == "zoom_in"
    assert optimized[1]["action"] == "zoom_out"
