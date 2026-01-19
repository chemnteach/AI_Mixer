"""Query operations for ChromaDB music library."""

import logging
from typing import Optional, List
from mixer.types import SongMetadata, MatchResult
from mixer.memory.client import get_client
from mixer.memory.schema import (
    sanitize_id,
    validate_metadata,
    create_document,
    generate_timestamp,
    handle_id_collision,
)
from mixer.config import get_config

logger = logging.getLogger(__name__)


class QueryError(Exception):
    """Query operation errors."""
    pass


def upsert_song(
    artist: str,
    title: str,
    metadata: SongMetadata,
    transcript: str = "",
    force_id: Optional[str] = None,
) -> str:
    """Insert or update a song in ChromaDB.

    Args:
        artist: Artist name
        title: Song title
        metadata: Complete song metadata
        transcript: Lyrical transcription from Whisper
        force_id: Optional ID to use instead of auto-generating

    Returns:
        Song ID used for storage

    Raises:
        QueryError: If upsert operation fails
    """
    try:
        # Validate metadata
        validate_metadata(metadata)

        # Generate or use provided ID
        if force_id:
            song_id = force_id
        else:
            song_id = sanitize_id(artist, title)

        # Check for ID collision
        client = get_client()
        collection = client.get_collection()
        existing = collection.get(ids=[song_id])

        if existing["ids"] and not force_id:
            # Handle collision
            all_ids = collection.get()["ids"]
            song_id = handle_id_collision(song_id, all_ids)
            logger.warning(f"ID collision detected. Using {song_id}")

        # Add timestamp if not present
        if "date_added" not in metadata:
            metadata["date_added"] = generate_timestamp()

        # Create document for embedding
        mood_summary = metadata.get("mood_summary", "")
        document = create_document(transcript, mood_summary)

        # Upsert to ChromaDB
        collection.upsert(
            ids=[song_id],
            documents=[document],
            metadatas=[metadata],
        )

        logger.info(f"Song upserted: {song_id} ({artist} - {title})")
        return song_id

    except Exception as e:
        raise QueryError(f"Failed to upsert song: {e}")


def get_song(song_id: str) -> Optional[dict]:
    """Retrieve a song by ID.

    Args:
        song_id: Song identifier

    Returns:
        Dictionary with 'id', 'metadata', 'document' or None if not found

    Raises:
        QueryError: If query fails
    """
    try:
        client = get_client()
        collection = client.get_collection()

        result = collection.get(
            ids=[song_id],
            include=["metadatas", "documents"]
        )

        if not result["ids"]:
            return None

        return {
            "id": result["ids"][0],
            "metadata": result["metadatas"][0],
            "document": result["documents"][0],
        }

    except Exception as e:
        raise QueryError(f"Failed to get song: {e}")


def delete_song(song_id: str) -> bool:
    """Delete a song from ChromaDB.

    Note: This does NOT delete the cached audio file.

    Args:
        song_id: Song identifier

    Returns:
        True if deleted, False if not found

    Raises:
        QueryError: If deletion fails
    """
    try:
        client = get_client()
        collection = client.get_collection()

        # Check if exists
        existing = collection.get(ids=[song_id])
        if not existing["ids"]:
            return False

        collection.delete(ids=[song_id])
        logger.info(f"Song deleted: {song_id}")
        return True

    except Exception as e:
        raise QueryError(f"Failed to delete song: {e}")


def query_harmonic(
    target_bpm: float,
    target_key: str,
    bpm_tolerance: Optional[float] = None,
    max_results: int = 5,
    exclude_ids: Optional[List[str]] = None,
) -> List[MatchResult]:
    """Find songs matching BPM and key (harmonic matching).

    Args:
        target_bpm: Target BPM
        target_key: Target key in Camelot notation (e.g., "8B")
        bpm_tolerance: BPM tolerance as fraction (default from config)
        max_results: Maximum results to return
        exclude_ids: Song IDs to exclude from results

    Returns:
        List of MatchResult dictionaries sorted by compatibility

    Raises:
        QueryError: If query fails
    """
    try:
        config = get_config()
        if bpm_tolerance is None:
            bpm_tolerance = config.get("curator.bpm_tolerance", 0.05)

        # Calculate BPM range
        bpm_min = target_bpm * (1 - bpm_tolerance)
        bpm_max = target_bpm * (1 + bpm_tolerance)

        # Get compatible keys
        compatible_keys = _get_compatible_keys(target_key)

        # Build where clause
        where_clause = {
            "$and": [
                {"bpm": {"$gte": bpm_min, "$lte": bpm_max}},
                {"camelot": {"$in": compatible_keys}},
            ]
        }

        client = get_client()
        collection = client.get_collection()

        # Query ChromaDB
        results = collection.get(
            where=where_clause,
            include=["metadatas"],
        )

        # Filter excluded IDs
        if exclude_ids:
            filtered_ids = []
            filtered_metadatas = []
            for i, song_id in enumerate(results["ids"]):
                if song_id not in exclude_ids:
                    filtered_ids.append(song_id)
                    filtered_metadatas.append(results["metadatas"][i])
            results["ids"] = filtered_ids
            results["metadatas"] = filtered_metadatas

        # Rank by BPM proximity
        ranked_results = []
        for i, song_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i]
            bpm_diff = abs(metadata["bpm"] - target_bpm)
            key_distance = _camelot_distance(target_key, metadata["camelot"])

            # Calculate compatibility score (0-1, higher is better)
            bpm_score = 1.0 - (bpm_diff / target_bpm)
            key_score = 1.0 - (key_distance / 6.0)  # Max distance is 6 on Camelot wheel
            compatibility_score = (bpm_score * 0.6) + (key_score * 0.4)

            match_reasons = [
                f"BPM: {metadata['bpm']:.1f} (within {abs(metadata['bpm'] - target_bpm):.1f} of target)",
                f"Key: {metadata['camelot']} (distance: {key_distance})",
            ]

            ranked_results.append({
                "id": song_id,
                "compatibility_score": compatibility_score,
                "metadata": metadata,
                "match_reasons": match_reasons,
            })

        # Sort by score
        ranked_results.sort(key=lambda x: x["compatibility_score"], reverse=True)

        return ranked_results[:max_results]

    except Exception as e:
        raise QueryError(f"Harmonic query failed: {e}")


def query_semantic(
    query_text: str,
    max_results: int = 5,
    genre_filter: Optional[str] = None,
    exclude_ids: Optional[List[str]] = None,
) -> List[MatchResult]:
    """Find songs by semantic similarity (mood, vibe, lyrics).

    Args:
        query_text: Natural language query (e.g., "ironic upbeat pop")
        max_results: Maximum results to return
        genre_filter: Optional genre constraint
        exclude_ids: Song IDs to exclude from results

    Returns:
        List of MatchResult dictionaries sorted by similarity

    Raises:
        QueryError: If query fails
    """
    try:
        client = get_client()
        collection = client.get_collection()

        # Build where clause
        where_clause = None
        if genre_filter:
            where_clause = {"primary_genre": genre_filter}

        # Query by semantic similarity
        results = collection.query(
            query_texts=[query_text],
            n_results=max_results * 2,  # Over-fetch for filtering
            where=where_clause,
            include=["metadatas", "distances"],
        )

        # Filter excluded IDs
        if exclude_ids:
            filtered_ids = []
            filtered_metadatas = []
            filtered_distances = []
            for i, song_id in enumerate(results["ids"][0]):
                if song_id not in exclude_ids:
                    filtered_ids.append(song_id)
                    filtered_metadatas.append(results["metadatas"][0][i])
                    filtered_distances.append(results["distances"][0][i])
            results["ids"][0] = filtered_ids
            results["metadatas"][0] = filtered_metadatas
            results["distances"][0] = filtered_distances

        # Format results
        match_results = []
        for i, song_id in enumerate(results["ids"][0][:max_results]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            # Convert distance to similarity score (0-1, higher is better)
            similarity_score = 1.0 - distance

            match_reasons = [
                f"Semantic similarity: {similarity_score:.2f}",
                f"Mood: {metadata.get('mood_summary', 'N/A')}",
                f"Genre: {metadata.get('primary_genre', 'N/A')}",
            ]

            match_results.append({
                "id": song_id,
                "compatibility_score": similarity_score,
                "metadata": metadata,
                "match_reasons": match_reasons,
            })

        return match_results

    except Exception as e:
        raise QueryError(f"Semantic query failed: {e}")


def query_hybrid(
    target_song_id: str,
    max_results: int = 5,
    genre_filter: Optional[str] = None,
    semantic_query: Optional[str] = None,
) -> List[MatchResult]:
    """Hybrid search: BPM/key filtering + semantic reranking.

    This is the RECOMMENDED matching strategy from the PRD.

    Args:
        target_song_id: ID of the base song
        max_results: Maximum results to return
        genre_filter: Optional genre constraint
        semantic_query: Optional semantic override (uses target mood if None)

    Returns:
        List of MatchResult dictionaries sorted by hybrid score

    Raises:
        QueryError: If query fails
    """
    try:
        # Get target song metadata
        target = get_song(target_song_id)
        if not target:
            raise QueryError(f"Target song not found: {target_song_id}")

        target_meta = target["metadata"]
        target_bpm = target_meta.get("bpm")
        target_key = target_meta.get("camelot")

        if not target_bpm or not target_key:
            raise QueryError(f"Target song missing BPM or key: {target_song_id}")

        # Step 1: Harmonic filtering (get candidates)
        harmonic_results = query_harmonic(
            target_bpm=target_bpm,
            target_key=target_key,
            max_results=50,  # Over-fetch for reranking
            exclude_ids=[target_song_id],
        )

        if not harmonic_results:
            logger.warning("No harmonic matches found")
            return []

        # Step 2: Semantic reranking
        candidate_ids = [r["id"] for r in harmonic_results]

        # Use target's mood or provided query
        if semantic_query is None:
            semantic_query = target["document"]

        client = get_client()
        collection = client.get_collection()

        # Build where clause for candidates
        where_clause = {"$and": [{"$or": [{"id": {"$eq": cid}} for cid in candidate_ids]}]}
        if genre_filter:
            where_clause["$and"].append({"primary_genre": genre_filter})

        # Semantic query on candidates
        semantic_results = collection.query(
            query_texts=[semantic_query],
            n_results=max_results,
            where=where_clause,
            include=["metadatas", "distances"],
        )

        # Combine scores (60% harmonic, 40% semantic)
        hybrid_results = []
        harmonic_lookup = {r["id"]: r for r in harmonic_results}

        for i, song_id in enumerate(semantic_results["ids"][0]):
            if song_id not in harmonic_lookup:
                continue

            harmonic_match = harmonic_lookup[song_id]
            harmonic_score = harmonic_match["compatibility_score"]

            distance = semantic_results["distances"][0][i]
            semantic_score = 1.0 - distance

            # Hybrid score
            hybrid_score = (harmonic_score * 0.6) + (semantic_score * 0.4)

            match_reasons = [
                f"Hybrid score: {hybrid_score:.2f}",
                f"BPM: {harmonic_match['metadata']['bpm']:.1f} (target: {target_bpm:.1f})",
                f"Key: {harmonic_match['metadata']['camelot']} (target: {target_key})",
                f"Semantic similarity: {semantic_score:.2f}",
            ]

            hybrid_results.append({
                "id": song_id,
                "compatibility_score": hybrid_score,
                "metadata": harmonic_match["metadata"],
                "match_reasons": match_reasons,
            })

        # Sort by hybrid score
        hybrid_results.sort(key=lambda x: x["compatibility_score"], reverse=True)

        return hybrid_results[:max_results]

    except Exception as e:
        raise QueryError(f"Hybrid query failed: {e}")


def list_all_songs(limit: int = 100, offset: int = 0) -> List[dict]:
    """List all songs in the library.

    Args:
        limit: Maximum songs to return
        offset: Number of songs to skip

    Returns:
        List of song dictionaries with 'id' and 'metadata'

    Raises:
        QueryError: If query fails
    """
    try:
        client = get_client()
        collection = client.get_collection()

        results = collection.get(
            limit=limit,
            offset=offset,
            include=["metadatas"],
        )

        songs = []
        for i, song_id in enumerate(results["ids"]):
            songs.append({
                "id": song_id,
                "metadata": results["metadatas"][i],
            })

        return songs

    except Exception as e:
        raise QueryError(f"Failed to list songs: {e}")


# Helper functions

def _get_compatible_keys(camelot: str) -> List[str]:
    """Get harmonically compatible Camelot keys.

    Compatible moves:
    - Same key (8B → 8B)
    - +1/-1 on wheel (8B → 7B, 9B)
    - Inner/outer circle (8B → 8A)

    Args:
        camelot: Camelot notation (e.g., "8B")

    Returns:
        List of compatible keys
    """
    # Parse number and letter
    if len(camelot) < 2:
        return [camelot]

    number = int(camelot[:-1])
    letter = camelot[-1]

    compatible = [camelot]  # Same key

    # Adjacent numbers on wheel (with wraparound)
    adjacent_plus = ((number % 12) + 1)
    adjacent_minus = ((number - 2) % 12) + 1

    compatible.append(f"{adjacent_plus}{letter}")
    compatible.append(f"{adjacent_minus}{letter}")

    # Inner/outer circle (A ↔ B)
    opposite_letter = "A" if letter == "B" else "B"
    compatible.append(f"{number}{opposite_letter}")

    return compatible


def _camelot_distance(key1: str, key2: str) -> int:
    """Calculate distance between two keys on Camelot wheel.

    Args:
        key1: First Camelot key
        key2: Second Camelot key

    Returns:
        Distance (0 = same, 1 = adjacent, 2 = two steps away, etc.)
    """
    if key1 == key2:
        return 0

    # Parse keys
    num1 = int(key1[:-1])
    letter1 = key1[-1]
    num2 = int(key2[:-1])
    letter2 = key2[-1]

    # Inner/outer circle (A ↔ B with same number)
    if num1 == num2:
        return 1

    # Calculate circular distance on wheel
    distance = min(abs(num1 - num2), 12 - abs(num1 - num2))

    # Add 1 if different circle
    if letter1 != letter2:
        distance += 1

    return distance
