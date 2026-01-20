"""Event-safe validation for client deliverables."""

from typing import List, Tuple
from pathlib import Path
from director.types import Timeline
from director.errors import SafetyViolationError


def validate_event_safe(
    timeline: Timeline,
    mode: str,
    strict: bool = True
) -> Tuple[bool, List[str]]:
    """Validate timeline for event-safe usage.

    Event-safe mode ensures outputs are appropriate for client events
    (weddings, corporate, etc.) by checking theme, content, and metadata.

    Args:
        timeline: Timeline to validate
        mode: Mode ("event", "mashup", "single")
        strict: If True, raise exception on violations. If False, return warnings.

    Returns:
        (is_safe, warnings) tuple

    Raises:
        SafetyViolationError: If strict=True and violations found
    """
    warnings = []

    # Only enforce for event mode
    if mode != "event":
        return (True, [])

    # Check theme is event-appropriate
    theme = timeline["meta"]["theme"]
    allowed_themes = ["award_elegant", "chill_lofi"]

    if theme not in allowed_themes:
        warnings.append(
            f"Theme '{theme}' may not be event-safe. "
            f"Consider: {', '.join(allowed_themes)}"
        )

    # Check for excessive visual effects
    if theme == "mashup_chaos":
        warnings.append(
            "Theme 'mashup_chaos' has strobes and high intensity. "
            "Not recommended for event-safe usage."
        )

    # Check audio file has usage manifest (if from mashup)
    audio_file = timeline["audio"]["file"]
    if "mashup" in audio_file.lower():
        manifest_path = Path(audio_file).parent.parent / "manifests" / f"{Path(audio_file).stem}_manifest.txt"
        if not manifest_path.exists():
            warnings.append(
                f"No usage manifest found at {manifest_path}. "
                "Event-safe mode requires licensing documentation for mashups."
            )

    # Determine safety
    is_safe = len(warnings) == 0

    if not is_safe and strict:
        raise SafetyViolationError(
            "Event-safe validation failed:\n" + "\n".join(f"  • {w}" for w in warnings)
        )

    return (is_safe, warnings)


def generate_usage_manifest(
    song_a_id: str,
    song_b_id: str,
    output_path: Path,
    client_name: str = "Unknown",
    event_type: str = "Unknown"
) -> None:
    """Generate a usage manifest for event-safe mashups.

    Documents which songs were used, for what purpose, and licensing notes.

    Args:
        song_a_id: First song ID
        song_b_id: Second song ID
        output_path: Where to save manifest.txt
        client_name: Client/event name
        event_type: Type of event (wedding, corporate, etc.)
    """
    manifest_content = f"""# Usage Manifest
# Generated for event-safe video output

## Songs Used
- Song A: {song_a_id}
- Song B: {song_b_id}

## Usage Context
- Client: {client_name}
- Event Type: {event_type}

## Legal Notes
This mashup was created for private, non-commercial use at the specified event.
User is responsible for ensuring appropriate licensing for public performance.

## Recommendations
- Verify ASCAP/BMI licensing if event venue requires
- Do not distribute publicly without artist permission
- Keep this manifest with all video outputs
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(manifest_content)


def check_strobe_safety(timeline: Timeline) -> List[str]:
    """Check for strobe/flash effects that may be problematic.

    Args:
        timeline: Timeline to check

    Returns:
        List of warnings about strobe effects
    """
    warnings = []

    # Check theme lighting config
    theme = timeline["meta"]["theme"]

    # These themes have strobes
    if theme in ["sponsor_neon", "mashup_chaos"]:
        warnings.append(
            f"Theme '{theme}' includes strobe effects. "
            "May not be suitable for photosensitive viewers or formal events."
        )

    return warnings
