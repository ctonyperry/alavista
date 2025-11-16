"""Tests for ingestion API routes."""

from fastapi.testclient import TestClient

from alavista.core.container import Container
from alavista.core.models import Corpus
from interfaces.api.app import create_app


def test_ingest_text_corpus_not_found(tmp_path):
    """Test ingesting text with non-existent corpus."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/ingest/text",
            json={
                "corpus_id": "nonexistent",
                "text": "Test document",
                "metadata": {},
            },
        )
        assert response.status_code == 404
    finally:
        Container.get_corpus_store = original_get


def test_ingest_text_validation():
    """Test ingest text request validation."""
    app = create_app()
    client = TestClient(app)

    # Missing text
    response = client.post(
        "/api/v1/ingest/text",
        json={"corpus_id": "test"},
    )
    assert response.status_code == 422

    # Missing corpus_id
    response = client.post(
        "/api/v1/ingest/text",
        json={"text": "test"},
    )
    assert response.status_code == 422


def test_ingest_url_corpus_not_found(tmp_path):
    """Test ingesting URL with non-existent corpus."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/ingest/url",
            json={
                "corpus_id": "nonexistent",
                "url": "https://example.com",
                "metadata": {},
            },
        )
        assert response.status_code == 404
    finally:
        Container.get_corpus_store = original_get


def test_ingest_url_validation():
    """Test ingest URL request validation."""
    app = create_app()
    client = TestClient(app)

    # Missing url
    response = client.post(
        "/api/v1/ingest/url",
        json={"corpus_id": "test"},
    )
    assert response.status_code == 422


def test_ingest_file_corpus_not_found(tmp_path):
    """Test ingesting file with non-existent corpus."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/ingest/file",
            json={
                "corpus_id": "nonexistent",
                "file_path": "/path/to/file.txt",
                "metadata": {},
            },
        )
        assert response.status_code == 404
    finally:
        Container.get_corpus_store = original_get


def test_ingest_file_validation():
    """Test ingest file request validation."""
    app = create_app()
    client = TestClient(app)

    # Missing file_path
    response = client.post(
        "/api/v1/ingest/file",
        json={"corpus_id": "test"},
    )
    assert response.status_code == 422


def test_ingest_text_success(tmp_path):
    """Test successful text ingestion."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )
    ingestion_service = Container.create_ingestion_service(corpus_store)

    # Create test corpus
    corpus = Corpus(id="test", type="research", name="Test")
    corpus_store.create_corpus(corpus)

    original_corpus = Container.get_corpus_store
    original_ingest = Container.get_ingestion_service
    Container.get_corpus_store = lambda: corpus_store
    Container.get_ingestion_service = lambda: ingestion_service

    try:
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/ingest/text",
            json={
                "corpus_id": "test",
                "text": "This is a test document for ingestion.",
                "metadata": {"source": "test"},
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "document_id" in data
        assert "chunk_count" in data
        assert data["chunk_count"] > 0
    finally:
        Container.get_corpus_store = original_corpus
        Container.get_ingestion_service = original_ingest
