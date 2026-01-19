"""Quick demo script to test memory system functionality.

Run this after installing dependencies:
    pip install -r requirements.txt
    python scripts/test_memory_demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mixer.memory import (
    get_client,
    reset_client,
    upsert_song,
    get_song,
    query_harmonic,
    query_semantic,
    query_hybrid,
    list_all_songs,
)
from mixer.types import SongMetadata


def main():
    """Run memory system demo."""
    print("=" * 60)
    print("The Mixer - Memory System Demo")
    print("=" * 60)

    # Reset client to start fresh
    reset_client()
    client = get_client()
    collection = client.get_collection()

    print(f"\n✓ ChromaDB initialized at: {client.persist_directory}")
    print(f"✓ Collection: {collection.name}")
    print(f"✓ Current song count: {collection.count()}")

    # Create sample songs
    print("\n" + "=" * 60)
    print("Adding Sample Songs")
    print("=" * 60)

    songs = [
        {
            "artist": "Taylor Swift",
            "title": "Shake It Off",
            "metadata": {
                "source": "youtube",
                "path": "./library_cache/taylor_swift_shake_it_off.wav",
                "bpm": 160.0,
                "key": "Gmaj",
                "camelot": "9B",
                "genres": ["Pop"],
                "primary_genre": "Pop",
                "irony_score": 3,
                "mood_summary": "Upbeat and carefree pop anthem",
                "energy_level": 9,
                "valence": 9,
                "first_downbeat_sec": 0.5,
                "duration_sec": 219.0,
                "sample_rate": 44100,
                "has_vocals": True,
                "artist": "Taylor Swift",
                "title": "Shake It Off",
            },
            "transcript": "I stay out too late, got nothing in my brain...",
        },
        {
            "artist": "Johnny Cash",
            "title": "Ring of Fire",
            "metadata": {
                "source": "local_file",
                "path": "./library_cache/johnny_cash_ring_of_fire.wav",
                "bpm": 152.0,
                "key": "Gmaj",
                "camelot": "9B",
                "genres": ["Country", "Rock"],
                "primary_genre": "Country",
                "irony_score": 2,
                "mood_summary": "Passionate country ballad with mariachi horns",
                "energy_level": 7,
                "valence": 6,
                "first_downbeat_sec": 0.3,
                "duration_sec": 156.0,
                "sample_rate": 44100,
                "has_vocals": True,
                "artist": "Johnny Cash",
                "title": "Ring of Fire",
            },
            "transcript": "Love is a burning thing, and it makes a fiery ring...",
        },
        {
            "artist": "Daft Punk",
            "title": "Around the World",
            "metadata": {
                "source": "youtube",
                "path": "./library_cache/daft_punk_around_the_world.wav",
                "bpm": 121.0,
                "key": "Cmaj",
                "camelot": "8B",
                "genres": ["Electronic", "House"],
                "primary_genre": "Electronic",
                "irony_score": 8,
                "mood_summary": "Repetitive electronic house with minimal vocals",
                "energy_level": 8,
                "valence": 7,
                "first_downbeat_sec": 0.0,
                "duration_sec": 429.0,
                "sample_rate": 44100,
                "has_vocals": True,
                "artist": "Daft Punk",
                "title": "Around the World",
            },
            "transcript": "Around the world, around the world... (repeated)",
        },
    ]

    for song in songs:
        song_id = upsert_song(
            artist=song["artist"],
            title=song["title"],
            metadata=song["metadata"],
            transcript=song["transcript"],
        )
        print(f"  ✓ Added: {song['artist']} - {song['title']} (ID: {song_id})")

    # Test retrieval
    print("\n" + "=" * 60)
    print("Testing Song Retrieval")
    print("=" * 60)

    song = get_song("taylor_swift_shake_it_off")
    if song:
        print(f"  ✓ Retrieved: {song['metadata']['artist']} - {song['metadata']['title']}")
        print(f"    BPM: {song['metadata']['bpm']}, Key: {song['metadata']['camelot']}")
        print(f"    Mood: {song['metadata']['mood_summary']}")

    # Test harmonic matching
    print("\n" + "=" * 60)
    print("Testing Harmonic Matching")
    print("=" * 60)
    print("  Query: BPM=160, Key=9B (like 'Shake It Off')")

    harmonic_matches = query_harmonic(
        target_bpm=160.0,
        target_key="9B",
        max_results=5,
    )

    for i, match in enumerate(harmonic_matches, 1):
        print(f"  {i}. {match['metadata']['artist']} - {match['metadata']['title']}")
        print(f"     Score: {match['compatibility_score']:.2f}")
        print(f"     {match['match_reasons'][0]}")

    # Test semantic matching
    print("\n" + "=" * 60)
    print("Testing Semantic Matching")
    print("=" * 60)
    print("  Query: 'ironic electronic repetitive'")

    semantic_matches = query_semantic(
        query_text="ironic electronic repetitive",
        max_results=5,
    )

    for i, match in enumerate(semantic_matches, 1):
        print(f"  {i}. {match['metadata']['artist']} - {match['metadata']['title']}")
        print(f"     Score: {match['compatibility_score']:.2f}")
        print(f"     Mood: {match['metadata']['mood_summary'][:50]}...")

    # Test hybrid matching
    print("\n" + "=" * 60)
    print("Testing Hybrid Matching")
    print("=" * 60)
    print("  Target: 'Johnny Cash - Ring of Fire'")

    hybrid_matches = query_hybrid(
        target_song_id="johnny_cash_ring_of_fire",
        max_results=5,
    )

    for i, match in enumerate(hybrid_matches, 1):
        print(f"  {i}. {match['metadata']['artist']} - {match['metadata']['title']}")
        print(f"     Hybrid Score: {match['compatibility_score']:.2f}")
        for reason in match['match_reasons'][:2]:
            print(f"     - {reason}")

    # Show collection stats
    print("\n" + "=" * 60)
    print("Collection Statistics")
    print("=" * 60)

    stats = client.get_stats()
    print(f"  Total songs: {stats['total_songs']}")
    print(f"  Unique genres: {stats['unique_genres']}")
    print(f"  Top genres: {', '.join(stats['top_genres'])}")
    print(f"  Songs with vocals: {stats['songs_with_vocals']}")

    print("\n" + "=" * 60)
    print("✓ Demo Complete!")
    print("=" * 60)
    print(f"\nChromaDB persisted to: {client.persist_directory}")
    print("Run this script again to see data persistence across sessions.")


if __name__ == "__main__":
    main()
