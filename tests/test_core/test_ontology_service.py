import pytest

from alavista.ontology.service import OntologyError, OntologyService


def test_load_and_lookup(tmp_path):
    ontology_path = tmp_path / "ont.json"
    ontology_path.write_text(
        """{
            "version": "0.1",
            "entities": {
                "Person": {"aliases": ["Individual"]},
                "Document": {"aliases": ["Doc"]}
            },
            "relations": {
                "APPEARS_IN": {
                    "domain": ["Person"],
                    "range": ["Document"]
                }
            }
        }"""
    )
    svc = OntologyService(ontology_path)
    assert "Person" in svc.list_entity_types()
    assert svc.resolve_entity_type("doc") == "Document"
    assert svc.validate_relation("Person", "APPEARS_IN", "Document") is True
    assert svc.validate_relation("Document", "APPEARS_IN", "Person") is False


def test_missing_file_raises(tmp_path):
    with pytest.raises(OntologyError):
        OntologyService(tmp_path / "missing.json")
