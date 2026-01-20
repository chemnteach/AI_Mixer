"""Engineer Agent - Creates mashups from analyzed songs."""

import logging
from pathlib import Path
from typing import Dict, Optional, List
import numpy as np
import librosa

from mixer.config import get_config
from mixer.memory import get_song
from mixer.types import SongMetadata, MashupConfig, QualityPreset, OutputFormat
from mixer.audio.processing import (
    separate_stems,
    time_stretch,
    align_to_grid,
    mix_and_export,
    combine_stems,
    pitch_shift,
    calculate_semitone_shift,
    ProcessingError
)


logger = logging.getLogger(__name__)


class EngineerError(Exception):
    """Base exception for engineer errors."""
    pass


class SongNotFoundError(EngineerError):
    """Raised when song not found in library."""
    pass


class MashupConfigError(EngineerError):
    """Raised when mashup configuration is invalid."""
    pass


def _load_song_audio(song_id: str) -> tuple[np.ndarray, SongMetadata]:
    """
    Load song audio and metadata from library.

    Args:
        song_id: Song ID in ChromaDB

    Returns:
        (audio_array, metadata) tuple

    Raises:
        SongNotFoundError: If song not found
        EngineerError: If audio file cannot be loaded
    """
    logger.info(f"Loading song: {song_id}")

    # Get metadata from memory
    metadata = get_song(song_id)
    if not metadata:
        raise SongNotFoundError(f"Song not found in library: {song_id}")

    # Load audio file
    audio_path = metadata.get("path")
    if not audio_path or not Path(audio_path).exists():
        raise EngineerError(f"Audio file not found: {audio_path}")

    try:
        # Load as mono (simpler for processing)
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        logger.info(f"✅ Loaded: {song_id} ({len(y)/sr:.1f}s @ {sr}Hz)")
        return y, metadata

    except Exception as e:
        raise EngineerError(f"Failed to load audio {audio_path}: {e}")


def _calculate_stretch_ratio(source_bpm: float, target_bpm: float) -> float:
    """
    Calculate time-stretch ratio to align BPMs.

    Args:
        source_bpm: BPM of source audio
        target_bpm: Target BPM to match

    Returns:
        Stretch ratio (e.g., 1.2 = 20% faster)
    """
    ratio = target_bpm / source_bpm
    logger.info(f"Stretch ratio: {ratio:.3f} ({source_bpm:.1f} → {target_bpm:.1f} BPM)")
    return ratio


def create_classic_mashup(
    vocal_id: str,
    inst_id: str,
    output_path: Optional[str] = None,
    quality: Optional[QualityPreset] = None,
    output_format: Optional[OutputFormat] = None
) -> str:
    """
    Create classic mashup: Vocal from song A + Instrumental from song B.

    Workflow:
    1. Load both songs from library
    2. Separate vocal track from song A
    3. Separate instrumental (everything except vocals) from song B
    4. Time-stretch vocal to match instrumental BPM
    5. Align by first downbeat
    6. Mix and export

    Args:
        vocal_id: ID of song to extract vocals from
        inst_id: ID of song to extract instrumental from
        output_path: Output file path (auto-generated if None)
        quality: "draft" | "high" | "broadcast" (from config if None)
        output_format: "mp3" | "wav" (from config if None)

    Returns:
        Absolute path to exported mashup

    Raises:
        SongNotFoundError: If either song not found
        EngineerError: If mashup creation fails
    """
    config = get_config()

    # Set defaults from config
    if quality is None:
        quality = config.get("engineer.default_quality", "high")
    if output_format is None:
        output_format = "mp3"

    logger.info(f"=== Creating Classic Mashup ===")
    logger.info(f"Vocal: {vocal_id}")
    logger.info(f"Instrumental: {inst_id}")
    logger.info(f"Quality: {quality}, Format: {output_format}")

    try:
        # Load songs
        vocal_audio, vocal_meta = _load_song_audio(vocal_id)
        inst_audio, inst_meta = _load_song_audio(inst_id)

        # Get sample rates
        vocal_sr = vocal_meta.get("sample_rate", 44100)
        inst_sr = inst_meta.get("sample_rate", 44100)

        # Separate stems
        logger.info("Separating vocal stems...")
        vocal_stems = separate_stems(
            vocal_meta["path"],
            model_name=config.get("models.demucs_model", "htdemucs"),
            device=None  # Auto-detect
        )
        vocals_only = vocal_stems["vocals"]

        logger.info("Separating instrumental stems...")
        inst_stems = separate_stems(
            inst_meta["path"],
            model_name=config.get("models.demucs_model", "htdemucs"),
            device=None
        )
        # Combine everything except vocals for instrumental
        instrumental = combine_stems(inst_stems, exclude=["vocals"])

        # Calculate stretch ratio
        vocal_bpm = vocal_meta.get("bpm")
        inst_bpm = inst_meta.get("bpm")

        if not vocal_bpm or not inst_bpm:
            raise EngineerError(
                f"Missing BPM metadata: vocal={vocal_bpm}, inst={inst_bpm}. "
                "Run analyst agent first."
            )

        stretch_ratio = _calculate_stretch_ratio(vocal_bpm, inst_bpm)

        # Check if stretch is within acceptable range
        max_stretch = config.get("curator.max_stretch_ratio", 1.2)
        if stretch_ratio > max_stretch or stretch_ratio < (1/max_stretch):
            logger.warning(
                f"Stretch ratio {stretch_ratio:.2f} exceeds max {max_stretch}. "
                "Quality may be degraded."
            )

        # Time-stretch vocals to match instrumental BPM
        logger.info("Time-stretching vocals...")
        vocals_stretched = time_stretch(
            vocals_only,
            sr=vocal_sr,
            stretch_ratio=stretch_ratio,
            quality=quality
        )

        # Align by downbeat
        vocal_downbeat = vocal_meta.get("first_downbeat_sec", 0.0)
        inst_downbeat = inst_meta.get("first_downbeat_sec", 0.0)

        vocals_aligned, inst_aligned = align_to_grid(
            vocals_stretched,
            instrumental,
            vocal_downbeat_sec=vocal_downbeat,
            inst_downbeat_sec=inst_downbeat,
            stretch_ratio=stretch_ratio,
            sr=inst_sr
        )

        # Generate output path if not provided
        if output_path is None:
            output_dir = config.get_path("mashup_output")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{vocal_id}_x_{inst_id}.{output_format}")

        # Mix and export
        vocal_attenuation = config.get("engineer.vocal_attenuation_db", -2.0)

        mashup_path = mix_and_export(
            vocals_aligned,
            inst_aligned,
            output_path=output_path,
            sr=inst_sr,
            output_format=output_format,
            vocal_attenuation_db=vocal_attenuation
        )

        logger.info(f"🎵 Classic mashup created: {mashup_path}")
        return mashup_path

    except (SongNotFoundError, ProcessingError) as e:
        raise
    except Exception as e:
        raise EngineerError(f"Classic mashup creation failed: {e}")


def create_stem_swap_mashup(
    stem_config: Dict[str, str],
    output_path: Optional[str] = None,
    quality: Optional[QualityPreset] = None,
    output_format: Optional[OutputFormat] = None
) -> str:
    """
    Create stem role swapping mashup: Mix stems from 3+ different songs.

    Takes specific stems from different songs and combines them into a single track.
    All stems are time-stretched to match a target BPM.

    Args:
        stem_config: Dict mapping stem type to song_id
                     e.g., {"vocals": "song1", "drums": "song2", "bass": "song3", "other": "song4"}
                     At minimum must have 2 stems from different songs
        output_path: Output file path (auto-generated if None)
        quality: "draft" | "high" | "broadcast" (from config if None)
        output_format: "mp3" | "wav" (from config if None)

    Returns:
        Absolute path to exported mashup

    Raises:
        MashupConfigError: If stem_config is invalid
        SongNotFoundError: If any song not found
        EngineerError: If mashup creation fails
    """
    config = get_config()

    # Set defaults
    if quality is None:
        quality = config.get("engineer.default_quality", "high")
    if output_format is None:
        output_format = "mp3"

    # Validate stem_config
    valid_stems = {"vocals", "drums", "bass", "other"}
    if not stem_config or len(stem_config) < 2:
        raise MashupConfigError("stem_config must have at least 2 stems from different songs")

    for stem_type in stem_config.keys():
        if stem_type not in valid_stems:
            raise MashupConfigError(
                f"Invalid stem type: {stem_type}. Must be one of {valid_stems}"
            )

    # Check that we have different songs (at least 2 unique)
    unique_songs = set(stem_config.values())
    if len(unique_songs) < 2:
        raise MashupConfigError("Must use stems from at least 2 different songs")

    logger.info(f"=== Creating Stem Swap Mashup ===")
    logger.info(f"Stem config: {stem_config}")
    logger.info(f"Quality: {quality}, Format: {output_format}")

    try:
        # Load all unique songs and their metadata
        song_data = {}  # song_id -> (audio, metadata, stems)
        all_bpms = []

        for song_id in unique_songs:
            audio, metadata = _load_song_audio(song_id)

            bpm = metadata.get("bpm")
            if not bpm:
                raise EngineerError(f"Missing BPM for {song_id}. Run analyst agent first.")
            all_bpms.append(bpm)

            # Separate stems
            logger.info(f"Separating stems for {song_id}...")
            stems = separate_stems(
                metadata["path"],
                model_name=config.get("models.demucs_model", "htdemucs"),
                device=None
            )

            song_data[song_id] = {
                "audio": audio,
                "metadata": metadata,
                "stems": stems,
                "sr": metadata.get("sample_rate", 44100)
            }

        # Determine target BPM (use median of all BPMs)
        target_bpm = float(np.median(all_bpms))
        logger.info(f"Target BPM: {target_bpm:.1f} (median of {all_bpms})")

        # Time-stretch and collect stems
        processed_stems = {}
        target_sr = 44100  # Standard sample rate

        for stem_type, song_id in stem_config.items():
            data = song_data[song_id]
            stem_audio = data["stems"][stem_type]
            source_bpm = data["metadata"]["bpm"]
            source_sr = data["sr"]

            # Calculate stretch ratio
            stretch_ratio = _calculate_stretch_ratio(source_bpm, target_bpm)

            # Time-stretch stem to target BPM
            logger.info(f"Stretching {stem_type} from {song_id}...")
            stretched = time_stretch(
                stem_audio,
                sr=source_sr,
                stretch_ratio=stretch_ratio,
                quality=quality
            )

            processed_stems[stem_type] = stretched

        # Find minimum length
        min_length = min(len(stem) for stem in processed_stems.values())
        logger.info(f"Trimming all stems to {min_length / target_sr:.1f}s")

        # Trim all stems to same length and mix
        final_mix = None
        for stem_type, stem_audio in processed_stems.items():
            trimmed = stem_audio[:min_length]

            if final_mix is None:
                final_mix = trimmed.copy()
            else:
                final_mix = final_mix + trimmed

        # Normalize mix
        max_val = np.abs(final_mix).max()
        if max_val > 0:
            final_mix = final_mix / max_val * 0.95  # Leave headroom

        # Generate output path
        if output_path is None:
            output_dir = config.get_path("mashup_output")
            output_dir.mkdir(parents=True, exist_ok=True)
            stem_names = "_".join(stem_config.keys())
            output_path = str(output_dir / f"stem_swap_{stem_names}.{output_format}")

        # Convert to AudioSegment and export
        logger.info("Exporting stem swap mashup...")
        from mixer.audio.processing import numpy_to_audiosegment

        mashup_seg = numpy_to_audiosegment(final_mix, target_sr)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Export
        if output_format == "mp3":
            mashup_seg.export(
                output_path,
                format="mp3",
                bitrate="320k",
                parameters=["-q:a", "0"]
            )
        elif output_format == "wav":
            mashup_seg.export(
                output_path,
                format="wav",
                parameters=["-ac", "2", "-ar", str(target_sr)]
            )
        else:
            raise MashupConfigError(f"Unsupported output format: {output_format}")

        logger.info(f"🎵 Stem swap mashup created: {output_path}")
        return output_path

    except (SongNotFoundError, MashupConfigError, ProcessingError) as e:
        raise
    except Exception as e:
        raise EngineerError(f"Stem swap mashup creation failed: {e}")


def create_energy_matched_mashup(
    song_a_id: str,
    song_b_id: str,
    output_path: Optional[str] = None,
    quality: Optional[QualityPreset] = None,
    output_format: Optional[OutputFormat] = None
) -> str:
    """
    Create energy-matched mashup: Swap between songs based on energy curves.

    Analyzes section-level energy from both songs and creates a mashup that
    follows the energy arc by switching between songs at section boundaries.
    High-energy sections from both songs are used during peaks, low-energy
    sections during valleys.

    Args:
        song_a_id: First song ID
        song_b_id: Second song ID
        output_path: Output file path (auto-generated if None)
        quality: "draft" | "high" | "broadcast" (from config if None)
        output_format: "mp3" | "wav" (from config if None)

    Returns:
        Absolute path to exported mashup

    Raises:
        SongNotFoundError: If either song not found
        EngineerError: If songs lack section metadata or creation fails
    """
    config = get_config()

    if quality is None:
        quality = config.get("engineer.default_quality", "high")
    if output_format is None:
        output_format = "mp3"

    logger.info(f"=== Creating Energy-Matched Mashup ===")
    logger.info(f"Song A: {song_a_id}")
    logger.info(f"Song B: {song_b_id}")

    try:
        # Load songs
        audio_a, meta_a = _load_song_audio(song_a_id)
        audio_b, meta_b = _load_song_audio(song_b_id)

        # Check for section metadata
        sections_a = meta_a.get("sections", [])
        sections_b = meta_b.get("sections", [])

        if not sections_a or not sections_b:
            raise EngineerError(
                "Songs must have section-level metadata. Run analyst agent first."
            )

        sr_a = meta_a.get("sample_rate", 44100)
        sr_b = meta_b.get("sample_rate", 44100)

        # Time-stretch song B to match song A's BPM
        bpm_a = meta_a.get("bpm")
        bpm_b = meta_b.get("bpm")

        if not bpm_a or not bpm_b:
            raise EngineerError("Songs must have BPM metadata")

        stretch_ratio = _calculate_stretch_ratio(bpm_b, bpm_a)
        audio_b_stretched = time_stretch(audio_b, sr_b, stretch_ratio, quality)

        # Build energy curve: choose high-energy sections from either song
        logger.info("Building energy-matched structure...")

        mashup_parts = []
        current_time = 0.0
        target_sr = sr_a

        # Interleave sections based on energy matching
        max_sections = max(len(sections_a), len(sections_b))

        for i in range(max_sections):
            # Get sections from both songs (if available)
            section_a = sections_a[i] if i < len(sections_a) else None
            section_b = sections_b[i] if i < len(sections_b) else None

            # Choose section with higher energy
            if section_a and section_b:
                energy_a = section_a.get("energy_level", 0.0)
                energy_b = section_b.get("energy_level", 0.0)

                if energy_a >= energy_b:
                    chosen_section = section_a
                    chosen_audio = audio_a
                    chosen_sr = sr_a
                    source = "A"
                else:
                    chosen_section = section_b
                    chosen_audio = audio_b_stretched
                    chosen_sr = sr_b
                    source = "B"

            elif section_a:
                chosen_section = section_a
                chosen_audio = audio_a
                chosen_sr = sr_a
                source = "A"
            elif section_b:
                chosen_section = section_b
                chosen_audio = audio_b_stretched
                chosen_sr = sr_b
                source = "B"
            else:
                break

            # Extract section audio
            start_sample = int(chosen_section["start_sec"] * chosen_sr)
            end_sample = int(chosen_section["end_sec"] * chosen_sr)
            section_audio = chosen_audio[start_sample:end_sample]

            logger.info(
                f"Section {i}: {chosen_section.get('section_type', 'unknown')} "
                f"from {source} (energy={chosen_section.get('energy_level', 0.0):.2f})"
            )

            mashup_parts.append(section_audio)

        # Concatenate all sections
        logger.info("Concatenating sections...")
        final_audio = np.concatenate(mashup_parts)

        # Generate output path
        if output_path is None:
            output_dir = config.get_path("mashup_output")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"energy_matched_{song_a_id}_x_{song_b_id}.{output_format}")

        # Export
        logger.info("Exporting energy-matched mashup...")
        from mixer.audio.processing import numpy_to_audiosegment

        mashup_seg = numpy_to_audiosegment(final_audio, target_sr)

        # Normalize
        from pydub.effects import normalize
        mashup_seg = normalize(mashup_seg, headroom=2.0)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Export
        if output_format == "mp3":
            mashup_seg.export(
                output_path,
                format="mp3",
                bitrate="320k",
                parameters=["-q:a", "0"]
            )
        elif output_format == "wav":
            mashup_seg.export(
                output_path,
                format="wav",
                parameters=["-ac", "2", "-ar", str(target_sr)]
            )
        else:
            raise MashupConfigError(f"Unsupported output format: {output_format}")

        logger.info(f"🎵 Energy-matched mashup created: {output_path}")
        return output_path

    except (SongNotFoundError, ProcessingError) as e:
        raise
    except Exception as e:
        raise EngineerError(f"Energy-matched mashup creation failed: {e}")


def create_adaptive_harmony_mashup(
    song_a_id: str,
    song_b_id: str,
    output_path: Optional[str] = None,
    quality: Optional[QualityPreset] = None,
    output_format: Optional[OutputFormat] = None,
    max_pitch_shift_semitones: int = 3
) -> str:
    """
    Create adaptive harmony mashup: Auto-fix key clashes via pitch-shifting.

    Detects key incompatibility between two songs and automatically pitch-shifts
    one to match the other, then creates a classic mashup. Prioritizes minimal
    pitch-shifting to preserve audio quality.

    Args:
        song_a_id: First song ID (used for vocals)
        song_b_id: Second song ID (used for instrumental, may be pitch-shifted)
        output_path: Output file path (auto-generated if None)
        quality: "draft" | "high" | "broadcast" (from config if None)
        output_format: "mp3" | "wav" (from config if None)
        max_pitch_shift_semitones: Maximum allowed pitch shift (default: 3)

    Returns:
        Absolute path to exported mashup

    Raises:
        SongNotFoundError: If either song not found
        EngineerError: If keys incompatible beyond max shift or creation fails
    """
    config = get_config()

    if quality is None:
        quality = config.get("engineer.default_quality", "high")
    if output_format is None:
        output_format = "mp3"

    logger.info(f"=== Creating Adaptive Harmony Mashup ===")
    logger.info(f"Vocal: {song_a_id}")
    logger.info(f"Instrumental: {song_b_id}")

    try:
        # Load songs
        audio_a, meta_a = _load_song_audio(song_a_id)
        audio_b, meta_b = _load_song_audio(song_b_id)

        # Get keys
        key_a = meta_a.get("key")
        key_b = meta_b.get("key")

        if not key_a or not key_b:
            raise EngineerError(
                "Both songs must have key metadata. Run analyst agent first."
            )

        logger.info(f"Keys: {song_a_id}={key_a}, {song_b_id}={key_b}")

        # Calculate required pitch shift
        semitone_shift = calculate_semitone_shift(key_b, key_a)

        if abs(semitone_shift) > max_pitch_shift_semitones:
            logger.warning(
                f"Required pitch shift ({semitone_shift:+d} semitones) exceeds "
                f"maximum ({max_pitch_shift_semitones}). Quality may degrade significantly."
            )

        # Pitch-shift instrumental (song B) to match vocal key (song A)
        sr_a = meta_a.get("sample_rate", 44100)
        sr_b = meta_b.get("sample_rate", 44100)

        if semitone_shift != 0:
            logger.info(f"Pitch-shifting instrumental by {semitone_shift:+d} semitones...")
            audio_b_shifted = pitch_shift(audio_b, sr_b, semitone_shift)
        else:
            logger.info("Keys already compatible, no pitch-shifting needed")
            audio_b_shifted = audio_b

        # Now create classic mashup with harmonically aligned songs
        logger.info("Creating classic mashup with aligned keys...")

        # Separate stems
        vocals = separate_stems(
            meta_a["path"],
            model_name=config.get("models.demucs_model", "htdemucs"),
            device=None
        )["vocals"]

        inst_stems = separate_stems(
            meta_b["path"],
            model_name=config.get("models.demucs_model", "htdemucs"),
            device=None
        )
        instrumental = combine_stems(inst_stems, exclude=["vocals"])

        # Pitch-shift instrumental if needed
        if semitone_shift != 0:
            instrumental = pitch_shift(instrumental, sr_b, semitone_shift)

        # Time-stretch and align
        bpm_a = meta_a.get("bpm")
        bpm_b = meta_b.get("bpm")

        if not bpm_a or not bpm_b:
            raise EngineerError("Songs must have BPM metadata")

        stretch_ratio = _calculate_stretch_ratio(bpm_a, bpm_b)
        vocals_stretched = time_stretch(vocals, sr_a, stretch_ratio, quality)

        # Align by downbeat
        vocal_downbeat = meta_a.get("first_downbeat_sec", 0.0)
        inst_downbeat = meta_b.get("first_downbeat_sec", 0.0)

        vocals_aligned, inst_aligned = align_to_grid(
            vocals_stretched,
            instrumental,
            vocal_downbeat_sec=vocal_downbeat,
            inst_downbeat_sec=inst_downbeat,
            stretch_ratio=stretch_ratio,
            sr=sr_b
        )

        # Generate output path
        if output_path is None:
            output_dir = config.get_path("mashup_output")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(
                output_dir / f"adaptive_harmony_{song_a_id}_x_{song_b_id}.{output_format}"
            )

        # Mix and export
        vocal_attenuation = config.get("engineer.vocal_attenuation_db", -2.0)

        mashup_path = mix_and_export(
            vocals_aligned,
            inst_aligned,
            output_path=output_path,
            sr=sr_b,
            output_format=output_format,
            vocal_attenuation_db=vocal_attenuation
        )

        logger.info(f"🎵 Adaptive harmony mashup created: {mashup_path}")
        logger.info(f"   Key adjustment: {key_b} → {key_a} ({semitone_shift:+d} semitones)")
        return mashup_path

    except (SongNotFoundError, ProcessingError) as e:
        raise
    except Exception as e:
        raise EngineerError(f"Adaptive harmony mashup creation failed: {e}")


def create_theme_fusion_mashup(
    song_a_id: str,
    song_b_id: str,
    theme: str,
    output_path: Optional[str] = None,
    quality: Optional[QualityPreset] = None,
    output_format: Optional[OutputFormat] = None
) -> str:
    """
    Create theme fusion mashup: Filter sections to unified lyrical theme.

    Analyzes lyrical themes in both songs and selects only sections that match
    the specified theme, creating a thematically coherent mashup. Useful for
    creating focused narratives (e.g., only "love" sections, only "rebellion").

    Args:
        song_a_id: First song ID
        song_b_id: Second song ID
        theme: Target theme to filter for (e.g., "love", "heartbreak", "rebellion")
        output_path: Output file path (auto-generated if None)
        quality: "draft" | "high" | "broadcast" (from config if None)
        output_format: "mp3" | "wav" (from config if None)

    Returns:
        Absolute path to exported mashup

    Raises:
        SongNotFoundError: If either song not found
        EngineerError: If songs lack section metadata or no matching sections found
    """
    config = get_config()

    if quality is None:
        quality = config.get("engineer.default_quality", "high")
    if output_format is None:
        output_format = "mp3"

    logger.info(f"=== Creating Theme Fusion Mashup ===")
    logger.info(f"Song A: {song_a_id}")
    logger.info(f"Song B: {song_b_id}")
    logger.info(f"Theme: {theme}")

    try:
        # Load songs
        audio_a, meta_a = _load_song_audio(song_a_id)
        audio_b, meta_b = _load_song_audio(song_b_id)

        # Check for section metadata
        sections_a = meta_a.get("sections", [])
        sections_b = meta_b.get("sections", [])

        if not sections_a or not sections_b:
            raise EngineerError(
                "Songs must have section-level metadata. Run analyst agent first."
            )

        sr_a = meta_a.get("sample_rate", 44100)
        sr_b = meta_b.get("sample_rate", 44100)

        # Time-stretch song B to match song A's BPM
        bpm_a = meta_a.get("bpm")
        bpm_b = meta_b.get("bpm")

        if not bpm_a or not bpm_b:
            raise EngineerError("Songs must have BPM metadata")

        stretch_ratio = _calculate_stretch_ratio(bpm_b, bpm_a)
        audio_b_stretched = time_stretch(audio_b, sr_b, stretch_ratio, quality)

        # Filter sections by theme
        theme_lower = theme.lower()

        def matches_theme(section: dict) -> bool:
            """Check if section matches the target theme."""
            section_themes = section.get("themes", [])
            # Check if theme appears in section themes (case-insensitive)
            return any(theme_lower in t.lower() for t in section_themes)

        # Collect matching sections from both songs
        matching_sections = []

        for section in sections_a:
            if matches_theme(section):
                matching_sections.append({
                    "audio": audio_a,
                    "section": section,
                    "sr": sr_a,
                    "source": "A"
                })

        for section in sections_b:
            if matches_theme(section):
                matching_sections.append({
                    "audio": audio_b_stretched,
                    "section": section,
                    "sr": sr_b,
                    "source": "B"
                })

        if not matching_sections:
            raise EngineerError(
                f"No sections found matching theme '{theme}' in either song. "
                "Try a different theme or check section metadata."
            )

        logger.info(f"Found {len(matching_sections)} sections matching theme '{theme}'")

        # Sort by emotional intensity or energy for coherent flow
        # (Higher energy sections first for impactful opening)
        matching_sections.sort(
            key=lambda x: x["section"].get("energy_level", 0.0),
            reverse=True
        )

        # Build mashup from theme-matched sections
        mashup_parts = []

        for i, item in enumerate(matching_sections):
            section = item["section"]
            audio = item["audio"]
            sr = item["sr"]
            source = item["source"]

            # Extract section audio
            start_sample = int(section["start_sec"] * sr)
            end_sample = int(section["end_sec"] * sr)
            section_audio = audio[start_sample:end_sample]

            logger.info(
                f"Section {i+1}: {section.get('section_type', 'unknown')} "
                f"from {source} - {section.get('emotional_tone', 'unknown')} "
                f"(themes: {section.get('themes', [])})"
            )

            mashup_parts.append(section_audio)

        # Concatenate all theme-matched sections
        logger.info("Concatenating theme-filtered sections...")
        final_audio = np.concatenate(mashup_parts)

        # Generate output path
        if output_path is None:
            output_dir = config.get_path("mashup_output")
            output_dir.mkdir(parents=True, exist_ok=True)
            safe_theme = theme.replace(" ", "_").lower()
            output_path = str(
                output_dir / f"theme_{safe_theme}_{song_a_id}_x_{song_b_id}.{output_format}"
            )

        # Export
        logger.info("Exporting theme fusion mashup...")
        from mixer.audio.processing import numpy_to_audiosegment
        from pydub.effects import normalize

        mashup_seg = numpy_to_audiosegment(final_audio, sr_a)
        mashup_seg = normalize(mashup_seg, headroom=2.0)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Export
        if output_format == "mp3":
            mashup_seg.export(
                output_path,
                format="mp3",
                bitrate="320k",
                parameters=["-q:a", "0"]
            )
        elif output_format == "wav":
            mashup_seg.export(
                output_path,
                format="wav",
                parameters=["-ac", "2", "-ar", str(sr_a)]
            )
        else:
            raise MashupConfigError(f"Unsupported output format: {output_format}")

        logger.info(f"🎵 Theme fusion mashup created: {output_path}")
        logger.info(f"   Theme: '{theme}' ({len(matching_sections)} sections)")
        return output_path

    except (SongNotFoundError, ProcessingError) as e:
        raise
    except Exception as e:
        raise EngineerError(f"Theme fusion mashup creation failed: {e}")


def create_semantic_aligned_mashup(
    song_a_id: str,
    song_b_id: str,
    output_path: Optional[str] = None,
    quality: Optional[QualityPreset] = None,
    output_format: Optional[OutputFormat] = None
) -> str:
    """
    Create semantic-aligned mashup: Meaning-driven structure (not tempo-driven).

    Uses LLM-derived semantic analysis to create a mashup based on lyrical
    function and emotional flow rather than traditional musical structure.
    Pairs questions with answers, narratives with reflections, etc.

    Args:
        song_a_id: First song ID
        song_b_id: Second song ID
        output_path: Output file path (auto-generated if None)
        quality: "draft" | "high" | "broadcast" (from config if None)
        output_format: "mp3" | "wav" (from config if None)

    Returns:
        Absolute path to exported mashup

    Raises:
        SongNotFoundError: If either song not found
        EngineerError: If songs lack section metadata or creation fails
    """
    config = get_config()

    if quality is None:
        quality = config.get("engineer.default_quality", "high")
    if output_format is None:
        output_format = "mp3"

    logger.info(f"=== Creating Semantic-Aligned Mashup ===")
    logger.info(f"Song A: {song_a_id}")
    logger.info(f"Song B: {song_b_id}")

    try:
        # Load songs
        audio_a, meta_a = _load_song_audio(song_a_id)
        audio_b, meta_b = _load_song_audio(song_b_id)

        # Check for section metadata
        sections_a = meta_a.get("sections", [])
        sections_b = meta_b.get("sections", [])

        if not sections_a or not sections_b:
            raise EngineerError(
                "Songs must have section-level metadata. Run analyst agent first."
            )

        sr_a = meta_a.get("sample_rate", 44100)
        sr_b = meta_b.get("sample_rate", 44100)

        # Time-stretch song B to match song A's BPM
        bpm_a = meta_a.get("bpm")
        bpm_b = meta_b.get("bpm")

        if not bpm_a or not bpm_b:
            raise EngineerError("Songs must have BPM metadata")

        stretch_ratio = _calculate_stretch_ratio(bpm_b, bpm_a)
        audio_b_stretched = time_stretch(audio_b, sr_b, stretch_ratio, quality)

        # Define lyrical function pairings (conversational flow)
        function_pairs = {
            "question": "answer",
            "narrative": "reflection",
            "hook": "hook",  # Hooks pair with themselves
            "call": "response"
        }

        # Build semantic structure
        logger.info("Building semantic structure...")
        mashup_parts = []
        used_b_indices = set()  # Track which B sections we've used

        for i, section_a in enumerate(sections_a):
            func_a = section_a.get("lyrical_function", "")

            # Add section from song A
            start_sample = int(section_a["start_sec"] * sr_a)
            end_sample = int(section_a["end_sec"] * sr_a)
            section_audio_a = audio_a[start_sample:end_sample]

            logger.info(
                f"A{i}: {section_a.get('section_type', 'unknown')} - "
                f"{func_a} ({section_a.get('emotional_tone', 'unknown')})"
            )

            mashup_parts.append(section_audio_a)

            # Find matching response from song B
            target_func = function_pairs.get(func_a)

            if target_func:
                # Look for a section in B that matches the target function
                for j, section_b in enumerate(sections_b):
                    if j in used_b_indices:
                        continue

                    func_b = section_b.get("lyrical_function", "")

                    if func_b == target_func:
                        # Found a semantic pair!
                        start_sample_b = int(section_b["start_sec"] * sr_b)
                        end_sample_b = int(section_b["end_sec"] * sr_b)
                        section_audio_b = audio_b_stretched[start_sample_b:end_sample_b]

                        logger.info(
                            f"  → B{j}: {section_b.get('section_type', 'unknown')} - "
                            f"{func_b} ({section_b.get('emotional_tone', 'unknown')}) "
                            "[PAIRED]"
                        )

                        mashup_parts.append(section_audio_b)
                        used_b_indices.add(j)
                        break  # Only pair once per A section

        if len(mashup_parts) <= len(sections_a):
            logger.warning(
                "No semantic pairs found - mashup will only contain song A sections. "
                "Consider using a different mashup type."
            )

        # Concatenate all sections
        logger.info("Concatenating semantically-aligned sections...")
        final_audio = np.concatenate(mashup_parts)

        # Generate output path
        if output_path is None:
            output_dir = config.get_path("mashup_output")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(
                output_dir / f"semantic_aligned_{song_a_id}_x_{song_b_id}.{output_format}"
            )

        # Export
        logger.info("Exporting semantic-aligned mashup...")
        from mixer.audio.processing import numpy_to_audiosegment
        from pydub.effects import normalize

        mashup_seg = numpy_to_audiosegment(final_audio, sr_a)
        mashup_seg = normalize(mashup_seg, headroom=2.0)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Export
        if output_format == "mp3":
            mashup_seg.export(
                output_path,
                format="mp3",
                bitrate="320k",
                parameters=["-q:a", "0"]
            )
        elif output_format == "wav":
            mashup_seg.export(
                output_path,
                format="wav",
                parameters=["-ac", "2", "-ar", str(sr_a)]
            )
        else:
            raise MashupConfigError(f"Unsupported output format: {output_format}")

        pairs_found = len(mashup_parts) - len(sections_a)
        logger.info(f"🎵 Semantic-aligned mashup created: {output_path}")
        logger.info(f"   Semantic pairs: {pairs_found}")
        return output_path

    except (SongNotFoundError, ProcessingError) as e:
        raise
    except Exception as e:
        raise EngineerError(f"Semantic-aligned mashup creation failed: {e}")


def create_role_aware_mashup(
    song_a_id: str,
    song_b_id: str,
    output_path: Optional[str] = None,
    quality: Optional[QualityPreset] = None,
    output_format: Optional[OutputFormat] = None
) -> str:
    """
    Create role-aware mashup: Vocals dynamically shift between lead, harmony, call, response.

    Analyzes vocal characteristics (density, intensity) from section metadata and
    assigns roles to each section. Processes vocals accordingly with role-based
    mixing: lead at full volume, harmony pitch-shifted and attenuated, call/response
    with temporal spacing.

    Args:
        song_a_id: First song ID
        song_b_id: Second song ID
        output_path: Output file path (auto-generated if None)
        quality: "draft" | "high" | "broadcast" (from config if None)
        output_format: "mp3" | "wav" (from config if None)

    Returns:
        Absolute path to exported mashup

    Raises:
        SongNotFoundError: If either song not found
        EngineerError: If songs lack section metadata or creation fails
    """
    config = get_config()

    if quality is None:
        quality = config.get("engineer.default_quality", "high")
    if output_format is None:
        output_format = "mp3"

    logger.info(f"=== Creating Role-Aware Mashup ===")
    logger.info(f"Song A: {song_a_id}")
    logger.info(f"Song B: {song_b_id}")

    try:
        # Load songs
        audio_a, meta_a = _load_song_audio(song_a_id)
        audio_b, meta_b = _load_song_audio(song_b_id)

        # Check for section metadata
        sections_a = meta_a.get("sections", [])
        sections_b = meta_b.get("sections", [])

        if not sections_a or not sections_b:
            raise EngineerError(
                "Songs must have section-level metadata. Run analyst agent first."
            )

        sr_a = meta_a.get("sample_rate", 44100)
        sr_b = meta_b.get("sample_rate", 44100)

        # Separate vocals from both songs
        logger.info("Separating vocal stems...")
        stems_a = separate_stems(
            meta_a["path"],
            model_name=config.get("models.demucs_model", "htdemucs"),
            device=None
        )
        stems_b = separate_stems(
            meta_b["path"],
            model_name=config.get("models.demucs_model", "htdemucs"),
            device=None
        )

        vocals_a = stems_a["vocals"]
        vocals_b = stems_b["vocals"]

        # Combine instrumentals from both songs
        inst_a = combine_stems(stems_a, exclude=["vocals"])
        inst_b = combine_stems(stems_b, exclude=["vocals"])

        # Time-stretch song B to match song A's BPM
        bpm_a = meta_a.get("bpm")
        bpm_b = meta_b.get("bpm")

        if not bpm_a or not bpm_b:
            raise EngineerError("Songs must have BPM metadata")

        stretch_ratio = _calculate_stretch_ratio(bpm_b, bpm_a)
        vocals_b_stretched = time_stretch(vocals_b, sr_b, stretch_ratio, quality)
        inst_b_stretched = time_stretch(inst_b, sr_b, stretch_ratio, quality)

        # Assign roles to sections based on vocal characteristics
        logger.info("Assigning vocal roles...")

        def assign_role(section: dict) -> str:
            """Assign role based on vocal characteristics."""
            density = section.get("vocal_density", "medium")
            intensity = section.get("vocal_intensity", 0.5)
            lyrical_func = section.get("lyrical_function", "")

            # Prioritize lyrical function for call/response
            if lyrical_func == "question":
                return "call"
            elif lyrical_func == "answer":
                return "response"
            # Use density/intensity for lead/harmony/texture
            elif density == "dense" and intensity > 0.6:
                return "lead"
            elif density == "medium" or (density == "dense" and intensity <= 0.6):
                return "harmony"
            else:  # sparse
                return "texture"

        # Build mashup with role-based processing
        logger.info("Building role-aware structure...")
        mashup_parts = []
        target_sr = sr_a

        # Interleave sections from both songs with role assignments
        max_sections = max(len(sections_a), len(sections_b))

        for i in range(max_sections):
            section_a = sections_a[i] if i < len(sections_a) else None
            section_b = sections_b[i] if i < len(sections_b) else None

            # Process section from song A
            if section_a:
                role_a = assign_role(section_a)
                start_sample = int(section_a["start_sec"] * sr_a)
                end_sample = int(section_a["end_sec"] * sr_a)
                vocal_section_a = vocals_a[start_sample:end_sample]
                inst_section_a = inst_a[start_sample:end_sample]

                # Process based on role
                processed_a = _process_vocal_by_role(
                    vocal_section_a,
                    inst_section_a,
                    role_a,
                    sr_a
                )

                logger.info(
                    f"A{i}: {section_a.get('section_type', 'unknown')} - "
                    f"role={role_a} (density={section_a.get('vocal_density', 'unknown')})"
                )

                mashup_parts.append(processed_a)

            # Process section from song B
            if section_b:
                role_b = assign_role(section_b)
                start_sample_b = int(section_b["start_sec"] * sr_b)
                end_sample_b = int(section_b["end_sec"] * sr_b)
                vocal_section_b = vocals_b_stretched[start_sample_b:end_sample_b]
                inst_section_b = inst_b_stretched[start_sample_b:end_sample_b]

                # Process based on role
                processed_b = _process_vocal_by_role(
                    vocal_section_b,
                    inst_section_b,
                    role_b,
                    sr_b
                )

                logger.info(
                    f"B{i}: {section_b.get('section_type', 'unknown')} - "
                    f"role={role_b} (density={section_b.get('vocal_density', 'unknown')})"
                )

                mashup_parts.append(processed_b)

        # Concatenate all role-processed sections
        logger.info("Concatenating role-aware sections...")
        final_audio = np.concatenate(mashup_parts)

        # Generate output path
        if output_path is None:
            output_dir = config.get_path("mashup_output")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(
                output_dir / f"role_aware_{song_a_id}_x_{song_b_id}.{output_format}"
            )

        # Export
        logger.info("Exporting role-aware mashup...")
        from mixer.audio.processing import numpy_to_audiosegment
        from pydub.effects import normalize

        mashup_seg = numpy_to_audiosegment(final_audio, target_sr)
        mashup_seg = normalize(mashup_seg, headroom=2.0)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Export
        if output_format == "mp3":
            mashup_seg.export(
                output_path,
                format="mp3",
                bitrate="320k",
                parameters=["-q:a", "0"]
            )
        elif output_format == "wav":
            mashup_seg.export(
                output_path,
                format="wav",
                parameters=["-ac", "2", "-ar", str(target_sr)]
            )
        else:
            raise MashupConfigError(f"Unsupported output format: {output_format}")

        logger.info(f"🎵 Role-aware mashup created: {output_path}")
        return output_path

    except (SongNotFoundError, ProcessingError) as e:
        raise
    except Exception as e:
        raise EngineerError(f"Role-aware mashup creation failed: {e}")


def _process_vocal_by_role(
    vocal_audio: np.ndarray,
    inst_audio: np.ndarray,
    role: str,
    sr: int
) -> np.ndarray:
    """
    Process vocal section based on assigned role.

    Args:
        vocal_audio: Vocal audio segment
        inst_audio: Instrumental audio segment
        role: Assigned role ("lead", "harmony", "call", "response", "texture")
        sr: Sample rate

    Returns:
        Processed audio with vocal and instrumental mixed
    """
    # Ensure both arrays are same length
    min_len = min(len(vocal_audio), len(inst_audio))
    vocal_audio = vocal_audio[:min_len]
    inst_audio = inst_audio[:min_len]

    if role == "lead":
        # Full volume vocals + full instrumental
        mixed = vocal_audio + inst_audio * 0.7

    elif role == "harmony":
        # Pitch-shifted +3 semitones, attenuated -6dB
        try:
            vocal_shifted = pitch_shift(vocal_audio, sr, n_steps=3)
            vocal_shifted = vocal_shifted[:min_len]  # Ensure same length
            mixed = vocal_shifted * 0.5 + inst_audio * 0.8  # -6dB ≈ 0.5x
        except Exception:
            # Fallback if pitch-shift fails
            mixed = vocal_audio * 0.5 + inst_audio * 0.8

    elif role == "call":
        # Vocal + short silence after (0.3s)
        silence_samples = int(0.3 * sr)
        silence = np.zeros(silence_samples, dtype=np.float32)
        mixed = vocal_audio * 1.0 + inst_audio * 0.6
        mixed = np.concatenate([mixed, silence])

    elif role == "response":
        # Short silence before (0.2s) + vocal
        silence_samples = int(0.2 * sr)
        silence = np.zeros(silence_samples, dtype=np.float32)
        mixed = vocal_audio * 1.0 + inst_audio * 0.6
        mixed = np.concatenate([silence, mixed])

    elif role == "texture":
        # Heavily attenuated, rhythmic texture
        mixed = vocal_audio * 0.3 + inst_audio * 0.9

    else:
        # Default: balanced mix
        mixed = vocal_audio * 0.7 + inst_audio * 0.8

    # Normalize to prevent clipping
    max_val = np.abs(mixed).max()
    if max_val > 0:
        mixed = mixed / max_val * 0.95

    return mixed


def create_conversational_mashup(
    song_a_id: str,
    song_b_id: str,
    output_path: Optional[str] = None,
    quality: Optional[QualityPreset] = None,
    output_format: Optional[OutputFormat] = None,
    silence_duration_sec: float = 0.4
) -> str:
    """
    Create conversational mashup: Songs talk to each other like a dialogue.

    Detects question/answer patterns and statement/response pairs from section
    metadata and arranges them with silence gaps to create realistic conversational
    flow. Creates the effect of two singers having a dialogue.

    Args:
        song_a_id: First song ID (typically asks questions or makes statements)
        song_b_id: Second song ID (typically answers or responds)
        output_path: Output file path (auto-generated if None)
        quality: "draft" | "high" | "broadcast" (from config if None)
        output_format: "mp3" | "wav" (from config if None)
        silence_duration_sec: Duration of silence between conversational turns (default: 0.4s)

    Returns:
        Absolute path to exported mashup

    Raises:
        SongNotFoundError: If either song not found
        EngineerError: If songs lack section metadata or no conversational pairs found
    """
    config = get_config()

    if quality is None:
        quality = config.get("engineer.default_quality", "high")
    if output_format is None:
        output_format = "mp3"

    logger.info(f"=== Creating Conversational Mashup ===")
    logger.info(f"Song A: {song_a_id}")
    logger.info(f"Song B: {song_b_id}")
    logger.info(f"Silence gap: {silence_duration_sec}s")

    try:
        # Load songs
        audio_a, meta_a = _load_song_audio(song_a_id)
        audio_b, meta_b = _load_song_audio(song_b_id)

        # Check for section metadata
        sections_a = meta_a.get("sections", [])
        sections_b = meta_b.get("sections", [])

        if not sections_a or not sections_b:
            raise EngineerError(
                "Songs must have section-level metadata. Run analyst agent first."
            )

        sr_a = meta_a.get("sample_rate", 44100)
        sr_b = meta_b.get("sample_rate", 44100)

        # Separate vocals from both songs
        logger.info("Separating vocal stems...")
        stems_a = separate_stems(
            meta_a["path"],
            model_name=config.get("models.demucs_model", "htdemucs"),
            device=None
        )
        stems_b = separate_stems(
            meta_b["path"],
            model_name=config.get("models.demucs_model", "htdemucs"),
            device=None
        )

        vocals_a = stems_a["vocals"]
        vocals_b = stems_b["vocals"]

        # Create instrumental bed (blend both instrumentals)
        inst_a = combine_stems(stems_a, exclude=["vocals"])
        inst_b = combine_stems(stems_b, exclude=["vocals"])

        # Time-stretch song B to match song A's BPM
        bpm_a = meta_a.get("bpm")
        bpm_b = meta_b.get("bpm")

        if not bpm_a or not bpm_b:
            raise EngineerError("Songs must have BPM metadata")

        stretch_ratio = _calculate_stretch_ratio(bpm_b, bpm_a)
        vocals_b_stretched = time_stretch(vocals_b, sr_b, stretch_ratio, quality)
        inst_b_stretched = time_stretch(inst_b, sr_b, stretch_ratio, quality)

        # Define conversational pairings
        conversational_pairs = {
            "question": ["answer", "reflection"],
            "narrative": ["answer", "reflection", "narrative"],
            "call": ["response"],
            "hook": [],  # Hooks don't pair conversationally
        }

        # Build conversational dialogue
        logger.info("Building conversational structure...")
        dialogue_parts = []
        instrumental_parts = []
        used_b_indices = set()
        silence_samples = int(silence_duration_sec * sr_a)
        silence = np.zeros(silence_samples, dtype=np.float32)

        for i, section_a in enumerate(sections_a):
            func_a = section_a.get("lyrical_function", "")

            # Extract vocal section from A
            start_sample_a = int(section_a["start_sec"] * sr_a)
            end_sample_a = int(section_a["end_sec"] * sr_a)
            vocal_section_a = vocals_a[start_sample_a:end_sample_a]
            inst_section_a = inst_a[start_sample_a:end_sample_a]

            logger.info(
                f"A{i}: {section_a.get('section_type', 'unknown')} - "
                f"{func_a} \"{section_a.get('emotional_tone', 'unknown')}\""
            )

            # Add section A
            dialogue_parts.append(vocal_section_a)
            instrumental_parts.append(inst_section_a)

            # Find conversational response from song B
            target_funcs = conversational_pairs.get(func_a, [])

            if target_funcs:
                # Add "listening" silence
                dialogue_parts.append(np.zeros_like(silence))
                instrumental_parts.append(silence)

                # Find best match from song B
                best_match = None
                for j, section_b in enumerate(sections_b):
                    if j in used_b_indices:
                        continue

                    func_b = section_b.get("lyrical_function", "")
                    if func_b in target_funcs:
                        best_match = (j, section_b)
                        break

                if best_match:
                    j, section_b = best_match
                    used_b_indices.add(j)

                    # Extract vocal section from B
                    start_sample_b = int(section_b["start_sec"] * sr_b)
                    end_sample_b = int(section_b["end_sec"] * sr_b)
                    vocal_section_b = vocals_b_stretched[start_sample_b:end_sample_b]
                    inst_section_b = inst_b_stretched[start_sample_b:end_sample_b]

                    logger.info(
                        f"  → B{j}: {section_b.get('section_type', 'unknown')} - "
                        f"{func_b} \"{section_b.get('emotional_tone', 'unknown')}\" [PAIRED]"
                    )

                    # Add section B
                    dialogue_parts.append(vocal_section_b)
                    instrumental_parts.append(inst_section_b)

                    # Add silence after response
                    dialogue_parts.append(np.zeros_like(silence))
                    instrumental_parts.append(silence)

        if len(dialogue_parts) <= len(sections_a):
            logger.warning(
                "No conversational pairs found - mashup will be mostly song A. "
                "Consider songs with complementary lyrical functions."
            )

        # Mix vocals with instrumental bed
        logger.info("Mixing vocals with instrumental bed...")
        final_parts = []

        for vocal_part, inst_part in zip(dialogue_parts, instrumental_parts):
            # Ensure same length
            min_len = min(len(vocal_part), len(inst_part))
            vocal_trimmed = vocal_part[:min_len]
            inst_trimmed = inst_part[:min_len]

            # Mix: vocals prominent, instrumental as bed
            mixed_part = vocal_trimmed * 1.0 + inst_trimmed * 0.4
            final_parts.append(mixed_part)

        # Concatenate all dialogue sections
        logger.info("Concatenating conversational sections...")
        final_audio = np.concatenate(final_parts)

        # Generate output path
        if output_path is None:
            output_dir = config.get_path("mashup_output")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(
                output_dir / f"conversational_{song_a_id}_x_{song_b_id}.{output_format}"
            )

        # Export
        logger.info("Exporting conversational mashup...")
        from mixer.audio.processing import numpy_to_audiosegment
        from pydub.effects import normalize

        mashup_seg = numpy_to_audiosegment(final_audio, sr_a)
        mashup_seg = normalize(mashup_seg, headroom=2.0)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Export
        if output_format == "mp3":
            mashup_seg.export(
                output_path,
                format="mp3",
                bitrate="320k",
                parameters=["-q:a", "0"]
            )
        elif output_format == "wav":
            mashup_seg.export(
                output_path,
                format="wav",
                parameters=["-ac", "2", "-ar", str(sr_a)]
            )
        else:
            raise MashupConfigError(f"Unsupported output format: {output_format}")

        pairs_found = len([p for p in dialogue_parts if len(p) > 0]) - len(sections_a)
        logger.info(f"🎵 Conversational mashup created: {output_path}")
        logger.info(f"   Conversational pairs: {pairs_found // 2}")
        return output_path

    except (SongNotFoundError, ProcessingError) as e:
        raise
    except Exception as e:
        raise EngineerError(f"Conversational mashup creation failed: {e}")
