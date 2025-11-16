"""Tests for search API routes."""

from fastapi.testclient import TestClient

from alavista.core.container import Container
from alavista.core.models import Corpus, Document
from interfaces.api.app import create_app


def test_search_corpus_not_found(tmp_path):
    """Test search with non-existent corpus."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/search",
            json={
                "corpus_id": "nonexistent",
                "query": "test query",
                "mode": "hybrid",
                "k": 10,
            },
        )
        assert response.status_code == 404
    finally:
        Container.get_corpus_store = original_get


def test_search_success(tmp_path):
    """Test successful search execution."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )
    search_service = Container.create_search_service(corpus_store)

    # Create corpus and document
    corpus = Corpus(id="test", type="research", name="Test")
    corpus_store.create_corpus(corpus)

    doc = Document(
        id="doc1",
        corpus_id="test",
        text="This is a test document about machine learning.",
        content_hash="hash1",
        metadata={},
    )
    corpus_store.add_document(doc)

    original_corpus = Container.get_corpus_store
    original_search = Container.get_search_service
    Container.get_corpus_store = lambda: corpus_store
    Container.get_search_service = lambda: search_service

    try:
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/search",
            json={
                "corpus_id": "test",
                "query": "machine learning",
                "mode": "hybrid",
                "k": 10,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "hits" in data
        assert "total_hits" in data
        assert data["query"] == "machine learning"
        assert data["mode"] == "hybrid"
    finally:
        Container.get_corpus_store = original_corpus
        Container.get_search_service = original_search


def test_search_validation():
    """Test search request validation."""
    app = create_app()
    client = TestClient(app)

    # Missing query
    response = client.post(
        "/api/v1/search",
        json={"corpus_id": "test", "mode": "hybrid"},
    )
    assert response.status_code == 422

    # Invalid mode
    response = client.post(
        "/api/v1/search",
        json={"corpus_id": "test", "query": "test", "mode": "invalid"},
    )
    assert response.status_code == 422
