"""Director Agent - Visual Intelligence Layer for Mixer.

Translates audio metadata from Mixer into visual animation timelines.
"""

from director.timeline import generate_timeline
from director.events import generate_events_from_sections
from director.camera import generate_camera_paths
from director.themes import load_theme
from director.safety import validate_event_safe
from director.errors import DirectorError, ThemeNotFoundError, InvalidTimelineError

__all__ = [
    "generate_timeline",
    "generate_events_from_sections",
    "generate_camera_paths",
    "load_theme",
    "validate_event_safe",
    "DirectorError",
    "ThemeNotFoundError",
    "InvalidTimelineError",
]
