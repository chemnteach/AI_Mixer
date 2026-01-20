"""LangGraph workflow nodes - agent wrappers for the mashup pipeline."""

import logging
from typing import Dict, Any
from mixer.workflow.state import MashupState, WorkflowStatus
from mixer.agents import (
    ingest_song,
    profile_audio,
    find_match,
    recommend_mashup_type,
    calculate_compatibility_score,
    create_classic_mashup,
    create_stem_swap_mashup,
    create_energy_matched_mashup,
    create_adaptive_harmony_mashup,
    create_theme_fusion_mashup,
    create_semantic_aligned_mashup,
    create_role_aware_mashup,
    create_conversational_mashup,
    IngestionError,
    AnalysisError,
    CuratorError,
    EngineerError,
)
from mixer.memory import get_song

logger = logging.getLogger(__name__)


def ingest_song_a_node(state: MashupState) -> Dict[str, Any]:
    """Ingest song A from URL or file path.

    Updates state with:
    - song_a_id
    - song_a_path
    - song_a_cached
    - status, progress_messages
    """
    logger.info(f"=== Ingesting Song A: {state['input_source_a']} ===")

    try:
        state["status"] = WorkflowStatus.INGESTING.value
        state["current_step"] = "ingest_song_a"
        state["progress_messages"].append(f"Ingesting song A from {state['input_source_a']}...")

        result = ingest_song(state["input_source_a"])

        state["song_a_id"] = result["id"]
        state["song_a_path"] = result["path"]
        state["song_a_cached"] = result["cached"]

        if result["cached"]:
            state["progress_messages"].append(f"✓ Song A already in library: {result['id']}")
        else:
            state["progress_messages"].append(f"✓ Song A ingested: {result['id']}")

        return state

    except IngestionError as e:
        logger.error(f"Ingestion failed for song A: {e}")
        state["status"] = WorkflowStatus.FAILED.value
        state["error"] = f"Failed to ingest song A: {e}"
        return state


def analyze_song_a_node(state: MashupState) -> Dict[str, Any]:
    """Analyze song A to extract section-level metadata.

    Updates state with:
    - song_a_metadata
    - status, progress_messages
    """
    logger.info(f"=== Analyzing Song A: {state['song_a_id']} ===")

    try:
        state["status"] = WorkflowStatus.ANALYZING.value
        state["current_step"] = "analyze_song_a"
        state["progress_messages"].append(f"Analyzing song A: {state['song_a_id']}...")

        # Check if already analyzed (cached song with metadata)
        existing = get_song(state["song_a_id"])
        if existing and existing.get("metadata") and existing["metadata"].get("sections"):
            logger.info(f"Song A already analyzed, skipping analysis")
            state["song_a_metadata"] = existing["metadata"]
            state["progress_messages"].append(f"✓ Song A already analyzed (using cached metadata)")
            return state

        # Run analysis
        profile_audio(state["song_a_path"])

        # Fetch updated metadata
        updated = get_song(state["song_a_id"])
        if not updated or not updated.get("metadata"):
            raise AnalysisError(f"Analysis completed but metadata not found for {state['song_a_id']}")

        state["song_a_metadata"] = updated["metadata"]
        state["progress_messages"].append(f"✓ Song A analyzed: {len(state['song_a_metadata'].get('sections', []))} sections found")

        return state

    except AnalysisError as e:
        logger.error(f"Analysis failed for song A: {e}")
        state["status"] = WorkflowStatus.FAILED.value
        state["error"] = f"Failed to analyze song A: {e}"
        return state


def ingest_song_b_node(state: MashupState) -> Dict[str, Any]:
    """Ingest song B from URL or file path (if provided).

    Updates state with:
    - song_b_id
    - song_b_path
    - song_b_cached
    - status, progress_messages
    """
    # If no song B provided, skip this node
    if not state.get("input_source_b"):
        logger.info("No song B provided, will use curator to find match")
        state["progress_messages"].append("No song B provided - curator will find compatible match")
        return state

    logger.info(f"=== Ingesting Song B: {state['input_source_b']} ===")

    try:
        state["status"] = WorkflowStatus.INGESTING.value
        state["current_step"] = "ingest_song_b"
        state["progress_messages"].append(f"Ingesting song B from {state['input_source_b']}...")

        result = ingest_song(state["input_source_b"])

        state["song_b_id"] = result["id"]
        state["song_b_path"] = result["path"]
        state["song_b_cached"] = result["cached"]

        if result["cached"]:
            state["progress_messages"].append(f"✓ Song B already in library: {result['id']}")
        else:
            state["progress_messages"].append(f"✓ Song B ingested: {result['id']}")

        return state

    except IngestionError as e:
        logger.error(f"Ingestion failed for song B: {e}")
        state["status"] = WorkflowStatus.FAILED.value
        state["error"] = f"Failed to ingest song B: {e}"
        return state


def analyze_song_b_node(state: MashupState) -> Dict[str, Any]:
    """Analyze song B to extract section-level metadata (if provided).

    Updates state with:
    - song_b_metadata
    - status, progress_messages
    """
    # If no song B, skip
    if not state.get("song_b_id"):
        return state

    logger.info(f"=== Analyzing Song B: {state['song_b_id']} ===")

    try:
        state["status"] = WorkflowStatus.ANALYZING.value
        state["current_step"] = "analyze_song_b"
        state["progress_messages"].append(f"Analyzing song B: {state['song_b_id']}...")

        # Check if already analyzed
        existing = get_song(state["song_b_id"])
        if existing and existing.get("metadata") and existing["metadata"].get("sections"):
            logger.info(f"Song B already analyzed, skipping analysis")
            state["song_b_metadata"] = existing["metadata"]
            state["progress_messages"].append(f"✓ Song B already analyzed (using cached metadata)")
            return state

        # Run analysis
        profile_audio(state["song_b_path"])

        # Fetch updated metadata
        updated = get_song(state["song_b_id"])
        if not updated or not updated.get("metadata"):
            raise AnalysisError(f"Analysis completed but metadata not found for {state['song_b_id']}")

        state["song_b_metadata"] = updated["metadata"]
        state["progress_messages"].append(f"✓ Song B analyzed: {len(state['song_b_metadata'].get('sections', []))} sections found")

        return state

    except AnalysisError as e:
        logger.error(f"Analysis failed for song B: {e}")
        state["status"] = WorkflowStatus.FAILED.value
        state["error"] = f"Failed to analyze song B: {e}"
        return state


def find_matches_node(state: MashupState) -> Dict[str, Any]:
    """Find compatible matches for song A using curator (if song B not provided).

    Updates state with:
    - match_candidates
    - status, progress_messages
    """
    # If song B provided, skip curation
    if state.get("song_b_id"):
        logger.info("Song B provided, skipping curation")
        return state

    logger.info(f"=== Finding Matches for Song A: {state['song_a_id']} ===")

    try:
        state["status"] = WorkflowStatus.CURATING.value
        state["current_step"] = "find_matches"
        state["progress_messages"].append(f"Finding compatible matches for {state['song_a_id']}...")

        # Use hybrid matching (recommended)
        matches = find_match(
            target_song_id=state["song_a_id"],
            criteria="hybrid",
            max_results=5
        )

        state["match_candidates"] = matches
        state["progress_messages"].append(f"✓ Found {len(matches)} compatible matches")

        if len(matches) > 0:
            # Log top match
            top = matches[0]
            state["progress_messages"].append(
                f"  Top match: {top['metadata']['artist']} - {top['metadata']['title']} (score: {top['compatibility_score']:.2f})"
            )

        return state

    except CuratorError as e:
        logger.error(f"Curation failed: {e}")
        state["status"] = WorkflowStatus.FAILED.value
        state["error"] = f"Failed to find matches: {e}"
        return state


def await_user_selection_node(state: MashupState) -> Dict[str, Any]:
    """Wait for user to select a match from candidates.

    This is a human-in-the-loop node. The workflow will pause here
    and wait for external input to set:
    - selected_match
    - song_b_id
    - song_b_metadata

    Updates state with:
    - status (AWAITING_APPROVAL)
    - progress_messages
    """
    # If song B already selected, skip
    if state.get("song_b_id"):
        return state

    logger.info("=== Awaiting User Match Selection ===")

    state["status"] = WorkflowStatus.AWAITING_APPROVAL.value
    state["current_step"] = "await_user_selection"
    state["progress_messages"].append("⏸ Awaiting user selection of match...")

    # In a real implementation, this would trigger a UI prompt or CLI input
    # For now, we'll auto-select the top match as a fallback
    if state.get("match_candidates") and len(state["match_candidates"]) > 0:
        top_match = state["match_candidates"][0]
        state["selected_match"] = top_match
        state["song_b_id"] = top_match["id"]
        state["song_b_metadata"] = top_match["metadata"]
        state["progress_messages"].append(f"✓ Auto-selected top match: {top_match['id']}")
        logger.info(f"Auto-selected top match: {top_match['id']}")

    return state


def recommend_mashup_type_node(state: MashupState) -> Dict[str, Any]:
    """Recommend optimal mashup type based on song characteristics.

    Updates state with:
    - recommended_mashup
    - status, progress_messages
    """
    logger.info("=== Recommending Mashup Type ===")

    try:
        state["status"] = WorkflowStatus.CURATING.value
        state["current_step"] = "recommend_mashup_type"
        state["progress_messages"].append("Analyzing songs to recommend mashup type...")

        if not state.get("song_a_metadata") or not state.get("song_b_metadata"):
            raise CuratorError("Cannot recommend mashup type - missing song metadata")

        recommendation = recommend_mashup_type(
            state["song_a_metadata"],
            state["song_b_metadata"]
        )

        state["recommended_mashup"] = recommendation
        state["progress_messages"].append(
            f"✓ Recommended: {recommendation['mashup_type']} "
            f"(confidence: {recommendation['confidence']:.0%})"
        )
        state["progress_messages"].append(f"  Reason: {recommendation['reasoning']}")

        return state

    except CuratorError as e:
        logger.error(f"Mashup type recommendation failed: {e}")
        state["status"] = WorkflowStatus.FAILED.value
        state["error"] = f"Failed to recommend mashup type: {e}"
        return state


def await_mashup_approval_node(state: MashupState) -> Dict[str, Any]:
    """Wait for user to approve or modify mashup type.

    This is a human-in-the-loop node. The workflow will pause here
    and wait for external input to set:
    - approved_mashup_type

    Updates state with:
    - status (AWAITING_APPROVAL)
    - progress_messages
    """
    logger.info("=== Awaiting Mashup Type Approval ===")

    state["status"] = WorkflowStatus.AWAITING_APPROVAL.value
    state["current_step"] = "await_mashup_approval"
    state["progress_messages"].append("⏸ Awaiting user approval of mashup type...")

    # Auto-approve recommended type if user didn't specify
    if not state.get("mashup_type") and state.get("recommended_mashup"):
        state["approved_mashup_type"] = state["recommended_mashup"]["mashup_type"]
        state["progress_messages"].append(
            f"✓ Auto-approved recommended type: {state['approved_mashup_type']}"
        )
        logger.info(f"Auto-approved: {state['approved_mashup_type']}")
    elif state.get("mashup_type"):
        # User specified mashup type upfront
        state["approved_mashup_type"] = state["mashup_type"]
        state["progress_messages"].append(f"✓ Using user-specified type: {state['approved_mashup_type']}")

    return state


def create_mashup_node(state: MashupState) -> Dict[str, Any]:
    """Create the final mashup using the engineer agent.

    Updates state with:
    - mashup_output_path
    - status (COMPLETED or FAILED)
    - progress_messages
    """
    logger.info("=== Creating Mashup ===")

    try:
        state["status"] = WorkflowStatus.ENGINEERING.value
        state["current_step"] = "create_mashup"

        mashup_type = state.get("approved_mashup_type", "CLASSIC")
        state["progress_messages"].append(f"Creating {mashup_type} mashup...")

        song_a_id = state["song_a_id"]
        song_b_id = state["song_b_id"]

        # Map mashup type to engineer function
        mashup_functions = {
            "CLASSIC": create_classic_mashup,
            "STEM_SWAP": create_stem_swap_mashup,  # Note: requires 3+ songs
            "ENERGY_MATCHED": create_energy_matched_mashup,
            "ADAPTIVE_HARMONY": create_adaptive_harmony_mashup,
            "THEME_FUSION": create_theme_fusion_mashup,
            "SEMANTIC_ALIGNED": create_semantic_aligned_mashup,
            "ROLE_AWARE": create_role_aware_mashup,
            "CONVERSATIONAL": create_conversational_mashup,
        }

        mashup_fn = mashup_functions.get(mashup_type)
        if not mashup_fn:
            raise EngineerError(f"Unknown mashup type: {mashup_type}")

        # Create mashup
        output_path = mashup_fn(
            song_a_id=song_a_id,
            song_b_id=song_b_id,
            quality="high",
            output_format="mp3"
        )

        state["mashup_output_path"] = output_path
        state["status"] = WorkflowStatus.COMPLETED.value
        state["progress_messages"].append(f"✓ Mashup created: {output_path}")

        logger.info(f"Mashup created successfully: {output_path}")
        return state

    except EngineerError as e:
        logger.error(f"Mashup creation failed: {e}")
        state["status"] = WorkflowStatus.FAILED.value
        state["error"] = f"Failed to create mashup: {e}"
        return state


def error_handler_node(state: MashupState) -> Dict[str, Any]:
    """Handle errors and determine if retry is appropriate.

    Updates state with:
    - retry_count
    - status
    - progress_messages
    """
    logger.error(f"=== Error Handler: {state.get('error')} ===")

    max_retries = 3
    current_retries = state.get("retry_count", 0)

    if current_retries < max_retries:
        state["retry_count"] = current_retries + 1
        state["progress_messages"].append(
            f"⚠ Error encountered, retrying... (attempt {state['retry_count']}/{max_retries})"
        )
        logger.info(f"Retrying workflow (attempt {state['retry_count']}/{max_retries})")
        # Reset error to allow retry
        state["error"] = None
    else:
        state["progress_messages"].append(f"❌ Max retries exceeded, workflow failed")
        logger.error("Max retries exceeded, workflow failed")

    return state
