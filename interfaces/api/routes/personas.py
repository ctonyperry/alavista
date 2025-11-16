"""Persona routes."""

from fastapi import APIRouter, HTTPException

from alavista.core.container import Container
from alavista.personas.persona_runtime import PersonaRuntimeError
from interfaces.api.schemas import (
    PersonaAnswerResponse,
    PersonaDetail,
    PersonaQuestionRequest,
    PersonaSummary,
)

router = APIRouter(tags=["personas"])


@router.get("/personas", response_model=list[PersonaSummary])
def list_personas():
    """List all available personas."""
    persona_registry = Container.get_persona_registry()
    personas = persona_registry.list_personas()

    return [
        PersonaSummary(
            id=persona.id,
            name=persona.name,
            description=persona.description,
        )
        for persona in personas
    ]


@router.get("/personas/{persona_id}", response_model=PersonaDetail)
def get_persona(persona_id: str):
    """Get detailed persona information."""
    persona_registry = Container.get_persona_registry()

    persona = persona_registry.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")

    return PersonaDetail(
        id=persona.id,
        name=persona.name,
        description=persona.description,
        entity_whitelist=persona.entity_whitelist,
        relation_whitelist=persona.relation_whitelist,
        tools_allowed=persona.tools_allowed,
    )


@router.post("/personas/{persona_id}/answer", response_model=PersonaAnswerResponse)
def ask_persona(persona_id: str, request: PersonaQuestionRequest):
    """Ask a persona a question."""
    corpus_store = Container.get_corpus_store()
    persona_runtime = Container.get_persona_runtime()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(request.corpus_id)
    if not corpus:
        raise HTTPException(
            status_code=404, detail=f"Corpus {request.corpus_id} not found"
        )

    # Execute persona query
    try:
        answer = persona_runtime.answer_question(
            persona_id=persona_id,
            question=request.question,
            corpus_id=request.corpus_id,
            k=request.k,
        )
    except PersonaRuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PersonaAnswerResponse(
        answer_text=answer.answer_text,
        evidence=answer.evidence,
        graph_evidence=answer.graph_evidence,
        reasoning_summary=answer.reasoning_summary,
        persona_id=answer.persona_id,
        disclaimers=answer.disclaimers,
        timestamp=answer.timestamp,
    )
