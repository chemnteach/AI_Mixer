"""Thumbnail extraction from video files."""

import subprocess
from pathlib import Path
from typing import Optional

from encoder.types import ThumbnailSettings
from encoder.errors import ThumbnailError, FFmpegNotFoundError


def generate_thumbnail(
    video_path: str,
    output_path: str,
    timestamp: float = 0.0,
    width: int = 1280,
    height: int = 720,
    quality: int = 85
) -> Path:
    """Extract thumbnail from video at specified timestamp.

    Args:
        video_path: Path to video file
        output_path: Where to save thumbnail (JPG)
        timestamp: Time in seconds to extract frame
        width: Thumbnail width
        height: Thumbnail height
        quality: JPEG quality (1-100)

    Returns:
        Path to generated thumbnail

    Raises:
        ThumbnailError: If extraction fails
        FFmpegNotFoundError: If FFmpeg not found
    """
    try:
        # Prepare output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Ensure JPG extension
        if output_file.suffix.lower() != ".jpg":
            output_file = output_file.with_suffix(".jpg")

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp),  # Seek to timestamp
            "-i", video_path,
            "-vframes", "1",  # Extract single frame
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-q:v", str(int((100 - quality) / 4)),  # Convert quality to FFmpeg scale (2-31)
            "-y",  # Overwrite
            str(output_file)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise ThumbnailError(f"FFmpeg thumbnail extraction failed: {result.stderr}")

        if not output_file.exists():
            raise ThumbnailError(f"Extraction completed but thumbnail not found: {output_file}")

        print(f"✓ Thumbnail extracted: {output_file}")
        print(f"  Size: {output_file.stat().st_size / 1024:.1f} KB")

        return output_file

    except FileNotFoundError as e:
        raise FFmpegNotFoundError("FFmpeg not found") from e

    except subprocess.TimeoutExpired as e:
        raise ThumbnailError("Thumbnail extraction timeout") from e

    except Exception as e:
        raise ThumbnailError(f"Failed to extract thumbnail: {e}") from e


def generate_thumbnail_from_timeline(
    video_path: str,
    timeline_path: str,
    output_path: str,
    width: int = 1280,
    height: int = 720
) -> Path:
    """Extract thumbnail at an interesting moment from timeline.

    Chooses timestamp based on first high-energy event (drop, section change).

    Args:
        video_path: Path to video file
        timeline_path: Path to timeline.json
        output_path: Where to save thumbnail
        width: Thumbnail width
        height: Thumbnail height

    Returns:
        Path to generated thumbnail

    Raises:
        ThumbnailError: If extraction fails
    """
    import json

    try:
        # Load timeline
        with open(timeline_path, "r") as f:
            timeline = json.load(f)

        # Find first high-intensity event
        events = timeline.get("events", [])
        timestamp = 0.0  # Default to start

        for event in events:
            if event.get("intensity") in ["high", "medium"]:
                timestamp = event["t"]
                print(f"  Using event at {timestamp:.1f}s: {event['type']} ({event['intensity']})")
                break

        # If no good event found, use 25% through video
        if timestamp == 0.0:
            duration = timeline.get("meta", {}).get("duration_sec", 30.0)
            timestamp = duration * 0.25
            print(f"  No high-energy events, using {timestamp:.1f}s (25% through)")

        return generate_thumbnail(
            video_path=video_path,
            output_path=output_path,
            timestamp=timestamp,
            width=width,
            height=height
        )

    except Exception as e:
        raise ThumbnailError(f"Failed to generate timeline thumbnail: {e}") from e


def generate_contact_sheet(
    video_path: str,
    output_path: str,
    columns: int = 4,
    rows: int = 3,
    width: int = 1920,
    height: int = 1080
) -> Path:
    """Generate contact sheet (grid of thumbnails) from video.

    Args:
        video_path: Path to video file
        output_path: Where to save contact sheet
        columns: Number of columns
        rows: Number of rows
        width: Total width
        height: Total height

    Returns:
        Path to generated contact sheet

    Raises:
        ThumbnailError: If generation fails
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # FFmpeg tile filter
        tile_filter = f"select='not(mod(n,10))',scale={width//columns}:{height//rows},tile={columns}x{rows}"

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", tile_filter,
            "-frames:v", "1",
            "-y",
            str(output_file)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise ThumbnailError(f"Contact sheet generation failed: {result.stderr}")

        if not output_file.exists():
            raise ThumbnailError(f"Contact sheet not found: {output_file}")

        print(f"✓ Contact sheet generated: {output_file}")
        return output_file

    except Exception as e:
        raise ThumbnailError(f"Failed to generate contact sheet: {e}") from e


def get_thumbnail_settings(platform: str) -> ThumbnailSettings:
    """Get recommended thumbnail settings for platform.

    Args:
        platform: Platform name (tiktok, reels, shorts, youtube)

    Returns:
        ThumbnailSettings with recommended dimensions
    """
    settings_map = {
        "tiktok": {
            "timestamp": 0.0,
            "width": 1080,
            "height": 1920,
            "quality": 85
        },
        "reels": {
            "timestamp": 0.0,
            "width": 1080,
            "height": 1920,
            "quality": 85
        },
        "shorts": {
            "timestamp": 0.0,
            "width": 1080,
            "height": 1920,
            "quality": 85
        },
        "youtube": {
            "timestamp": 0.0,
            "width": 1280,
            "height": 720,
            "quality": 90
        }
    }

    return settings_map.get(platform, settings_map["youtube"])
