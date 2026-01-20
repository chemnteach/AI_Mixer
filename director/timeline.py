"""Timeline generation - Main entry point for Director agent."""

import json
import librosa
from pathlib import Path
from typing import Optional, List, Literal

from director.types import Timeline, TimelineMeta, AudioData, BeatData, AvatarData, LightingData, AudioSection
from director.events import generate_events_from_sections
from director.camera import generate_camera_paths
from director.themes import load_theme, get_theme_color
from director.errors import InvalidTimelineError


def generate_beat_grid(audio_path: str, bpm: float) -> BeatData:
    """Generate beat timestamps from audio file.

    Args:
        audio_path: Path to audio file
        bpm: BPM of the audio

    Returns:
        BeatData with timestamps, bpm, and downbeats
    """
    # Load audio
    y, sr = librosa.load(audio_path, sr=None)

    # Detect beats
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, bpm=bpm)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Estimate downbeats (every 4 beats for 4/4 time)
    downbeats = beat_times[::4].tolist()

    return {
        "timestamps": beat_times.tolist(),
        "bpm": float(bpm),
        "downbeats": downbeats
    }


def generate_avatar_triggers(
    events: list,
    base_action: str = "idle_bob"
) -> AvatarData:
    """Generate avatar action triggers from timeline events.

    Args:
        events: Timeline events
        base_action: Default idle animation

    Returns:
        AvatarData with base action and triggers
    """
    triggers = []

    for event in events:
        # Map visual_trigger to action duration
        action = event["visual_trigger"]

        # Set duration based on action type
        if action == "drop_reaction":
            duration = 1.5
        elif action == "crossfader_hit":
            duration = 1.0
        elif action == "spotlight_present":
            duration = 2.0
        elif action in ["deck_scratch_L", "deck_scratch_R"]:
            duration = 0.8
        else:
            duration = 1.0

        triggers.append({
            "t": event["t"],
            "action": action,
            "duration": duration
        })

    return {
        "base_action": base_action,
        "triggers": triggers
    }


def generate_lighting_curve(
    sections: List[AudioSection],
    theme_config: dict
) -> LightingData:
    """Generate lighting intensity curve from audio sections.

    Args:
        sections: Audio sections with energy levels
        theme_config: Theme configuration

    Returns:
        LightingData with preset and intensity curve
    """
    # Get theme colors
    primary_color = theme_config.get("lighting", {}).get("primary_color", [1.0, 1.0, 1.0])
    base_intensity = theme_config.get("lighting", {}).get("base_intensity", 0.7)

    # Build intensity curve from section energy
    intensity_curve = []

    for section in sections:
        # Map energy to intensity
        intensity = base_intensity + (section["energy_level"] * 0.3)
        intensity = min(1.0, intensity)  # Clamp to 1.0

        intensity_curve.append({
            "t": section["start_time"],
            "value": intensity
        })

    return {
        "preset": theme_config.get("name", "unknown"),
        "primary_color": primary_color,
        "intensity_curve": intensity_curve
    }


def generate_timeline(
    audio_path: str,
    song_id: str,
    theme_name: str = "sponsor_neon",
    mode: Literal["mashup", "single", "event"] = "mashup",
    format_type: Literal["short", "long"] = "short",
    output_path: Optional[str] = None
) -> Timeline:
    """Generate complete timeline from audio file and Mixer metadata.

    This is the main entry point for the Director agent.

    Args:
        audio_path: Path to audio file (.wav)
        song_id: Song ID to fetch metadata from ChromaDB
        theme_name: Theme to use (sponsor_neon, award_elegant, etc.)
        mode: Output mode (mashup, single, event)
        format_type: Video format (short=9:16, long=16:9)
        output_path: Optional path to save timeline.json

    Returns:
        Complete Timeline dictionary

    Raises:
        InvalidTimelineError: If timeline generation fails
    """
    try:
        # Load theme
        theme = load_theme(theme_name)

        # Get song metadata from Mixer's ChromaDB
        from mixer.memory import get_song

        song_data = get_song(song_id)
        metadata = song_data["metadata"]
        sections = metadata.get("sections", [])
        bpm = metadata.get("bpm", 120.0)
        duration_sec = metadata.get("duration_sec", 0.0)

        # If no duration in metadata, get from audio file
        if duration_sec == 0.0:
            y, sr = librosa.load(audio_path, sr=None)
            duration_sec = librosa.get_duration(y=y, sr=sr)

        # Generate beat grid
        beats = generate_beat_grid(audio_path, bpm)

        # Generate events from sections
        drop_threshold = theme.get("director", {}).get("drop_energy_threshold", 0.2)
        retention_interval = theme.get("camera", {}).get("retention_nudge_interval_sec", 25)

        events = generate_events_from_sections(
            sections,
            duration_sec,
            drop_energy_threshold=drop_threshold,
            retention_nudge_interval=retention_interval
        )

        # Generate camera paths
        camera = generate_camera_paths(events, theme)

        # Generate avatar triggers
        avatar = generate_avatar_triggers(events)

        # Generate lighting
        lighting = generate_lighting_curve(sections, theme)

        # Build complete timeline
        timeline: Timeline = {
            "meta": {
                "mode": mode,
                "format": format_type,
                "theme": theme_name,
                "duration_sec": duration_sec,
                "bpm": bpm
            },
            "audio": {
                "file": audio_path,
                "sections": sections
            },
            "beats": beats,
            "events": events,
            "camera": camera,
            "avatar": avatar,
            "lighting": lighting
        }

        # Save if output path specified
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w") as f:
                json.dump(timeline, f, indent=2)

        return timeline

    except Exception as e:
        raise InvalidTimelineError(f"Failed to generate timeline: {e}") from e


def load_timeline(timeline_path: str) -> Timeline:
    """Load timeline from JSON file.

    Args:
        timeline_path: Path to timeline.json

    Returns:
        Timeline dictionary
    """
    with open(timeline_path, "r") as f:
        return json.load(f)


def validate_timeline(timeline: Timeline) -> bool:
    """Validate timeline structure.

    Args:
        timeline: Timeline to validate

    Returns:
        True if valid

    Raises:
        InvalidTimelineError: If validation fails
    """
    required_keys = ["meta", "audio", "beats", "events", "camera", "avatar", "lighting"]

    for key in required_keys:
        if key not in timeline:
            raise InvalidTimelineError(f"Timeline missing required key: {key}")

    # Validate meta
    if timeline["meta"]["duration_sec"] <= 0:
        raise InvalidTimelineError("Invalid duration_sec")

    # Validate events are sorted
    event_times = [e["t"] for e in timeline["events"]]
    if event_times != sorted(event_times):
        raise InvalidTimelineError("Events are not sorted by timestamp")

    return True
