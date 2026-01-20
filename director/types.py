"""Type definitions for Director module."""

from typing import TypedDict, Literal, List, Optional


class TimelineMeta(TypedDict):
    """Metadata for the timeline."""
    mode: Literal["mashup", "single", "event"]
    format: Literal["short", "long"]
    theme: str
    duration_sec: float
    bpm: float


class AudioSection(TypedDict):
    """Audio section data (passthrough from Mixer SongMetadata)."""
    start_time: float
    end_time: float
    section_type: str
    energy_level: float
    vocal_density: str
    emotional_tone: str


class AudioData(TypedDict):
    """Audio file and section data."""
    file: str
    sections: List[AudioSection]


class BeatData(TypedDict):
    """Beat grid information."""
    timestamps: List[float]
    bpm: float
    downbeats: List[float]


class TimelineEvent(TypedDict):
    """Visual event triggered by audio analysis."""
    t: float  # Timestamp in seconds
    type: Literal["drop", "section_change", "hard_start", "retention_nudge"]
    intensity: Literal["low", "medium", "high"]
    visual_trigger: str  # Action name: "drop_reaction", "crossfader_hit", etc.
    reason: str  # Human-readable explanation


class CameraMovement(TypedDict):
    """Camera movement instruction."""
    t: float
    action: Literal["zoom_in", "zoom_out", "nudge_left", "nudge_right", "reset"]
    duration: float


class CameraData(TypedDict):
    """Camera configuration."""
    base_shot: Literal["close", "medium", "wide"]
    movements: List[CameraMovement]


class AvatarTrigger(TypedDict):
    """Avatar action trigger."""
    t: float
    action: str  # Action clip name: "idle_bob", "drop_reaction", etc.
    duration: float


class AvatarData(TypedDict):
    """Avatar configuration."""
    base_action: str  # Default idle animation
    triggers: List[AvatarTrigger]


class IntensityCurvePoint(TypedDict):
    """Point on intensity curve."""
    t: float
    value: float  # 0.0-1.0


class LightingData(TypedDict):
    """Lighting configuration."""
    preset: str  # Theme name
    primary_color: List[float]  # RGB 0-1
    intensity_curve: List[IntensityCurvePoint]


class Timeline(TypedDict):
    """Complete timeline structure (authoritative animation script)."""
    meta: TimelineMeta
    audio: AudioData
    beats: BeatData
    events: List[TimelineEvent]
    camera: CameraData
    avatar: AvatarData
    lighting: LightingData


class ThemeConfig(TypedDict):
    """Theme configuration from YAML."""
    lighting: dict
    avatar: dict
    camera: Optional[dict]
