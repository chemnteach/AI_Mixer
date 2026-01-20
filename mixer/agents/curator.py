"""Curator Agent - Intelligent song selection and compatibility ranking."""

import logging
from typing import List, Optional, Literal
from mixer.types import MatchResult, MashupRecommendation, PairRecommendation, SongMetadata
from mixer.memory import query_harmonic, query_semantic, query_hybrid, get_song
from mixer.config import get_config

logger = logging.getLogger(__name__)


class CuratorError(Exception):
    """Base exception for curator errors."""
    pass


def find_match(
    target_song_id: str,
    criteria: Literal["harmonic", "semantic", "hybrid"] = "hybrid",
    genre_filter: Optional[str] = None,
    semantic_query: Optional[str] = None,
    max_results: int = 5
) -> List[MatchResult]:
    """
    Find compatible songs for mashup creation.

    This is the main entry point for the Curator Agent. It wraps the existing
    query functions with enhanced compatibility scoring and ranking.

    Args:
        target_song_id: ID of the base song
        criteria: Matching strategy ("harmonic" | "semantic" | "hybrid")
        genre_filter: Optional genre constraint (e.g., "Pop", "Country")
        semantic_query: Optional vibe description (e.g., "ironic and upbeat")
        max_results: Number of candidates to return

    Returns:
        List of MatchResult dictionaries sorted by compatibility score

    Raises:
        CuratorError: If target song not found or matching fails
    """
    try:
        logger.info(f"=== Finding Matches for {target_song_id} ===")
        logger.info(f"Criteria: {criteria}, Genre: {genre_filter}, Max: {max_results}")

        # Get target song to validate it exists
        target = get_song(target_song_id)
        if not target:
            raise CuratorError(f"Target song not found: {target_song_id}")

        target_meta = target["metadata"]

        # Route to appropriate query strategy
        if criteria == "harmonic":
            logger.info("Using harmonic matching (BPM + Key)")
            results = query_harmonic(
                target_bpm=target_meta.get("bpm", 120.0),
                target_key=target_meta.get("camelot", "8B"),
                max_results=max_results * 2,  # Over-fetch for filtering
                exclude_ids=[target_song_id]
            )

        elif criteria == "semantic":
            logger.info("Using semantic matching (mood + vibe)")
            query_text = semantic_query or target_meta.get("mood_summary", "")
            if not query_text:
                raise CuratorError("semantic_query required when target has no mood_summary")

            results = query_semantic(
                query_text=query_text,
                max_results=max_results,
                genre_filter=genre_filter,
                exclude_ids=[target_song_id]
            )

        elif criteria == "hybrid":
            logger.info("Using hybrid matching (BPM/Key + semantic reranking)")
            results = query_hybrid(
                target_song_id=target_song_id,
                max_results=max_results,
                genre_filter=genre_filter,
                semantic_query=semantic_query
            )

        else:
            raise CuratorError(f"Invalid criteria: {criteria}. Must be harmonic, semantic, or hybrid")

        # Enhance with detailed compatibility scores and reasons
        enhanced_results = []
        for result in results[:max_results]:
            enhanced = _enhance_match_result(result, target_meta, criteria)
            enhanced_results.append(enhanced)

        logger.info(f"✅ Found {len(enhanced_results)} compatible matches")
        return enhanced_results

    except Exception as e:
        if isinstance(e, CuratorError):
            raise
        raise CuratorError(f"Match finding failed: {e}")


def calculate_compatibility_score(
    song_a_meta: SongMetadata,
    song_b_meta: SongMetadata,
    weights: Optional[dict] = None
) -> tuple[float, List[str]]:
    """
    Calculate compatibility score between two songs.

    Uses weighted combination of:
    - BPM proximity (0-1, closer is better)
    - Key compatibility (0-1, Camelot distance)
    - Energy alignment (0-1, similar energy levels)
    - Genre similarity (0-1, same genre bonus)

    Args:
        song_a_meta: Metadata for first song
        song_b_meta: Metadata for second song
        weights: Optional weight overrides (default from config)

    Returns:
        Tuple of (compatibility_score, match_reasons)
        - compatibility_score: 0.0-1.0 (higher is better)
        - match_reasons: List of human-readable explanations
    """
    config = get_config()

    # Default weights (can be overridden via config)
    if weights is None:
        weights = {
            "bpm": config.get("curator.weight_bpm", 0.35),
            "key": config.get("curator.weight_key", 0.30),
            "energy": config.get("curator.weight_energy", 0.20),
            "genre": config.get("curator.weight_genre", 0.15)
        }

    reasons = []
    scores = {}

    # 1. BPM Proximity (0-1, exponential decay)
    bpm_a = song_a_meta.get("bpm", 120.0)
    bpm_b = song_b_meta.get("bpm", 120.0)
    bpm_diff_pct = abs(bpm_a - bpm_b) / bpm_a
    bpm_score = max(0, 1.0 - (bpm_diff_pct / 0.1))  # 10% diff = 0 score
    scores["bpm"] = bpm_score

    if bpm_diff_pct < 0.02:
        reasons.append(f"BPM: {bpm_b:.1f} (perfect match, <2% diff)")
    elif bpm_diff_pct < 0.05:
        reasons.append(f"BPM: {bpm_b:.1f} (excellent match, {bpm_diff_pct*100:.1f}% diff)")
    else:
        reasons.append(f"BPM: {bpm_b:.1f} ({bpm_diff_pct*100:.1f}% diff)")

    # 2. Key Compatibility (Camelot distance)
    camelot_a = song_a_meta.get("camelot", "8B")
    camelot_b = song_b_meta.get("camelot", "8B")
    key_distance = _calculate_camelot_distance(camelot_a, camelot_b)
    key_score = max(0, 1.0 - (key_distance / 6.0))  # Max distance ~6
    scores["key"] = key_score

    if key_distance == 0:
        reasons.append(f"Key: {camelot_b} (perfect match)")
    elif key_distance == 1:
        reasons.append(f"Key: {camelot_b} (adjacent on Camelot wheel)")
    else:
        reasons.append(f"Key: {camelot_b} (distance: {key_distance})")

    # 3. Energy Alignment
    energy_a = song_a_meta.get("energy_level", 5) / 10.0  # Normalize to 0-1
    energy_b = song_b_meta.get("energy_level", 5) / 10.0
    energy_diff = abs(energy_a - energy_b)
    energy_score = max(0, 1.0 - energy_diff)
    scores["energy"] = energy_score

    if energy_diff < 0.15:
        reasons.append(f"Energy: {energy_b*10:.1f}/10 (similar vibe)")
    else:
        reasons.append(f"Energy: {energy_b*10:.1f}/10 (contrast)")

    # 4. Genre Similarity
    genre_a = song_a_meta.get("primary_genre", "Unknown")
    genre_b = song_b_meta.get("primary_genre", "Unknown")
    genre_score = 1.0 if genre_a == genre_b else 0.5  # Partial credit for different genres
    scores["genre"] = genre_score

    if genre_a == genre_b:
        reasons.append(f"Genre: {genre_b} (same genre)")
    else:
        reasons.append(f"Genre: {genre_b} (cross-genre blend)")

    # Calculate weighted total
    total_score = sum(scores[k] * weights[k] for k in weights.keys())

    # Normalize to 0-1 range
    total_score = min(1.0, max(0.0, total_score))

    logger.debug(f"Compatibility: {total_score:.3f} (BPM:{bpm_score:.2f} Key:{key_score:.2f} Energy:{energy_score:.2f} Genre:{genre_score:.2f})")

    return total_score, reasons


def recommend_mashup_type(
    song_a_meta: SongMetadata,
    song_b_meta: SongMetadata
) -> MashupRecommendation:
    """
    Recommend best mashup type for a song pair.

    Analyzes song characteristics to suggest the most suitable mashup strategy
    from the 8 available types.

    Decision logic:
    - CLASSIC: Default for most pairs with vocals
    - ADAPTIVE_HARMONY: Different keys (>2 semitones apart)
    - ENERGY_MATCHED: Similar energy curves, different structures
    - THEME_FUSION: Overlapping lyrical themes
    - SEMANTIC_ALIGNED: Complementary lyrical functions
    - ROLE_AWARE: Dense vocals + sparse vocals
    - CONVERSATIONAL: Question/answer or narrative/reflection patterns
    - STEM_SWAP: Requires 3+ songs (not applicable for pairs)

    Args:
        song_a_meta: Metadata for first song
        song_b_meta: Metadata for second song

    Returns:
        MashupRecommendation with type, confidence, reasoning, and config

    """
    # Check for section-level metadata
    has_sections_a = bool(song_a_meta.get("sections"))
    has_sections_b = bool(song_b_meta.get("sections"))
    has_sections = has_sections_a and has_sections_b

    # Get key characteristics
    key_distance = _calculate_camelot_distance(
        song_a_meta.get("camelot", "8B"),
        song_b_meta.get("camelot", "8B")
    )
    has_vocals_a = song_a_meta.get("has_vocals", True)
    has_vocals_b = song_b_meta.get("has_vocals", True)

    # Decision tree for mashup type recommendation
    recommendations = []

    # 1. Check for key incompatibility → Adaptive Harmony
    if key_distance > 2 and has_vocals_a and has_vocals_b:
        recommendations.append({
            "type": "ADAPTIVE_HARMONY",
            "confidence": 0.9,
            "reason": f"Keys are {key_distance} steps apart - pitch-shifting will fix clash"
        })

    # 2. Check for conversational potential (requires sections)
    if has_sections:
        sections_a = song_a_meta.get("sections", [])
        sections_b = song_b_meta.get("sections", [])

        # Count lyrical function types
        funcs_a = set(s.get("lyrical_function", "") for s in sections_a)
        funcs_b = set(s.get("lyrical_function", "") for s in sections_b)

        # Check for conversational pairs
        has_question_a = "question" in funcs_a
        has_answer_b = "answer" in funcs_b
        has_narrative = "narrative" in funcs_a or "narrative" in funcs_b
        has_reflection = "reflection" in funcs_a or "reflection" in funcs_b

        if (has_question_a and has_answer_b) or (has_narrative and has_reflection):
            recommendations.append({
                "type": "CONVERSATIONAL",
                "confidence": 0.85,
                "reason": "Songs have complementary lyrical functions (question→answer or narrative→reflection)"
            })

        # Check for theme overlap
        themes_a = set()
        themes_b = set()
        for section in sections_a:
            themes_a.update(section.get("themes", []))
        for section in sections_b:
            themes_b.update(section.get("themes", []))

        common_themes = themes_a & themes_b
        if common_themes:
            theme = list(common_themes)[0]  # Pick first common theme
            recommendations.append({
                "type": "THEME_FUSION",
                "confidence": 0.80,
                "reason": f"Shared theme: '{theme}' - can create thematic narrative"
            })

        # Check for role-aware potential (different vocal densities)
        densities_a = set(s.get("vocal_density", "") for s in sections_a)
        densities_b = set(s.get("vocal_density", "") for s in sections_b)

        has_dense = "dense" in densities_a or "dense" in densities_b
        has_sparse = "sparse" in densities_a or "sparse" in densities_b

        if has_dense and has_sparse:
            recommendations.append({
                "type": "ROLE_AWARE",
                "confidence": 0.75,
                "reason": "Contrasting vocal densities - can create lead/harmony/texture roles"
            })

    # 3. Default to CLASSIC if both have vocals
    if has_vocals_a and has_vocals_b:
        recommendations.append({
            "type": "CLASSIC",
            "confidence": 0.70,
            "reason": "Both songs have vocals - classic vocal+instrumental mashup works well"
        })
    elif has_vocals_a or has_vocals_b:
        recommendations.append({
            "type": "CLASSIC",
            "confidence": 0.60,
            "reason": "One song has vocals - can extract vocal or instrumental as needed"
        })

    # Pick best recommendation (highest confidence)
    if not recommendations:
        # Fallback
        recommendations.append({
            "type": "CLASSIC",
            "confidence": 0.50,
            "reason": "Default mashup type (no special characteristics detected)"
        })

    best = max(recommendations, key=lambda x: x["confidence"])

    # Build config suggestion
    config_suggestion = {
        "song_a_id": song_a_meta.get("artist", "unknown") + "_" + song_a_meta.get("title", "unknown"),
        "song_b_id": song_b_meta.get("artist", "unknown") + "_" + song_b_meta.get("title", "unknown"),
    }

    if best["type"] == "THEME_FUSION" and has_sections:
        # Add theme suggestion
        themes_a = set()
        for section in song_a_meta.get("sections", []):
            themes_a.update(section.get("themes", []))
        if themes_a:
            config_suggestion["theme"] = list(themes_a)[0]

    return MashupRecommendation(
        mashup_type=best["type"],
        confidence=best["confidence"],
        reasoning=best["reason"],
        config_suggestion=config_suggestion
    )


def find_all_pairs(
    max_pairs: int = 10,
    min_compatibility: float = 0.5,
    genre_filter: Optional[str] = None
) -> List[PairRecommendation]:
    """
    Find best song pairs across entire library.

    Performs batch analysis to discover the most compatible song combinations
    for mashup creation. Useful for automated playlist generation.

    Args:
        max_pairs: Maximum number of pairs to return
        min_compatibility: Minimum compatibility score threshold (0.0-1.0)
        genre_filter: Optional genre constraint

    Returns:
        List of PairRecommendation sorted by compatibility (best first)

    Raises:
        CuratorError: If library querying fails
    """
    try:
        from mixer.memory import get_client

        logger.info(f"=== Finding Best Pairs in Library ===")
        logger.info(f"Max pairs: {max_pairs}, Min compatibility: {min_compatibility}")

        client = get_client()
        collection = client.get_collection()

        # Get all songs
        where_clause = {"primary_genre": genre_filter} if genre_filter else None
        all_songs = collection.get(
            where=where_clause,
            include=["metadatas"]
        )

        song_ids = all_songs["ids"]
        song_metas = all_songs["metadatas"]

        if len(song_ids) < 2:
            logger.warning("Library has fewer than 2 songs - cannot find pairs")
            return []

        logger.info(f"Analyzing {len(song_ids)} songs...")

        # Generate all unique pairs
        pairs = []
        for i in range(len(song_ids)):
            for j in range(i + 1, len(song_ids)):
                song_a_id = song_ids[i]
                song_b_id = song_ids[j]
                meta_a = song_metas[i]
                meta_b = song_metas[j]

                # Calculate compatibility
                score, reasons = calculate_compatibility_score(meta_a, meta_b)

                if score >= min_compatibility:
                    # Get mashup recommendation
                    mashup_rec = recommend_mashup_type(meta_a, meta_b)

                    pair = PairRecommendation(
                        song_a_id=song_a_id,
                        song_b_id=song_b_id,
                        compatibility_score=score,
                        match_reasons=reasons,
                        recommended_mashup=mashup_rec
                    )
                    pairs.append(pair)

        # Sort by compatibility (best first)
        pairs.sort(key=lambda x: x["compatibility_score"], reverse=True)

        result = pairs[:max_pairs]
        logger.info(f"✅ Found {len(result)} compatible pairs (from {len(pairs)} candidates)")

        return result

    except Exception as e:
        raise CuratorError(f"Batch pair finding failed: {e}")


# Helper functions

def _enhance_match_result(
    result: MatchResult,
    target_meta: SongMetadata,
    criteria: str
) -> MatchResult:
    """
    Enhance match result with detailed compatibility info.

    Args:
        result: Raw match result from query
        target_meta: Target song metadata
        criteria: Matching criteria used

    Returns:
        Enhanced MatchResult with detailed match_reasons
    """
    # Recalculate with detailed reasons
    score, reasons = calculate_compatibility_score(target_meta, result["metadata"])

    # Update result
    result["compatibility_score"] = score
    result["match_reasons"] = reasons

    return result


def _calculate_camelot_distance(camelot_a: str, camelot_b: str) -> int:
    """
    Calculate distance between two Camelot keys.

    Distance metrics:
    - Same key: 0
    - Adjacent on wheel (±1): 1
    - Inner/outer circle: 1
    - Opposite on wheel: 6 (maximum)

    Args:
        camelot_a: First Camelot key (e.g., "8B")
        camelot_b: Second Camelot key (e.g., "9A")

    Returns:
        Distance as integer (0-6)
    """
    if camelot_a == camelot_b:
        return 0

    # Parse number and letter
    try:
        num_a = int(camelot_a[:-1])
        letter_a = camelot_a[-1]
        num_b = int(camelot_b[:-1])
        letter_b = camelot_b[-1]
    except (ValueError, IndexError):
        # Invalid format, return max distance
        return 6

    # Calculate circular distance on wheel (1-12)
    wheel_dist = min(abs(num_a - num_b), 12 - abs(num_a - num_b))

    # Inner/outer circle adds distance if numbers are same but letters differ
    if num_a == num_b and letter_a != letter_b:
        return 1  # Relative major/minor

    # If same letter (same circle), just wheel distance
    if letter_a == letter_b:
        return wheel_dist

    # Different circle and different number: combine distances
    return wheel_dist + 1
