"""
Knowledge graph module for Alavista.

This module implements the typed entity-relationship graph layer:
- Typed nodes (Person, Organization, Document, Event, etc.)
- Typed edges with provenance tracking
- Entity extraction from documents
- Entity resolution and deduplication
- Graph querying and traversal
- Confidence scoring for relationships
"""

from alavista.graph.graph_service import GraphService
from alavista.graph.graph_store import GraphStoreProtocol, SQLiteGraphStore
from alavista.graph.models import GraphEdge, GraphNeighborhood, GraphNode, GraphPath

__all__ = [
    "GraphService",
    "GraphStoreProtocol",
    "SQLiteGraphStore",
    "GraphNode",
    "GraphEdge",
    "GraphNeighborhood",
    "GraphPath",
]
