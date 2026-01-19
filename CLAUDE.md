# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**The Mixer** is an intelligent audio mashup pipeline that uses semantic understanding (not just BPM/key) to discover and create musical mashups. The system combines ChromaDB vector search with LLM-powered semantic analysis to match songs based on harmonic compatibility, mood, genre, and lyrical themes.

## Development Commands

### Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure API keys (required for LLM features)
cp .env.template .env
# Edit .env and add ANTHROPIC_API_KEY and OPENAI_API_KEY
```

### Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=mixer --cov-report=html --cov-report=term

# Run specific test modules
pytest tests/unit/test_memory.py -v
pytest tests/unit/test_ingestion.py -v
pytest tests/unit/test_analyst.py -v

# Run single test
pytest tests/unit/test_memory.py::test_sanitize_id -v

# Interactive memory system demo
python scripts/test_memory_demo.py
```

### Code Quality

```bash
# Format code
black mixer/ tests/

# Type checking
mypy mixer/
```

### CLI Usage (In Development)

```bash
# CLI entry point
python -m mixer --help

# Example commands (not all implemented yet)
python -m mixer ingest <youtube-url-or-file>
python -m mixer analyze --batch
python -m mixer match <song-id> --criteria hybrid
python -m mixer library list
```

## Architecture

### High-Level Design

The system is organized around **4 main agents** that form a pipeline:

1. **Ingestion Agent** (`mixer/agents/ingestion.py`) - Downloads/caches audio from YouTube URLs or local files, validates format, converts to standard WAV
2. **Analyst Agent** (`mixer/agents/analyst.py`) - Extracts section-level metadata (verse/chorus boundaries, energy curves, vocal analysis, semantic analysis via LLM)
3. **Curator Agent** (not yet implemented) - Finds compatible song pairs using hybrid matching (harmonic + semantic)
4. **Engineer Agent** (not yet implemented) - Builds final mashup with stem separation and alignment

### Memory System (ChromaDB)

The **memory layer** (`mixer/memory/`) is the foundation that all agents rely on:

- **Singleton client pattern**: Use `get_client()` from `mixer/memory/client.py` for consistent ChromaDB access
- **Collection name**: `tiki_library` (hardcoded)
- **ID format**: `{artist}_{title}` sanitized (lowercase, no special chars, max 128 chars)
- **Document format**: `"{transcript}\n\n[MOOD]: {mood_summary}"` (embedded using sentence-transformers/all-MiniLM-L6-v2)
- **Metadata schema**: Defined in `mixer/types.py` as `SongMetadata` TypedDict

#### Three Query Modes

1. **Harmonic matching** (`query_harmonic`) - BPM tolerance (±5%) + Camelot wheel key compatibility
2. **Semantic matching** (`query_semantic`) - Mood, genre, vibe similarity via embeddings
3. **Hybrid matching** (`query_hybrid`) - **Recommended**: 60% harmonic + 40% semantic using RRF (Reciprocal Rank Fusion)

**Camelot Wheel Compatibility Rules**:
- Same Camelot key = perfect match
- ±1 on wheel = adjacent keys (Circle of 5ths)
- Inner/outer circle = relative major/minor

### Configuration System

- **User-facing config**: `config.yaml` (paths, model choices, matching criteria, performance settings)
- **ConfigManager**: `mixer/config.py` provides dot-notation access (e.g., `config.get("curator.bpm_tolerance")`)
- **Type safety**: All config sections typed as TypedDicts in `mixer/types.py`
- **API keys**: Loaded from `.env` file (use `.env.template` as reference)

### Section-Level Metadata (Phase 3A)

The **Analyst Agent** extracts detailed section-level data to enable advanced mashup types:

- **Structural**: Section boundaries (intro/verse/chorus/bridge/outro)
- **Energy**: RMS energy, spectral centroid (brightness), tempo stability
- **Vocal**: Density (sparse/medium/dense), intensity, lyrical content
- **Semantic**: Emotional tone, lyrical function (narrative/hook/question/answer), themes

This section metadata is stored in the `sections` field of `SongMetadata` and enables 8 different mashup strategies (see `MashupType` enum in `mixer/types.py`).

### Audio Processing Stack

- **librosa**: Core audio analysis (BPM, key, energy, spectral features)
- **whisper**: Lyric transcription (configurable model size: tiny/base/small/medium/large)
- **demucs**: Stem separation (vocals/drums/bass/other)
- **pydub + ffmpeg**: Format conversion and audio manipulation
- **pyrubberband**: Time-stretching for BPM alignment

### LLM Integration

- **Primary provider**: Anthropic Claude (configurable model: claude-3-5-sonnet-20241022)
- **Fallback provider**: OpenAI GPT-4 Turbo
- **Usage**: Semantic analysis of lyrics (mood, themes, emotional tone), genre classification, irony detection
- **Location**: `mixer/llm/semantic.py`

## Key Implementation Patterns

### Working with the Memory System

```python
from mixer.memory import get_client, upsert_song, query_hybrid, sanitize_id

# Get singleton client
client = get_client()
collection = client.get_collection()

# Create song ID
song_id = sanitize_id(artist="Taylor Swift", title="Shake It Off")
# Result: "taylor_swift_shake_it_off"

# Add/update song
upsert_song(
    artist="Taylor Swift",
    title="Shake It Off",
    metadata={
        "bpm": 160.0,
        "key": "G major",
        "camelot": "9B",
        "mood_summary": "upbeat pop confidence",
        # ... other fields
    },
    transcript="I stay out too late..."
)

# Find compatible matches (hybrid is recommended)
matches = query_hybrid(
    target_song_id="taylor_swift_shake_it_off",
    max_results=5
)
```

### Test Fixtures Pattern

Tests use temporary ChromaDB directories to ensure isolation:

```python
import pytest
from mixer.memory import reset_client, ChromaClient

@pytest.fixture
def chroma_client(temp_chroma_dir):
    """Fixture providing isolated ChromaDB client for testing."""
    reset_client()  # Clear global singleton
    client = ChromaClient(persist_directory=temp_chroma_dir)
    yield client
    client.close()
    reset_client()
```

See `tests/conftest.py` for shared fixtures.

### Configuration Access

```python
from mixer.config import get_config

config = get_config()  # Loads from config.yaml

# Dot notation access
bpm_tolerance = config.get("curator.bpm_tolerance")  # 0.05
sample_rate = config.get("audio.sample_rate")  # 44100

# Path objects (automatically resolved)
chroma_path = config.get_path("chroma_db")  # Returns Path object
library_cache = config.get_path("library_cache")
```

## Project State & Phases

**Current Status**: Phase 3A Complete → Phase 3B Next

**Completed**:
- ✅ Phase 0: Foundation (directory structure, config, logging, CLI skeleton)
- ✅ Phase 1: Memory System (ChromaDB integration, 47 unit tests)
- ✅ Phase 2: Ingestion Agent (local files + YouTube, 22 unit tests)
- ✅ Phase 3A: Enhanced Analyst Agent (section-level metadata, 10 unit tests)

**In Progress**:
- ⏳ Phase 3B: Simple Mashup Types (Classic vocal+instrumental, Stem Swap)

**Future Phases**:
- Phase 3C: Energy-Based Mashups
- Phase 3D: Semantic Mashups
- Phase 3E: Interactive Mashups (Role-Aware, Conversational)
- Phase 4: Curator Agent
- Phase 5: LangGraph Workflow
- Phase 6: CLI Refinement
- Phase 7: Testing & QA

## Critical Files

| File | Purpose |
|------|---------|
| `mixer/types.py` | TypedDict definitions for all data structures |
| `mixer/config.py` | Configuration management with dot-notation access |
| `mixer/memory/client.py` | ChromaDB singleton client |
| `mixer/memory/queries.py` | Core query operations (harmonic/semantic/hybrid) |
| `mixer/memory/schema.py` | ID sanitization and metadata validation |
| `mixer/agents/ingestion.py` | Audio ingestion from files/YouTube |
| `mixer/agents/analyst.py` | Section-level metadata extraction |
| `mixer/audio/analysis.py` | Signal processing and section detection |
| `mixer/llm/semantic.py` | LLM-based semantic analysis |
| `config.yaml` | User-editable configuration |
| `CONTINUITY.md` | Detailed project state and architecture decisions |

## Important Constraints

### System Dependencies

- **ffmpeg** is required for audio conversion (check with `scripts/check_dependencies.sh` or `.bat`)
- **libsndfile** is optional but recommended for better audio I/O
- **CUDA 11.8+** optional for GPU acceleration (Demucs/Whisper)

### ChromaDB Version

- **Pinned to 0.4.22** in requirements.txt to avoid breaking changes during development
- Do not upgrade without testing thoroughly

### ID Sanitization Rules

When creating song IDs, follow `mixer/memory/schema.py` rules:
- Format: `{artist}_{title}`
- Lowercase, remove special characters, replace spaces with underscores
- Maximum 128 characters
- Handles collisions with automatic versioning (_v2, _v3, etc.)

### Metadata Validation

All metadata must pass validation in `mixer/memory/schema.py`:
- **BPM**: 20-300 range
- **Irony/Energy/Valence**: 0-10 range
- **Key**: Must be valid musical key (C major, A minor, etc.)
- **Camelot**: Must be valid Camelot notation (1A-12A, 1B-12B)

### Legal & Usage

This tool is intended for:
- Educational purposes (learning audio processing, ML)
- Personal use (non-commercial experimentation)
- Fair use (research, commentary, parody)

**Users are responsible for**:
- Ensuring they have rights to process audio
- Complying with YouTube Terms of Service
- Not distributing copyrighted mashups without permission

## Documentation References

- **PRD.md**: Complete product requirements and technical specifications (1360+ lines)
- **CONTINUITY.md**: Detailed project state, architecture decisions, session history
- **README.md**: User-facing quick start and feature overview
- **Handoff documents**: `thoughts/shared/handoffs/general/*.yaml` - Detailed session outcomes
