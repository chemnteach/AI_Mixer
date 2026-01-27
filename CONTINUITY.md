# Continuity Ledger - The Mixer

**Last Updated:** 2026-01-27 (Session 13)
**Project:** The Mixer - AI-powered audio mashup pipeline + Crossfade Club visual DJ system
**Current Phase:** Asset Acquisition In Progress - Avatar Complete (1/8) 🎯

---

## Project State

### Completion Status

- ✅ **Phase 0: Foundation** (Complete 2026-01-18)
- ✅ **Phase 1: Memory System** (Complete 2026-01-19)
- ✅ **Phase 2: Ingestion Agent** (Complete 2026-01-19)
- ✅ **Phase 3A: Enhanced Analyst Agent** (Complete 2026-01-19 - Section-level metadata)
- ✅ **Phase 3B: Simple Mashup Types** (Complete 2026-01-19 - Classic, Stem Swap)
- ✅ **Phase 3C: Energy-Based Mashups** (Complete 2026-01-19 - Energy Match, Adaptive Harmony)
- ✅ **Phase 3D: Semantic Mashups** (Complete 2026-01-19 - Theme Fusion, Semantic-Aligned)
- ✅ **Phase 3E: Interactive Mashups** (Complete 2026-01-19 - Role-Aware, Conversational)
- ✅ **Phase 4: Curator Agent** (Complete 2026-01-19 - Intelligent song pairing, compatibility scoring, mashup type recommendation)
- ✅ **Phase 5: LangGraph Workflow** (Complete 2026-01-19 - Multi-agent orchestration, state machine, human-in-the-loop)
- ✅ **Phase 6: CLI Refinement** (Complete 2026-01-19 - Production-ready command-line interface with rich formatting, auto/interactive modes)
- ✅ **Phase 7: Testing & QA** (Complete 2026-01-19 - Integration tests, CLI tests, performance benchmarking, 170+ total unit tests)

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

**Engineer Agent (Phase 3B-3E):**
- `mixer/agents/engineer.py` - All 8 mashup creation functions (676 lines, 93% coverage)
- `mixer/audio/processing.py` - Stem separation, time-stretching, alignment, pitch-shifting (474 lines)
- `tests/unit/test_engineer.py` - 34 unit tests (phases 3B-3D)
- `tests/unit/test_engineer_phase3e.py` - 14 unit tests (phase 3E)
- Features: 8 mashup types (classic, stem swap, energy match, adaptive harmony, theme fusion, semantic aligned, role-aware, conversational)

**Curator Agent (Phase 4):**
- `mixer/agents/curator.py` - Song pairing and compatibility analysis (190 lines, 94% coverage)
- `tests/unit/test_curator.py` - 19 unit tests
- Features: harmonic/semantic/hybrid matching, weighted compatibility scoring (BPM/key/energy/genre), mashup type recommendation, batch pair discovery
- Functions: `find_match()`, `calculate_compatibility_score()`, `recommend_mashup_type()`, `find_all_pairs()`

**LangGraph Workflow (Phase 5):**
- `mixer/workflow/state.py` - Workflow state definitions (MashupState TypedDict, WorkflowStatus enum)
- `mixer/workflow/nodes.py` - Agent node functions (201 lines, 73% coverage)
- `mixer/workflow/graph.py` - Workflow graph definition and execution (66 lines, 68% coverage)
- `tests/unit/test_workflow.py` - 25 unit tests
- Features: multi-agent orchestration, state machine, conditional routing, error handling with retry, human-in-the-loop approval, progress streaming
- Nodes: ingest_song_a, analyze_song_a, ingest_song_b, analyze_song_b, find_matches, await_user_selection, recommend_mashup_type, await_mashup_approval, create_mashup, error_handler

**Types:**
- `mixer/types.py` - TypedDict definitions for Config, SongMetadata, SectionMetadata, MashupType, etc.

**Utilities:**
- `mixer/utils/logging.py` - Structured logging with rotation

**CLI (Phase 6):**
- `mixer/cli.py` - Production-ready CLI with rich formatting (645 lines)
- `mixer/__main__.py` - Entry point
- Commands: ingest, analyze, match, mashup, library (list/search/stats), auto, interactive
- Features: progress bars, tables, panels, workflow integration, all 8 mashup types supported

**Testing & QA (Phase 7):**
- `tests/unit/` - 170+ unit tests across all modules (85%+ average coverage)
- `tests/integration/test_e2e_workflow.py` - End-to-end workflow integration tests
- `tests/integration/test_cli_integration.py` - CLI command integration tests
- `scripts/benchmark.py` - Performance benchmarking tool for workflow stages
- Coverage: memory (98%), ingestion (95%), analyst (92%), engineer (93-98%), curator (94%), workflow (68-100%), CLI (production-ready)

**Web UI (Post-Phase 7 Enhancement):**
- `mixer_ui.py` - Complete Streamlit web interface (1066 lines)
- `UI_GUIDE.md` - Comprehensive UI usage guide with workflows and FAQ
- Features: Create Mashup tab (auto/manual modes), Library Management (browse/ingest/stats), Generate Video tab (disabled pending assets), Settings viewer
- All 8 mashup types accessible via dropdown
- Visual library browser with search, charts, metadata display
- File upload, audio playback, download functionality

**Batch Ingestion Features (Post-Phase 7 Enhancement):**
- `mixer/agents/ingestion.py` - Added `extract_playlist_info()` function for YouTube playlists
- **Batch Folder Ingest:** CLI `--folder` option and UI "Batch Folder" mode for CD rips
- **YouTube Playlist Ingest:** CLI `--playlist` option and UI "YouTube Playlist" mode for curated collections
- CLI: Progress bars, summaries, auto-analyze flag, max limit for playlists
- UI: Four ingest modes (Upload, YouTube URL, Batch Folder, YouTube Playlist)
- UI: Checkbox selection for playlist videos, select/deselect all buttons
- Perfect for building libraries from CD collections or themed YouTube playlists

**Crossfade Club — Visual DJ System (Implementation Complete):**
- `docs/crossfade-club/CROSSFADE_CLUB_PRD.md` - Product requirements (35 sections)
- `docs/crossfade-club/CROSSFADE_CLUB_COMPLETE.md` - Implementation summary
- **Concept:** Convert Mixer audio mashups into platform-optimized video content with animated cartoon DJ avatar
- **Architecture:** Mixer → Director Agent → Blender Studio → FFmpeg Encoder → Platform variants
- **Components (All Implemented):**
  - `director/` - Visual intelligence layer (timeline, events, camera, themes, safety)
  - `studio/` - Blender integration (renderer, asset_loader, blender_scripts)
  - `encoder/` - FFmpeg platform variants (platform, captions, thumbnail)
  - `batch/` - Batch runner for automated video generation
- **Themes:** 4 presets (sponsor_neon, award_elegant, mashup_chaos, chill_lofi)
- **Tests:** 67 tests (63 unit + 4 integration), 100% pass rate
- **Status:** ✅ Code complete, ⚠️ Requires Blender assets (8 .blend files) - see `studio/assets/README.md`
- **Current:** Researching free/cheap asset sources (Mixamo, BlendSwap, AI tools)

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
| Pyrubberband for time-stretching | Pitch-preserving, high quality, proven library | 2026-01-19 |
| Librosa for pitch-shifting | Standard, reliable, good quality within ±6 semitones | 2026-01-19 |
| Chromatic circle shortest path | Minimize pitch-shifting artifacts (max ±6 semitones) | 2026-01-19 |
| Pydub for mixing/export | Simple API, reliable ffmpeg wrapper | 2026-01-19 |
| Lyrical function pairing | Question→answer, narrative→reflection for semantic mashups | 2026-01-19 |
| Case-insensitive theme matching | More robust theme fusion matching | 2026-01-19 |
| Weighted compatibility scoring | BPM (35%), key (30%), energy (20%), genre (15%) balances factors | 2026-01-19 |
| Curator wraps existing queries | Reuse Phase 1 query_harmonic/semantic/hybrid infrastructure | 2026-01-19 |
| Streamlit for web UI | Pure Python, perfect for audio/ML, fast development, local-first | 2026-01-19 |
| Batch folder ingestion | CD rips use case, reduces friction for building large libraries | 2026-01-19 |
| YouTube playlist extraction | yt-dlp --flat-playlist avoids downloading until user confirms | 2026-01-19 |
| Checkbox selection for playlists | User control over which videos to ingest from large playlists | 2026-01-19 |
| Configurable weight overrides | Allow user customization via config.yaml or function args | 2026-01-19 |
| Mashup type recommendation | Decision tree based on song characteristics (vocals, key distance, sections) | 2026-01-19 |
| LangGraph for workflow orchestration | Proven library for agent state machines with built-in error handling | 2026-01-19 |
| TypedDict for workflow state | Type-safe state with clear field definitions | 2026-01-19 |
| Node functions wrap agents | Each node calls one agent and updates state (separation of concerns) | 2026-01-19 |
| Conditional edges for routing | Dynamic workflow paths based on state (song B provided vs curator match) | 2026-01-19 |
| Human-in-the-loop nodes | Workflow pauses for user input (match selection, mashup approval) | 2026-01-19 |
| Auto-selection fallback | Auto-select top match if user doesn't respond (graceful degradation) | 2026-01-19 |
| Progress message accumulation | List of human-readable messages for streaming display | 2026-01-19 |
| Error handler with retry | Max 3 retries before workflow fails | 2026-01-19 |
| Director Agent architecture | Separate visual intelligence layer bridges Mixer → video pipeline | 2026-01-20 |
| Hybrid animation approach | Baked clips (quality) + procedural modulation (audio-responsive) | 2026-01-20 |
| Timeline.json as authority | All visual behavior driven by timeline metadata, not code | 2026-01-20 |
| Event-safe guardrails | Hard validation prevents risky outputs for client deliverables | 2026-01-20 |
| Blender for 3D rendering | Industry standard, Python API (bpy), headless rendering support | 2026-01-20 |
| AI for design, rigging for control | AI generates character concept, artist rigs once, automation forever | 2026-01-20 |
| Platform-aware batch generation | Default to all variants (TikTok/Reels/Shorts/YouTube), opt-out supported | 2026-01-20 |
| Theme system for presets | Lighting + color + studio variant bundles for rapid customization | 2026-01-20 |
| Usage manifests for legal compliance | Plain-text documents clarify licensing responsibility for events | 2026-01-20 |
| Base look MVP, expansions later | Single avatar/studio proves concept before wardrobe/props investment | 2026-01-20 |

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

### Engineer Agent Usage

```python
from mixer.agents import (
    create_classic_mashup,
    create_stem_swap_mashup,
    create_energy_matched_mashup,
    create_adaptive_harmony_mashup,
    create_theme_fusion_mashup,
    create_semantic_aligned_mashup,
)

# Classic mashup (vocal A + instrumental B)
output_path = create_classic_mashup(
    vocal_id="taylor_swift_shake_it_off",
    inst_id="daft_punk_get_lucky",
    output_path="mashups/shake_it_lucky.mp3",
    quality="high",  # draft | high | broadcast
    output_format="mp3"  # mp3 | wav
)

# Stem swap (mix drums/bass/vocals from different songs)
output_path = create_stem_swap_mashup(
    stem_config={
        "vocals": "taylor_swift_shake_it_off",
        "drums": "daft_punk_get_lucky",
        "bass": "mark_ronson_uptown_funk"
    },
    quality="high"
)

# Energy-matched (dynamic section selection)
output_path = create_energy_matched_mashup(
    song_a_id="taylor_swift_shake_it_off",
    song_b_id="daft_punk_get_lucky"
)

# Adaptive harmony (auto-fix key clashes)
output_path = create_adaptive_harmony_mashup(
    song_a_id="taylor_swift_shake_it_off",
    song_b_id="daft_punk_get_lucky",
    max_pitch_shift_semitones=3
)

# Theme fusion (filter by lyrical theme)
output_path = create_theme_fusion_mashup(
    song_a_id="taylor_swift_shake_it_off",
    song_b_id="daft_punk_get_lucky",
    theme="celebration"
)

# Semantic-aligned (conversational structure)
output_path = create_semantic_aligned_mashup(
    song_a_id="taylor_swift_shake_it_off",
    song_b_id="daft_punk_get_lucky"
)
```

**Note:** All advanced mashups (energy-matched, adaptive harmony, theme fusion, semantic-aligned) require section-level metadata from the Analyst Agent.

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
- pyrubberband>=0.3.0 (time-stretching, Phase 3B+)
- torch>=2.0.0 (Demucs dependency)

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

### Current Blockers

1. **Blender assets required** - 8 .blend files needed to enable video generation (see `studio/assets/README.md`)
   - `avatar_base.blend` - DJ character with Rigify rig
   - `studio_default.blend` - DJ booth environment
   - 6 action clips in `actions/` folder

### Future Considerations

1. **YouTube TOS** - yt-dlp usage technically violates TOS (warn users, consider alternatives)
2. **Large installations** - PyTorch dependencies ~5GB total
3. **GPU memory** - Demucs peak usage ~8GB VRAM, fallback to CPU needed
4. **Cache management** - Need LRU eviction if library exceeds 50GB
5. **Video rendering time** - Studio module is bottleneck (2-5 min per 30s video)

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

### Test Coverage Summary

**Mixer Core:** 170+ unit tests
- Phase 1 (Memory): 47 tests - ID sanitization, metadata validation, ChromaDB, Camelot wheel
- Phase 2 (Ingestion): 22 tests - Local files, YouTube, cache, format conversion
- Phase 3A (Analyst): 10 tests - Section detection, energy/vocal analysis
- Phase 3B-3E (Engineer): 48 tests - All 8 mashup types, 93% coverage
- Phase 4 (Curator): 19 tests - Compatibility scoring, mashup recommendation, 94% coverage
- Phase 5 (Workflow): 25 tests - LangGraph state machine, error handling
- Integration: E2E workflow tests, CLI integration tests

**Crossfade Club:** 67 tests (63 unit + 4 integration)
- Director: themes, events, camera, safety
- Studio: asset_loader, renderer
- Encoder: platform, captions, thumbnail
- Batch: runner, pipeline integration

**Total: 237+ tests across all modules**

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

### ✅ Phase 3B: Simple Mashup Types (Completed 2026-01-19)

**Implemented:**
- `mixer/agents/engineer.py` (444 lines total) - Core mashup creation engine
- `create_classic_mashup()` (154 lines) - Vocal from song A + instrumental from song B
- `create_stem_swap_mashup()` (102 lines) - Mix stems from 3+ different songs
- Full audio processing pipeline: stem separation → time-stretching → alignment → mixing
- Quality presets (draft/high/broadcast) and output formats (mp3/wav)
- Comprehensive error handling and logging

**Test Results:**
- 16 unit tests (classic + stem swap), all passing ✅
- 97% code coverage on engineer.py
- Validates stretch ratio calculation, song loading, BPM matching, stem configuration

**Key Features:**
- Automatic BPM alignment via time-stretching (pyrubberband)
- First downbeat alignment for tight beat matching
- Configurable vocal attenuation for classic mashups
- Multi-song stem validation and combination

### ✅ Phase 3C: Energy-Based Mashups (Completed 2026-01-19)

**Implemented:**
- `mixer/audio/processing.py` additions: `pitch_shift()` and `calculate_semitone_shift()`
- `create_energy_matched_mashup()` (87 lines) - Dynamic section selection by energy curves
- `create_adaptive_harmony_mashup()` (71 lines) - Auto-fix key clashes via pitch-shifting
- Chromatic circle shortest-path algorithm for optimal key transposition
- Key normalization (handles "Cmaj", "C major", "CM" formats)

**Test Results:**
- 13 unit tests (pitch-shifting + 2 mashup types), all passing ✅
- 91% code coverage on engineer.py
- Validates semitone calculation, pitch-shifting, energy analysis, key compatibility

**Key Features:**
- Energy curve matching for climactic mashup structure
- Intelligent pitch-shifting (±6 semitones max for quality)
- Multiple key format support with normalization
- Requires section-level metadata from Phase 3A

### ✅ Phase 3D: Semantic Mashups (Completed 2026-01-19)

**Implemented:**
- `create_theme_fusion_mashup()` (186 lines) - Filter sections by lyrical themes
- `create_semantic_aligned_mashup()` (164 lines) - Meaning-driven structure with function pairing
- Lyrical function pairing logic: question→answer, narrative→reflection, hook→hook
- Case-insensitive theme matching with energy-based sorting
- Comprehensive logging for transparency in section selection

**Test Results:**
- 5 unit tests (2 mashup types), all passing ✅
- 92% code coverage on engineer.py
- Validates theme filtering, function pairing, section ordering

**Key Features:**
- Theme-based narrative construction
- Conversational flow via semantic function pairing
- Energy-aware section ordering for coherent flow
- Requires section-level semantic metadata from Phase 3A

**Overall Achievement:** 6 out of 8 total mashup types complete (75% of Phase 3 implementation).

---

### ✅ Phase 3E: Interactive Mashups (Completed 2026-01-19)

**Implemented:**
- `create_role_aware_mashup()` (217 lines) - Vocals shift between lead/harmony/call/response/texture
- `create_conversational_mashup()` (235 lines) - Songs talk to each other with dialogue-like flow
- `_process_vocal_by_role()` helper function with fallback for pitch-shift failures
- `word_timings` field in SongMetadata for future word-level enhancements
- Role assignment heuristics based on vocal density, intensity, and lyrical function

**Test Results:**
- 14 unit tests (2 mashup types + helper function), all passing ✅
- 93% code coverage on engineer.py (exceeds 90% target)
- 48 total engineer tests (all phases combined)
- Validates role processing, conversational pairing, silence gap insertion

**Key Features:**
- **Role-Aware**: Lead (full volume), Harmony (+3 semitones, -6dB), Call/Response (temporal spacing with silence), Texture (0.3x attenuation)
- **Conversational**: Configurable silence gaps (default 0.4s), question→answer/reflection pairing, warns if no pairs found
- **Section-level approach**: More stable than word-level, word_timings stored for future enhancement
- **Graceful degradation**: Fallback if pitch-shifting fails

**Overall Achievement:** 8 out of 8 total mashup types complete (100% of Phase 3 implementation). ✨

---

## Next Session Priorities

### Immediate: Acquire Remaining Blender Assets (7 remaining) 🔄

**Status:** IN PROGRESS (2026-01-27)

**Completed Assets (1/8):**
- ✅ `avatar_base.blend` (1.3 MB) - DJ character with working rig

**Session 12-13 Progress:**
- ✅ Decided on **Ultra-Budget path** ($0 - found free alternative)
- ✅ Found FREE DJ character on Sketchfab (saved $7 vs TurboSquid)
  - "Black Lowpoly Character Rigged for UE4" - rigged with Auto-Rig Pro
  - URL: https://sketchfab.com/3d-models/black-lowpoly-character-rigged-for-ue4-a76c754f01c44e36915b96609788168d
- ✅ Downloaded and extracted to `studio/assets/source/Black Character Rigged UE4/`
- ✅ Installed Blender 5.0.1
- ✅ Imported FBX into Blender, tested rig (bones move mesh correctly)
- ✅ Saved as `studio/assets/avatar_base.blend`

**Still Needed (7 assets):**
- `studio_default.blend` - DJ booth environment (search Sketchfab/BlendSwap)
- 6 animation clips from Mixamo (free):
  - `actions/idle_bob.blend`
  - `actions/deck_scratch_L.blend`
  - `actions/deck_scratch_R.blend`
  - `actions/crossfader_hit.blend`
  - `actions/drop_reaction.blend`
  - `actions/spotlight_present.blend`

**Recommended Next Steps:**
1. **Mixamo animations** (quickest) - Download 5-6 FBX clips from mixamo.com
2. **DJ booth** - Find free asset on Sketchfab or model simple version

**Research Reference:** See `docs/research/blender-assets/synthesis.md` for full tool recommendations

---

### Future Enhancements

**Crossfade Club v1.1:**
- Parallel platform encoding (~50% speedup)
- Asset upload interface in UI
- Video preview player
- Real-time rendering preview

**Crossfade Club v2.0:**
- Wardrobe system (outfit swapping)
- Props system (sunglasses, headphones, glow sticks)
- Multiple avatar characters
- Additional studio environments

---

## Handoff Documents

**Location:** `thoughts/shared/handoffs/general/`

- `2026-01-18_22-00_phase-0-foundation-complete.yaml` - Phase 0 completion
- `2026-01-19_05-33_phase-1-memory-system-complete.yaml` - Phase 1 completion
- `2026-01-19_15-52_phases-3b-3c-3d-complete.yaml` - Phases 2, 3A, 3B, 3C, 3D completion
- `2026-01-19_23-00_phase-3e-complete.yaml` - Phase 3E completion
- `2026-01-19_23-30_phase-4-complete.yaml` - Phase 4 (Curator Agent) completion
- `2026-01-20_00-00_phase-5-complete.yaml` - Phase 5 (LangGraph Workflow) completion
- `2026-01-20_01-00_phase-6-7-complete.yaml` - Phases 6-7 completion
- `2026-01-20_02-00_web-ui-complete.yaml` - Web UI addition
- `2026-01-20_crossfade-club-complete.yaml` - Crossfade Club implementation (4 phases, 48 files, 67 tests)
- `2026-01-20_ui-video-tab-integration.yaml` - Generate Video tab added to UI (disabled)
- `2026-01-20_project-cleanup.yaml` - Docs reorganization, cache cleanup
- `2026-01-20_documentation-update.yaml` - SETUP.md, README, CLAUDE.md updates
- `2026-01-21_blender-asset-research.yaml` - Multi-LLM asset research complete
- `2026-01-26_avatar-acquisition-started.yaml` - DJ character downloaded, Blender installed
- `2026-01-27_avatar-import-complete.yaml` - Avatar imported to Blender, rig tested, saved ⭐ (Latest)

**Format:** YAML with sections: goal, done_this_session, blockers, decisions, findings, worked, failed, next

---

## Project Resources

**Documentation:**
- `README.md` - User-facing documentation, quick start
- `PRD.md` - Complete product requirements (1360 lines)
- `CROSSFADE_CLUB_PRD.md` - Visual DJ system expansion PRD (35 sections)
- `UI_GUIDE.md` - Comprehensive web UI usage guide
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
**Pyrubberband:** Python wrapper for Rubber Band time-stretching library (pitch-preserving)
**Time-stretching:** Changing tempo without affecting pitch
**Pitch-shifting:** Changing pitch without affecting tempo
**Chromatic Circle:** 12-tone arrangement for calculating shortest key transposition path
**Lyrical Function:** Semantic role of lyrics (question, answer, narrative, reflection, hook)
**Energy Curve:** RMS energy over time, used for dynamic section selection
**Stem:** Isolated instrument/vocal track (vocals, drums, bass, other)

---

*This ledger is updated at each major milestone. For session details, see handoff documents in `thoughts/shared/handoffs/general/`*
