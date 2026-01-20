"""LangGraph workflow definition for mashup creation pipeline."""

import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from mixer.workflow.state import MashupState, WorkflowStatus
from mixer.workflow.nodes import (
    ingest_song_a_node,
    analyze_song_a_node,
    ingest_song_b_node,
    analyze_song_b_node,
    find_matches_node,
    await_user_selection_node,
    recommend_mashup_type_node,
    await_mashup_approval_node,
    create_mashup_node,
    error_handler_node,
)

logger = logging.getLogger(__name__)


def should_continue_after_error(state: MashupState) -> Literal["retry", "end"]:
    """Conditional edge: determine if workflow should retry or end after error."""
    if state.get("error") is None:
        # Error was cleared by error handler, retry from current step
        return "retry"
    else:
        # Max retries exceeded, end workflow
        return "end"


def should_find_matches(state: MashupState) -> Literal["find_matches", "recommend_type"]:
    """Conditional edge: determine if we need to find matches or proceed to recommendation."""
    if state.get("song_b_id"):
        # Song B provided, skip curation
        return "recommend_type"
    else:
        # Need to find matches for song A
        return "find_matches"


def has_match_selected(state: MashupState) -> Literal["await_selection", "recommend_type"]:
    """Conditional edge: check if a match has been selected."""
    if state.get("song_b_id"):
        # Match selected (either auto-selected or by user)
        return "recommend_type"
    else:
        # Still waiting for user selection
        return "await_selection"


def create_mashup_workflow() -> StateGraph:
    """Create the LangGraph workflow for mashup creation.

    Workflow DAG:
    START
      ↓
    ingest_song_a → analyze_song_a → [song_b provided?]
                                        ↓ Yes: ingest_song_b → analyze_song_b
                                        ↓ No: find_matches → await_user_selection
      ↓
    recommend_mashup_type → await_mashup_approval → create_mashup
      ↓
    END

    Error handling:
    - Any node can fail and trigger error_handler
    - Error handler decides retry vs abort
    - Retry returns to the failed node

    Returns:
        StateGraph ready to compile
    """
    workflow = StateGraph(MashupState)

    # Add all nodes
    workflow.add_node("ingest_song_a", ingest_song_a_node)
    workflow.add_node("analyze_song_a", analyze_song_a_node)
    workflow.add_node("ingest_song_b", ingest_song_b_node)
    workflow.add_node("analyze_song_b", analyze_song_b_node)
    workflow.add_node("find_matches", find_matches_node)
    workflow.add_node("await_user_selection", await_user_selection_node)
    workflow.add_node("recommend_mashup_type", recommend_mashup_type_node)
    workflow.add_node("await_mashup_approval", await_mashup_approval_node)
    workflow.add_node("create_mashup", create_mashup_node)
    workflow.add_node("error_handler", error_handler_node)

    # Set entry point
    workflow.set_entry_point("ingest_song_a")

    # Define workflow edges (happy path)
    workflow.add_edge("ingest_song_a", "analyze_song_a")

    # After analyzing song A, check if song B provided
    workflow.add_conditional_edges(
        "analyze_song_a",
        should_find_matches,
        {
            "find_matches": "find_matches",
            "recommend_type": "ingest_song_b",  # Process song B if provided
        }
    )

    # Song B path
    workflow.add_edge("ingest_song_b", "analyze_song_b")
    workflow.add_edge("analyze_song_b", "recommend_mashup_type")

    # Curation path (when song B not provided)
    workflow.add_edge("find_matches", "await_user_selection")
    workflow.add_conditional_edges(
        "await_user_selection",
        has_match_selected,
        {
            "await_selection": "await_user_selection",  # Loop until selected
            "recommend_type": "recommend_mashup_type",
        }
    )

    # Mashup creation path
    workflow.add_edge("recommend_mashup_type", "await_mashup_approval")
    workflow.add_edge("await_mashup_approval", "create_mashup")

    # Terminal edge
    workflow.add_edge("create_mashup", END)

    # Error handling edges
    # Note: In a full implementation, we would add conditional edges
    # from each node to error_handler on failure, but for simplicity
    # we're handling errors within nodes for now

    logger.info("Mashup workflow graph created")
    return workflow


def run_mashup_workflow(
    input_source_a: str,
    input_source_b: str = None,
    mashup_type: str = None,
    stream: bool = False
) -> Dict[str, Any]:
    """Run the mashup creation workflow.

    Args:
        input_source_a: URL or file path for song A
        input_source_b: Optional URL or file path for song B
        mashup_type: Optional mashup type (if None, curator will recommend)
        stream: If True, stream progress messages

    Returns:
        Final workflow state with mashup_output_path

    Raises:
        WorkflowError: If workflow fails after retries
    """
    logger.info("=== Starting Mashup Workflow ===")
    logger.info(f"Song A: {input_source_a}")
    logger.info(f"Song B: {input_source_b or 'TBD (will find match)'}")
    logger.info(f"Mashup Type: {mashup_type or 'TBD (will recommend)'}")

    # Initialize state
    initial_state: MashupState = {
        "input_source_a": input_source_a,
        "input_source_b": input_source_b,
        "mashup_type": mashup_type,
        "status": WorkflowStatus.PENDING.value,
        "current_step": "start",
        "error": None,
        "retry_count": 0,
        "song_a_cached": False,
        "song_b_cached": False,
        "progress_messages": [],
    }

    # Create and compile workflow
    workflow = create_mashup_workflow()
    app = workflow.compile()

    # Run workflow
    try:
        # Execute workflow
        final_state = app.invoke(initial_state)

        # Stream progress if requested
        if stream:
            for msg in final_state.get("progress_messages", []):
                print(msg)

        # Check final status
        if final_state["status"] == WorkflowStatus.COMPLETED.value:
            logger.info(f"✅ Workflow completed: {final_state['mashup_output_path']}")
            return final_state
        else:
            error_msg = final_state.get("error", "Unknown error")
            logger.error(f"❌ Workflow failed: {error_msg}")
            raise WorkflowError(f"Workflow failed: {error_msg}")

    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise WorkflowError(f"Workflow execution failed: {e}")


class WorkflowError(Exception):
    """Base exception for workflow errors."""
    pass
