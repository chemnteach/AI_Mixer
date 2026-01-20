"""Workflow state definitions for LangGraph orchestration."""

from typing import TypedDict, Optional, List, Literal
from enum import Enum
from mixer.types import SongMetadata, MatchResult, MashupRecommendation


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    INGESTING = "ingesting"
    ANALYZING = "analyzing"
    CURATING = "curating"
    AWAITING_APPROVAL = "awaiting_approval"
    ENGINEERING = "engineering"
    COMPLETED = "completed"
    FAILED = "failed"


class MashupState(TypedDict, total=False):
    """State for mashup creation workflow.

    This state flows through the LangGraph workflow and accumulates
    data from each agent node.
    """
    # Input parameters
    input_source_a: str  # URL or file path for song A
    input_source_b: Optional[str]  # URL or file path for song B (if provided)
    mashup_type: Optional[str]  # User-specified mashup type (or None for auto-recommend)

    # Workflow control
    status: str  # WorkflowStatus value
    current_step: str  # Current node name
    error: Optional[str]  # Error message if failed
    retry_count: int  # Number of retries attempted

    # Song A data (ingested and analyzed)
    song_a_id: Optional[str]  # Sanitized ID from ingestion
    song_a_path: Optional[str]  # Cached file path
    song_a_metadata: Optional[SongMetadata]  # Full metadata from analyst
    song_a_cached: bool  # Whether song A was already in library

    # Song B data (if provided, or selected by curator)
    song_b_id: Optional[str]
    song_b_path: Optional[str]
    song_b_metadata: Optional[SongMetadata]
    song_b_cached: bool

    # Curation results (if song B not provided)
    match_candidates: Optional[List[MatchResult]]  # Top matches from curator
    selected_match: Optional[MatchResult]  # User-selected match

    # Mashup recommendation
    recommended_mashup: Optional[MashupRecommendation]  # From curator
    approved_mashup_type: Optional[str]  # After user approval

    # Engineering output
    mashup_output_path: Optional[str]  # Final mashup file path

    # Progress tracking
    progress_messages: List[str]  # Human-readable progress updates
