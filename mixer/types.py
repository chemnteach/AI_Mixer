"""Type definitions for The Mixer."""

from typing import TypedDict, Literal, Optional, List, Dict
from datetime import datetime
from enum import Enum


# Configuration Types
class PathConfig(TypedDict):
    """Path configuration."""
    library_cache: str
    mashup_output: str
    chroma_db: str
    failed_files: str


class AudioConfig(TypedDict):
    """Audio processing configuration."""
    sample_rate: int
    bit_depth: int
    channels: int
    default_format: str


class ModelConfig(TypedDict):
    """ML model configuration."""
    whisper_size: str
    demucs_model: str
    embedding_model: str


class LLMConfig(TypedDict):
    """LLM provider configuration."""
    primary_provider: str
    fallback_provider: str
    anthropic_model: str
    openai_model: str
    max_retries: int
    timeout: int


class CuratorConfig(TypedDict):
    """Curator agent configuration."""
    bpm_tolerance: float
    max_stretch_ratio: float
    default_match_criteria: str
    max_candidates: int


class EngineerConfig(TypedDict):
    """Engineer agent configuration."""
    default_quality: str
    vocal_attenuation_db: float
    fade_duration_sec: float
    normalize_lufs: int


class PerformanceConfig(TypedDict):
    """Performance settings."""
    max_concurrent_downloads: int
    enable_gpu: bool
    fallback_to_cpu: bool
    max_cache_size_gb: int


class LoggingConfig(TypedDict):
    """Logging configuration."""
    level: str
    file: str
    max_file_size_mb: int
    backup_count: int


class Config(TypedDict):
    """Complete system configuration."""
    paths: PathConfig
    audio: AudioConfig
    models: ModelConfig
    llm: LLMConfig
    curator: CuratorConfig
    engineer: EngineerConfig
    performance: PerformanceConfig
    logging: LoggingConfig


# Mashup Types (Phase 3+)
class MashupType(Enum):
    """Types of mashup strategies.

    Phase 3B (Simple):
    - CLASSIC: Traditional vocal A + instrumental B
    - STEM_SWAP: Mix drums/bass/vocals from 3+ songs

    Phase 3C (Energy-based):
    - ENERGY_MATCHED: Align sections by energy curves
    - ADAPTIVE_HARMONY: Auto-fix key clashes via pitch-shifting

    Phase 3D (Semantic):
    - THEME_FUSION: Filter lyrics to unified theme
    - SEMANTIC_ALIGNED: Meaning-driven structure (not tempo-driven)

    Phase 3E (Interactive):
    - ROLE_AWARE: Vocals become lead/harmony/call/response dynamically
    - CONVERSATIONAL: Songs talk to each other (lyric dialogue)
    """
    CLASSIC = "classic"
    STEM_SWAP = "stem_swap"
    ENERGY_MATCHED = "energy_matched"
    ADAPTIVE_HARMONY = "adaptive_harmony"
    THEME_FUSION = "theme_fusion"
    SEMANTIC_ALIGNED = "semantic_aligned"
    ROLE_AWARE = "role_aware"
    CONVERSATIONAL = "conversational"


class SectionMetadata(TypedDict, total=False):
    """Section-level metadata (verse, chorus, bridge, etc.).

    Added in Phase 3A to enable advanced mashup types.
    """
    # Structural
    section_type: str              # "intro" | "verse" | "chorus" | "bridge" | "outro"
    start_sec: float               # Start timestamp
    end_sec: float                 # End timestamp
    duration_sec: float            # Section duration

    # Energy characteristics (from librosa)
    energy_level: float            # 0.0-1.0 (RMS energy)
    spectral_centroid: float       # Brightness in Hz
    tempo_stability: float         # Beat consistency 0-1

    # Vocal characteristics (from stem analysis)
    vocal_density: str             # "sparse" | "medium" | "dense"
    vocal_intensity: float         # 0.0-1.0 (loudness + energy)
    lyrical_content: str           # Actual lyrics in this section

    # Semantic analysis (LLM-derived)
    emotional_tone: str            # "hopeful" | "melancholic" | "defiant" | etc.
    lyrical_function: str          # "narrative" | "hook" | "question" | "answer" | "reflection"
    themes: List[str]              # ["love", "loss", "rebellion"]


# Data Types
class SongMetadata(TypedDict, total=False):
    """Complete metadata for a song in ChromaDB."""
    source: Literal["youtube", "local_file"]
    path: str
    bpm: Optional[float]
    key: Optional[str]
    camelot: Optional[str]
    genres: List[str]
    primary_genre: str
    irony_score: int
    mood_summary: str
    energy_level: int
    valence: int
    first_downbeat_sec: float
    duration_sec: float
    sample_rate: int
    has_vocals: bool
    original_url: Optional[str]
    artist: str
    title: str
    date_added: str

    # Phase 3A: Section-level analysis for advanced mashups
    sections: List[SectionMetadata]  # Section breakdown (verse, chorus, etc.)
    emotional_arc: str                # e.g., "intro:hopeful → verse:doubt → chorus:defiant"


class IngestionResult(TypedDict):
    """Result from ingestion agent."""
    id: str
    path: str
    cached: bool
    source: str
    metadata: Optional[SongMetadata]


class MatchResult(TypedDict):
    """Result from curator agent."""
    id: str
    compatibility_score: float
    metadata: SongMetadata
    match_reasons: List[str]


class LLMAnalysis(TypedDict):
    """LLM-generated analysis."""
    genres: List[str]
    primary_genre: str
    irony_score: int
    mood_summary: str
    valence: int


class MashupConfig(TypedDict, total=False):
    """Configuration for mashup creation.

    Different mashup types require different config fields:
    - CLASSIC: vocal_id, inst_id
    - STEM_SWAP: vocals, drums, bass, other (song IDs)
    - ENERGY_MATCHED: song_a_id, song_b_id
    - THEME_FUSION: song_a_id, song_b_id, theme
    - etc.
    """
    # Classic/Adaptive
    vocal_id: str
    inst_id: str

    # Stem Swap
    vocals: str
    drums: str
    bass: str
    other: str

    # Energy/Semantic/Role/Conversational
    song_a_id: str
    song_b_id: str

    # Theme Fusion
    theme: str  # "love" | "heartbreak" | "rebellion" | etc.

    # Output settings
    output_format: str  # "mp3" | "wav"
    quality_preset: str  # "draft" | "high" | "broadcast"


# Type Aliases
QualityPreset = Literal["draft", "high", "broadcast"]
MatchCriteria = Literal["harmonic", "semantic", "hybrid"]
OutputFormat = Literal["mp3", "wav"]
SourceType = Literal["youtube", "local_file"]
