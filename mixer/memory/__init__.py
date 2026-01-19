"""Memory system for The Mixer using ChromaDB."""

from mixer.memory.client import (
    ChromaClient,
    ChromaClientError,
    get_client,
    reset_client,
)

from mixer.memory.schema import (
    SchemaError,
    sanitize_id,
    validate_metadata,
    create_document,
    generate_timestamp,
    handle_id_collision,
    extract_artist_title_from_filename,
    camelot_to_key,
    key_to_camelot,
)

from mixer.memory.queries import (
    QueryError,
    upsert_song,
    get_song,
    delete_song,
    query_harmonic,
    query_semantic,
    query_hybrid,
    list_all_songs,
)

__all__ = [
    # Client
    "ChromaClient",
    "ChromaClientError",
    "get_client",
    "reset_client",
    # Schema
    "SchemaError",
    "sanitize_id",
    "validate_metadata",
    "create_document",
    "generate_timestamp",
    "handle_id_collision",
    "extract_artist_title_from_filename",
    "camelot_to_key",
    "key_to_camelot",
    # Queries
    "QueryError",
    "upsert_song",
    "get_song",
    "delete_song",
    "query_harmonic",
    "query_semantic",
    "query_hybrid",
    "list_all_songs",
]
