"""Command-line interface for The Mixer."""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from mixer.config import get_config
from mixer.utils.logging import setup_logging, get_logger
from mixer.agents import (
    ingest_song,
    profile_audio,
    find_match,
    IngestionError,
    AnalysisError,
    CuratorError,
    EngineerError,
)
from mixer.workflow import run_mashup_workflow, WorkflowError
from mixer.memory import get_client, get_song

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
@click.argument('input_source', required=False)
@click.option(
    '--folder',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help='Ingest all audio files from a folder'
)
@click.option(
    '--playlist',
    help='Ingest all videos from a YouTube playlist URL'
)
@click.option(
    '--max',
    'max_songs',
    type=int,
    help='Maximum number of songs to ingest from playlist'
)
@click.option(
    '--analyze',
    is_flag=True,
    help='Automatically analyze songs after ingestion'
)
@click.pass_context
def ingest(ctx: click.Context, input_source: str | None, folder: str | None, playlist: str | None, max_songs: int | None, analyze: bool) -> None:
    """Ingest audio from YouTube URL, local file, folder, or playlist.

    INPUT_SOURCE: YouTube URL or path to audio file (if not using --folder or --playlist)
    """
    from pathlib import Path

    # Validate arguments
    if not input_source and not folder and not playlist:
        console.print("[red]Error: Provide INPUT_SOURCE, --folder, or --playlist[/red]")
        sys.exit(1)

    exclusive_count = sum([bool(input_source), bool(folder), bool(playlist)])
    if exclusive_count > 1:
        console.print("[red]Error: Cannot use INPUT_SOURCE, --folder, and --playlist together[/red]")
        sys.exit(1)

    # Single file/URL mode
    if input_source:
        console.print(Panel.fit(
            f"[bold cyan]Ingesting:[/bold cyan] {input_source}",
            border_style="cyan"
        ))

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Downloading and processing...", total=None)

                result = ingest_song(input_source)

                progress.update(task, description="✓ Complete")

            if result["cached"]:
                console.print(f"[yellow]⚠ Song already in library:[/yellow] {result['id']}")
            else:
                console.print(f"[green]✓ Successfully ingested:[/green] {result['id']}")

            console.print(f"[dim]Path:[/dim] {result['path']}")
            console.print(f"[dim]Source:[/dim] {result['source']}")

            # Auto-analyze if requested
            if analyze:
                console.print("\n[bold cyan]Analyzing song...[/bold cyan]")
                try:
                    from mixer.agents import profile_audio
                    song_data = get_song(result['id'])
                    if song_data:
                        profile_audio(song_data['metadata']['path'])
                        console.print(f"[green]✓ Analysis complete![/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠ Analysis failed:[/yellow] {e}")

        except IngestionError as e:
            console.print(f"[red]✗ Ingestion failed:[/red] {e}")
            sys.exit(1)

    # Batch folder mode
    elif folder:
        folder_path = Path(folder)

        console.print(Panel.fit(
            f"[bold cyan]Batch Ingesting from:[/bold cyan] {folder_path}",
            border_style="cyan"
        ))

        # Find all audio files
        audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}
        audio_files = []

        for ext in audio_extensions:
            audio_files.extend(folder_path.glob(f"*{ext}"))
            audio_files.extend(folder_path.glob(f"*{ext.upper()}"))

        if not audio_files:
            console.print(f"[yellow]No audio files found in {folder_path}[/yellow]")
            return

        console.print(f"Found {len(audio_files)} audio files\n")

        # Ingest each file
        ingested = []
        skipped = []
        failed = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Ingesting files...", total=len(audio_files))

            for audio_file in audio_files:
                progress.update(task, description=f"Ingesting: {audio_file.name}")

                try:
                    result = ingest_song(str(audio_file))

                    if result["cached"]:
                        skipped.append(audio_file.name)
                    else:
                        ingested.append(result['id'])

                except Exception as e:
                    failed.append((audio_file.name, str(e)))

                progress.advance(task)

        # Summary
        console.print("\n[bold]Ingestion Summary:[/bold]")
        console.print(f"  [green]✓ Ingested:[/green] {len(ingested)}")
        console.print(f"  [yellow]⚠ Skipped (already in library):[/yellow] {len(skipped)}")
        console.print(f"  [red]✗ Failed:[/red] {len(failed)}")

        if failed:
            console.print("\n[bold red]Failed files:[/bold red]")
            for filename, error in failed:
                console.print(f"  - {filename}: {error}")

        # Auto-analyze if requested
        if analyze and ingested:
            console.print("\n[bold cyan]Analyzing ingested songs...[/bold cyan]")

            from mixer.agents import profile_audio

            analyzed = 0
            analysis_failed = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing...", total=len(ingested))

                for song_id in ingested:
                    progress.update(task, description=f"Analyzing: {song_id}")

                    try:
                        song_data = get_song(song_id)
                        if song_data:
                            profile_audio(song_data['metadata']['path'])
                            analyzed += 1
                    except Exception as e:
                        analysis_failed += 1
                        console.print(f"[yellow]⚠ Analysis failed for {song_id}:[/yellow] {e}")

                    progress.advance(task)

            console.print(f"\n[green]✓ Analyzed {analyzed} songs[/green]")
            if analysis_failed:
                console.print(f"[yellow]⚠ {analysis_failed} analysis failures[/yellow]")

    # Batch playlist mode
    elif playlist:
        console.print(Panel.fit(
            f"[bold cyan]Extracting Playlist:[/bold cyan] {playlist}",
            border_style="cyan"
        ))

        try:
            from mixer.agents import extract_playlist_info

            # Extract playlist info
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Fetching playlist...", total=None)
                videos = extract_playlist_info(playlist)
                progress.update(task, description="✓ Playlist fetched")

            if not videos:
                console.print("[yellow]No videos found in playlist[/yellow]")
                return

            # Apply max limit
            if max_songs and max_songs < len(videos):
                videos = videos[:max_songs]
                console.print(f"[yellow]Limiting to first {max_songs} videos[/yellow]")

            console.print(f"Found {len(videos)} videos\n")

            # Show preview table
            table = Table(title="Playlist Videos")
            table.add_column("#", style="dim")
            table.add_column("Title", style="cyan")
            table.add_column("Uploader", style="green")
            table.add_column("Duration", justify="right")

            for i, video in enumerate(videos[:10], 1):  # Show first 10
                duration_str = f"{video['duration']//60}:{video['duration']%60:02d}" if video['duration'] else "N/A"
                table.add_row(str(i), video['title'][:50], video['uploader'][:20], duration_str)

            if len(videos) > 10:
                table.add_row("...", f"... and {len(videos)-10} more", "", "")

            console.print(table)
            console.print()

            # Confirm ingestion
            if not click.confirm(f"Ingest {len(videos)} videos from playlist?", default=True):
                console.print("[yellow]Cancelled[/yellow]")
                return

            # Ingest each video
            ingested = []
            skipped = []
            failed = []

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("Ingesting videos...", total=len(videos))

                for video in videos:
                    progress.update(task, description=f"Ingesting: {video['title'][:40]}")

                    try:
                        result = ingest_song(video['url'])

                        if result["cached"]:
                            skipped.append(video['title'])
                        else:
                            ingested.append(result['id'])

                    except Exception as e:
                        failed.append((video['title'], str(e)))

                    progress.advance(task)

            # Summary
            console.print("\n[bold]Ingestion Summary:[/bold]")
            console.print(f"  [green]✓ Ingested:[/green] {len(ingested)}")
            console.print(f"  [yellow]⚠ Skipped (already in library):[/yellow] {len(skipped)}")
            console.print(f"  [red]✗ Failed:[/red] {len(failed)}")

            if failed:
                console.print("\n[bold red]Failed videos:[/bold red]")
                for title, error in failed[:5]:  # Show first 5
                    console.print(f"  - {title[:50]}: {error}")
                if len(failed) > 5:
                    console.print(f"  ... and {len(failed)-5} more failures")

            # Auto-analyze if requested
            if analyze and ingested:
                console.print("\n[bold cyan]Analyzing ingested songs...[/bold cyan]")

                from mixer.agents import profile_audio

                analyzed = 0
                analysis_failed = 0

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    console=console
                ) as progress:
                    task = progress.add_task("Analyzing...", total=len(ingested))

                    for song_id in ingested:
                        progress.update(task, description=f"Analyzing: {song_id}")

                        try:
                            song_data = get_song(song_id)
                            if song_data:
                                profile_audio(song_data['metadata']['path'])
                                analyzed += 1
                        except Exception as e:
                            analysis_failed += 1

                        progress.advance(task)

                console.print(f"\n[green]✓ Analyzed {analyzed} songs[/green]")
                if analysis_failed:
                    console.print(f"[yellow]⚠ {analysis_failed} analysis failures[/yellow]")

        except IngestionError as e:
            console.print(f"[red]✗ Playlist ingestion failed:[/red] {e}")
            sys.exit(1)


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
    if not batch and not song_id:
        console.print("[red]Error: Provide SONG_ID or use --batch[/red]")
        sys.exit(1)

    try:
        if batch:
            console.print("[bold cyan]Analyzing all un-profiled songs...[/bold cyan]")

            # Get all songs
            client = get_client()
            collection = client.get_collection()
            all_songs = collection.get(include=["metadatas"])

            # Filter for un-profiled (no sections)
            un_profiled = []
            for song_id_iter, metadata in zip(all_songs["ids"], all_songs["metadatas"]):
                if not metadata.get("sections"):
                    song_data = get_song(song_id_iter)
                    if song_data:
                        un_profiled.append((song_id_iter, song_data["metadata"]["path"]))

            if not un_profiled:
                console.print("[yellow]No un-profiled songs found![/yellow]")
                return

            console.print(f"Found {len(un_profiled)} un-profiled songs")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing...", total=len(un_profiled))

                for idx, (sid, path) in enumerate(un_profiled):
                    progress.update(task, description=f"Analyzing {sid}...")
                    profile_audio(path)
                    progress.advance(task)

            console.print(f"[green]✓ Analyzed {len(un_profiled)} songs[/green]")

        else:
            console.print(f"[bold cyan]Analyzing song:[/bold cyan] {song_id}")

            # Get song path
            song_data = get_song(song_id)
            if not song_data:
                console.print(f"[red]✗ Song not found:[/red] {song_id}")
                sys.exit(1)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing...", total=None)
                profile_audio(song_data["metadata"]["path"])
                progress.update(task, description="✓ Complete")

            console.print(f"[green]✓ Analysis complete:[/green] {song_id}")

            # Show metadata summary
            updated = get_song(song_id)
            if updated and updated.get("metadata"):
                meta = updated["metadata"]
                console.print(f"[dim]BPM:[/dim] {meta.get('bpm', 'N/A')}")
                console.print(f"[dim]Key:[/dim] {meta.get('key', 'N/A')} ({meta.get('camelot', 'N/A')})")
                console.print(f"[dim]Sections:[/dim] {len(meta.get('sections', []))}")

    except AnalysisError as e:
        console.print(f"[red]✗ Analysis failed:[/red] {e}")
        sys.exit(1)


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

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching library...", total=None)

            matches = find_match(
                target_song_id=song_id,
                criteria=criteria,
                genre_filter=genre,
                semantic_query=semantic,
                max_results=max_results
            )

            progress.update(task, description="✓ Complete")

        if not matches:
            console.print("[yellow]No compatible matches found[/yellow]")
            return

        # Display results table
        table = Table(title=f"Top {len(matches)} Matches")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Song ID", style="green")
        table.add_column("Artist - Title", style="bold")
        table.add_column("Score", justify="right", style="magenta")
        table.add_column("Reasons", style="dim")

        for idx, match in enumerate(matches, 1):
            meta = match["metadata"]
            artist_title = f"{meta['artist']} - {meta['title']}"
            score = f"{match['compatibility_score']:.2f}"
            reasons = ", ".join(match["match_reasons"][:2])  # Show first 2 reasons

            table.add_row(
                str(idx),
                match["id"],
                artist_title,
                score,
                reasons
            )

        console.print(table)

    except CuratorError as e:
        console.print(f"[red]✗ Matching failed:[/red] {e}")
        sys.exit(1)


@main.command()
@click.argument('input_source_a')
@click.argument('input_source_b', required=False)
@click.option(
    '--type',
    'mashup_type',
    type=click.Choice([
        'classic', 'stem-swap', 'energy', 'adaptive',
        'theme', 'semantic', 'role-aware', 'convo'
    ]),
    help='Mashup type (if not specified, will auto-recommend)'
)
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
    input_source_a: str,
    input_source_b: str | None,
    mashup_type: str | None,
    output: str,
    output_format: str
) -> None:
    """Create mashup using automated workflow.

    INPUT_SOURCE_A: First song (URL or file path or song ID)

    INPUT_SOURCE_B: Second song (optional - will find match if not provided)
    """
    console.print(Panel.fit(
        "[bold cyan]Starting mashup workflow...[/bold cyan]",
        border_style="cyan"
    ))

    # Map CLI mashup type to enum value
    type_mapping = {
        'classic': 'CLASSIC',
        'stem-swap': 'STEM_SWAP',
        'energy': 'ENERGY_MATCHED',
        'adaptive': 'ADAPTIVE_HARMONY',
        'theme': 'THEME_FUSION',
        'semantic': 'SEMANTIC_ALIGNED',
        'role-aware': 'ROLE_AWARE',
        'convo': 'CONVERSATIONAL',
    }
    enum_type = type_mapping.get(mashup_type) if mashup_type else None

    try:
        console.print("\n[bold]Workflow Progress:[/bold]")

        # Run workflow with streaming
        final_state = run_mashup_workflow(
            input_source_a=input_source_a,
            input_source_b=input_source_b,
            mashup_type=enum_type,
            stream=True
        )

        # Success!
        console.print(f"\n[green]✓ Mashup created successfully![/green]")
        console.print(f"[bold]Output:[/bold] {final_state['mashup_output_path']}")

        # Show mashup details
        console.print(f"\n[dim]Type:[/dim] {final_state['approved_mashup_type']}")
        console.print(f"[dim]Song A:[/dim] {final_state['song_a_id']}")
        console.print(f"[dim]Song B:[/dim] {final_state['song_b_id']}")

    except WorkflowError as e:
        console.print(f"\n[red]✗ Mashup workflow failed:[/red] {e}")
        sys.exit(1)


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
    console.print(f"[bold cyan]Library (showing up to {limit} songs):[/bold cyan]\n")

    try:
        client = get_client()
        collection = client.get_collection()
        all_songs = collection.get(include=["metadatas"])

        if not all_songs["ids"]:
            console.print("[yellow]Library is empty. Use 'mixer ingest' to add songs.[/yellow]")
            return

        # Create table
        table = Table()
        table.add_column("#", style="cyan", width=4)
        table.add_column("Song ID", style="green")
        table.add_column("Artist - Title", style="bold")
        table.add_column("BPM", justify="right")
        table.add_column("Key", justify="center")
        table.add_column("Analyzed", justify="center")

        for idx, (song_id, metadata) in enumerate(zip(all_songs["ids"][:limit], all_songs["metadatas"][:limit]), 1):
            artist = metadata.get("artist", "Unknown")
            title = metadata.get("title", "Unknown")
            bpm = str(int(metadata["bpm"])) if metadata.get("bpm") else "N/A"
            key = metadata.get("camelot", "N/A")
            analyzed = "✓" if metadata.get("sections") else "✗"

            table.add_row(
                str(idx),
                song_id,
                f"{artist} - {title}",
                bpm,
                key,
                analyzed
            )

        console.print(table)

        total = len(all_songs["ids"])
        if total > limit:
            console.print(f"\n[dim]Showing {limit} of {total} songs[/dim]")

    except Exception as e:
        console.print(f"[red]✗ Error listing library:[/red] {e}")
        sys.exit(1)


@library.command('search')
@click.argument('query')
@click.pass_context
def library_search(ctx: click.Context, query: str) -> None:
    """Semantic search in library.

    QUERY: Search query (e.g., "upbeat country songs")
    """
    console.print(f"[bold cyan]Searching for:[/bold cyan] {query}\n")

    try:
        from mixer.memory import query_semantic

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Searching...", total=None)

            results = query_semantic(query_text=query, max_results=10)

            progress.update(task, description="✓ Complete")

        if not results:
            console.print("[yellow]No matching songs found[/yellow]")
            return

        # Display results
        table = Table(title=f"Search Results for '{query}'")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Song ID", style="green")
        table.add_column("Artist - Title", style="bold")
        table.add_column("Mood", style="dim")

        for idx, result in enumerate(results, 1):
            meta = result["metadata"]
            artist_title = f"{meta['artist']} - {meta['title']}"
            mood = meta.get("mood_summary", "N/A")

            table.add_row(
                str(idx),
                result["id"],
                artist_title,
                mood
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Search failed:[/red] {e}")
        sys.exit(1)


@library.command('stats')
@click.pass_context
def library_stats(ctx: click.Context) -> None:
    """Show library statistics."""
    console.print("[bold cyan]Library Statistics:[/bold cyan]\n")

    try:
        client = get_client()
        collection = client.get_collection()
        all_songs = collection.get(include=["metadatas"])

        if not all_songs["ids"]:
            console.print("[yellow]Library is empty[/yellow]")
            return

        # Calculate stats
        total = len(all_songs["ids"])
        analyzed = sum(1 for m in all_songs["metadatas"] if m.get("sections"))
        genres = {}
        sources = {"youtube": 0, "local_file": 0}

        for metadata in all_songs["metadatas"]:
            # Genre count
            genre = metadata.get("primary_genre", "Unknown")
            genres[genre] = genres.get(genre, 0) + 1

            # Source count
            source = metadata.get("source", "unknown")
            if source in sources:
                sources[source] += 1

        # Display stats
        console.print(f"[bold]Total Songs:[/bold] {total}")
        console.print(f"[bold]Analyzed:[/bold] {analyzed} ({analyzed/total*100:.0f}%)")
        console.print(f"[bold]Un-analyzed:[/bold] {total - analyzed}")
        console.print()
        console.print(f"[bold]Sources:[/bold]")
        console.print(f"  YouTube: {sources['youtube']}")
        console.print(f"  Local files: {sources['local_file']}")
        console.print()
        console.print(f"[bold]Top Genres:[/bold]")
        top_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:5]
        for genre, count in top_genres:
            console.print(f"  {genre}: {count}")

    except Exception as e:
        console.print(f"[red]✗ Error getting stats:[/red] {e}")
        sys.exit(1)


@main.command()
@click.argument('input_source')
@click.pass_context
def auto(ctx: click.Context, input_source: str) -> None:
    """Fully automated workflow: ingest → analyze → match → mashup.

    INPUT_SOURCE: YouTube URL or path to audio file
    """
    console.print(Panel.fit(
        "[bold cyan]Starting fully automated workflow...[/bold cyan]\n"
        "[dim]This will ingest, analyze, find a match, and create a mashup[/dim]",
        border_style="cyan"
    ))

    try:
        # Run workflow without song B (will auto-select match)
        final_state = run_mashup_workflow(
            input_source_a=input_source,
            input_source_b=None,
            mashup_type=None,  # Auto-recommend
            stream=True
        )

        console.print(f"\n[green]✓ Automated workflow complete![/green]")
        console.print(f"[bold]Mashup:[/bold] {final_state['mashup_output_path']}")

    except WorkflowError as e:
        console.print(f"\n[red]✗ Automated workflow failed:[/red] {e}")
        sys.exit(1)


@main.command()
@click.pass_context
def interactive(ctx: click.Context) -> None:
    """Interactive mode for guided mashup creation."""
    console.print(Panel.fit(
        "[bold cyan]🎵 Welcome to The Mixer![/bold cyan]\n"
        "[dim]Interactive mode - I'll guide you through creating a mashup[/dim]",
        border_style="cyan"
    ))

    try:
        # Step 1: Get input song
        console.print("\n[bold]Step 1: Input Song[/bold]")
        input_source = Prompt.ask("Enter a song URL or file path")

        # Step 2: Ask if they have a second song
        console.print("\n[bold]Step 2: Second Song[/bold]")
        has_song_b = Confirm.ask("Do you have a specific song to pair with?", default=False)

        input_source_b = None
        if has_song_b:
            input_source_b = Prompt.ask("Enter second song URL or file path")

        # Step 3: Ask about mashup type
        console.print("\n[bold]Step 3: Mashup Type[/bold]")
        auto_type = Confirm.ask("Auto-recommend mashup type?", default=True)

        mashup_type = None
        if not auto_type:
            console.print("\nAvailable mashup types:")
            console.print("  1. Classic (vocals + instrumental)")
            console.print("  2. Energy Matched (align by energy)")
            console.print("  3. Adaptive Harmony (auto pitch-shift)")
            console.print("  4. Role-Aware (lead/harmony vocals)")
            console.print("  5. Conversational (call and response)")

            type_choice = Prompt.ask(
                "Select type",
                choices=["1", "2", "3", "4", "5"],
                default="1"
            )

            type_map = {
                "1": "CLASSIC",
                "2": "ENERGY_MATCHED",
                "3": "ADAPTIVE_HARMONY",
                "4": "ROLE_AWARE",
                "5": "CONVERSATIONAL",
            }
            mashup_type = type_map[type_choice]

        # Step 4: Run workflow
        console.print("\n[bold]Step 4: Creating Mashup[/bold]")

        final_state = run_mashup_workflow(
            input_source_a=input_source,
            input_source_b=input_source_b,
            mashup_type=mashup_type,
            stream=True
        )

        # Success!
        console.print(Panel.fit(
            f"[bold green]✓ Mashup Complete![/bold green]\n\n"
            f"[bold]Output:[/bold] {final_state['mashup_output_path']}\n"
            f"[dim]Type:[/dim] {final_state['approved_mashup_type']}\n"
            f"[dim]Songs:[/dim] {final_state['song_a_id']} + {final_state['song_b_id']}",
            border_style="green"
        ))

    except WorkflowError as e:
        console.print(f"\n[red]✗ Workflow failed:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(0)


if __name__ == '__main__':
    main()
