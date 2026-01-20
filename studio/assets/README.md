# Studio Assets - User-Provided Files

This directory contains Blender assets required for rendering the Crossfade Club DJ avatar.

**IMPORTANT**: These assets are **NOT** included in the repository. You must provide your own .blend files.

## Required Assets

### 1. Avatar Base (`avatar_base.blend`)

The main DJ character rig.

**Specifications**:
- Rigged humanoid character (Rigify or custom rig)
- Named armature: `Avatar_Rig`
- Default pose: Standing at DJ booth, hands on decks
- UV-mapped and textured
- Compatible with Blender 3.6+

**Recommended Structure**:
- Head bone: `head`
- Spine bones: `spine`, `spine.001`, `spine.002`
- Arm bones: `upper_arm.L`, `upper_arm.R`, `forearm.L`, `forearm.R`
- Hand bones: `hand.L`, `hand.R`

### 2. Studio Environment (`studio_default.blend`)

The DJ booth environment.

**Specifications**:
- Camera named `Camera` positioned for medium shot
- Lighting rig (3-point or studio setup)
- DJ booth mesh with:
  - Left deck (position: X=-0.5)
  - Right deck (position: X=0.5)
  - Crossfader (center position)
- Background elements (optional)

**Scene Settings**:
- Units: Metric
- Frame rate: 30 FPS
- Render engine: EEVEE (for speed)

### 3. Action Clips (`actions/`)

Pre-baked animations for the avatar.

#### Required Actions

| File | Animation | Duration | Description |
|------|-----------|----------|-------------|
| `idle_bob.blend` | Idle head bob | 2.0s loop | Subtle bobbing to beat |
| `deck_scratch_L.blend` | Left deck scratch | 0.8s | Left hand scratches left deck |
| `deck_scratch_R.blend` | Right deck scratch | 0.8s | Right hand scratches right deck |
| `crossfader_hit.blend` | Crossfader hit | 1.0s | Quick crossfader slide |
| `drop_reaction.blend` | Drop reaction | 1.5s | Energetic reaction (head throw, arms up) |
| `spotlight_present.blend` | Spotlight present | 2.0s | Gesture towards audience/camera |

**Action Specifications**:
- Each file contains ONE action
- Action name matches filename (e.g., "idle_bob" action in `idle_bob.blend`)
- All actions use the same armature structure as `avatar_base.blend`
- Start frame: 1
- Loopable: `idle_bob` (others are one-shots)

## Asset Creation Workflow

### Option 1: Create Your Own

1. Model or download a rigged character
2. Create the DJ booth environment
3. Animate the 6 required actions
4. Export each as separate .blend files

**Resources**:
- Character rigs: Mixamo, Rigify, ManuelBastioni LAB
- DJ booth references: Pinterest, ArtStation
- Animation tutorials: Blender Guru, CG Cookie

### Option 2: Use Placeholder Assets (Testing)

For testing the pipeline without assets:

```bash
# Run with placeholder mode (generates blank frames)
python -m studio.renderer \
  --timeline timeline.json \
  --output test.mp4 \
  --placeholder-mode
```

## File Organization

```
studio/assets/
├── README.md (this file)
├── avatar_base.blend
├── studio_default.blend
├── actions/
│   ├── idle_bob.blend
│   ├── deck_scratch_L.blend
│   ├── deck_scratch_R.blend
│   ├── crossfader_hit.blend
│   ├── drop_reaction.blend
│   └── spotlight_present.blend
└── textures/ (optional)
    ├── avatar_diffuse.png
    ├── booth_material.png
    └── ...
```

## Validation

Check if your assets are valid:

```bash
python -c "from studio.asset_loader import validate_assets; print(validate_assets())"
```

**Expected Output** (when all assets present):
```
(True, [])
```

**If assets missing**:
```
(False, ['avatar_base.blend', 'actions/idle_bob.blend', ...])
```

## Technical Notes

### Coordinate System
- Forward: -Y
- Up: Z
- Avatar faces camera (forward direction)

### Scale
- Avatar height: ~1.8 Blender units (realistic human scale)
- DJ booth: Proportional to avatar

### Materials
- Use principled BSDF for all materials
- Keep shader complexity moderate for EEVEE
- Avoid heavy procedural textures

### Rendering
- The renderer will:
  - Load `studio_default.blend`
  - Append avatar from `avatar_base.blend`
  - Apply action clips from `actions/` based on timeline events
  - Render to video (MP4, H.264)

## Licensing

**Your Responsibility**: Ensure you have rights to use any character models, textures, or animations.

- Original creations: You own the rights
- Downloaded assets: Check license (CC0, CC-BY, etc.)
- Commercial use: Ensure license permits it

The Mixer/Crossfade Club system itself is [LICENSE], but assets you provide are subject to their own licenses.

## Support

If you create high-quality assets and want to share with the community, consider:
- Uploading to Blender Market (paid)
- Sharing on Blend Swap (free)
- Creating a tutorial video

**Note**: The core development team does NOT provide pre-made assets to avoid legal complexities.
