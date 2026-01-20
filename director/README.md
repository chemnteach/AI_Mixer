# Director Agent - Visual Intelligence Layer

The Director Agent translates Mixer's audio metadata into visual animation timelines for the Crossfade Club system.

## Overview

The Director is the **visual intelligence layer** that sits between Mixer (audio) and Blender (3D animation). It generates `timeline.json` files that serve as authoritative animation scripts.

## Key Components

### 1. Timeline Generation (`timeline.py`)

Main entry point for generating complete timelines:

```python
from director.timeline import generate_timeline

timeline = generate_timeline(
    audio_path="./mashups/song_a_x_song_b.wav",
    song_id="song_a_x_song_b",
    theme_name="sponsor_neon",
    mode="mashup",
    format_type="short",
    output_path="./outputs/timeline/test.json"
)
```

### 2. Event Detection (`events.py`)

Detects visual triggers from audio sections:

- **Energy drops**: Sudden energy spikes trigger "drop_reaction" animations
- **Section changes**: Verse→Chorus transitions trigger "crossfader_hit"
- **Hard starts**: High-energy intros trigger immediate reactions
- **Retention nudges**: Periodic subtle actions to maintain viewer engagement

### 3. Camera Path Generation (`camera.py`)

Generates camera movements based on events:

- **Zoom on drops**: Camera zooms in during energy spikes
- **Retention nudges**: Subtle left/right camera movements
- **Movement optimization**: Removes overlapping camera actions

### 4. Theme System (`themes.py`)

Loads visual presets from YAML configs:

```yaml
# config/themes/sponsor_neon.yaml
lighting:
  primary_color: [0.0, 0.6, 1.0]  # Cyan blue
  strobes_enabled: true
avatar:
  energy_multiplier: 1.2  # Amplified movements
camera:
  zoom_on_drop: true
```

**Available Themes**:
- `sponsor_neon` - High-energy branded content
- `award_elegant` - Sophisticated, event-safe
- `mashup_chaos` - Maximum visual mayhem
- `chill_lofi` - Relaxed, downtempo

### 5. Safety Validation (`safety.py`)

Ensures event-safe outputs for client work:

```python
from director.safety import validate_event_safe

is_safe, warnings = validate_event_safe(timeline, mode="event", strict=True)
```

## Timeline.json Structure

```json
{
  "meta": {
    "mode": "mashup",
    "format": "short",
    "theme": "sponsor_neon",
    "duration_sec": 185.3,
    "bpm": 128.0
  },
  "audio": {
    "file": "./mashups/song_a_x_song_b.wav",
    "sections": [/* from Mixer */]
  },
  "beats": {
    "timestamps": [0.0, 0.48, 0.96, ...],
    "bpm": 128.0,
    "downbeats": [0.0, 1.92, 3.84, ...]
  },
  "events": [
    {
      "t": 15.2,
      "type": "drop",
      "intensity": "high",
      "visual_trigger": "drop_reaction",
      "reason": "Energy jump 0.35→0.85"
    }
  ],
  "camera": { /* movements */ },
  "avatar": { /* triggers */ },
  "lighting": { /* intensity curve */ }
}
```

## Usage Examples

### Basic Timeline Generation

```bash
python scripts/test_director.py \
  --audio ./mashups/test.wav \
  --song-id "test_song" \
  --theme sponsor_neon \
  --output ./outputs/timeline/test.json
```

### With Safety Validation

```bash
python scripts/test_director.py \
  --audio ./library/wedding_song.wav \
  --song-id "wedding_song" \
  --theme award_elegant \
  --mode event \
  --validate-safety
```

## Testing

Run the comprehensive test suite:

```bash
pytest tests/director/ -v
```

**Test Coverage**:
- Theme loading and color extraction
- Event detection (drops, section changes, retention)
- Camera path generation and optimization
- Safety validation and strobe checking

## Integration with Mixer

The Director reads section-level metadata directly from Mixer's ChromaDB:

```python
from mixer.memory import get_song

song_data = get_song(song_id)
sections = song_data["metadata"]["sections"]  # SectionMetadata[]
```

**Key Fields Used**:
- `energy_level` → Detect drops
- `section_type` → Trigger transitions
- `emotional_tone` → Lighting mood
- `bpm` → Beat grid alignment

## Next Steps

Phase 2 (Weeks 3-4) will implement the **Studio module** to render these timelines in Blender with an animated DJ avatar.
