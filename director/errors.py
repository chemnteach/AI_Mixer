"""Error definitions for Director module."""


class DirectorError(Exception):
    """Base exception for Director module."""
    pass


class ThemeNotFoundError(DirectorError):
    """Raised when requested theme config file not found."""
    pass


class InvalidTimelineError(DirectorError):
    """Raised when timeline generation fails validation."""
    pass


class EventDetectionError(DirectorError):
    """Raised when event detection fails."""
    pass


class CameraPathError(DirectorError):
    """Raised when camera path generation fails."""
    pass


class SafetyViolationError(DirectorError):
    """Raised when event-safe validation fails."""
    pass
