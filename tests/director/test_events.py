"""Tests for director.events module."""

import pytest
from director.events import (
    detect_energy_drop,
    detect_section_changes,
    detect_hard_start,
    generate_retention_nudges,
    generate_events_from_sections,
    filter_events_by_intensity
)


def test_detect_energy_drop():
    """Test energy drop detection."""
    sections = [
        {"start_time": 0.0, "energy_level": 0.3, "section_type": "intro", "emotional_tone": "calm"},
        {"start_time": 10.0, "energy_level": 0.8, "section_type": "verse", "emotional_tone": "energetic"},
        {"start_time": 20.0, "energy_level": 0.85, "section_type": "chorus", "emotional_tone": "energetic"}
    ]

    events = detect_energy_drop(sections, energy_threshold=0.2)

    assert len(events) >= 1
    assert events[0]["type"] == "drop"
    assert events[0]["t"] == 10.0
    assert events[0]["intensity"] in ["high", "medium", "low"]


def test_detect_section_changes():
    """Test section change detection."""
    sections = [
        {"start_time": 0.0, "section_type": "intro", "energy_level": 0.3, "emotional_tone": "calm"},
        {"start_time": 10.0, "section_type": "verse", "energy_level": 0.5, "emotional_tone": "neutral"},
        {"start_time": 20.0, "section_type": "chorus", "energy_level": 0.8, "emotional_tone": "energetic"}
    ]

    events = detect_section_changes(sections)

    assert len(events) == 2
    assert events[0]["type"] == "section_change"
    assert events[1]["type"] == "section_change"
    assert events[1]["visual_trigger"] == "crossfader_hit"  # For chorus


def test_detect_hard_start():
    """Test hard start detection."""
    # Hard start case
    sections_hot = [
        {"start_time": 0.0, "energy_level": 0.8, "section_type": "intro", "emotional_tone": "energetic"}
    ]

    events = detect_hard_start(sections_hot, threshold=0.1)
    assert len(events) == 1
    assert events[0]["type"] == "hard_start"

    # Soft start case
    sections_soft = [
        {"start_time": 0.0, "energy_level": 0.05, "section_type": "intro", "emotional_tone": "calm"}
    ]

    events = detect_hard_start(sections_soft, threshold=0.1)
    assert len(events) == 0


def test_generate_retention_nudges():
    """Test retention nudge generation."""
    duration = 60.0
    interval = 20.0

    events = generate_retention_nudges(duration, interval)

    assert len(events) == 2  # At 20s and 40s
    assert events[0]["t"] == 20.0
    assert events[1]["t"] == 40.0
    assert all(e["type"] == "retention_nudge" for e in events)


def test_generate_events_from_sections():
    """Test complete event generation."""
    sections = [
        {"start_time": 0.0, "energy_level": 0.3, "section_type": "intro", "emotional_tone": "calm", "vocal_density": "sparse"},
        {"start_time": 10.0, "energy_level": 0.8, "section_type": "verse", "emotional_tone": "energetic", "vocal_density": "medium"},
        {"start_time": 20.0, "energy_level": 0.85, "section_type": "chorus", "emotional_tone": "energetic", "vocal_density": "dense"}
    ]

    events = generate_events_from_sections(sections, duration_sec=60.0)

    # Should have drops, section changes, and retention nudges
    assert len(events) >= 3

    # Events should be sorted by timestamp
    timestamps = [e["t"] for e in events]
    assert timestamps == sorted(timestamps)

    # Should have various event types
    event_types = {e["type"] for e in events}
    assert "drop" in event_types or "section_change" in event_types


def test_filter_events_by_intensity():
    """Test filtering events by intensity."""
    events = [
        {"t": 0.0, "type": "drop", "intensity": "low", "visual_trigger": "test", "reason": "test"},
        {"t": 1.0, "type": "drop", "intensity": "medium", "visual_trigger": "test", "reason": "test"},
        {"t": 2.0, "type": "drop", "intensity": "high", "visual_trigger": "test", "reason": "test"}
    ]

    # Filter for medium+
    filtered = filter_events_by_intensity(events, min_intensity="medium")
    assert len(filtered) == 2
    assert all(e["intensity"] in ["medium", "high"] for e in filtered)

    # Filter for high only
    filtered_high = filter_events_by_intensity(events, min_intensity="high")
    assert len(filtered_high) == 1
    assert filtered_high[0]["intensity"] == "high"
