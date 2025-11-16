"""Tests for PersonaBase and DefaultPersona."""

from alavista.personas.models import PersonaAnswer, PersonaConfig, QuestionCategory
from alavista.personas.persona_base import DefaultPersona


def test_default_persona_categorize_structural():
    """Test categorization of structural questions."""
    config = PersonaConfig(
        name="Test",
        id="test",
        description="Test persona",
        tools_allowed=["semantic_search", "graph_neighbors"],
    )
    persona = DefaultPersona(config)

    structural_questions = [
        "Who is connected to John Smith?",
        "What is the relationship between Company A and Company B?",
        "Find the path from Person A to Person B",
        "Show me the network around this organization",
    ]

    for q in structural_questions:
        cat = persona.categorize_question(q)
        assert cat.category == "structural", f"Failed for: {q}"
        assert cat.confidence > 0


def test_default_persona_categorize_timeline():
    """Test categorization of timeline questions."""
    config = PersonaConfig(
        name="Test",
        id="test",
        description="Test persona",
    )
    persona = DefaultPersona(config)

    timeline_questions = [
        "What happened over time?",
        "Show me the timeline of events",
        "When did this occur?",
        "What changed in 2020?",
        "Describe the historical evolution",
    ]

    for q in timeline_questions:
        cat = persona.categorize_question(q)
        assert cat.category == "timeline", f"Failed for: {q}"


def test_default_persona_categorize_comparison():
    """Test categorization of comparison questions."""
    config = PersonaConfig(
        name="Test",
        id="test",
        description="Test persona",
    )
    persona = DefaultPersona(config)

    comparison_questions = [
        "Compare Person A to Person B",
        "What's the difference between these two?",
        "A vs B: which is better?",
        "Show similarities between X and Y",
    ]

    for q in comparison_questions:
        cat = persona.categorize_question(q)
        assert cat.category == "comparison", f"Failed for: {q}"


def test_default_persona_categorize_semantic_default():
    """Test that semantic is the default category."""
    config = PersonaConfig(
        name="Test",
        id="test",
        description="Test persona",
    )
    persona = DefaultPersona(config)

    semantic_questions = [
        "Tell me about corruption",
        "What is this document about?",
        "Find information on banking fraud",
    ]

    for q in semantic_questions:
        cat = persona.categorize_question(q)
        assert cat.category == "semantic", f"Failed for: {q}"


def test_default_persona_select_tools_structural():
    """Test tool selection for structural questions."""
    config = PersonaConfig(
        name="Test",
        id="test",
        description="Test persona",
        tools_allowed=[
            "semantic_search",
            "graph_find_entity",
            "graph_neighbors",
            "graph_paths",
        ],
    )
    persona = DefaultPersona(config)

    cat = QuestionCategory(category="structural", confidence=0.8)
    tools = persona.select_tools("Who is connected to X?", cat)

    assert "graph_find_entity" in tools
    assert "graph_neighbors" in tools
    # May also include search for context
    assert len(tools) > 0


def test_default_persona_select_tools_semantic():
    """Test tool selection for semantic questions."""
    config = PersonaConfig(
        name="Test",
        id="test",
        description="Test persona",
        tools_allowed=["semantic_search", "keyword_search"],
    )
    persona = DefaultPersona(config)

    cat = QuestionCategory(category="semantic", confidence=0.9)
    tools = persona.select_tools("What is corruption?", cat)

    assert "semantic_search" in tools or "keyword_search" in tools


def test_default_persona_format_answer():
    """Test answer formatting."""
    config = PersonaConfig(
        name="Test",
        id="test",
        description="Test persona",
    )
    persona = DefaultPersona(config)

    answer = PersonaAnswer(
        answer_text="This is the main answer.",
        evidence=[
            {"document_id": "doc1", "excerpt": "Some evidence text here"},
            {"document_id": "doc2", "excerpt": "More evidence"},
        ],
        graph_evidence=[
            {"type": "Person", "name": "John Doe", "id": "person1"},
        ],
        reasoning_summary="Used hybrid search",
        persona_id="test",
        disclaimers=["This is test data only."],
    )

    formatted = persona.format_answer(answer)

    assert "This is the main answer" in formatted
    assert "Evidence" in formatted
    assert "doc1" in formatted
    assert "Graph Connections" in formatted
    assert "John Doe" in formatted
    assert "Approach" in formatted
    assert "test data only" in formatted


def test_default_persona_respects_tool_whitelist():
    """Test that only allowed tools are selected."""
    config = PersonaConfig(
        name="Test",
        id="test",
        description="Test persona",
        tools_allowed=["semantic_search"],  # Only semantic search allowed
    )
    persona = DefaultPersona(config)

    # Even for a structural question, should not select graph tools
    cat = QuestionCategory(category="structural", confidence=0.8)
    tools = persona.select_tools("Who is connected?", cat)

    # Should only contain semantic_search since that's all that's allowed
    assert all(tool in ["semantic_search"] for tool in tools)
