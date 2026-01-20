"""Encoder Module - FFmpeg Platform Variants for Crossfade Club.

Converts Blender-rendered videos into platform-optimized outputs with captions.
"""

import subprocess
from encoder.platform import create_platform_variant, create_all_variants, PLATFORM_SETTINGS
from encoder.captions import burn_captions, generate_vtt_from_timeline
from encoder.thumbnail import generate_thumbnail
from encoder.errors import EncoderError, PlatformError, FFmpegNotFoundError, CaptionError

__all__ = [
    "create_platform_variant",
    "create_all_variants",
    "PLATFORM_SETTINGS",
    "burn_captions",
    "generate_vtt_from_timeline",
    "generate_thumbnail",
    "EncoderError",
    "PlatformError",
    "FFmpegNotFoundError",
    "CaptionError",
]


def check_ffmpeg_installed() -> bool:
    """Check if FFmpeg is installed and accessible.

    Returns:
        True if FFmpeg is found, False otherwise
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


# Validate on import (optional - can be disabled with env var)
import os
if os.getenv("SKIP_ENCODER_VALIDATION") != "1":
    if not check_ffmpeg_installed():
        import warnings
        warnings.warn(
            "FFmpeg not found on PATH. Encoder module requires FFmpeg for video processing.\n"
            "Install from: https://ffmpeg.org/download.html\n"
            "Or set SKIP_ENCODER_VALIDATION=1 to suppress this warning."
        )
