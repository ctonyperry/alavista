"""Tests for PersonaRuntime."""

from unittest.mock import MagicMock, Mock

import pytest

from alavista.core.models import Corpus, Document, SearchResult
from alavista.personas.models import PersonaConfig
from alavista.personas.persona_base import DefaultPersona
from alavista.personas.persona_registry import PersonaRegistry
from alavista.personas.persona_runtime import PersonaRuntime, PersonaRuntimeError


@pytest.fixture
def mock_services():
    """Create mocked services for testing."""
    search_service = Mock()
    graph_service = Mock()
    corpus_store = Mock()

    # Mock corpus store to return a corpus
    corpus = Corpus(id="test_corpus", type="research", name="Test Corpus")
    corpus_store.get_corpus.return_value = corpus
    corpus_store.list_documents.return_value = [
        Document(
            id="doc1",
            corpus_id="test_corpus",
            text="Sample document content for testing.",
            content_hash="hash1",
            metadata={},
        )
    ]

    # Mock search results
    search_service.search_bm25.return_value = [
        SearchResult(
            doc_id="doc1",
            chunk_id="doc1::chunk_0",
            score=0.9,
            excerpt="Sample document content for testing.",
            metadata={},
        )
    ]

    # Mock graph results
    from alavista.graph.models import GraphNode
    graph_service.find_entity.return_value = [
        GraphNode(
            id="person1",
            type="Person",
            name="John Doe",
            aliases=[],
            metadata={},
        )
    ]

    return {
        "search_service": search_service,
        "graph_service": graph_service,
        "corpus_store": corpus_store,
    }


@pytest.fixture
def persona_registry():
    """Create a test persona registry."""
    from alavista.ontology.service import OntologyService
    from pathlib import Path
    import tempfile
    import json

    # Create temporary ontology
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
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(ontology_data, f)
        ontology_path = Path(f.name)

    ontology_service = OntologyService(ontology_path)

    registry = PersonaRegistry(
        ontology_service=ontology_service,
        allowed_tools=[
            "semantic_search",
            "keyword_search",
            "graph_find_entity",
            "graph_neighbors",
            "graph_paths",
        ],
    )

    # Add a test persona
    config = PersonaConfig(
        name="Test Persona",
        id="test_persona",
        description="A test persona",
        entity_whitelist=["Person", "Organization"],
        relation_whitelist=["APPEARS_IN"],
        tools_allowed=["semantic_search", "graph_find_entity"],
        safety={"disclaimers": ["Test disclaimer"]},
        reasoning={"approach": "Test approach"},
    )
    persona = DefaultPersona(config)
    registry._personas["test_persona"] = persona

    return registry


def test_persona_runtime_initialization(persona_registry, mock_services):
    """Test PersonaRuntime initialization."""
    runtime = PersonaRuntime(
        persona_registry=persona_registry,
        search_service=mock_services["search_service"],
        graph_service=mock_services["graph_service"],
        corpus_store=mock_services["corpus_store"],
    )

    assert runtime.persona_registry == persona_registry
    assert runtime.search_service == mock_services["search_service"]


def test_persona_runtime_answer_question(persona_registry, mock_services):
    """Test answering a question."""
    runtime = PersonaRuntime(
        persona_registry=persona_registry,
        search_service=mock_services["search_service"],
        graph_service=mock_services["graph_service"],
        corpus_store=mock_services["corpus_store"],
    )

    answer = runtime.answer_question(
        persona_id="test_persona",
        question="What is corruption?",
        corpus_id="test_corpus",
        k=10,
    )

    assert answer is not None
    assert answer.persona_id == "test_persona"
    assert answer.answer_text
    assert "Test disclaimer" in answer.disclaimers
    assert answer.reasoning_summary


def test_persona_runtime_unknown_persona(persona_registry, mock_services):
    """Test error handling for unknown persona."""
    runtime = PersonaRuntime(
        persona_registry=persona_registry,
        search_service=mock_services["search_service"],
        graph_service=mock_services["graph_service"],
        corpus_store=mock_services["corpus_store"],
    )

    with pytest.raises(PersonaRuntimeError, match="not found"):
        runtime.answer_question(
            persona_id="nonexistent",
            question="Test question",
            corpus_id="test_corpus",
        )


def test_persona_runtime_uses_correct_tools(persona_registry, mock_services):
    """Test that runtime uses persona-appropriate tools."""
    runtime = PersonaRuntime(
        persona_registry=persona_registry,
        search_service=mock_services["search_service"],
        graph_service=mock_services["graph_service"],
        corpus_store=mock_services["corpus_store"],
    )

    # Ask a semantic question
    answer = runtime.answer_question(
        persona_id="test_persona",
        question="What is corruption?",
        corpus_id="test_corpus",
    )

    # Should have called search service
    mock_services["search_service"].search_bm25.assert_called()

    # Evidence should be populated
    assert len(answer.evidence) > 0


def test_persona_runtime_evidence_deduplication(persona_registry, mock_services):
    """Test that evidence is deduplicated."""
    # Create duplicate results
    mock_services["search_service"].search_bm25.return_value = [
        SearchResult(
            doc_id="doc1",
            chunk_id="doc1::chunk_0",
            score=0.9,
            excerpt="Text 1",
            metadata={},
        ),
        SearchResult(
            doc_id="doc1",
            chunk_id="doc1::chunk_0",  # Duplicate
            score=0.8,
            excerpt="Text 1",
            metadata={},
        ),
    ]

    runtime = PersonaRuntime(
        persona_registry=persona_registry,
        search_service=mock_services["search_service"],
        graph_service=mock_services["graph_service"],
        corpus_store=mock_services["corpus_store"],
    )

    answer = runtime.answer_question(
        persona_id="test_persona",
        question="Test question",
        corpus_id="test_corpus",
    )

    # Should only have one evidence item after deduplication
    assert len(answer.evidence) == 1


def test_persona_runtime_no_evidence_response(persona_registry, mock_services):
    """Test response when no evidence is found."""
    # Mock empty results
    mock_services["search_service"].search_bm25.return_value = []
    mock_services["graph_service"].find_entity.return_value = []

    runtime = PersonaRuntime(
        persona_registry=persona_registry,
        search_service=mock_services["search_service"],
        graph_service=mock_services["graph_service"],
        corpus_store=mock_services["corpus_store"],
    )

    answer = runtime.answer_question(
        persona_id="test_persona",
        question="Obscure question with no results",
        corpus_id="test_corpus",
    )

    assert answer is not None
    assert "could not find sufficient evidence" in answer.answer_text.lower()
