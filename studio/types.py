"""Type definitions for Studio module."""

from typing import TypedDict, Literal, Optional


class BlenderConfig(TypedDict):
    """Blender executable configuration."""
    executable: str  # Path to blender binary
    timeout_sec: int
    background_mode: bool


class RenderSettings(TypedDict):
    """Render quality settings."""
    fps: int
    resolution: tuple[int, int]  # (width, height)
    samples: int  # EEVEE samples
    render_engine: Literal["EEVEE", "CYCLES"]
    shadow_quality: Literal["low", "medium", "high"]
    output_format: Literal["MP4", "AVI", "PNG"]


class AssetManifest(TypedDict):
    """Required asset list."""
    avatar_base: str  # Path to avatar_base.blend
    studio_environment: str  # Path to studio_default.blend
    actions: list[str]  # List of action .blend files
