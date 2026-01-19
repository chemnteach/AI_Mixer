"""Type definitions for The Mixer."""

from typing import TypedDict, Literal, Optional, List
from datetime import datetime


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


# Type Aliases
QualityPreset = Literal["draft", "high", "broadcast"]
MatchCriteria = Literal["harmonic", "semantic", "hybrid"]
OutputFormat = Literal["mp3", "wav"]
SourceType = Literal["youtube", "local_file"]
