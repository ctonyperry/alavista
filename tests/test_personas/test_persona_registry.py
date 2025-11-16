"""Tests for PersonaRegistry."""

import tempfile
from pathlib import Path

import pytest
import yaml

from alavista.ontology.service import OntologyService
from alavista.personas.persona_registry import PersonaRegistry, PersonaValidationError


@pytest.fixture
def ontology_service(tmp_path):
    """Create a test ontology service."""
    ontology_data = {
        "version": "0.1",
        "entities": {
            "Person": {"description": "A person"},
            "Organization": {"description": "An organization"},
            "Document": {"description": "A document"},
        },
        "relations": {
            "APPEARS_IN": {
                "description": "Appears in",
                "domain": ["Person", "Organization"],
                "range": ["Document"],
            },
            "MENTIONED_WITH": {
                "description": "Mentioned with",
                "domain": ["Person", "Organization"],
                "range": ["Person", "Organization"],
            },
        },
    }
    ontology_path = tmp_path / "ontology.json"
    with open(ontology_path, "w") as f:
        import json

        json.dump(ontology_data, f)

    return OntologyService(ontology_path)


@pytest.fixture
def test_persona_yaml():
    """Sample persona YAML data."""
    return {
        "name": "Test Persona",
        "id": "test_persona",
        "description": "A test persona",
        "entity_whitelist": ["Person", "Organization"],
        "relation_whitelist": ["APPEARS_IN"],
        "tools_allowed": ["semantic_search", "graph_find_entity"],
        "strength_rules": {"strong": ["APPEARS_IN"]},
        "corpus": {},
        "reasoning": {"approach": "Test approach"},
        "safety": {"disclaimers": ["Test disclaimer"], "provenance_required": True},
    }


def test_persona_registry_initialization(ontology_service):
    """Test basic registry initialization."""
    registry = PersonaRegistry(
        ontology_service=ontology_service, allowed_tools=["semantic_search"]
    )
    assert registry.list_personas() == []
    assert registry.list_persona_ids() == []


def test_persona_registry_load_from_file(ontology_service, test_persona_yaml, tmp_path):
    """Test loading a persona from a YAML file."""
    registry = PersonaRegistry(
        ontology_service=ontology_service,
        allowed_tools=["semantic_search", "graph_find_entity"],
    )

    # Write YAML file
    yaml_file = tmp_path / "test_persona.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(test_persona_yaml, f)

    # Load persona
    persona = registry.load_from_file(yaml_file)

    assert persona.id == "test_persona"
    assert persona.name == "Test Persona"
    assert "Person" in persona.entity_whitelist
    assert "APPEARS_IN" in persona.relation_whitelist


def test_persona_registry_load_all(ontology_service, test_persona_yaml, tmp_path):
    """Test loading all personas from a directory."""
    registry = PersonaRegistry(
        ontology_service=ontology_service,
        allowed_tools=["semantic_search", "graph_find_entity"],
    )

    # Create multiple YAML files
    for i in range(3):
        persona_data = test_persona_yaml.copy()
        persona_data["id"] = f"persona_{i}"
        persona_data["name"] = f"Persona {i}"

        yaml_file = tmp_path / f"persona_{i}.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(persona_data, f)

    # Load all
    registry.load_all(tmp_path)

    assert len(registry.list_personas()) == 3
    assert "persona_0" in registry.list_persona_ids()
    assert "persona_1" in registry.list_persona_ids()
    assert "persona_2" in registry.list_persona_ids()


def test_persona_registry_get_persona(ontology_service, test_persona_yaml, tmp_path):
    """Test retrieving a persona by ID."""
    registry = PersonaRegistry(
        ontology_service=ontology_service,
        allowed_tools=["semantic_search", "graph_find_entity"],
    )

    yaml_file = tmp_path / "test_persona.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(test_persona_yaml, f)

    registry.load_from_file(yaml_file)

    persona = registry.get_persona("test_persona")
    assert persona is not None
    assert persona.id == "test_persona"

    # Test non-existent persona
    assert registry.get_persona("nonexistent") is None


def test_persona_registry_validate_unknown_entity_type(ontology_service, tmp_path):
    """Test validation fails for unknown entity types."""
    registry = PersonaRegistry(
        ontology_service=ontology_service, allowed_tools=["semantic_search"]
    )

    invalid_persona = {
        "name": "Invalid",
        "id": "invalid",
        "description": "Has unknown entity type",
        "entity_whitelist": ["UnknownType"],  # This doesn't exist in ontology
        "relation_whitelist": [],
        "tools_allowed": [],
    }

    yaml_file = tmp_path / "invalid.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(invalid_persona, f)

    with pytest.raises(PersonaValidationError, match="Unknown entity type"):
        registry.load_from_file(yaml_file)


def test_persona_registry_validate_unknown_relation_type(ontology_service, tmp_path):
    """Test validation fails for unknown relation types."""
    registry = PersonaRegistry(
        ontology_service=ontology_service, allowed_tools=["semantic_search"]
    )

    invalid_persona = {
        "name": "Invalid",
        "id": "invalid",
        "description": "Has unknown relation type",
        "entity_whitelist": ["Person"],
        "relation_whitelist": ["UNKNOWN_RELATION"],  # Doesn't exist
        "tools_allowed": [],
    }

    yaml_file = tmp_path / "invalid.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(invalid_persona, f)

    with pytest.raises(PersonaValidationError, match="Unknown relation type"):
        registry.load_from_file(yaml_file)


def test_persona_registry_validate_unknown_tool(ontology_service, tmp_path):
    """Test validation fails for unknown tools."""
    registry = PersonaRegistry(
        ontology_service=ontology_service, allowed_tools=["semantic_search"]
    )

    invalid_persona = {
        "name": "Invalid",
        "id": "invalid",
        "description": "Has unknown tool",
        "entity_whitelist": ["Person"],
        "relation_whitelist": ["APPEARS_IN"],
        "tools_allowed": ["unknown_tool"],  # Not in allowed_tools
    }

    yaml_file = tmp_path / "invalid.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(invalid_persona, f)

    with pytest.raises(PersonaValidationError, match="Unknown tool"):
        registry.load_from_file(yaml_file)


def test_persona_registry_get_persona_summary(ontology_service, test_persona_yaml, tmp_path):
    """Test getting a persona summary."""
    registry = PersonaRegistry(
        ontology_service=ontology_service,
        allowed_tools=["semantic_search", "graph_find_entity"],
    )

    yaml_file = tmp_path / "test_persona.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(test_persona_yaml, f)

    registry.load_from_file(yaml_file)

    summary = registry.get_persona_summary("test_persona")
    assert summary is not None
    assert summary["id"] == "test_persona"
    assert summary["name"] == "Test Persona"
    assert summary["description"] == "A test persona"
    assert "Person" in summary["entity_types"]
    assert "semantic_search" in summary["tools"]


def test_persona_registry_list_persona_summaries(ontology_service, test_persona_yaml, tmp_path):
    """Test listing all persona summaries."""
    registry = PersonaRegistry(
        ontology_service=ontology_service,
        allowed_tools=["semantic_search", "graph_find_entity"],
    )

    # Create two personas
    for i in range(2):
        persona_data = test_persona_yaml.copy()
        persona_data["id"] = f"persona_{i}"
        yaml_file = tmp_path / f"persona_{i}.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(persona_data, f)

    registry.load_all(tmp_path)

    summaries = registry.list_persona_summaries()
    assert len(summaries) == 2
    assert all("id" in s and "name" in s for s in summaries)
