"""Unit tests for Analyst Agent."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from mixer.agents.analyst import (
    profile_audio,
    _analyze_signal,
    _analyze_sections,
    _extract_section_lyrics,
    _analyze_section_vocals,
    AnalysisError,
)
from mixer.audio.analysis import (
    detect_sections,
    classify_section_type,
    analyze_section_energy,
    estimate_key,
    key_to_camelot,
)


class TestSignalAnalysis:
    """Test basic signal analysis functions."""

    def test_key_estimation(self):
        """Should estimate musical key from chroma features."""
        # Create a simple C major chroma
        chroma = np.zeros((12, 100))
        chroma[[0, 4, 7], :] = 1.0  # C, E, G (C major triad)

        key = estimate_key(chroma)

        # Should detect C major or a related key
        assert "maj" in key or "min" in key

    def test_camelot_conversion(self):
        """Should convert keys to Camelot notation."""
        assert key_to_camelot("Cmaj") == "8B"
        assert key_to_camelot("Amin") == "8A"
        assert key_to_camelot("Gmaj") == "9B"
        assert key_to_camelot("Unknown") == "Unknown"

    @patch('librosa.beat.beat_track')
    @patch('librosa.feature.chroma_cqt')
    @patch('librosa.feature.rms')
    @patch('librosa.get_duration')
    def test_analyze_signal_success(
        self,
        mock_duration,
        mock_rms,
        mock_chroma,
        mock_beat_track
    ):
        """Should successfully analyze audio signal."""
        # Setup mocks
        mock_beat_track.return_value = (128.0, np.array([0, 100, 200]))
        mock_chroma.return_value = np.random.rand(12, 100)
        mock_rms.return_value = np.array([[0.5]])
        mock_duration.return_value = 180.0

        # Create dummy audio
        y = np.random.rand(44100 * 3)  # 3 seconds
        sr = 44100

        result = _analyze_signal(y, sr)

        # Verify results
        assert result['bpm'] == 128.0
        assert result['duration_sec'] == 180.0
        assert 'key' in result
        assert 'camelot' in result
        assert 0.0 <= result['energy_level'] <= 1.0


class TestSectionDetection:
    """Test section detection and classification."""

    @patch('librosa.feature.chroma_cqt')
    @patch('librosa.segment.agglomerative')
    @patch('librosa.frames_to_time')
    @patch('librosa.get_duration')
    def test_detect_sections(
        self,
        mock_duration,
        mock_frames_to_time,
        mock_agglomerative,
        mock_chroma
    ):
        """Should detect section boundaries."""
        # Setup mocks
        mock_duration.return_value = 180.0  # 3 minutes
        mock_chroma.return_value = np.random.rand(12, 1000)
        mock_agglomerative.return_value = np.array([0, 250, 500, 750, 1000])
        mock_frames_to_time.return_value = np.array([0.0, 30.0, 60.0, 90.0, 120.0])

        # Create dummy audio
        y = np.random.rand(44100 * 180)
        sr = 44100

        sections = detect_sections(y, sr)

        # Should return list of (start, end) tuples
        assert isinstance(sections, list)
        assert len(sections) > 0
        assert all(isinstance(s, tuple) and len(s) == 2 for s in sections)

    def test_classify_section_type(self):
        """Should classify sections based on position and features."""
        # First section should be intro
        assert classify_section_type(0, 8, 0.5, 2000) == "intro"

        # Last section should be outro
        assert classify_section_type(7, 8, 0.5, 2000) == "outro"

        # High energy + bright should be chorus
        assert classify_section_type(3, 8, 0.8, 3000) == "chorus"

        # Low energy should be bridge
        assert classify_section_type(3, 8, 0.2, 1500) == "bridge"

        # Medium energy should be verse
        assert classify_section_type(3, 8, 0.5, 2000) == "verse"

    @patch('librosa.feature.rms')
    @patch('librosa.feature.spectral_centroid')
    @patch('librosa.beat.beat_track')
    def test_analyze_section_energy(
        self,
        mock_beat_track,
        mock_centroid,
        mock_rms
    ):
        """Should analyze energy for a section."""
        # Setup mocks
        mock_rms.return_value = np.array([[0.6, 0.6, 0.6]])
        mock_centroid.return_value = np.array([[2500.0, 2500.0]])
        mock_beat_track.return_value = (120.0, np.array([0, 10, 20, 30]))

        # Create dummy audio
        y = np.random.rand(44100 * 10)  # 10 seconds
        sr = 44100

        result = analyze_section_energy(y, sr, 0.0, 10.0)

        assert 'energy_level' in result
        assert 'spectral_centroid' in result
        assert 'tempo_stability' in result
        assert 0.0 <= result['energy_level'] <= 1.0


class TestLyricExtraction:
    """Test lyric extraction from word timings."""

    def test_extract_section_lyrics_with_timings(self):
        """Should extract lyrics for a section from word timings."""
        word_timings = [
            {"start": 0.0, "end": 2.0, "text": "Hello"},
            {"start": 2.0, "end": 4.0, "text": "world"},
            {"start": 10.0, "end": 12.0, "text": "goodbye"},
        ]

        # Extract first section (0-5s)
        lyrics = _extract_section_lyrics(0.0, 5.0, word_timings, "")
        assert "Hello" in lyrics
        assert "world" in lyrics
        assert "goodbye" not in lyrics

        # Extract second section (8-15s)
        lyrics = _extract_section_lyrics(8.0, 15.0, word_timings, "")
        assert "goodbye" in lyrics
        assert "Hello" not in lyrics

    def test_extract_section_lyrics_no_timings(self):
        """Should return empty string when no timings available."""
        lyrics = _extract_section_lyrics(0.0, 10.0, [], "full transcript")
        assert lyrics == ""


class TestVocalAnalysis:
    """Test vocal characteristic analysis."""

    @patch('librosa.feature.rms')
    def test_analyze_section_vocals(self, mock_rms):
        """Should analyze vocal characteristics."""
        mock_rms.return_value = np.array([[0.7]])

        y = np.random.rand(44100 * 10)
        sr = 44100

        # Dense lyrics (high word count)
        result = _analyze_section_vocals(y, sr, 0.0, 10.0, "lots of words " * 50)
        assert result['vocal_density'] == "dense"
        assert 0.0 <= result['vocal_intensity'] <= 1.0

        # Sparse lyrics (low word count)
        result = _analyze_section_vocals(y, sr, 0.0, 10.0, "few words")
        assert result['vocal_density'] == "sparse"

        # Medium lyrics
        result = _analyze_section_vocals(y, sr, 0.0, 10.0, "some words here " * 10)
        assert result['vocal_density'] in ["medium", "dense", "sparse"]


class TestIntegration:
    """Integration tests for full pipeline."""

    @patch('mixer.agents.analyst.whisper.load_model')
    @patch('mixer.agents.analyst.upsert_song')
    @patch('mixer.agents.analyst.analyze_song_semantics')
    @patch('mixer.agents.analyst.analyze_section_semantics')
    @patch('librosa.load')
    @patch('librosa.beat.beat_track')
    @patch('librosa.feature.chroma_cqt')
    @patch('librosa.get_duration')
    def test_profile_audio_success(
        self,
        mock_duration,
        mock_chroma,
        mock_beat_track,
        mock_load,
        mock_section_semantics,
        mock_song_semantics,
        mock_upsert,
        mock_whisper,
        tmp_path
    ):
        """Should successfully profile an audio file."""
        # Create a test file
        test_file = tmp_path / "test.wav"
        test_file.touch()

        # Setup mocks
        mock_load.return_value = (np.random.rand(44100 * 60), 44100)
        mock_duration.return_value = 60.0
        mock_beat_track.return_value = (120.0, np.array([0, 100, 200]))
        mock_chroma.return_value = np.random.rand(12, 100)

        # Mock Whisper
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "test lyrics " * 20,
            "segments": []
        }
        mock_whisper.return_value = mock_model

        # Mock semantic analysis
        mock_song_semantics.return_value = {
            "genres": ["Pop"],
            "primary_genre": "Pop",
            "irony_score": 0,
            "mood_summary": "Upbeat and happy",
            "valence": 8
        }

        mock_section_semantics.return_value = {
            "emotional_tone": "happy",
            "lyrical_function": "hook",
            "themes": ["love"]
        }

        # Call profile_audio
        result = profile_audio(
            str(test_file),
            "test_song",
            "Test Artist",
            "Test Song"
        )

        # Verify result
        assert result['status'] == "success"
        assert result['song_id'] == "test_song"
        assert 'metadata' in result

        # Verify upsert was called
        mock_upsert.assert_called_once()
