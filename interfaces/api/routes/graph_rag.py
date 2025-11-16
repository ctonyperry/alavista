"""Graph RAG routes."""

from fastapi import APIRouter, HTTPException

from alavista.core.container import Container
from interfaces.api.schemas import (
    GraphRAGContext,
    GraphRAGEvidenceItem,
    GraphRAGRequest,
    GraphRAGResponse,
)

router = APIRouter(tags=["graph_rag"])


@router.post("/graph_rag", response_model=GraphRAGResponse)
def execute_graph_rag(request: GraphRAGRequest):
    """Execute graph-guided RAG to answer a question."""
    graph_rag_service = Container.get_graph_rag_service()
    persona_registry = Container.get_persona_registry()

    # Verify persona exists
    persona = persona_registry.get_persona(request.persona_id)
    if not persona:
        raise HTTPException(
            status_code=404, detail=f"Persona {request.persona_id} not found"
        )

    # Execute graph-guided RAG
    try:
        result = graph_rag_service.answer(
            question=request.question,
            persona=persona,
            topic_corpus_id=request.corpus_id,
            k=request.k,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph RAG failed: {str(e)}")

    # Convert to response format
    return GraphRAGResponse(
        answer_text=result.answer_text,
        evidence_docs=[
            GraphRAGEvidenceItem(
                document_id=ev.document_id,
                chunk_id=ev.chunk_id,
                score=ev.score,
                excerpt=ev.excerpt,
                metadata=ev.metadata,
            )
            for ev in result.evidence_docs
        ],
        graph_context=[
            GraphRAGContext(
                context_type=ctx.context_type,
                nodes=ctx.nodes,
                edges=ctx.edges,
                summary=ctx.summary,
            )
            for ctx in result.graph_context
        ],
        retrieval_summary=result.retrieval_summary,
        persona_id=result.persona_id,
        timestamp=result.timestamp,
    )
