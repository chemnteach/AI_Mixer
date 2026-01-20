"""Tests for director.safety module."""

import pytest
from pathlib import Path
from director.safety import validate_event_safe, generate_usage_manifest, check_strobe_safety
from director.errors import SafetyViolationError


def test_validate_event_safe_mashup_mode():
    """Test that non-event modes pass validation."""
    timeline = {
        "meta": {"mode": "mashup", "theme": "mashup_chaos", "format": "short", "duration_sec": 30.0, "bpm": 128.0},
        "audio": {"file": "./mashups/test.wav", "sections": []},
        "beats": {"timestamps": [], "bpm": 128.0, "downbeats": []},
        "events": [],
        "camera": {"base_shot": "medium", "movements": []},
        "avatar": {"base_action": "idle_bob", "triggers": []},
        "lighting": {"preset": "mashup_chaos", "primary_color": [1.0, 0.0, 0.5], "intensity_curve": []}
    }

    is_safe, warnings = validate_event_safe(timeline, mode="mashup", strict=False)
    assert is_safe is True
    assert len(warnings) == 0


def test_validate_event_safe_passes():
    """Test event-safe validation passes for appropriate theme."""
    timeline = {
        "meta": {"mode": "event", "theme": "award_elegant", "format": "short", "duration_sec": 30.0, "bpm": 128.0},
        "audio": {"file": "./library/single_song.wav", "sections": []},
        "beats": {"timestamps": [], "bpm": 128.0, "downbeats": []},
        "events": [],
        "camera": {"base_shot": "medium", "movements": []},
        "avatar": {"base_action": "idle_bob", "triggers": []},
        "lighting": {"preset": "award_elegant", "primary_color": [1.0, 0.95, 0.85], "intensity_curve": []}
    }

    is_safe, warnings = validate_event_safe(timeline, mode="event", strict=False)
    assert is_safe is True
    assert len(warnings) == 0


def test_validate_event_safe_fails_theme():
    """Test event-safe validation catches inappropriate theme."""
    timeline = {
        "meta": {"mode": "event", "theme": "mashup_chaos", "format": "short", "duration_sec": 30.0, "bpm": 128.0},
        "audio": {"file": "./library/test.wav", "sections": []},
        "beats": {"timestamps": [], "bpm": 128.0, "downbeats": []},
        "events": [],
        "camera": {"base_shot": "medium", "movements": []},
        "avatar": {"base_action": "idle_bob", "triggers": []},
        "lighting": {"preset": "mashup_chaos", "primary_color": [1.0, 0.0, 0.5], "intensity_curve": []}
    }

    is_safe, warnings = validate_event_safe(timeline, mode="event", strict=False)
    assert is_safe is False
    assert len(warnings) > 0
    assert any("mashup_chaos" in w for w in warnings)


def test_validate_event_safe_strict_raises():
    """Test strict mode raises exception on violations."""
    timeline = {
        "meta": {"mode": "event", "theme": "sponsor_neon", "format": "short", "duration_sec": 30.0, "bpm": 128.0},
        "audio": {"file": "./library/test.wav", "sections": []},
        "beats": {"timestamps": [], "bpm": 128.0, "downbeats": []},
        "events": [],
        "camera": {"base_shot": "medium", "movements": []},
        "avatar": {"base_action": "idle_bob", "triggers": []},
        "lighting": {"preset": "sponsor_neon", "primary_color": [0.0, 0.6, 1.0], "intensity_curve": []}
    }

    with pytest.raises(SafetyViolationError):
        validate_event_safe(timeline, mode="event", strict=True)


def test_generate_usage_manifest(tmp_path):
    """Test usage manifest generation."""
    output_path = tmp_path / "test_manifest.txt"

    generate_usage_manifest(
        song_a_id="song_a",
        song_b_id="song_b",
        output_path=output_path,
        client_name="Test Client",
        event_type="Wedding"
    )

    assert output_path.exists()
    content = output_path.read_text()
    assert "song_a" in content
    assert "song_b" in content
    assert "Test Client" in content
    assert "Wedding" in content


def test_check_strobe_safety():
    """Test strobe safety checking."""
    timeline_safe = {
        "meta": {"theme": "award_elegant", "mode": "event", "format": "short", "duration_sec": 30.0, "bpm": 128.0}
    }

    warnings = check_strobe_safety(timeline_safe)
    assert len(warnings) == 0

    timeline_strobes = {
        "meta": {"theme": "mashup_chaos", "mode": "event", "format": "short", "duration_sec": 30.0, "bpm": 128.0}
    }

    warnings = check_strobe_safety(timeline_strobes)
    assert len(warnings) > 0
    assert any("strobe" in w.lower() for w in warnings)
