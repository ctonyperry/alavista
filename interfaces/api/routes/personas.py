"""Persona routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from alavista.core.container import Container
from alavista.core.ingestion_service import IngestionError
from alavista.personas.persona_runtime import PersonaRuntimeError
from interfaces.api.schemas import (
    PersonaAnswerResponse,
    PersonaDetail,
    PersonaIngestFileRequest,
    PersonaIngestResponse,
    PersonaIngestTextRequest,
    PersonaIngestURLRequest,
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


@router.post("/personas/{persona_id}/ingest/text", response_model=PersonaIngestResponse)
def ingest_persona_text(persona_id: str, request: PersonaIngestTextRequest):
    """Ingest text into a persona's manual corpus."""
    persona_registry = Container.get_persona_registry()
    ingestion_service = Container.get_ingestion_service()

    # Verify persona exists
    persona = persona_registry.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")

    # Ingest text
    try:
        document, chunks = ingestion_service.ingest_persona_text(
            persona_id=persona_id,
            text=request.text,
            metadata=request.metadata,
        )
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get corpus ID
    corpus_id = persona_registry.get_persona_corpus_id(persona_id)

    return PersonaIngestResponse(
        document_id=document.id,
        chunk_count=len(chunks),
        persona_id=persona_id,
        corpus_id=corpus_id,
    )


@router.post("/personas/{persona_id}/ingest/url", response_model=PersonaIngestResponse)
def ingest_persona_url(persona_id: str, request: PersonaIngestURLRequest):
    """Ingest content from a URL into a persona's manual corpus."""
    persona_registry = Container.get_persona_registry()
    ingestion_service = Container.get_ingestion_service()

    # Verify persona exists
    persona = persona_registry.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")

    # Ingest URL
    try:
        document, chunks = ingestion_service.ingest_persona_url(
            persona_id=persona_id,
            url=request.url,
            metadata=request.metadata,
        )
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get corpus ID
    corpus_id = persona_registry.get_persona_corpus_id(persona_id)

    return PersonaIngestResponse(
        document_id=document.id,
        chunk_count=len(chunks),
        persona_id=persona_id,
        corpus_id=corpus_id,
    )


@router.post("/personas/{persona_id}/ingest/file", response_model=PersonaIngestResponse)
def ingest_persona_file(persona_id: str, request: PersonaIngestFileRequest):
    """Ingest a file into a persona's manual corpus."""
    persona_registry = Container.get_persona_registry()
    ingestion_service = Container.get_ingestion_service()

    # Verify persona exists
    persona = persona_registry.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona {persona_id} not found")

    # Ingest file
    try:
        document, chunks = ingestion_service.ingest_persona_file(
            persona_id=persona_id,
            file_path=Path(request.file_path),
            metadata=request.metadata,
        )
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get corpus ID
    corpus_id = persona_registry.get_persona_corpus_id(persona_id)

    return PersonaIngestResponse(
        document_id=document.id,
        chunk_count=len(chunks),
        persona_id=persona_id,
        corpus_id=corpus_id,
    )
