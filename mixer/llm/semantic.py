"""LLM-based semantic analysis for music metadata."""

import logging
import json
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def analyze_song_semantics(
    transcript: str,
    bpm: float,
    key: str,
    energy_level: float,
    provider: str = "anthropic"
) -> Dict:
    """
    Analyze song semantics using LLM.

    Args:
        transcript: Full lyrics/transcript
        bpm: Detected BPM
        key: Musical key
        energy_level: Energy level (0.0-1.0)
        provider: "anthropic" or "openai"

    Returns:
        Dict with genres, primary_genre, irony_score, mood_summary, valence
    """
    if provider == "anthropic":
        return _analyze_with_anthropic(transcript, bpm, key, energy_level)
    elif provider == "openai":
        return _analyze_with_openai(transcript, bpm, key, energy_level)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def analyze_section_semantics(
    lyrical_content: str,
    section_type: str,
    energy_level: float
) -> Dict:
    """
    Analyze semantics for a single section.

    Args:
        lyrical_content: Lyrics for this section
        section_type: "intro" | "verse" | "chorus" | "bridge" | "outro"
        energy_level: Section energy (0.0-1.0)

    Returns:
        Dict with emotional_tone, lyrical_function, themes
    """
    prompt = f"""Analyze this song section's lyrics.

SECTION TYPE: {section_type}
ENERGY LEVEL: {energy_level:.2f} (0.0-1.0)
LYRICS:
{lyrical_content or "[Instrumental]"}

Return a JSON object with:
1. "emotional_tone": Single word describing emotion (e.g., "hopeful", "melancholic", "defiant", "nostalgic")
2. "lyrical_function": The role of this section (e.g., "narrative", "hook", "question", "answer", "reflection", "climax")
3. "themes": Array of 1-3 themes present (e.g., ["love", "loss", "rebellion"])

IMPORTANT: Return ONLY valid JSON. No additional text."""

    try:
        import anthropic

        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Parse JSON
        result = json.loads(response_text)

        return {
            "emotional_tone": result.get("emotional_tone", "neutral"),
            "lyrical_function": result.get("lyrical_function", "narrative"),
            "themes": result.get("themes", [])
        }

    except Exception as e:
        logger.warning(f"Section semantic analysis failed: {e}")
        # Fallback: simple heuristics
        return {
            "emotional_tone": "neutral",
            "lyrical_function": _infer_function_from_type(section_type),
            "themes": []
        }


def _analyze_with_anthropic(
    transcript: str,
    bpm: float,
    key: str,
    energy_level: float
) -> Dict:
    """Use Anthropic Claude for semantic analysis."""
    import anthropic
    import os

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompt = f"""You are a music analyst. Analyze the following song lyrics and metadata.

LYRICS:
{transcript or "[Instrumental - No Lyrics]"}

TECHNICAL DATA:
- BPM: {bpm:.1f}
- Key: {key}
- Energy: {energy_level:.2f} (0.0-1.0)

TASK:
Return a JSON object with:
1. "genres": Array of 1-3 applicable genres (e.g., ["Pop", "Dance", "Electronic"])
2. "primary_genre": The single most fitting genre
3. "irony_score": Integer 0-10 (0=literal, 10=highly ironic/sarcastic)
4. "mood_summary": 1-2 sentence description of the emotional vibe
5. "valence": Integer 0-10 (0=sad/negative, 10=happy/positive)

IMPORTANT: Return ONLY valid JSON. No additional commentary."""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()
        logger.debug(f"Claude response: {response_text}")

        # Parse JSON response
        result = json.loads(response_text)

        return {
            "genres": result.get("genres", ["Unknown"]),
            "primary_genre": result.get("primary_genre", "Unknown"),
            "irony_score": result.get("irony_score", 0),
            "mood_summary": result.get("mood_summary", ""),
            "valence": result.get("valence", 5)
        }

    except Exception as e:
        logger.error(f"Anthropic analysis failed: {e}")
        return _fallback_semantic_analysis(transcript, bpm, energy_level)


def _analyze_with_openai(
    transcript: str,
    bpm: float,
    key: str,
    energy_level: float
) -> Dict:
    """Use OpenAI GPT-4 for semantic analysis."""
    import openai
    import os

    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""You are a music analyst. Analyze the following song lyrics and metadata.

LYRICS:
{transcript or "[Instrumental - No Lyrics]"}

TECHNICAL DATA:
- BPM: {bpm:.1f}
- Key: {key}
- Energy: {energy_level:.2f} (0.0-1.0)

TASK:
Return a JSON object with:
1. "genres": Array of 1-3 applicable genres
2. "primary_genre": The single most fitting genre
3. "irony_score": Integer 0-10
4. "mood_summary": 1-2 sentence description
5. "valence": Integer 0-10

Return ONLY valid JSON."""

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.3
        )

        response_text = response.choices[0].message.content.strip()
        logger.debug(f"GPT-4 response: {response_text}")

        # Parse JSON
        result = json.loads(response_text)

        return {
            "genres": result.get("genres", ["Unknown"]),
            "primary_genre": result.get("primary_genre", "Unknown"),
            "irony_score": result.get("irony_score", 0),
            "mood_summary": result.get("mood_summary", ""),
            "valence": result.get("valence", 5)
        }

    except Exception as e:
        logger.error(f"OpenAI analysis failed: {e}")
        return _fallback_semantic_analysis(transcript, bpm, energy_level)


def _fallback_semantic_analysis(
    transcript: str,
    bpm: float,
    energy_level: float
) -> Dict:
    """
    Fallback semantic analysis using simple heuristics.

    Used when LLM API calls fail.
    """
    # Simple genre inference from BPM and energy
    if bpm > 140:
        if energy_level > 0.7:
            primary_genre = "Electronic"
            genres = ["Electronic", "Dance"]
        else:
            primary_genre = "Drum and Bass"
            genres = ["Drum and Bass", "Electronic"]
    elif bpm > 120:
        if energy_level > 0.6:
            primary_genre = "Pop"
            genres = ["Pop", "Dance"]
        else:
            primary_genre = "Rock"
            genres = ["Rock", "Alternative"]
    else:
        if energy_level < 0.4:
            primary_genre = "Ballad"
            genres = ["Ballad", "Pop"]
        else:
            primary_genre = "Indie"
            genres = ["Indie", "Alternative"]

    # Simple valence from energy (not accurate but reasonable fallback)
    valence = int(energy_level * 10)

    return {
        "genres": genres,
        "primary_genre": primary_genre,
        "irony_score": 0,  # Can't infer without LLM
        "mood_summary": f"Mid-tempo {primary_genre.lower()} with moderate energy.",
        "valence": valence
    }


def _infer_function_from_type(section_type: str) -> str:
    """Infer lyrical function from section type."""
    function_map = {
        "intro": "setup",
        "verse": "narrative",
        "chorus": "hook",
        "bridge": "reflection",
        "outro": "resolution"
    }
    return function_map.get(section_type, "narrative")


def generate_emotional_arc(sections: List[Dict]) -> str:
    """
    Generate emotional arc summary from section metadata.

    Args:
        sections: List of SectionMetadata dicts

    Returns:
        String like "intro:hopeful → verse:doubt → chorus:defiant"
    """
    if not sections:
        return ""

    arc_parts = []
    for section in sections:
        section_type = section.get("section_type", "unknown")
        emotional_tone = section.get("emotional_tone", "neutral")
        arc_parts.append(f"{section_type}:{emotional_tone}")

    return " → ".join(arc_parts)
