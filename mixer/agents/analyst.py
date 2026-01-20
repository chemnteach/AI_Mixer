"""Analyst Agent - Extracts comprehensive metadata from audio files."""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import numpy as np
import librosa
import whisper

from mixer.config import get_config
from mixer.memory import upsert_song
from mixer.types import SongMetadata, SectionMetadata
from mixer.audio.analysis import (
    detect_sections,
    classify_section_type,
    analyze_section_energy,
    estimate_key,
    key_to_camelot,
)
from mixer.llm.semantic import (
    analyze_song_semantics,
    analyze_section_semantics,
    generate_emotional_arc,
)


logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Base exception for analysis errors."""
    pass


def profile_audio(file_path: str, song_id: str, artist: str, title: str) -> Dict:
    """
    Analyze audio file and extract comprehensive metadata.

    Phase 3A Enhanced: Includes section-level analysis for advanced mashups.

    Args:
        file_path: Absolute path to WAV file
        song_id: Unique identifier
        artist: Artist name
        title: Song title

    Returns:
        Complete metadata dict with sections
    """
    logger.info(f"Profiling audio: {artist} - {title}")

    config = get_config()

    try:
        # Step 1: Load audio
        logger.info("Loading audio file...")
        y, sr = librosa.load(file_path, sr=44100, mono=False)

        # Convert to mono for analysis
        if y.ndim > 1:
            y_mono = librosa.to_mono(y)
        else:
            y_mono = y

        # Step 2: Basic signal analysis
        logger.info("Running signal analysis...")
        basic_metadata = _analyze_signal(y_mono, sr)

        # Step 3: Transcription (Whisper)
        logger.info("Transcribing audio...")
        transcript_data = _transcribe_audio(file_path, config)

        # Step 4: Section detection
        logger.info("Detecting sections...")
        section_boundaries = detect_sections(y_mono, sr)

        # Step 5: Analyze each section
        logger.info(f"Analyzing {len(section_boundaries)} sections...")
        sections = _analyze_sections(
            y_mono,
            sr,
            section_boundaries,
            transcript_data
        )

        # Step 6: Song-level semantic analysis
        logger.info("Running semantic analysis...")
        semantic_metadata = analyze_song_semantics(
            transcript_data['transcript'],
            basic_metadata['bpm'],
            basic_metadata['key'],
            basic_metadata['energy_level'],
            provider=config.get("llm.primary_provider", "anthropic")
        )

        # Step 7: Generate emotional arc
        emotional_arc = generate_emotional_arc(sections)

        # Step 8: Combine all metadata
        metadata = SongMetadata(
            source="local_file",  # Will be updated by caller if YouTube
            path=file_path,
            bpm=basic_metadata['bpm'],
            key=basic_metadata['key'],
            camelot=basic_metadata['camelot'],
            genres=semantic_metadata['genres'],
            primary_genre=semantic_metadata['primary_genre'],
            irony_score=semantic_metadata['irony_score'],
            mood_summary=semantic_metadata['mood_summary'],
            energy_level=int(basic_metadata['energy_level'] * 10),  # 0-10 scale
            valence=semantic_metadata['valence'],
            first_downbeat_sec=basic_metadata['first_downbeat_sec'],
            duration_sec=basic_metadata['duration_sec'],
            sample_rate=sr,
            has_vocals=transcript_data['has_vocals'],
            artist=artist,
            title=title,
            date_added=datetime.utcnow().isoformat(),
            # Phase 3A additions
            sections=sections,
            emotional_arc=emotional_arc,
            # Phase 3E additions
            word_timings=transcript_data.get('word_timings', [])
        )

        # Step 9: Store in ChromaDB
        logger.info("Storing in ChromaDB...")
        document = f"{transcript_data['transcript']}\n\n[MOOD]: {semantic_metadata['mood_summary']}"

        upsert_song(
            artist=artist,
            title=title,
            metadata=metadata,
            transcript=document
        )

        logger.info("✅ Profile complete")

        return {
            "status": "success",
            "song_id": song_id,
            "metadata": metadata
        }

    except Exception as e:
        logger.error(f"Profile failed: {e}", exc_info=True)
        raise AnalysisError(f"Analysis failed for {song_id}: {e}")


def _analyze_signal(y: np.ndarray, sr: int) -> Dict:
    """
    Run basic signal analysis (BPM, key, energy, etc.).

    Args:
        y: Audio time series
        sr: Sample rate

    Returns:
        Dict with basic metadata
    """
    # BPM Detection
    try:
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo)

        # First downbeat
        if len(beats) > 0:
            first_downbeat_sec = float(librosa.frames_to_time(beats[0], sr=sr))
        else:
            first_downbeat_sec = 0.0
    except Exception as e:
        logger.warning(f"BPM detection failed: {e}")
        bpm = None
        first_downbeat_sec = 0.0

    # Key Detection
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        key = estimate_key(chroma)
        camelot = key_to_camelot(key)
    except Exception as e:
        logger.warning(f"Key detection failed: {e}")
        key = "Unknown"
        camelot = "Unknown"

    # Energy Level (RMS)
    try:
        rms = librosa.feature.rms(y=y)
        energy_level = float(np.mean(rms))
    except Exception as e:
        logger.warning(f"Energy calculation failed: {e}")
        energy_level = 0.5

    # Duration
    duration_sec = float(librosa.get_duration(y=y, sr=sr))

    return {
        "bpm": bpm,
        "key": key,
        "camelot": camelot,
        "energy_level": energy_level,
        "first_downbeat_sec": first_downbeat_sec,
        "duration_sec": duration_sec
    }


def _transcribe_audio(file_path: str, config) -> Dict:
    """
    Transcribe audio using Whisper.

    Args:
        file_path: Path to audio file
        config: Configuration object

    Returns:
        Dict with transcript, has_vocals, word_timings
    """
    try:
        model_size = config.get("models.whisper_size", "base")
        logger.info(f"Loading Whisper model: {model_size}")

        model = whisper.load_model(model_size)

        result = model.transcribe(
            file_path,
            word_timestamps=True,  # For future lyric sync
            language="en"
        )

        transcript = result['text'].strip()
        word_timings = result.get('segments', [])

        # Vocal detection heuristic
        has_vocals = len(transcript.split()) > 50

        logger.info(f"Transcription: {len(transcript)} chars, has_vocals={has_vocals}")

        return {
            "transcript": transcript,
            "has_vocals": has_vocals,
            "word_timings": word_timings
        }

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {
            "transcript": "",
            "has_vocals": False,
            "word_timings": []
        }


def _analyze_sections(
    y: np.ndarray,
    sr: int,
    section_boundaries: List[tuple],
    transcript_data: Dict
) -> List[SectionMetadata]:
    """
    Analyze each section for energy, vocals, and semantics.

    Args:
        y: Audio time series
        sr: Sample rate
        section_boundaries: List of (start, end) tuples
        transcript_data: Transcript and word timings

    Returns:
        List of SectionMetadata dicts
    """
    sections = []
    transcript = transcript_data['transcript']
    word_timings = transcript_data['word_timings']

    for idx, (start, end) in enumerate(section_boundaries):
        # Energy analysis
        energy_data = analyze_section_energy(y, sr, start, end)

        # Classify section type
        section_type = classify_section_type(
            idx,
            len(section_boundaries),
            energy_data['energy_level'],
            energy_data['spectral_centroid']
        )

        # Extract lyrics for this section
        lyrical_content = _extract_section_lyrics(
            start, end, word_timings, transcript
        )

        # Vocal characteristics
        vocal_data = _analyze_section_vocals(y, sr, start, end, lyrical_content)

        # Semantic analysis (LLM)
        try:
            semantic_data = analyze_section_semantics(
                lyrical_content,
                section_type,
                energy_data['energy_level']
            )
        except Exception as e:
            logger.warning(f"Section semantic analysis failed: {e}")
            semantic_data = {
                "emotional_tone": "neutral",
                "lyrical_function": "narrative",
                "themes": []
            }

        # Build SectionMetadata
        section_metadata = SectionMetadata(
            section_type=section_type,
            start_sec=start,
            end_sec=end,
            duration_sec=end - start,
            energy_level=energy_data['energy_level'],
            spectral_centroid=energy_data['spectral_centroid'],
            tempo_stability=energy_data['tempo_stability'],
            vocal_density=vocal_data['vocal_density'],
            vocal_intensity=vocal_data['vocal_intensity'],
            lyrical_content=lyrical_content,
            emotional_tone=semantic_data['emotional_tone'],
            lyrical_function=semantic_data['lyrical_function'],
            themes=semantic_data['themes']
        )

        sections.append(section_metadata)

    return sections


def _extract_section_lyrics(
    start_sec: float,
    end_sec: float,
    word_timings: List[Dict],
    full_transcript: str
) -> str:
    """
    Extract lyrics for a specific section based on word timings.

    Args:
        start_sec: Section start time
        end_sec: Section end time
        word_timings: Whisper word timing segments
        full_transcript: Full transcript (fallback)

    Returns:
        Lyrics for this section
    """
    if not word_timings:
        # Fallback: split transcript into equal chunks
        return ""

    # Extract words within this section's time range
    section_words = []

    for segment in word_timings:
        segment_start = segment.get('start', 0)
        segment_end = segment.get('end', 0)

        # Check if segment overlaps with this section
        if segment_start < end_sec and segment_end > start_sec:
            section_words.append(segment.get('text', '').strip())

    return ' '.join(section_words)


def _analyze_section_vocals(
    y: np.ndarray,
    sr: int,
    start_sec: float,
    end_sec: float,
    lyrical_content: str
) -> Dict:
    """
    Analyze vocal characteristics for a section.

    Args:
        y: Audio time series
        sr: Sample rate
        start_sec: Section start
        end_sec: Section end
        lyrical_content: Lyrics for this section

    Returns:
        Dict with vocal_density and vocal_intensity
    """
    # Extract section audio
    start_sample = int(start_sec * sr)
    end_sample = int(end_sec * sr)
    section_audio = y[start_sample:end_sample]

    if len(section_audio) == 0:
        return {"vocal_density": "sparse", "vocal_intensity": 0.0}

    # Vocal intensity (RMS energy of section)
    rms = librosa.feature.rms(y=section_audio)
    vocal_intensity = float(np.mean(rms))

    # Vocal density (based on lyric word count)
    word_count = len(lyrical_content.split())
    section_duration = end_sec - start_sec

    if section_duration > 0:
        words_per_second = word_count / section_duration

        if words_per_second > 3:
            vocal_density = "dense"
        elif words_per_second > 1:
            vocal_density = "medium"
        else:
            vocal_density = "sparse"
    else:
        vocal_density = "sparse"

    return {
        "vocal_density": vocal_density,
        "vocal_intensity": vocal_intensity
    }
