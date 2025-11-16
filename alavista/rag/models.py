"""Models for Graph-guided RAG."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """Evidence from document retrieval."""

    document_id: str
    chunk_id: str
    score: float
    excerpt: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphContext(BaseModel):
    """Graph context (paths, neighborhoods, relationships)."""

    context_type: str  # "path", "neighborhood", "entity"
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""


class GraphRAGResult(BaseModel):
    """Result from graph-guided RAG."""

    answer_text: str
    evidence_docs: list[EvidenceItem] = Field(default_factory=list)
    graph_context: list[GraphContext] = Field(default_factory=list)
    retrieval_summary: str
    persona_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
