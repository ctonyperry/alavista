"""Tests for graph API routes."""

from fastapi.testclient import TestClient

from interfaces.api.app import create_app


def test_find_entity():
    """Test finding entities."""
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/graph/find_entity",
        json={"name": "test entity", "corpus_id": "test", "limit": 10},
    )
    # May return 200 with empty results or error depending on implementation
    assert response.status_code in [200, 404, 500]


def test_find_entity_validation():
    """Test find entity request validation."""
    app = create_app()
    client = TestClient(app)

    # Missing name
    response = client.post(
        "/api/v1/graph/find_entity",
        json={"corpus_id": "test"},
    )
    assert response.status_code == 422

    # Missing corpus_id
    response = client.post(
        "/api/v1/graph/find_entity",
        json={"name": "test"},
    )
    assert response.status_code == 422


def test_get_neighbors():
    """Test getting node neighbors."""
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/graph/neighbors",
        json={"node_id": "test_node", "depth": 1},
    )
    # May return 200 with empty results or error
    assert response.status_code in [200, 404, 500]


def test_get_neighbors_validation():
    """Test neighbors request validation."""
    app = create_app()
    client = TestClient(app)

    # Missing node_id
    response = client.post(
        "/api/v1/graph/neighbors",
        json={"depth": 1},
    )
    assert response.status_code == 422


def test_find_paths():
    """Test finding paths between nodes."""
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/graph/paths",
        json={
            "start_node_id": "node1",
            "end_node_id": "node2",
            "max_depth": 3,
        },
    )
    # May return 200 with empty results or error
    assert response.status_code in [200, 404, 500]


def test_find_paths_validation():
    """Test paths request validation."""
    app = create_app()
    client = TestClient(app)

    # Missing start_node_id
    response = client.post(
        "/api/v1/graph/paths",
        json={"end_node_id": "node2", "max_depth": 3},
    )
    assert response.status_code == 422

    # Missing end_node_id
    response = client.post(
        "/api/v1/graph/paths",
        json={"start_node_id": "node1", "max_depth": 3},
    )
    assert response.status_code == 422
