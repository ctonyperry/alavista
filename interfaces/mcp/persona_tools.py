"""MCP tools for persona operations."""

from alavista.core.container import Container


def list_personas_tool(args: dict) -> dict:
    """List all available personas (analysis profiles).

    Args:
        args: Empty dict (no arguments required)

    Returns:
        dict with 'personas' list containing persona summaries
    """
    persona_registry = Container.get_persona_registry()
    summaries = persona_registry.list_persona_summaries()

    return {"personas": summaries}


def persona_query_tool(args: dict) -> dict:
    """Execute a persona-scoped question answering pass.

    Args:
        args: dict with 'persona_id', 'question', 'corpus_id', and optional 'k' (default 20)

    Returns:
        dict with answer, evidence, graph_evidence, and reasoning_summary

    Raises:
        ValueError: If required args missing
    """
    persona_id = args.get("persona_id")
    question = args.get("question")
    corpus_id = args.get("corpus_id")
    k = int(args.get("k", 20))

    if not persona_id:
        raise ValueError("persona_id is required")
    if not question:
        raise ValueError("question is required")
    if not corpus_id:
        raise ValueError("corpus_id is required")

    persona_runtime = Container.get_persona_runtime()

    answer = persona_runtime.answer_question(
        persona_id=persona_id,
        question=question,
        corpus_id=corpus_id,
        k=k,
    )

    return {
        "answer_text": answer.answer_text,
        "evidence": answer.evidence,
        "graph_evidence": answer.graph_evidence,
        "reasoning_summary": answer.reasoning_summary,
        "persona_id": answer.persona_id,
        "disclaimers": answer.disclaimers,
        "timestamp": answer.timestamp.isoformat(),
    }
