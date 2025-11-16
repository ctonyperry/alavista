"""Tests for corpus API routes."""

from fastapi.testclient import TestClient

from alavista.core.container import Container
from alavista.core.models import Corpus
from interfaces.api.app import create_app


def test_list_corpora_empty(tmp_path):
    """Test listing corpora when none exist."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/corpora")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        Container.get_corpus_store = original_get


def test_list_corpora_with_data(tmp_path):
    """Test listing corpora when some exist."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    # Create test corpora
    corpus1 = Corpus(id="test1", type="research", name="Test 1")
    corpus2 = Corpus(id="test2", type="research", name="Test 2")
    corpus_store.create_corpus(corpus1)
    corpus_store.create_corpus(corpus2)

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/corpora")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] in ["test1", "test2"]
        assert "name" in data[0]
        assert "document_count" in data[0]
    finally:
        Container.get_corpus_store = original_get


def test_get_corpus_success(tmp_path):
    """Test getting a specific corpus."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    corpus = Corpus(id="test", type="research", name="Test Corpus")
    corpus_store.create_corpus(corpus)

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/corpora/test")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "test"
        assert data["name"] == "Test Corpus"
        assert data["type"] == "research"
    finally:
        Container.get_corpus_store = original_get


def test_get_corpus_not_found(tmp_path):
    """Test getting a non-existent corpus."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/corpora/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        Container.get_corpus_store = original_get
