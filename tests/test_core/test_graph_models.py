from datetime import datetime

from alavista.graph.models import GraphEdge, GraphNode


def test_graph_node_instantiation_and_defaults():
    node = GraphNode(id="n1", type="Person", name="Alice")
    assert node.id == "n1"
    assert node.aliases == []
    assert isinstance(node.created_at, datetime)


def test_graph_edge_instantiation_and_defaults():
    edge = GraphEdge(
        id="e1",
        type="APPEARS_IN",
        source="n1",
        target="d1",
        doc_id="doc1",
    )
    assert edge.confidence == 1.0
    assert isinstance(edge.created_at, datetime)
