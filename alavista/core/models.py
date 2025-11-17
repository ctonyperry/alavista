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


class SearchResult(BaseModel):
    """
    Represents a single search result from BM25 or other search methods.

    Contains the matched chunk/document, its relevance score, an excerpt for display,
    and associated metadata.
    """

    doc_id: str = Field(..., description="ID of the matched document")
    chunk_id: str = Field(..., description="ID of the matched chunk")
    score: float = Field(..., description="Relevance score (higher is better)")
    excerpt: str = Field(..., description="Text excerpt from the matched chunk")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Document metadata (source_type, source_path, etc.)"
    )


# ============================================================================
# Agent/Run Models (Phase 12)
# ============================================================================


class Step(BaseModel):
    """
    Represents a planned action within an investigation run.

    A step describes what action should be taken (e.g., search, graph traversal)
    and any parameters needed to execute it.
    """

    action: str = Field(..., description="Action type (search, graph_find, graph_neighbors, etc.)")
    target: str | None = Field(None, description="Target corpus_id, entity_id, or other identifier")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Action-specific parameters (query, depth, etc.)"
    )


class StepExecution(BaseModel):
    """
    Represents the execution status and result of a planned step.

    Tracks when a step started/completed, its status, and any results or errors.
    """

    step_index: int = Field(..., description="Index of the step in the plan")
    status: Literal["pending", "running", "completed", "error"] = Field(
        ..., description="Current execution status"
    )
    started_at: datetime | None = Field(None, description="When execution started")
    completed_at: datetime | None = Field(None, description="When execution completed")
    result: dict[str, Any] | None = Field(None, description="Execution result data")
    error: str | None = Field(None, description="Error message if status is 'error'")


class Evidence(BaseModel):
    """
    Represents evidence collected during an investigation run.

    Evidence items are document chunks that support findings, along with
    metadata about which step produced them and their relevance.
    """

    document_id: str = Field(..., description="ID of the source document")
    chunk_id: str | None = Field(None, description="ID of the specific chunk")
    excerpt: str = Field(..., description="Text excerpt from the evidence")
    score: float = Field(..., description="Relevance score")
    source_step: int = Field(..., description="Step index that produced this evidence")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata (source, date, etc.)"
    )


class Run(BaseModel):
    """
    Represents an investigation run - an agent executing a plan to answer a question.

    A run includes the user's task/question, a planned sequence of steps, execution
    status for each step, and collected evidence.
    """

    id: str = Field(..., description="Unique identifier for the run")
    status: Literal["created", "running", "completed", "error", "cancelled"] = Field(
        ..., description="Overall run status"
    )
    task: str = Field(..., description="User's question or investigation goal")
    persona_id: str = Field(..., description="Persona conducting the investigation")
    corpus_id: str | None = Field(None, description="Primary corpus to investigate (optional)")
    plan: list[Step] = Field(default_factory=list, description="Planned sequence of actions")
    steps: list[StepExecution] = Field(
        default_factory=list, description="Execution status for each planned step"
    )
    evidence: list[Evidence] = Field(
        default_factory=list, description="Evidence collected during execution"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )
