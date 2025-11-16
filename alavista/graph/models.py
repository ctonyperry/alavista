from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, List

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    type: str  # e.g., "Person", "Organization", "Document"
    name: str
    aliases: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GraphEdge(BaseModel):
    id: str
    type: str  # e.g., "APPEARS_IN", "MENTIONED_WITH"
    source: str  # node_id
    target: str  # node_id
    doc_id: str
    chunk_id: str | None = None
    excerpt: str | None = None
    page: int | None = None
    confidence: float = 1.0
    extraction_method: str = "unknown"  # "regex", "llm", "hybrid", etc.
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GraphNeighborhood(BaseModel):
    center_node: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    stats: dict[str, Any] = Field(default_factory=dict)


class GraphPath(BaseModel):
    nodes: list[str]
