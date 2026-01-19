# Continuity Ledger - The Mixer

**Last Updated:** 2026-01-19
**Project:** The Mixer - AI-powered audio mashup pipeline
**Current Phase:** Phase 1 Complete → Phase 2 Starting

---

## Project State

### Completion Status

- ✅ **Phase 0: Foundation** (Complete 2026-01-18)
- ✅ **Phase 1: Memory System** (Complete 2026-01-19)
- ⏳ **Phase 2: Ingestion Agent** (Next)
- ⏸️ Phase 3: Analyst Agent
- ⏸️ Phase 4: Curator Agent
- ⏸️ Phase 5: Engineer Agent
- ⏸️ Phase 6: LangGraph Workflow
- ⏸️ Phase 7: CLI Refinement
- ⏸️ Phase 8: Testing & QA

### Key Files & Architecture

**Configuration:**
- `config.yaml` - User-facing configuration (paths, models, performance)
- `mixer/config.py` - ConfigManager with dot-notation access
- `.env.template` - API keys template (ANTHROPIC_API_KEY, OPENAI_API_KEY)

**Memory System (Phase 1):**
- `mixer/memory/client.py` - ChromaDB persistent client (singleton)
- `mixer/memory/schema.py` - ID sanitization, metadata validation, Camelot conversion
- `mixer/memory/queries.py` - Upsert, get, delete, harmonic/semantic/hybrid queries
- `tests/unit/test_memory.py` - 47 unit tests
- `scripts/test_memory_demo.py` - Interactive demo

**Types:**
- `mixer/types.py` - TypedDict definitions for Config, SongMetadata, MatchResult, etc.

**Utilities:**
- `mixer/utils/logging.py` - Structured logging with rotation

**CLI:**
- `mixer/cli.py` - Click-based CLI skeleton
- `mixer/__main__.py` - Entry point

---

## Key Decisions & Rationale

### Architecture Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| ChromaDB 0.4.22 pinned | Avoid breaking changes during development | 2026-01-18 |
| Click over Typer | Mature ecosystem, better documentation | 2026-01-18 |
| TypedDict for config | Type safety without runtime overhead | 2026-01-18 |
| Singleton client pattern | Consistent ChromaDB access, prevent multiple connections | 2026-01-19 |
| Hybrid matching recommended | 60% harmonic + 40% semantic per PRD design | 2026-01-19 |
| Local files first for Phase 2 | Simpler than YouTube, no TOS concerns initially | 2026-01-19 |
| sentence-transformers/all-MiniLM-L6-v2 | Balance of speed/quality (384-dim embeddings) | 2026-01-19 |

### Data Schema

**ChromaDB Collection:** `tiki_library`
- **ID Format:** `{artist}_{title}` (sanitized: lowercase, no special chars, max 128)
- **Document:** `"{transcript}\n\n[MOOD]: {mood_summary}"` (for embedding)
- **Metadata:** SongMetadata TypedDict (see `mixer/types.py:86-107`)

**Key Fields:**
- Technical: bpm, key, camelot, sample_rate, duration_sec, first_downbeat_sec
- Semantic: genres, primary_genre, mood_summary, irony_score, energy_level, valence
- Source: source (youtube/local_file), path, original_url

**Camelot Wheel Compatibility:**
- Same key: Perfect match
- ±1 on wheel: Adjacent keys (Circle of 5ths)
- Inner/outer circle: Relative major/minor

---

## Implementation Patterns

### Memory System Usage

```python
from mixer.memory import (
    get_client,           # Get singleton ChromaDB client
    upsert_song,          # Insert/update song
    get_song,             # Retrieve by ID
    query_hybrid,         # Recommended: harmonic + semantic
    sanitize_id,          # Create valid ID from artist/title
)

# Initialize
client = get_client()
collection = client.get_collection()

# Add song
song_id = upsert_song(
    artist="Taylor Swift",
    title="Shake It Off",
    metadata=song_metadata,
    transcript="I stay out too late..."
)

# Find matches (hybrid recommended)
matches = query_hybrid(
    target_song_id="taylor_swift_shake_it_off",
    max_results=5
)
```

### Configuration Access

```python
from mixer.config import get_config

config = get_config()
bpm_tolerance = config.get("curator.bpm_tolerance")  # 0.05
chroma_path = config.get_path("chroma_db")           # Path object
```

### Testing Pattern

```python
import pytest
from mixer.memory import reset_client, ChromaClient

@pytest.fixture
def chroma_client(temp_chroma_dir):
    reset_client()  # Reset global client
    client = ChromaClient(persist_directory=temp_chroma_dir)
    yield client
    client.close()
    reset_client()
```

---

## Critical Dependencies

### Python Packages (requirements.txt)

**Core:**
- chromadb==0.4.22 (pinned for stability)
- sentence-transformers>=2.2.0
- click>=8.0.0
- pyyaml>=6.0

**Audio (Phase 2+):**
- librosa>=0.10.0
- openai-whisper>=20230314
- pydub>=0.25.0
- demucs>=4.0.0
- yt-dlp>=2023.3.4
- ffmpeg-python>=0.2.0

**LLM (Phase 3+):**
- anthropic>=0.18.0
- openai>=1.0.0

**Testing:**
- pytest>=7.4.0
- pytest-cov>=4.1.0

### System Dependencies

- **Python 3.9+**
- **ffmpeg** (audio conversion)
- **libsndfile** (optional, audio I/O)
- **CUDA 11.8+** (optional, GPU acceleration for Demucs/Whisper)

---

## Known Issues & Constraints

### Current Limitations

1. **Memory system only** - Ingestion, analysis, and engineering not yet implemented
2. **No actual audio processing** - Pure metadata/vector storage at this stage
3. **Manual metadata entry** - Analyst agent needed for automatic metadata extraction

### Future Considerations

1. **YouTube TOS** - yt-dlp usage technically violates TOS (warn users, consider alternatives)
2. **Large installations** - PyTorch dependencies ~5GB total
3. **GPU memory** - Demucs peak usage ~8GB VRAM, fallback to CPU needed
4. **Cache management** - Need LRU eviction if library exceeds 50GB

---

## Testing & Verification

### Test Commands

```bash
# Unit tests
pytest tests/unit/test_memory.py -v

# Coverage
pytest tests/ -v --cov=mixer

# Interactive demo
python scripts/test_memory_demo.py

# CLI (skeleton only)
python -m mixer --help
```

### Test Coverage (Phase 1)

- ✅ ID sanitization (special chars, max length, collisions)
- ✅ Metadata validation (ranges, required fields, types)
- ✅ ChromaDB persistence across restarts
- ✅ Harmonic matching (BPM, key compatibility)
- ✅ Semantic matching (mood, genre, vibe)
- ✅ Hybrid matching (combined scoring)
- ✅ Camelot wheel logic
- ✅ Document creation and embedding

**Total: 47 unit tests**

---

## Next Session Priorities

### Phase 2: Ingestion Agent

**Scope:**
1. Implement `mixer/agents/ingestion.py`
2. Local file support (WAV, MP3, FLAC)
3. Format conversion to standard WAV (44.1kHz, 16-bit, stereo)
4. File validation (size, duration, integrity)
5. Cache management (check ChromaDB before processing)

**Implementation order:**
1. Local file ingestion (simpler)
2. YouTube ingestion (yt-dlp integration)
3. Cache checking (query by ID, skip if exists)
4. Error handling (corrupt files, network timeouts)

**Files to create:**
- `mixer/agents/ingestion.py`
- `mixer/agents/__init__.py` (update exports)
- `tests/unit/test_ingestion.py`
- Test fixtures: sample audio files

**References:**
- PRD.md lines 259-336 (Ingestion Agent spec)
- Handoff: `thoughts/shared/handoffs/general/2026-01-19_05-33_phase-1-memory-system-complete.yaml`

---

## Handoff Documents

**Location:** `thoughts/shared/handoffs/general/`

- `2026-01-18_22-00_phase-0-foundation-complete.yaml`
- `2026-01-19_05-33_phase-1-memory-system-complete.yaml`

**Format:** YAML with sections: goal, done_this_session, blockers, decisions, findings, worked, failed, next

---

## Project Resources

**Documentation:**
- `README.md` - User-facing documentation, quick start
- `PRD.md` - Complete product requirements (1360 lines)
- `CONTINUITY.md` - This file (architecture, decisions, state)

**Configuration:**
- `config.yaml` - Editable configuration
- `.env.template` - API keys template

**Development:**
- `pyproject.toml` - Project metadata
- `requirements.txt` - Python dependencies
- `.gitignore` - Git exclusions

---

## Glossary

**Camelot Wheel:** DJ notation for musical keys (1A-12A minor, 1B-12B major), enables harmonic mixing
**Hybrid Matching:** Combined harmonic (BPM+key) and semantic (mood+vibe) matching strategy
**RRF:** Reciprocal Rank Fusion, ranking algorithm for combining search results
**Demucs:** ML model for source separation (isolating vocals/drums/bass/other)
**Whisper:** OpenAI speech recognition model for lyric transcription
**ChromaDB:** Vector database for semantic search with embeddings
**LUFS:** Loudness Units Full Scale, broadcast standard for audio normalization

---

*This ledger is updated at each major milestone. For session details, see handoff documents in `thoughts/shared/handoffs/general/`*
