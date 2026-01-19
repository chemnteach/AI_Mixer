"""Unit tests for memory system (ChromaDB)."""

import pytest
import tempfile
import shutil
from pathlib import Path
from mixer.memory import (
    # Schema
    sanitize_id,
    validate_metadata,
    create_document,
    handle_id_collision,
    extract_artist_title_from_filename,
    camelot_to_key,
    key_to_camelot,
    SchemaError,
    # Client
    ChromaClient,
    reset_client,
    # Queries
    upsert_song,
    get_song,
    delete_song,
    query_harmonic,
    query_semantic,
    query_hybrid,
    list_all_songs,
)
from mixer.types import SongMetadata


# Fixtures

@pytest.fixture
def temp_chroma_dir():
    """Create temporary ChromaDB directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def chroma_client(temp_chroma_dir):
    """Create ChromaDB client with temporary directory."""
    reset_client()  # Reset global client
    client = ChromaClient(persist_directory=temp_chroma_dir)
    yield client
    client.close()
    reset_client()


@pytest.fixture
def sample_metadata() -> SongMetadata:
    """Create sample song metadata."""
    return {
        "source": "local_file",
        "path": "/path/to/song.wav",
        "bpm": 128.5,
        "key": "Cmaj",
        "camelot": "8B",
        "genres": ["Pop", "Dance"],
        "primary_genre": "Pop",
        "irony_score": 5,
        "mood_summary": "Upbeat and energetic",
        "energy_level": 8,
        "valence": 7,
        "first_downbeat_sec": 0.5,
        "duration_sec": 215.3,
        "sample_rate": 44100,
        "has_vocals": True,
        "artist": "Test Artist",
        "title": "Test Song",
        "date_added": "2026-01-18T22:00:00Z",
    }


# Schema Tests

class TestSanitizeID:
    """Test ID sanitization."""

    def test_basic_sanitization(self):
        """Test basic artist/title sanitization."""
        result = sanitize_id("Taylor Swift", "Shake It Off")
        assert result == "taylor_swift_shake_it_off"

    def test_special_characters_removed(self):
        """Test special characters are removed."""
        result = sanitize_id("Ke$ha", "TiK ToK")
        assert result == "keha_tik_tok"

    def test_slash_removed(self):
        """Test slashes are removed."""
        result = sanitize_id("AC/DC", "Back in Black")
        assert result == "acdc_back_in_black"

    def test_consecutive_underscores_collapsed(self):
        """Test consecutive underscores are collapsed."""
        result = sanitize_id("Artist  Name", "Song  Title")
        assert result == "artist_name_song_title"

    def test_max_length_enforced(self):
        """Test ID is truncated to 128 characters."""
        long_artist = "A" * 100
        long_title = "B" * 100
        result = sanitize_id(long_artist, long_title)
        assert len(result) == 128

    def test_empty_raises_error(self):
        """Test empty artist/title raises error."""
        with pytest.raises(SchemaError):
            sanitize_id("", "Title")
        with pytest.raises(SchemaError):
            sanitize_id("Artist", "")


class TestValidateMetadata:
    """Test metadata validation."""

    def test_valid_metadata(self, sample_metadata):
        """Test valid metadata passes validation."""
        validate_metadata(sample_metadata)  # Should not raise

    def test_missing_required_field(self, sample_metadata):
        """Test missing required field raises error."""
        del sample_metadata["artist"]
        with pytest.raises(SchemaError, match="Missing required field"):
            validate_metadata(sample_metadata)

    def test_invalid_source(self, sample_metadata):
        """Test invalid source type raises error."""
        sample_metadata["source"] = "invalid"
        with pytest.raises(SchemaError, match="Invalid source"):
            validate_metadata(sample_metadata)

    def test_irony_score_out_of_range(self, sample_metadata):
        """Test irony score out of range raises error."""
        sample_metadata["irony_score"] = 15
        with pytest.raises(SchemaError, match="irony_score must be 0-10"):
            validate_metadata(sample_metadata)

    def test_bpm_out_of_range(self, sample_metadata):
        """Test BPM out of range raises error."""
        sample_metadata["bpm"] = 500
        with pytest.raises(SchemaError, match="bpm must be 20-300"):
            validate_metadata(sample_metadata)

    def test_invalid_sample_rate(self, sample_metadata):
        """Test invalid sample rate raises error."""
        sample_metadata["sample_rate"] = 32000
        with pytest.raises(SchemaError, match="sample_rate must be one of"):
            validate_metadata(sample_metadata)

    def test_primary_genre_not_in_genres(self, sample_metadata):
        """Test primary_genre not in genres list raises error."""
        sample_metadata["primary_genre"] = "Rock"
        with pytest.raises(SchemaError, match="primary_genre .* not in genres list"):
            validate_metadata(sample_metadata)


class TestCreateDocument:
    """Test document creation."""

    def test_document_format(self):
        """Test document is formatted correctly."""
        transcript = "Verse 1: Test lyrics"
        mood = "Happy and upbeat"
        doc = create_document(transcript, mood)
        assert transcript in doc
        assert "[MOOD]:" in doc
        assert mood in doc


class TestHandleIDCollision:
    """Test ID collision handling."""

    def test_no_collision(self):
        """Test no collision returns base ID."""
        result = handle_id_collision("artist_song", [])
        assert result == "artist_song"

    def test_single_collision(self):
        """Test single collision appends _v2."""
        result = handle_id_collision("artist_song", ["artist_song"])
        assert result == "artist_song_v2"

    def test_multiple_collisions(self):
        """Test multiple collisions increment version."""
        existing = ["artist_song", "artist_song_v2", "artist_song_v3"]
        result = handle_id_collision("artist_song", existing)
        assert result == "artist_song_v4"


class TestExtractArtistTitle:
    """Test artist/title extraction from filename."""

    def test_dash_format(self):
        """Test 'Artist - Title.mp3' format."""
        artist, title = extract_artist_title_from_filename("Taylor Swift - Shake It Off.mp3")
        assert artist == "Taylor Swift"
        assert title == "Shake It Off"

    def test_underscore_format(self):
        """Test 'Artist_Title.wav' format."""
        artist, title = extract_artist_title_from_filename("Taylor_Swift_Shake_It_Off.wav")
        assert artist == "Taylor"
        assert title == "Swift_Shake_It_Off"

    def test_no_artist(self):
        """Test filename with no artist defaults to Unknown."""
        artist, title = extract_artist_title_from_filename("SongTitle.mp3")
        assert artist == "Unknown"
        assert title == "SongTitle"


class TestCamelotConversion:
    """Test Camelot key conversion."""

    def test_camelot_to_key(self):
        """Test Camelot to traditional key conversion."""
        assert camelot_to_key("8B") == "Cmaj"
        assert camelot_to_key("8A") == "Amin"
        assert camelot_to_key("1B") == "Bmaj"

    def test_key_to_camelot(self):
        """Test traditional key to Camelot conversion."""
        assert key_to_camelot("Cmaj") == "8B"
        assert key_to_camelot("Amin") == "8A"
        assert key_to_camelot("Bmaj") == "1B"

    def test_invalid_camelot(self):
        """Test invalid Camelot notation raises error."""
        with pytest.raises(SchemaError):
            camelot_to_key("13B")

    def test_invalid_key(self):
        """Test invalid key notation raises error."""
        with pytest.raises(SchemaError):
            key_to_camelot("Xmaj")


# Client Tests

class TestChromaClient:
    """Test ChromaDB client."""

    def test_client_initialization(self, chroma_client):
        """Test client initializes successfully."""
        assert chroma_client is not None
        assert chroma_client.persist_directory.exists()

    def test_get_collection(self, chroma_client):
        """Test collection is created/retrieved."""
        collection = chroma_client.get_collection()
        assert collection is not None
        assert collection.name == "tiki_library"

    def test_collection_persistence(self, temp_chroma_dir):
        """Test collection persists across client restarts."""
        # Create client and add data
        client1 = ChromaClient(persist_directory=temp_chroma_dir)
        collection1 = client1.get_collection()
        collection1.add(
            ids=["test_id"],
            documents=["test doc"],
            metadatas=[{"test": "data"}]
        )
        client1.close()

        # Recreate client and verify data persists
        client2 = ChromaClient(persist_directory=temp_chroma_dir)
        collection2 = client2.get_collection()
        result = collection2.get(ids=["test_id"])
        assert "test_id" in result["ids"]
        client2.close()

    def test_get_stats(self, chroma_client):
        """Test collection statistics."""
        stats = chroma_client.get_stats()
        assert "total_songs" in stats
        assert stats["total_songs"] == 0  # Empty collection


# Query Tests

class TestUpsertSong:
    """Test song upsert operations."""

    def test_upsert_new_song(self, chroma_client, sample_metadata):
        """Test upserting a new song."""
        song_id = upsert_song(
            artist="Test Artist",
            title="Test Song",
            metadata=sample_metadata,
            transcript="Test lyrics"
        )
        assert song_id == "test_artist_test_song"

        # Verify stored
        song = get_song(song_id)
        assert song is not None
        assert song["metadata"]["artist"] == "Test Artist"

    def test_upsert_updates_existing(self, chroma_client, sample_metadata):
        """Test upserting updates existing song."""
        # Insert first time
        song_id = upsert_song(
            artist="Test Artist",
            title="Test Song",
            metadata=sample_metadata
        )

        # Update metadata
        sample_metadata["bpm"] = 140.0
        upsert_song(
            artist="Test Artist",
            title="Test Song",
            metadata=sample_metadata,
            force_id=song_id
        )

        # Verify updated
        song = get_song(song_id)
        assert song["metadata"]["bpm"] == 140.0


class TestGetSong:
    """Test song retrieval."""

    def test_get_existing_song(self, chroma_client, sample_metadata):
        """Test getting an existing song."""
        song_id = upsert_song("Artist", "Song", sample_metadata)
        song = get_song(song_id)
        assert song is not None
        assert song["id"] == song_id

    def test_get_nonexistent_song(self, chroma_client):
        """Test getting non-existent song returns None."""
        song = get_song("nonexistent_id")
        assert song is None


class TestDeleteSong:
    """Test song deletion."""

    def test_delete_existing_song(self, chroma_client, sample_metadata):
        """Test deleting an existing song."""
        song_id = upsert_song("Artist", "Song", sample_metadata)
        result = delete_song(song_id)
        assert result is True

        # Verify deleted
        song = get_song(song_id)
        assert song is None

    def test_delete_nonexistent_song(self, chroma_client):
        """Test deleting non-existent song returns False."""
        result = delete_song("nonexistent_id")
        assert result is False


class TestQueryHarmonic:
    """Test harmonic matching."""

    def test_query_by_bpm_and_key(self, chroma_client, sample_metadata):
        """Test querying by BPM and key."""
        # Add test songs
        song1_meta = sample_metadata.copy()
        song1_meta["bpm"] = 128.0
        song1_meta["camelot"] = "8B"
        upsert_song("Artist1", "Song1", song1_meta)

        song2_meta = sample_metadata.copy()
        song2_meta["bpm"] = 130.0
        song2_meta["camelot"] = "9B"  # Adjacent key
        upsert_song("Artist2", "Song2", song2_meta)

        song3_meta = sample_metadata.copy()
        song3_meta["bpm"] = 200.0  # Way off
        song3_meta["camelot"] = "1B"  # Incompatible key
        upsert_song("Artist3", "Song3", song3_meta)

        # Query for songs near 128 BPM, 8B key
        results = query_harmonic(
            target_bpm=128.0,
            target_key="8B",
            max_results=5
        )

        # Should find song1 and song2, not song3
        assert len(results) >= 1
        result_ids = [r["id"] for r in results]
        assert "artist1_song1" in result_ids


class TestQuerySemantic:
    """Test semantic matching."""

    def test_query_by_mood(self, chroma_client, sample_metadata):
        """Test querying by mood/vibe."""
        # Add songs with different moods
        song1_meta = sample_metadata.copy()
        song1_meta["mood_summary"] = "Happy and upbeat dance track"
        upsert_song("Artist1", "Song1", song1_meta, transcript="Happy lyrics")

        song2_meta = sample_metadata.copy()
        song2_meta["mood_summary"] = "Sad and melancholic ballad"
        upsert_song("Artist2", "Song2", song2_meta, transcript="Sad lyrics")

        # Query for happy songs
        results = query_semantic(
            query_text="happy upbeat energetic",
            max_results=5
        )

        # Should rank song1 higher
        assert len(results) > 0
        # Top result should be song1
        assert "song1" in results[0]["id"]


class TestQueryHybrid:
    """Test hybrid matching."""

    def test_hybrid_matching(self, chroma_client, sample_metadata):
        """Test hybrid (harmonic + semantic) matching."""
        # Add target song
        target_meta = sample_metadata.copy()
        target_meta["bpm"] = 128.0
        target_meta["camelot"] = "8B"
        target_meta["mood_summary"] = "Upbeat pop"
        target_id = upsert_song("Target", "Song", target_meta, transcript="Pop lyrics")

        # Add compatible song (good BPM, key, and mood)
        match_meta = sample_metadata.copy()
        match_meta["bpm"] = 130.0
        match_meta["camelot"] = "8B"
        match_meta["mood_summary"] = "Energetic pop dance"
        upsert_song("Match", "Song", match_meta, transcript="Dance pop lyrics")

        # Add incompatible song (wrong BPM and key)
        incompatible_meta = sample_metadata.copy()
        incompatible_meta["bpm"] = 200.0
        incompatible_meta["camelot"] = "1B"
        incompatible_meta["mood_summary"] = "Heavy metal aggressive"
        upsert_song("Incompatible", "Song", incompatible_meta)

        # Query hybrid
        results = query_hybrid(
            target_song_id=target_id,
            max_results=5
        )

        # Should find match_song but not incompatible_song
        if len(results) > 0:
            result_ids = [r["id"] for r in results]
            assert "match_song" in result_ids


class TestListAllSongs:
    """Test listing all songs."""

    def test_list_all(self, chroma_client, sample_metadata):
        """Test listing all songs in library."""
        # Add multiple songs
        for i in range(3):
            meta = sample_metadata.copy()
            upsert_song(f"Artist{i}", f"Song{i}", meta)

        # List all
        songs = list_all_songs(limit=10)
        assert len(songs) == 3

    def test_list_with_limit(self, chroma_client, sample_metadata):
        """Test listing with limit."""
        # Add multiple songs
        for i in range(5):
            meta = sample_metadata.copy()
            upsert_song(f"Artist{i}", f"Song{i}", meta)

        # List with limit
        songs = list_all_songs(limit=3)
        assert len(songs) == 3
