"""Ingestion routes."""

from fastapi import APIRouter, HTTPException

from alavista.core.container import Container
from interfaces.api.schemas import (
    IngestFileRequest,
    IngestResponse,
    IngestTextRequest,
    IngestURLRequest,
)

router = APIRouter(tags=["ingestion"])


@router.post("/ingest/text", response_model=IngestResponse)
def ingest_text(request: IngestTextRequest):
    """Ingest text into a corpus."""
    corpus_store = Container.get_corpus_store()
    ingestion_service = Container.get_ingestion_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(request.corpus_id)
    if not corpus:
        raise HTTPException(
            status_code=404, detail=f"Corpus {request.corpus_id} not found"
        )

    # Ingest text (returns tuple of (Document, list[Chunk]))
    document, chunks = ingestion_service.ingest_text(
        corpus_id=request.corpus_id,
        text=request.text,
        metadata=request.metadata,
    )

    return IngestResponse(
        document_id=document.id,
        chunk_count=len(chunks),
    )


@router.post("/ingest/url", response_model=IngestResponse)
def ingest_url(request: IngestURLRequest):
    """Ingest content from a URL into a corpus."""
    corpus_store = Container.get_corpus_store()
    ingestion_service = Container.get_ingestion_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(request.corpus_id)
    if not corpus:
        raise HTTPException(
            status_code=404, detail=f"Corpus {request.corpus_id} not found"
        )

    # Ingest URL (returns tuple of (Document, list[Chunk]))
    document, chunks = ingestion_service.ingest_url(
        corpus_id=request.corpus_id,
        url=request.url,
        metadata=request.metadata,
    )

    return IngestResponse(
        document_id=document.id,
        chunk_count=len(chunks),
    )


@router.post("/ingest/file", response_model=IngestResponse)
def ingest_file(request: IngestFileRequest):
    """Ingest a file into a corpus."""
    corpus_store = Container.get_corpus_store()
    ingestion_service = Container.get_ingestion_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(request.corpus_id)
    if not corpus:
        raise HTTPException(
            status_code=404, detail=f"Corpus {request.corpus_id} not found"
        )

    # Ingest file (returns tuple of (Document, list[Chunk]))
    document, chunks = ingestion_service.ingest_file(
        corpus_id=request.corpus_id,
        file_path=request.file_path,
        metadata=request.metadata,
    )

    return IngestResponse(
        document_id=document.id,
        chunk_count=len(chunks),
    )
