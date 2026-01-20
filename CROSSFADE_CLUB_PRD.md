# Crossfade Club — Mixer Visual DJ System
## Product Requirements Document (PRD)

**Version:** 1.0
**Date:** 2026-01-19
**Status:** Design Phase

---

## 1. Purpose

Build a fully automated, Python-first video production system that converts audio processed by the Mixer app into platform-optimized video content featuring a branded, animated cartoon DJ avatar.

The system must support:
- Creative mashups (primary content)
- Single-song intelligent formatting (events, awards, sponsors)
- Short-form discovery content
- Long-form YouTube retention content

The system must:
- Require zero manual animation
- Be batch-capable
- Be platform-aware
- Be legally and ethically structured
- Treat the avatar and studio as the brand and monetizable surface — not the music

---

## 2. Core Design Principles

1. **Audio drives everything; visuals are intentional, not reactive noise**
2. **Timeline metadata is authoritative**
3. **Shorts discover; long-form retains**
4. **One audio input → many outputs**
5. **Automation over polish**
6. **Music rights are never implicitly included**

---

## 3. System Architecture

```
Mixer (audio intelligence)
  ↓
  audio.wav + metadata
  ↓
Director Agent (visual intelligence)
  ↓
  timeline.json + captions.vtt + usage_manifest.txt
  ↓
Blender Studio (avatar + environment animation)
  ↓
FFmpeg Encoder (platform variants)
  ↓
Platform-ready video assets
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Mixer** | Audio intelligence, section detection, energy analysis |
| **Director** | Visual intelligence, timeline generation, event mapping |
| **Studio** | Blender integration, avatar animation, rendering |
| **Encoder** | FFmpeg encoding, platform variants, captions |
| **Batch Runner** | Orchestration, multi-output generation |

---

## 4. Supported Audio Modes

Mixer must support two mutually exclusive audio modes, selectable per run.

### Mode A — Mashup Mode

- Multiple source songs
- Creative blending / collision
- Used for:
  - Social discovery
  - Experimentation
  - Long-form DJ sessions

### Mode B — Single-Song Format Mode (Event Mode)

- One source song
- No remixing or creative alteration
- Intelligent trimming and formatting only
- Used for:
  - Award nominee intros
  - Sponsor segments
  - Announcements
  - Event openers

---

## 5. Event Safety Flag (Hard Guardrail)

Mixer must support an explicit flag:

```
event_safe = true | false
```

### When `event_safe = true`:

- ✅ Mashup mode is **disabled**
- ✅ Only single-song formatting is allowed
- ✅ Experimental audio transforms are **disabled**
- ✅ `usage_manifest.txt` is **mandatory**
- ✅ Output must be suitable for legal and licensing review

**Failure to meet these conditions must halt execution with actionable error.**

---

## 6. Mixer Responsibilities

Mixer is responsible for audio intelligence only, not rendering.

### Required Outputs (per run)

```
/output/
 ├── audio.wav
 ├── metadata.json        # Existing Mixer metadata
 └── usage_source.txt     # Source info for Director
```

**Note:** Director Agent will consume Mixer outputs to generate timeline.json.

---

## 7. Single-Song Format Mode — Audio Intelligence

When `mode = single_song` (and/or `event_safe = true`), Mixer must:

1. Analyze song structure (intro, verse, chorus, hook, drop)
2. Identify the most recognizable or emotionally strong segment
3. Trim or stitch to a target duration (default: 15–25 seconds)
4. Apply clean fade-in / fade-out
5. Preserve musical continuity (no jarring cuts)

**This is DJ-style formatting, not remixing.**

---

## 8. Minimum Song Length Enforcement

When `event_safe = true`:

- Input song must be **≥ 45 seconds**
- Shorter inputs must **fail with clear error**

### Error Message Format

```
ERROR: Event Safety Violation

Input audio is too short for event-safe mode.
Minimum duration: 45 seconds
Current duration: 32 seconds

Event-safe mode requires sufficient audio for intelligent
formatting without creative manipulation.

To fix:
  1. Provide a song ≥45 seconds
  2. Use mashup mode for short clips (set event_safe=false)
```

**Rationale:** Songs under 45 seconds don't allow for intelligent excerpt selection without creative manipulation, which violates event-safe guarantees.

---

## 9. Timeline Metadata (Authoritative)

`timeline.json` controls all animation and visual behavior.

### Required Schema (Minimum)

```json
{
  "mode": "mashup" | "single_song",
  "format": "short" | "long",
  "event_safe": true | false,
  "event_type": "none" | "award_intro" | "sponsor_intro",

  "duration_sec": 22.5,
  "bpm": 124,

  "energy_curve": [
    { "t": 0.0, "energy": 0.35 },
    { "t": 6.2, "energy": 0.85 },
    { "t": 12.0, "energy": 0.60 }
  ],

  "beats": [0.48, 0.96, 1.44, 1.92],

  "sections": [
    { "t": 0.0, "type": "intro", "energy": 0.35 },
    { "t": 6.2, "type": "hook", "energy": 0.85 },
    { "t": 18.0, "type": "outro", "energy": 0.40 }
  ],

  "events": [
    { "t": 0.0, "type": "hard_start" },
    { "t": 6.2, "type": "drop", "intensity": "high" },
    { "t": 12.5, "type": "spotlight" }
  ],

  "segments": [
    { "start": 0.0, "end": 5.0, "role": "hook" },
    { "start": 5.0, "end": 22.5, "role": "engagement" }
  ],

  "camera": {
    "base_shot": "medium",
    "movements": [
      { "t": 6.2, "action": "zoom_in", "duration": 2.0 },
      { "t": 18.0, "action": "pull_back", "duration": 1.5 }
    ]
  },

  "theme": "sponsor_neon"
}
```

---

## 10. Usage Manifest (Event Compliance)

For event or client-delivered work, Director must emit:

```
usage_manifest.txt
```

### Format

```
CROSSFADE CLUB — MUSIC USAGE MANIFEST
Generated: 2026-01-19 14:32:00 UTC
Output: award_intro_nominee_24.mp4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUDIO SOURCE
  Song Title: "Shape of You"
  Artist: Ed Sheeran
  Recording Reference: Atlantic Records, 2017

USAGE DETAILS
  Duration Used: 22.5 seconds
  Type of Use: Award Nominee Introduction
  Format Mode: Single-Song (Event Safe)
  Modifications: Intelligent trim + fade (no creative remix)

LICENSING NOTICE
  Music licensing is NOT included with this video.

  The client is responsible for securing:
    - Synchronization license (composition)
    - Master use license (recording)

  Clearance must be obtained before public performance,
  broadcast, or distribution.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For licensing questions, consult your music supervisor
or rights clearance team.
```

**Purpose:** Plain-text compliance artifact for client legal and licensing teams.

---

## 11. Avatar Asset Responsibility (IMPORTANT)

### Avatar and Studio Asset Provisioning

**Claude Code is NOT responsible for generating the avatar character or studio assets.**

All avatar meshes, rigs, textures, and studio assets will be **provided externally**.

### Claude Code Responsibilities (Limited to):

- Loading provided assets
- Animating provided rigs
- Positioning provided studio elements
- Rendering outputs

### Assumptions

- Avatar is fully rigged
- Required bones and controls are documented
- Studio assets are production-ready
- No character or asset generation is required

---

## 12. Avatar System Requirements

### Avatar Characteristics

- 3D cartoon
- Female
- Joyful, confident, mischievous
- Plush / puppet-inspired but original
- Merch-friendly proportions
- Clear hand and arm visibility

### Required Actions

**Always-on (energy-driven):**
- Head bob (synced to BPM)
- Upper body bounce

**Event-driven:**
- Left deck scratch
- Right deck scratch
- Crossfader hit
- Drop reaction
- Spotlight / presentation gesture

---

## 13. Studio Environment

### Modular DJ Booth

**Swappable elements:**
- Lighting
- Background panels
- Sponsor signage

### Sponsor Branding Rules

- Sponsor logos are **static by default**
- **No animation, distortion, or timing shifts**
- Logos may be affected only by:
  - Lighting spill
  - Camera parallax
  - Depth of field

**Animated sponsor elements require explicit approval flags.**

---

## 14. Visual Behavior Mapping

### Mashup Mode

- High motion density
- Frequent deck switching
- Emphasis on collision moments

### Single-Song / Event Mode

- Smoother motion
- Fewer gestures
- Confident "presentation" energy

### Example Logic

```python
if mode == "single_song":
    gesture_frequency *= 0.6
    head_bob_gain *= 0.8
```

---

## 15. Hook Engineering (Mandatory)

Applies to all short-form outputs.

### First 1 Second Rules

- ✅ No silence
- ✅ Avatar moves on frame 1
- ✅ Camera already framed
- ✅ Audio and motion hit together
- ❌ No fade-ins
- ❌ No static openers

**Goal:** Immediate engagement for TikTok/Reels/Shorts algorithm.

---

## 16. Short-Form Render Mode (9:16)

**Resolution:** 1080×1920
**Duration:** 15–40 seconds
**Pacing:** Aggressive
**Animation Gain:** High

**Used for:**
- TikTok
- Instagram Reels
- YouTube Shorts

---

## 17. Long-Form Render Mode (16:9)

**Resolution:** 1920×1080
**Duration:** 2–6 minutes
**Pacing:** Smooth
**Overlays:** Minimal

### Retention Mechanics

Micro visual variation every 20–30 seconds:
- Lighting shifts
- Camera nudges
- Subtle avatar behavior changes
- No abrupt visual or audio stops

**Goal:** "Leave-on-able" content for background listening.

---

## 18. YouTube Enhancements

### Auto Chapters

Generated from `sections[]` in timeline.json:

```
0:00 Intro
0:15 Hook
1:30 Drop
3:45 Outro
```

### Thumbnail Render Pass

- Expressive avatar pose
- Studio visible
- No song references unless explicitly approved

---

## 19. Caption System

### Caption Generation

- Whisper already integrated in Mixer
- VTT always generated
- Burn-in captions:
  - **ON by default** for Shorts (9:16)
  - **OFF by default** for long-form (16:9)

### Platform-Specific Caption Styling

```yaml
# config/captions.yaml
tiktok:
  font: "Montserrat-Bold"
  size: 72
  color: white
  outline: black (4px)
  position: center_bottom
  animation: word_pop  # Each word scales in on beat

youtube_shorts:
  font: "Roboto-Bold"
  size: 64
  color: yellow
  outline: black (3px)
  position: lower_third
  animation: fade_in

instagram_reels:
  font: "Montserrat-Bold"
  size: 68
  color: white
  outline: black (4px)
  position: center_bottom
  animation: word_pop

youtube_long:
  font: "Roboto-Regular"
  size: 48
  color: white
  outline: black (2px)
  position: lower_third
  animation: fade_in
```

---

## 20. Batch Runner

### Single Command Example

```bash
python run_batch.py \
  --mode mashup \
  --format short,long \
  --count 10 \
  --theme sponsor_neon
```

### Event Mode Example

```bash
python run_batch.py \
  --mode single_song \
  --event_safe true \
  --event_type award_intro \
  --format short \
  --theme award_elegant
```

### Default Behavior

By default, generates **all platform variants**:
- TikTok 9:16
- Instagram Reels 9:16
- YouTube Shorts 9:16
- YouTube 16:9
- Thumbnail

### Opt-Out

```bash
python run_batch.py \
  --mode mashup \
  --skip-platforms reels,youtube_long
```

### Outputs

```
outputs/
├── renders/
│   ├── mashup_001_tiktok.mp4
│   ├── mashup_001_reels.mp4
│   ├── mashup_001_shorts.mp4
│   ├── mashup_001_youtube.mp4
│   └── mashup_001_thumbnail.jpg
├── timeline/
│   └── mashup_001_timeline.json
└── manifests/
    └── mashup_001_manifest.txt  (when event_safe=true)
```

---

## 21. Theme System

Themes control **lighting preset + color palette + studio variant**.

### Theme Definition

```yaml
# config/themes/sponsor_neon.yaml
name: "Sponsor Neon"
description: "High-energy, modern, brand-friendly"

lighting:
  primary: neon_blue
  accent: neon_pink
  intensity: high
  strobes: enabled

studio:
  background: cityscape_night
  booth_style: modern_glass

sponsor_zones:
  - position: left_panel
  - position: right_panel

avatar:
  energy_multiplier: 1.2
  gesture_frequency: high
```

### Included Themes (MVP)

| Theme | Use Case | Lighting | Energy |
|-------|----------|----------|--------|
| `sponsor_neon` | Brand content | High intensity, neon | High |
| `award_elegant` | Formal events | Warm, soft | Low |
| `mashup_chaos` | Creative content | Strobes, color shifts | Very High |
| `chill_lofi` | Relaxed content | Soft, muted | Low |

Themes can be expanded over time.

---

## 22. Camera System

### Camera Behaviors

**Base Shot:** Medium shot of avatar + decks

**Energy-Driven:**
- Slow zoom in during buildup
- Pull back on drop

**Retention Nudges (Long-Form):**
- Subtle position shifts every 20-30s
- ±5° rotation
- ±10% zoom

**Event-Triggered:**
- Close-up on spotlight gesture
- Wide shot on crossfader hit

### Format-Specific Framing

**Short-Form (9:16):**
- Tighter framing
- More camera motion
- Emphasize avatar

**Long-Form (16:9):**
- Wider framing
- Smoother motion
- Show full studio

---

## 23. Director Agent Responsibilities

The **Director Agent** is a new component that bridges Mixer and the video pipeline.

### Inputs

- `audio.wav` (from Mixer)
- `metadata.json` (from Mixer's Analyst agent)
- `usage_source.txt` (song info)

### Outputs

- `timeline.json` (authoritative animation script)
- `captions.vtt` (from Whisper)
- `usage_manifest.txt` (when event_safe=true)

### Core Functions

1. **Timeline Generation**
   - Convert Mixer's section metadata to visual events
   - Map beats to avatar actions
   - Generate camera paths

2. **Event Mapping**
   - Detect drops, hooks, buildups
   - Assign visual triggers (deck scratch, crossfader hit)
   - Apply mode-specific rules (mashup vs event)

3. **Theme Application**
   - Load theme configuration
   - Apply lighting/color/energy settings
   - Configure studio variant

4. **Safety Validation**
   - Enforce event_safe rules
   - Generate usage manifest
   - Validate minimum song length

---

## 24. Asset Specifications

### Avatar Rig Requirements

To ensure compatibility with Blender animation scripts:

**Required Bones:**
- `head` - Head position and rotation
- `neck` - Neck bend
- `spine` - Upper body rotation
- `shoulder.L` / `shoulder.R` - Shoulder movement
- `upper_arm.L` / `upper_arm.R` - Arm positioning
- `forearm.L` / `forearm.R` - Elbow bend
- `hand.L` / `hand.R` - Hand positioning

**Optional (Enhanced):**
- `eye.L` / `eye.R` - Eye tracking
- `jaw` - Mouth open/close
- `fingers.*` - Individual finger control

**Naming Convention:** Blender standard (lowercase, dot notation for L/R)

### Mesh Requirements

- **Poly Count:** 5,000–15,000 triangles (optimized for real-time preview)
- **Texture Resolution:** 2048×2048 (body), 1024×1024 (accessories)
- **Format:** `.blend` (native Blender)
- **UV Mapping:** Single UV map, no overlapping UVs

### Studio Asset Requirements

- **Background Panels:** Separate objects for easy swapping
- **DJ Booth:** Deck.L, Deck.R, Crossfader (named objects for camera tracking)
- **Lighting Rig:** Pre-configured light groups per theme
- **Sponsor Zones:** Empty objects marking logo placement areas

---

## 25. Animation Strategy (Hybrid Approach)

### Baked Animation Clips

Pre-created actions stored in avatar.blend:

- `idle_bob` - Looping head bob synced to BPM
- `deck_scratch_L` - Left deck scratch gesture
- `deck_scratch_R` - Right deck scratch gesture
- `crossfader_hit` - Crossfader push motion
- `drop_reaction` - Explosive energy burst
- `spotlight_present` - Arm raise, confident pose

### Procedural Modulation

Timeline-driven adjustments:

```python
# Pseudo-code
base_bob_intensity = 0.5
if energy > 0.7:
    bob_intensity = base_bob_intensity * 1.5

# Apply to existing animation
modulate_action("idle_bob", intensity=bob_intensity)
```

### Event Triggering

```python
if event["type"] == "drop":
    play_action("drop_reaction", start_time=event["t"])
    trigger_camera_move("zoom_in", duration=2.0)
```

**Benefits:**
- Quality motion from baked clips
- Responsive to audio via modulation
- Easy to swap avatar rigs (same action names)

---

## 26. Implementation Architecture

```
AI_Mixer/
├── mixer/              # Existing audio intelligence
│   └── (no changes to existing code)
│
├── director/           # NEW: Visual intelligence layer
│   ├── __init__.py
│   ├── timeline.py     # Generate timeline.json from Mixer metadata
│   ├── events.py       # Map audio moments to visual events
│   ├── camera.py       # Camera path generation
│   ├── themes.py       # Theme system
│   └── safety.py       # Event-safe validation
│
├── studio/             # NEW: Blender integration
│   ├── __init__.py
│   ├── avatar.py       # Avatar animation via bpy (Blender Python)
│   ├── environment.py  # Studio setup and lighting
│   ├── renderer.py     # Blender render orchestration
│   └── assets/         # Avatar rigs, studio models (user-provided)
│       ├── avatar_base.blend
│       ├── studio_default.blend
│       └── actions/    # Baked animation clips
│
├── encoder/            # NEW: FFmpeg final encoding
│   ├── __init__.py
│   ├── platform.py     # Platform-specific variants
│   ├── captions.py     # Burn-in captions
│   └── thumbnail.py    # Thumbnail generation
│
├── batch/              # NEW: Batch orchestration
│   ├── __init__.py
│   └── runner.py       # Main batch script entry point
│
├── config/
│   ├── themes/         # Theme YAML files
│   │   ├── sponsor_neon.yaml
│   │   ├── award_elegant.yaml
│   │   ├── mashup_chaos.yaml
│   │   └── chill_lofi.yaml
│   └── captions.yaml   # Caption styling per platform
│
└── outputs/
    ├── timeline/       # timeline.json outputs
    ├── renders/        # Final videos
    └── manifests/      # usage_manifest.txt files
```

---

## 27. Error Handling and Validation

### Event Safety Violations

**Trigger:** `event_safe=true` but mashup audio detected

```
ERROR: Event Safety Violation

Input audio contains multiple source songs (mashup detected).
Event-safe mode requires single-song inputs only.

To fix this:
  1. Use Mixer in single-song mode: --mode single_song
  2. Provide one audio file (not a mashup)
  3. Ensure event_safe=true flag is set

Current input: audio.wav (detected 2 sources)
Required: Single song ≥45 seconds
```

**Action:** Halt execution, do not render.

### Minimum Length Violations

**Trigger:** `event_safe=true` and song duration < 45 seconds

```
ERROR: Minimum Length Violation

Event-safe mode requires songs ≥45 seconds for intelligent formatting.

Current song: 32 seconds
Minimum required: 45 seconds

This ensures sufficient audio for excerpt selection without
creative manipulation.
```

**Action:** Halt execution.

### Missing Assets

**Trigger:** Avatar or studio assets not found

```
ERROR: Missing Asset

Required avatar rig not found: studio/assets/avatar_base.blend

Please ensure:
  1. Avatar rig is placed in studio/assets/
  2. File follows naming convention
  3. Rig contains required bones (see Asset Specifications)
```

**Action:** Halt execution with asset path.

---

## 28. Explicit Non-Goals

The system will **NOT** handle:

- ❌ Music licensing negotiation
- ❌ Monetization logic
- ❌ Rights management
- ❌ Live streaming
- ❌ Analytics ingestion (design hooks only for future)
- ❌ Avatar character generation (assets provided externally)
- ❌ Custom 3D modeling (use provided assets)

---

## 29. Success Criteria

### Technical Success

- ✅ Avatar motion feels intentional in all modes
- ✅ Hooks capture attention immediately (first 1 second)
- ✅ Long-form feels "leave-on-able"
- ✅ One command → complete asset set
- ✅ Beat-synced actions (±50ms accuracy)
- ✅ Batch processing of 10+ songs without manual intervention

### Legal Success

- ✅ Event outputs are legally clean and documented
- ✅ Usage manifests are clear and actionable
- ✅ event_safe flag prevents risky outputs

### Brand Success

- ✅ Consistent avatar appearance across all videos
- ✅ Studio environment reinforces brand identity
- ✅ Suitable for sponsor/client presentations

---

## 30. MVP Scope (Phase 1)

### In Scope

**Audio:**
- Mashup mode (existing Mixer functionality)
- Single-song format mode (new Mixer enhancement)
- Event-safe flag and validation

**Visual:**
- Director agent (timeline generation)
- Base avatar with 5 core actions (idle bob, 2x deck scratch, crossfader, drop reaction)
- Single studio environment
- 4 themes (sponsor_neon, award_elegant, mashup_chaos, chill_lofi)

**Output:**
- Short-form 9:16 (TikTok, Reels, Shorts)
- Long-form 16:9 (YouTube)
- Thumbnail generation
- Caption burn-in

**Batch:**
- Single command for multiple outputs
- Platform variants (all enabled by default)

### Out of Scope (Future Enhancements)

- ❌ Wardrobe system (outfit swapping)
- ❌ Props system (sunglasses, headphones, etc.)
- ❌ Multiple avatar characters
- ❌ Live performance mode
- ❌ Interactive parameter tuning UI
- ❌ Advanced camera choreography
- ❌ Real-time preview

**Rationale:** Start with base look and decide additions later. No growth, no need for other outfits and props yet. Focus on proving the brand concept first.

---

## 31. Future Enhancement: Wardrobe and Props System

**Status:** Not in MVP scope, documented for future consideration.

### Concept

With a properly rigged 3D character, outfits and props are **additional mesh layers** that follow the same skeleton.

### How It Would Work

**Base Character (One-Time Setup):**
```
avatar_base.blend
├── Rig (armature/skeleton) ← Never changes
├── Base mesh (body)
└── Default outfit
```

**Outfit Library (Future):**
```
outfits/
├── holiday_santa.blend       # Christmas mashups
├── summer_tank.blend          # Beach/summer vibes
├── award_elegant_dress.blend  # Formal events
├── sponsor_branded_hoodie.blend  # Sponsor content
└── retro_80s_jacket.blend     # Themed mashups
```

**Props Library (Future):**
```
props/
├── sunglasses_neon.blend
├── headphones_wireless.blend
├── drink_cup.blend
└── glow_sticks.blend
```

Props would parent to bones:
- Sunglasses → Head bone
- Headphones → Head bone
- Drink → Right hand bone
- Glow sticks → Both hand bones

### Timeline-Driven Customization (Future)

```json
{
  "avatar_outfit": "holiday_santa",
  "props": ["sunglasses_neon"],
  "prop_events": [
    {"t": 8.5, "action": "put_on_sunglasses"},
    {"t": 15.2, "action": "remove_sunglasses"}
  ]
}
```

### Cost Breakdown (If Implemented)

**Initial Investment:**
- Base rig: $300 (one-time)
- Default outfit: Included

**Growing Wardrobe (Optional):**
- Seasonal outfits: $80-150 each
- Props: $20-50 each
- Sponsored branded items: $75-150 per item

### Content Possibilities (Future)

- Seasonal content (Christmas, Halloween, Summer)
- Sponsor-branded wardrobe
- Song-specific theming (80s jacket for retro mashup)
- Event customization (formal dress for awards)

### Decision Point

Once brand is established and there's demand for variety:
- Assess engagement metrics
- Evaluate if outfit variations improve retention
- Commission wardrobe assets as needed

**For now:** Single base look is sufficient to test brand concept.

---

## 32. Development Phases

### Phase 1: Foundation (Weeks 1-2)
- Extend Mixer for single-song format mode
- Implement event_safe flag and validation
- Create Director agent skeleton

### Phase 2: Director Agent (Weeks 3-4)
- Timeline generation from Mixer metadata
- Event mapping logic
- Theme system implementation
- Usage manifest generation

### Phase 3: Studio Integration (Weeks 5-6)
- Blender Python integration
- Avatar loading and basic animation
- Studio environment setup
- Camera system

### Phase 4: Rendering Pipeline (Weeks 7-8)
- FFmpeg encoder
- Platform variants
- Caption burn-in
- Thumbnail generation

### Phase 5: Batch System (Week 9)
- Batch runner orchestration
- Multi-output generation
- Error handling and logging

### Phase 6: Testing & Refinement (Week 10)
- End-to-end testing with real songs
- Animation quality tuning
- Performance optimization

---

## 33. Technical Dependencies

### Python Packages (New)
- `bpy` - Blender Python API (requires Blender as Python module)
- `ffmpeg-python` - Already in Mixer requirements
- `Pillow` - Image processing for thumbnails

### System Dependencies (New)
- **Blender 3.6+** - 3D rendering (can be run headless)

### Existing Dependencies (From Mixer)
- librosa, whisper, demucs, yt-dlp (audio processing)
- ChromaDB, sentence-transformers (memory/matching)
- anthropic, openai (LLM semantic analysis)

---

## 34. Performance Targets

### Render Times (Target)

| Format | Duration | Target Render Time | Acceptable Max |
|--------|----------|-------------------|----------------|
| Short 9:16 | 15-30s | 2-4 minutes | 8 minutes |
| Long 16:9 | 2-6 min | 10-20 minutes | 45 minutes |
| Thumbnail | N/A | 30 seconds | 2 minutes |

**Hardware Assumption:** RTX 3060 or equivalent GPU

### Batch Processing

- 10 short-form videos: ~30-60 minutes total
- 5 long-form videos: ~90-120 minutes total

---

## 35. Final Notes

This PRD defines:

1. **A creative system** - Automated video production from audio
2. **A production system** - Batch-capable, platform-aware workflow
3. **A defensible legal posture** - Event-safe mode with usage manifests

Without turning the creator into:
- ❌ A licensing broker
- ❌ A negotiator
- ❌ A rights holder

It is intentionally:
- ✅ Modular
- ✅ Guardrailed
- ✅ Future-proof
- ✅ MVP-focused with clear expansion paths

---

**End of PRD**
