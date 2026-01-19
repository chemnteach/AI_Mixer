"""Audio signal analysis - section detection, energy, spectral features."""

import logging
from typing import List, Tuple
import numpy as np
import librosa


logger = logging.getLogger(__name__)


def detect_sections(
    y: np.ndarray,
    sr: int,
    n_segments: int = 8
) -> List[Tuple[float, float]]:
    """
    Detect section boundaries in audio using spectral clustering.

    Uses librosa's agglomerative segmentation to find natural breakpoints
    in the audio based on spectral similarity.

    Args:
        y: Audio time series
        sr: Sample rate
        n_segments: Target number of segments (will be adjusted based on duration)

    Returns:
        List of (start_sec, end_sec) tuples for each section
    """
    try:
        # Adjust n_segments based on duration
        duration = librosa.get_duration(y=y, sr=sr)

        # Use 1 segment per ~20 seconds of audio (minimum 4, maximum 16)
        adjusted_segments = max(4, min(16, int(duration / 20)))

        logger.info(
            f"Detecting sections: duration={duration:.1f}s, "
            f"target_segments={adjusted_segments}"
        )

        # Compute chroma features for segmentation
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

        # Agglomerative clustering to find section boundaries
        boundaries = librosa.segment.agglomerative(
            chroma,
            adjusted_segments
        )

        # Convert frame indices to timestamps
        boundary_times = librosa.frames_to_time(boundaries, sr=sr)

        # Create (start, end) tuples
        sections = []
        for i in range(len(boundary_times) - 1):
            start = float(boundary_times[i])
            end = float(boundary_times[i + 1])
            sections.append((start, end))

        logger.info(f"Detected {len(sections)} sections")
        return sections

    except Exception as e:
        logger.error(f"Section detection failed: {e}")
        # Fallback: divide into 8-second chunks
        duration = librosa.get_duration(y=y, sr=sr)
        n_chunks = max(1, int(duration / 8))
        chunk_duration = duration / n_chunks

        sections = []
        for i in range(n_chunks):
            start = i * chunk_duration
            end = min((i + 1) * chunk_duration, duration)
            sections.append((start, end))

        logger.warning(f"Using fallback: {len(sections)} equal chunks")
        return sections


def classify_section_type(
    section_idx: int,
    total_sections: int,
    energy_level: float,
    spectral_centroid: float
) -> str:
    """
    Classify section type based on position and audio features.

    Simple heuristic-based classification:
    - First section: usually intro
    - Last section: usually outro
    - High energy + high spectral centroid: likely chorus
    - Medium energy: likely verse
    - Low energy or sparse: likely bridge

    Args:
        section_idx: Index of this section (0-based)
        total_sections: Total number of sections
        energy_level: RMS energy (0.0-1.0)
        spectral_centroid: Brightness metric (Hz)

    Returns:
        Section type: "intro" | "verse" | "chorus" | "bridge" | "outro"
    """
    # First section is usually intro
    if section_idx == 0:
        return "intro"

    # Last section is usually outro
    if section_idx == total_sections - 1:
        return "outro"

    # Use energy and spectral features for middle sections
    # These thresholds are heuristic and could be tuned
    if energy_level > 0.6 and spectral_centroid > 2000:
        return "chorus"  # High energy + bright = chorus
    elif energy_level < 0.3:
        return "bridge"  # Low energy = bridge/breakdown
    else:
        return "verse"  # Medium energy = verse


def analyze_section_energy(
    y: np.ndarray,
    sr: int,
    start_sec: float,
    end_sec: float
) -> dict:
    """
    Analyze energy characteristics for a specific section.

    Args:
        y: Full audio time series
        sr: Sample rate
        start_sec: Section start time
        end_sec: Section end time

    Returns:
        Dict with energy_level, spectral_centroid, tempo_stability
    """
    # Extract section audio
    start_sample = int(start_sec * sr)
    end_sample = int(end_sec * sr)
    section_audio = y[start_sample:end_sample]

    if len(section_audio) == 0:
        logger.warning(f"Empty section ({start_sec:.1f}s-{end_sec:.1f}s)")
        return {
            "energy_level": 0.0,
            "spectral_centroid": 0.0,
            "tempo_stability": 0.0
        }

    try:
        # RMS Energy (normalized to 0-1)
        rms = librosa.feature.rms(y=section_audio)[0]
        energy_level = float(np.mean(rms))

        # Spectral Centroid (brightness)
        centroid = librosa.feature.spectral_centroid(y=section_audio, sr=sr)[0]
        spectral_centroid = float(np.mean(centroid))

        # Tempo Stability (variance of beat intervals)
        try:
            tempo, beats = librosa.beat.beat_track(y=section_audio, sr=sr)

            if len(beats) > 1:
                beat_times = librosa.frames_to_time(beats, sr=sr)
                beat_intervals = np.diff(beat_times)
                tempo_variance = np.var(beat_intervals)

                # Convert variance to stability (0=unstable, 1=very stable)
                # Lower variance = higher stability
                tempo_stability = float(np.exp(-tempo_variance * 10))
            else:
                tempo_stability = 0.0  # Not enough beats to measure

        except Exception as e:
            logger.debug(f"Tempo stability calculation failed: {e}")
            tempo_stability = 0.5  # Neutral default

        return {
            "energy_level": energy_level,
            "spectral_centroid": spectral_centroid,
            "tempo_stability": tempo_stability
        }

    except Exception as e:
        logger.error(f"Energy analysis failed for section: {e}")
        return {
            "energy_level": 0.0,
            "spectral_centroid": 0.0,
            "tempo_stability": 0.0
        }


def estimate_key(chroma: np.ndarray) -> str:
    """
    Estimate musical key from chroma features.

    Uses template matching against major/minor key profiles.

    Args:
        chroma: Chroma features (12 x n_frames)

    Returns:
        Key string like "Cmaj", "Amin", "F#maj", etc.
    """
    # Average chroma across time
    chroma_mean = np.mean(chroma, axis=1)

    # Normalize
    chroma_mean = chroma_mean / np.sum(chroma_mean)

    # Major and minor key profiles (Krumhansl-Schmuckler)
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                              2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                              2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    # Normalize profiles
    major_profile = major_profile / np.sum(major_profile)
    minor_profile = minor_profile / np.sum(minor_profile)

    # Pitch class names
    pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F',
                     'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Test all rotations
    best_correlation = -1
    best_key = "Unknown"

    for shift in range(12):
        # Rotate chroma to test different tonics
        rotated_chroma = np.roll(chroma_mean, shift)

        # Correlate with major
        corr_major = np.corrcoef(rotated_chroma, major_profile)[0, 1]
        if corr_major > best_correlation:
            best_correlation = corr_major
            best_key = f"{pitch_classes[shift]}maj"

        # Correlate with minor
        corr_minor = np.corrcoef(rotated_chroma, minor_profile)[0, 1]
        if corr_minor > best_correlation:
            best_correlation = corr_minor
            best_key = f"{pitch_classes[shift]}min"

    return best_key


def key_to_camelot(key: str) -> str:
    """
    Convert musical key to Camelot wheel notation.

    Args:
        key: Key string like "Cmaj", "Amin", "F#maj"

    Returns:
        Camelot notation like "8B", "5A", etc.
    """
    camelot_map = {
        # Major keys (B = outer wheel)
        "Cmaj": "8B", "Gmaj": "9B", "Dmaj": "10B", "Amaj": "11B",
        "Emaj": "12B", "Bmaj": "1B", "F#maj": "2B", "C#maj": "3B",
        "G#maj": "4B", "D#maj": "5B", "A#maj": "6B", "Fmaj": "7B",

        # Minor keys (A = inner wheel)
        "Amin": "8A", "Emin": "9A", "Bmin": "10A", "F#min": "11A",
        "C#min": "12A", "G#min": "1A", "D#min": "2A", "A#min": "3A",
        "Fmin": "4A", "Cmin": "5A", "Gmin": "6A", "Dmin": "7A"
    }

    return camelot_map.get(key, "Unknown")
