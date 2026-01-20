# The Mixer - Web UI Guide 🎵

A complete guide to using the Streamlit web interface for The Mixer.

## Quick Start

### Installation

```bash
# Install UI dependency (if not already installed)
pip install streamlit

# Launch the web interface
streamlit run mixer_ui.py

# The app will open in your browser at http://localhost:8501
```

### First Time Setup

1. **Add API Keys** (if using LLM features):
   - Create `.env` file from `.env.template`
   - Add your `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`

2. **Ingest Some Songs**:
   - Go to **Library** tab → **Ingest** sub-tab
   - Upload local files or paste YouTube URLs
   - Check "Analyze now?" to extract metadata

3. **Create Your First Mashup**:
   - Go to **Create Mashup** tab
   - Select "Automatic" mode
   - Upload one song
   - Click "Create Mashup"
   - Download the result!

## Interface Overview

### 🎵 Create Mashup Tab

The main interface for creating mashups with two modes:

#### Automatic Mode (Recommended)
- **Upload one song** - We'll find the best match from your library
- **Select mashup type** - Or choose "Auto-Recommend" for best results
- **One-click creation** - Fully automated workflow
- **Perfect for**: Quick mashups, discovery, first-time users

**Example Workflow:**
1. Upload "Shake It Off" by Taylor Swift
2. Select "Conversational" mashup type
3. Click "Create Mashup"
4. System finds best match (e.g., "Blank Space")
5. Download your mashup!

#### Manual Mode
- **Choose both songs** - From library or upload new
- **Full control** - Select exact songs and mashup type
- **See metadata** - View BPM, key, genre before creating
- **Perfect for**: Specific pairings, experimentation, advanced users

**Example Workflow:**
1. Select "Song A" from library: "Bohemian Rhapsody"
2. Select "Song B" from library: "Smells Like Teen Spirit"
3. Choose "Classic" mashup type
4. Create and download!

### 📚 Library Tab

Manage your song collection with three sub-tabs:

#### Browse
- **Grid view** - See all songs in your library
- **Search** - Filter by artist, title, genre, or mood
- **Song cards** - Display metadata (BPM, key, genre, mood, energy)
- **Actions**:
  - **Analyze** - Extract section-level metadata
  - **Delete** - Remove from library (double-click to confirm)

#### Ingest
Three ways to add songs:

**Upload File:**
- Supported formats: MP3, WAV, FLAC
- Auto-analyze option (recommended)
- Cached to avoid duplicates

**YouTube URL:**
- Paste any YouTube video URL
- Audio extracted automatically
- Cached for future use

**Batch Folder:** ⭐ NEW!
- Perfect for CD rips or large music collections
- Paste folder path (e.g., `C:\Users\YourName\Music\New Rips`)
- Supports: MP3, WAV, FLAC, M4A, OGG
- Auto-analyze all songs after ingestion
- Progress bar shows ingestion status
- Summary shows ingested/skipped/failed counts

**Tips:**
- Always check "Analyze now?" for better mashups
- Upload diverse genres for interesting combinations
- YouTube URLs work with music videos, live performances, etc.
- Use Batch Folder for CD rips - rip with Windows Media Player first, then batch ingest

#### Stats
Visual analytics for your library:

- **Total songs** - Library size
- **Analyzed songs** - How many have full metadata
- **Total duration** - Combined length of all songs
- **Average BPM** - Across your collection
- **Genre distribution** - Bar chart of genre breakdown
- **Key distribution** - Musical keys in your library

**Use stats to:**
- See if you need more variety
- Find dominant genres/keys
- Track library growth

### ⚙️ Settings Tab

View your current configuration:

- **Audio Settings**: Sample rate, bit depth, channels, quality
- **Model Settings**: Whisper size, LLM provider, Demucs model
- **Curator Settings**: BPM tolerance, matching weights

**Note:** Settings are read-only in the UI. To change them, edit `config.yaml` in the project root.

## Mashup Types Explained

### Simple Mashups

**Classic**
- Vocals from Song A + Instrumental from Song B
- Most popular mashup style
- Example: Adele vocals + Daft Punk instrumental

**Stem Swap**
- Exchange specific instruments between songs
- Swap drums, bass, or other stems
- Example: AC/DC drums + Beatles bass

### Energy-Based Mashups

**Energy Matched**
- Align sections by energy level
- Intro→Intro, Verse→Verse, Chorus→Chorus
- Creates smooth transitions

**Adaptive Harmony**
- Dynamic mixing based on energy curves
- Fades between songs based on intensity
- Perfect for live DJ-style mixes

### Semantic Mashups

**Theme Fusion**
- Align songs by lyrical themes
- Narrative structure matching
- Example: Two breakup songs with complementary stories

**Semantic-Aligned**
- Match emotional arcs
- Happy→Happy, Sad→Sad sections
- Creates cohesive emotional journey

### Interactive Mashups

**Role-Aware**
- Question-and-answer vocal dynamics
- One song "asks", the other "answers"
- Conversational flow between artists

**Conversational**
- Dialogue-style vocal arrangement
- Back-and-forth between songs
- Most AI-powered, experimental type

## Tips & Best Practices

### For Best Results

1. **Analyze all songs** - Section-level metadata improves mashup quality
2. **Start with Automatic mode** - Great for discovering unexpected pairings
3. **Try different types** - Same song pair works differently with each mashup type
4. **Use semantic matching** - Upload songs with similar moods/themes
5. **Check compatibility** - In manual mode, check BPM/key before creating

### Performance Tips

1. **Mashup creation takes time** - 2-5 minutes is normal
2. **First-time analysis is slow** - Whisper + Demucs models download on first run
3. **GPU helps** - If you have CUDA, analysis is much faster
4. **Library size** - 10-50 songs is ideal for good matches
5. **Disk space** - Cache can grow large, clear periodically

### Troubleshooting

**"Library is empty"**
- Go to Library → Ingest tab
- Add at least 2 songs for auto-matching

**"Mashup creation failed"**
- Check that both songs are analyzed
- Verify API keys in `.env` file
- Try a different mashup type

**"No compatible matches found"**
- Add more songs with diverse BPMs/keys
- Try Manual mode instead
- Lower compatibility threshold in config.yaml

**UI won't start**
- Run: `pip install streamlit`
- Check Python version (3.9+ required)
- Verify all dependencies installed

## Keyboard Shortcuts

Streamlit provides these shortcuts:

- **R** - Rerun the app (refresh data)
- **C** - Clear cache
- **?** - Show keyboard shortcuts
- **Ctrl+Shift+P** - Command palette

## Advanced Features

### Session State

The UI remembers:
- Last created mashup (stays visible until next creation)
- File upload states
- Delete confirmations

### Progress Indicators

Watch for:
- Spinners during long operations
- Success/error messages
- Progress updates in workflow

### Download Management

- Mashups saved to `outputs/mashups/`
- Download button provides direct file access
- Files persist after download for later access

## Example Workflows

### Workflow 1: Quick Mashup
1. Click **Create Mashup** tab
2. Select **Automatic** mode
3. Upload "Don't Stop Believin'" (Journey)
4. Select **Auto-Recommend**
5. Click **Create Mashup**
6. System finds "Livin' on a Prayer" (Bon Jovi)
7. Creates "Classic" mashup (compatible BPM/key/genre)
8. Download and enjoy!

**Time:** ~3 minutes

### Workflow 2: Build a Library
1. Click **Library** tab → **Ingest**
2. Upload 10 songs from your music collection
3. Check "Analyze now?" for each
4. Go to **Stats** tab
5. View genre/key distribution
6. Identify gaps (e.g., need more 120 BPM songs)
7. Add more songs to fill gaps

**Time:** ~15-30 minutes (analysis takes time)

### Workflow 3: Experiment with Types
1. Create a mashup with "Classic" type
2. Note the result
3. Go back, use same songs with "Conversational" type
4. Compare the two outputs
5. Try all 8 types with your favorite pair
6. Find your preferred style!

**Time:** ~20 minutes

### Workflow 4: Theme-Based Mashup
1. Upload two songs with similar themes (e.g., both about summer)
2. Analyze both songs
3. Select **Manual** mode
4. Choose both songs
5. Select **Theme Fusion** mashup type
6. Create mashup
7. Listen to how lyrical themes align

**Time:** ~5 minutes

### Workflow 5: Batch Ingest CD Collection ⭐ NEW!
1. Rip CD with Windows Media Player to `C:\Users\YourName\Music\Album Name`
2. Open The Mixer web UI
3. Go to **Library** tab → **Ingest** sub-tab
4. Select **Batch Folder** mode
5. Paste folder path: `C:\Users\YourName\Music\Album Name`
6. Check "Analyze all songs after ingestion?"
7. Click **Batch Ingest Folder**
8. Watch progress bar as songs are ingested and analyzed
9. View summary (ingested/skipped/failed counts)
10. Repeat for more CDs!

**Time:** ~2-5 minutes per CD (depending on number of tracks and analysis)

**Perfect for:**
- Building library from CD collection
- Processing folder of downloaded music
- Migrating existing music library

## FAQ

**Q: Can I use any YouTube video?**
A: Yes, but music videos work best. Live performances and covers work too.

**Q: How many songs can I have in my library?**
A: No hard limit, but 10-100 is optimal. Larger libraries slow down search.

**Q: Can I preview songs before creating mashups?**
A: Not yet in the UI, but you can play the audio files from your cache directory.

**Q: What audio formats are supported?**
A: MP3, WAV, FLAC for upload. YouTube URLs extract as MP3.

**Q: Do I need API keys?**
A: Yes, for semantic analysis features. Basic mashups work without them.

**Q: Can I run this on a server?**
A: Yes! Use `streamlit run mixer_ui.py --server.port 8501 --server.address 0.0.0.0`

**Q: How do I close the UI?**
A: Press `Ctrl+C` in the terminal where it's running.

**Q: Can I use this commercially?**
A: The Mixer is for personal/educational use. Commercial use requires proper licensing for source audio.

## Support

For issues, feature requests, or questions:
- Check `README.md` for general info
- See `CLAUDE.md` for development details
- Review `PRD.md` for technical specs

Enjoy creating mashups! 🎵
