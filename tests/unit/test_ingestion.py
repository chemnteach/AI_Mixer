"""Unit tests for Ingestion Agent."""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mixer.agents.ingestion import (
    detect_source_type,
    extract_artist_title_from_filename,
    extract_artist_title_from_youtube_title,
    check_cache,
    validate_audio_file,
    ingest_song,
    InvalidInputError,
    DownloadError,
    ValidationError,
)


class TestSourceDetection:
    """Test input source type detection."""

    def test_detect_youtube_url(self):
        """Should detect YouTube URLs."""
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=abc123",
        ]

        for url in urls:
            assert detect_source_type(url) == "youtube"

    def test_detect_local_file(self, tmp_path):
        """Should detect local files."""
        # Create a temporary file
        test_file = tmp_path / "test.mp3"
        test_file.touch()

        assert detect_source_type(str(test_file)) == "local_file"

    def test_invalid_input_non_youtube_url(self):
        """Should reject non-YouTube URLs."""
        with pytest.raises(InvalidInputError, match="not a YouTube link"):
            detect_source_type("https://example.com/song.mp3")

    def test_invalid_input_nonexistent_file(self):
        """Should reject nonexistent files."""
        with pytest.raises(InvalidInputError, match="neither a YouTube URL nor an existing file"):
            detect_source_type("/path/to/nonexistent/file.mp3")


class TestArtistTitleExtraction:
    """Test artist/title extraction from various sources."""

    def test_extract_from_filename_dash_separator(self):
        """Should extract artist and title with ' - ' separator."""
        artist, title = extract_artist_title_from_filename("Taylor Swift - Shake It Off.mp3")
        assert artist == "Taylor Swift"
        assert title == "Shake It Off"

    def test_extract_from_filename_underscore_separator(self):
        """Should extract artist and title with '_-_' separator."""
        artist, title = extract_artist_title_from_filename("Drake_-_Hotline Bling.wav")
        assert artist == "Drake"
        assert title == "Hotline Bling"

    def test_extract_from_filename_no_artist(self):
        """Should use 'Unknown' when no artist detected."""
        artist, title = extract_artist_title_from_filename("Some Song.mp3")
        assert artist == "Unknown"
        assert title == "Some Song"

    def test_extract_from_youtube_title_dash(self):
        """Should extract from YouTube title with ' - '."""
        artist, title = extract_artist_title_from_youtube_title(
            "Taylor Swift - Shake It Off (Official Video)"
        )
        assert artist == "Taylor Swift"
        assert title == "Shake It Off (Official Video)"

    def test_extract_from_youtube_title_colon(self):
        """Should extract from YouTube title with ': '."""
        artist, title = extract_artist_title_from_youtube_title(
            "Artist Name: Song Title"
        )
        assert artist == "Artist Name"
        assert title == "Song Title"

    def test_extract_from_youtube_title_no_separator(self):
        """Should use 'Unknown' when no separator found."""
        artist, title = extract_artist_title_from_youtube_title("Just A Title")
        assert artist == "Unknown"
        assert title == "Just A Title"


class TestCacheChecking:
    """Test ChromaDB cache checking."""

    @patch('mixer.agents.ingestion.get_client')
    def test_check_cache_hit(self, mock_get_client):
        """Should return metadata when song is cached."""
        # Mock ChromaDB client
        mock_collection = Mock()
        mock_collection.get.return_value = {
            'ids': ['taylor_swift_shake_it_off'],
            'metadatas': [{'path': '/path/to/song.wav', 'bpm': 120.0}]
        }

        mock_client = Mock()
        mock_client.get_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        # Call check_cache
        result = check_cache('taylor_swift_shake_it_off')

        assert result is not None
        assert result['path'] == '/path/to/song.wav'
        assert result['bpm'] == 120.0

    @patch('mixer.agents.ingestion.get_client')
    def test_check_cache_miss(self, mock_get_client):
        """Should return None when song not cached."""
        # Mock ChromaDB client
        mock_collection = Mock()
        mock_collection.get.return_value = {
            'ids': [],
            'metadatas': []
        }

        mock_client = Mock()
        mock_client.get_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        # Call check_cache
        result = check_cache('nonexistent_song')

        assert result is None


class TestFileValidation:
    """Test audio file validation."""

    def test_validate_nonexistent_file(self):
        """Should raise error for nonexistent file."""
        with pytest.raises(ValidationError, match="File does not exist"):
            validate_audio_file("/path/to/nonexistent.wav")

    def test_validate_file_too_small(self, tmp_path):
        """Should raise error for files < 100KB."""
        small_file = tmp_path / "small.wav"
        small_file.write_bytes(b"tiny")  # < 100KB

        with pytest.raises(ValidationError, match="File too small"):
            validate_audio_file(str(small_file))

    @patch('librosa.get_duration')
    def test_validate_file_too_short(self, mock_get_duration, tmp_path):
        """Should raise error for audio < 30 seconds."""
        # Create a file > 100KB
        test_file = tmp_path / "short.wav"
        test_file.write_bytes(b"x" * 200000)  # 200KB

        # Mock duration
        mock_get_duration.return_value = 15.0  # 15 seconds

        with pytest.raises(ValidationError, match="Audio too short"):
            validate_audio_file(str(test_file))

    @patch('librosa.get_duration')
    def test_validate_success(self, mock_get_duration, tmp_path):
        """Should pass validation for valid file."""
        # Create a file > 100KB
        test_file = tmp_path / "valid.wav"
        test_file.write_bytes(b"x" * 200000)  # 200KB

        # Mock duration
        mock_get_duration.return_value = 180.0  # 3 minutes

        # Should not raise
        validate_audio_file(str(test_file))


class TestLocalFileIngestion:
    """Test local file ingestion."""

    @patch('mixer.agents.ingestion.check_cache')
    @patch('mixer.agents.ingestion.convert_to_standard_wav')
    @patch('mixer.agents.ingestion.validate_audio_file')
    def test_ingest_local_file_success(
        self,
        mock_validate,
        mock_convert,
        mock_cache,
        tmp_path
    ):
        """Should successfully ingest a local file."""
        # Setup
        mock_cache.return_value = None  # Not cached

        # Create test file
        test_file = tmp_path / "Taylor Swift - Shake It Off.mp3"
        test_file.touch()

        # Call ingest_song
        with patch('mixer.agents.ingestion.get_config') as mock_config:
            mock_cfg = Mock()
            mock_cfg.get_path.return_value = tmp_path
            mock_config.return_value = mock_cfg

            result = ingest_song(str(test_file))

        # Assertions
        assert result['id'] == 'taylor_swift_shake_it_off'
        assert result['cached'] is False
        assert result['source'] == 'local_file'
        assert result['metadata'] is None

        mock_convert.assert_called_once()
        mock_validate.assert_called_once()

    @patch('mixer.agents.ingestion.check_cache')
    def test_ingest_local_file_cached(self, mock_cache, tmp_path):
        """Should return cached result without processing."""
        # Setup cached metadata
        cached_path = str(tmp_path / "cached.wav")
        Path(cached_path).touch()  # Create the cached file

        mock_cache.return_value = {
            'path': cached_path,
            'bpm': 128.0
        }

        # Create test file
        test_file = tmp_path / "Artist - Song.mp3"
        test_file.touch()

        # Call ingest_song
        result = ingest_song(str(test_file))

        # Assertions
        assert result['cached'] is True
        assert result['path'] == cached_path
        assert result['metadata']['bpm'] == 128.0


class TestYouTubeIngestion:
    """Test YouTube URL ingestion."""

    @patch('subprocess.run')
    @patch('mixer.agents.ingestion.check_cache')
    @patch('mixer.agents.ingestion.validate_audio_file')
    def test_ingest_youtube_url_success(
        self,
        mock_validate,
        mock_cache,
        mock_subprocess,
        tmp_path
    ):
        """Should successfully download from YouTube."""
        # Setup
        mock_cache.return_value = None  # Not cached

        # Mock metadata fetch
        metadata_result = Mock()
        metadata_result.returncode = 0
        metadata_result.stdout = '{"title": "Taylor Swift - Shake It Off"}'

        # Mock download
        download_result = Mock()
        download_result.returncode = 0

        # Mock subprocess calls (metadata then download)
        mock_subprocess.side_effect = [metadata_result, download_result]

        # Create the expected output file
        output_file = tmp_path / "taylor_swift_shake_it_off.wav"
        output_file.touch()

        # Call ingest_song
        url = "https://www.youtube.com/watch?v=test123"

        with patch('mixer.agents.ingestion.get_config') as mock_config:
            mock_cfg = Mock()
            mock_cfg.get_path.return_value = tmp_path
            mock_config.return_value = mock_cfg

            with patch('os.path.exists', return_value=True):
                result = ingest_song(url)

        # Assertions
        assert result['id'] == 'taylor_swift_shake_it_off'
        assert result['cached'] is False
        assert result['source'] == 'youtube'

        # Verify subprocess was called twice (metadata + download)
        assert mock_subprocess.call_count == 2

    @patch('subprocess.run')
    @patch('mixer.agents.ingestion.check_cache')
    def test_ingest_youtube_url_download_failure(self, mock_cache, mock_subprocess, tmp_path):
        """Should raise DownloadError when download fails."""
        # Setup
        mock_cache.return_value = None  # Not cached

        # Mock metadata fetch (success)
        metadata_result = Mock()
        metadata_result.returncode = 0
        metadata_result.stdout = '{"title": "Test Video"}'

        # Mock download (failure)
        download_result = Mock()
        download_result.returncode = 1
        download_result.stderr = "Download error"

        mock_subprocess.side_effect = [metadata_result, download_result]

        url = "https://www.youtube.com/watch?v=test123"

        with patch('mixer.agents.ingestion.get_config') as mock_config:
            mock_cfg = Mock()
            mock_cfg.get_path.return_value = tmp_path
            mock_config.return_value = mock_cfg

            with pytest.raises(DownloadError, match="yt-dlp download failed"):
                ingest_song(url, max_retries=1)  # Only 1 retry for faster test


class TestIntegration:
    """Integration tests (require actual dependencies)."""

    def test_ingest_song_invalid_input(self):
        """Should raise InvalidInputError for invalid input."""
        with pytest.raises(InvalidInputError):
            ingest_song("not_a_file_or_url")

    def test_ingest_song_non_youtube_url(self):
        """Should raise InvalidInputError for non-YouTube URLs."""
        with pytest.raises(InvalidInputError, match="not a YouTube link"):
            ingest_song("https://example.com/song.mp3")
