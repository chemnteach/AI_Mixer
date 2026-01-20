"""Crossfade Club - Batch Video Generation

Entry point for end-to-end pipeline:
  Mixer Audio → Director Timeline → Studio Render → Encoder Platforms

Usage:
  python run_batch.py --audio mashups/test.wav --song-id test_song
  python run_batch.py --audio mashups/test.wav --song-id test_song --platforms tiktok youtube
  python run_batch.py --audio mashups/test.wav --song-id test_song --theme mashup_chaos --mode mashup
"""

import sys
import argparse
from pathlib import Path

from batch.runner import BatchRunner
from batch.errors import PipelineError


def main():
    parser = argparse.ArgumentParser(
        description="Crossfade Club - Batch Video Generation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all platform variants with captions
  python run_batch.py --audio mashups/test.wav --song-id test_song

  # Generate specific platforms only
  python run_batch.py --audio mashups/test.wav --song-id test_song --platforms tiktok youtube

  # Use different theme
  python run_batch.py --audio mashups/test.wav --song-id test_song --theme mashup_chaos

  # Skip Blender rendering (use existing raw video)
  python run_batch.py --audio mashups/test.wav --song-id test_song --skip-studio
        """
    )

    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--song-id", required=True, help="Song ID in ChromaDB")
    parser.add_argument("--theme", default="sponsor_neon",
                       choices=["sponsor_neon", "award_elegant", "mashup_chaos", "chill_lofi"],
                       help="Visual theme (default: sponsor_neon)")
    parser.add_argument("--mode", default="mashup",
                       choices=["mashup", "single", "event"],
                       help="Output mode (default: mashup)")
    parser.add_argument("--platforms", nargs="+",
                       choices=["tiktok", "reels", "shorts", "youtube"],
                       help="Platforms to create (default: all)")
    parser.add_argument("--output-dir", default="./outputs",
                       help="Output directory (default: ./outputs)")
    parser.add_argument("--no-captions", action="store_true",
                       help="Skip caption generation")
    parser.add_argument("--no-thumbnail", action="store_true",
                       help="Skip thumbnail generation")
    parser.add_argument("--skip-studio", action="store_true",
                       help="Skip Blender rendering (use existing raw video)")

    args = parser.parse_args()

    # Validate audio file exists
    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"✗ Error: Audio file not found: {audio_path}")
        print(f"\nEnsure the audio file exists or use Mixer to create a mashup first:")
        print(f"  python -m mixer auto <song-or-url>")
        sys.exit(1)

    # Create batch runner
    runner = BatchRunner(
        audio_path=str(audio_path),
        song_id=args.song_id,
        theme=args.theme,
        mode=args.mode,
        output_dir=args.output_dir
    )

    try:
        # Run pipeline
        outputs = runner.run(
            platforms=args.platforms,
            with_captions=not args.no_captions,
            with_thumbnail=not args.no_thumbnail,
            skip_studio=args.skip_studio
        )

        print(f"✓ Success! Generated {len([k for k in outputs.keys() if k.startswith('video_')])} platform variants")
        print(f"\nOutputs saved to: {args.output_dir}")

        sys.exit(0)

    except PipelineError as e:
        print(f"\n✗ Pipeline Error: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n\n⚠ Pipeline interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
