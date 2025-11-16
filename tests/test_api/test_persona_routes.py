"""Tests for persona API routes."""

from fastapi.testclient import TestClient

from alavista.core.container import Container
from alavista.core.models import Corpus
from interfaces.api.app import create_app


def test_list_personas():
    """Test listing personas."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/personas")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3  # Should have at least our 3 default personas

    if data:
        assert "id" in data[0]
        assert "name" in data[0]
        assert "description" in data[0]


def test_get_persona_success():
    """Test getting a specific persona."""
    app = create_app()
    client = TestClient(app)

    # Get list first to find a valid ID
    list_response = client.get("/api/v1/personas")
    personas = list_response.json()
    if not personas:
        return  # Skip if no personas

    persona_id = personas[0]["id"]

    response = client.get(f"/api/v1/personas/{persona_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == persona_id
    assert "name" in data
    assert "entity_whitelist" in data
    assert "relation_whitelist" in data
    assert "tools_allowed" in data


def test_get_persona_not_found():
    """Test getting a non-existent persona."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/personas/nonexistent")
    assert response.status_code == 404


def test_ask_persona_corpus_not_found(tmp_path):
    """Test asking persona with non-existent corpus."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        app = create_app()
        client = TestClient(app)

        # Get a valid persona ID
        list_response = client.get("/api/v1/personas")
        personas = list_response.json()
        if not personas:
            return

        persona_id = personas[0]["id"]

        response = client.post(
            f"/api/v1/personas/{persona_id}/answer",
            json={
                "question": "What is this about?",
                "corpus_id": "nonexistent",
                "k": 10,
            },
        )
        assert response.status_code == 404
    finally:
        Container.get_corpus_store = original_get


def test_ask_persona_validation():
    """Test persona Q&A request validation."""
    app = create_app()
    client = TestClient(app)

    # Get a valid persona ID
    list_response = client.get("/api/v1/personas")
    personas = list_response.json()
    if not personas:
        return

    persona_id = personas[0]["id"]

    # Missing question
    response = client.post(
        f"/api/v1/personas/{persona_id}/answer",
        json={"corpus_id": "test"},
    )
    assert response.status_code == 422

    # Missing corpus_id
    response = client.post(
        f"/api/v1/personas/{persona_id}/answer",
        json={"question": "test"},
    )
    assert response.status_code == 422


def test_ask_persona_success(tmp_path):
    """Test successful persona Q&A."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    # Create test corpus
    corpus = Corpus(id="test", type="research", name="Test")
    corpus_store.create_corpus(corpus)

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        app = create_app()
        client = TestClient(app)

        # Get a valid persona ID
        list_response = client.get("/api/v1/personas")
        personas = list_response.json()
        if not personas:
            return

        persona_id = personas[0]["id"]

        response = client.post(
            f"/api/v1/personas/{persona_id}/answer",
            json={
                "question": "What is corruption?",
                "corpus_id": "test",
                "k": 10,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "answer_text" in data
        assert "evidence" in data
        assert "graph_evidence" in data
        assert "reasoning_summary" in data
        assert data["persona_id"] == persona_id
    finally:
        Container.get_corpus_store = original_get
