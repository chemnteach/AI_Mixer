"""Ingestion Agent - Downloads and caches audio files."""

import os
import re
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlparse

from mixer.config import get_config
from mixer.memory import get_client, sanitize_id
from mixer.types import IngestionResult, SourceType


logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Base exception for ingestion errors."""
    pass


class InvalidInputError(IngestionError):
    """Raised when input is neither a valid URL nor existing file."""
    pass


class DownloadError(IngestionError):
    """Raised when download fails."""
    pass


class ValidationError(IngestionError):
    """Raised when file validation fails."""
    pass


def detect_source_type(input_source: str) -> SourceType:
    """
    Detect if input is a YouTube URL or local file.

    Args:
        input_source: YouTube URL or file path

    Returns:
        "youtube" or "local_file"

    Raises:
        InvalidInputError: If input is neither URL nor existing file
    """
    # Check if it's a URL
    if input_source.startswith(('http://', 'https://')):
        parsed = urlparse(input_source)
        # Basic YouTube domain check
        if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
            return "youtube"
        else:
            raise InvalidInputError(f"URL is not a YouTube link: {input_source}")

    # Check if it's an existing file
    if os.path.exists(input_source):
        return "local_file"

    # Neither URL nor file
    raise InvalidInputError(
        f"Invalid input: '{input_source}' is neither a YouTube URL nor an existing file"
    )


def extract_artist_title_from_filename(file_path: str) -> tuple[str, str]:
    """
    Extract artist and title from filename.

    Tries to parse patterns like:
    - "Artist - Title.mp3"
    - "Artist_-_Title.wav"
    - "Title.mp3" (artist = "Unknown")

    Args:
        file_path: Path to audio file

    Returns:
        (artist, title) tuple
    """
    filename = Path(file_path).stem  # Remove extension

    # Try to split on " - " or "_-_"
    if " - " in filename:
        parts = filename.split(" - ", 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
    elif "_-_" in filename:
        parts = filename.split("_-_", 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()

    # Fallback: use filename as title, "Unknown" as artist
    logger.warning(
        f"Could not extract artist from filename '{filename}'. "
        "Using 'Unknown' as artist."
    )
    return "Unknown", filename.strip()


def extract_artist_title_from_youtube_title(video_title: str) -> tuple[str, str]:
    """
    Extract artist and title from YouTube video title.

    Common patterns:
    - "Artist - Title"
    - "Artist: Title"
    - "Title (Official Video)" → artist="Unknown"

    Args:
        video_title: YouTube video title

    Returns:
        (artist, title) tuple
    """
    # Try " - " separator
    if " - " in video_title:
        parts = video_title.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()

    # Try ": " separator
    if ": " in video_title:
        parts = video_title.split(": ", 1)
        return parts[0].strip(), parts[1].strip()

    # Fallback: use whole title, "Unknown" artist
    logger.warning(
        f"Could not extract artist from YouTube title '{video_title}'. "
        "Using 'Unknown' as artist."
    )
    return "Unknown", video_title.strip()


def check_cache(song_id: str) -> Optional[Dict]:
    """
    Check if song is already in ChromaDB cache.

    Args:
        song_id: Sanitized song ID

    Returns:
        Metadata dict if cached, None otherwise
    """
    try:
        client = get_client()
        collection = client.get_collection()

        result = collection.get(ids=[song_id])

        if result['ids']:
            logger.info(f"Song '{song_id}' found in cache")
            metadata = result['metadatas'][0] if result['metadatas'] else {}
            return metadata

        logger.info(f"Song '{song_id}' not in cache")
        return None

    except Exception as e:
        logger.warning(f"Error checking cache for '{song_id}': {e}")
        return None


def validate_audio_file(file_path: str) -> None:
    """
    Validate audio file meets minimum requirements.

    Checks:
    - File exists
    - File size > 100KB (not empty)
    - Duration > 30 seconds (using librosa)

    Args:
        file_path: Path to audio file

    Raises:
        ValidationError: If validation fails
    """
    import librosa

    # Check existence
    if not os.path.exists(file_path):
        raise ValidationError(f"File does not exist: {file_path}")

    # Check size
    file_size = os.path.getsize(file_path)
    min_size = 100 * 1024  # 100 KB
    if file_size < min_size:
        raise ValidationError(
            f"File too small ({file_size} bytes). "
            f"Minimum: {min_size} bytes"
        )

    # Check duration
    try:
        duration = librosa.get_duration(path=file_path)
        if duration < 30.0:
            raise ValidationError(
                f"Audio too short ({duration:.1f} seconds). "
                "Minimum: 30 seconds"
            )

        logger.info(f"Validation passed: {duration:.1f}s, {file_size / (1024*1024):.1f} MB")

    except Exception as e:
        raise ValidationError(f"Could not read audio file: {e}")


def convert_to_standard_wav(input_path: str, output_path: str) -> None:
    """
    Convert audio file to standard WAV format.

    Standard: 44.1kHz, 16-bit, stereo

    Args:
        input_path: Source audio file
        output_path: Destination WAV file

    Raises:
        ValidationError: If conversion fails
    """
    import subprocess

    config = get_config()
    sample_rate = config.get("audio.sample_rate", 44100)
    bit_depth = config.get("audio.bit_depth", 16)
    channels = config.get("audio.channels", 2)

    # Use ffmpeg for conversion
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-ar", str(sample_rate),        # Sample rate
        "-ac", str(channels),            # Channels (stereo)
        "-sample_fmt", f"s{bit_depth}",  # Bit depth
        "-y",                             # Overwrite output
        output_path
    ]

    try:
        logger.info(f"Converting to WAV: {sample_rate}Hz, {bit_depth}-bit, {channels}ch")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            raise ValidationError(
                f"ffmpeg conversion failed: {result.stderr}"
            )

        logger.info(f"Conversion successful: {output_path}")

    except subprocess.TimeoutExpired:
        raise ValidationError("Audio conversion timed out (>5 minutes)")
    except FileNotFoundError:
        raise ValidationError(
            "ffmpeg not found. Please install ffmpeg to use The Mixer."
        )
    except Exception as e:
        raise ValidationError(f"Conversion error: {e}")


def ingest_local_file(file_path: str) -> IngestionResult:
    """
    Ingest audio from local file.

    Steps:
    1. Extract artist/title from filename
    2. Generate song ID
    3. Check cache
    4. Convert to standard WAV
    5. Validate
    6. Copy to library cache

    Args:
        file_path: Path to local audio file

    Returns:
        IngestionResult with id, path, cached status
    """
    config = get_config()
    library_cache = config.get_path("library_cache")
    failed_dir = config.get_path("failed_files")

    # Ensure directories exist
    library_cache.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)

    # Extract artist/title
    artist, title = extract_artist_title_from_filename(file_path)
    song_id = sanitize_id(artist, title)

    logger.info(f"Ingesting local file: {artist} - {title} (ID: {song_id})")

    # Check cache
    cached_metadata = check_cache(song_id)
    if cached_metadata:
        cached_path = cached_metadata.get('path', '')
        if os.path.exists(cached_path):
            return IngestionResult(
                id=song_id,
                path=cached_path,
                cached=True,
                source="local_file",
                metadata=cached_metadata
            )
        else:
            logger.warning(f"Cached file missing: {cached_path}. Re-ingesting.")

    # Determine output path
    output_filename = f"{song_id}.wav"
    output_path = str(library_cache / output_filename)

    try:
        # Convert to standard WAV
        convert_to_standard_wav(file_path, output_path)

        # Validate
        validate_audio_file(output_path)

        logger.info(f"Successfully ingested: {output_path}")

        return IngestionResult(
            id=song_id,
            path=output_path,
            cached=False,
            source="local_file",
            metadata=None  # Will be populated by Analyst Agent
        )

    except ValidationError as e:
        # Move to failed directory
        failed_path = failed_dir / output_filename
        if os.path.exists(output_path):
            shutil.move(output_path, failed_path)

        logger.error(f"Ingestion failed: {e}")
        raise


def ingest_youtube_url(url: str) -> IngestionResult:
    """
    Ingest audio from YouTube URL.

    Steps:
    1. Download using yt-dlp
    2. Extract artist/title from video metadata
    3. Generate song ID
    4. Check cache
    5. Convert to standard WAV
    6. Validate

    Args:
        url: YouTube URL

    Returns:
        IngestionResult with id, path, cached status
    """
    import subprocess
    import json

    config = get_config()
    library_cache = config.get_path("library_cache")
    failed_dir = config.get_path("failed_files")

    # Ensure directories exist
    library_cache.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading from YouTube: {url}")

    # First, extract metadata without downloading
    try:
        metadata_cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-playlist",
            url
        ]

        result = subprocess.run(
            metadata_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise DownloadError(f"Failed to fetch YouTube metadata: {result.stderr}")

        metadata = json.loads(result.stdout)
        video_title = metadata.get('title', 'Unknown')

    except subprocess.TimeoutExpired:
        raise DownloadError("YouTube metadata fetch timed out")
    except json.JSONDecodeError:
        raise DownloadError("Could not parse YouTube metadata")
    except Exception as e:
        raise DownloadError(f"Error fetching YouTube metadata: {e}")

    # Extract artist/title
    artist, title = extract_artist_title_from_youtube_title(video_title)
    song_id = sanitize_id(artist, title)

    logger.info(f"YouTube video: {artist} - {title} (ID: {song_id})")

    # Check cache
    cached_metadata = check_cache(song_id)
    if cached_metadata:
        cached_path = cached_metadata.get('path', '')
        if os.path.exists(cached_path):
            return IngestionResult(
                id=song_id,
                path=cached_path,
                cached=True,
                source="youtube",
                metadata=cached_metadata
            )
        else:
            logger.warning(f"Cached file missing: {cached_path}. Re-downloading.")

    # Download audio
    output_filename = f"{song_id}.%(ext)s"
    output_template = str(library_cache / output_filename)

    try:
        download_cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "wav",
            "--audio-quality", "0",  # Best quality
            "--no-playlist",
            "--output", output_template,
            url
        ]

        logger.info("Downloading audio...")
        result = subprocess.run(
            download_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if result.returncode != 0:
            raise DownloadError(f"yt-dlp download failed: {result.stderr}")

        # yt-dlp should create file with .wav extension
        output_path = str(library_cache / f"{song_id}.wav")

        if not os.path.exists(output_path):
            raise DownloadError(f"Download succeeded but file not found: {output_path}")

        # Validate
        validate_audio_file(output_path)

        logger.info(f"Successfully downloaded: {output_path}")

        return IngestionResult(
            id=song_id,
            path=output_path,
            cached=False,
            source="youtube",
            metadata=None  # Will be populated by Analyst Agent
        )

    except subprocess.TimeoutExpired:
        raise DownloadError("YouTube download timed out (>10 minutes)")
    except ValidationError as e:
        # Move to failed directory
        output_path = str(library_cache / f"{song_id}.wav")
        failed_path = failed_dir / f"{song_id}.wav"

        if os.path.exists(output_path):
            shutil.move(output_path, failed_path)

        logger.error(f"Download validation failed: {e}")
        raise
    except Exception as e:
        raise DownloadError(f"Unexpected error during download: {e}")


def extract_playlist_info(playlist_url: str) -> list[dict]:
    """
    Extract video information from a YouTube playlist without downloading.

    Args:
        playlist_url: YouTube playlist URL

    Returns:
        List of dicts with keys: url, title, duration, uploader

    Raises:
        DownloadError: If playlist extraction fails
    """
    import subprocess
    import json

    logger.info(f"Extracting playlist info from: {playlist_url}")

    try:
        # Use yt-dlp to extract playlist info without downloading
        result = subprocess.run(
            [
                "yt-dlp",
                "--flat-playlist",
                "--dump-json",
                "--no-warnings",
                playlist_url
            ],
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout
            check=True
        )

        # Parse JSON lines (one JSON object per video)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video_data = json.loads(line)
                    videos.append({
                        'url': f"https://www.youtube.com/watch?v={video_data['id']}",
                        'title': video_data.get('title', 'Unknown'),
                        'duration': video_data.get('duration', 0),
                        'uploader': video_data.get('uploader', 'Unknown')
                    })
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON line: {line}")
                    continue

        logger.info(f"Extracted {len(videos)} videos from playlist")
        return videos

    except subprocess.TimeoutExpired:
        raise DownloadError("Playlist extraction timed out")
    except subprocess.CalledProcessError as e:
        raise DownloadError(f"Failed to extract playlist: {e.stderr}")
    except Exception as e:
        raise DownloadError(f"Unexpected error extracting playlist: {e}")


def ingest_song(input_source: str, max_retries: int = 3) -> IngestionResult:
    """
    Ingest audio from YouTube URL or local file.

    Main entry point for the Ingestion Agent.

    Args:
        input_source: YouTube URL or absolute file path
        max_retries: Number of retry attempts for network operations

    Returns:
        IngestionResult with keys: id, path, cached, source, metadata

    Raises:
        InvalidInputError: If input is neither URL nor existing file
        DownloadError: If YouTube download fails after retries
        ValidationError: If file validation fails
    """
    # Detect source type
    source_type = detect_source_type(input_source)

    # Ingest based on source
    if source_type == "local_file":
        return ingest_local_file(input_source)

    elif source_type == "youtube":
        # Retry logic for YouTube downloads
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                return ingest_youtube_url(input_source)

            except DownloadError as e:
                last_error = e
                if attempt < max_retries:
                    import time
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Download failed (attempt {attempt}/{max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Download failed after {max_retries} attempts: {e}"
                    )

        # If we get here, all retries failed
        raise last_error

    else:
        # Should never reach here
        raise InvalidInputError(f"Unknown source type: {source_type}")
