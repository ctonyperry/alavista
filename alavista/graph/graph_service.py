from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import List

from alavista.graph.graph_store import GraphStoreProtocol
from alavista.graph.models import (
    GraphEdge,
    GraphNeighborhood,
    GraphNode,
    GraphPath,
)
from alavista.ontology.service import OntologyService, OntologyError


@dataclass
class GraphService:
    """
    High-level graph API on top of GraphStore.
    """

    store: GraphStoreProtocol
    ontology: OntologyService | None = None

    def add_node(self, node: GraphNode) -> GraphNode:
        if self.ontology:
            if not self.ontology.resolve_entity_type(node.type):
                raise OntologyError(f"Unknown entity type: {node.type}")
        return self.store.upsert_node(node)

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        if self.ontology:
            subject = self.store.get_node(edge.source)
            target = self.store.get_node(edge.target)
            if not subject or not target:
                raise OntologyError("Edge references missing nodes")
            if not self.ontology.validate_relation(subject.type, edge.type, target.type):
                raise OntologyError(
                    f"Invalid relation: {edge.type} for {subject.type} -> {target.type}"
                )
        return self.store.add_edge(edge)

    def find_entity(self, name: str) -> List[GraphNode]:
        return self.store.find_nodes_by_name(name)

    def graph_neighbors(self, node_id: str, depth: int = 1) -> GraphNeighborhood:
        center = self.store.get_node(node_id)
        if center is None:
            return GraphNeighborhood(center_node=node_id, nodes=[], edges=[], stats={})

        nodes = self.store.neighbors(node_id, depth=depth)
        edges = self.store.edges_from(node_id) + self.store.edges_to(node_id)

        stats = self._compute_stats(center, edges)
        return GraphNeighborhood(center_node=node_id, nodes=[center] + nodes, edges=edges, stats=stats)

    def graph_paths(self, start_id: str, end_id: str, max_hops: int = 4) -> List[GraphPath]:
        paths = self.store.find_paths(start_id, end_id, max_hops=max_hops)
        return [GraphPath(nodes=p) for p in paths]

    def graph_stats(self, node_id: str) -> dict:
        node = self.store.get_node(node_id)
        if node is None:
            return {}
        edges_out = self.store.edges_from(node_id)
        edges_in = self.store.edges_to(node_id)
        relations = Counter([e.type for e in edges_out + edges_in])
        connected_docs = len({e.doc_id for e in edges_out + edges_in})
        return {
            "degree": len(edges_out) + len(edges_in),
            "in_degree": len(edges_in),
            "out_degree": len(edges_out),
            "relations_by_type": dict(relations),
            "connected_docs": connected_docs,
        }

    def _compute_stats(self, node: GraphNode, edges: list[GraphEdge]) -> dict:
        relations = Counter([e.type for e in edges])
        return {
            "degree": len(edges),
            "relations_by_type": dict(relations),
        }
