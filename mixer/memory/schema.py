"""Schema validation and ID sanitization for ChromaDB."""

import re
from typing import Optional
from datetime import datetime
from mixer.types import SongMetadata


class SchemaError(Exception):
    """Schema validation errors."""
    pass


def sanitize_id(artist: str, title: str) -> str:
    """Sanitize artist and title into a valid ChromaDB ID.

    Rules (from PRD lines 205-213):
    - Lowercase
    - Replace spaces with underscores
    - Remove special characters (keep only a-z, 0-9, _)
    - Max length: 128 characters

    Args:
        artist: Artist name (e.g., "Taylor Swift")
        title: Song title (e.g., "Shake It Off")

    Returns:
        Sanitized ID (e.g., "taylor_swift_shake_it_off")

    Examples:
        >>> sanitize_id("Taylor Swift", "Shake It Off")
        'taylor_swift_shake_it_off'
        >>> sanitize_id("Ke$ha", "TiK ToK")
        'keha_tik_tok'
        >>> sanitize_id("AC/DC", "Back in Black")
        'acdc_back_in_black'
    """
    if not artist or not title:
        raise SchemaError("Artist and title cannot be empty")

    # Combine artist and title
    combined = f"{artist}_{title}"

    # Lowercase
    combined = combined.lower()

    # Replace spaces with underscores
    combined = combined.replace(" ", "_")

    # Remove special characters (keep only a-z, 0-9, _)
    combined = re.sub(r'[^a-z0-9_]', '', combined)

    # Remove consecutive underscores
    combined = re.sub(r'_+', '_', combined)

    # Remove leading/trailing underscores
    combined = combined.strip("_")

    # Enforce max length (128 characters)
    if len(combined) > 128:
        combined = combined[:128]

    # Ensure we didn't end up with empty string
    if not combined:
        raise SchemaError(f"Sanitization resulted in empty ID for artist='{artist}', title='{title}'")

    return combined


def validate_metadata(metadata: SongMetadata) -> None:
    """Validate song metadata before ChromaDB insertion.

    Args:
        metadata: Song metadata dictionary

    Raises:
        SchemaError: If metadata is invalid
    """
    required_fields = [
        "source", "path", "artist", "title", "sample_rate",
        "duration_sec", "has_vocals", "primary_genre", "genres",
        "mood_summary", "energy_level", "valence", "irony_score"
    ]

    # Check required fields
    for field in required_fields:
        if field not in metadata:
            raise SchemaError(f"Missing required field: {field}")

    # Validate source type
    if metadata["source"] not in ["youtube", "local_file"]:
        raise SchemaError(f"Invalid source: {metadata['source']}. Must be 'youtube' or 'local_file'")

    # Validate numeric ranges
    if metadata.get("irony_score") is not None:
        if not (0 <= metadata["irony_score"] <= 10):
            raise SchemaError(f"irony_score must be 0-10, got {metadata['irony_score']}")

    if metadata.get("energy_level") is not None:
        if not (0 <= metadata["energy_level"] <= 10):
            raise SchemaError(f"energy_level must be 0-10, got {metadata['energy_level']}")

    if metadata.get("valence") is not None:
        if not (0 <= metadata["valence"] <= 10):
            raise SchemaError(f"valence must be 0-10, got {metadata['valence']}")

    # Validate BPM range (if present)
    if metadata.get("bpm") is not None:
        if not (20 <= metadata["bpm"] <= 300):
            raise SchemaError(f"bpm must be 20-300, got {metadata['bpm']}")

    # Validate sample rate
    valid_sample_rates = [22050, 44100, 48000, 96000]
    if metadata["sample_rate"] not in valid_sample_rates:
        raise SchemaError(
            f"sample_rate must be one of {valid_sample_rates}, got {metadata['sample_rate']}"
        )

    # Validate duration
    if metadata["duration_sec"] <= 0:
        raise SchemaError(f"duration_sec must be positive, got {metadata['duration_sec']}")

    # Validate genres is a non-empty list
    if not isinstance(metadata["genres"], list) or len(metadata["genres"]) == 0:
        raise SchemaError("genres must be a non-empty list")

    # Validate primary_genre is in genres list
    if metadata["primary_genre"] not in metadata["genres"]:
        raise SchemaError(f"primary_genre '{metadata['primary_genre']}' not in genres list")


def create_document(transcript: str, mood_summary: str) -> str:
    """Create ChromaDB document from lyrics and mood.

    Args:
        transcript: Full lyrical transcription from Whisper
        mood_summary: LLM-generated mood description

    Returns:
        Formatted document string for embedding

    Example:
        >>> create_document("Verse 1: I've been walking...", "Melancholic introspection")
        'Verse 1: I've been walking...\n\n[MOOD]: Melancholic introspection'
    """
    return f"{transcript}\n\n[MOOD]: {mood_summary}"


def generate_timestamp() -> str:
    """Generate ISO 8601 timestamp for date_added field.

    Returns:
        ISO 8601 formatted timestamp string

    Example:
        >>> generate_timestamp()
        '2026-01-18T22:30:45Z'
    """
    return datetime.utcnow().isoformat() + "Z"


def handle_id_collision(base_id: str, existing_ids: list[str]) -> str:
    """Handle ID collision by appending version suffix.

    Args:
        base_id: Base sanitized ID
        existing_ids: List of existing IDs in ChromaDB

    Returns:
        Unique ID with version suffix if needed

    Examples:
        >>> handle_id_collision("artist_song", ["artist_song"])
        'artist_song_v2'
        >>> handle_id_collision("artist_song", ["artist_song", "artist_song_v2"])
        'artist_song_v3'
    """
    if base_id not in existing_ids:
        return base_id

    # Try appending _v2, _v3, etc.
    version = 2
    while True:
        versioned_id = f"{base_id}_v{version}"
        if versioned_id not in existing_ids:
            return versioned_id
        version += 1

        # Safety check to prevent infinite loop
        if version > 100:
            raise SchemaError(f"Too many ID collisions for {base_id}")


def extract_artist_title_from_filename(filename: str) -> tuple[str, str]:
    """Extract artist and title from filename.

    Supports formats:
    - "Artist - Title.mp3"
    - "Artist_Title.wav"
    - "Title.flac" (artist defaults to "Unknown")

    Args:
        filename: Audio filename

    Returns:
        Tuple of (artist, title)

    Examples:
        >>> extract_artist_title_from_filename("Taylor Swift - Shake It Off.mp3")
        ('Taylor Swift', 'Shake It Off')
        >>> extract_artist_title_from_filename("unknown_song.wav")
        ('Unknown', 'unknown_song')
    """
    # Remove file extension
    name_without_ext = re.sub(r'\.(mp3|wav|flac|m4a|ogg)$', '', filename, flags=re.IGNORECASE)

    # Try "Artist - Title" format
    if " - " in name_without_ext:
        parts = name_without_ext.split(" - ", 1)
        return (parts[0].strip(), parts[1].strip())

    # Try "Artist_Title" format
    if "_" in name_without_ext and not name_without_ext.startswith("_"):
        parts = name_without_ext.split("_", 1)
        return (parts[0].strip(), parts[1].strip())

    # Default: use filename as title, artist unknown
    return ("Unknown", name_without_ext.strip())


def camelot_to_key(camelot: str) -> str:
    """Convert Camelot notation to traditional key notation.

    Args:
        camelot: Camelot wheel notation (e.g., "8B")

    Returns:
        Traditional key notation (e.g., "Cmaj")

    Raises:
        SchemaError: If camelot notation is invalid
    """
    camelot_map = {
        "1A": "Abmin", "1B": "Bmaj",
        "2A": "Ebmin", "2B": "F#maj",
        "3A": "Bbmin", "3B": "Dbmaj",
        "4A": "Fmin", "4B": "Abmaj",
        "5A": "Cmin", "5B": "Ebmaj",
        "6A": "Gmin", "6B": "Bbmaj",
        "7A": "Dmin", "7B": "Fmaj",
        "8A": "Amin", "8B": "Cmaj",
        "9A": "Emin", "9B": "Gmaj",
        "10A": "Bmin", "10B": "Dmaj",
        "11A": "F#min", "11B": "Amaj",
        "12A": "C#min", "12B": "Emaj",
    }

    if camelot not in camelot_map:
        raise SchemaError(f"Invalid Camelot notation: {camelot}")

    return camelot_map[camelot]


def key_to_camelot(key: str) -> str:
    """Convert traditional key notation to Camelot notation.

    Args:
        key: Traditional key notation (e.g., "Cmaj", "Amin")

    Returns:
        Camelot wheel notation (e.g., "8B", "8A")

    Raises:
        SchemaError: If key notation is invalid
    """
    key_map = {
        "Abmin": "1A", "Bmaj": "1B",
        "Ebmin": "2A", "F#maj": "2B",
        "Bbmin": "3A", "Dbmaj": "3B",
        "Fmin": "4A", "Abmaj": "4B",
        "Cmin": "5A", "Ebmaj": "5B",
        "Gmin": "6A", "Bbmaj": "6B",
        "Dmin": "7A", "Fmaj": "7B",
        "Amin": "8A", "Cmaj": "8B",
        "Emin": "9A", "Gmaj": "9B",
        "Bmin": "10A", "Dmaj": "10B",
        "F#min": "11A", "Amaj": "11B",
        "C#min": "12A", "Emaj": "12B",
    }

    if key not in key_map:
        raise SchemaError(f"Invalid key notation: {key}")

    return key_map[key]
