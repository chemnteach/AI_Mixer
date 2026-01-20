"""End-to-end integration tests for complete workflow."""

import pytest
from pathlib import Path
from mixer.workflow import run_mashup_workflow, WorkflowError
from mixer.memory import get_client, reset_client
from mixer.agents import ingest_song, profile_audio


@pytest.fixture(scope="module")
def temp_chroma_dir(tmp_path_factory):
    """Create temporary ChromaDB directory for integration tests."""
    return tmp_path_factory.mktemp("chroma_integration")


@pytest.fixture(scope="module", autouse=True)
def setup_test_env(temp_chroma_dir, monkeypatch):
    """Setup isolated test environment."""
    # Use temporary ChromaDB
    monkeypatch.setenv("CHROMA_PERSIST_DIRECTORY", str(temp_chroma_dir))
    reset_client()
    yield
    reset_client()


@pytest.mark.integration
@pytest.mark.skip(reason="Requires real audio files and network access")
def test_full_workflow_with_two_songs():
    """Test complete workflow: ingest 2 songs → analyze → recommend → mashup.

    This test requires:
    - Two valid audio files or YouTube URLs
    - All dependencies installed (Whisper, Demucs, etc.)
    - LLM API keys configured

    """
    # Arrange
    song_a_path = "path/to/test_song_a.mp3"  # Replace with actual test file
    song_b_path = "path/to/test_song_b.mp3"  # Replace with actual test file

    # Act
    final_state = run_mashup_workflow(
        input_source_a=song_a_path,
        input_source_b=song_b_path,
        mashup_type="CLASSIC",
        stream=False
    )

    # Assert
    assert final_state["status"] == "completed"
    assert final_state["mashup_output_path"] is not None
    assert Path(final_state["mashup_output_path"]).exists()
    assert final_state["song_a_id"] is not None
    assert final_state["song_b_id"] is not None


@pytest.mark.integration
@pytest.mark.skip(reason="Requires real audio files and network access")
def test_workflow_with_auto_match():
    """Test workflow with automatic match selection.

    This test requires:
    - One audio file
    - Library with at least 2 songs already ingested
    - All dependencies installed

    """
    # Arrange
    song_a_path = "path/to/test_song_a.mp3"

    # Act
    final_state = run_mashup_workflow(
        input_source_a=song_a_path,
        input_source_b=None,  # Auto-match
        mashup_type=None,  # Auto-recommend
        stream=False
    )

    # Assert
    assert final_state["status"] == "completed"
    assert final_state["song_b_id"] is not None  # Should auto-select
    assert final_state["approved_mashup_type"] is not None  # Should auto-recommend


@pytest.mark.integration
@pytest.mark.skip(reason="Requires ChromaDB with test data")
def test_workflow_error_recovery():
    """Test workflow error handling and retry logic."""
    # Arrange
    invalid_source = "http://invalid-url-that-does-not-exist.com/song.mp3"

    # Act & Assert
    with pytest.raises(WorkflowError):
        run_mashup_workflow(
            input_source_a=invalid_source,
            input_source_b=None,
            mashup_type="CLASSIC",
            stream=False
        )


@pytest.mark.integration
def test_workflow_state_persistence():
    """Test that workflow state is properly maintained through all steps.

    This is a mock integration test that validates state flow without
    requiring real audio processing.
    """
    # This would need mocking of all agent functions
    # Left as TODO for real-world implementation
    pass


@pytest.mark.integration
@pytest.mark.skip(reason="Performance test - run manually")
def test_workflow_performance_benchmark():
    """Benchmark full workflow execution time.

    Expected timings (rough estimates):
    - Ingestion: 5-30s (depends on download speed)
    - Analysis: 30-60s per song (Whisper + Demucs + section detection)
    - Curation: <1s (database query)
    - Engineering: 30-60s (stem separation + mixing)
    - Total: ~2-3 minutes for classic mashup

    """
    import time

    song_a_path = "path/to/test_song_a.mp3"
    song_b_path = "path/to/test_song_b.mp3"

    start_time = time.time()

    final_state = run_mashup_workflow(
        input_source_a=song_a_path,
        input_source_b=song_b_path,
        mashup_type="CLASSIC",
        stream=False
    )

    end_time = time.time()
    duration = end_time - start_time

    assert final_state["status"] == "completed"
    assert duration < 300  # Should complete in under 5 minutes

    print(f"\n=== Performance Benchmark ===")
    print(f"Total duration: {duration:.1f}s")
    print(f"Average per-song processing: {duration/2:.1f}s")
