"""Performance benchmarking script for The Mixer.

Usage:
    python scripts/benchmark.py --song-a path/to/song_a.mp3 --song-b path/to/song_b.mp3

This script measures performance of each workflow stage:
- Ingestion
- Analysis (Whisper + Demucs + section detection)
- Curation (database queries)
- Engineering (mashup creation)

"""

import time
import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mixer.agents import ingest_song, profile_audio, find_match, create_classic_mashup
from mixer.memory import get_song, reset_client

console = Console()


def benchmark_ingestion(source: str) -> dict:
    """Benchmark ingestion stage."""
    console.print(f"\n[bold cyan]Benchmarking Ingestion:[/bold cyan] {source}")

    start = time.time()
    result = ingest_song(source)
    duration = time.time() - start

    console.print(f"  Duration: {duration:.2f}s")
    console.print(f"  Cached: {result['cached']}")

    return {
        "stage": "Ingestion",
        "duration": duration,
        "cached": result["cached"],
        "song_id": result["id"]
    }


def benchmark_analysis(song_path: str, song_id: str) -> dict:
    """Benchmark analysis stage."""
    console.print(f"\n[bold cyan]Benchmarking Analysis:[/bold cyan] {song_id}")

    # Check if already analyzed
    song_data = get_song(song_id)
    if song_data and song_data["metadata"].get("sections"):
        console.print("  [yellow]Already analyzed, skipping[/yellow]")
        return {
            "stage": "Analysis",
            "duration": 0,
            "skipped": True,
            "sections": len(song_data["metadata"]["sections"])
        }

    start = time.time()
    profile_audio(song_path)
    duration = time.time() - start

    # Get updated metadata
    updated = get_song(song_id)
    sections = len(updated["metadata"].get("sections", []))

    console.print(f"  Duration: {duration:.2f}s")
    console.print(f"  Sections found: {sections}")

    return {
        "stage": "Analysis",
        "duration": duration,
        "skipped": False,
        "sections": sections
    }


def benchmark_curation(song_id: str) -> dict:
    """Benchmark curation stage."""
    console.print(f"\n[bold cyan]Benchmarking Curation:[/bold cyan] {song_id}")

    start = time.time()
    matches = find_match(song_id, criteria="hybrid", max_results=5)
    duration = time.time() - start

    console.print(f"  Duration: {duration:.2f}s")
    console.print(f"  Matches found: {len(matches)}")

    return {
        "stage": "Curation",
        "duration": duration,
        "matches_found": len(matches)
    }


def benchmark_engineering(song_a_id: str, song_b_id: str) -> dict:
    """Benchmark engineering stage."""
    console.print(f"\n[bold cyan]Benchmarking Engineering:[/bold cyan] {song_a_id} + {song_b_id}")

    start = time.time()
    output_path = create_classic_mashup(
        song_a_id=song_a_id,
        song_b_id=song_b_id,
        quality="draft",  # Use draft for faster benchmarking
        output_format="mp3"
    )
    duration = time.time() - start

    console.print(f"  Duration: {duration:.2f}s")
    console.print(f"  Output: {output_path}")

    return {
        "stage": "Engineering",
        "duration": duration,
        "output_path": output_path
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark The Mixer performance")
    parser.add_argument("--song-a", required=True, help="Path to first test song")
    parser.add_argument("--song-b", required=True, help="Path to second test song")
    parser.add_argument("--skip-ingestion", action="store_true", help="Skip ingestion (assume songs already ingested)")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip analysis (assume songs already analyzed)")
    parser.add_argument("--skip-curation", action="store_true", help="Skip curation benchmark")
    parser.add_argument("--skip-engineering", action="store_true", help="Skip engineering benchmark")

    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold cyan]The Mixer - Performance Benchmark[/bold cyan]\n"
        "[dim]Measuring workflow stage performance[/dim]",
        border_style="cyan"
    ))

    results = []
    song_a_id = None
    song_b_id = None

    try:
        # Benchmark Ingestion
        if not args.skip_ingestion:
            result_a = benchmark_ingestion(args.song_a)
            results.append(result_a)
            song_a_id = result_a["song_id"]

            result_b = benchmark_ingestion(args.song_b)
            results.append(result_b)
            song_b_id = result_b["song_id"]
        else:
            console.print("\n[yellow]Skipping ingestion[/yellow]")
            # Try to infer song IDs from paths
            # This is a simplification - real implementation would need ID lookup

        # Benchmark Analysis
        if not args.skip_analysis and song_a_id and song_b_id:
            result_a_analysis = benchmark_analysis(args.song_a, song_a_id)
            results.append(result_a_analysis)

            result_b_analysis = benchmark_analysis(args.song_b, song_b_id)
            results.append(result_b_analysis)
        else:
            console.print("\n[yellow]Skipping analysis[/yellow]")

        # Benchmark Curation
        if not args.skip_curation and song_a_id:
            result_curation = benchmark_curation(song_a_id)
            results.append(result_curation)
        else:
            console.print("\n[yellow]Skipping curation[/yellow]")

        # Benchmark Engineering
        if not args.skip_engineering and song_a_id and song_b_id:
            result_engineering = benchmark_engineering(song_a_id, song_b_id)
            results.append(result_engineering)
        else:
            console.print("\n[yellow]Skipping engineering[/yellow]")

        # Display results table
        console.print("\n[bold green]Benchmark Results:[/bold green]\n")

        table = Table(title="Performance Summary")
        table.add_column("Stage", style="cyan")
        table.add_column("Duration (s)", justify="right", style="magenta")
        table.add_column("Notes", style="dim")

        for result in results:
            duration = f"{result['duration']:.2f}"
            notes = []

            if result.get("cached"):
                notes.append("Cached")
            if result.get("skipped"):
                notes.append("Skipped (already done)")
            if result.get("sections"):
                notes.append(f"{result['sections']} sections")
            if result.get("matches_found"):
                notes.append(f"{result['matches_found']} matches")

            table.add_row(
                result["stage"],
                duration,
                ", ".join(notes) if notes else ""
            )

        # Add total
        total_duration = sum(r["duration"] for r in results)
        table.add_section()
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{total_duration:.2f}[/bold]",
            ""
        )

        console.print(table)

        # Performance insights
        console.print("\n[bold]Performance Insights:[/bold]")
        console.print(f"  - Average per-song ingestion: {sum(r['duration'] for r in results if r['stage'] == 'Ingestion') / 2:.2f}s")
        analysis_results = [r for r in results if r['stage'] == 'Analysis' and not r.get('skipped')]
        if analysis_results:
            console.print(f"  - Average per-song analysis: {sum(r['duration'] for r in analysis_results) / len(analysis_results):.2f}s")
        console.print(f"  - Total workflow time: {total_duration:.2f}s ({total_duration/60:.1f} minutes)")

    except Exception as e:
        console.print(f"\n[red]Benchmark failed:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    from rich.panel import Panel
    main()
