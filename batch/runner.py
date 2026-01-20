"""Batch runner for end-to-end video generation pipeline."""

import time
from pathlib import Path
from typing import Optional, List, Dict, Literal
from enum import Enum

from batch.errors import PipelineError, StageError


class PipelineStage(Enum):
    """Pipeline stages."""
    DIRECTOR = "director"
    STUDIO = "studio"
    ENCODER = "encoder"
    COMPLETE = "complete"


class BatchRunner:
    """Orchestrates complete pipeline from audio to platform videos.

    Pipeline:
      1. Director: audio + metadata → timeline.json
      2. Studio: timeline.json → raw video (Blender)
      3. Encoder: raw video + audio → platform variants (FFmpeg)
    """

    def __init__(
        self,
        audio_path: str,
        song_id: str,
        theme: str = "sponsor_neon",
        mode: Literal["mashup", "single", "event"] = "mashup",
        output_dir: str = "./outputs"
    ):
        """Initialize batch runner.

        Args:
            audio_path: Path to audio file
            song_id: Song ID in ChromaDB
            theme: Visual theme name
            mode: Output mode (mashup, single, event)
            output_dir: Base output directory
        """
        self.audio_path = audio_path
        self.song_id = song_id
        self.theme = theme
        self.mode = mode
        self.output_dir = Path(output_dir)

        # Paths for intermediate outputs
        self.timeline_path: Optional[Path] = None
        self.raw_video_path: Optional[Path] = None
        self.platform_videos: Dict[str, Path] = {}
        self.thumbnail_path: Optional[Path] = None

        # Performance metrics
        self.stage_times: Dict[str, float] = {}
        self.total_time: float = 0.0

    def run(
        self,
        platforms: Optional[List[str]] = None,
        with_captions: bool = True,
        with_thumbnail: bool = True,
        skip_studio: bool = False
    ) -> Dict[str, Path]:
        """Run complete pipeline.

        Args:
            platforms: List of platforms to create (None = all)
            with_captions: Generate and burn captions
            with_thumbnail: Generate thumbnail
            skip_studio: Skip Blender rendering (for testing, requires existing raw video)

        Returns:
            Dict mapping output type to path

        Raises:
            PipelineError: If pipeline fails
        """
        start_time = time.time()

        try:
            print(f"\n{'='*70}")
            print(f"Crossfade Club - Batch Pipeline")
            print(f"{'='*70}")
            print(f"Audio: {self.audio_path}")
            print(f"Song ID: {self.song_id}")
            print(f"Theme: {self.theme}")
            print(f"Mode: {self.mode}")
            print(f"Platforms: {platforms or 'all'}")
            print(f"{'='*70}\n")

            # Stage 1: Director
            self._run_director()

            # Stage 2: Studio (unless skipped)
            if not skip_studio:
                self._run_studio()
            else:
                print("⚠ Skipping Studio stage (using existing raw video)\n")
                # Assume raw video exists
                self.raw_video_path = self.output_dir / "blender_temp" / f"{self.song_id}.mp4"

            # Stage 3: Encoder
            self._run_encoder(platforms, with_captions, with_thumbnail)

            self.total_time = time.time() - start_time

            # Print summary
            self._print_summary()

            return self._get_outputs()

        except Exception as e:
            self.total_time = time.time() - start_time
            raise PipelineError(f"Pipeline failed after {self.total_time:.1f}s: {e}") from e

    def _run_director(self):
        """Run Director stage: generate timeline.json."""
        print(f"{'─'*70}")
        print(f"Stage 1: Director (Timeline Generation)")
        print(f"{'─'*70}")

        stage_start = time.time()

        try:
            from director.timeline import generate_timeline

            # Output path
            self.timeline_path = self.output_dir / "timeline" / f"{self.song_id}.json"

            # Generate timeline
            timeline = generate_timeline(
                audio_path=self.audio_path,
                song_id=self.song_id,
                theme_name=self.theme,
                mode=self.mode,
                format_type="short",  # Default to short-form
                output_path=str(self.timeline_path)
            )

            stage_time = time.time() - stage_start
            self.stage_times["director"] = stage_time

            print(f"✓ Timeline generated: {self.timeline_path}")
            print(f"  Duration: {timeline['meta']['duration_sec']:.1f}s")
            print(f"  Events: {len(timeline['events'])}")
            print(f"  Stage time: {stage_time:.1f}s\n")

        except Exception as e:
            raise StageError("director", str(e), e) from e

    def _run_studio(self):
        """Run Studio stage: render video with Blender."""
        print(f"{'─'*70}")
        print(f"Stage 2: Studio (Blender Rendering)")
        print(f"{'─'*70}")

        stage_start = time.time()

        try:
            from studio.renderer import render_video

            # Output path
            self.raw_video_path = self.output_dir / "blender_temp" / f"{self.song_id}.mp4"

            # Render video
            render_video(
                timeline_path=str(self.timeline_path),
                output_path=str(self.raw_video_path),
                format_type="short",
                placeholder_mode=True  # Use placeholder for now (no assets required)
            )

            stage_time = time.time() - stage_start
            self.stage_times["studio"] = stage_time

            print(f"✓ Video rendered: {self.raw_video_path}")
            print(f"  Size: {self.raw_video_path.stat().st_size / (1024*1024):.2f} MB")
            print(f"  Stage time: {stage_time:.1f}s\n")

        except Exception as e:
            raise StageError("studio", str(e), e) from e

    def _run_encoder(
        self,
        platforms: Optional[List[str]],
        with_captions: bool,
        with_thumbnail: bool
    ):
        """Run Encoder stage: create platform variants."""
        print(f"{'─'*70}")
        print(f"Stage 3: Encoder (Platform Variants)")
        print(f"{'─'*70}")

        stage_start = time.time()

        try:
            from encoder.platform import create_all_variants
            from encoder.captions import generate_vtt_from_timeline
            from encoder.thumbnail import generate_thumbnail_from_timeline

            # Generate VTT captions if requested
            vtt_file = None
            if with_captions:
                vtt_path = self.output_dir / "renders" / f"{self.song_id}.vtt"
                vtt_file = str(generate_vtt_from_timeline(
                    timeline_path=str(self.timeline_path),
                    output_path=str(vtt_path)
                ))

            # Create platform variants
            render_dir = self.output_dir / "renders"

            self.platform_videos = create_all_variants(
                input_video=str(self.raw_video_path),
                input_audio=self.audio_path,
                output_dir=str(render_dir),
                base_name=self.song_id,
                vtt_file=vtt_file,
                platforms=platforms
            )

            # Generate thumbnail if requested
            if with_thumbnail and self.platform_videos:
                # Use first platform variant for thumbnail
                first_platform = list(self.platform_videos.keys())[0]
                thumb_path = render_dir / f"{self.song_id}_thumb.jpg"

                self.thumbnail_path = generate_thumbnail_from_timeline(
                    video_path=str(self.platform_videos[first_platform]),
                    timeline_path=str(self.timeline_path),
                    output_path=str(thumb_path)
                )

            stage_time = time.time() - stage_start
            self.stage_times["encoder"] = stage_time

            print(f"✓ Platform variants created: {len(self.platform_videos)}")
            for platform, path in self.platform_videos.items():
                size_mb = path.stat().st_size / (1024*1024)
                print(f"  • {platform}: {size_mb:.2f} MB")

            if self.thumbnail_path:
                print(f"✓ Thumbnail: {self.thumbnail_path}")

            print(f"  Stage time: {stage_time:.1f}s\n")

        except Exception as e:
            raise StageError("encoder", str(e), e) from e

    def _print_summary(self):
        """Print pipeline execution summary."""
        print(f"{'='*70}")
        print(f"Pipeline Complete")
        print(f"{'='*70}")

        print(f"\nOutputs:")
        print(f"  Timeline: {self.timeline_path}")
        print(f"  Raw video: {self.raw_video_path}")
        for platform, path in self.platform_videos.items():
            print(f"  {platform.capitalize()}: {path}")
        if self.thumbnail_path:
            print(f"  Thumbnail: {self.thumbnail_path}")

        print(f"\nPerformance:")
        for stage, duration in self.stage_times.items():
            print(f"  {stage.capitalize()}: {duration:.1f}s")
        print(f"  Total: {self.total_time:.1f}s")

        print(f"\n{'='*70}\n")

    def _get_outputs(self) -> Dict[str, Path]:
        """Get all output paths.

        Returns:
            Dict mapping output type to path
        """
        outputs = {
            "timeline": self.timeline_path,
            "raw_video": self.raw_video_path,
        }

        for platform, path in self.platform_videos.items():
            outputs[f"video_{platform}"] = path

        if self.thumbnail_path:
            outputs["thumbnail"] = self.thumbnail_path

        return outputs
