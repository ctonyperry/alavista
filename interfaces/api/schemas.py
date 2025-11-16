"""Pydantic schemas for HTTP API requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Corpus Schemas
# ============================================================================


class CorpusSummary(BaseModel):
    """Summary of a corpus for listing."""

    id: str
    type: str
    name: str
    created_at: datetime
    document_count: int = 0


class CorpusDetail(BaseModel):
    """Detailed corpus information."""

    id: str
    type: str
    name: str
    created_at: datetime
    document_count: int


# ============================================================================
# Search Schemas
# ============================================================================


class SearchRequest(BaseModel):
    """Request for search endpoint."""

    corpus_id: str
    query: str
    mode: str = Field(default="hybrid", pattern="^(bm25|vector|hybrid)$")
    k: int = Field(default=20, ge=1, le=100)


class SearchHit(BaseModel):
    """Single search result hit."""

    document_id: str
    chunk_id: str
    score: float
    excerpt: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Response from search endpoint."""

    hits: list[SearchHit]
    total_hits: int
    query: str
    mode: str


# ============================================================================
# Persona Schemas
# ============================================================================


class PersonaSummary(BaseModel):
    """Summary of a persona for listing."""

    id: str
    name: str
    description: str


class PersonaDetail(BaseModel):
    """Detailed persona information."""

    id: str
    name: str
    description: str
    entity_whitelist: list[str]
    relation_whitelist: list[str]
    tools_allowed: list[str]


class PersonaQuestionRequest(BaseModel):
    """Request for persona Q&A."""

    question: str
    corpus_id: str
    k: int = Field(default=10, ge=1, le=50)


class PersonaAnswerResponse(BaseModel):
    """Response from persona Q&A."""

    answer_text: str
    evidence: list[dict[str, Any]]
    graph_evidence: list[dict[str, Any]]
    reasoning_summary: str
    persona_id: str
    disclaimers: list[str]
    timestamp: datetime


# ============================================================================
# Graph Schemas
# ============================================================================


class GraphFindEntityRequest(BaseModel):
    """Request to find entities by name."""

    name: str
    corpus_id: str
    limit: int = Field(default=10, ge=1, le=50)


class GraphNode(BaseModel):
    """Graph node representation."""

    id: str
    type: str
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Graph edge representation."""

    source_id: str
    target_id: str
    relation_type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphFindEntityResponse(BaseModel):
    """Response from find entity."""

    nodes: list[GraphNode]


class GraphNeighborsRequest(BaseModel):
    """Request for node neighbors."""

    node_id: str
    depth: int = Field(default=1, ge=1, le=3)


class GraphNeighborsResponse(BaseModel):
    """Response from neighbors query."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class GraphPathsRequest(BaseModel):
    """Request for paths between nodes."""

    start_node_id: str
    end_node_id: str
    max_depth: int = Field(default=3, ge=1, le=5)


class GraphPathsResponse(BaseModel):
    """Response from paths query."""

    paths: list[list[str]]


# ============================================================================
# Ontology Schemas
# ============================================================================


class EntityTypeSummary(BaseModel):
    """Summary of an entity type."""

    name: str
    description: str


class RelationTypeSummary(BaseModel):
    """Summary of a relation type."""

    name: str
    description: str
    domain: list[str]
    range: list[str]


class EntityTypeDetail(BaseModel):
    """Detailed entity type information."""

    name: str
    description: str
    properties: dict[str, Any] = Field(default_factory=dict)


class RelationTypeDetail(BaseModel):
    """Detailed relation type information."""

    name: str
    description: str
    domain: list[str]
    range: list[str]
    properties: dict[str, Any] = Field(default_factory=dict)


class OntologyListResponse(BaseModel):
    """Response for listing ontology types."""

    entity_types: list[EntityTypeSummary] | None = None
    relation_types: list[RelationTypeSummary] | None = None


# ============================================================================
# Ingestion Schemas
# ============================================================================


class IngestTextRequest(BaseModel):
    """Request to ingest text."""

    corpus_id: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestURLRequest(BaseModel):
    """Request to ingest from URL."""

    corpus_id: str
    url: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestFileRequest(BaseModel):
    """Request to ingest a file."""

    corpus_id: str
    file_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    """Response from ingestion."""

    document_id: str
    chunk_count: int
