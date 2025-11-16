"""Tests for corpora MCP tools."""

import pytest

from alavista.core.container import Container
from alavista.core.models import Corpus
from interfaces.mcp.corpora_tools import get_corpus_tool, list_corpora_tool


def test_list_corpora_tool_empty(tmp_path):
    """Test listing corpora when none exist."""
    # Create isolated corpus store
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    # Mock the singleton to use test store
    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        result = list_corpora_tool({})
        assert "corpora" in result
        assert result["corpora"] == []
    finally:
        Container.get_corpus_store = original_get


def test_list_corpora_tool_with_corpora(tmp_path):
    """Test listing corpora when some exist."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    # Create test corpora
    corpus1 = Corpus(id="test1", type="research", name="Test 1")
    corpus2 = Corpus(id="test2", type="research", name="Test 2")
    corpus_store.create_corpus(corpus1)
    corpus_store.create_corpus(corpus2)

    # Mock singleton
    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        result = list_corpora_tool({})
        assert "corpora" in result
        assert len(result["corpora"]) == 2

        # Check structure
        corpus_data = result["corpora"][0]
        assert "id" in corpus_data
        assert "type" in corpus_data
        assert "name" in corpus_data
        assert "created_at" in corpus_data
    finally:
        Container.get_corpus_store = original_get


def test_get_corpus_tool_missing_id():
    """Test error when corpus_id is missing."""
    with pytest.raises(ValueError, match="corpus_id is required"):
        get_corpus_tool({})


def test_get_corpus_tool_not_found(tmp_path):
    """Test error when corpus doesn't exist."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        with pytest.raises(ValueError, match="Corpus .* not found"):
            get_corpus_tool({"corpus_id": "nonexistent"})
    finally:
        Container.get_corpus_store = original_get


def test_get_corpus_tool_success(tmp_path):
    """Test successfully getting corpus details."""
    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    # Create test corpus
    corpus = Corpus(id="test", type="research", name="Test Corpus")
    corpus_store.create_corpus(corpus)

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        result = get_corpus_tool({"corpus_id": "test"})

        assert "corpus" in result
        corpus_data = result["corpus"]
        assert corpus_data["id"] == "test"
        assert corpus_data["name"] == "Test Corpus"
        assert corpus_data["type"] == "research"
        assert "document_count" in corpus_data
        assert corpus_data["document_count"] == 0
    finally:
        Container.get_corpus_store = original_get
