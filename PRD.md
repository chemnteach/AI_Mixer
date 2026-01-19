# Master Product Requirements Document: "The Mixer"
**Version:** 4.0 - Complete Architecture
**Last Updated:** 2026-01-18
**Status:** Ready for Implementation

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Core Philosophy](#2-core-philosophy)
3. [Technical Stack](#3-technical-stack)
4. [System Architecture](#4-system-architecture)
5. [Data Schema](#5-data-schema)
6. [Module Requirements](#6-module-requirements)
7. [User Interface](#7-user-interface)
8. [Error Handling & Logging](#8-error-handling--logging)
9. [Performance Requirements](#9-performance-requirements)
10. [Testing Strategy](#10-testing-strategy)
11. [Legal & Compliance](#11-legal--compliance)
12. [Future Enhancements](#12-future-enhancements)

---

## 1. Project Overview

**The Mixer** is an intelligent, agentic audio processing pipeline designed to automate the discovery, analysis, and creation of musical mashups.

### Goals
- Automate the tedious process of finding compatible songs for mashups
- Use semantic understanding (not just BPM/key matching) to find creative pairings
- Build a persistent, queryable music library with both technical and emotional metadata
- Generate broadcast-quality mashups with minimal user intervention

### Target Users
- Hobbyist DJs exploring mashup creation
- Music producers seeking creative inspiration
- Researchers studying music information retrieval
- Personal use for educational purposes

### Scope
- **In Scope:** Local audio processing, YouTube ingestion, automated mashup creation
- **Out of Scope:** Real-time DJ performance tools, streaming integration, cloud deployment

---

## 2. Core Philosophy

### Source Agnostic
The system treats all audio sources equally:
- A local demo tape from an independent artist
- A hit song downloaded from YouTube
- A Creative Commons track from Free Music Archive

**No bias based on source.** All songs are analyzed with the same rigor.

### Semantic-First Matching
Traditional DJ software matches by BPM and key alone. The Mixer adds:
- **Genre understanding:** "Find a country song"
- **Mood/vibe matching:** "Ironic pop track"
- **Lyrical theme:** "Songs about heartbreak"

This enables queries like:
> "Find a melancholic instrumental hip-hop track that matches this upbeat indie vocal"

### Memory as Intelligence
ChromaDB acts as the system's "brain," storing:
- Technical specs (BPM, key, downbeat)
- Semantic data (genre, mood, irony score)
- Vector embeddings of lyrics + vibe descriptions

This enables **fast retrieval** without re-analyzing songs.

---

## 3. Technical Stack

### Core Language
- **Python 3.9+** (Type hints required)

### Orchestration
- **LangGraph** (for agent state management and workflow)
- **langchain** (for LLM integration and prompt templates)

### Vector Memory
- **ChromaDB** (Persistent local storage)
  - Embedding Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
  - Storage Location: `./chroma_db/`

### Audio Intelligence

#### Local Processing (Offline-capable)
- **Transcription:** `openai-whisper` (model: `base` for speed, `medium` for accuracy)
- **Signal Analysis:** `librosa` (BPM, key, spectral analysis)
- **Stem Separation:** `demucs` (v4 - best quality) with `spleeter` fallback

#### Cloud Processing (API calls)
- **Reasoning:** Anthropic Claude 3.5 Sonnet (primary) or OpenAI GPT-4 (fallback)
  - Used for genre classification, mood analysis, irony scoring

### Audio Manipulation
- **Ingestion:** `yt-dlp` (YouTube downloads)
- **Backend Processing:** `ffmpeg-python` (format conversion, normalization)
- **Time Stretching:** `pyrubberband` (pitch-preserving tempo changes)
- **Mixing:** `pydub` (combining stems, effects, export)

### Dependencies Management
- **Environment:** `uv` or `pip` with `requirements.txt`
- **Virtual Environment Required:** Yes (avoid system-wide installations)

---

## 4. System Architecture

### High-Level Flow

```
┌─────────────┐
│ User Input  │ (YouTube URL or Local File)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: INGESTION & MEMORY                            │
│  ┌────────────────┐         ┌──────────────────┐       │
│  │ Ingestion      │────────▶│  ChromaDB        │       │
│  │ Agent          │  Check  │  (Vector Memory) │       │
│  │ (Collector)    │◀────────│                  │       │
│  └────────┬───────┘  Cache  └──────────────────┘       │
│           │ Hit?                      ▲                 │
│           │ No                        │                 │
│           ▼                           │                 │
│  ┌────────────────┐                  │                 │
│  │ Analyst Agent  │──────────────────┘                 │
│  │ (Profiler)     │  Store Metadata                    │
│  └────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: DISCOVERY (THE CURATOR)                       │
│  ┌────────────────┐         ┌──────────────────┐       │
│  │ Curator Agent  │────────▶│  Genre Filter    │       │
│  │ (Matchmaker)   │         │  BPM ± 5%        │       │
│  │                │         │  Key Compat.     │       │
│  │                │◀────────│  Semantic Query  │       │
│  └────────┬───────┘         └──────────────────┘       │
│           │                                             │
│           ▼                                             │
│  [ Top 5 Candidate Pairs ]                             │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: EXECUTION (THE ENGINEER)                      │
│  ┌────────────────┐                                     │
│  │ Engineer Agent │                                     │
│  │ (Builder)      │                                     │
│  └────────┬───────┘                                     │
│           │                                             │
│           ├──▶ Demucs/Spleeter (Stem Separation)       │
│           │                                             │
│           ├──▶ Pyrubberband (Time Stretch)             │
│           │                                             │
│           ├──▶ Grid Alignment (Downbeat Sync)          │
│           │                                             │
│           └──▶ Pydub (Mix & Export)                    │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│ Final       │ (Mashup_ArtistA_x_ArtistB.mp3)
│ Mashup File │
└─────────────┘
```

### Agent Responsibilities

| Agent | Role | Primary Tools | Output |
|-------|------|---------------|--------|
| **Ingestion Agent** | Download/cache audio | yt-dlp, ffmpeg | Standardized WAV file |
| **Analyst Agent** | Extract metadata | librosa, whisper, LLM | ChromaDB entry |
| **Curator Agent** | Find compatible pairs | ChromaDB queries | List of candidates |
| **Engineer Agent** | Build mashup | demucs, pyrubberband, pydub | Final MP3 |

---

## 5. Data Schema

### ChromaDB Collection: `tiki_library`

#### Storage Location
- **Path:** `./chroma_db/`
- **Persistence:** Enabled (survives restarts)

#### Schema Structure

**Document (Text Field):**
```
Full lyrical transcription + LLM-generated mood summary
Example: "Verse 1: I've been walking alone... [Mood: Melancholic introspection with hints of hope]"
```

**ID (Unique Identifier):**
```
Format: {artist}_{title}
Sanitization Rules:
  - Lowercase
  - Replace spaces with underscores
  - Remove special characters (keep only a-z, 0-9, _)
  - Max length: 128 characters

Example: "taylor_swift_shake_it_off"
```

**Embeddings (Vector):**
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions:** 384
- **Input:** Document field (lyrics + mood summary)

**Metadata (JSON):**

```json
{
  "source": "youtube",              // "youtube" | "local_file"
  "path": "/abs/path/to/file.wav",  // Absolute path to cached audio
  "bpm": 128.5,                     // Float (Beats Per Minute)
  "key": "Cmaj",                    // String (Key notation: [A-G][maj|min])
  "camelot": "8B",                  // String (Camelot Wheel notation)
  "genres": ["Pop", "Dance"],       // List[String] (Multi-genre support)
  "primary_genre": "Pop",           // String (Primary classification)
  "irony_score": 7,                 // Integer (0-10, higher = more ironic)
  "mood_summary": "Upbeat and...",  // String (LLM-generated)
  "energy_level": 8,                // Integer (0-10, higher = more energetic)
  "valence": 6,                     // Integer (0-10, 0=sad, 10=happy)
  "first_downbeat_sec": 0.523,      // Float (Timestamp of first beat)
  "duration_sec": 215.3,            // Float (Song length)
  "sample_rate": 44100,             // Integer (Hz)
  "has_vocals": true,               // Boolean (Detected vocals?)
  "original_url": "https://...",    // String (If from YouTube)
  "artist": "Taylor Swift",         // String (Cleaned artist name)
  "title": "Shake It Off",          // String (Cleaned title)
  "date_added": "2026-01-18T10:30:00Z" // ISO 8601 timestamp
}
```

#### Audio File Standards

All audio cached in `./library_cache/` must conform to:

- **Format:** WAV (uncompressed)
- **Sample Rate:** 44,100 Hz (CD quality)
- **Bit Depth:** 16-bit
- **Channels:** Stereo (2 channels)
- **Naming Convention:** `{artist}_{title}.wav` (same as ID)

---

## 6. Module Requirements

### Module A: The Ingestion Agent (The Collector)

**Function Signature:**
```python
def ingest_song(input_source: str) -> dict:
    """
    Ingest audio from YouTube or local file.

    Args:
        input_source: YouTube URL or absolute file path

    Returns:
        dict with keys: 'id', 'path', 'cached', 'metadata'
    """
```

**Behavior:**

1. **Input Detection:**
   ```python
   if input_source.startswith(('http://', 'https://')):
       source_type = 'youtube'
   elif os.path.exists(input_source):
       source_type = 'local_file'
   else:
       raise ValueError("Invalid input: not a URL or existing file")
   ```

2. **Fingerprinting:**
   - Extract artist/title from:
     - **YouTube:** Video title parsing (use regex to extract "Artist - Title")
     - **Local File:** Metadata tags (mutagen/eyed3) or filename
   - Generate ID: `sanitize(f"{artist}_{title}")`

3. **Cache Check:**
   ```python
   result = chroma_collection.get(ids=[song_id])
   if result['ids']:
       return {'cached': True, 'metadata': result['metadatas'][0]}
   ```

4. **Download (if YouTube):**
   ```bash
   yt-dlp \
     --extract-audio \
     --audio-format wav \
     --audio-quality 0 \
     --output "./library_cache/%(artist)s_%(title)s.%(ext)s" \
     {url}
   ```

5. **Standardization (if local file):**
   - Convert to WAV (44.1kHz, 16-bit, stereo) using ffmpeg
   - Copy to `./library_cache/`

6. **Validation:**
   - Check file size > 100KB (not empty)
   - Verify WAV header integrity
   - Duration > 30 seconds (skip short clips)

**Error Handling:**
- **YouTube unavailable:** Log error, skip song, notify user
- **Corrupt file:** Move to `./library_cache/failed/`, log details
- **Network timeout:** Retry 3 times with exponential backoff
- **Duplicate ID collision:** Append `_v2`, `_v3` to ID

**Returns:**
```json
{
  "id": "artist_title",
  "path": "/abs/path/to/library_cache/artist_title.wav",
  "cached": false,
  "source": "youtube",
  "metadata": null  // Will be populated by Analyst Agent
}
```

---

### Module B: The Analyst Agent (The Profiler)

**Function Signature:**
```python
def profile_audio(file_path: str, song_id: str) -> dict:
    """
    Analyze audio file and extract all metadata.

    Args:
        file_path: Absolute path to WAV file
        song_id: Unique identifier from Ingestion Agent

    Returns:
        Complete metadata dict ready for ChromaDB
    """
```

**Step 1: Signal Analysis (Local - Librosa)**

```python
import librosa

y, sr = librosa.load(file_path, sr=44100)

# BPM Detection
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
bpm = float(tempo)

# Key Detection (Chroma-based)
chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
key = estimate_key(chroma)  # Returns "Cmaj", "Amin", etc.
camelot = key_to_camelot(key)

# First Downbeat
first_downbeat_sec = librosa.frames_to_time(beats[0], sr=sr)

# Duration
duration_sec = librosa.get_duration(y=y, sr=sr)

# Energy Level (RMS)
rms = librosa.feature.rms(y=y)
energy_level = int(np.mean(rms) * 10)  # Normalize to 0-10
```

**Step 2: Semantic Analysis (Local - Whisper)**

```python
import whisper

model = whisper.load_model("base")  # or "medium" for better accuracy
result = model.transcribe(
    file_path,
    word_timestamps=True,  # CRITICAL: For future lyric sync
    language="en"
)

full_transcript = result['text']
word_timings = result['segments']  # For future use
```

**Vocal Detection:**
```python
# Simple heuristic: If transcript has > 50 words, likely has vocals
has_vocals = len(full_transcript.split()) > 50
```

**Step 3: Cognitive Analysis (Cloud - LLM)**

**Prompt Template:**
```
You are a music analyst. Analyze the following song lyrics and metadata.

LYRICS:
{full_transcript}

TECHNICAL DATA:
- BPM: {bpm}
- Key: {key}
- Energy: {energy_level}/10

TASK:
Return a JSON object with:
1. "genres": Array of 1-3 applicable genres (e.g., ["Pop", "Dance", "Electronic"])
2. "primary_genre": The single most fitting genre
3. "irony_score": Integer 0-10 (0=literal, 10=highly ironic/sarcastic)
4. "mood_summary": 1-2 sentence description of the emotional vibe
5. "valence": Integer 0-10 (0=sad/negative, 10=happy/positive)

IMPORTANT: Return ONLY valid JSON. No additional commentary.
```

**Example LLM Response:**
```json
{
  "genres": ["Pop", "Indie", "Folk"],
  "primary_genre": "Indie",
  "irony_score": 3,
  "mood_summary": "Wistful nostalgia with underlying optimism. The lyrics reflect on past relationships with bittersweet acceptance.",
  "valence": 4
}
```

**Step 4: Memorization (ChromaDB Upsert)**

```python
# Construct document for embedding
document = f"{full_transcript}\n\n[MOOD]: {mood_summary}"

# Combine all metadata
metadata = {
    "source": "youtube",
    "path": file_path,
    "bpm": bpm,
    "key": key,
    "camelot": camelot,
    "genres": genres,
    "primary_genre": primary_genre,
    "irony_score": irony_score,
    "mood_summary": mood_summary,
    "energy_level": energy_level,
    "valence": valence,
    "first_downbeat_sec": first_downbeat_sec,
    "duration_sec": duration_sec,
    "sample_rate": sr,
    "has_vocals": has_vocals,
    "artist": artist,
    "title": title,
    "date_added": datetime.utcnow().isoformat()
}

# Upsert to ChromaDB
chroma_collection.upsert(
    ids=[song_id],
    documents=[document],
    metadatas=[metadata]
)
```

**Error Handling:**
- **BPM detection fails:** Set to `null`, warn user (manual entry needed)
- **Key detection uncertain:** Set to "Unknown"
- **Whisper timeout:** Set `has_vocals = false`, transcript = ""
- **LLM API failure:** Use fallback rules (e.g., genre from filename keywords)

**Returns:**
```json
{
  "status": "success",
  "song_id": "artist_title",
  "metadata": { /* full metadata dict */ }
}
```

---

### Module C: The Curator Agent (The Matchmaker)

**Function Signature:**
```python
def find_match(
    target_song_id: str,
    criteria: str = "harmonic",  # "harmonic" | "semantic" | "hybrid"
    genre_filter: Optional[str] = None,
    semantic_query: Optional[str] = None,
    max_results: int = 5
) -> List[dict]:
    """
    Find compatible songs for mashup creation.

    Args:
        target_song_id: ID of the base song
        criteria: Matching strategy
        genre_filter: Optional genre constraint (e.g., "Country")
        semantic_query: Optional vibe description (e.g., "ironic and upbeat")
        max_results: Number of candidates to return

    Returns:
        List of dicts with keys: 'id', 'score', 'metadata'
    """
```

**Step 1: Fetch Target Metadata**

```python
target = chroma_collection.get(ids=[target_song_id])
if not target['ids']:
    raise ValueError(f"Song {target_song_id} not found in library")

target_meta = target['metadatas'][0]
target_bpm = target_meta['bpm']
target_key = target_meta['key']
```

**Step 2: Build Hard Filters (Mathematical Constraints)**

```python
# BPM Tolerance: ±5% (tighter than original ±10%)
bpm_min = target_bpm * 0.95
bpm_max = target_bpm * 1.05

# Compatible Keys (Camelot Wheel Logic)
compatible_keys = get_compatible_keys(target_meta['camelot'])
# Returns: Same key, ±1 on Camelot wheel, relative major/minor

# Genre Filter (if specified)
where_clause = {
    "$and": [
        {"bpm": {"$gte": bpm_min, "$lte": bpm_max}},
        {"key": {"$in": compatible_keys}}
    ]
}

if genre_filter:
    where_clause["$and"].append({"primary_genre": genre_filter})
```

**Step 3: Query Strategy**

**A) Harmonic Matching (criteria="harmonic"):**
```python
results = chroma_collection.query(
    where=where_clause,
    n_results=max_results * 2  # Over-fetch for filtering
)
# Rank by BPM proximity
ranked = sorted(results, key=lambda x: abs(x['bpm'] - target_bpm))
```

**B) Semantic Matching (criteria="semantic"):**
```python
if not semantic_query:
    raise ValueError("semantic_query required for semantic matching")

results = chroma_collection.query(
    query_texts=[semantic_query],
    where=where_clause,
    n_results=max_results
)
# Already ranked by cosine similarity (ChromaDB default)
```

**C) Hybrid Matching (criteria="hybrid" - RECOMMENDED):**
```python
# Step 1: Hard filter by BPM/key
candidates = chroma_collection.query(where=where_clause, n_results=50)

# Step 2: Re-rank by semantic similarity to target's mood
target_doc = target['documents'][0]
reranked = chroma_collection.query(
    query_texts=[target_doc],
    ids=candidates['ids'],
    n_results=max_results
)
```

**Step 4: Post-Processing**

```python
# Remove the target song itself
results = [r for r in results if r['id'] != target_song_id]

# Add compatibility score
for result in results:
    result['compatibility_score'] = calculate_score(
        bpm_diff=abs(result['bpm'] - target_bpm),
        key_distance=camelot_distance(target_meta['camelot'], result['camelot']),
        semantic_sim=result.get('distance', 0)  # From ChromaDB
    )

# Sort by score
results.sort(key=lambda x: x['compatibility_score'], reverse=True)
```

**Returns:**
```json
[
  {
    "id": "candidate_song_1",
    "compatibility_score": 0.92,
    "metadata": { /* full metadata */ },
    "match_reasons": [
      "BPM: 128 (within 2% of target)",
      "Key: 8B (perfect harmonic match)",
      "Mood: High semantic similarity (0.88)"
    ]
  },
  // ... up to max_results
]
```

**Camelot Wheel Compatibility Rules:**

```python
def get_compatible_keys(camelot: str) -> List[str]:
    """
    Returns harmonically compatible Camelot keys.

    Compatible moves:
    - Same key (8B → 8B)
    - +1/-1 on wheel (8B → 7B, 9B)
    - Inner/outer circle (8B → 8A)
    """
    # Implementation uses Camelot wheel adjacency matrix
```

---

### Module D: The Engineer Agent (The Builder)

**Function Signature:**
```python
def build_mashup(
    vocal_source_id: str,
    instrumental_source_id: str,
    output_format: str = "mp3",  # "mp3" | "wav"
    quality_preset: str = "high"  # "draft" | "high" | "broadcast"
) -> str:
    """
    Create mashup from two songs.

    Args:
        vocal_source_id: ID of song to extract vocals from
        instrumental_source_id: ID of song to extract instrumental from
        output_format: Export format
        quality_preset: Processing quality level

    Returns:
        Absolute path to output file
    """
```

**Step 1: Stem Separation**

```python
from demucs.pretrained import get_model
from demucs.apply import apply_model

# Load Demucs model (v4 hybrid transformer)
model = get_model('htdemucs')

# Process Song A (Vocals)
stems_a = apply_model(model, vocal_path)
vocals = stems_a['vocals']  # Isolated vocal track

# Process Song B (Instrumental)
stems_b = apply_model(model, instrumental_path)
instrumental = stems_b['drums'] + stems_b['bass'] + stems_b['other']
# Combine all non-vocal stems
```

**Fallback Strategy:**
```python
try:
    # Try Demucs (best quality)
    stems = separate_with_demucs(file_path)
except Exception as e:
    logging.warning(f"Demucs failed: {e}. Falling back to Spleeter.")
    # Fallback to Spleeter (faster, GPU-optional)
    stems = separate_with_spleeter(file_path)
```

**Quality Presets:**

| Preset | Demucs Model | Shifts | Processing Time |
|--------|--------------|--------|-----------------|
| `draft` | `mdx` | 1 | ~30s per song |
| `high` | `htdemucs` | 5 | ~2 min per song |
| `broadcast` | `htdemucs_ft` | 10 | ~5 min per song |

**Step 2: Tempo Normalization**

```python
# Fetch BPMs from ChromaDB
vocal_bpm = get_metadata(vocal_source_id)['bpm']
inst_bpm = get_metadata(instrumental_source_id)['bpm']

# Calculate stretch ratio
stretch_ratio = inst_bpm / vocal_bpm

# Validate stretch range
if not (0.8 <= stretch_ratio <= 1.2):
    logging.warning(
        f"Large stretch ratio: {stretch_ratio:.2f}. "
        f"Quality may degrade. Recommend selecting closer BPM match."
    )
    if stretch_ratio > 1.3 or stretch_ratio < 0.7:
        raise ValueError("Stretch ratio out of acceptable bounds (0.7-1.3)")

# Apply time-stretch (pitch-preserving)
import pyrubberband as pyrb

vocals_stretched = pyrb.time_stretch(
    vocals,
    sr=44100,
    rate=stretch_ratio,
    rbargs={'--fine': ''}  # High-quality mode
)
```

**Step 3: Grid Alignment**

```python
# Fetch first downbeat timestamps
vocal_downbeat = get_metadata(vocal_source_id)['first_downbeat_sec']
inst_downbeat = get_metadata(instrumental_source_id)['first_downbeat_sec']

# After time-stretching, adjust vocal downbeat
adjusted_vocal_downbeat = vocal_downbeat * stretch_ratio

# Calculate offset needed to align
offset_samples = int((inst_downbeat - adjusted_vocal_downbeat) * 44100)

# Apply offset
if offset_samples > 0:
    # Delay vocals (pad beginning)
    vocals_aligned = np.pad(vocals_stretched, (offset_samples, 0))
else:
    # Advance vocals (trim beginning)
    vocals_aligned = vocals_stretched[abs(offset_samples):]

# Match length to instrumental
min_length = min(len(instrumental), len(vocals_aligned))
vocals_final = vocals_aligned[:min_length]
instrumental_final = instrumental[:min_length]
```

**Edge Case - Length Mismatch:**
```python
# If vocal track is significantly shorter, crossfade ending
if len(vocals_aligned) < len(instrumental) * 0.8:
    # Apply 4-second fade-out starting at 80% of vocal length
    fade_start = int(len(vocals_aligned) * 0.8)
    vocals_aligned = apply_fadeout(vocals_aligned, fade_start, duration=4.0)
```

**Step 4: Mixing & Export**

```python
from pydub import AudioSegment
from pydub.effects import normalize

# Convert numpy arrays to AudioSegment
vocals_seg = numpy_to_audiosegment(vocals_final, sr=44100)
inst_seg = numpy_to_audiosegment(instrumental_final, sr=44100)

# Normalize levels (LUFS targeting)
vocals_seg = normalize(vocals_seg, headroom=2.0)
inst_seg = normalize(inst_seg, headroom=2.0)

# Adjust relative volumes
vocals_seg = vocals_seg - 2  # Vocals 2dB quieter (mix preference)

# Overlay
mashup = inst_seg.overlay(vocals_seg)

# Export
output_filename = f"Mashup_{vocal_id}_x_{inst_id}.{output_format}"
output_path = os.path.join("./mashups/", output_filename)

if output_format == "mp3":
    mashup.export(output_path, format="mp3", bitrate="320k")
elif output_format == "wav":
    mashup.export(output_path, format="wav", parameters=["-ac", "2", "-ar", "44100"])

logging.info(f"Mashup created: {output_path}")
return output_path
```

**Advanced Mixing Options (Future):**
```python
# Optional: Apply EQ to reduce frequency masking
vocals_seg = apply_highpass(vocals_seg, cutoff=200)  # Remove low-end rumble
inst_seg = apply_lowpass(inst_seg, cutoff=8000)     # Reduce harsh highs

# Optional: Sidechain compression (duck instrumental when vocals present)
inst_seg = sidechain_compress(inst_seg, vocals_seg, threshold=-20, ratio=4)
```

**Error Handling:**
- **Stem separation fails:** Log error, provide original file paths for manual processing
- **Stretch ratio extreme:** Warn user, prompt to confirm or select different song
- **Alignment failure:** Fall back to simple overlap (no downbeat sync)
- **Export fails:** Try alternate format (WAV if MP3 fails)

**Returns:**
```
"/abs/path/to/mashups/Mashup_artist1_song1_x_artist2_song2.mp3"
```

---

### Advanced Mashup Types (Phase 3+)

**Status:** Future enhancement - requires section-level analysis from Analyst Agent

The Engineer Agent will support **8 mashup strategies** that use AI reasoning to create genuinely novel combinations. These go beyond traditional "vocal over instrumental" mashups.

#### Updated Function Signature (Phase 3)

```python
def build_mashup(
    mashup_type: MashupType,
    config: MashupConfig,
    output_format: str = "mp3",
    quality_preset: str = "high"
) -> str:
    """
    Create mashup using specified strategy.

    Args:
        mashup_type: Which mashup strategy to use (see MashupType enum)
        config: Type-specific configuration (vocal IDs, theme, etc.)
        output_format: Export format
        quality_preset: Processing quality level

    Returns:
        Absolute path to output file
    """
```

#### Mashup Type Taxonomy

| Type | Complexity | Key Innovation | Phase |
|------|-----------|----------------|-------|
| **Classic** | Low | Vocal A + Instrumental B (current spec) | 3B |
| **Stem Role Swapping** | Low | Mix drums/bass/vocals from 3+ songs | 3B |
| **Energy Curve Matching** | Medium | Align high-energy sections | 3C |
| **Adaptive Harmony** | Medium | Auto-fix key clashes via pitch-shifting | 3C |
| **Lyrical Theme Fusion** | Medium | Filter lyrics to unified theme | 3D |
| **Semantic-Aligned** | Medium-High | Meaning-driven structure (not tempo) | 3D |
| **Role-Aware Recomposition** | High | Vocals become lead/harmony/call/response | 3E |
| **Conversational** | High | Songs talk to each other (dialogue) | 3E |

#### Type 1: Classic (Already Spec'd)
**What it does:** Traditional mashup - vocals from Song A over instrumental from Song B
**Config:**
```python
{"vocal_id": "adele_rolling", "inst_id": "daft_punk_one_more_time"}
```
**Implementation:** See lines 670-826 above

#### Type 2: Stem Role Swapping
**What it does:** Compose from a palette of stems (drums, bass, vocals, other)
**Use case:** "Beyoncé vocals + Daft Punk drums + Beatles bass"
**Config:**
```python
{
    "vocals": "beyonce_crazy_in_love",
    "drums": "daft_punk_harder_better",
    "bass": "beatles_come_together",
    "other": "radiohead_everything"
}
```
**Algorithm:**
1. Separate each source song into stems
2. Time-stretch all to match target BPM (use drums' BPM as reference)
3. Align downbeats
4. Mix all stems together

**Innovation:** Instead of 2-song mashups, you're composing from multiple sources

#### Type 3: Energy Curve Matching
**What it does:** Align sections by energy level (not just tempo/key)
**Use case:** "Make high-energy choruses align with high-energy drops"
**Config:**
```python
{"song_a_id": "quiet_verse_song", "song_b_id": "explosive_drop_song"}
```
**Algorithm:**
1. Extract energy profiles for all sections (using `librosa.feature.rms`)
2. Find best energy alignments (e.g., high-energy chorus A → high-energy drop B)
3. Build mashup by swapping sections based on energy similarity
4. Crossfade between sections for smooth transitions

**Innovation:** Structure follows emotional intensity, not just bar counts

#### Type 4: Adaptive Harmony
**What it does:** Detect key clashes and pitch-shift to eliminate them
**Use case:** "These songs are in different keys - fix it without losing vocal character"
**Config:**
```python
{"vocal_id": "song_in_C", "inst_id": "song_in_F_sharp_minor"}
```
**Algorithm:**
1. Check if keys are harmonically compatible (Camelot wheel)
2. If not, calculate semitone shift needed
3. LLM decides: shift vocal (changes voice) or shift instrumental (preserves vocal authenticity)
4. Apply pitch-shift to chosen track
5. Build mashup with aligned keys

**Innovation:** AI decides which track to shift based on preserving authenticity

#### Type 5: Lyrical Theme Fusion
**What it does:** Only include lyrics that reinforce a target theme
**Use case:** "Create a coherent heartbreak narrative from these two songs"
**Config:**
```python
{
    "song_a_id": "taylor_swift_all_too_well",
    "song_b_id": "adele_someone_like_you",
    "theme": "heartbreak"
}
```
**Algorithm:**
1. LLM analyzes each section's lyrics
2. Classifies: Does this section reinforce the theme?
3. Keep sections that match theme (with vocals)
4. Replace non-matching sections with instrumental fills
5. Build mashup with thematic coherence

**Innovation:** Creates unified narrative from disparate songs

#### Type 6: Semantic-Aligned Mashups
**What it does:** AI designs emotional arc, selecting sections based on meaning
**Use case:** "Build a journey from hope → doubt → defiance"
**Config:**
```python
{
    "song_a_id": "imagine_dragons_believer",
    "song_b_id": "twenty_one_pilots_stressed_out"
}
```
**Algorithm:**
1. Extract emotional tone for each section (LLM-derived)
2. LLM designs coherent emotional arc: Intro → Build → Climax → Resolution
3. Select sections from either song to fulfill the arc
4. Arrange non-linearly (e.g., A_verse → B_chorus → A_bridge)
5. Crossfade between sections

**Innovation:** Meaning drives structure, not musical rules

#### Type 7: Role-Aware Vocal Recomposition
**What it does:** Vocals dynamically shift between lead, harmony, call, response, texture
**Use case:** "Make sparse vocals become harmony, dense vocals become lead"
**Config:**
```python
{
    "song_a_id": "ed_sheeran_shape_of_you",
    "song_b_id": "the_weeknd_blinding_lights"
}
```
**Algorithm:**
1. Analyze vocal characteristics per section (density, intensity)
2. LLM assigns roles dynamically:
   - Lead (main melodic focus)
   - Harmony (supporting layer, pitch-shifted)
   - Call (poses question)
   - Response (answers/echoes)
   - Texture (rhythmic, no lyrics)
3. Build mashup with role-based mixing:
   - Lead: Full volume
   - Harmony: -6dB, pitch-shifted +3 semitones
   - Call/Response: Temporal arrangement with silence gaps
   - Texture: Heavy processing (reverb, delay)

**Innovation:** Vocals interact instead of just overlaying

#### Type 8: Conversational Mashups
**What it does:** Lyrics respond to each other like a dialogue
**Use case:** "Make it sound like the singers are having a conversation"
**Config:**
```python
{
    "song_a_id": "song_with_questions",
    "song_b_id": "song_with_answers"
}
```
**Algorithm:**
1. LLM detects question/answer patterns in both songs' lyrics
2. Pairs lines that create dialogue:
   - Question → Answer
   - Statement → Agreement/Disagreement
   - Emotion → Echo/Contrast
3. Extract vocal snippets at lyric-level precision
4. Arrange temporally with silence gaps (creates "listening" moments)
5. Layer instrumental bed underneath

**Example conversation:**
```
A: "Do you believe in love?"
(silence - 0.3s)
B: "I used to, yeah"
(silence - 0.5s)
A: "What changed?"
(silence - 0.3s)
B: "Everything and nothing"
```

**Innovation:** Creates duets that were never recorded

---

### Section-Level Metadata (Required for Advanced Types)

**Added in Phase 3A** - Analyst Agent extracts per-section metadata:

```python
class SectionMetadata(TypedDict):
    section_type: str              # "intro" | "verse" | "chorus" | "bridge" | "outro"
    start_sec: float
    end_sec: float
    duration_sec: float

    # Energy characteristics (librosa)
    energy_level: float            # 0.0-1.0 (RMS energy)
    spectral_centroid: float       # Brightness (Hz)
    tempo_stability: float         # Beat consistency

    # Vocal characteristics
    vocal_density: str             # "sparse" | "medium" | "dense"
    vocal_intensity: float         # 0.0-1.0

    # Semantic analysis (LLM)
    emotional_tone: str            # "hopeful" | "melancholic" | "defiant"
    lyrical_function: str          # "narrative" | "hook" | "question" | "answer"
    themes: List[str]              # ["love", "loss", "rebellion"]
```

**Libraries needed:**
- `madmom` (onset/beat tracking)
- `librosa.segment.agglomerative` (section detection)
- Existing: Demucs, Whisper, Claude/GPT-4

**Implementation phases:**
- **Phase 3A:** Enhance Analyst Agent to extract section metadata
- **Phase 3B:** Implement simple types (Classic, Stem Swap)
- **Phase 3C:** Implement energy-based types (Energy Matching, Adaptive Harmony)
- **Phase 3D:** Implement semantic types (Theme Fusion, Semantic-Aligned)
- **Phase 3E:** Implement interactive types (Role-Aware, Conversational)

---

## 7. User Interface

### CLI (Phase 1 - MVP)

**Command Structure:**
```bash
# Ingest songs
python mixer.py ingest "https://youtube.com/watch?v=..."
python mixer.py ingest "/path/to/song.mp3"

# Analyze library
python mixer.py analyze  # Analyze all un-profiled songs

# Find matches
python mixer.py match "artist_title" --genre Country --semantic "ironic and upbeat"

# Create mashup (Phase 2 - Classic only)
python mixer.py mashup "song1_id" "song2_id" --vocals-from song1 --output high

# Create mashup (Phase 3+ - Advanced types)
python -m mixer mashup classic --vocal "song1" --inst "song2"
python -m mixer mashup stem-swap --vocals "s1" --drums "s2" --bass "s3" --other "s4"
python -m mixer mashup energy --songs "song1" "song2"
python -m mixer mashup adaptive --vocal "song1" --inst "song2"
python -m mixer mashup theme --songs "song1" "song2" --theme "heartbreak"
python -m mixer mashup semantic --songs "song1" "song2"
python -m mixer mashup role-aware --songs "song1" "song2"
python -m mixer mashup convo --songs "song1" "song2"

# Library management
python mixer.py library list
python mixer.py library search "country songs"
python mixer.py library stats
```

**Interactive Mode:**
```bash
python mixer.py interactive

> Welcome to The Mixer!
> Enter a song URL or file path to begin: https://youtube.com/...
> Analyzing... Done!
>
> Find matches for this song? (y/n): y
> Match criteria:
>   [1] Harmonic (BPM + Key)
>   [2] Semantic (Mood + Vibe)
>   [3] Hybrid (Recommended)
> Select: 3
>
> Top 5 Matches:
>   1. Artist - Title (Score: 0.92)
>   2. Artist - Title (Score: 0.88)
>   ...
>
> Select match (1-5) or 'q' to quit: 1
> Building mashup... Done!
> Output: ./mashups/Mashup_...mp3
```

### Web UI (Phase 2 - Future)

**Tech Stack:**
- **Backend:** FastAPI (async endpoints)
- **Frontend:** React + TailwindCSS
- **Real-time Updates:** WebSocket for processing status

**Key Features:**
- Drag-and-drop file upload
- YouTube URL paste
- Visual BPM/key compatibility matrix
- Waveform preview with downbeat markers
- Stem separation preview (play vocals/instrumental separately)
- Mashup player with A/B comparison

---

## 8. Error Handling & Logging

### Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mixer.log'),
        logging.StreamHandler()  # Console output
    ]
)
```

### Error Categories

| Error Type | Severity | User Action | System Action |
|------------|----------|-------------|---------------|
| Network timeout (yt-dlp) | Warning | Retry or skip | Log, retry 3x |
| Corrupt audio file | Error | Provide valid file | Move to `./failed/` |
| LLM API failure | Warning | Continue w/ defaults | Use fallback rules |
| ChromaDB connection fail | Critical | Restart system | Alert, exit gracefully |
| Demucs GPU unavailable | Warning | Use CPU mode | Fallback to Spleeter |
| BPM detection fail | Warning | Manual entry | Set `bpm: null` |

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def download_youtube(url: str) -> str:
    # yt-dlp download logic
    pass
```

### User Notifications

**Severity Levels:**
- **INFO:** "Song already cached. Loading metadata..."
- **WARNING:** "BPM detection uncertain (confidence: 60%). Results may vary."
- **ERROR:** "Failed to download: Video is private."
- **CRITICAL:** "Database connection lost. Shutting down."

---

## 9. Performance Requirements

### Processing Time Targets

| Operation | Target | Acceptable | Notes |
|-----------|--------|------------|-------|
| YouTube download | < 30s | < 60s | 3-5 min song |
| Whisper transcription | < 60s | < 120s | Using `base` model |
| Librosa analysis | < 10s | < 20s | BPM + Key + Downbeat |
| LLM classification | < 5s | < 10s | Single API call |
| Demucs separation | < 120s | < 300s | High quality preset |
| Mashup creation | < 60s | < 120s | Full pipeline |

### Concurrency

**Parallel Processing:**
```python
# Batch ingestion
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(ingest_song, url_list)
```

**GPU Acceleration:**
- **Demucs:** Use CUDA if available
- **Whisper:** Use GPU for `medium`/`large` models
- **Fallback:** Gracefully degrade to CPU if GPU unavailable

### Resource Limits

**Disk Space:**
- Monitor `./library_cache/` size
- Implement LRU eviction if > 50GB
- Keep metadata in ChromaDB even if audio deleted

**Memory:**
- Demucs peak usage: ~4GB RAM (CPU) / ~8GB VRAM (GPU)
- Process songs sequentially if RAM < 8GB

**Rate Limiting:**
- YouTube: Respect `yt-dlp` rate limits (no more than 5 concurrent downloads)
- LLM API: Implement exponential backoff on 429 errors

---

## 10. Testing Strategy

### Unit Tests

**Coverage Target:** 80% minimum

**Critical Test Cases:**

```python
# test_ingestion.py
def test_youtube_download():
    # Mock yt-dlp, verify file creation
    pass

def test_duplicate_detection():
    # Add same song twice, should return cached
    pass

# test_analysis.py
def test_bpm_detection():
    # Use known-BPM test files (120 BPM, 140 BPM, etc.)
    pass

def test_key_detection():
    # C major scale test audio
    pass

# test_curator.py
def test_harmonic_matching():
    # Song at 120 BPM, Cmaj should match 122 BPM, Gmaj
    pass

def test_genre_filter():
    # Query with genre="Country" should exclude Pop songs
    pass

# test_engineer.py
def test_stem_separation():
    # Verify vocals/instrumental are distinct
    pass

def test_time_stretch():
    # 100 BPM → 120 BPM should result in shorter duration
    pass
```

### Integration Tests

```python
# test_e2e.py
def test_full_pipeline():
    # Ingest → Analyze → Match → Mashup
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Test video
    result = ingest_song(url)
    assert result['cached'] == False

    profile_audio(result['path'], result['id'])
    matches = find_match(result['id'], criteria='hybrid')
    assert len(matches) > 0

    mashup_path = build_mashup(result['id'], matches[0]['id'])
    assert os.path.exists(mashup_path)
```

### Test Fixtures

**Location:** `./tests/fixtures/`

**Required Test Files:**
- `test_120bpm_cmaj.wav` (Known BPM/key for calibration)
- `test_vocals_only.wav` (A cappella)
- `test_instrumental.wav` (No vocals)
- `test_corrupt.wav` (Invalid header for error handling)

### Mock Data

```python
# Mock LLM responses to avoid API costs during testing
@pytest.fixture
def mock_llm_response():
    return {
        "genres": ["Pop"],
        "primary_genre": "Pop",
        "irony_score": 5,
        "mood_summary": "Test mood",
        "valence": 6
    }
```

### Performance Tests

```python
import pytest
import time

@pytest.mark.performance
def test_analysis_speed():
    start = time.time()
    profile_audio("./tests/fixtures/test_120bpm_cmaj.wav", "test_song")
    elapsed = time.time() - start
    assert elapsed < 30, f"Analysis took {elapsed}s (target: <30s)"
```

---

## 11. Legal & Compliance

### Disclaimer

**The Mixer is intended for:**
- **Educational purposes** (learning audio processing, ML)
- **Personal use** (non-commercial experimentation)
- **Fair use** (research, commentary, parody)

**The Mixer is NOT intended for:**
- Commercial distribution of copyrighted mashups
- Circumventing artist rights or streaming platform TOS
- Mass piracy or content redistribution

### User Responsibility

**Users Must:**
1. Ensure they have rights to the audio they process
2. Comply with YouTube Terms of Service
3. Not distribute copyrighted mashups without permission
4. Respect DMCA and international copyright laws

**Recommended Sources:**
- Creative Commons music (FreeMusicArchive, ccMixter)
- Royalty-free libraries (Incompetech, Purple Planet)
- Personal recordings
- Public domain works

### YouTube Terms of Service

**yt-dlp Usage:**
- Technically violates YouTube TOS (downloading content)
- Risk: YouTube may block IP or take legal action
- Mitigation:
  - Include warning in documentation
  - Consider using YouTube Audio Library (TOS-compliant)
  - Add option to disable YouTube ingestion

**Alternative Approach:**
```python
# Phase 2: Replace yt-dlp with API-based services
# - YouTube Audio Library API (legal)
# - Spotify/SoundCloud integrations (streaming preview only)
```

### Data Privacy

**No User Data Collection:**
- All processing is local
- No telemetry or analytics sent to external servers
- User's music library stays on their machine

**LLM API Calls:**
- Lyrics sent to Anthropic/OpenAI for analysis
- Users should be aware of data transmission
- Option to disable LLM features for fully offline mode

---

## 12. Future Enhancements

### Phase 2 Features

**Advanced Curator:**
- Multi-song mashups (3+ sources)
- "Find the weirdest combo" mode (maximize genre distance)
- Temporal matching (find songs with similar structural changes)

**Smart Engineer:**
- Auto-detect best vocal/instrumental split (don't require user to specify)
- Key transposition (pitch-shift vocals to match instrumental)
- Dynamic arrangement (intro from Song A, chorus from Song B)

**Web UI:**
- Drag-and-drop mashup builder
- Real-time waveform editing
- Social sharing (export to SoundCloud/YouTube)

### Phase 3 - Advanced Features

**Collaborative Filtering:**
- "Users who liked this mashup also enjoyed..." (recommendation engine)
- Community-contributed ratings

**Live Performance Mode:**
- Real-time mashup generation
- MIDI controller integration
- Crossfader/EQ controls

**AI-Generated Transitions:**
- LLM suggests creative transitions between song sections
- "What if we mash up only the choruses?"

**Stem Marketplace:**
- Share/download isolated stems (with artist permission)
- Remix competitions

---

## Appendix A: Key Compatibility Chart

### Camelot Wheel

```
       12B (Bmaj)
    11B    1B
 10B          2B
9B              3B
 8B            4B
    7B    5B
       6B (F#maj)

    [Inner Circle = Minor Keys]
    8A = Amin (relative to 8B = Cmaj)
```

**Compatible Transitions:**
- **Same Number:** Major ↔ Minor (8B ↔ 8A)
- **±1 Number:** Circle of 5ths (8B → 9B or 7B)
- **Same Key:** Perfect match (8B → 8B)

---

## Appendix B: Dependencies

### requirements.txt

```
# Core
python>=3.9
langchain>=0.1.0
langgraph>=0.0.20

# Vector Store
chromadb>=0.4.0
sentence-transformers>=2.2.0

# Audio Processing
librosa>=0.10.0
openai-whisper>=20230314
pydub>=0.25.0
pyrubberband>=0.3.0
soundfile>=0.12.0

# Stem Separation
demucs>=4.0.0
# spleeter  # Optional fallback

# Ingestion
yt-dlp>=2023.3.4
ffmpeg-python>=0.2.0

# LLM
anthropic>=0.18.0
openai>=1.0.0  # Fallback

# Utilities
numpy>=1.24.0
scipy>=1.10.0
tenacity>=8.2.0  # Retry logic
python-dotenv>=1.0.0

# Development
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
mypy>=1.5.0
```

### System Dependencies

**Required:**
- `ffmpeg` (audio conversion)
- `libsndfile` (audio I/O)

**Optional:**
- CUDA 11.8+ (GPU acceleration for Demucs/Whisper)

**Installation (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg libsndfile1
```

**Installation (macOS):**
```bash
brew install ffmpeg libsndfile
```

---

## Appendix C: Configuration File

### config.yaml

```yaml
# The Mixer Configuration File

paths:
  library_cache: "./library_cache"
  mashup_output: "./mashups"
  chroma_db: "./chroma_db"
  failed_files: "./library_cache/failed"

audio:
  sample_rate: 44100
  bit_depth: 16
  channels: 2
  default_format: "wav"

models:
  whisper_size: "base"  # tiny | base | small | medium | large
  demucs_model: "htdemucs"  # mdx | htdemucs | htdemucs_ft
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

llm:
  primary_provider: "anthropic"  # anthropic | openai
  fallback_provider: "openai"
  anthropic_model: "claude-3-5-sonnet-20241022"
  openai_model: "gpt-4-turbo-preview"
  max_retries: 3
  timeout: 30

curator:
  bpm_tolerance: 0.05  # ±5%
  max_stretch_ratio: 1.2  # Don't stretch beyond 20%
  default_match_criteria: "hybrid"
  max_candidates: 5

engineer:
  default_quality: "high"  # draft | high | broadcast
  vocal_attenuation_db: -2  # How much quieter vocals vs instrumental
  fade_duration_sec: 4.0
  normalize_lufs: -14  # Target loudness

performance:
  max_concurrent_downloads: 4
  enable_gpu: true
  fallback_to_cpu: true
  max_cache_size_gb: 50

logging:
  level: "INFO"  # DEBUG | INFO | WARNING | ERROR
  file: "mixer.log"
  max_file_size_mb: 100
  backup_count: 5
```

---

## Document Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-01-XX | Initial draft (incomplete) | Gemini |
| 2.0 | 2025-01-XX | Added Module D partial spec | Gemini |
| 3.0 | 2025-01-XX | Flowchart added, schema refined | Gemini |
| **4.0** | **2026-01-18** | **Complete rewrite: All modules specified, legal section added, testing strategy, config management** | **Claude (Anthropic)** |

---

## Approval & Sign-off

**Ready for Implementation:** ✅
**Blocking Issues:** None
**Next Steps:**
1. Set up project repository
2. Create virtual environment + install dependencies
3. Implement Module A (Ingestion) - first milestone
4. Create test fixtures
5. Begin unit testing

---

*This PRD is a living document. Update as requirements evolve.*
