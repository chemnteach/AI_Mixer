"""Audio processing - stem separation, time-stretching, alignment, mixing."""

import logging
import os
from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import torch
import pyrubberband as pyrb
from pydub import AudioSegment
from pydub.effects import normalize

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Base exception for audio processing errors."""
    pass


def separate_stems(
    audio_path: str,
    model_name: str = "htdemucs",
    device: str = None
) -> Dict[str, np.ndarray]:
    """
    Separate audio into stems using Demucs.

    Args:
        audio_path: Path to audio file
        model_name: Demucs model ("mdx" | "htdemucs" | "htdemucs_ft")
        device: "cuda" or "cpu" (auto-detects if None)

    Returns:
        Dict with keys: "vocals", "drums", "bass", "other"
        Each value is a numpy array (samples,)
    """
    try:
        from demucs.pretrained import get_model
        from demucs.apply import apply_model
        from demucs.audio import convert_audio
        import torchaudio

        logger.info(f"Loading Demucs model: {model_name}")

        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Using device: {device}")

        # Load model
        model = get_model(model_name)
        model.to(device)

        # Load audio
        logger.info(f"Loading audio: {audio_path}")
        wav, sr = torchaudio.load(audio_path)

        # Convert to model's expected format
        wav = convert_audio(wav, sr, model.samplerate, model.audio_channels)
        wav = wav.to(device)

        # Apply model
        logger.info("Separating stems...")
        with torch.no_grad():
            stems = apply_model(model, wav[None], device=device)[0]

        # Convert to numpy (mono for simplicity)
        stems_dict = {}
        source_names = model.sources  # ["drums", "bass", "other", "vocals"]

        for i, name in enumerate(source_names):
            # Get stem tensor
            stem = stems[i]

            # Convert to mono if stereo
            if stem.shape[0] > 1:
                stem = stem.mean(dim=0)

            # Convert to numpy
            stem_np = stem.cpu().numpy()
            stems_dict[name] = stem_np

        logger.info(f"✅ Stems separated: {list(stems_dict.keys())}")
        return stems_dict

    except ImportError as e:
        raise ProcessingError(
            f"Demucs not installed or dependencies missing: {e}. "
            "Install with: pip install demucs"
        )
    except Exception as e:
        raise ProcessingError(f"Stem separation failed: {e}")


def time_stretch(
    audio: np.ndarray,
    sr: int,
    stretch_ratio: float,
    quality: str = "high"
) -> np.ndarray:
    """
    Time-stretch audio (pitch-preserving).

    Args:
        audio: Audio array
        sr: Sample rate
        stretch_ratio: Rate multiplier (e.g., 1.2 = 20% faster)
        quality: "draft" | "high" | "broadcast"

    Returns:
        Time-stretched audio array
    """
    # Validate stretch ratio
    if not (0.7 <= stretch_ratio <= 1.3):
        logger.warning(
            f"Extreme stretch ratio: {stretch_ratio:.2f}. "
            "Quality may degrade significantly."
        )
        if stretch_ratio > 2.0 or stretch_ratio < 0.5:
            raise ProcessingError(
                f"Stretch ratio {stretch_ratio:.2f} is out of acceptable bounds (0.5-2.0)"
            )

    logger.info(f"Time-stretching: ratio={stretch_ratio:.2f}, quality={quality}")

    try:
        # Set rubberband args based on quality
        rbargs = {}
        if quality == "broadcast":
            rbargs = {'--fine': '', '--threads': '4'}
        elif quality == "high":
            rbargs = {'--fine': ''}
        # draft uses defaults

        stretched = pyrb.time_stretch(
            audio,
            sr,
            stretch_ratio,
            rbargs=rbargs if rbargs else None
        )

        return stretched

    except Exception as e:
        raise ProcessingError(f"Time-stretching failed: {e}")


def align_to_grid(
    vocals: np.ndarray,
    instrumental: np.ndarray,
    vocal_downbeat_sec: float,
    inst_downbeat_sec: float,
    stretch_ratio: float,
    sr: int = 44100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align vocal and instrumental tracks by downbeat.

    Args:
        vocals: Vocal audio (after time-stretching)
        instrumental: Instrumental audio
        vocal_downbeat_sec: First downbeat in vocal (original time)
        inst_downbeat_sec: First downbeat in instrumental
        stretch_ratio: How much vocal was stretched
        sr: Sample rate

    Returns:
        (vocals_aligned, instrumental_aligned) tuple
    """
    logger.info("Aligning tracks to grid...")

    # Adjust vocal downbeat for time-stretching
    adjusted_vocal_downbeat = vocal_downbeat_sec * stretch_ratio

    # Calculate offset needed
    offset_sec = inst_downbeat_sec - adjusted_vocal_downbeat
    offset_samples = int(offset_sec * sr)

    logger.info(
        f"Offset: {offset_sec:.3f}s ({offset_samples} samples), "
        f"vocal_db={vocal_downbeat_sec:.2f}s, "
        f"inst_db={inst_downbeat_sec:.2f}s"
    )

    # Apply offset
    if offset_samples > 0:
        # Delay vocals (pad beginning with silence)
        vocals_aligned = np.pad(vocals, (offset_samples, 0), mode='constant')
    elif offset_samples < 0:
        # Advance vocals (trim beginning)
        vocals_aligned = vocals[abs(offset_samples):]
    else:
        vocals_aligned = vocals

    # Match lengths
    min_length = min(len(instrumental), len(vocals_aligned))
    vocals_final = vocals_aligned[:min_length]
    instrumental_final = instrumental[:min_length]

    # Handle length mismatch (fade out if vocal is significantly shorter)
    if len(vocals_aligned) < len(instrumental) * 0.8:
        logger.warning("Vocal track significantly shorter than instrumental. Applying fadeout.")

        fade_duration_sec = 4.0
        fade_start = int(len(vocals_final) * 0.8)
        fade_length = int(fade_duration_sec * sr)

        # Apply linear fadeout
        fade_end = min(fade_start + fade_length, len(vocals_final))
        fade_curve = np.linspace(1.0, 0.0, fade_end - fade_start)
        vocals_final[fade_start:fade_end] *= fade_curve

    logger.info(f"✅ Tracks aligned: {min_length / sr:.1f}s")

    return vocals_final, instrumental_final


def numpy_to_audiosegment(
    audio: np.ndarray,
    sr: int
) -> AudioSegment:
    """
    Convert numpy array to pydub AudioSegment.

    Args:
        audio: Audio array (mono or stereo)
        sr: Sample rate

    Returns:
        pydub AudioSegment
    """
    # Ensure audio is in int16 format
    if audio.dtype != np.int16:
        audio = (audio * 32767).astype(np.int16)

    # Convert to bytes
    audio_bytes = audio.tobytes()

    # Create AudioSegment
    segment = AudioSegment(
        audio_bytes,
        frame_rate=sr,
        sample_width=2,  # 16-bit = 2 bytes
        channels=1  # Mono
    )

    return segment


def mix_and_export(
    vocals: np.ndarray,
    instrumental: np.ndarray,
    output_path: str,
    sr: int = 44100,
    output_format: str = "mp3",
    vocal_attenuation_db: float = -2.0
) -> str:
    """
    Mix vocal and instrumental tracks and export to file.

    Args:
        vocals: Vocal audio array
        instrumental: Instrumental audio array
        output_path: Output file path
        sr: Sample rate
        output_format: "mp3" or "wav"
        vocal_attenuation_db: How much quieter to make vocals (negative = quieter)

    Returns:
        Absolute path to exported file
    """
    logger.info("Mixing tracks...")

    # Convert to AudioSegment
    vocals_seg = numpy_to_audiosegment(vocals, sr)
    inst_seg = numpy_to_audiosegment(instrumental, sr)

    # Normalize levels
    logger.info("Normalizing levels...")
    vocals_seg = normalize(vocals_seg, headroom=2.0)
    inst_seg = normalize(inst_seg, headroom=2.0)

    # Adjust relative volume
    vocals_seg = vocals_seg + vocal_attenuation_db

    logger.info(f"Vocal attenuation: {vocal_attenuation_db:.1f} dB")

    # Overlay (mix)
    mashup = inst_seg.overlay(vocals_seg)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export
    logger.info(f"Exporting to {output_format}...")

    try:
        if output_format == "mp3":
            mashup.export(
                output_path,
                format="mp3",
                bitrate="320k",
                parameters=["-q:a", "0"]  # Highest quality
            )
        elif output_format == "wav":
            mashup.export(
                output_path,
                format="wav",
                parameters=["-ac", "2", "-ar", str(sr)]
            )
        else:
            raise ProcessingError(f"Unsupported output format: {output_format}")

        logger.info(f"✅ Mashup exported: {output_path}")
        return os.path.abspath(output_path)

    except Exception as e:
        raise ProcessingError(f"Export failed: {e}")


def combine_stems(
    stem_dict: Dict[str, np.ndarray],
    exclude: list = None
) -> np.ndarray:
    """
    Combine multiple stems into a single audio track.

    Args:
        stem_dict: Dict of stem_name -> audio_array
        exclude: List of stem names to exclude (e.g., ["vocals"])

    Returns:
        Combined audio array
    """
    if exclude is None:
        exclude = []

    logger.info(f"Combining stems (excluding: {exclude})...")

    combined = None

    for name, audio in stem_dict.items():
        if name in exclude:
            continue

        if combined is None:
            combined = audio.copy()
        else:
            # Match lengths
            min_len = min(len(combined), len(audio))
            combined = combined[:min_len] + audio[:min_len]

    if combined is None:
        raise ProcessingError("No stems to combine")

    return combined


def pitch_shift(
    audio: np.ndarray,
    sr: int,
    semitones: float
) -> np.ndarray:
    """
    Pitch-shift audio by a given number of semitones.

    Args:
        audio: Audio array
        sr: Sample rate
        semitones: Number of semitones to shift (positive = higher, negative = lower)

    Returns:
        Pitch-shifted audio array
    """
    if semitones == 0:
        return audio

    logger.info(f"Pitch-shifting by {semitones:+.1f} semitones")

    try:
        import librosa

        shifted = librosa.effects.pitch_shift(
            y=audio,
            sr=sr,
            n_steps=semitones
        )

        return shifted

    except Exception as e:
        raise ProcessingError(f"Pitch-shifting failed: {e}")


def calculate_semitone_shift(source_key: str, target_key: str) -> int:
    """
    Calculate semitone shift needed to transpose from source key to target key.

    Args:
        source_key: Source musical key (e.g., "Cmaj", "Amin", "C major", "A minor")
        target_key: Target musical key

    Returns:
        Number of semitones to shift (positive = up, negative = down)

    Raises:
        ProcessingError: If keys are invalid or unrecognized
    """
    # Normalize key names
    def normalize_key(key: str) -> str:
        """Convert various key formats to standard format."""
        key = key.strip()

        # Handle "C major" -> "Cmaj", "A minor" -> "Amin"
        key = key.replace(" major", "maj").replace(" minor", "min")
        key = key.replace("Major", "maj").replace("Minor", "min")

        # Handle "CM" -> "Cmaj", "Am" -> "Amin"
        if len(key) >= 2:
            if key[-1] == 'M' and key[-2] != 'm':
                key = key[:-1] + "maj"
            elif key[-1] == 'm' and (len(key) == 2 or key[-2] in ['#', 'b']):
                key = key + "in"

        return key

    source_key = normalize_key(source_key)
    target_key = normalize_key(target_key)

    # Chromatic scale (semitone positions)
    note_to_semitone = {
        'C': 0, 'C#': 1, 'Db': 1,
        'D': 2, 'D#': 3, 'Eb': 3,
        'E': 4,
        'F': 5, 'F#': 6, 'Gb': 6,
        'G': 7, 'G#': 8, 'Ab': 8,
        'A': 9, 'A#': 10, 'Bb': 10,
        'B': 11
    }

    def extract_root(key: str) -> str:
        """Extract root note from key string."""
        # Handle sharp/flat (e.g., "C#maj", "Bbmin")
        if len(key) >= 2 and key[1] in ['#', 'b']:
            return key[:2]
        return key[0]

    try:
        source_root = extract_root(source_key)
        target_root = extract_root(target_key)

        source_semitone = note_to_semitone[source_root]
        target_semitone = note_to_semitone[target_root]

        # Calculate shift (shortest path on chromatic circle)
        shift = target_semitone - source_semitone

        # Normalize to [-6, 6] range (shortest path)
        if shift > 6:
            shift -= 12
        elif shift < -6:
            shift += 12

        logger.info(f"Key shift: {source_key} → {target_key} = {shift:+d} semitones")
        return shift

    except KeyError as e:
        raise ProcessingError(f"Invalid key: {e}. Use format like 'Cmaj', 'Amin', 'F#maj'")
    except Exception as e:
        raise ProcessingError(f"Key calculation failed: {e}")
