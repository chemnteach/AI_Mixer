"""Event detection from audio sections for visual triggers."""

from typing import List
from director.types import TimelineEvent, AudioSection
from director.errors import EventDetectionError


def detect_energy_drop(
    sections: List[AudioSection],
    energy_threshold: float = 0.2
) -> List[TimelineEvent]:
    """Detect energy drops (big transitions) in audio sections.

    Args:
        sections: List of audio sections with energy_level
        energy_threshold: Minimum energy jump to qualify as a drop

    Returns:
        List of TimelineEvent for detected drops
    """
    events = []

    for i in range(1, len(sections)):
        prev_energy = sections[i - 1]["energy_level"]
        curr_energy = sections[i]["energy_level"]
        energy_delta = curr_energy - prev_energy

        if energy_delta >= energy_threshold:
            # Energy spike detected - this is a DROP
            intensity = "high" if energy_delta >= 0.4 else "medium" if energy_delta >= 0.25 else "low"

            events.append({
                "t": sections[i]["start_time"],
                "type": "drop",
                "intensity": intensity,
                "visual_trigger": "drop_reaction",
                "reason": f"Energy jump {prev_energy:.2f}→{curr_energy:.2f} detected"
            })

    return events


def detect_section_changes(sections: List[AudioSection]) -> List[TimelineEvent]:
    """Detect section type changes (verse→chorus, etc.).

    Args:
        sections: List of audio sections

    Returns:
        List of TimelineEvent for section transitions
    """
    events = []

    for i in range(1, len(sections)):
        prev_type = sections[i - 1]["section_type"]
        curr_type = sections[i]["section_type"]

        if prev_type != curr_type:
            # Section boundary detected
            # Use different visual triggers based on transition type
            if curr_type.lower() == "chorus":
                visual_trigger = "crossfader_hit"
                intensity = "medium"
            elif curr_type.lower() == "bridge":
                visual_trigger = "spotlight_present"
                intensity = "low"
            else:
                visual_trigger = "deck_scratch_L"
                intensity = "low"

            events.append({
                "t": sections[i]["start_time"],
                "type": "section_change",
                "intensity": intensity,
                "visual_trigger": visual_trigger,
                "reason": f"Section transition: {prev_type} → {curr_type}"
            })

    return events


def detect_hard_start(sections: List[AudioSection], threshold: float = 0.1) -> List[TimelineEvent]:
    """Detect hard starts (song begins with high energy).

    Args:
        sections: List of audio sections
        threshold: Minimum energy for first section to qualify as hard start

    Returns:
        List with single event if hard start detected, empty otherwise
    """
    if not sections:
        return []

    first_section = sections[0]

    if first_section["energy_level"] >= threshold and first_section["start_time"] < 1.0:
        return [{
            "t": first_section["start_time"],
            "type": "hard_start",
            "intensity": "high",
            "visual_trigger": "drop_reaction",
            "reason": f"Song starts hot with energy {first_section['energy_level']:.2f}"
        }]

    return []


def generate_retention_nudges(
    duration_sec: float,
    interval_sec: float = 25
) -> List[TimelineEvent]:
    """Generate periodic retention nudges for viewer engagement.

    Args:
        duration_sec: Total duration of audio
        interval_sec: Seconds between nudges

    Returns:
        List of TimelineEvent for camera nudges
    """
    events = []
    current_time = interval_sec

    while current_time < duration_sec:
        events.append({
            "t": current_time,
            "type": "retention_nudge",
            "intensity": "low",
            "visual_trigger": "deck_scratch_R",  # Subtle action
            "reason": f"Retention nudge at {current_time}s interval"
        })
        current_time += interval_sec

    return events


def generate_events_from_sections(
    sections: List[AudioSection],
    duration_sec: float,
    drop_energy_threshold: float = 0.2,
    hard_start_threshold: float = 0.1,
    retention_nudge_interval: float = 25
) -> List[TimelineEvent]:
    """Generate all visual events from audio section analysis.

    This is the main entry point for event detection.

    Args:
        sections: Audio sections from Mixer analyst
        duration_sec: Total audio duration
        drop_energy_threshold: Energy jump threshold for drops
        hard_start_threshold: Energy threshold for hard start detection
        retention_nudge_interval: Seconds between retention nudges

    Returns:
        Combined list of all detected events, sorted by timestamp

    Raises:
        EventDetectionError: If event generation fails
    """
    try:
        all_events = []

        # Detect various event types
        all_events.extend(detect_energy_drop(sections, drop_energy_threshold))
        all_events.extend(detect_section_changes(sections))
        all_events.extend(detect_hard_start(sections, hard_start_threshold))
        all_events.extend(generate_retention_nudges(duration_sec, retention_nudge_interval))

        # Sort by timestamp
        all_events.sort(key=lambda e: e["t"])

        return all_events

    except Exception as e:
        raise EventDetectionError(f"Failed to generate events: {e}") from e


def filter_events_by_intensity(
    events: List[TimelineEvent],
    min_intensity: str = "low"
) -> List[TimelineEvent]:
    """Filter events by minimum intensity level.

    Args:
        events: List of events to filter
        min_intensity: Minimum intensity ("low", "medium", "high")

    Returns:
        Filtered event list
    """
    intensity_order = {"low": 0, "medium": 1, "high": 2}
    min_level = intensity_order[min_intensity]

    return [e for e in events if intensity_order[e["intensity"]] >= min_level]
