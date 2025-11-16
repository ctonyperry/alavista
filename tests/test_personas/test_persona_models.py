"""Tests for persona models."""

from alavista.personas.models import PersonaAnswer, PersonaConfig, QuestionCategory


def test_persona_config_instantiation():
    """Test creating a PersonaConfig."""
    config = PersonaConfig(
        name="Test Persona",
        id="test_persona",
        description="A test persona",
        entity_whitelist=["Person", "Organization"],
        relation_whitelist=["APPEARS_IN"],
        tools_allowed=["semantic_search"],
    )
    assert config.name == "Test Persona"
    assert config.id == "test_persona"
    assert "Person" in config.entity_whitelist
    assert "semantic_search" in config.tools_allowed


def test_persona_config_defaults():
    """Test PersonaConfig defaults."""
    config = PersonaConfig(
        name="Minimal",
        id="minimal",
        description="Minimal config",
    )
    assert config.entity_whitelist == []
    assert config.relation_whitelist == []
    assert config.tools_allowed == []
    assert config.corpus == {}


def test_question_category():
    """Test QuestionCategory model."""
    cat = QuestionCategory(
        category="structural",
        confidence=0.8,
        reasoning="Contains relationship keywords",
    )
    assert cat.category == "structural"
    assert cat.confidence == 0.8
    assert "relationship" in cat.reasoning


def test_persona_answer():
    """Test PersonaAnswer model."""
    answer = PersonaAnswer(
        answer_text="This is the answer",
        evidence=[{"doc_id": "doc1", "excerpt": "text"}],
        graph_evidence=[{"type": "Person", "name": "John"}],
        reasoning_summary="Used semantic search",
        persona_id="test_persona",
        disclaimers=["This is a test"],
    )
    assert answer.answer_text == "This is the answer"
    assert len(answer.evidence) == 1
    assert len(answer.graph_evidence) == 1
    assert answer.persona_id == "test_persona"
    assert answer.timestamp is not None
