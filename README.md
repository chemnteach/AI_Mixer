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

**Next: Phase 3B - Simple Mashup Types**

**Future Vision (Phase 3+):** 8 advanced mashup types including conversational mashups, semantic-aligned structures, and role-aware vocal recomposition. See `thoughts/shared/plans/advanced-mashup-types-roadmap.md` for full vision.

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

**CLI Commands (coming soon):**
```bash
# Ingest audio
python -m mixer ingest <youtube-url-or-file>

# Analyze songs
python -m mixer analyze --batch

# Find matches
python -m mixer match <song-id> --criteria hybrid

# Create mashup
python -m mixer mashup <vocal-id> <instrumental-id>

# Library management
python -m mixer library list
python -m mixer library search "upbeat country"

# Fully automated workflow
python -m mixer auto <input-source>
```

**Help:**
```bash
python -m mixer --help
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
│   ├── utils/          # Utilities (logging, validation, etc.)
│   ├── cli.py          # Command-line interface
│   └── config.py       # Configuration management
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
- **Broadcast Quality:** Professional-grade stem separation and mixing

### Workflow
1. **Ingestion Agent:** Download/cache audio from any source
2. **Analyst Agent:** Extract BPM, key, lyrics, genre, mood
3. **Curator Agent:** Find compatible song pairs using hybrid matching
4. **Engineer Agent:** Build final mashup with stem separation and alignment

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

- [x] Phase 0: Foundation (COMPLETE)
- [x] Phase 1: Memory System (COMPLETE)
- [ ] Phase 2: Ingestion Agent (IN PROGRESS)
- [ ] Phase 3A: Enhanced Analyst Agent (section-level metadata)
- [ ] Phase 3B: Simple Mashup Types (Classic, Stem Swap)
- [ ] Phase 3C: Energy-Based Mashups (Energy Match, Adaptive Harmony)
- [ ] Phase 3D: Semantic Mashups (Theme Fusion, Semantic-Aligned)
- [ ] Phase 3E: Interactive Mashups (Role-Aware, Conversational)
- [ ] Phase 4: Curator Agent
- [ ] Phase 5: LangGraph Workflow
- [ ] Phase 6: CLI Refinement
- [ ] Phase 7: Testing & QA

**Current Focus:** Phase 2 (Ingestion Agent)
**Advanced Vision:** 8 AI-powered mashup types (see roadmap in `thoughts/shared/plans/`)
