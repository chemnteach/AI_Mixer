"""Caption burn-in and VTT generation for video encoding."""

import subprocess
import yaml
from pathlib import Path
from typing import Optional, Dict

from encoder.types import CaptionStyle
from encoder.errors import CaptionError, FFmpegNotFoundError


def load_caption_styles() -> Dict[str, CaptionStyle]:
    """Load caption styles from config/captions.yaml.

    Returns:
        Dict mapping platform name to CaptionStyle
    """
    config_path = Path(__file__).parent.parent / "config" / "captions.yaml"

    if not config_path.exists():
        raise CaptionError(f"Caption config not found: {config_path}")

    with open(config_path, "r") as f:
        styles = yaml.safe_load(f)

    return styles


def get_caption_style(platform: str) -> CaptionStyle:
    """Get caption style for specific platform.

    Args:
        platform: Platform name (tiktok, reels, shorts, youtube)

    Returns:
        CaptionStyle configuration

    Raises:
        CaptionError: If platform not found
    """
    styles = load_caption_styles()

    if platform not in styles:
        print(f"Warning: No caption style for {platform}, using default")
        return styles.get("default", {})

    return styles[platform]


def generate_vtt_from_timeline(timeline_path: str, output_path: str) -> Path:
    """Generate VTT captions from timeline.json.

    Extracts lyrical content from timeline sections and creates WebVTT file.

    Args:
        timeline_path: Path to timeline.json
        output_path: Where to save .vtt file

    Returns:
        Path to generated VTT file

    Raises:
        CaptionError: If generation fails
    """
    import json

    try:
        # Load timeline
        with open(timeline_path, "r") as f:
            timeline = json.load(f)

        sections = timeline.get("audio", {}).get("sections", [])

        # Create VTT content
        vtt_lines = ["WEBVTT\n"]

        for i, section in enumerate(sections):
            start_time = section.get("start_time", 0.0)
            end_time = section.get("end_time", start_time + 5.0)

            # Get lyrical content if available
            # NOTE: Mixer's sections don't currently have full lyrics per section
            # This is a placeholder - real implementation would need word-level timing
            text = section.get("emotional_tone", "").capitalize()

            if text:
                # Format timestamps for VTT (HH:MM:SS.mmm)
                start_vtt = format_vtt_timestamp(start_time)
                end_vtt = format_vtt_timestamp(end_time)

                vtt_lines.append(f"\n{i+1}")
                vtt_lines.append(f"{start_vtt} --> {end_vtt}")
                vtt_lines.append(f"{text}\n")

        # Write VTT file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(vtt_lines))

        print(f"✓ Generated VTT captions: {output_file}")
        return output_file

    except Exception as e:
        raise CaptionError(f"Failed to generate VTT: {e}") from e


def format_vtt_timestamp(seconds: float) -> str:
    """Format seconds to VTT timestamp (HH:MM:SS.mmm).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def burn_captions(
    input_video: str,
    vtt_file: str,
    output_path: str,
    platform: str = "default"
) -> Path:
    """Burn captions into video using FFmpeg subtitle filter.

    Args:
        input_video: Path to input video
        vtt_file: Path to VTT captions file
        output_path: Where to save video with burned captions
        platform: Platform name for styling

    Returns:
        Path to output video

    Raises:
        CaptionError: If burning fails
        FFmpegNotFoundError: If FFmpeg not found
    """
    try:
        # Get caption style
        style = get_caption_style(platform)

        # Prepare output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Build FFmpeg subtitle filter
        # Convert VTT to ASS for better styling support
        ass_file = Path(vtt_file).with_suffix(".ass")

        # First convert VTT to ASS
        subprocess.run(
            ["ffmpeg", "-i", vtt_file, str(ass_file), "-y"],
            capture_output=True,
            timeout=30,
            check=True
        )

        # Build subtitle filter with styling
        font = style.get("font", "Arial")
        size = style.get("size", 60)
        color = style.get("color", "FFFFFF")
        outline_color = style.get("outline_color", "000000")
        outline_width = style.get("outline_width", 2)

        # FFmpeg subtitles filter
        subtitle_filter = f"subtitles={ass_file}:force_style='FontName={font},FontSize={size},PrimaryColour=&H{color}&,OutlineColour=&H{outline_color}&,Outline={outline_width}'"

        # Encode with burned subtitles
        cmd = [
            "ffmpeg",
            "-i", input_video,
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-y",
            str(output_file)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            raise CaptionError(f"FFmpeg caption burn failed: {result.stderr}")

        # Clean up ASS file
        ass_file.unlink(missing_ok=True)

        if not output_file.exists():
            raise CaptionError(f"Caption burn completed but output file not found: {output_file}")

        print(f"✓ Captions burned: {output_file}")
        return output_file

    except FileNotFoundError as e:
        raise FFmpegNotFoundError("FFmpeg not found") from e

    except subprocess.TimeoutExpired as e:
        raise CaptionError("Caption burn timeout") from e

    except Exception as e:
        raise CaptionError(f"Failed to burn captions: {e}") from e


def create_simple_vtt(text: str, duration: float, output_path: str) -> Path:
    """Create a simple VTT file with single caption.

    Utility function for testing.

    Args:
        text: Caption text
        duration: Video duration
        output_path: Where to save VTT

    Returns:
        Path to VTT file
    """
    vtt_content = f"""WEBVTT

1
00:00:00.000 --> {format_vtt_timestamp(duration)}
{text}
"""

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(vtt_content)

    return output_file


def validate_vtt(vtt_path: str) -> bool:
    """Validate VTT file format.

    Args:
        vtt_path: Path to VTT file

    Returns:
        True if valid, False otherwise
    """
    try:
        with open(vtt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Basic validation: must start with WEBVTT
        if not content.strip().startswith("WEBVTT"):
            return False

        # Should have at least one timestamp
        if "-->" not in content:
            return False

        return True

    except Exception:
        return False
