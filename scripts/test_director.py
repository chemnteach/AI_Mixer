"""Test script for Director standalone functionality (Milestone 1).

Demonstrates timeline.json generation from Mixer metadata.
"""

import json
import argparse
from pathlib import Path
from director.timeline import generate_timeline
from director.safety import validate_event_safe, check_strobe_safety


def main():
    parser = argparse.ArgumentParser(description="Test Director timeline generation")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--song-id", required=True, help="Song ID in ChromaDB")
    parser.add_argument("--theme", default="sponsor_neon", help="Theme name")
    parser.add_argument("--mode", default="mashup", choices=["mashup", "single", "event"], help="Output mode")
    parser.add_argument("--format", default="short", choices=["short", "long"], help="Video format")
    parser.add_argument("--output", default="./outputs/timeline/test.json", help="Output path for timeline.json")
    parser.add_argument("--validate-safety", action="store_true", help="Run event-safe validation")

    args = parser.parse_args()

    print(f"Director Test - Milestone 1")
    print(f"{'='*60}")
    print(f"Audio: {args.audio}")
    print(f"Song ID: {args.song_id}")
    print(f"Theme: {args.theme}")
    print(f"Mode: {args.mode}")
    print(f"Format: {args.format}")
    print(f"Output: {args.output}")
    print(f"{'='*60}\n")

    try:
        print("Generating timeline...")
        timeline = generate_timeline(
            audio_path=args.audio,
            song_id=args.song_id,
            theme_name=args.theme,
            mode=args.mode,
            format_type=args.format,
            output_path=args.output
        )

        print(f"\n✓ Timeline generated successfully!")
        print(f"\nTimeline Summary:")
        print(f"  Duration: {timeline['meta']['duration_sec']:.1f}s")
        print(f"  BPM: {timeline['meta']['bpm']:.1f}")
        print(f"  Events detected: {len(timeline['events'])}")
        print(f"  Camera movements: {len(timeline['camera']['movements'])}")
        print(f"  Avatar triggers: {len(timeline['avatar']['triggers'])}")
        print(f"  Audio sections: {len(timeline['audio']['sections'])}")

        print(f"\nEvent Breakdown:")
        event_types = {}
        for event in timeline['events']:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1

        for etype, count in sorted(event_types.items()):
            print(f"  {etype}: {count}")

        # Safety validation
        if args.validate_safety:
            print(f"\nRunning safety validation...")
            is_safe, warnings = validate_event_safe(timeline, mode=args.mode, strict=False)

            if is_safe:
                print(f"  ✓ Event-safe validation passed")
            else:
                print(f"  ⚠ Event-safe warnings:")
                for warning in warnings:
                    print(f"    • {warning}")

            strobe_warnings = check_strobe_safety(timeline)
            if strobe_warnings:
                print(f"  ⚠ Strobe warnings:")
                for warning in strobe_warnings:
                    print(f"    • {warning}")

        print(f"\n✓ Timeline saved to: {args.output}")

        # Show first few events
        print(f"\nFirst 5 events:")
        for i, event in enumerate(timeline['events'][:5]):
            print(f"  {i+1}. {event['t']:.2f}s - {event['type']} ({event['intensity']}) → {event['visual_trigger']}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
