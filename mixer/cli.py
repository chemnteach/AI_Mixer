"""Command-line interface for The Mixer."""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from mixer.config import get_config
from mixer.utils.logging import setup_logging, get_logger


console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
@click.option(
    '--config',
    type=click.Path(exists=True, path_type=Path),
    help='Path to configuration file (default: ./config.yaml)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output (DEBUG level)'
)
@click.pass_context
def main(ctx: click.Context, config: Path | None, verbose: bool) -> None:
    """The Mixer - Intelligent Audio Mashup Pipeline.

    Create musical mashups using semantic understanding, not just BPM/key matching.
    """
    # Initialize configuration
    ctx.ensure_object(dict)
    cfg = get_config(config)
    ctx.obj['config'] = cfg

    # Setup logging
    log_level = "DEBUG" if verbose else cfg.get("logging.level", "INFO")
    log_file = Path(cfg.get("logging.file", "logs/mixer.log"))
    setup_logging(
        log_file=log_file,
        level=log_level,
        max_file_size_mb=cfg.get("logging.max_file_size_mb", 100),
        backup_count=cfg.get("logging.backup_count", 5)
    )

    logger.info("The Mixer initialized")


@main.command()
@click.argument('input_source')
@click.pass_context
def ingest(ctx: click.Context, input_source: str) -> None:
    """Ingest audio from YouTube URL or local file.

    INPUT_SOURCE: YouTube URL or path to audio file
    """
    console.print(Panel.fit(
        f"[bold cyan]Ingesting:[/bold cyan] {input_source}",
        border_style="cyan"
    ))

    # TODO: Implement ingestion logic
    console.print("[yellow]⚠ Ingestion not yet implemented[/yellow]")


@main.command()
@click.option(
    '--batch',
    is_flag=True,
    help='Analyze all un-profiled songs in library'
)
@click.argument('song_id', required=False)
@click.pass_context
def analyze(ctx: click.Context, batch: bool, song_id: str | None) -> None:
    """Analyze audio and extract metadata.

    If SONG_ID provided, analyze specific song.
    If --batch flag set, analyze all un-profiled songs.
    """
    if batch:
        console.print("[bold cyan]Analyzing all un-profiled songs...[/bold cyan]")
    elif song_id:
        console.print(f"[bold cyan]Analyzing song:[/bold cyan] {song_id}")
    else:
        console.print("[red]Error: Provide SONG_ID or use --batch[/red]")
        sys.exit(1)

    # TODO: Implement analysis logic
    console.print("[yellow]⚠ Analysis not yet implemented[/yellow]")


@main.command()
@click.argument('song_id')
@click.option(
    '--genre',
    help='Filter by genre (e.g., "Country")'
)
@click.option(
    '--semantic',
    help='Semantic query (e.g., "ironic and upbeat")'
)
@click.option(
    '--criteria',
    type=click.Choice(['harmonic', 'semantic', 'hybrid']),
    default='hybrid',
    help='Matching strategy (default: hybrid)'
)
@click.option(
    '--max-results',
    type=int,
    default=5,
    help='Maximum number of matches (default: 5)'
)
@click.pass_context
def match(
    ctx: click.Context,
    song_id: str,
    genre: str | None,
    semantic: str | None,
    criteria: str,
    max_results: int
) -> None:
    """Find compatible songs for mashup.

    SONG_ID: ID of the target song
    """
    console.print(Panel.fit(
        f"[bold cyan]Finding matches for:[/bold cyan] {song_id}\n"
        f"[dim]Criteria: {criteria}[/dim]",
        border_style="cyan"
    ))

    # TODO: Implement matching logic
    console.print("[yellow]⚠ Matching not yet implemented[/yellow]")


@main.command()
@click.argument('vocal_id')
@click.argument('instrumental_id')
@click.option(
    '--output',
    type=click.Choice(['draft', 'high', 'broadcast']),
    default='high',
    help='Quality preset (default: high)'
)
@click.option(
    '--format',
    'output_format',
    type=click.Choice(['mp3', 'wav']),
    default='mp3',
    help='Output format (default: mp3)'
)
@click.pass_context
def mashup(
    ctx: click.Context,
    vocal_id: str,
    instrumental_id: str,
    output: str,
    output_format: str
) -> None:
    """Create mashup from two songs.

    VOCAL_ID: Song to extract vocals from
    INSTRUMENTAL_ID: Song to extract instrumental from
    """
    console.print(Panel.fit(
        f"[bold cyan]Building mashup:[/bold cyan]\n"
        f"Vocals: {vocal_id}\n"
        f"Instrumental: {instrumental_id}\n"
        f"Quality: {output}",
        border_style="cyan"
    ))

    # TODO: Implement mashup building logic
    console.print("[yellow]⚠ Mashup creation not yet implemented[/yellow]")


@main.group()
def library() -> None:
    """Library management commands."""
    pass


@library.command('list')
@click.option(
    '--limit',
    type=int,
    default=20,
    help='Maximum number of songs to display (default: 20)'
)
@click.pass_context
def library_list(ctx: click.Context, limit: int) -> None:
    """List all songs in library."""
    console.print(f"[bold cyan]Library (showing {limit} songs):[/bold cyan]")

    # TODO: Implement library listing
    console.print("[yellow]⚠ Library listing not yet implemented[/yellow]")


@library.command('search')
@click.argument('query')
@click.pass_context
def library_search(ctx: click.Context, query: str) -> None:
    """Semantic search in library.

    QUERY: Search query (e.g., "upbeat country songs")
    """
    console.print(f"[bold cyan]Searching for:[/bold cyan] {query}")

    # TODO: Implement semantic search
    console.print("[yellow]⚠ Library search not yet implemented[/yellow]")


@library.command('stats')
@click.pass_context
def library_stats(ctx: click.Context) -> None:
    """Show library statistics."""
    console.print("[bold cyan]Library Statistics:[/bold cyan]")

    # TODO: Implement stats display
    console.print("[yellow]⚠ Library stats not yet implemented[/yellow]")


@main.command()
@click.argument('input_source')
@click.pass_context
def auto(ctx: click.Context, input_source: str) -> None:
    """Fully automated workflow: ingest → analyze → match → mashup.

    INPUT_SOURCE: YouTube URL or path to audio file
    """
    console.print(Panel.fit(
        "[bold cyan]Starting automated workflow...[/bold cyan]",
        border_style="cyan"
    ))

    # TODO: Implement automated workflow
    console.print("[yellow]⚠ Auto workflow not yet implemented[/yellow]")


if __name__ == '__main__':
    main()
