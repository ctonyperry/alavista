"""MCP tools for Graph-guided RAG operations."""

from alavista.core.container import Container


def graph_rag_tool(args: dict) -> dict:
    """Execute graph-guided RAG to answer a question.

    Args:
        args: dict with required keys:
            - question: The question to answer
            - persona_id: ID of the persona to use
            - corpus_id: Optional corpus to search (if None, uses global)
            - k: Optional number of results (default 20)

    Returns:
        dict with answer_text, evidence_docs, graph_context, and retrieval_summary

    Raises:
        ValueError: If required args missing
    """
    question = args.get("question")
    persona_id = args.get("persona_id")
    corpus_id = args.get("corpus_id")
    k = int(args.get("k", 20))

    if not question:
        raise ValueError("question is required")
    if not persona_id:
        raise ValueError("persona_id is required")

    # Get services
    graph_rag_service = Container.get_graph_rag_service()
    persona_registry = Container.get_persona_registry()

    # Get persona
    persona = persona_registry.get_persona(persona_id)
    if not persona:
        raise ValueError(f"Persona '{persona_id}' not found")

    # Execute graph-guided RAG
    result = graph_rag_service.answer(
        question=question,
        persona=persona,
        topic_corpus_id=corpus_id,
        k=k,
    )

    # Convert to dict
    return {
        "answer_text": result.answer_text,
        "evidence_docs": [
            {
                "document_id": ev.document_id,
                "chunk_id": ev.chunk_id,
                "score": ev.score,
                "excerpt": ev.excerpt,
                "metadata": ev.metadata,
            }
            for ev in result.evidence_docs
        ],
        "graph_context": [
            {
                "context_type": ctx.context_type,
                "nodes": ctx.nodes,
                "edges": ctx.edges,
                "summary": ctx.summary,
            }
            for ctx in result.graph_context
        ],
        "retrieval_summary": result.retrieval_summary,
        "persona_id": result.persona_id,
        "timestamp": result.timestamp.isoformat(),
    }
