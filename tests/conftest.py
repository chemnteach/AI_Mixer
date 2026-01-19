"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
import sys

# Add mixer package to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_config_path(tmp_path):
    """Create a temporary config file for testing."""
    config_content = """
paths:
  library_cache: "./test_library_cache"
  mashup_output: "./test_mashups"
  chroma_db: "./test_chroma_db"
  failed_files: "./test_library_cache/failed"

audio:
  sample_rate: 44100
  bit_depth: 16
  channels: 2
  default_format: "wav"

models:
  whisper_size: "base"
  demucs_model: "htdemucs"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

llm:
  primary_provider: "anthropic"
  fallback_provider: "openai"
  anthropic_model: "claude-3-5-sonnet-20241022"
  openai_model: "gpt-4-turbo-preview"
  max_retries: 3
  timeout: 30

curator:
  bpm_tolerance: 0.05
  max_stretch_ratio: 1.2
  default_match_criteria: "hybrid"
  max_candidates: 5

engineer:
  default_quality: "high"
  vocal_attenuation_db: -2.0
  fade_duration_sec: 4.0
  normalize_lufs: -14

performance:
  max_concurrent_downloads: 4
  enable_gpu: false
  fallback_to_cpu: true
  max_cache_size_gb: 50

logging:
  level: "INFO"
  file: "test_mixer.log"
  max_file_size_mb: 100
  backup_count: 5
"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "genres": ["Pop", "Dance"],
        "primary_genre": "Pop",
        "irony_score": 5,
        "mood_summary": "Upbeat and energetic with electronic influences",
        "valence": 7
    }


@pytest.fixture
def sample_metadata():
    """Sample song metadata for testing."""
    return {
        "source": "local_file",
        "path": "/path/to/test.wav",
        "bpm": 120.0,
        "key": "Cmaj",
        "camelot": "8B",
        "genres": ["Pop"],
        "primary_genre": "Pop",
        "irony_score": 3,
        "mood_summary": "Test mood",
        "energy_level": 7,
        "valence": 6,
        "first_downbeat_sec": 0.5,
        "duration_sec": 180.0,
        "sample_rate": 44100,
        "has_vocals": True,
        "artist": "Test Artist",
        "title": "Test Song",
        "date_added": "2026-01-18T00:00:00Z"
    }
