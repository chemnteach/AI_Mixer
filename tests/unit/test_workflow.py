"""Unit tests for LangGraph Workflow (Phase 5)."""

import pytest
from unittest.mock import patch, MagicMock
from mixer.workflow.state import MashupState, WorkflowStatus
from mixer.workflow.nodes import (
    ingest_song_a_node,
    analyze_song_a_node,
    ingest_song_b_node,
    analyze_song_b_node,
    find_matches_node,
    await_user_selection_node,
    recommend_mashup_type_node,
    await_mashup_approval_node,
    create_mashup_node,
    error_handler_node,
)
from mixer.workflow.graph import (
    create_mashup_workflow,
    should_continue_after_error,
    should_find_matches,
    has_match_selected,
)
from mixer.types import SongMetadata


# Fixtures for test data
@pytest.fixture
def initial_state():
    """Initial workflow state."""
    return MashupState(
        input_source_a="https://youtube.com/watch?v=test_a",
        input_source_b=None,
        mashup_type=None,
        status=WorkflowStatus.PENDING.value,
        current_step="start",
        error=None,
        retry_count=0,
        song_a_cached=False,
        song_b_cached=False,
        progress_messages=[],
    )


@pytest.fixture
def sample_metadata():
    """Sample song metadata."""
    return SongMetadata(
        source="youtube",
        path="/path/to/song.wav",
        bpm=120.0,
        key="C major",
        camelot="8B",
        genres=["Pop"],
        primary_genre="Pop",
        irony_score=5,
        mood_summary="upbeat",
        energy_level=7,
        valence=8,
        first_downbeat_sec=0.5,
        duration_sec=180.0,
        sample_rate=44100,
        has_vocals=True,
        artist="Test Artist",
        title="Test Song",
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
                "lyrical_content": "test",
                "emotional_tone": "hopeful",
                "lyrical_function": "narrative",
                "themes": ["love"],
            }
        ],
        emotional_arc="intro:hopeful",
        word_timings=[],
    )


# Tests for node functions
@patch("mixer.workflow.nodes.ingest_song")
def test_ingest_song_a_node_success(mock_ingest, initial_state):
    """Test successful ingestion of song A."""
    mock_ingest.return_value = {
        "id": "test_artist_test_song_a",
        "path": "/cache/test_song_a.wav",
        "cached": False,
        "source": "youtube",
    }

    result = ingest_song_a_node(initial_state)

    assert result["song_a_id"] == "test_artist_test_song_a"
    assert result["song_a_path"] == "/cache/test_song_a.wav"
    assert result["song_a_cached"] == False
    assert result["status"] == WorkflowStatus.INGESTING.value
    assert len(result["progress_messages"]) > 0
    mock_ingest.assert_called_once_with("https://youtube.com/watch?v=test_a")


@patch("mixer.workflow.nodes.ingest_song")
def test_ingest_song_a_node_cached(mock_ingest, initial_state):
    """Test ingestion of cached song A."""
    mock_ingest.return_value = {
        "id": "test_artist_test_song_a",
        "path": "/cache/test_song_a.wav",
        "cached": True,
        "source": "local_file",
    }

    result = ingest_song_a_node(initial_state)

    assert result["song_a_cached"] == True
    assert any("already in library" in msg for msg in result["progress_messages"])


@patch("mixer.workflow.nodes.ingest_song")
def test_ingest_song_a_node_error(mock_ingest, initial_state):
    """Test ingestion error handling."""
    from mixer.agents import IngestionError
    mock_ingest.side_effect = IngestionError("Download failed")

    result = ingest_song_a_node(initial_state)

    assert result["status"] == WorkflowStatus.FAILED.value
    assert "Failed to ingest song A" in result["error"]


@patch("mixer.workflow.nodes.get_song")
@patch("mixer.workflow.nodes.profile_audio")
def test_analyze_song_a_node_success(mock_profile, mock_get_song, initial_state, sample_metadata):
    """Test successful analysis of song A."""
    # Setup state from ingestion
    initial_state["song_a_id"] = "test_artist_test_song_a"
    initial_state["song_a_path"] = "/cache/test_song_a.wav"

    # Mock: not yet analyzed (first get_song returns no metadata)
    mock_get_song.side_effect = [
        None,  # First call: check if analyzed
        {"id": "test_artist_test_song_a", "metadata": sample_metadata},  # After analysis
    ]

    result = analyze_song_a_node(initial_state)

    assert result["song_a_metadata"] == sample_metadata
    assert result["status"] == WorkflowStatus.ANALYZING.value
    assert len(result["progress_messages"]) > 0
    mock_profile.assert_called_once_with("/cache/test_song_a.wav")


@patch("mixer.workflow.nodes.get_song")
def test_analyze_song_a_node_already_analyzed(mock_get_song, initial_state, sample_metadata):
    """Test skipping analysis when song already analyzed."""
    initial_state["song_a_id"] = "test_artist_test_song_a"
    initial_state["song_a_path"] = "/cache/test_song_a.wav"

    # Mock: already analyzed
    mock_get_song.return_value = {"id": "test_artist_test_song_a", "metadata": sample_metadata}

    result = analyze_song_a_node(initial_state)

    assert result["song_a_metadata"] == sample_metadata
    assert any("already analyzed" in msg for msg in result["progress_messages"])


@patch("mixer.workflow.nodes.ingest_song")
def test_ingest_song_b_node_provided(mock_ingest, initial_state):
    """Test ingestion of song B when provided."""
    initial_state["input_source_b"] = "https://youtube.com/watch?v=test_b"

    mock_ingest.return_value = {
        "id": "test_artist_test_song_b",
        "path": "/cache/test_song_b.wav",
        "cached": False,
        "source": "youtube",
    }

    result = ingest_song_b_node(initial_state)

    assert result["song_b_id"] == "test_artist_test_song_b"
    assert result["song_b_path"] == "/cache/test_song_b.wav"
    mock_ingest.assert_called_once_with("https://youtube.com/watch?v=test_b")


def test_ingest_song_b_node_not_provided(initial_state):
    """Test skipping song B ingestion when not provided."""
    result = ingest_song_b_node(initial_state)

    assert "song_b_id" not in result or result["song_b_id"] is None
    assert any("curator will find" in msg for msg in result["progress_messages"])


@patch("mixer.workflow.nodes.find_match")
def test_find_matches_node_success(mock_find_match, initial_state, sample_metadata):
    """Test finding matches for song A."""
    initial_state["song_a_id"] = "test_artist_test_song_a"

    mock_find_match.return_value = [
        {
            "id": "match_1",
            "compatibility_score": 0.92,
            "metadata": sample_metadata,
            "match_reasons": ["BPM compatible", "Key adjacent"],
        },
        {
            "id": "match_2",
            "compatibility_score": 0.85,
            "metadata": sample_metadata,
            "match_reasons": ["Genre match"],
        },
    ]

    result = find_matches_node(initial_state)

    assert len(result["match_candidates"]) == 2
    assert result["match_candidates"][0]["id"] == "match_1"
    assert result["status"] == WorkflowStatus.CURATING.value
    mock_find_match.assert_called_once()


def test_find_matches_node_skip_when_song_b_provided(initial_state):
    """Test skipping match finding when song B already provided."""
    initial_state["song_b_id"] = "test_artist_test_song_b"

    result = find_matches_node(initial_state)

    assert "match_candidates" not in result or result["match_candidates"] is None


def test_await_user_selection_node_auto_select(initial_state, sample_metadata):
    """Test auto-selection of top match."""
    initial_state["match_candidates"] = [
        {
            "id": "match_1",
            "compatibility_score": 0.92,
            "metadata": sample_metadata,
            "match_reasons": ["BPM compatible"],
        }
    ]

    result = await_user_selection_node(initial_state)

    assert result["song_b_id"] == "match_1"
    assert result["selected_match"]["id"] == "match_1"
    assert result["song_b_metadata"] == sample_metadata
    assert any("Auto-selected" in msg for msg in result["progress_messages"])


def test_await_user_selection_node_skip_when_selected(initial_state):
    """Test skipping selection when song B already selected."""
    initial_state["song_b_id"] = "test_artist_test_song_b"

    result = await_user_selection_node(initial_state)

    # State unchanged
    assert result["song_b_id"] == "test_artist_test_song_b"


@patch("mixer.workflow.nodes.recommend_mashup_type")
def test_recommend_mashup_type_node_success(mock_recommend, initial_state, sample_metadata):
    """Test mashup type recommendation."""
    initial_state["song_a_metadata"] = sample_metadata
    initial_state["song_b_metadata"] = sample_metadata

    mock_recommend.return_value = {
        "mashup_type": "CLASSIC",
        "confidence": 0.85,
        "reasoning": "Both songs have vocals, good for classic mashup",
        "config_suggestion": {"vocal_id": "song_a", "inst_id": "song_b"},
    }

    result = recommend_mashup_type_node(initial_state)

    assert result["recommended_mashup"]["mashup_type"] == "CLASSIC"
    assert result["recommended_mashup"]["confidence"] == 0.85
    assert any("Recommended: CLASSIC" in msg for msg in result["progress_messages"])


def test_await_mashup_approval_node_auto_approve(initial_state):
    """Test auto-approval of recommended mashup type."""
    initial_state["recommended_mashup"] = {
        "mashup_type": "ENERGY_MATCHED",
        "confidence": 0.90,
        "reasoning": "Test",
        "config_suggestion": {},
    }

    result = await_mashup_approval_node(initial_state)

    assert result["approved_mashup_type"] == "ENERGY_MATCHED"
    assert any("Auto-approved" in msg for msg in result["progress_messages"])


def test_await_mashup_approval_node_user_specified(initial_state):
    """Test using user-specified mashup type."""
    initial_state["mashup_type"] = "ADAPTIVE_HARMONY"

    result = await_mashup_approval_node(initial_state)

    assert result["approved_mashup_type"] == "ADAPTIVE_HARMONY"
    assert any("user-specified" in msg for msg in result["progress_messages"])


@patch("mixer.workflow.nodes.create_classic_mashup")
def test_create_mashup_node_success(mock_create, initial_state):
    """Test successful mashup creation."""
    initial_state["song_a_id"] = "song_a"
    initial_state["song_b_id"] = "song_b"
    initial_state["approved_mashup_type"] = "CLASSIC"

    mock_create.return_value = "/mashups/output.mp3"

    result = create_mashup_node(initial_state)

    assert result["mashup_output_path"] == "/mashups/output.mp3"
    assert result["status"] == WorkflowStatus.COMPLETED.value
    assert any("Mashup created" in msg for msg in result["progress_messages"])
    mock_create.assert_called_once_with(
        song_a_id="song_a",
        song_b_id="song_b",
        quality="high",
        output_format="mp3"
    )


@patch("mixer.workflow.nodes.create_energy_matched_mashup")
def test_create_mashup_node_different_type(mock_create, initial_state):
    """Test mashup creation with different type."""
    initial_state["song_a_id"] = "song_a"
    initial_state["song_b_id"] = "song_b"
    initial_state["approved_mashup_type"] = "ENERGY_MATCHED"

    mock_create.return_value = "/mashups/energy_output.mp3"

    result = create_mashup_node(initial_state)

    assert result["mashup_output_path"] == "/mashups/energy_output.mp3"
    mock_create.assert_called_once()


def test_error_handler_node_first_retry(initial_state):
    """Test error handler on first retry."""
    initial_state["error"] = "Test error"
    initial_state["retry_count"] = 0

    result = error_handler_node(initial_state)

    assert result["retry_count"] == 1
    assert result["error"] is None  # Cleared for retry
    assert any("retrying" in msg for msg in result["progress_messages"])


def test_error_handler_node_max_retries(initial_state):
    """Test error handler when max retries exceeded."""
    initial_state["error"] = "Test error"
    initial_state["retry_count"] = 3

    result = error_handler_node(initial_state)

    assert result["retry_count"] == 3
    assert result["error"] == "Test error"  # Not cleared
    assert any("Max retries exceeded" in msg for msg in result["progress_messages"])


# Tests for conditional edge functions
def test_should_continue_after_error_retry():
    """Test retry decision after error cleared."""
    state = MashupState(error=None, retry_count=1, progress_messages=[])
    assert should_continue_after_error(state) == "retry"


def test_should_continue_after_error_end():
    """Test end decision after max retries."""
    state = MashupState(error="Persistent error", retry_count=3, progress_messages=[])
    assert should_continue_after_error(state) == "end"


def test_should_find_matches_yes():
    """Test should find matches when song B not provided."""
    state = MashupState(song_b_id=None, progress_messages=[])
    assert should_find_matches(state) == "find_matches"


def test_should_find_matches_no():
    """Test skip finding matches when song B provided."""
    state = MashupState(song_b_id="song_b", progress_messages=[])
    assert should_find_matches(state) == "recommend_type"


def test_has_match_selected_yes():
    """Test match selected."""
    state = MashupState(song_b_id="match_1", progress_messages=[])
    assert has_match_selected(state) == "recommend_type"


def test_has_match_selected_no():
    """Test match not yet selected."""
    state = MashupState(song_b_id=None, progress_messages=[])
    assert has_match_selected(state) == "await_selection"


# Tests for workflow graph
def test_create_mashup_workflow():
    """Test workflow graph creation."""
    workflow = create_mashup_workflow()

    assert workflow is not None
    # Check that nodes are added
    assert "ingest_song_a" in workflow.nodes
    assert "analyze_song_a" in workflow.nodes
    assert "find_matches" in workflow.nodes
    assert "create_mashup" in workflow.nodes
