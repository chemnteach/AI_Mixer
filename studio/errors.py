"""Error definitions for Studio module."""


class StudioError(Exception):
    """Base exception for Studio module."""
    pass


class AssetError(StudioError):
    """Raised when required assets are missing or invalid."""
    pass


class RenderError(StudioError):
    """Raised when Blender rendering fails."""
    pass


class BlenderNotFoundError(StudioError):
    """Raised when Blender executable is not found."""
    pass


class TimeoutError(StudioError):
    """Raised when Blender render exceeds timeout."""
    pass
