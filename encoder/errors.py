"""Error definitions for Encoder module."""


class EncoderError(Exception):
    """Base exception for Encoder module."""
    pass


class PlatformError(EncoderError):
    """Raised when platform variant creation fails."""
    pass


class FFmpegNotFoundError(EncoderError):
    """Raised when FFmpeg executable is not found."""
    pass


class CaptionError(EncoderError):
    """Raised when caption processing fails."""
    pass


class ThumbnailError(EncoderError):
    """Raised when thumbnail extraction fails."""
    pass


class CodecError(EncoderError):
    """Raised when required video/audio codec is missing."""
    pass
