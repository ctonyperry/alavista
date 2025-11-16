import uuid

import pytest

from alavista.graph.graph_service import GraphService
from alavista.graph.graph_store import SQLiteGraphStore
from alavista.graph.models import GraphEdge, GraphNode
from alavista.ontology.service import OntologyError, OntologyService


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "graph.db"
    return SQLiteGraphStore(db_path=db)


def _node(node_id: str, name: str, type_: str = "Person") -> GraphNode:
    return GraphNode(id=node_id, type=type_, name=name)


def _edge(edge_id: str, source: str, target: str, type_: str = "MENTIONED_WITH") -> GraphEdge:
    return GraphEdge(
        id=edge_id,
        type=type_,
        source=source,
        target=target,
        doc_id="doc1",
    )


def test_upsert_and_get_node(store):
    node = _node("n1", "Alice")
    store.upsert_node(node)
    retrieved = store.get_node("n1")
    assert retrieved is not None
    assert retrieved.name == "Alice"


def test_find_nodes_by_name(store):
    store.upsert_node(_node("n1", "Bob"))
    matches = store.find_nodes_by_name("bob")
    assert len(matches) == 1
    assert matches[0].id == "n1"


def test_add_and_get_edge(store):
    store.upsert_node(_node("n1", "Alice"))
    store.upsert_node(_node("n2", "Doc", type_="Document"))
    edge = _edge("e1", "n1", "n2", type_="APPEARS_IN")
    store.add_edge(edge)
    retrieved = store.get_edge("e1")
    assert retrieved is not None
    assert retrieved.type == "APPEARS_IN"


def test_neighbors_and_paths(store):
    store.upsert_node(_node("a", "A"))
    store.upsert_node(_node("b", "B"))
    store.upsert_node(_node("c", "C"))
    store.add_edge(_edge("e1", "a", "b"))
    store.add_edge(_edge("e2", "b", "c"))

    neighbors = store.neighbors("a", depth=2)
    ids = {n.id for n in neighbors}
    assert "b" in ids and "c" in ids

    paths = store.find_paths("a", "c", max_hops=3)
    assert ["a", "b", "c"] in paths


def test_graph_service_queries(store):
    store.upsert_node(_node("p1", "Alice"))
    store.upsert_node(_node("p2", "Bob"))
    store.add_edge(_edge("e1", "p1", "p2"))
    service = GraphService(store)

    found = service.find_entity("Alice")
    assert len(found) == 1

    neighbors = service.graph_neighbors("p1", depth=1)
    assert any(n.id == "p2" for n in neighbors.nodes)

    stats = service.graph_stats("p1")
    assert stats["degree"] == 1

    paths = service.graph_paths("p1", "p2")
    assert paths and paths[0].nodes == ["p1", "p2"]


def test_graph_service_with_ontology(tmp_path, store):
    ont_path = tmp_path / "ontology.json"
    ont_path.write_text(
        """{
            "entities": {
                "Person": {"aliases": []},
                "Document": {"aliases": []}
            },
            "relations": {
                "APPEARS_IN": {"domain": ["Person"], "range": ["Document"]}
            }
        }"""
    )
    ontology = OntologyService(ont_path)
    store.upsert_node(_node("p1", "Alice"))
    store.upsert_node(_node("d1", "Doc1", type_="Document"))

    svc = GraphService(store, ontology=ontology)
    svc.add_edge(_edge("e1", "p1", "d1", type_="APPEARS_IN"))

    with pytest.raises(OntologyError):
        svc.add_edge(_edge("e2", "d1", "p1", type_="APPEARS_IN"))

    with pytest.raises(OntologyError):
        svc.add_node(_node("x1", "Unknown", type_="Alien"))
