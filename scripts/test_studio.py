"""Test script for Studio rendering (Milestone 2).

Tests the Blender integration and rendering pipeline.

NOTE: This requires Blender to be installed and accessible on PATH.
"""

import argparse
from pathlib import Path
from studio.renderer import render_video, check_render_health


def main():
    parser = argparse.ArgumentParser(description="Test Studio rendering")
    parser.add_argument("--timeline", required=True, help="Path to timeline.json")
    parser.add_argument("--output", default="./outputs/blender_temp/test.mp4", help="Output video path")
    parser.add_argument("--format", default="short", choices=["short", "long"], help="Video format")
    parser.add_argument("--duration", type=float, help="Override duration (for testing)")
    parser.add_argument("--placeholder", action="store_true", help="Placeholder mode (no assets required)")

    args = parser.parse_args()

    print(f"Studio Test - Milestone 2")
    print(f"{'='*60}")
    print(f"Timeline: {args.timeline}")
    print(f"Output: {args.output}")
    print(f"Format: {args.format}")
    if args.duration:
        print(f"Duration override: {args.duration}s")
    if args.placeholder:
        print(f"Placeholder mode: ENABLED (no assets required)")
    print(f"{'='*60}\n")

    # Check if timeline exists
    timeline_path = Path(args.timeline)
    if not timeline_path.exists():
        print(f"✗ Timeline not found: {timeline_path}")
        print(f"\nGenerate a timeline first:")
        print(f"  python scripts/test_director.py --audio <audio> --song-id <id> --output {args.timeline}")
        return

    try:
        print("Starting Blender render...")
        print("This may take several minutes depending on duration and quality settings.\n")

        # Render video
        result_path = render_video(
            timeline_path=str(timeline_path),
            output_path=args.output,
            format_type=args.format,
            duration_override=args.duration,
            placeholder_mode=args.placeholder
        )

        print(f"\n✓ Render complete: {result_path}")

        # Check health
        print(f"\nRunning health check...")
        health = check_render_health(str(result_path))

        print(f"  File exists: {'✓' if health['exists'] else '✗'}")
        print(f"  File size: {health['size_mb']:.2f} MB")
        print(f"  Is video: {'✓' if health['is_video'] else '✗'}")
        if health['has_h264']:
            print(f"  Codec: H.264 ✓")

        # Verify milestones
        print(f"\nMilestone 2 Verification:")
        checks = [
            ("Video file created (MP4)", health['exists']),
            ("File size >500KB", health['size_mb'] > 0.5),
            ("Contains H.264 video stream", health['has_h264']),
        ]

        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")

        all_passed = all(p for _, p in checks)
        if all_passed:
            print(f"\n🎉 Milestone 2 PASSED!")
        else:
            print(f"\n⚠ Some checks failed. Review output above.")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
