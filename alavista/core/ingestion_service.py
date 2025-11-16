"""
IngestionService for processing and storing documents.

This module handles the ingestion of documents from various sources (text, files, URLs),
including normalization, deduplication, chunking, and (optionally) embedding + vector indexing.
"""

import asyncio
import hashlib
import uuid
from pathlib import Path
from typing import Any, Protocol

from alavista.core.chunking import chunk_text, normalize_text
from alavista.core.corpus_store import CorpusStore
from alavista.core.models import Chunk, Document
from alavista.vector import VectorSearchService


class EmbeddingServiceProtocol(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class IngestionError(Exception):
    """Base exception for ingestion errors."""

    pass


class UnsupportedFormatError(IngestionError):
    """Raised when attempting to ingest an unsupported file format."""

    pass


class IngestionService:
    """
    Service for ingesting documents from various sources.

    Handles text normalization, deduplication, chunking, and optional embedding + vector indexing.
    """

    def __init__(
        self,
        corpus_store: CorpusStore,
        min_chunk_size: int = 500,
        max_chunk_size: int = 1500,
        embedding_service: EmbeddingServiceProtocol | None = None,
        vector_search_service: VectorSearchService | None = None,
        persona_registry=None,
    ):
        """
        Initialize the ingestion service.

        Args:
            corpus_store: Storage backend for corpora and documents
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size in characters
            embedding_service: Optional embedding backend for chunk vectors
            vector_search_service: Optional vector index backend
            persona_registry: Optional PersonaRegistry for persona-specific ingestion
        """
        self.corpus_store = corpus_store
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.embedding_service = embedding_service
        self.vector_search_service = vector_search_service
        self.persona_registry = persona_registry

    def ingest_text(
        self,
        corpus_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Document, list[Chunk]]:
        """
        Ingest plain text into a corpus.

        Args:
            corpus_id: ID of the target corpus
            text: Text content to ingest
            metadata: Optional metadata (source_type, title, etc.)

        Returns:
            Tuple of (Document, list of Chunks)

        Raises:
            IngestionError: If corpus doesn't exist or ingestion fails
        """
        # Verify corpus exists
        if not self.corpus_store.get_corpus(corpus_id):
            raise IngestionError(f"Corpus '{corpus_id}' not found")

        # Normalize text
        normalized_text = normalize_text(text)

        if not normalized_text:
            raise IngestionError("Cannot ingest empty text")

        # Compute content hash for deduplication
        content_hash = self._compute_hash(normalized_text)

        # Check for duplicates
        existing_doc = self.corpus_store.find_by_hash(corpus_id, content_hash)
        if existing_doc:
            # Return existing document with its chunks
            chunks = self._create_chunks(existing_doc)
            return existing_doc, chunks

        # Create new document
        doc_metadata = metadata or {}
        doc_metadata.setdefault("source_type", "text")

        document = Document(
            id=str(uuid.uuid4()),
            corpus_id=corpus_id,
            text=normalized_text,
            content_hash=content_hash,
            metadata=doc_metadata,
        )

        # Store document
        self.corpus_store.add_document(document)

        # Create chunks
        chunks = self._create_chunks(document)

        # Optionally embed and index
        self._embed_and_index_chunks(document.corpus_id, chunks)

        return document, chunks

    def ingest_file(
        self,
        corpus_id: str,
        file_path: Path | str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Document, list[Chunk]]:
        """
        Ingest a file into a corpus.

        Currently supports:
        - Plain text (.txt)
        - Markdown (.md)

        Args:
            corpus_id: ID of the target corpus
            file_path: Path to the file
            metadata: Optional metadata

        Returns:
            Tuple of (Document, list of Chunks)

        Raises:
            IngestionError: If file cannot be read or format unsupported
            UnsupportedFormatError: If file format is not supported
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise IngestionError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise IngestionError(f"Not a file: {file_path}")

        # Check supported formats
        suffix = file_path.suffix.lower()
        supported_formats = {".txt", ".md"}

        if suffix not in supported_formats:
            raise UnsupportedFormatError(
                f"Unsupported file format: {suffix}. Supported: {supported_formats}"
            )

        # Read file content
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            try:
                text = file_path.read_text(encoding="latin-1")
            except Exception as e:
                raise IngestionError(f"Failed to read file {file_path}: {e}") from e
        except Exception as e:
            raise IngestionError(f"Failed to read file {file_path}: {e}") from e

        # Prepare metadata
        file_metadata = metadata or {}
        file_metadata.setdefault("source_type", "file")
        file_metadata.setdefault("source_path", str(file_path))
        file_metadata.setdefault("file_name", file_path.name)
        file_metadata.setdefault("file_format", suffix)

        # Ingest as text
        return self.ingest_text(corpus_id, text, file_metadata)

    def ingest_url(
        self,
        corpus_id: str,
        url: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Document, list[Chunk]]:
        """
        Ingest content from a URL.

        This is a placeholder for Phase 1. Full URL fetching and parsing
        will be implemented in future phases.

        Args:
            corpus_id: ID of the target corpus
            url: URL to fetch
            metadata: Optional metadata

        Returns:
            Tuple of (Document, list of Chunks)

        Raises:
            IngestionError: URL ingestion not yet implemented
        """
        raise IngestionError(
            "URL ingestion not yet implemented. "
            "This feature will be added in a future phase."
        )

    def ingest_persona_text(
        self,
        persona_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Document, list[Chunk]]:
        """
        Ingest plain text into a persona's manual corpus.

        Args:
            persona_id: ID of the persona
            text: Text content to ingest
            metadata: Optional metadata

        Returns:
            Tuple of (Document, list of Chunks)

        Raises:
            IngestionError: If PersonaRegistry not configured or persona not found
        """
        if not self.persona_registry:
            raise IngestionError("PersonaRegistry not configured for persona ingestion")

        # Get persona's manual corpus ID
        corpus_id = self.persona_registry.get_persona_corpus_id(persona_id)
        if not corpus_id:
            raise IngestionError(
                f"No manual corpus found for persona '{persona_id}'. "
                "Ensure auto_create_persona_corpora is enabled."
            )

        # Add persona_id to metadata
        persona_metadata = metadata or {}
        persona_metadata["persona_id"] = persona_id
        persona_metadata.setdefault("source_type", "persona_manual")

        # Delegate to standard ingestion
        return self.ingest_text(corpus_id, text, persona_metadata)

    def ingest_persona_file(
        self,
        persona_id: str,
        file_path: Path | str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Document, list[Chunk]]:
        """
        Ingest a file into a persona's manual corpus.

        Args:
            persona_id: ID of the persona
            file_path: Path to the file
            metadata: Optional metadata

        Returns:
            Tuple of (Document, list of Chunks)

        Raises:
            IngestionError: If PersonaRegistry not configured or persona not found
        """
        if not self.persona_registry:
            raise IngestionError("PersonaRegistry not configured for persona ingestion")

        # Get persona's manual corpus ID
        corpus_id = self.persona_registry.get_persona_corpus_id(persona_id)
        if not corpus_id:
            raise IngestionError(
                f"No manual corpus found for persona '{persona_id}'. "
                "Ensure auto_create_persona_corpora is enabled."
            )

        # Add persona_id to metadata
        persona_metadata = metadata or {}
        persona_metadata["persona_id"] = persona_id
        persona_metadata.setdefault("source_type", "persona_manual")

        # Delegate to standard ingestion
        return self.ingest_file(corpus_id, file_path, persona_metadata)

    def ingest_persona_url(
        self,
        persona_id: str,
        url: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Document, list[Chunk]]:
        """
        Ingest content from a URL into a persona's manual corpus.

        Args:
            persona_id: ID of the persona
            url: URL to fetch
            metadata: Optional metadata

        Returns:
            Tuple of (Document, list of Chunks)

        Raises:
            IngestionError: If PersonaRegistry not configured or persona not found
        """
        if not self.persona_registry:
            raise IngestionError("PersonaRegistry not configured for persona ingestion")

        # Get persona's manual corpus ID
        corpus_id = self.persona_registry.get_persona_corpus_id(persona_id)
        if not corpus_id:
            raise IngestionError(
                f"No manual corpus found for persona '{persona_id}'. "
                "Ensure auto_create_persona_corpora is enabled."
            )

        # Add persona_id to metadata
        persona_metadata = metadata or {}
        persona_metadata["persona_id"] = persona_id
        persona_metadata.setdefault("source_type", "persona_manual")

        # Delegate to standard ingestion
        return self.ingest_url(corpus_id, url, persona_metadata)

    def _compute_hash(self, text: str) -> str:
        """
        Compute SHA-256 hash of text for deduplication.

        Args:
            text: Text to hash

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _create_chunks(self, document: Document) -> list[Chunk]:
        """
        Create chunks from a document.

        Args:
            document: Document to chunk

        Returns:
            List of Chunk objects
        """
        chunk_infos = chunk_text(
            document.text,
            min_chunk_size=self.min_chunk_size,
            max_chunk_size=self.max_chunk_size,
        )

        chunks = []
        for i, chunk_info in enumerate(chunk_infos):
            chunk = Chunk(
                id=f"{document.id}::chunk_{i}",
                document_id=document.id,
                corpus_id=document.corpus_id,
                text=chunk_info.text,
                start_offset=chunk_info.start_offset,
                end_offset=chunk_info.end_offset,
                metadata={
                    "chunk_index": i,
                    "total_chunks": len(chunk_infos),
                },
            )
            chunks.append(chunk)

        return chunks

    def _embed_and_index_chunks(self, corpus_id: str, chunks: list[Chunk]) -> None:
        """Embed and index chunks if services are configured."""
        if not self.embedding_service or not self.vector_search_service:
            return
        texts = [chunk.text for chunk in chunks]
        try:
            vectors = self._run_coro(self.embedding_service.embed_texts(texts))
            items = [
                (chunk.document_id, chunk.id, vectors[i]) for i, chunk in enumerate(chunks)
            ]
            self._run_coro(self.vector_search_service.index_embeddings(corpus_id, items))
        except Exception as e:
            raise IngestionError("Failed to embed or index document chunks") from e

    def _run_coro(self, coro):
        """Run an async coroutine from sync context."""
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(coro, loop).result()
        except RuntimeError:
            return asyncio.run(coro)
