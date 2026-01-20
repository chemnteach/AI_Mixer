"""Platform-specific video encoding for TikTok, Reels, YouTube, Shorts."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, List

from encoder.types import PlatformSettings, EncodeJob
from encoder.errors import PlatformError, FFmpegNotFoundError, CodecError
from encoder.captions import burn_captions


# Platform-specific encoding settings
PLATFORM_SETTINGS: Dict[str, PlatformSettings] = {
    "tiktok": {
        "resolution": (1080, 1920),  # 9:16
        "video_bitrate": "5M",
        "audio_bitrate": "192k",
        "burn_captions": True,
        "fps": 30,
        "max_duration": 180  # 3 minutes
    },
    "reels": {
        "resolution": (1080, 1920),  # 9:16
        "video_bitrate": "5M",
        "audio_bitrate": "192k",
        "burn_captions": True,
        "fps": 30,
        "max_duration": 90  # 90 seconds
    },
    "shorts": {
        "resolution": (1080, 1920),  # 9:16
        "video_bitrate": "5M",
        "audio_bitrate": "192k",
        "burn_captions": True,
        "fps": 30,
        "max_duration": 60  # 60 seconds
    },
    "youtube": {
        "resolution": (1920, 1080),  # 16:9
        "video_bitrate": "8M",
        "audio_bitrate": "320k",
        "burn_captions": False,  # Soft subtitles
        "fps": 30,
        "max_duration": None  # Unlimited
    }
}


def find_ffmpeg_executable() -> Optional[str]:
    """Find FFmpeg executable on system PATH.

    Returns:
        Path to ffmpeg executable, or None if not found
    """
    exe_path = shutil.which("ffmpeg")
    return exe_path


def check_codec_support() -> Dict[str, bool]:
    """Check which codecs are available in FFmpeg.

    Returns:
        Dict mapping codec name to availability
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-codecs"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout

        return {
            "h264": "libx264" in output,
            "aac": "aac" in output,
            "vp9": "libvpx-vp9" in output
        }

    except (subprocess.SubprocessError, FileNotFoundError):
        return {"h264": False, "aac": False, "vp9": False}


def create_platform_variant(
    input_video: str,
    input_audio: str,
    platform: str,
    output_path: str,
    vtt_file: Optional[str] = None,
    quality_preset: str = "medium"
) -> Path:
    """Create platform-optimized video variant.

    Args:
        input_video: Path to raw Blender render (video only)
        input_audio: Path to audio file
        platform: Platform name (tiktok, reels, shorts, youtube)
        output_path: Where to save encoded video
        vtt_file: Optional VTT captions file
        quality_preset: FFmpeg preset (ultrafast, fast, medium, slow, veryslow)

    Returns:
        Path to encoded video

    Raises:
        PlatformError: If encoding fails
        FFmpegNotFoundError: If FFmpeg not found
    """
    # Validate FFmpeg
    ffmpeg = find_ffmpeg_executable()
    if not ffmpeg:
        raise FFmpegNotFoundError("FFmpeg not found on PATH")

    # Get platform settings
    if platform not in PLATFORM_SETTINGS:
        raise PlatformError(f"Unknown platform: {platform}. Valid: {list(PLATFORM_SETTINGS.keys())}")

    settings = PLATFORM_SETTINGS[platform]

    # Prepare output directory
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Check if we need caption burn-in
    if settings["burn_captions"] and vtt_file:
        # Create temporary file with captions burned in
        temp_video = output_file.parent / f"temp_{output_file.name}"

        print(f"Burning captions into video...")
        burn_captions(input_video, vtt_file, str(temp_video), platform)

        # Use captioned video as input
        video_source = str(temp_video)
    else:
        video_source = input_video

    # Build FFmpeg command
    width, height = settings["resolution"]

    cmd = [
        ffmpeg,
        "-i", video_source,  # Video input
        "-i", input_audio,  # Audio input
        "-c:v", "libx264",  # Video codec
        "-preset", quality_preset,
        "-b:v", settings["video_bitrate"],
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac",  # Audio codec
        "-b:a", settings["audio_bitrate"],
        "-ar", "48000",  # Audio sample rate
        "-r", str(settings["fps"]),
        "-pix_fmt", "yuv420p",  # Compatibility
        "-movflags", "+faststart",  # Web optimization
        "-y",  # Overwrite output
        str(output_file)
    ]

    # Truncate if max duration specified
    if settings["max_duration"]:
        cmd.insert(1, "-t")
        cmd.insert(2, str(settings["max_duration"]))

    try:
        print(f"Encoding {platform} variant...")
        print(f"  Resolution: {width}x{height}")
        print(f"  Video bitrate: {settings['video_bitrate']}")
        print(f"  Audio bitrate: {settings['audio_bitrate']}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 min max
        )

        if result.returncode != 0:
            raise PlatformError(
                f"FFmpeg encoding failed for {platform}\n"
                f"Command: {' '.join(cmd)}\n"
                f"Error: {result.stderr}"
            )

        # Clean up temp file if created
        if settings["burn_captions"] and vtt_file:
            temp_video.unlink(missing_ok=True)

        if not output_file.exists():
            raise PlatformError(f"Encoding completed but output file not found: {output_file}")

        print(f"  ✓ Encoded: {output_file}")
        print(f"  Size: {output_file.stat().st_size / (1024*1024):.2f} MB")

        return output_file

    except subprocess.TimeoutExpired as e:
        raise PlatformError(f"FFmpeg encoding timeout for {platform}") from e

    except Exception as e:
        raise PlatformError(f"Encoding failed for {platform}: {e}") from e


def create_all_variants(
    input_video: str,
    input_audio: str,
    output_dir: str,
    base_name: str,
    vtt_file: Optional[str] = None,
    platforms: Optional[List[str]] = None
) -> Dict[str, Path]:
    """Create all platform variants in parallel (sequential for now).

    Args:
        input_video: Path to raw Blender render
        input_audio: Path to audio file
        output_dir: Directory to save variants
        base_name: Base filename (e.g., "song_a_x_song_b")
        vtt_file: Optional VTT captions
        platforms: List of platforms to create (None = all)

    Returns:
        Dict mapping platform name to output path

    Raises:
        PlatformError: If any encoding fails
    """
    if platforms is None:
        platforms = list(PLATFORM_SETTINGS.keys())

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    results = {}

    for platform in platforms:
        output_path = output_dir_path / f"{base_name}_{platform}.mp4"

        try:
            result_path = create_platform_variant(
                input_video=input_video,
                input_audio=input_audio,
                platform=platform,
                output_path=str(output_path),
                vtt_file=vtt_file
            )
            results[platform] = result_path

        except Exception as e:
            print(f"  ✗ Failed to create {platform} variant: {e}")
            # Continue with other platforms

    return results


def get_video_info(video_path: str) -> Dict[str, any]:
    """Get video file information using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Dict with duration, resolution, codec, bitrate info
    """
    try:
        # Get duration
        result_duration = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Get resolution
        result_resolution = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height",
             "-of", "csv=s=x:p=0", video_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Get codec
        result_codec = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        duration = float(result_duration.stdout.strip()) if result_duration.returncode == 0 else 0.0
        resolution = result_resolution.stdout.strip() if result_resolution.returncode == 0 else "unknown"
        codec = result_codec.stdout.strip() if result_codec.returncode == 0 else "unknown"

        return {
            "duration": duration,
            "resolution": resolution,
            "codec": codec,
            "exists": Path(video_path).exists(),
            "size_mb": Path(video_path).stat().st_size / (1024*1024) if Path(video_path).exists() else 0.0
        }

    except Exception:
        return {
            "duration": 0.0,
            "resolution": "unknown",
            "codec": "unknown",
            "exists": False,
            "size_mb": 0.0
        }
