import pytest

from alavista.graph.extraction import filter_entities, filter_relations
from alavista.ontology.service import OntologyService


@pytest.fixture
def ontology(tmp_path):
    ont_path = tmp_path / "ont.json"
    ont_path.write_text(
        """{
            "entities": {
                "Person": {"aliases": ["Individual"]},
                "Organization": {"aliases": ["Org"]},
                "Document": {"aliases": ["Doc"]}
            },
            "relations": {
                "APPEARS_IN": {
                    "domain": ["Person", "Organization"],
                    "range": ["Document"]
                },
                "MENTIONED_WITH": {
                    "domain": ["Person", "Organization"],
                    "range": ["Person", "Organization"]
                }
            }
        }"""
    )
    return OntologyService(ont_path)


def test_filter_entities_validates_types(ontology):
    entities = [
        {"id": "e1", "type": "Person", "name": "Alice"},
        {"id": "e2", "type": "Alien", "name": "Zorg"},
        {"id": "e3", "type": "Org", "name": "ACME"},
    ]
    kept = filter_entities(entities, ontology)
    assert len(kept) == 2
    assert {e["id"] for e in kept} == {"e1", "e3"}
    # alias should resolve to canonical
    assert any(e["type"] == "Organization" for e in kept)


def test_filter_relations_validates_domain_range(ontology):
    relations = [
        {"id": "r1", "type": "APPEARS_IN", "subject_type": "Person", "object_type": "Document"},
        {"id": "r2", "type": "APPEARS_IN", "subject_type": "Document", "object_type": "Person"},
        {"id": "r3", "type": "MENTIONED_WITH", "subject_type": "Person", "object_type": "Organization"},
    ]
    kept = filter_relations(relations, ontology)
    assert {r["id"] for r in kept} == {"r1", "r3"}
