"""Tests for ontology API routes."""

from fastapi.testclient import TestClient

from interfaces.api.app import create_app


def test_list_entity_types():
    """Test listing entity types."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/ontology/entities")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    # Should have core types from ontology
    assert len(data) > 0

    if data:
        assert "name" in data[0]
        assert "description" in data[0]


def test_list_relation_types():
    """Test listing relation types."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/ontology/relations")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    if data:
        assert "name" in data[0]
        assert "description" in data[0]
        assert "domain" in data[0]
        assert "range" in data[0]


def test_get_entity_type_success():
    """Test getting a specific entity type."""
    app = create_app()
    client = TestClient(app)

    # Get list first to find a valid type
    list_response = client.get("/api/v1/ontology/entities")
    entity_types = list_response.json()

    if not entity_types:
        return

    type_name = entity_types[0]["name"]

    response = client.get(f"/api/v1/ontology/entity/{type_name}")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == type_name
    assert "description" in data
    assert "properties" in data


def test_get_entity_type_not_found():
    """Test getting a non-existent entity type."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/ontology/entity/NonExistentType")
    assert response.status_code == 404


def test_get_relation_type_success():
    """Test getting a specific relation type."""
    app = create_app()
    client = TestClient(app)

    # Get list first to find a valid type
    list_response = client.get("/api/v1/ontology/relations")
    relation_types = list_response.json()

    if not relation_types:
        return

    type_name = relation_types[0]["name"]

    response = client.get(f"/api/v1/ontology/relation/{type_name}")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == type_name
    assert "description" in data
    assert "domain" in data
    assert "range" in data
    assert "properties" in data


def test_get_relation_type_not_found():
    """Test getting a non-existent relation type."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/ontology/relation/NonExistentRelation")
    assert response.status_code == 404
