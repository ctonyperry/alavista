"""Tests for persona MCP tools."""

import pytest

from alavista.core.container import Container
from interfaces.mcp.persona_tools import list_personas_tool, persona_query_tool


def test_list_personas_tool():
    """Test listing personas."""
    result = list_personas_tool({})

    assert "personas" in result
    assert isinstance(result["personas"], list)

    # Should have at least the 3 personas we created
    assert len(result["personas"]) >= 3

    # Check structure
    if result["personas"]:
        persona = result["personas"][0]
        assert "id" in persona
        assert "name" in persona
        assert "description" in persona


def test_persona_query_tool_missing_persona_id():
    """Test error when persona_id is missing."""
    with pytest.raises(ValueError, match="persona_id is required"):
        persona_query_tool({"question": "test", "corpus_id": "test"})


def test_persona_query_tool_missing_question():
    """Test error when question is missing."""
    with pytest.raises(ValueError, match="question is required"):
        persona_query_tool({"persona_id": "test", "corpus_id": "test"})


def test_persona_query_tool_missing_corpus_id():
    """Test error when corpus_id is missing."""
    with pytest.raises(ValueError, match="corpus_id is required"):
        persona_query_tool({"persona_id": "test", "question": "test"})


def test_persona_query_tool_unknown_persona(tmp_path):
    """Test error with unknown persona."""
    from alavista.core.models import Corpus

    corpus_store = Container.create_corpus_store(
        Container.create_settings(data_dir=tmp_path)
    )

    # Create test corpus
    corpus = Corpus(id="test", type="research", name="Test")
    corpus_store.create_corpus(corpus)

    original_get = Container.get_corpus_store
    Container.get_corpus_store = lambda: corpus_store

    try:
        from alavista.personas.persona_runtime import PersonaRuntimeError

        with pytest.raises(PersonaRuntimeError, match="not found"):
            persona_query_tool({
                "persona_id": "nonexistent",
                "question": "What is corruption?",
                "corpus_id": "test",
            })
    finally:
        Container.get_corpus_store = original_get
