"""Studio Module - Blender Integration for Crossfade Club.

This module handles 3D animation rendering via Blender subprocess.
"""

import subprocess
from pathlib import Path

from studio.renderer import render_video
from studio.asset_loader import validate_assets, list_required_assets
from studio.errors import StudioError, AssetError, RenderError

__all__ = [
    "render_video",
    "validate_assets",
    "list_required_assets",
    "StudioError",
    "AssetError",
    "RenderError",
]


def check_blender_installed() -> bool:
    """Check if Blender is installed and accessible.

    Returns:
        True if Blender is found, False otherwise
    """
    try:
        result = subprocess.run(
            ["blender", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


# Validate on import (optional - can be disabled with env var)
import os
if os.getenv("SKIP_STUDIO_VALIDATION") != "1":
    if not check_blender_installed():
        import warnings
        warnings.warn(
            "Blender not found on PATH. Studio module requires Blender for rendering.\n"
            "Install from: https://www.blender.org/download/\n"
            "Or set SKIP_STUDIO_VALIDATION=1 to suppress this warning."
        )
