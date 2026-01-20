"""Batch Module - End-to-End Orchestration for Crossfade Club.

Orchestrates the complete pipeline:
  Mixer → Director → Studio → Encoder → Output
"""

from batch.runner import BatchRunner, PipelineStage
from batch.errors import BatchError, PipelineError

__all__ = [
    "BatchRunner",
    "PipelineStage",
    "BatchError",
    "PipelineError",
]
