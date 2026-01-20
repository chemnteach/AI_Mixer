# The Mixer 🎵

An intelligent audio mashup pipeline that uses semantic understanding (not just BPM/key) to discover and create musical mashups.

## Status

**Phase 0: Foundation ✅ COMPLETE**

The project foundation is established with:
- Directory structure and package organization
- Configuration management system
- Logging infrastructure
- CLI skeleton with Click
- Type definitions
- Development environment setup

**Phase 1: Memory System ✅ COMPLETE**

ChromaDB integration fully implemented with:
- ID sanitization and metadata validation
- Persistent ChromaDB client with singleton pattern
- Harmonic matching (BPM + key compatibility)
- Semantic matching (mood, genre, vibe)
- Hybrid matching (recommended: combines harmonic + semantic)
- Comprehensive test suite (47 unit tests)

**Phase 2: Ingestion Agent ✅ COMPLETE**

Audio ingestion from local files and YouTube:
- Local file support (WAV, MP3, FLAC)
- YouTube download via yt-dlp
- Format conversion to standard WAV
- Cache checking and deduplication
- Comprehensive test suite (22 unit tests)

**Phase 3A: Enhanced Analyst Agent ✅ COMPLETE**

Section-level metadata extraction (foundation for advanced mashups):
- Section detection (verse/chorus/bridge boundaries)
- Energy analysis per section (RMS, spectral centroid, tempo stability)
- Vocal analysis (density, intensity, lyric extraction)
- Semantic analysis via LLM (emotional tone, themes, function)
- Emotional arc generation
- Comprehensive test suite (10 unit tests)

**Phase 3B-3E: All 8 Mashup Types ✅ COMPLETE**

All mashup creation strategies implemented with comprehensive test coverage:
- **Simple:** Classic (vocal+instrumental), Stem Swap (instrument exchange)
- **Energy-Based:** Energy Matched (intensity alignment), Adaptive Harmony (dynamic mixing)
- **Semantic:** Theme Fusion (lyrical coherence), Semantic-Aligned (emotional arcs)
- **Interactive:** Role-Aware (Q&A vocal dynamics), Conversational (dialogue flow)
- Comprehensive test suite (70+ unit tests, 98% coverage)

**Phase 4: Curator Agent ✅ COMPLETE**

Intelligent song pairing with multi-criteria compatibility scoring:
- Weighted compatibility (BPM 35%, key 30%, energy 20%, genre 15%)
- Mashup type recommendation with confidence scoring
- Batch pair discovery across entire library
- Comprehensive test suite (19 unit tests, 94% coverage)

**Phase 5: LangGraph Workflow ✅ COMPLETE**

State machine orchestration for end-to-end mashup creation:
- Conditional routing (auto-match vs manual pairing)
- Human-in-the-loop approval points with auto-fallback
- Progress tracking and streaming output
- Error recovery and retry logic
- Comprehensive test suite (25 unit tests, 68-100% coverage)

**Phase 6: CLI Refinement ✅ COMPLETE**

Production-ready command-line interface with rich formatting:
- All core commands: ingest, analyze, match, mashup
- Library management: list, search, stats
- Automated workflow: auto command (one-step mashup)
- Interactive mode: guided workflow with prompts
- Rich progress bars, tables, and panels

**Phase 7: Testing & QA ✅ COMPLETE**

Comprehensive test coverage and performance validation:
- Integration tests for end-to-end workflows
- CLI integration tests for all commands
- Performance benchmarking script
- 170+ total unit tests with 85%+ average coverage

**Status: Production Ready** 🚀

## Quick Start

### Prerequisites

**System Dependencies:**
- Python 3.9+
- ffmpeg
- libsndfile (optional but recommended)

Check dependencies:
```bash
# Linux/Mac
bash scripts/check_dependencies.sh

# Windows
scripts\check_dependencies.bat
```

### Installation

1. **Clone the repository:**
```bash
git clone <repo-url>
cd AI_Mixer
```

2. **Create virtual environment:**
```bash
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

3. **Install Python packages:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.template .env
# Edit .env and add your API keys:
# - ANTHROPIC_API_KEY
# - OPENAI_API_KEY
```

### Usage

**Web UI (Recommended for ease of use):**
```bash
# Install UI dependencies
pip install streamlit

# Launch web interface
streamlit run mixer_ui.py

# Opens in browser at http://localhost:8501
```

The web UI provides:
- 🎵 **Create Mashup:** Upload songs, select mashup type, auto-matching
- 📚 **Library Management:** Browse, search, ingest, analyze songs
- ⚙️ **Settings:** View configuration and system stats
- 🎨 **8 Mashup Types:** All types accessible via dropdown
- 📊 **Visual Stats:** Genre/key distribution, library analytics

**CLI - Fully Automated Workflow:**
```bash
# One-step mashup creation with auto-matching
python -m mixer auto path/to/song.mp3

# Interactive mode with guided prompts
python -m mixer interactive
```

**Manual Workflow:**
```bash
# 1. Ingest audio files or YouTube URLs
python -m mixer ingest https://youtube.com/watch?v=...
python -m mixer ingest path/to/song.mp3

# 1b. Batch ingest from folder (perfect for CD rips!)
python -m mixer ingest --folder "C:\Users\YourName\Music\New Rips"
python -m mixer ingest --folder "C:\Users\YourName\Music\New Rips" --analyze

# 1c. Batch ingest from YouTube playlist (perfect for curated collections!)
python -m mixer ingest --playlist "https://www.youtube.com/playlist?list=PLxxxxxxx"
python -m mixer ingest --playlist "https://www.youtube.com/playlist?list=PLxxxxxxx" --max 20 --analyze

# 2. Analyze songs (extracts BPM, key, lyrics, mood, sections)
python -m mixer analyze <song-id>
python -m mixer analyze --batch  # Analyze all unanalyzed songs

# 3. Find compatible matches
python -m mixer match <song-id> --criteria hybrid --top 5

# 4. Create mashup
python -m mixer mashup <song-a> <song-b> --type classic
python -m mixer mashup <song-a> <song-b> --type conversational
```

**Library Management:**
```bash
# List all songs
python -m mixer library list

# Search library
python -m mixer library search "upbeat country"

# Show statistics
python -m mixer library stats
```

**Available Mashup Types:**
- `classic` - Vocal from A + instrumental from B
- `stem-swap` - Swap specific instruments between songs
- `energy` - Match energy levels across sections
- `adaptive` - Dynamic mixing based on energy curves
- `theme` - Align songs by lyrical themes
- `semantic` - Match emotional arcs
- `role-aware` - Q&A vocal dynamics
- `conversational` - Dialogue-style vocal flow

**Help:**
```bash
python -m mixer --help
python -m mixer mashup --help  # Command-specific help
```

### Testing the Memory System

**Run the interactive demo:**
```bash
python scripts/test_memory_demo.py
```

This demo script:
- Initializes ChromaDB with sample songs
- Demonstrates harmonic matching (BPM + key)
- Shows semantic matching (mood + vibe)
- Tests hybrid matching (recommended)
- Displays collection statistics

**Run unit tests:**
```bash
pytest tests/unit/test_memory.py -v
```

## Project Structure

```
AI_Mixer/
├── mixer/              # Main package
│   ├── agents/         # 4 main agents (Ingestion, Analyst, Curator, Engineer)
│   ├── audio/          # Audio processing (librosa, whisper, demucs)
│   ├── memory/         # ChromaDB interface
│   ├── llm/            # LLM integration (Anthropic, OpenAI)
│   ├── workflow/       # LangGraph orchestration
│   ├── utils/          # Utilities (logging, validation, etc.)
│   ├── cli.py          # Command-line interface
│   └── config.py       # Configuration management
├── mixer_ui.py         # Streamlit web interface (600+ lines)
├── tests/              # Unit and integration tests
├── scripts/            # Setup and utility scripts
├── config.yaml         # User configuration
├── requirements.txt    # Python dependencies
└── PRD.md              # Product Requirements Document
```

## Features

### Core Capabilities
- **Source Agnostic:** YouTube URLs or local audio files
- **Semantic Matching:** Find songs by mood, genre, and vibe (not just BPM)
- **Hybrid Search:** Combines harmonic (BPM/key) + semantic (mood/lyrics) matching
- **Intelligent Memory:** ChromaDB stores metadata and enables fast retrieval
- **8 Mashup Types:** From simple vocal swaps to AI-powered conversational mashups
- **Broadcast Quality:** Professional-grade stem separation and mixing
- **Automated Workflow:** One-command mashup creation with intelligent pairing
- **Interactive Mode:** Guided workflow with user prompts and approvals

### 8 Mashup Types

**Simple Mashups:**
- **Classic:** Vocal from song A over instrumental from song B
- **Stem Swap:** Exchange specific instruments between two songs

**Energy-Based Mashups:**
- **Energy Matched:** Align sections by energy level (intro→intro, verse→verse)
- **Adaptive Harmony:** Dynamic mixing based on energy curves and transitions

**Semantic Mashups:**
- **Theme Fusion:** Align songs by lyrical themes and narrative structure
- **Semantic-Aligned:** Match emotional arcs across both songs

**Interactive Mashups:**
- **Role-Aware:** Question-and-answer vocal dynamics
- **Conversational:** Dialogue-style vocal flow between songs

### Workflow
1. **Ingestion Agent:** Download/cache audio from any source
2. **Analyst Agent:** Extract BPM, key, lyrics, genre, mood, section boundaries
3. **Curator Agent:** Find compatible song pairs using hybrid matching
4. **Engineer Agent:** Build final mashup with stem separation and alignment
5. **LangGraph Orchestration:** Automated workflow with conditional routing

## Configuration

Edit `config.yaml` to customize:
- Audio quality settings (sample rate, bit depth)
- Model choices (Whisper size, Demucs model)
- LLM providers (Anthropic vs OpenAI)
- Matching criteria (BPM tolerance, stretch ratio)
- Performance settings (GPU, concurrent downloads)

## Development

**Run tests:**
```bash
pytest tests/ -v --cov=mixer
```

**Code formatting:**
```bash
black mixer/ tests/
```

**Type checking:**
```bash
mypy mixer/
```

## Legal Notice

The Mixer is intended for:
- Educational purposes (learning audio processing, ML)
- Personal use (non-commercial experimentation)
- Fair use (research, commentary, parody)

**Users are responsible for:**
- Ensuring they have rights to process audio
- Complying with YouTube Terms of Service
- Not distributing copyrighted mashups without permission

**Recommended sources:** Creative Commons music, royalty-free libraries, personal recordings, public domain works.

## License

MIT License - See LICENSE file for details

## Documentation

- **PRD.md:** Complete product requirements and technical specifications
- **Implementation Plan:** See PRD.md Appendix for phased rollout strategy

## Roadmap

- [x] Phase 0: Foundation ✅
- [x] Phase 1: Memory System ✅
- [x] Phase 2: Ingestion Agent ✅
- [x] Phase 3A: Enhanced Analyst Agent (section-level metadata) ✅
- [x] Phase 3B: Simple Mashup Types (Classic, Stem Swap) ✅
- [x] Phase 3C: Energy-Based Mashups (Energy Match, Adaptive Harmony) ✅
- [x] Phase 3D: Semantic Mashups (Theme Fusion, Semantic-Aligned) ✅
- [x] Phase 3E: Interactive Mashups (Role-Aware, Conversational) ✅
- [x] Phase 4: Curator Agent ✅
- [x] Phase 5: LangGraph Workflow ✅
- [x] Phase 6: CLI Refinement ✅
- [x] Phase 7: Testing & QA ✅

**Status:** All 7 phases complete. The Mixer is production ready with 170+ unit tests, comprehensive integration tests, and 8 AI-powered mashup types.
