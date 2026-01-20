# Batch Module - End-to-End Pipeline Orchestration

The Batch module orchestrates the complete Crossfade Club pipeline from audio to platform-optimized videos.

## Pipeline Overview

```
Audio File → Director → Studio → Encoder → Platform Videos
            (timeline)  (render)  (variants)
```

### Stages

1. **Director**: Generates timeline.json from audio metadata
2. **Studio**: Renders video with Blender using timeline
3. **Encoder**: Creates platform-specific variants with FFmpeg

## Quick Start

### One-Command Video Generation

```bash
# Generate all platform variants
python run_batch.py --audio mashups/test.wav --song-id test_song

# Generate specific platforms only
python run_batch.py --audio mashups/test.wav --song-id test_song --platforms tiktok youtube

# Use different theme
python run_batch.py --audio mashups/test.wav --song-id test_song --theme mashup_chaos

# Skip Blender rendering (use existing raw video)
python run_batch.py --audio mashups/test.wav --song-id test_song --skip-studio
```

### Programmatic Usage

```python
from batch.runner import BatchRunner

runner = BatchRunner(
    audio_path="./mashups/test.wav",
    song_id="test_song",
    theme="sponsor_neon",
    mode="mashup",
    output_dir="./outputs"
)

outputs = runner.run(
    platforms=["tiktok", "youtube"],
    with_captions=True,
    with_thumbnail=True
)

print(f"Timeline: {outputs['timeline']}")
print(f"TikTok video: {outputs['video_tiktok']}")
print(f"YouTube video: {outputs['video_youtube']}")
```

## BatchRunner Class

### Constructor

```python
BatchRunner(
    audio_path: str,           # Path to audio file
    song_id: str,             # Song ID in ChromaDB
    theme: str = "sponsor_neon",  # Visual theme
    mode: str = "mashup",     # Output mode (mashup/single/event)
    output_dir: str = "./outputs"  # Base output directory
)
```

### run() Method

```python
outputs = runner.run(
    platforms: Optional[List[str]] = None,  # Platforms to create (None = all)
    with_captions: bool = True,            # Generate and burn captions
    with_thumbnail: bool = True,           # Generate thumbnail
    skip_studio: bool = False              # Skip Blender (for testing)
)
```

**Returns**: Dict mapping output type to Path
- `timeline`: Path to timeline.json
- `raw_video`: Path to raw Blender render
- `video_{platform}`: Path to each platform variant
- `thumbnail`: Path to thumbnail (if generated)

## Output Structure

```
outputs/
├── timeline/
│   └── test_song.json          # Timeline from Director
├── blender_temp/
│   └── test_song.mp4          # Raw render from Studio
└── renders/
    ├── test_song_tiktok.mp4   # TikTok variant (9:16)
    ├── test_song_reels.mp4    # Reels variant (9:16)
    ├── test_song_shorts.mp4   # Shorts variant (9:16)
    ├── test_song_youtube.mp4  # YouTube variant (16:9)
    ├── test_song.vtt          # WebVTT captions
    └── test_song_thumb.jpg    # Thumbnail
```

## Performance

### Typical Performance (30s video)

| Stage | Duration | Notes |
|-------|----------|-------|
| Director | 5-10s | Fast (metadata extraction) |
| Studio | 2-5min | Slowest (Blender rendering) |
| Encoder | 1-2min | 4 platforms sequentially |
| **Total** | **3-7min** | For all outputs |

### Benchmarking

Use the benchmark script to measure performance:

```bash
python scripts/benchmark_pipeline.py \
  --audio mashups/test.wav \
  --song-id test_song \
  --iterations 3
```

**Output**:
```
Benchmark Results
══════════════════════════════════════════════════════════════════════
Iterations: 3

Stage Performance (seconds):
──────────────────────────────────────────────────────────────────────
Stage                Mean       Median     Min        Max
──────────────────────────────────────────────────────────────────────
total_time          185.32     184.15     181.20     190.60
encoder             95.40      94.80      92.10      99.30
studio              82.15      82.00      80.50      84.00
director            7.77       7.50       7.20       8.60
──────────────────────────────────────────────────────────────────────

Throughput:
  Mean time per video: 185.32s
  Videos per minute: 0.32

Bottleneck Analysis:
  Slowest stage: encoder (51.5% of total time)
```

## Error Handling

### StageError

Each pipeline stage raises `StageError` with the stage name and original error:

```python
from batch.errors import StageError

try:
    outputs = runner.run()
except StageError as e:
    print(f"Stage failed: {e.stage}")
    print(f"Error: {e}")
    if e.original_error:
        print(f"Original: {e.original_error}")
```

### PipelineError

General pipeline failures raise `PipelineError`:

```python
from batch.errors import PipelineError

try:
    outputs = runner.run()
except PipelineError as e:
    print(f"Pipeline failed: {e}")
```

## Configuration

The batch runner uses settings from `config.yaml`:

```yaml
director:
  default_theme: "sponsor_neon"
  drop_energy_threshold: 0.2

studio:
  blender_executable: "blender"
  render_timeout_sec: 600
  fps: 30

encoder:
  platforms:
    tiktok:
      resolution: [1080, 1920]
      video_bitrate: "5M"
```

## Dependencies

### Required

- **Blender**: For Studio stage (3D rendering)
- **FFmpeg**: For Encoder stage (video encoding)
- **ChromaDB**: For song metadata storage

### Optional

- **Mixer**: For audio mashup creation (can use pre-existing audio files)

## Integration with Mixer

The batch pipeline works seamlessly with Mixer:

```bash
# Create mashup with Mixer
python -m mixer auto song_a.mp3

# Generate videos with Batch
python run_batch.py --audio mashups/song_a_x_auto.wav --song-id song_a_x_auto
```

## Advanced Usage

### Custom Output Directory

```python
runner = BatchRunner(
    audio_path="./test.wav",
    song_id="test_song",
    output_dir="./custom_outputs"
)
```

### Skip Studio (Use Existing Raw Video)

Useful for testing encoder without re-rendering:

```python
outputs = runner.run(skip_studio=True)
```

### Selective Platform Generation

```python
# Only create TikTok and YouTube
outputs = runner.run(platforms=["tiktok", "youtube"])
```

### No Captions or Thumbnail

```python
outputs = runner.run(
    with_captions=False,
    with_thumbnail=False
)
```

## Testing

### Unit Tests

```bash
pytest tests/batch/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v -s -m integration
```

**Note**: Integration tests require full setup (Blender, FFmpeg, ChromaDB with test data) and are slow.

## Performance Optimization

### Parallel Encoding (Future)

Currently, platform variants are created sequentially. Parallel encoding could reduce total time by ~50%:

```python
# Planned for future release
outputs = runner.run(
    parallel_encoding=True  # Encode all platforms concurrently
)
```

### Caching

The pipeline caches intermediate outputs:

- Timeline.json can be reused if audio unchanged
- Raw video can be reused for different encoder settings

## Troubleshooting

### "Blender not found"

Ensure Blender is installed and on PATH, or set in config.yaml:

```yaml
studio:
  blender_executable: "/path/to/blender"
```

### "FFmpeg not found"

Install FFmpeg from https://ffmpeg.org/download.html

### "Song not found in ChromaDB"

Ensure the song has been analyzed by Mixer:

```bash
python -m mixer analyze <song-id>
```

### Pipeline hangs at Studio stage

Check Blender logs in the console output. Common issues:
- Missing assets (use `--skip-studio` for testing)
- Timeout (increase `studio.render_timeout_sec` in config)

## See Also

- `director/README.md` - Timeline generation details
- `studio/assets/README.md` - Blender asset specifications
- `CROSSFADE_CLUB_PRD.md` - Complete product requirements
- `IMPLEMENTATION_PROGRESS.md` - Development roadmap
