"""Unit tests for Engineer Agent - Phase 3E (Interactive Mashups)."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mixer.agents.engineer import (
    create_role_aware_mashup,
    create_conversational_mashup,
    _process_vocal_by_role,
    EngineerError,
    SongNotFoundError,
)


@pytest.fixture
def mock_audio_data():
    """Generate mock audio data for testing."""
    sr = 44100
    duration = 3.0  # 3 seconds
    samples = int(sr * duration)
    # Generate simple sine wave
    audio = np.sin(2 * np.pi * 440 * np.arange(samples) / sr).astype(np.float32)
    return audio, sr


@pytest.fixture
def mock_song_metadata():
    """Mock song metadata."""
    return {
        "path": "/fake/path/song.wav",
        "bpm": 120.0,
        "key": "Cmaj",
        "camelot": "8B",
        "first_downbeat_sec": 0.5,
        "sample_rate": 44100,
        "duration_sec": 180.0,
        "has_vocals": True,
        "artist": "Test Artist",
        "title": "Test Song",
    }


@pytest.fixture
def mock_stems():
    """Mock separated stems."""
    sr = 44100
    duration = 3.0
    samples = int(sr * duration)

    # Create simple mock stems
    vocals = np.random.randn(samples).astype(np.float32) * 0.1
    drums = np.random.randn(samples).astype(np.float32) * 0.1
    bass = np.random.randn(samples).astype(np.float32) * 0.1
    other = np.random.randn(samples).astype(np.float32) * 0.1

    return {
        "vocals": vocals,
        "drums": drums,
        "bass": bass,
        "other": other,
    }


@pytest.fixture
def mock_role_aware_sections():
    """Create mock sections with vocal characteristics for role assignment."""
    sections_a = [
        {
            "section_type": "verse",
            "start_sec": 0.0,
            "end_sec": 20.0,
            "vocal_density": "dense",
            "vocal_intensity": 0.8,
            "lyrical_function": "narrative",
            "emotional_tone": "descriptive"
        },
        {
            "section_type": "chorus",
            "start_sec": 20.0,
            "end_sec": 40.0,
            "vocal_density": "medium",
            "vocal_intensity": 0.6,
            "lyrical_function": "hook",
            "emotional_tone": "intense"
        },
    ]
    sections_b = [
        {
            "section_type": "verse",
            "start_sec": 0.0,
            "end_sec": 18.0,
            "vocal_density": "sparse",
            "vocal_intensity": 0.3,
            "lyrical_function": "question",
            "emotional_tone": "curious"
        },
        {
            "section_type": "bridge",
            "start_sec": 18.0,
            "end_sec": 30.0,
            "vocal_density": "dense",
            "vocal_intensity": 0.5,
            "lyrical_function": "answer",
            "emotional_tone": "resolute"
        },
    ]
    return sections_a, sections_b


@pytest.fixture
def mock_conversational_sections():
    """Create mock sections with lyrical functions for conversational pairing."""
    sections_a = [
        {
            "section_type": "verse",
            "start_sec": 0.0,
            "end_sec": 20.0,
            "lyrical_function": "question",
            "emotional_tone": "curious"
        },
        {
            "section_type": "verse",
            "start_sec": 20.0,
            "end_sec": 40.0,
            "lyrical_function": "narrative",
            "emotional_tone": "descriptive"
        },
        {
            "section_type": "chorus",
            "start_sec": 40.0,
            "end_sec": 60.0,
            "lyrical_function": "hook",
            "emotional_tone": "intense"
        },
    ]
    sections_b = [
        {
            "section_type": "verse",
            "start_sec": 0.0,
            "end_sec": 18.0,
            "lyrical_function": "answer",
            "emotional_tone": "resolute"
        },
        {
            "section_type": "bridge",
            "start_sec": 18.0,
            "end_sec": 35.0,
            "lyrical_function": "reflection",
            "emotional_tone": "contemplative"
        },
        {
            "section_type": "chorus",
            "start_sec": 35.0,
            "end_sec": 50.0,
            "lyrical_function": "response",
            "emotional_tone": "powerful"
        },
    ]
    return sections_a, sections_b


class TestProcessVocalByRole:
    """Test the _process_vocal_by_role helper function."""

    def test_process_lead_role(self, mock_audio_data):
        """Should process lead role with full volume."""
        audio, sr = mock_audio_data
        vocal = audio[:sr]  # 1 second
        inst = audio[:sr]

        result = _process_vocal_by_role(vocal, inst, "lead", sr)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(vocal)

    def test_process_harmony_role(self, mock_audio_data):
        """Should process harmony role with pitch-shift and attenuation."""
        audio, sr = mock_audio_data
        vocal = audio[:sr]
        inst = audio[:sr]

        with patch("mixer.agents.engineer.pitch_shift") as mock_pitch:
            mock_pitch.return_value = vocal.copy()
            result = _process_vocal_by_role(vocal, inst, "harmony", sr)

            assert isinstance(result, np.ndarray)
            # Verify pitch_shift was called (can't directly compare numpy arrays in mock assertions)
            assert mock_pitch.call_count == 1
            assert mock_pitch.call_args[0][1] == sr  # Check sr
            assert mock_pitch.call_args[1]["n_steps"] == 3  # Check n_steps

    def test_process_harmony_role_pitch_shift_fallback(self, mock_audio_data):
        """Should fallback gracefully if pitch-shift fails."""
        audio, sr = mock_audio_data
        vocal = audio[:sr]
        inst = audio[:sr]

        with patch("mixer.agents.engineer.pitch_shift", side_effect=Exception("Pitch shift failed")):
            result = _process_vocal_by_role(vocal, inst, "harmony", sr)

            assert isinstance(result, np.ndarray)
            # Should still return something even if pitch-shift fails

    def test_process_call_role(self, mock_audio_data):
        """Should add silence after call role."""
        audio, sr = mock_audio_data
        vocal = audio[:sr]
        inst = audio[:sr]

        result = _process_vocal_by_role(vocal, inst, "call", sr)

        # Should be longer due to added silence
        assert len(result) > len(vocal)

    def test_process_response_role(self, mock_audio_data):
        """Should add silence before response role."""
        audio, sr = mock_audio_data
        vocal = audio[:sr]
        inst = audio[:sr]

        result = _process_vocal_by_role(vocal, inst, "response", sr)

        # Should be longer due to added silence
        assert len(result) > len(vocal)

    def test_process_texture_role(self, mock_audio_data):
        """Should attenuate texture role heavily."""
        audio, sr = mock_audio_data
        vocal = audio[:sr]
        inst = audio[:sr]

        result = _process_vocal_by_role(vocal, inst, "texture", sr)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(vocal)

    def test_process_unknown_role(self, mock_audio_data):
        """Should use default balanced mix for unknown role."""
        audio, sr = mock_audio_data
        vocal = audio[:sr]
        inst = audio[:sr]

        result = _process_vocal_by_role(vocal, inst, "unknown_role", sr)

        assert isinstance(result, np.ndarray)
        assert len(result) == len(vocal)


class TestRoleAwareMashup:
    """Test role-aware mashup creation."""

    @patch("mixer.agents.engineer._load_song_audio")
    @patch("mixer.agents.engineer.separate_stems")
    @patch("mixer.agents.engineer.combine_stems")
    @patch("mixer.agents.engineer.time_stretch")
    @patch("mixer.agents.engineer._process_vocal_by_role")
    @patch("mixer.agents.engineer.get_config")
    @patch("mixer.audio.processing.numpy_to_audiosegment")
    @patch("pydub.effects.normalize")
    @patch("mixer.agents.engineer.Path")
    def test_create_role_aware_success(
        self,
        mock_path_class,
        mock_normalize,
        mock_to_audioseg,
        mock_config,
        mock_process_role,
        mock_stretch,
        mock_combine,
        mock_separate,
        mock_load,
        mock_audio_data,
        mock_song_metadata,
        mock_role_aware_sections,
        mock_stems,
        tmp_path
    ):
        """Should create role-aware mashup successfully."""
        audio, sr = mock_audio_data
        sections_a, sections_b = mock_role_aware_sections

        # Setup metadata with role-aware sections
        meta_a = mock_song_metadata.copy()
        meta_a["sections"] = sections_a
        meta_a["bpm"] = 120.0

        meta_b = mock_song_metadata.copy()
        meta_b["sections"] = sections_b
        meta_b["bpm"] = 120.0

        mock_load.side_effect = [(audio, meta_a), (audio, meta_b)]
        mock_separate.return_value = mock_stems
        mock_combine.return_value = audio
        mock_stretch.return_value = audio

        # Mock _process_vocal_by_role to return audio segments
        mock_process_role.return_value = audio[:sr]  # Return 1 second of audio

        # Mock config
        config_mock = MagicMock()
        config_mock.get.return_value = "high"
        config_mock.get_path.return_value = tmp_path
        mock_config.return_value = config_mock

        # Mock AudioSegment
        mock_audioseg = MagicMock()
        mock_to_audioseg.return_value = mock_audioseg
        mock_normalize.return_value = mock_audioseg

        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent.mkdir = MagicMock()
        mock_path_class.return_value = mock_path_instance

        # Create role-aware mashup
        result = create_role_aware_mashup(
            "song_a",
            "song_b",
            output_format="mp3"
        )

        # Verify
        assert isinstance(result, str)
        assert mock_load.call_count == 2
        assert mock_separate.call_count == 2
        mock_audioseg.export.assert_called_once()

    @patch("mixer.agents.engineer._load_song_audio")
    def test_create_role_aware_missing_sections(
        self,
        mock_load,
        mock_audio_data,
        mock_song_metadata
    ):
        """Should raise EngineerError when sections missing."""
        audio, sr = mock_audio_data

        meta_a = mock_song_metadata.copy()
        meta_a["sections"] = []
        meta_b = mock_song_metadata.copy()
        meta_b["sections"] = []

        mock_load.side_effect = [(audio, meta_a), (audio, meta_b)]

        with pytest.raises(EngineerError, match="section-level metadata"):
            create_role_aware_mashup("song_a", "song_b")

    @patch("mixer.agents.engineer._load_song_audio")
    @patch("mixer.agents.engineer.separate_stems")
    @patch("mixer.agents.engineer.combine_stems")
    def test_create_role_aware_missing_bpm(
        self,
        mock_combine,
        mock_separate,
        mock_load,
        mock_audio_data,
        mock_song_metadata,
        mock_role_aware_sections,
        mock_stems
    ):
        """Should raise EngineerError when BPM missing."""
        audio, sr = mock_audio_data
        sections_a, sections_b = mock_role_aware_sections

        meta_a = mock_song_metadata.copy()
        meta_a["sections"] = sections_a
        meta_a["bpm"] = None

        meta_b = mock_song_metadata.copy()
        meta_b["sections"] = sections_b
        meta_b["bpm"] = 120.0

        mock_load.side_effect = [(audio, meta_a), (audio, meta_b)]
        mock_separate.return_value = mock_stems
        mock_combine.return_value = audio

        with pytest.raises(EngineerError, match="BPM metadata"):
            create_role_aware_mashup("song_a", "song_b")


class TestConversationalMashup:
    """Test conversational mashup creation."""

    @patch("mixer.agents.engineer._load_song_audio")
    @patch("mixer.agents.engineer.separate_stems")
    @patch("mixer.agents.engineer.combine_stems")
    @patch("mixer.agents.engineer.time_stretch")
    @patch("mixer.agents.engineer.get_config")
    @patch("mixer.audio.processing.numpy_to_audiosegment")
    @patch("pydub.effects.normalize")
    @patch("mixer.agents.engineer.Path")
    def test_create_conversational_success(
        self,
        mock_path_class,
        mock_normalize,
        mock_to_audioseg,
        mock_config,
        mock_stretch,
        mock_combine,
        mock_separate,
        mock_load,
        mock_audio_data,
        mock_song_metadata,
        mock_conversational_sections,
        mock_stems,
        tmp_path
    ):
        """Should create conversational mashup successfully."""
        audio, sr = mock_audio_data
        sections_a, sections_b = mock_conversational_sections

        # Setup metadata with conversational sections
        meta_a = mock_song_metadata.copy()
        meta_a["sections"] = sections_a
        meta_a["bpm"] = 120.0

        meta_b = mock_song_metadata.copy()
        meta_b["sections"] = sections_b
        meta_b["bpm"] = 120.0

        mock_load.side_effect = [(audio, meta_a), (audio, meta_b)]
        mock_separate.return_value = mock_stems
        mock_combine.return_value = audio
        mock_stretch.return_value = audio

        # Mock config
        config_mock = MagicMock()
        config_mock.get.return_value = "high"
        config_mock.get_path.return_value = tmp_path
        mock_config.return_value = config_mock

        # Mock AudioSegment
        mock_audioseg = MagicMock()
        mock_to_audioseg.return_value = mock_audioseg
        mock_normalize.return_value = mock_audioseg

        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent.mkdir = MagicMock()
        mock_path_class.return_value = mock_path_instance

        # Create conversational mashup
        result = create_conversational_mashup(
            "song_a",
            "song_b",
            output_format="mp3",
            silence_duration_sec=0.5
        )

        # Verify
        assert isinstance(result, str)
        assert mock_load.call_count == 2
        assert mock_separate.call_count == 2
        mock_audioseg.export.assert_called_once()

    @patch("mixer.agents.engineer._load_song_audio")
    def test_create_conversational_missing_sections(
        self,
        mock_load,
        mock_audio_data,
        mock_song_metadata
    ):
        """Should raise EngineerError when sections missing."""
        audio, sr = mock_audio_data

        meta_a = mock_song_metadata.copy()
        meta_a["sections"] = []
        meta_b = mock_song_metadata.copy()
        meta_b["sections"] = []

        mock_load.side_effect = [(audio, meta_a), (audio, meta_b)]

        with pytest.raises(EngineerError, match="section-level metadata"):
            create_conversational_mashup("song_a", "song_b")

    @patch("mixer.agents.engineer._load_song_audio")
    @patch("mixer.agents.engineer.separate_stems")
    @patch("mixer.agents.engineer.combine_stems")
    def test_create_conversational_missing_bpm(
        self,
        mock_combine,
        mock_separate,
        mock_load,
        mock_audio_data,
        mock_song_metadata,
        mock_conversational_sections,
        mock_stems
    ):
        """Should raise EngineerError when BPM missing."""
        audio, sr = mock_audio_data
        sections_a, sections_b = mock_conversational_sections

        meta_a = mock_song_metadata.copy()
        meta_a["sections"] = sections_a
        meta_a["bpm"] = None

        meta_b = mock_song_metadata.copy()
        meta_b["sections"] = sections_b
        meta_b["bpm"] = 120.0

        mock_load.side_effect = [(audio, meta_a), (audio, meta_b)]
        mock_separate.return_value = mock_stems
        mock_combine.return_value = audio

        with pytest.raises(EngineerError, match="BPM metadata"):
            create_conversational_mashup("song_a", "song_b")

    @patch("mixer.agents.engineer._load_song_audio")
    @patch("mixer.agents.engineer.separate_stems")
    @patch("mixer.agents.engineer.combine_stems")
    @patch("mixer.agents.engineer.time_stretch")
    @patch("mixer.agents.engineer.get_config")
    @patch("mixer.audio.processing.numpy_to_audiosegment")
    @patch("pydub.effects.normalize")
    @patch("mixer.agents.engineer.Path")
    def test_create_conversational_custom_silence(
        self,
        mock_path_class,
        mock_normalize,
        mock_to_audioseg,
        mock_config,
        mock_stretch,
        mock_combine,
        mock_separate,
        mock_load,
        mock_audio_data,
        mock_song_metadata,
        mock_conversational_sections,
        mock_stems,
        tmp_path
    ):
        """Should create conversational mashup with custom silence duration."""
        audio, sr = mock_audio_data
        sections_a, sections_b = mock_conversational_sections

        # Setup metadata
        meta_a = mock_song_metadata.copy()
        meta_a["sections"] = sections_a
        meta_a["bpm"] = 120.0

        meta_b = mock_song_metadata.copy()
        meta_b["sections"] = sections_b
        meta_b["bpm"] = 120.0

        mock_load.side_effect = [(audio, meta_a), (audio, meta_b)]
        mock_separate.return_value = mock_stems
        mock_combine.return_value = audio
        mock_stretch.return_value = audio

        # Mock config
        config_mock = MagicMock()
        config_mock.get.return_value = "high"
        config_mock.get_path.return_value = tmp_path
        mock_config.return_value = config_mock

        # Mock AudioSegment
        mock_audioseg = MagicMock()
        mock_to_audioseg.return_value = mock_audioseg
        mock_normalize.return_value = mock_audioseg

        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent.mkdir = MagicMock()
        mock_path_class.return_value = mock_path_instance

        # Create with custom silence duration
        result = create_conversational_mashup(
            "song_a",
            "song_b",
            silence_duration_sec=1.0,  # Longer silence
            output_format="mp3"
        )

        # Verify
        assert isinstance(result, str)
        mock_audioseg.export.assert_called_once()
