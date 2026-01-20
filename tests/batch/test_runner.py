"""Tests for batch.runner module."""

import pytest
from pathlib import Path
from batch.runner import BatchRunner, PipelineStage
from batch.errors import StageError


def test_batch_runner_init():
    """Test BatchRunner initialization."""
    runner = BatchRunner(
        audio_path="./test.wav",
        song_id="test_song",
        theme="sponsor_neon",
        mode="mashup"
    )

    assert runner.audio_path == "./test.wav"
    assert runner.song_id == "test_song"
    assert runner.theme == "sponsor_neon"
    assert runner.mode == "mashup"
    assert runner.timeline_path is None
    assert runner.raw_video_path is None
    assert runner.platform_videos == {}


def test_pipeline_stage_enum():
    """Test PipelineStage enum."""
    assert PipelineStage.DIRECTOR.value == "director"
    assert PipelineStage.STUDIO.value == "studio"
    assert PipelineStage.ENCODER.value == "encoder"
    assert PipelineStage.COMPLETE.value == "complete"


def test_stage_error():
    """Test StageError exception."""
    error = StageError("director", "Test error")

    assert error.stage == "director"
    assert "director" in str(error)
    assert "Test error" in str(error)


def test_stage_error_with_original():
    """Test StageError with original exception."""
    original = ValueError("Original error")
    error = StageError("studio", "Wrapped error", original)

    assert error.stage == "studio"
    assert error.original_error == original
    assert "studio" in str(error)
