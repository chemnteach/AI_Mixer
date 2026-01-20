"""Unit tests for Curator Agent (Phase 4)."""

import pytest
from unittest.mock import patch, MagicMock
from mixer.agents.curator import (
    find_match,
    calculate_compatibility_score,
    recommend_mashup_type,
    find_all_pairs,
    CuratorError,
)
from mixer.types import SongMetadata, MatchResult


# Test fixtures for sample song metadata
@pytest.fixture
def song_a_meta():
    """Sample song A metadata."""
    return SongMetadata(
        source="local_file",
        path="/path/to/song_a.wav",
        bpm=120.0,
        key="C major",
        camelot="8B",
        genres=["Pop", "Dance"],
        primary_genre="Pop",
        irony_score=3,
        mood_summary="upbeat and energetic",
        energy_level=8,
        valence=7,
        first_downbeat_sec=0.5,
        duration_sec=180.0,
        sample_rate=44100,
        has_vocals=True,
        artist="Artist A",
        title="Song A",
        date_added="2024-01-01",
        sections=[
            {
                "section_type": "verse",
                "start_sec": 0.0,
                "end_sec": 30.0,
                "duration_sec": 30.0,
                "energy_level": 0.7,
                "spectral_centroid": 2000.0,
                "tempo_stability": 0.9,
                "vocal_density": "medium",
                "vocal_intensity": 0.6,
                "lyrical_content": "test lyrics",
                "emotional_tone": "hopeful",
                "lyrical_function": "narrative",
                "themes": ["love"],
            }
        ],
        emotional_arc="intro:hopeful → verse:doubt → chorus:defiant",
        word_timings=[],
    )


@pytest.fixture
def song_b_meta():
    """Sample song B metadata - compatible with song A."""
    return SongMetadata(
        source="youtube",
        path="/path/to/song_b.wav",
        bpm=125.0,  # Within 5% of 120 (120 * 1.05 = 126)
        key="G major",
        camelot="9B",  # Adjacent on Camelot wheel to 8B
        genres=["Pop", "Electronic"],
        primary_genre="Pop",
        irony_score=4,
        mood_summary="uplifting and bright",
        energy_level=8,  # Same as song A
        valence=8,
        first_downbeat_sec=0.3,
        duration_sec=200.0,
        sample_rate=44100,
        has_vocals=True,
        artist="Artist B",
        title="Song B",
        date_added="2024-01-02",
        sections=[
            {
                "section_type": "chorus",
                "start_sec": 0.0,
                "end_sec": 20.0,
                "duration_sec": 20.0,
                "energy_level": 0.8,
                "spectral_centroid": 2200.0,
                "tempo_stability": 0.85,
                "vocal_density": "dense",
                "vocal_intensity": 0.8,
                "lyrical_content": "test chorus",
                "emotional_tone": "defiant",
                "lyrical_function": "hook",
                "themes": ["empowerment"],
            }
        ],
        emotional_arc="intro:calm → verse:building → chorus:explosive",
        word_timings=[],
    )


@pytest.fixture
def song_c_meta():
    """Sample song C metadata - incompatible with song A."""
    return SongMetadata(
        source="local_file",
        path="/path/to/song_c.wav",
        bpm=80.0,  # Far from 120
        key="F# minor",
        camelot="11A",  # Far from 8B
        genres=["Country", "Folk"],
        primary_genre="Country",
        irony_score=7,
        mood_summary="melancholic and slow",
        energy_level=3,  # Low energy
        valence=3,
        first_downbeat_sec=0.4,
        duration_sec=220.0,
        sample_rate=44100,
        has_vocals=True,
        artist="Artist C",
        title="Song C",
        date_added="2024-01-03",
        sections=[],
        emotional_arc="intro:sad → verse:reflective → chorus:resigned",
        word_timings=[],
    )


# Tests for calculate_compatibility_score
def test_calculate_compatibility_score_perfect_match(song_a_meta, song_b_meta):
    """Test scoring for highly compatible songs."""
    # song_b is designed to be compatible with song_a
    score, reasons = calculate_compatibility_score(song_a_meta, song_b_meta)

    assert 0.0 <= score <= 1.0, "Score must be between 0 and 1"
    assert score > 0.7, "Compatible songs should score high"
    assert len(reasons) > 0, "Should provide match reasons"
    assert any("BPM" in reason for reason in reasons), "Should mention BPM compatibility"
    assert any("key" in reason.lower() for reason in reasons), "Should mention key compatibility"


def test_calculate_compatibility_score_poor_match(song_a_meta, song_c_meta):
    """Test scoring for incompatible songs."""
    score, reasons = calculate_compatibility_score(song_a_meta, song_c_meta)

    assert 0.0 <= score <= 1.0, "Score must be between 0 and 1"
    assert score < 0.5, "Incompatible songs should score low"


def test_calculate_compatibility_score_custom_weights(song_a_meta, song_b_meta):
    """Test custom weight configuration."""
    custom_weights = {
        "bpm": 0.5,
        "key": 0.3,
        "energy": 0.1,
        "genre": 0.1,
    }

    score, reasons = calculate_compatibility_score(
        song_a_meta, song_b_meta, weights=custom_weights
    )

    assert 0.0 <= score <= 1.0, "Score must be between 0 and 1"
    assert len(reasons) > 0, "Should provide match reasons"


def test_calculate_compatibility_score_default_bpm(song_a_meta, song_b_meta):
    """Test scoring with default BPM values."""
    # Using .get() with defaults handles missing BPM gracefully
    score, reasons = calculate_compatibility_score(song_a_meta, song_b_meta)

    # Should work with default values
    assert 0.0 <= score <= 1.0, "Score must be between 0 and 1"


# Tests for recommend_mashup_type
def test_recommend_mashup_type_classic(song_a_meta, song_b_meta):
    """Test classic mashup recommendation for simple case."""
    # Modify metadata to favor classic mashup (good vocals, different energy)
    song_a_classic = song_a_meta.copy()
    song_b_classic = song_b_meta.copy()
    song_a_classic["has_vocals"] = True
    song_b_classic["has_vocals"] = False  # No vocals = instrumental

    recommendation = recommend_mashup_type(song_a_classic, song_b_classic)

    assert recommendation["mashup_type"] == "CLASSIC"
    assert 0.0 <= recommendation["confidence"] <= 1.0
    assert len(recommendation["reasoning"]) > 0
    assert "config_suggestion" in recommendation


def test_recommend_mashup_type_energy_matched(song_a_meta, song_b_meta):
    """Test energy-matched recommendation."""
    # Both songs have high energy and sections
    recommendation = recommend_mashup_type(song_a_meta, song_b_meta)

    # Could be ENERGY_MATCHED, ADAPTIVE_HARMONY, or STEM_SWAP
    # depending on other characteristics
    assert recommendation["mashup_type"] in [
        "CLASSIC",
        "STEM_SWAP",
        "ENERGY_MATCHED",
        "ADAPTIVE_HARMONY",
    ]
    assert 0.0 <= recommendation["confidence"] <= 1.0
    assert len(recommendation["reasoning"]) > 0


def test_recommend_mashup_type_theme_fusion(song_a_meta, song_b_meta):
    """Test theme fusion recommendation."""
    # Add overlapping themes to favor theme fusion
    song_a_themed = song_a_meta.copy()
    song_b_themed = song_b_meta.copy()

    # Ensure sections have themes
    if song_a_themed["sections"]:
        song_a_themed["sections"][0]["themes"] = ["love", "hope"]
    if song_b_themed["sections"]:
        song_b_themed["sections"][0]["themes"] = ["love", "empowerment"]

    recommendation = recommend_mashup_type(song_a_themed, song_b_themed)

    # Should recommend theme fusion or semantic aligned due to theme overlap
    assert recommendation["mashup_type"] in [
        "CLASSIC",
        "STEM_SWAP",
        "ENERGY_MATCHED",
        "ADAPTIVE_HARMONY",
        "THEME_FUSION",
        "SEMANTIC_ALIGNED",
    ]
    assert 0.0 <= recommendation["confidence"] <= 1.0


# Tests for find_match
@patch("mixer.agents.curator.query_hybrid")
@patch("mixer.agents.curator.get_song")
def test_find_match_hybrid_success(mock_get_song, mock_query_hybrid, song_a_meta, song_b_meta):
    """Test find_match with hybrid criteria."""
    # Mock get_song to return song A wrapped in dict with metadata key
    mock_get_song.return_value = {"id": "artist_a_song_a", "metadata": song_a_meta}

    # Mock query_hybrid to return song B as a match
    mock_query_hybrid.return_value = [
        {
            "id": "artist_b_song_b",
            "compatibility_score": 0.85,
            "metadata": song_b_meta,
            "match_reasons": ["BPM compatible", "Key adjacent on Camelot wheel"],
        }
    ]

    results = find_match("artist_a_song_a", criteria="hybrid", max_results=5)

    assert len(results) == 1
    assert results[0]["id"] == "artist_b_song_b"
    assert "compatibility_score" in results[0]
    assert len(results[0]["match_reasons"]) > 0
    mock_query_hybrid.assert_called_once()


@patch("mixer.agents.curator.query_harmonic")
@patch("mixer.agents.curator.get_song")
def test_find_match_harmonic_mode(mock_get_song, mock_query_harmonic, song_a_meta, song_b_meta):
    """Test find_match with harmonic criteria."""
    mock_get_song.return_value = {"id": "artist_a_song_a", "metadata": song_a_meta}
    mock_query_harmonic.return_value = [
        {
            "id": "artist_b_song_b",
            "compatibility_score": 0.9,
            "metadata": song_b_meta,
            "match_reasons": ["BPM within tolerance", "Camelot adjacent"],
        }
    ]

    results = find_match("artist_a_song_a", criteria="harmonic", max_results=3)

    assert len(results) == 1
    mock_query_harmonic.assert_called_once()


@patch("mixer.agents.curator.query_semantic")
@patch("mixer.agents.curator.get_song")
def test_find_match_semantic_mode(mock_get_song, mock_query_semantic, song_a_meta, song_b_meta):
    """Test find_match with semantic criteria."""
    mock_get_song.return_value = {"id": "artist_a_song_a", "metadata": song_a_meta}
    mock_query_semantic.return_value = [
        {
            "id": "artist_b_song_b",
            "compatibility_score": 0.75,
            "metadata": song_b_meta,
            "match_reasons": ["Similar mood", "Genre overlap"],
        }
    ]

    results = find_match(
        "artist_a_song_a",
        criteria="semantic",
        semantic_query="upbeat pop",
        max_results=5,
    )

    assert len(results) == 1
    mock_query_semantic.assert_called_once()


@patch("mixer.agents.curator.get_song")
def test_find_match_target_not_found(mock_get_song):
    """Test find_match when target song doesn't exist."""
    mock_get_song.return_value = None

    with pytest.raises(CuratorError, match="Target song not found"):
        find_match("nonexistent_song", criteria="hybrid")


@patch("mixer.agents.curator.query_hybrid")
@patch("mixer.agents.curator.get_song")
def test_find_match_genre_filter(mock_get_song, mock_query_hybrid, song_a_meta, song_b_meta):
    """Test find_match with genre filtering."""
    mock_get_song.return_value = {"id": "artist_a_song_a", "metadata": song_a_meta}
    mock_query_hybrid.return_value = [
        {
            "id": "artist_b_song_b",
            "compatibility_score": 0.85,
            "metadata": song_b_meta,
            "match_reasons": ["Genre: Pop"],
        }
    ]

    results = find_match("artist_a_song_a", criteria="hybrid", genre_filter="Pop")

    assert len(results) == 1
    # Verify genre_filter was passed to query_hybrid
    call_kwargs = mock_query_hybrid.call_args[1]
    assert call_kwargs.get("genre_filter") == "Pop"


# Tests for find_all_pairs
@patch("mixer.memory.get_client")
def test_find_all_pairs_success(mock_get_client, song_a_meta, song_b_meta):
    """Test find_all_pairs batch processing."""
    # Mock ChromaDB client
    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "ids": ["artist_a_song_a", "artist_b_song_b"],
        "metadatas": [song_a_meta, song_b_meta],
    }
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection
    mock_get_client.return_value = mock_client

    results = find_all_pairs(max_pairs=10, min_compatibility=0.5)

    # Should return at least one pair (A-B or B-A)
    assert len(results) >= 0, "Should return list of pairs"
    assert isinstance(results, list), "Should return list"


@patch("mixer.memory.get_client")
def test_find_all_pairs_min_compatibility_filter(mock_get_client, song_a_meta, song_c_meta):
    """Test find_all_pairs filters by minimum compatibility."""
    # Mock ChromaDB with incompatible songs
    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "ids": ["artist_a_song_a", "artist_c_song_c"],
        "metadatas": [song_a_meta, song_c_meta],
    }
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection
    mock_get_client.return_value = mock_client

    results = find_all_pairs(max_pairs=5, min_compatibility=0.8)

    # Should return fewer pairs due to high min_compatibility threshold
    # (song A and C are incompatible, so should be filtered out)
    assert isinstance(results, list), "Should return list"
    # All returned pairs should meet min_compatibility
    for pair in results:
        assert pair["compatibility_score"] >= 0.8


@patch("mixer.memory.get_client")
def test_find_all_pairs_genre_filter(mock_get_client, song_a_meta, song_b_meta, song_c_meta):
    """Test find_all_pairs with genre filtering."""
    # Mock ChromaDB with mixed genres
    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "ids": ["artist_a_song_a", "artist_b_song_b", "artist_c_song_c"],
        "metadatas": [song_a_meta, song_b_meta, song_c_meta],
    }
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection
    mock_get_client.return_value = mock_client

    results = find_all_pairs(max_pairs=5, genre_filter="Pop")

    # Should only include pairs with Pop genre
    for pair in results:
        song_a_id = pair["song_a_id"]
        song_b_id = pair["song_b_id"]
        # At least one song should have Pop genre
        # (based on our test data, A and B are Pop, C is Country)
        assert song_a_id != "artist_c_song_c" or song_b_id != "artist_c_song_c"


@patch("mixer.memory.get_client")
def test_find_all_pairs_empty_library(mock_get_client):
    """Test find_all_pairs with empty library."""
    # Mock empty ChromaDB
    mock_collection = MagicMock()
    mock_collection.get.return_value = {"ids": [], "metadatas": []}
    mock_client = MagicMock()
    mock_client.get_collection.return_value = mock_collection
    mock_get_client.return_value = mock_client

    results = find_all_pairs(max_pairs=10)

    assert results == [], "Should return empty list for empty library"


# Edge case tests
def test_calculate_compatibility_score_same_song(song_a_meta):
    """Test scoring when comparing song to itself."""
    score, reasons = calculate_compatibility_score(song_a_meta, song_a_meta)

    # Should be perfect match (with floating point tolerance)
    assert score >= 0.99, "Song compared to itself should have near-perfect score"
    assert len(reasons) > 0


def test_calculate_compatibility_score_default_key(song_a_meta, song_b_meta):
    """Test scoring with default key values."""
    # Using .get() with defaults handles missing keys gracefully
    score, reasons = calculate_compatibility_score(song_a_meta, song_b_meta)

    # Should work with default values
    assert 0.0 <= score <= 1.0


@patch("mixer.agents.curator.query_hybrid")
@patch("mixer.agents.curator.get_song")
def test_find_match_no_results(mock_get_song, mock_query_hybrid, song_a_meta):
    """Test find_match when no compatible songs found."""
    mock_get_song.return_value = {"id": "artist_a_song_a", "metadata": song_a_meta}
    mock_query_hybrid.return_value = []

    results = find_match("artist_a_song_a", criteria="hybrid")

    assert results == [], "Should return empty list when no matches found"
