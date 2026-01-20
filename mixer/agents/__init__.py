"""The Mixer Agents - Ingestion, Analysis, Curation, Engineering."""

from mixer.agents.ingestion import (
    ingest_song,
    IngestionError,
    InvalidInputError,
    DownloadError,
    ValidationError,
)

from mixer.agents.analyst import (
    profile_audio,
    AnalysisError,
)

from mixer.agents.curator import (
    find_match,
    calculate_compatibility_score,
    recommend_mashup_type,
    find_all_pairs,
    CuratorError,
)

from mixer.agents.engineer import (
    create_classic_mashup,
    create_stem_swap_mashup,
    create_energy_matched_mashup,
    create_adaptive_harmony_mashup,
    create_theme_fusion_mashup,
    create_semantic_aligned_mashup,
    create_role_aware_mashup,
    create_conversational_mashup,
    EngineerError,
    SongNotFoundError,
    MashupConfigError,
)

__all__ = [
    # Ingestion
    "ingest_song",
    "IngestionError",
    "InvalidInputError",
    "DownloadError",
    "ValidationError",
    # Analysis
    "profile_audio",
    "AnalysisError",
    # Curation
    "find_match",
    "calculate_compatibility_score",
    "recommend_mashup_type",
    "find_all_pairs",
    "CuratorError",
    # Engineering
    "create_classic_mashup",
    "create_stem_swap_mashup",
    "create_energy_matched_mashup",
    "create_adaptive_harmony_mashup",
    "create_theme_fusion_mashup",
    "create_semantic_aligned_mashup",
    "create_role_aware_mashup",
    "create_conversational_mashup",
    "EngineerError",
    "SongNotFoundError",
    "MashupConfigError",
]
