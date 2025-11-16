"""Tests for search MCP tools."""

import pytest

from alavista.core.container import Container
from alavista.core.models import Corpus, Document
from interfaces.mcp.search_tools import keyword_search_tool, semantic_search_tool


def test_semantic_search_tool_missing_corpus_id():
    """Test error when corpus_id is missing."""
    with pytest.raises(ValueError, match="corpus_id is required"):
        semantic_search_tool({"query": "test"})


def test_semantic_search_tool_missing_query():
    """Test error when query is missing."""
    with pytest.raises(ValueError, match="query is required"):
        semantic_search_tool({"corpus_id": "test"})


def test_semantic_search_tool_corpus_not_found(tmp_path):
    """Test error when corpus doesn't exist."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        with pytest.raises(ValueError, match="Corpus .* not found"):
            semantic_search_tool({"corpus_id": "nonexistent", "query": "test"})
    finally:
        Container.get_corpus_store = original_get


def test_semantic_search_tool_success(tmp_path):
    """Test successful search execution."""
    # Setup
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

    # Mock singletons
    original_corpus = Container.get_corpus_store
    original_search = Container.get_search_service
    Container.get_corpus_store = lambda: corpus_store
    Container.get_search_service = lambda: search_service

    try:
        result = semantic_search_tool(
            {"corpus_id": "test", "query": "machine learning", "k": 5}
        )

        assert "hits" in result
        assert isinstance(result["hits"], list)

        if result["hits"]:
            hit = result["hits"][0]
            assert "document_id" in hit
            assert "chunk_id" in hit
            assert "score" in hit
            assert "excerpt" in hit
    finally:
        Container.get_corpus_store = original_corpus
        Container.get_search_service = original_search


def test_keyword_search_tool_is_alias():
    """Test that keyword_search is an alias for semantic_search."""
    # Both should work with same args
    args = {"corpus_id": "test", "query": "test"}

    # They should both require the same parameters
    with pytest.raises(ValueError):
        keyword_search_tool({"query": "test"})

    with pytest.raises(ValueError):
        keyword_search_tool({"corpus_id": "test"})
