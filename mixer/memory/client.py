"""ChromaDB client initialization and management."""

import logging
from pathlib import Path
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.api.models.Collection import Collection
except ImportError:
    raise ImportError(
        "ChromaDB not installed. Run: pip install chromadb==0.4.22"
    )

from mixer.config import get_config

logger = logging.getLogger(__name__)


class ChromaClientError(Exception):
    """ChromaDB client errors."""
    pass


class ChromaClient:
    """Manages ChromaDB client and collection for The Mixer.

    This class provides a singleton interface to ChromaDB, ensuring
    persistent storage and consistent access to the music library.
    """

    COLLECTION_NAME = "tiki_library"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSIONS = 384

    def __init__(self, persist_directory: Optional[Path] = None):
        """Initialize ChromaDB client.

        Args:
            persist_directory: Path to ChromaDB storage. If None, uses config.

        Raises:
            ChromaClientError: If client initialization fails
        """
        config = get_config()

        if persist_directory is None:
            persist_directory = config.get_path("chroma_db")

        self.persist_directory = persist_directory
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[Collection] = None

        logger.info(f"Initializing ChromaDB client at {self.persist_directory}")
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize ChromaDB persistent client.

        Raises:
            ChromaClientError: If initialization fails
        """
        try:
            # Ensure directory exists
            self.persist_directory.mkdir(parents=True, exist_ok=True)

            # Create persistent client
            self._client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )

            logger.info("ChromaDB client initialized successfully")

        except Exception as e:
            raise ChromaClientError(f"Failed to initialize ChromaDB client: {e}")

    def get_collection(self) -> Collection:
        """Get or create the tiki_library collection.

        Returns:
            ChromaDB collection for music library

        Raises:
            ChromaClientError: If collection access fails
        """
        if self._collection is not None:
            return self._collection

        if self._client is None:
            raise ChromaClientError("ChromaDB client not initialized")

        try:
            # Try to get existing collection
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={
                    "description": "The Mixer music library",
                    "embedding_model": self.EMBEDDING_MODEL,
                    "embedding_dimensions": self.EMBEDDING_DIMENSIONS,
                }
            )

            count = self._collection.count()
            logger.info(f"Collection '{self.COLLECTION_NAME}' loaded with {count} songs")

            return self._collection

        except Exception as e:
            raise ChromaClientError(f"Failed to access collection: {e}")

    def reset_collection(self) -> None:
        """Delete and recreate the collection. USE WITH CAUTION.

        This permanently deletes all songs from the library while
        keeping the cached audio files intact.
        """
        if self._client is None:
            raise ChromaClientError("ChromaDB client not initialized")

        try:
            # Delete existing collection
            self._client.delete_collection(name=self.COLLECTION_NAME)
            logger.warning(f"Collection '{self.COLLECTION_NAME}' deleted")

            # Reset cached collection
            self._collection = None

            # Recreate collection
            self.get_collection()
            logger.info(f"Collection '{self.COLLECTION_NAME}' recreated")

        except Exception as e:
            raise ChromaClientError(f"Failed to reset collection: {e}")

    def get_stats(self) -> dict:
        """Get collection statistics.

        Returns:
            Dictionary with collection stats
        """
        collection = self.get_collection()

        try:
            count = collection.count()

            # Get sample metadata to analyze
            if count > 0:
                sample = collection.get(limit=min(100, count), include=["metadatas"])
                metadatas = sample["metadatas"]

                # Analyze genres
                all_genres = []
                for meta in metadatas:
                    if "genres" in meta:
                        all_genres.extend(meta["genres"])

                unique_genres = set(all_genres)

                # Analyze sources
                sources = [meta.get("source", "unknown") for meta in metadatas]
                youtube_count = sources.count("youtube")
                local_count = sources.count("local_file")

                # Analyze vocals
                has_vocals_count = sum(1 for meta in metadatas if meta.get("has_vocals", False))

                return {
                    "total_songs": count,
                    "unique_genres": len(unique_genres),
                    "top_genres": list(unique_genres)[:10],
                    "youtube_sources": youtube_count,
                    "local_sources": local_count,
                    "songs_with_vocals": has_vocals_count,
                    "songs_instrumental": count - has_vocals_count,
                }
            else:
                return {
                    "total_songs": 0,
                    "unique_genres": 0,
                    "top_genres": [],
                    "youtube_sources": 0,
                    "local_sources": 0,
                    "songs_with_vocals": 0,
                    "songs_instrumental": 0,
                }

        except Exception as e:
            raise ChromaClientError(f"Failed to get stats: {e}")

    def close(self) -> None:
        """Close ChromaDB client and persist data."""
        if self._client is not None:
            # ChromaDB auto-persists with PersistentClient
            logger.info("ChromaDB client closed")
            self._client = None
            self._collection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global client instance
_client_instance: Optional[ChromaClient] = None


def get_client(persist_directory: Optional[Path] = None) -> ChromaClient:
    """Get or create global ChromaDB client instance.

    Args:
        persist_directory: Path to ChromaDB storage. Only used on first call.

    Returns:
        Global ChromaClient instance
    """
    global _client_instance

    if _client_instance is None:
        _client_instance = ChromaClient(persist_directory)

    return _client_instance


def reset_client() -> None:
    """Reset global client instance. Useful for testing."""
    global _client_instance

    if _client_instance is not None:
        _client_instance.close()
        _client_instance = None
