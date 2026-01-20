"""Performance benchmarking for Crossfade Club pipeline.

Measures performance of each pipeline stage and overall throughput.

Usage:
  python scripts/benchmark_pipeline.py --audio mashups/test.wav --song-id test_song
  python scripts/benchmark_pipeline.py --audio mashups/test.wav --song-id test_song --iterations 3
"""

import argparse
import time
import statistics
from pathlib import Path
from typing import List, Dict

from batch.runner import BatchRunner


class PipelineBenchmark:
    """Benchmark runner for pipeline performance."""

    def __init__(self, audio_path: str, song_id: str):
        self.audio_path = audio_path
        self.song_id = song_id
        self.results: List[Dict[str, float]] = []

    def run_benchmark(self, iterations: int = 1, platforms: List[str] = None) -> Dict[str, any]:
        """Run benchmark iterations.

        Args:
            iterations: Number of iterations to run
            platforms: Platforms to test (None = all)

        Returns:
            Dict with benchmark results
        """
        print(f"\n{'='*70}")
        print(f"Crossfade Club - Pipeline Benchmark")
        print(f"{'='*70}")
        print(f"Audio: {self.audio_path}")
        print(f"Song ID: {self.song_id}")
        print(f"Iterations: {iterations}")
        print(f"Platforms: {platforms or 'all'}")
        print(f"{'='*70}\n")

        for i in range(iterations):
            print(f"Iteration {i+1}/{iterations}")
            print(f"{'─'*70}")

            runner = BatchRunner(
                audio_path=self.audio_path,
                song_id=f"{self.song_id}_bench_{i}",
                output_dir=f"./outputs/benchmark_{i}"
            )

            start_time = time.time()

            try:
                outputs = runner.run(
                    platforms=platforms,
                    with_captions=True,
                    with_thumbnail=True,
                    skip_studio=True  # Skip for faster benchmarking
                )

                total_time = time.time() - start_time

                # Record results
                iteration_result = {
                    "total_time": total_time,
                    **runner.stage_times
                }
                self.results.append(iteration_result)

                print(f"Iteration {i+1} completed: {total_time:.2f}s\n")

            except Exception as e:
                print(f"Iteration {i+1} failed: {e}\n")
                continue

        # Compute statistics
        return self._compute_statistics()

    def _compute_statistics(self) -> Dict[str, any]:
        """Compute statistics from benchmark results.

        Returns:
            Dict with mean, median, min, max for each stage
        """
        if not self.results:
            return {}

        stats = {}

        # Get all stage names
        stages = set()
        for result in self.results:
            stages.update(result.keys())

        # Compute stats for each stage
        for stage in stages:
            values = [r[stage] for r in self.results if stage in r]

            if values:
                stats[stage] = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0.0
                }

        return stats

    def print_results(self, stats: Dict[str, any]):
        """Print benchmark results.

        Args:
            stats: Statistics dict from _compute_statistics()
        """
        print(f"\n{'='*70}")
        print(f"Benchmark Results")
        print(f"{'='*70}\n")

        print(f"Iterations: {len(self.results)}")
        print(f"\nStage Performance (seconds):")
        print(f"{'─'*70}")
        print(f"{'Stage':<20} {'Mean':<10} {'Median':<10} {'Min':<10} {'Max':<10}")
        print(f"{'─'*70}")

        # Sort by mean time (descending)
        sorted_stages = sorted(
            stats.items(),
            key=lambda x: x[1]["mean"],
            reverse=True
        )

        for stage, values in sorted_stages:
            print(f"{stage:<20} {values['mean']:>9.2f} {values['median']:>9.2f} "
                  f"{values['min']:>9.2f} {values['max']:>9.2f}")

        print(f"{'─'*70}")

        # Throughput calculation
        if "total_time" in stats:
            total_mean = stats["total_time"]["mean"]
            throughput = 60.0 / total_mean  # Videos per minute

            print(f"\nThroughput:")
            print(f"  Mean time per video: {total_mean:.2f}s")
            print(f"  Videos per minute: {throughput:.2f}")

        # Bottleneck analysis
        print(f"\nBottleneck Analysis:")
        if len(sorted_stages) > 1:
            slowest_stage, slowest_stats = sorted_stages[0]
            total_time = stats.get("total_time", {}).get("mean", 0)

            if total_time > 0:
                percentage = (slowest_stats["mean"] / total_time) * 100
                print(f"  Slowest stage: {slowest_stage} ({percentage:.1f}% of total time)")

        print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Benchmark Crossfade Club pipeline")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--song-id", required=True, help="Song ID")
    parser.add_argument("--iterations", type=int, default=1, help="Number of iterations (default: 1)")
    parser.add_argument("--platforms", nargs="+",
                       choices=["tiktok", "reels", "shorts", "youtube"],
                       help="Platforms to benchmark (default: all)")

    args = parser.parse_args()

    # Validate audio exists
    if not Path(args.audio).exists():
        print(f"✗ Error: Audio file not found: {args.audio}")
        return

    # Run benchmark
    benchmark = PipelineBenchmark(
        audio_path=args.audio,
        song_id=args.song_id
    )

    stats = benchmark.run_benchmark(
        iterations=args.iterations,
        platforms=args.platforms
    )

    benchmark.print_results(stats)


if __name__ == "__main__":
    main()
