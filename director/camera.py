"""Camera path generation from timeline events."""

from typing import List, Literal
from director.types import CameraMovement, CameraData, TimelineEvent, ThemeConfig
from director.errors import CameraPathError


def generate_zoom_on_drop(
    events: List[TimelineEvent],
    zoom_duration: float = 2.0,
    zoom_magnitude: float = 0.15
) -> List[CameraMovement]:
    """Generate zoom movements for drop events.

    Args:
        events: Timeline events to process
        zoom_duration: How long the zoom lasts (seconds)
        zoom_magnitude: Not used in basic implementation, for future

    Returns:
        List of camera movements
    """
    movements = []

    for event in events:
        if event["type"] == "drop" and event["intensity"] in ["medium", "high"]:
            # Zoom in on drops
            movements.append({
                "t": event["t"],
                "action": "zoom_in",
                "duration": zoom_duration
            })

            # Zoom back out after drop
            movements.append({
                "t": event["t"] + zoom_duration,
                "action": "zoom_out",
                "duration": zoom_duration * 0.5  # Faster return
            })

    return movements


def generate_retention_nudges(
    events: List[TimelineEvent],
    nudge_magnitude: float = 0.1
) -> List[CameraMovement]:
    """Generate subtle camera nudges for retention events.

    Args:
        events: Timeline events to process
        nudge_magnitude: Not used in basic implementation, for future

    Returns:
        List of camera movements
    """
    movements = []
    alternate = True

    for event in events:
        if event["type"] == "retention_nudge":
            # Alternate left/right nudges
            action = "nudge_left" if alternate else "nudge_right"
            movements.append({
                "t": event["t"],
                "action": action,
                "duration": 1.0
            })
            alternate = not alternate

    return movements


def generate_camera_paths(
    events: List[TimelineEvent],
    theme: ThemeConfig,
    base_shot: Literal["close", "medium", "wide"] = "medium"
) -> CameraData:
    """Generate camera configuration from events and theme.

    Args:
        events: Timeline events
        theme: Theme configuration
        base_shot: Default camera framing

    Returns:
        CameraData with base shot and movement list

    Raises:
        CameraPathError: If camera path generation fails
    """
    try:
        movements = []

        # Get theme settings
        zoom_on_drop = theme.get("camera", {}).get("zoom_on_drop", True)
        retention_nudges = theme.get("camera", {}).get("retention_nudges", True)
        zoom_magnitude = theme.get("camera", {}).get("zoom_magnitude", 0.15)
        nudge_magnitude = theme.get("camera", {}).get("nudge_magnitude", 0.1)

        # Generate movements based on events
        if zoom_on_drop:
            movements.extend(generate_zoom_on_drop(
                events,
                zoom_duration=2.0,
                zoom_magnitude=zoom_magnitude
            ))

        if retention_nudges:
            movements.extend(generate_retention_nudges(
                events,
                nudge_magnitude=nudge_magnitude
            ))

        # Sort movements by timestamp
        movements.sort(key=lambda m: m["t"])

        return {
            "base_shot": base_shot,
            "movements": movements
        }

    except Exception as e:
        raise CameraPathError(f"Failed to generate camera paths: {e}") from e


def optimize_camera_movements(movements: List[CameraMovement]) -> List[CameraMovement]:
    """Optimize camera movements to avoid conflicts.

    Removes overlapping movements, keeping only the most impactful.

    Args:
        movements: Raw camera movements

    Returns:
        Optimized movement list
    """
    if not movements:
        return []

    optimized = []
    current_end_time = 0.0

    for movement in sorted(movements, key=lambda m: m["t"]):
        # Only add if it doesn't overlap with previous movement
        if movement["t"] >= current_end_time:
            optimized.append(movement)
            current_end_time = movement["t"] + movement["duration"]

    return optimized
