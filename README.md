# The Mixer 🎵 + Crossfade Club 🎬

An intelligent audio mashup pipeline with automated video generation featuring an animated DJ avatar.

---

## Status

### The Mixer (Audio Pipeline) - Production Ready ✅

**Phase 0-7: Complete** 🚀

- ✅ **Phase 0:** Foundation (directory structure, config, logging, CLI)
- ✅ **Phase 1:** Memory System (ChromaDB, harmonic/semantic/hybrid matching, 47 tests)
- ✅ **Phase 2:** Ingestion Agent (local files + YouTube, 22 tests)
- ✅ **Phase 3A:** Enhanced Analyst Agent (section-level metadata, 10 tests)
- ✅ **Phase 3B-3E:** All 8 Mashup Types (70+ tests, 98% coverage)
- ✅ **Phase 4:** Curator Agent (compatibility scoring, 19 tests, 94% coverage)
- ✅ **Phase 5:** LangGraph Workflow (state machine orchestration, 25 tests)
- ✅ **Phase 6:** CLI Refinement (production-ready interface)
- ✅ **Phase 7:** Testing & QA (170+ unit tests, integration tests, benchmarking)

### Crossfade Club (Video Pipeline) - Implementation Complete ✅

**All 4 Phases Delivered** 🎬

- ✅ **Phase 1:** Director Agent (visual intelligence, timeline generation, 23 tests)
- ✅ **Phase 2:** Studio Module (Blender 3D integration, 16 tests)
- ✅ **Phase 3:** Encoder Module (FFmpeg platform variants, 20 tests)
- ✅ **Phase 4:** Batch Runner (end-to-end orchestration, 8 tests)

**Total:** 48 new files, 67 tests passing, 100% pass rate

**Note:** Video generation requires Blender animation assets (8 .blend files) - see `studio/assets/README.md` for specifications. Feature is fully implemented but disabled in UI until assets are ready.

---

## What Is This?

### The Mixer (Audio)

Intelligent audio mashup creation using AI-powered semantic matching. Unlike traditional DJ tools that only match BPM and key, The Mixer understands **mood, genre, themes, and emotional arcs** to create mashups that actually make sense together.

**8 Mashup Types:**
- **Simple:** Classic, Stem Swap
- **Energy-Based:** Energy Matched, Adaptive Harmony
- **Semantic:** Theme Fusion, Semantic-Aligned
- **Interactive:** Role-Aware, Conversational

### Crossfade Club (Video)

Automated video production system that converts audio mashups into platform-optimized social media content with an animated DJ avatar.

**Pipeline:** Audio → Director Agent (timeline) → Blender (3D render) → FFmpeg (platform variants)

**Output:** TikTok (9:16), Reels (9:16), Shorts (9:16), YouTube (16:9), thumbnail

**Themes:** sponsor_neon, award_elegant, mashup_chaos, chill_lofi

---

## Quick Start

### Prerequisites

**System Dependencies:**
- **Python 3.9+** (required)
- **ffmpeg** (required - audio conversion + video encoding)
- **libsndfile** (optional but recommended - audio I/O)
- **Blender 3.6+** (optional - only for video generation)

**Check dependencies:**
```bash
# Linux/Mac
bash scripts/check_dependencies.sh

# Windows
scripts\check_dependencies.bat
```

**Installation:**
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg libsndfile1
sudo snap install blender --classic

# macOS
brew install ffmpeg libsndfile
brew install --cask blender

# Windows
# Download from ffmpeg.org and blender.org
```

### Installation

1. **Clone and setup:**
```bash
git clone <repo-url>
cd AI_Mixer
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure API keys:**
```bash
cp .env.template .env
# Edit .env and add:
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
```

### Usage

#### Web UI (Recommended)

```bash
streamlit run mixer_ui.py
# Opens at http://localhost:8501
```

**4 Tabs:**
- **🎵 Create Mashup:** Upload songs, auto-match, 8 mashup types
- **📚 Library:** Browse, search, ingest (file/YouTube/folder/playlist), analyze
- **🎬 Generate Video:** Crossfade Club interface (disabled pending assets)
- **⚙️ Settings:** View configuration

#### CLI - Audio Mashups

**Automated workflow:**
```bash
# One-step mashup creation
python -m mixer auto path/to/song.mp3

# Interactive mode with prompts
python -m mixer interactive
```

**Manual workflow:**
```bash
# 1. Ingest audio
python -m mixer ingest https://youtube.com/watch?v=...
python -m mixer ingest path/to/song.mp3

# Batch ingest from folder
python -m mixer ingest --folder "C:\Music\New Rips" --analyze

# Batch ingest from YouTube playlist
python -m mixer ingest --playlist "https://youtube.com/playlist?list=..." --max 20

# 2. Analyze (extracts BPM, key, lyrics, sections)
python -m mixer analyze <song-id>
python -m mixer analyze --batch

# 3. Find matches
python -m mixer match <song-id> --criteria hybrid --top 5

# 4. Create mashup
python -m mixer mashup <song-a> <song-b> --type classic
```

**Library management:**
```bash
python -m mixer library list
python -m mixer library search "upbeat country"
python -m mixer library stats
```

#### CLI - Video Generation

**Generate platform variants from audio:**
```bash
# All platforms with default theme
python run_batch.py --audio mashups/test.wav --song-id test_song

# Specific platforms only
python run_batch.py --audio mashups/test.wav --song-id test_song --platforms tiktok youtube

# Different theme
python run_batch.py --audio mashups/test.wav --song-id test_song --theme mashup_chaos

# Skip Blender (use existing render)
python run_batch.py --audio mashups/test.wav --song-id test_song --skip-studio
```

**Performance benchmark:**
```bash
python scripts/benchmark_pipeline.py --audio mashups/test.wav --song-id test_song --iterations 3
```

---

## Project Structure

```
AI_Mixer/
├── mixer/                  # Audio pipeline (Phases 1-7)
│   ├── agents/             # Ingestion, Analyst, Curator, Engineer
│   ├── audio/              # Audio processing (librosa, whisper, demucs)
│   ├── memory/             # ChromaDB interface
│   ├── llm/                # LLM integration (Anthropic, OpenAI)
│   ├── workflow/           # LangGraph orchestration
│   ├── utils/              # Utilities
│   ├── cli.py              # CLI interface
│   └── config.py           # Configuration management
│
├── director/               # Crossfade Club - Visual Intelligence
│   ├── timeline.py         # Generate timeline.json from audio
│   ├── events.py           # Audio moments → visual triggers
│   ├── camera.py           # Energy-driven camera paths
│   ├── themes.py           # Load theme configs
│   └── safety.py           # Event-safe validation
│
├── studio/                 # Crossfade Club - Blender Integration
│   ├── renderer.py         # Subprocess orchestration
│   ├── asset_loader.py     # Validate .blend assets
│   ├── blender_scripts/    # Runs INSIDE Blender
│   └── assets/             # USER-PROVIDED (8 .blend files)
│
├── encoder/                # Crossfade Club - FFmpeg Encoding
│   ├── platform.py         # Platform-specific variants
│   ├── captions.py         # Burn-in captions
│   └── thumbnail.py        # Extract thumbnails
│
├── batch/                  # Crossfade Club - Orchestration
│   └── runner.py           # Director → Studio → Encoder
│
├── config/
│   ├── themes/             # 4 visual themes (YAML)
│   └── captions.yaml       # Caption styles per platform
│
├── tests/                  # 170+ tests (Mixer + Crossfade Club)
├── scripts/                # Setup, testing, benchmarking
├── docs/                   # Documentation
│   ├── crossfade-club/     # Crossfade Club PRD and summary
│   └── archive/            # Historical docs
│
├── mixer_ui.py             # Streamlit web interface (1066 lines)
├── run_batch.py            # Crossfade Club CLI entry point
├── config.yaml             # User configuration
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── CLAUDE.md               # Developer guide (for AI assistants)
├── UI_GUIDE.md             # Comprehensive UI guide
└── SETUP.md                # New machine setup instructions
```

---

## Features

### Audio Pipeline (The Mixer)

**Core Capabilities:**
- **Source Agnostic:** YouTube URLs or local audio files
- **Semantic Matching:** Find songs by mood, genre, vibe (not just BPM)
- **Hybrid Search:** Combines harmonic (BPM/key) + semantic (mood/lyrics)
- **ChromaDB Memory:** Fast metadata storage and retrieval
- **8 Mashup Types:** Simple to AI-powered conversational mashups
- **Broadcast Quality:** Professional stem separation (Demucs)
- **Automated Workflow:** One-command mashup creation
- **Interactive Mode:** Guided workflow with approvals

**8 Mashup Types:**

| Type | Description | Use Case |
|------|-------------|----------|
| **Classic** | Vocal from A + instrumental from B | Traditional mashup |
| **Stem Swap** | Exchange instruments between songs | Creative remixing |
| **Energy Matched** | Align sections by energy level | High-energy mixes |
| **Adaptive Harmony** | Dynamic mixing with transitions | Smooth blending |
| **Theme Fusion** | Align by lyrical themes | Storytelling mashups |
| **Semantic-Aligned** | Match emotional arcs | Emotional journeys |
| **Role-Aware** | Q&A vocal dynamics | Call-and-response |
| **Conversational** | Dialogue-style flow | Songs talking to each other |

### Video Pipeline (Crossfade Club)

**Pipeline Stages:**
1. **Director Agent** - Translates audio metadata into visual timeline
2. **Studio Module** - Renders 3D animated DJ avatar with Blender
3. **Encoder Module** - Creates platform-specific variants with FFmpeg

**Output Formats:**

| Platform | Resolution | Aspect Ratio | Bitrate | Captions |
|----------|-----------|--------------|---------|----------|
| **TikTok** | 1080×1920 | 9:16 | 5M | Burned-in |
| **Reels** | 1080×1920 | 9:16 | 5M | Burned-in |
| **Shorts** | 1080×1920 | 9:16 | 5M | Burned-in |
| **YouTube** | 1920×1080 | 16:9 | 8M | Soft subtitles |
| **Thumbnail** | 1280×720 | 16:9 | - | - |

**Visual Themes:**
- **sponsor_neon** - High-energy neon lights with strobes
- **award_elegant** - Sophisticated event-safe theme
- **mashup_chaos** - Maximum visual mayhem
- **chill_lofi** - Relaxed downtempo vibes

**Event Detection:**
- Drops (energy spikes trigger visual reactions)
- Section changes (verse→chorus transitions)
- Retention nudges (periodic engagement)
- Camera movements (zoom, pan, nudge)

**Performance:** 3-7 minutes per 30-second video (Blender rendering is bottleneck)

---

## Configuration

Edit `config.yaml` to customize:

**Audio Settings:**
- Sample rate, bit depth, channels
- Quality presets

**Model Settings:**
- Whisper model size (tiny/base/small/medium/large)
- Demucs model
- LLM provider (Anthropic/OpenAI)
- Claude/GPT model selection

**Curator Settings:**
- BPM tolerance, max stretch ratio
- Weight factors (BPM 35%, key 30%, energy 20%, genre 15%)

**Crossfade Club Settings:**
- Director: Theme, event detection thresholds
- Studio: Blender executable, render timeout, FPS
- Encoder: Platform settings, codecs, bitrates

---

## Testing

**Run all tests:**
```bash
# Mixer + Crossfade Club (170+ tests)
pytest tests/ -v --cov=mixer --cov=director --cov=studio --cov=encoder --cov=batch
```

**Module-specific tests:**
```bash
# Mixer modules
pytest tests/unit/test_memory.py -v
pytest tests/unit/test_analyst.py -v
pytest tests/unit/test_curator.py -v

# Crossfade Club modules
pytest tests/director/ -v
pytest tests/studio/ -v
pytest tests/encoder/ -v
pytest tests/batch/ -v

# Integration tests
pytest tests/integration/ -v
```

**Interactive demo:**
```bash
python scripts/test_memory_demo.py
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| **README.md** | This file - quick start and overview |
| **SETUP.md** | Comprehensive new machine setup guide |
| **CLAUDE.md** | Developer guide for AI assistants |
| **UI_GUIDE.md** | Streamlit UI usage guide |
| **docs/crossfade-club/CROSSFADE_CLUB_PRD.md** | Video system product requirements (35 sections) |
| **docs/crossfade-club/CROSSFADE_CLUB_COMPLETE.md** | Implementation summary |
| **director/README.md** | Director Agent documentation |
| **studio/assets/README.md** | Blender asset specifications |
| **batch/README.md** | Batch pipeline documentation |

---

## Legal Notice

**The Mixer** is intended for:
- Educational purposes (learning audio processing, ML, video generation)
- Personal use (non-commercial experimentation)
- Fair use (research, commentary, parody)

**Users are responsible for:**
- Ensuring they have rights to process audio/video
- Complying with YouTube Terms of Service
- Not distributing copyrighted content without permission
- Respecting platform-specific content policies (TikTok, Instagram, YouTube)

**Recommended sources:** Creative Commons music, royalty-free libraries, personal recordings, public domain works.

---

## Development

**Code formatting:**
```bash
black mixer/ director/ studio/ encoder/ batch/ tests/
```

**Type checking:**
```bash
mypy mixer/ director/ studio/ encoder/ batch/
```

**Performance benchmarking:**
```bash
# Mixer workflow
python scripts/benchmark.py

# Crossfade Club pipeline
python scripts/benchmark_pipeline.py --audio test.wav --song-id test --iterations 3
```

---

## Roadmap

### Mixer (Audio Pipeline) - Complete ✅

- [x] Phase 0: Foundation
- [x] Phase 1: Memory System
- [x] Phase 2: Ingestion Agent
- [x] Phase 3A-3E: All 8 Mashup Types
- [x] Phase 4: Curator Agent
- [x] Phase 5: LangGraph Workflow
- [x] Phase 6: CLI Refinement
- [x] Phase 7: Testing & QA

### Crossfade Club (Video Pipeline) - Complete ✅

- [x] Phase 1: Director Agent (visual intelligence)
- [x] Phase 2: Studio Module (Blender integration)
- [x] Phase 3: Encoder Module (FFmpeg platform variants)
- [x] Phase 4: Batch Runner (orchestration)

### Future Enhancements

**Short-term (v1.1):**
- Parallel platform encoding (~50% speedup)
- Asset template library (starter .blend files)
- Real-time rendering preview
- Web UI progress indicators for video generation

**Long-term (v2.0):**
- Wardrobe system (avatar outfit swapping)
- Props system (sunglasses, headphones, glow sticks)
- Multiple avatar characters
- Additional studio environments
- Custom animation action library

---

## License

MIT License - See LICENSE file for details

---

## Acknowledgments

Built with:
- **ChromaDB** - Vector database for semantic search
- **librosa** - Audio analysis
- **Whisper** - Lyric transcription
- **Demucs** - Stem separation
- **LangGraph** - Workflow orchestration
- **Anthropic Claude** - Semantic analysis
- **Streamlit** - Web interface
- **Blender** - 3D animation rendering
- **FFmpeg** - Video encoding

---

**Status:** Production ready with 240+ tests and comprehensive documentation. Audio mashup pipeline fully operational. Video generation pipeline implemented and ready for asset integration.
