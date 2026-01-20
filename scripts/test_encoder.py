"""Test script for Encoder platform variants (Milestone 3).

Tests FFmpeg encoding and platform-specific video generation.

NOTE: This requires FFmpeg to be installed and accessible on PATH.
"""

import argparse
from pathlib import Path
from encoder.platform import create_platform_variant, create_all_variants, get_video_info
from encoder.captions import create_simple_vtt
from encoder.thumbnail import generate_thumbnail


def main():
    parser = argparse.ArgumentParser(description="Test Encoder platform variants")
    parser.add_argument("--video", required=True, help="Path to input video (raw Blender render)")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--platform", default="tiktok",
                       choices=["tiktok", "reels", "shorts", "youtube", "all"],
                       help="Platform variant to create (or 'all')")
    parser.add_argument("--output-dir", default="./outputs/renders", help="Output directory")
    parser.add_argument("--base-name", default="test", help="Base filename")
    parser.add_argument("--with-captions", action="store_true", help="Add test captions")
    parser.add_argument("--with-thumbnail", action="store_true", help="Generate thumbnail")

    args = parser.parse_args()

    print(f"Encoder Test - Milestone 3")
    print(f"{'='*60}")
    print(f"Video: {args.video}")
    print(f"Audio: {args.audio}")
    print(f"Platform: {args.platform}")
    print(f"Output: {args.output_dir}")
    if args.with_captions:
        print(f"Captions: ENABLED")
    if args.with_thumbnail:
        print(f"Thumbnail: ENABLED")
    print(f"{'='*60}\n")

    # Check inputs exist
    video_path = Path(args.video)
    audio_path = Path(args.audio)

    if not video_path.exists():
        print(f"✗ Video not found: {video_path}")
        print(f"\nRender a video first:")
        print(f"  python scripts/test_studio.py --timeline <timeline> --output {args.video}")
        return

    if not audio_path.exists():
        print(f"✗ Audio not found: {audio_path}")
        return

    try:
        # Create VTT captions if requested
        vtt_file = None
        if args.with_captions:
            print("Creating test captions...")
            vtt_path = Path(args.output_dir) / f"{args.base_name}.vtt"
            vtt_file = str(create_simple_vtt(
                text="Test Caption - Crossfade Club",
                duration=30.0,  # Assume 30s for test
                output_path=str(vtt_path)
            ))
            print(f"  ✓ Created: {vtt_file}\n")

        # Create platform variants
        if args.platform == "all":
            print("Creating all platform variants...\n")

            results = create_all_variants(
                input_video=str(video_path),
                input_audio=str(audio_path),
                output_dir=args.output_dir,
                base_name=args.base_name,
                vtt_file=vtt_file
            )

            print(f"\n{'='*60}")
            print(f"Platform Variants Created:")
            for platform, output_path in results.items():
                print(f"  ✓ {platform}: {output_path}")

        else:
            print(f"Creating {args.platform} variant...\n")

            output_path = Path(args.output_dir) / f"{args.base_name}_{args.platform}.mp4"

            result_path = create_platform_variant(
                input_video=str(video_path),
                input_audio=str(audio_path),
                platform=args.platform,
                output_path=str(output_path),
                vtt_file=vtt_file
            )

            print(f"\n✓ Created: {result_path}")

            # Get video info
            print(f"\nVideo Info:")
            info = get_video_info(str(result_path))
            print(f"  Duration: {info['duration']:.1f}s")
            print(f"  Resolution: {info['resolution']}")
            print(f"  Codec: {info['codec']}")
            print(f"  Size: {info['size_mb']:.2f} MB")

        # Generate thumbnail if requested
        if args.with_thumbnail:
            print(f"\nGenerating thumbnail...")

            thumb_output = Path(args.output_dir) / f"{args.base_name}_thumb.jpg"

            if args.platform == "all":
                # Use first created variant
                first_platform = list(results.keys())[0]
                thumb_source = results[first_platform]
            else:
                thumb_source = result_path

            thumbnail_path = generate_thumbnail(
                video_path=str(thumb_source),
                output_path=str(thumb_output),
                timestamp=5.0,  # 5 seconds in
                width=1280,
                height=720
            )

            print(f"  ✓ Thumbnail: {thumbnail_path}")

        # Milestone 3 verification
        print(f"\n{'='*60}")
        print(f"Milestone 3 Verification:")

        if args.platform == "all":
            checks = [
                ("All 4 platform variants created", len(results) == 4),
                ("TikTok variant exists", "tiktok" in results),
                ("Reels variant exists", "reels" in results),
                ("Shorts variant exists", "shorts" in results),
                ("YouTube variant exists", "youtube" in results),
            ]
        else:
            info = get_video_info(str(result_path))
            checks = [
                ("Video file created (MP4)", result_path.exists()),
                ("File size >500KB", info['size_mb'] > 0.5),
                ("Has H.264 codec", info['codec'] == "h264"),
                ("Has audio + video", info['duration'] > 0),
            ]

        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")

        all_passed = all(p for _, p in checks)
        if all_passed:
            print(f"\n🎉 Milestone 3 PASSED!")
        else:
            print(f"\n⚠ Some checks failed. Review output above.")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
