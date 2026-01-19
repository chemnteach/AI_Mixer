# Continuity Ledger - The Mixer

**Last Updated:** 2026-01-19
**Project:** The Mixer - AI-powered audio mashup pipeline
**Current Phase:** Phase 1 Complete → Phase 2 Starting

---

## Project State

### Completion Status

- ✅ **Phase 0: Foundation** (Complete 2026-01-18)
- ✅ **Phase 1: Memory System** (Complete 2026-01-19)
- ✅ **Phase 2: Ingestion Agent** (Complete 2026-01-19)
- ✅ **Phase 3A: Enhanced Analyst Agent** (Complete 2026-01-19 - Section-level metadata)
- ⏳ **Phase 3B: Simple Mashup Types** (Next - Classic, Stem Swap)
- ⏸️ **Phase 3C: Energy-Based Mashups** (Energy Match, Adaptive Harmony)
- ⏸️ **Phase 3D: Semantic Mashups** (Theme Fusion, Semantic-Aligned)
- ⏸️ **Phase 3E: Interactive Mashups** (Role-Aware, Conversational)
- ⏸️ Phase 4: Curator Agent
- ⏸️ Phase 5: LangGraph Workflow
- ⏸️ Phase 6: CLI Refinement
- ⏸️ Phase 7: Testing & QA

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

**Ingestion Agent (Phase 2):**
- `mixer/agents/ingestion.py` - Audio ingestion from local files and YouTube
- `tests/unit/test_ingestion.py` - 22 unit tests
- Features: cache checking, format conversion, retry logic, validation

**Analyst Agent (Phase 3A):**
- `mixer/agents/analyst.py` - Section-level metadata extraction (131 lines)
- `mixer/audio/analysis.py` - Signal processing and section detection (93 lines)
- `mixer/llm/semantic.py` - LLM-based semantic analysis (82 lines)
- `tests/unit/test_analyst.py` - 10 unit tests
- Features: section boundaries, energy analysis, vocal analysis, emotional arc

**Types:**
- `mixer/types.py` - TypedDict definitions for Config, SongMetadata, SectionMetadata, MashupType, etc.

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
| yt-dlp for YouTube ingestion | More actively maintained than youtube-dl | 2026-01-19 |
| ffmpeg for format conversion | Standard tool, reliable, widely available | 2026-01-19 |
| Exponential backoff for retries | 3 attempts with 2^n delay for network resilience | 2026-01-19 |
| madmom for section detection | Proven beat tracking, complements librosa | 2026-01-19 |
| Agglomerative clustering for sections | Librosa's spectral similarity clustering works well | 2026-01-19 |
| Whisper base model default | Balance of speed/accuracy for transcription | 2026-01-19 |
| Section-level metadata storage | Foundation for all advanced mashup types | 2026-01-19 |

### Advanced Mashup Types (Phase 3+)

**8 Mashup Strategies:**

| Type | Complexity | Key Innovation | Phase |
|------|-----------|----------------|-------|
| Classic | Low | Vocal A + Instrumental B | 3B |
| Stem Role Swapping | Low | Mix stems from 3+ songs | 3B |
| Energy Curve Matching | Medium | Align by energy peaks | 3C |
| Adaptive Harmony | Medium | Auto-fix key clashes | 3C |
| Lyrical Theme Fusion | Medium | Filter to unified theme | 3D |
| Semantic-Aligned | Medium-High | Meaning-driven structure | 3D |
| Role-Aware Recomposition | High | Dynamic lead/harmony/call/response | 3E |
| Conversational | High | Songs talk to each other | 3E |

**Foundation:** Section-level metadata (Phase 3A)
- Section boundaries (verse, chorus, bridge)
- Energy characteristics (RMS, spectral centroid)
- Vocal characteristics (density, intensity)
- Semantic analysis (emotional tone, lyrical function, themes)

**Types defined in:** `mixer/types.py` (MashupType enum, SectionMetadata)

**Full spec in:** PRD.md lines 828-1070

---

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

## Completed Sessions

### ✅ Phase 2: Ingestion Agent (Completed 2026-01-19)

**Implemented:**
- `mixer/agents/ingestion.py` (200 lines) - Full ingestion pipeline
- Local file support (WAV, MP3, FLAC) with format conversion
- YouTube ingestion via yt-dlp with retry logic
- Cache checking and deduplication via ChromaDB
- File validation (size, duration, integrity)
- Comprehensive error handling and logging

**Test Results:**
- 22 unit tests, all passing ✅
- 74% code coverage on ingestion module
- Validates corrupt files, network failures, caching

### ✅ Phase 3A: Enhanced Analyst Agent (Completed 2026-01-19)

**Implemented:**
- `mixer/agents/analyst.py` (131 lines) - Main orchestrator
- `mixer/audio/analysis.py` (93 lines) - Section detection and energy analysis
- `mixer/llm/semantic.py` (82 lines) - LLM-based semantic analysis
- Section detection via agglomerative clustering (librosa)
- Energy analysis per section (RMS, spectral centroid, tempo stability)
- Vocal analysis (density, intensity, lyric extraction)
- Semantic analysis via LLM (emotional tone, themes, lyrical function)
- Emotional arc generation

**Test Results:**
- 10 unit tests, all passing ✅
- 82% coverage on analyst, 77% on audio analysis
- Validates section detection, energy calculation, semantic extraction

**Critical Achievement:** Section-level metadata foundation now in place for all advanced mashup types.

---

## Next Session Priorities

### Immediate: Phase 3B - Simple Mashup Types

**Goal:** Validate core audio engineering architecture with working mashups

---

### Future Phases (Documented, Not Yet Started)

#### Phase 3A: Enhanced Analyst Agent (Critical Foundation)
**Goal:** Extract section-level metadata for advanced mashup types

**Why critical:** All 7 advanced mashup types depend on this

**Deliverables:**
1. Section detection (verse/chorus/bridge boundaries)
2. Energy analysis per section (RMS energy, spectral centroid)
3. Vocal analysis per section (density, intensity)
4. Semantic analysis per section (emotional tone via LLM)

**New dependencies:** `madmom>=0.16.1` (onset/beat tracking)

**Test criteria:**
- ✅ Run on 20 songs, verify section boundaries are reasonable
- ✅ Energy curves make sense (choruses > verses)
- ✅ Emotional tone classifications feel accurate

---

#### Phase 3B: Simple Mashup Types
**Goal:** Validate core audio engineering architecture

**Implement:**
1. Classic (vocal A + instrumental B) - already spec'd
2. Stem Role Swapping (mix drums/bass/vocals from 3+ songs)

**Test criteria:**
- ✅ Create 5 classic mashups - sound quality is good
- ✅ Time-stretching doesn't create artifacts
- ✅ Beat alignment is tight
- ✅ Stem swapping produces coherent multi-song mashups

---

#### Phase 3C: Energy-Based Mashup Types
**Goal:** Prove section-level metadata is useful

**Implement:**
1. Energy Curve Matching (align by energy, not just tempo)
2. Adaptive Harmony (auto-fix key clashes)

**Test criteria:**
- ✅ Energy-matched mashups feel more climactic
- ✅ Pitch-shifting quality is acceptable (within ±3 semitones)
- ✅ Key clash detection works correctly

---

#### Phase 3D: Semantic Mashup Types
**Goal:** Prove AI can reason about music structure

**Implement:**
1. Lyrical Theme Fusion (filter lyrics to theme)
2. Semantic-Aligned (meaning-driven structure)

**Test criteria:**
- ✅ Theme filtering creates coherent narratives
- ✅ LLM choices about section ordering make sense
- ✅ Crossfades between sections sound smooth

---

#### Phase 3E: Interactive Mashup Types
**Goal:** Push boundaries - vocals interact dynamically

**Implement:**
1. Role-Aware Recomposition (lead/harmony/call/response)
2. Conversational (songs talk to each other)

**Test criteria:**
- ✅ Role assignments sound natural
- ✅ Conversational mashups feel like genuine dialogue
- ✅ Vocal extraction at lyric-level works cleanly

---

### Implementation Philosophy

**Incremental Build-and-Test:** Validate each layer before moving to the next. When complex mashup types are built, all underlying pieces are proven solid.

**Testing:** Use real songs (not synthetic test files) across 6 categories:
- Simple pop (4/4, clear sections)
- Complex arrangement (odd time, irregular structure)
- A cappella (vocal detection test)
- Instrumental (no-vocals detection test)
- Rap (dense lyrics test)
- Ballad (sparse, emotional, semantic test)

**Timeline (Rough Estimate):**
- Phase 2 (Ingestion): 1-2 weeks
- Phase 3A (Enhanced Analyst): 2-3 weeks (most critical)
- Phase 3B (Simple Mashups): 1 week
- Phase 3C (Energy Types): 1 week
- Phase 3D (Semantic Types): 1-2 weeks
- Phase 3E (Interactive Types): 2 weeks
- **Total:** ~2-3 months for full advanced mashup system

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
