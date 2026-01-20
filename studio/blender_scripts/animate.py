"""Blender Animation Script - Runs INSIDE Blender Python environment.

This script is executed by Blender via `blender --python animate.py`.
It loads the timeline.json and renders the animated DJ avatar.

DO NOT run this script directly with system Python - it requires Blender's bpy module.
"""

import sys
import json
import argparse
from pathlib import Path


def main():
    """Main entry point for Blender script."""

    # Parse arguments passed after "--"
    # Blender command: blender --background --python animate.py -- --timeline foo.json --output bar.mp4
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="Render Crossfade Club animation")
    parser.add_argument("--timeline", required=True, help="Path to timeline.json")
    parser.add_argument("--output", required=True, help="Output video path")
    parser.add_argument("--format", default="short", choices=["short", "long"], help="Video format")
    parser.add_argument("--fps", type=int, default=30, help="Frame rate")
    parser.add_argument("--resolution", default="1080x1920", help="Resolution (WxH)")
    parser.add_argument("--samples", type=int, default=64, help="EEVEE samples")
    parser.add_argument("--engine", default="EEVEE", choices=["EEVEE", "CYCLES"], help="Render engine")
    parser.add_argument("--duration", type=float, help="Override duration (for testing)")
    parser.add_argument("--placeholder", action="store_true", help="Placeholder mode (no assets)")

    args = parser.parse_args(argv)

    print(f"\n{'='*60}")
    print(f"Crossfade Club - Blender Render")
    print(f"{'='*60}")
    print(f"Timeline: {args.timeline}")
    print(f"Output: {args.output}")
    print(f"Format: {args.format}")
    print(f"FPS: {args.fps}")
    print(f"Resolution: {args.resolution}")
    print(f"Samples: {args.samples}")
    print(f"Engine: {args.engine}")
    if args.duration:
        print(f"Duration override: {args.duration}s")
    if args.placeholder:
        print(f"Placeholder mode: ENABLED")
    print(f"{'='*60}\n")

    # Import bpy (Blender Python API) - only works inside Blender
    try:
        import bpy
    except ImportError:
        print("ERROR: This script must be run inside Blender, not with system Python!")
        print("Usage: blender --background --python animate.py -- --timeline foo.json --output bar.mp4")
        sys.exit(1)

    # Load timeline
    print("Loading timeline...")
    with open(args.timeline, "r") as f:
        timeline = json.load(f)

    print(f"  Duration: {timeline['meta']['duration_sec']:.1f}s")
    print(f"  BPM: {timeline['meta']['bpm']:.1f}")
    print(f"  Theme: {timeline['meta']['theme']}")
    print(f"  Events: {len(timeline['events'])}")

    # Setup scene
    print("\nSetting up scene...")
    setup_scene(bpy, args, timeline)

    if not args.placeholder:
        # Load assets
        print("\nLoading assets...")
        load_assets(bpy, timeline)

        # Apply animations
        print("\nApplying animations...")
        apply_animations(bpy, timeline)

        # Setup lighting
        print("\nSetting up lighting...")
        setup_lighting(bpy, timeline)

    # Setup camera
    print("\nSetting up camera...")
    setup_camera(bpy, timeline, args)

    # Render
    print("\nRendering...")
    render_video(bpy, args, timeline)

    print(f"\n✓ Render complete: {args.output}\n")


def setup_scene(bpy, args, timeline):
    """Configure Blender scene settings."""

    scene = bpy.context.scene

    # Set frame rate
    scene.render.fps = args.fps

    # Set resolution
    width, height = map(int, args.resolution.split('x'))
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100

    # Set render engine
    scene.render.engine = args.engine

    if args.engine == "EEVEE":
        scene.eevee.taa_render_samples = args.samples

    # Set output format
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.ffmpeg.audio_codec = 'NONE'  # Audio added later by encoder

    # Set frame range
    duration = args.duration if args.duration else timeline['meta']['duration_sec']
    end_frame = int(duration * args.fps)
    scene.frame_start = 1
    scene.frame_end = end_frame

    print(f"  Scene configured: {width}x{height} @ {args.fps}fps, {end_frame} frames")


def load_assets(bpy, timeline):
    """Load avatar and studio environment from .blend files."""

    # Get assets directory
    # NOTE: This assumes script is in studio/blender_scripts/
    assets_dir = Path(__file__).parent.parent / "assets"

    # Load studio environment
    studio_file = assets_dir / "studio_default.blend"
    if studio_file.exists():
        bpy.ops.wm.append(
            filepath=str(studio_file),
            directory=str(studio_file / "Object"),
            files=[{"name": "Studio"}],
            link=False
        )
        print(f"  Loaded studio: {studio_file.name}")
    else:
        print(f"  Warning: Studio file not found: {studio_file}")

    # Load avatar
    avatar_file = assets_dir / "avatar_base.blend"
    if avatar_file.exists():
        bpy.ops.wm.append(
            filepath=str(avatar_file),
            directory=str(avatar_file / "Object"),
            files=[{"name": "Avatar"}],
            link=False
        )
        print(f"  Loaded avatar: {avatar_file.name}")
    else:
        print(f"  Warning: Avatar file not found: {avatar_file}")


def apply_animations(bpy, timeline):
    """Apply action clips from timeline events."""

    avatar_triggers = timeline['avatar']['triggers']
    fps = bpy.context.scene.render.fps

    print(f"  Applying {len(avatar_triggers)} avatar triggers...")

    # Get avatar object
    avatar = bpy.data.objects.get("Avatar")
    if not avatar:
        print("  Warning: Avatar object not found, skipping animations")
        return

    # For each trigger, insert keyframes or apply action clips
    # NOTE: Simplified implementation - real version would load action .blend files
    for i, trigger in enumerate(avatar_triggers):
        t = trigger['t']
        action_name = trigger['action']
        duration = trigger['duration']

        frame = int(t * fps)

        print(f"    {i+1}. Frame {frame}: {action_name} ({duration}s)")

        # TODO: Load action from actions/{action_name}.blend and apply
        # For now, just log it


def setup_lighting(bpy, timeline):
    """Apply lighting from timeline theme."""

    lighting = timeline['lighting']
    primary_color = lighting['primary_color']

    print(f"  Primary color: RGB{tuple(primary_color)}")

    # Get or create key light
    if "Key_Light" in bpy.data.objects:
        key_light = bpy.data.objects["Key_Light"]
    else:
        # Create default light
        bpy.ops.object.light_add(type='AREA', location=(2, -2, 3))
        key_light = bpy.context.active_object
        key_light.name = "Key_Light"

    # Set color
    key_light.data.color = primary_color

    # Animate intensity based on curve
    intensity_curve = lighting['intensity_curve']
    fps = bpy.context.scene.render.fps

    for point in intensity_curve:
        frame = int(point['t'] * fps)
        intensity = point['value'] * 1000  # Scale to Watts

        key_light.data.energy = intensity
        key_light.data.keyframe_insert(data_path="energy", frame=frame)

    print(f"  Animated lighting: {len(intensity_curve)} keyframes")


def setup_camera(bpy, timeline, args):
    """Setup camera and apply movements."""

    camera_data = timeline['camera']
    movements = camera_data['movements']
    fps = bpy.context.scene.render.fps

    # Get or create camera
    if "Camera" in bpy.data.objects:
        camera = bpy.data.objects["Camera"]
    else:
        bpy.ops.object.camera_add(location=(0, -5, 1.6))
        camera = bpy.context.active_object
        camera.name = "Camera"

    bpy.context.scene.camera = camera

    print(f"  Base shot: {camera_data['base_shot']}")
    print(f"  Camera movements: {len(movements)}")

    # Apply camera movements
    for movement in movements:
        frame = int(movement['t'] * fps)
        action = movement['action']
        duration = movement['duration']

        # TODO: Apply actual camera movements (zoom, pan, etc.)
        print(f"    Frame {frame}: {action} ({duration}s)")


def render_video(bpy, args, timeline):
    """Execute the render."""

    scene = bpy.context.scene
    scene.render.filepath = args.output

    print(f"  Output: {args.output}")
    print(f"  Frames: {scene.frame_start}-{scene.frame_end}")
    print(f"  Rendering...")

    # Render animation
    bpy.ops.render.render(animation=True, write_still=False)

    print(f"  ✓ Render complete")


if __name__ == "__main__":
    main()
