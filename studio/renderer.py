"""Blender subprocess rendering orchestration."""

import subprocess
import json
from pathlib import Path
from typing import Optional
import shutil

from studio.errors import RenderError, BlenderNotFoundError, TimeoutError
from studio.types import RenderSettings, BlenderConfig
from studio.asset_loader import validate_assets_strict


def find_blender_executable() -> Optional[str]:
    """Find Blender executable on system PATH.

    Returns:
        Path to blender executable, or None if not found
    """
    # Try common names
    for name in ["blender", "blender.exe", "Blender"]:
        exe_path = shutil.which(name)
        if exe_path:
            return exe_path

    return None


def get_blender_config() -> BlenderConfig:
    """Get Blender configuration from config.yaml.

    Returns:
        BlenderConfig with executable path and settings
    """
    from mixer.config import get_config

    config = get_config()

    # Get blender executable from config or find on PATH
    blender_exe = config.get("studio.blender_executable", "blender")

    if blender_exe == "blender":
        # Try to find it
        found_exe = find_blender_executable()
        if not found_exe:
            raise BlenderNotFoundError(
                "Blender not found on PATH. Install from https://www.blender.org/download/ "
                "or set studio.blender_executable in config.yaml"
            )
        blender_exe = found_exe

    return {
        "executable": blender_exe,
        "timeout_sec": config.get("studio.render_timeout_sec", 600),
        "background_mode": True
    }


def get_render_settings(format_type: str = "short") -> RenderSettings:
    """Get render settings from config.yaml.

    Args:
        format_type: "short" (9:16) or "long" (16:9)

    Returns:
        RenderSettings with resolution, FPS, quality settings
    """
    from mixer.config import get_config

    config = get_config()

    resolution = config.get(f"studio.resolution.{format_type}", [1080, 1920])

    return {
        "fps": config.get("studio.fps", 30),
        "resolution": tuple(resolution),
        "samples": config.get("studio.quality.samples", 64),
        "render_engine": config.get("studio.render_engine", "EEVEE"),
        "shadow_quality": config.get("studio.quality.shadow_quality", "medium"),
        "output_format": "MP4"
    }


def render_video(
    timeline_path: str,
    output_path: str,
    format_type: str = "short",
    duration_override: Optional[float] = None,
    placeholder_mode: bool = False
) -> Path:
    """Render video from timeline using Blender.

    Args:
        timeline_path: Path to timeline.json
        output_path: Where to save rendered video
        format_type: "short" or "long"
        duration_override: Override duration (for testing shorter renders)
        placeholder_mode: If True, skip asset validation (for testing)

    Returns:
        Path to rendered video file

    Raises:
        RenderError: If rendering fails
        BlenderNotFoundError: If Blender not found
        TimeoutError: If render exceeds timeout
        AssetError: If required assets missing (unless placeholder_mode)
    """
    # Validate assets (unless placeholder mode)
    if not placeholder_mode:
        validate_assets_strict()

    # Get Blender config
    blender_config = get_blender_config()
    render_settings = get_render_settings(format_type)

    # Get path to animate.py script
    script_path = Path(__file__).parent / "blender_scripts" / "animate.py"

    if not script_path.exists():
        raise RenderError(f"Blender script not found: {script_path}")

    # Prepare output directory
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Build Blender command
    cmd = [
        blender_config["executable"],
        "--background",  # No GUI
        "--python", str(script_path),
        "--",
        "--timeline", timeline_path,
        "--output", output_path,
        "--format", format_type,
        "--fps", str(render_settings["fps"]),
        "--resolution", f"{render_settings['resolution'][0]}x{render_settings['resolution'][1]}",
        "--samples", str(render_settings["samples"]),
        "--engine", render_settings["render_engine"]
    ]

    if duration_override:
        cmd.extend(["--duration", str(duration_override)])

    if placeholder_mode:
        cmd.append("--placeholder")

    # Run Blender subprocess
    try:
        print(f"Running Blender render...")
        print(f"Command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=blender_config["timeout_sec"]
        )

        if result.returncode != 0:
            raise RenderError(
                f"Blender render failed with code {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        # Check output file exists
        if not output_file.exists():
            raise RenderError(
                f"Render completed but output file not found: {output_file}\n"
                f"Blender output:\n{result.stdout}"
            )

        print(f"✓ Render complete: {output_file}")
        print(f"  Size: {output_file.stat().st_size / (1024*1024):.2f} MB")

        return output_file

    except subprocess.TimeoutExpired as e:
        raise TimeoutError(
            f"Blender render exceeded timeout ({blender_config['timeout_sec']}s)"
        ) from e

    except FileNotFoundError as e:
        raise BlenderNotFoundError(
            f"Blender executable not found: {blender_config['executable']}"
        ) from e

    except Exception as e:
        raise RenderError(f"Unexpected error during rendering: {e}") from e


def estimate_render_time(duration_sec: float, format_type: str = "short") -> float:
    """Estimate render time based on duration and format.

    Args:
        duration_sec: Audio duration
        format_type: "short" or "long"

    Returns:
        Estimated render time in seconds
    """
    # Rough estimate: ~5-10x real-time for EEVEE
    # Short form (9:16) renders slightly faster than long form (16:9)

    multiplier = 7.0 if format_type == "short" else 8.5

    return duration_sec * multiplier


def check_render_health(output_path: str) -> dict:
    """Check health of rendered video file.

    Args:
        output_path: Path to rendered video

    Returns:
        Dict with health check results
    """
    video_path = Path(output_path)

    health = {
        "exists": video_path.exists(),
        "size_mb": 0.0,
        "is_video": False,
        "has_h264": False
    }

    if not video_path.exists():
        return health

    health["size_mb"] = video_path.stat().st_size / (1024 * 1024)

    # Basic check: MP4 files should be >500KB for even short clips
    if health["size_mb"] > 0.5:
        health["is_video"] = True

    # Check for H.264 codec (requires ffprobe, optional)
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1",
             str(video_path)],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and "h264" in result.stdout.lower():
            health["has_h264"] = True

    except (subprocess.SubprocessError, FileNotFoundError):
        # ffprobe not available, skip codec check
        pass

    return health
