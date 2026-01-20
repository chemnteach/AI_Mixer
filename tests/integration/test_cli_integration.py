"""Integration tests for CLI commands."""

import pytest
from click.testing import CliRunner
from mixer.cli import main
from mixer.memory import reset_client


@pytest.fixture
def cli_runner():
    """Create Click CLI test runner."""
    return CliRunner()


@pytest.fixture(autouse=True)
def reset_db():
    """Reset ChromaDB between tests."""
    reset_client()
    yield
    reset_client()


@pytest.mark.integration
def test_cli_help(cli_runner):
    """Test CLI help command."""
    result = cli_runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert "The Mixer" in result.output
    assert "ingest" in result.output
    assert "mashup" in result.output


@pytest.mark.integration
def test_cli_version(cli_runner):
    """Test CLI version command."""
    result = cli_runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


@pytest.mark.integration
def test_library_list_empty(cli_runner):
    """Test library list with empty library."""
    result = cli_runner.invoke(main, ['library', 'list'])
    assert result.exit_code == 0
    assert "Library is empty" in result.output


@pytest.mark.integration
def test_library_stats_empty(cli_runner):
    """Test library stats with empty library."""
    result = cli_runner.invoke(main, ['library', 'stats'])
    assert result.exit_code == 0
    assert "Library is empty" in result.output


@pytest.mark.integration
@pytest.mark.skip(reason="Requires real audio file")
def test_cli_ingest_local_file(cli_runner):
    """Test ingesting a local audio file via CLI."""
    test_file = "path/to/test_audio.mp3"

    result = cli_runner.invoke(main, ['ingest', test_file])

    assert result.exit_code == 0
    assert "Successfully ingested" in result.output or "already in library" in result.output


@pytest.mark.integration
@pytest.mark.skip(reason="Requires real audio files")
def test_cli_analyze_song(cli_runner):
    """Test analyzing a song via CLI."""
    # First ingest
    test_file = "path/to/test_audio.mp3"
    cli_runner.invoke(main, ['ingest', test_file])

    # Then analyze
    result = cli_runner.invoke(main, ['analyze', 'test_song_id'])

    assert result.exit_code == 0
    assert "Analysis complete" in result.output


@pytest.mark.integration
@pytest.mark.skip(reason="Requires real audio files")
def test_cli_match_command(cli_runner):
    """Test match command via CLI."""
    result = cli_runner.invoke(main, ['match', 'test_song_id'])

    # Should either find matches or report error
    assert result.exit_code in [0, 1]


@pytest.mark.integration
@pytest.mark.skip(reason="Requires real audio files")
def test_cli_mashup_workflow(cli_runner):
    """Test full mashup creation via CLI."""
    song_a = "path/to/song_a.mp3"
    song_b = "path/to/song_b.mp3"

    result = cli_runner.invoke(main, ['mashup', song_a, song_b, '--type', 'classic'])

    assert result.exit_code == 0
    assert "Mashup created successfully" in result.output


@pytest.mark.integration
def test_cli_invalid_command(cli_runner):
    """Test CLI with invalid command."""
    result = cli_runner.invoke(main, ['invalid_command'])

    assert result.exit_code != 0
    assert "Error" in result.output or "Usage" in result.output


@pytest.mark.integration
def test_analyze_without_args(cli_runner):
    """Test analyze command without required arguments."""
    result = cli_runner.invoke(main, ['analyze'])

    assert result.exit_code == 1
    assert "Error" in result.output


@pytest.mark.integration
@pytest.mark.skip(reason="Requires interactive input")
def test_cli_interactive_mode(cli_runner):
    """Test interactive mode.

    This test requires simulating user input which is complex with Click.
    Left as manual test for now.
    """
    pass
