# Setup Checklist for New Machine

Beyond the standard git clone, here's what you need for The Mixer + Crossfade Club.

---

## 1. Python Virtual Environment (Not in Git)

```bash
cd AI_Mixer
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

---

## 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note:** This is ~5GB due to PyTorch (required for Demucs/Whisper). First install will take a few minutes.

---

## 3. API Keys (Not in Git)

```bash
cp .env.template .env
# Edit .env and add:
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
```

**Required for:**
- Analyst Agent (LLM-based semantic analysis)
- Curator Agent (compatibility scoring)

---

## 4. System Dependencies

### Check What's Installed

```bash
# Linux/Mac
bash scripts/check_dependencies.sh

# Windows
scripts\check_dependencies.bat
```

### Required Dependencies

| Tool | Purpose | Required For |
|------|---------|--------------|
| **ffmpeg** | Audio conversion, video encoding | Mixer + Crossfade Club (critical) |
| **libsndfile** | Audio I/O | Mixer (recommended) |
| **Blender 3.6+** | 3D animation rendering | Crossfade Club video generation (optional) |

### Installation

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg libsndfile1
sudo snap install blender --classic
```

**macOS:**
```bash
brew install ffmpeg libsndfile
brew install --cask blender
```

**Windows:**
- **ffmpeg**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- **Blender**: Download from [blender.org](https://www.blender.org/download/)

### Verify Installation

```bash
ffmpeg -version
blender --version
```

---

## 5. Git Configuration

Set your identity on the new machine:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## 6. ChromaDB Starts Fresh (Gitignored)

The `./chroma_db/` directory is gitignored, so:
- You'll start with an empty library on the new machine
- This is intentional (audio data is local, not committed)
- Test with: `python scripts/test_memory_demo.py` to populate sample data

### Other Gitignored Directories (Auto-Created)

| Directory | Purpose |
|-----------|---------|
| `library_cache/` | Cached audio files from ingestion |
| `mashups/` | Generated mashup outputs (Mixer) |
| `outputs/timeline/` | Timeline.json files (Crossfade Club Director) |
| `outputs/blender_temp/` | Raw Blender renders (Crossfade Club Studio) |
| `outputs/renders/` | Platform video variants (Crossfade Club Encoder) |
| `outputs/manifests/` | Event-safe usage manifests (Crossfade Club) |
| `studio/assets/` | User-provided Blender .blend files (optional) |
| `logs/` | Log files |

---

## 7. Blender Assets (Optional - For Video Generation)

The Crossfade Club video generation feature requires 8 Blender asset files:

```
studio/assets/
├── avatar_base.blend           # Base DJ character model
├── studio_default.blend        # DJ booth environment
└── actions/
    ├── idle_bob.blend         # Idle head bob animation
    ├── deck_scratch_L.blend   # Left deck scratch
    ├── deck_scratch_R.blend   # Right deck scratch
    ├── crossfader_hit.blend   # Crossfader movement
    ├── drop_reaction.blend    # Drop reaction animation
    └── spotlight_present.blend # Presenting to camera
```

**Status:** Not yet available - feature is implemented but disabled in UI until assets are ready.

**Documentation:** See `studio/assets/README.md` for detailed asset specifications.

---

## 8. Platform-Specific Notes

### Windows

- Line endings warnings are normal (CRLF vs LF) - can ignore
- Use `venv\Scripts\activate` (backslashes)
- Use `scripts\check_dependencies.bat`

### Linux/Mac

- Use `source venv/bin/activate`
- Use `bash scripts/check_dependencies.sh`
- May need `sudo` for system package installs

---

## 9. Verify Setup

### Basic Verification

```bash
# 1. Test memory system
python scripts/test_memory_demo.py

# 2. Run unit tests (Mixer)
pytest tests/unit/test_memory.py -v
pytest tests/unit/test_ingestion.py -v

# 3. Check CLI
python -m mixer --help
```

### Crossfade Club Verification

```bash
# 4. Test Director Agent (timeline generation)
pytest tests/director/ -v

# 5. Test Studio Module (Blender integration - requires Blender)
pytest tests/studio/ -v

# 6. Test Encoder Module (FFmpeg platform variants)
pytest tests/encoder/ -v

# 7. Test Batch Runner (end-to-end pipeline)
pytest tests/batch/ -v

# 8. Integration tests (requires full setup)
pytest tests/integration/test_pipeline.py -v -s
```

### Run All Tests

```bash
# Complete test suite (170+ tests)
pytest tests/ -v --cov=mixer --cov=director --cov=studio --cov=encoder --cov=batch
```

### Launch Web UI

```bash
streamlit run mixer_ui.py
# Opens browser at http://localhost:8501
```

---

## Quick Setup Script

Here's everything in one go:

```bash
# Clone and enter
git clone https://github.com/yourusername/AI_Mixer.git
cd AI_Mixer

# Setup Python
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Setup config
cp .env.template .env
# Edit .env and add your API keys

# Verify Mixer
python scripts/test_memory_demo.py
pytest tests/unit/test_memory.py -v
python -m mixer --help

# Verify Crossfade Club (optional - requires Blender + FFmpeg)
pytest tests/director/ -v
pytest tests/encoder/ -v

# Launch UI
streamlit run mixer_ui.py
```

---

## What's Different on Fresh Clone

| Item | Status | Notes |
|------|--------|-------|
| **Python code** | ✅ In git | All modules (mixer, director, studio, encoder, batch) |
| **Config files** | ✅ In git | config.yaml, theme YAMLs, caption YAML |
| **Tests** | ✅ In git | 170+ unit + integration tests |
| **Documentation** | ✅ In git | docs/crossfade-club/, README, UI_GUIDE, CLAUDE.md |
| **Virtual env** | ❌ Gitignored | Create fresh with `python -m venv venv` |
| **Dependencies** | ❌ Not included | Install with `pip install -r requirements.txt` |
| **ChromaDB** | ❌ Gitignored | Empty library - ingest songs to populate |
| **Audio cache** | ❌ Gitignored | library_cache/ starts empty |
| **Outputs** | ❌ Gitignored | outputs/ directory created on first run |
| **Blender assets** | ❌ Gitignored | User-provided - see studio/assets/README.md |
| **API keys** | ❌ Gitignored | Copy .env.template → .env and add keys |
| **System tools** | ❌ Not included | Install ffmpeg, Blender separately |

---

## Feature Availability on New Machine

### Immediately Available (After pip install)

✅ Audio ingestion (local files + YouTube)
✅ Library management
✅ Song analysis (metadata extraction)
✅ Semantic matching
✅ All 8 mashup types
✅ CLI (`python -m mixer`)
✅ Streamlit UI (`streamlit run mixer_ui.py`)
✅ Director Agent (timeline generation)
✅ Encoder Module (platform variants)

### Requires Additional Setup

⚙️ **LLM Analysis** - Add API keys to `.env`
⚙️ **Video Rendering** - Install Blender 3.6+
⚙️ **Video Generation** - Add Blender assets to `studio/assets/`

---

## Troubleshooting

### "ffmpeg not found"

- Install ffmpeg and ensure it's on PATH
- Verify: `ffmpeg -version`

### "Blender not found"

- Install Blender 3.6+ and ensure it's on PATH
- Verify: `blender --version`
- Only needed for video generation

### "Module not found" errors

- Activate virtual environment: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

### Empty library after clone

- This is normal - ChromaDB is gitignored
- Ingest songs: `python -m mixer ingest <file-or-url>`
- Or use Streamlit UI "Ingest" tab

### Video generation disabled in UI

- Expected - Blender assets not yet available
- Feature fully implemented but requires assets
- See `studio/assets/README.md` for specifications

---

## Documentation

| Document | Purpose |
|----------|---------|
| `README.md` | User-facing quick start |
| `CLAUDE.md` | Developer guide for Claude Code |
| `UI_GUIDE.md` | Comprehensive Streamlit UI guide |
| `SETUP.md` | This file - setup instructions |
| `docs/crossfade-club/CROSSFADE_CLUB_PRD.md` | Crossfade Club product requirements |
| `docs/crossfade-club/CROSSFADE_CLUB_COMPLETE.md` | Implementation summary |
| `director/README.md` | Director Agent documentation |
| `studio/assets/README.md` | Blender asset specifications |
| `batch/README.md` | Batch pipeline documentation |

---

## Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: See docs/ directory
- **Tests**: Run `pytest tests/ -v` to verify setup
