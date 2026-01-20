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

### CLI Usage

```bash
# CLI entry point
python -m mixer --help

# Fully automated workflow (recommended)
python -m mixer auto path/to/song.mp3
python -m mixer interactive  # Guided mode with prompts

# Manual workflow
python -m mixer ingest <youtube-url-or-file>
python -m mixer analyze <song-id>
python -m mixer analyze --batch
python -m mixer match <song-id> --criteria hybrid --top 5
python -m mixer mashup <song-a> <song-b> --type classic

# Library management
python -m mixer library list
python -m mixer library search "upbeat country"
python -m mixer library stats

# Available mashup types: classic, stem-swap, energy, adaptive, theme, semantic, role-aware, conversational
```

## Architecture

### High-Level Design

The system is organized around **4 main agents** that form a pipeline:

1. **Ingestion Agent** (`mixer/agents/ingestion.py`) - Downloads/caches audio from YouTube URLs or local files, validates format, converts to standard WAV
2. **Analyst Agent** (`mixer/agents/analyst.py`) - Extracts section-level metadata (verse/chorus boundaries, energy curves, vocal analysis, semantic analysis via LLM)
3. **Curator Agent** (`mixer/agents/curator.py`) - Finds compatible song pairs using hybrid matching (harmonic + semantic), calculates compatibility scores with weighted BPM/key/energy/genre factors, recommends optimal mashup types based on song characteristics
4. **Engineer Agent** (`mixer/agents/engineer.py`) - Builds final mashup with stem separation and alignment (8 mashup types implemented)

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

This section metadata is stored in the `sections` field of `SongMetadata` and enables 8 different mashup strategies (see `MashupType` enum in `mixer/types.py`):

1. **Classic** (`create_classic_mashup`) - Vocal from song A + instrumental from song B
2. **Stem Swap** (`create_stem_swap_mashup`) - Mix stems from 3+ songs (drums/bass/vocals/other)
3. **Energy Match** (`create_energy_matched_mashup`) - Align high-energy sections dynamically
4. **Adaptive Harmony** (`create_adaptive_harmony_mashup`) - Auto-fix key clashes via pitch-shifting
5. **Theme Fusion** (`create_theme_fusion_mashup`) - Filter sections by lyrical themes
6. **Semantic-Aligned** (`create_semantic_aligned_mashup`) - Question→answer, narrative→reflection pairing
7. **Role-Aware** (`create_role_aware_mashup`) - Vocals shift between lead/harmony/call/response/texture based on vocal characteristics
8. **Conversational** (`create_conversational_mashup`) - Songs talk to each other like a dialogue with silence gaps

### Word-Level Timing (Phase 3E)

For interactive mashup types (Role-Aware, Conversational), the **Analyst Agent** now stores word-level timestamps from Whisper:

- **Field**: `word_timings` in `SongMetadata` (list of Whisper segment dictionaries)
- **Source**: Whisper transcription with `word_timestamps=True`
- **Usage**: Enables future word-level vocal extraction for precise dialogue creation
- **Current Implementation**: Phase 3E mashups work at section-level (for MVP stability)

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

**Current Status**: All 7 Phases Complete - Production Ready 🚀

**Completed**:
- ✅ Phase 0: Foundation (directory structure, config, logging, CLI skeleton)
- ✅ Phase 1: Memory System (ChromaDB integration, 47 unit tests)
- ✅ Phase 2: Ingestion Agent (local files + YouTube, 22 unit tests)
- ✅ Phase 3A: Enhanced Analyst Agent (section-level metadata, 10 unit tests)
- ✅ Phase 3B: Simple Mashup Types (Classic, Stem Swap, 16 unit tests)
- ✅ Phase 3C: Energy-Based Mashups (Energy Match, Adaptive Harmony, 13 unit tests)
- ✅ Phase 3D: Semantic Mashups (Theme Fusion, Semantic-Aligned, 5 unit tests)
- ✅ Phase 3E: Interactive Mashups (Role-Aware, Conversational, 14 unit tests)
- ✅ Phase 4: Curator Agent (intelligent song pairing, compatibility scoring, mashup type recommendation, 19 unit tests, 94% coverage)
- ✅ Phase 5: LangGraph Workflow (multi-agent orchestration, state machine, human-in-the-loop, 25 unit tests, 68-73% coverage)
- ✅ Phase 6: CLI Refinement (production-ready CLI with rich formatting, auto/interactive modes, all 8 mashup types, 645 lines)
- ✅ Phase 7: Testing & QA (integration tests, CLI tests, performance benchmarking, 170+ total unit tests)

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
| `mixer/agents/curator.py` | Song pairing, compatibility scoring, mashup type recommendation |
| `mixer/agents/engineer.py` | All 8 mashup implementations (classic, stem swap, energy, adaptive, theme, semantic, role-aware, conversational) |
| `mixer/workflow/state.py` | LangGraph workflow state definitions (MashupState, WorkflowStatus) |
| `mixer/workflow/nodes.py` | Workflow node functions that wrap agents |
| `mixer/workflow/graph.py` | LangGraph workflow graph definition and execution |
| `mixer/cli.py` | Production-ready CLI with all commands (ingest, analyze, match, mashup, library, auto, interactive) |
| `mixer/audio/analysis.py` | Signal processing and section detection |
| `mixer/llm/semantic.py` | LLM-based semantic analysis |
| `tests/unit/` | 170+ unit tests across all modules |
| `tests/integration/` | End-to-end workflow tests and CLI integration tests |
| `scripts/benchmark.py` | Performance benchmarking tool for workflow stages |
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
