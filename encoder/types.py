"""Type definitions for Encoder module."""

from typing import TypedDict, Literal, Optional


class PlatformSettings(TypedDict):
    """Platform-specific encoding settings."""
    resolution: tuple[int, int]  # (width, height)
    video_bitrate: str  # e.g., "5M"
    audio_bitrate: str  # e.g., "192k"
    burn_captions: bool
    fps: int
    max_duration: Optional[int]  # Max duration in seconds (None = unlimited)


class CaptionStyle(TypedDict):
    """Caption styling configuration."""
    font: str  # Font name
    size: int  # Font size in pixels
    position: Literal["top", "center_bottom", "bottom"]
    color: str  # Hex color (e.g., "FFFFFF")
    outline_color: str  # Hex color for outline
    outline_width: int  # Outline width in pixels
    animation: Optional[Literal["word_pop", "fade_in", "slide_up"]]


class ThumbnailSettings(TypedDict):
    """Thumbnail extraction settings."""
    timestamp: float  # Timestamp to extract (seconds)
    width: int
    height: int
    quality: int  # JPEG quality 1-100


class EncodeJob(TypedDict):
    """Complete encoding job specification."""
    input_video: str  # Path to raw Blender video
    input_audio: str  # Path to audio file
    vtt_file: Optional[str]  # Path to VTT captions (optional)
    platform: Literal["tiktok", "reels", "shorts", "youtube"]
    output_path: str
    settings: PlatformSettings
