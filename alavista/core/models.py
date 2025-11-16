"""
Core data models for Alavista.

This module defines the foundational data structures used across the system,
including Corpus, Document, and Chunk models.
"""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Corpus(BaseModel):
    """
    Represents a logical collection of documents.

    A corpus can be associated with a persona (manual corpus) or research topic,
    or be a general collection.
    """

    id: str = Field(..., description="Unique identifier for the corpus")
    type: Literal["persona_manual", "research", "global"] = Field(
        ..., description="Type of corpus"
    )
    persona_id: str | None = Field(None, description="Persona ID for persona_manual type")
    topic_id: str | None = Field(None, description="Topic ID for research corpora")
    name: str = Field(..., description="Human-readable name")
    description: str | None = Field(None, description="Optional description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )


class Document(BaseModel):
    """
    Represents a single document within a corpus.

    Documents are stored with their full text, content hash for deduplication,
    and metadata about their source.
    """

    id: str = Field(..., description="Unique identifier for the document")
    corpus_id: str = Field(..., description="ID of the corpus this document belongs to")
    text: str = Field(..., description="Full text content of the document")
    content_hash: str = Field(..., description="SHA-256 hash of normalized text for deduplication")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata (source_type, source_path, title, etc.)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )


class Chunk(BaseModel):
    """
    Represents a chunk of text from a document.

    Documents are split into chunks for embedding and indexing. Each chunk
    maintains a reference to its parent document and position within it.
    """

    id: str = Field(..., description="Unique identifier for the chunk (e.g., doc_id::chunk_0)")
    document_id: str = Field(..., description="ID of the parent document")
    corpus_id: str = Field(..., description="ID of the corpus")
    text: str = Field(..., description="Text content of this chunk")
    start_offset: int = Field(..., description="Character offset where chunk starts in document")
    end_offset: int = Field(..., description="Character offset where chunk ends in document")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Chunk-specific metadata"
    )
