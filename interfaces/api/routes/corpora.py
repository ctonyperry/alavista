"""Corpus management routes."""

from fastapi import APIRouter, HTTPException

from alavista.core.container import Container
from alavista.core.models import Corpus
from interfaces.api.schemas import CorpusDetail, CorpusSummary, CreateCorpusRequest

router = APIRouter(tags=["corpora"])


@router.get("/corpora", response_model=list[CorpusSummary])
def list_corpora():
    """List all corpora."""
    corpus_store = Container.get_corpus_store()
    corpora = corpus_store.list_corpora()

    return [
        CorpusSummary(
            id=corpus.id,
            type=corpus.type,
            name=corpus.name,
            created_at=corpus.created_at,
            document_count=len(corpus_store.list_documents(corpus.id)),
        )
        for corpus in corpora
    ]


@router.get("/corpora/{corpus_id}", response_model=CorpusDetail)
def get_corpus(corpus_id: str):
    """Get detailed corpus information."""
    corpus_store = Container.get_corpus_store()
    corpus = corpus_store.get_corpus(corpus_id)

    if not corpus:
        raise HTTPException(status_code=404, detail=f"Corpus {corpus_id} not found")

    return CorpusDetail(
        id=corpus.id,
        type=corpus.type,
        name=corpus.name,
        created_at=corpus.created_at,
        document_count=len(corpus_store.list_documents(corpus.id)),
    )


@router.post("/corpora", response_model=CorpusDetail)
def create_corpus(request: CreateCorpusRequest):
    """Create a new corpus."""
    corpus_store = Container.get_corpus_store()

    # Generate ID from name (lowercase, replace spaces with underscores)
    corpus_id = request.name.lower().replace(" ", "_").replace("-", "_")

    # Check if corpus already exists
    existing = corpus_store.get_corpus(corpus_id)
    if existing:
        raise HTTPException(
            status_code=400, detail=f"Corpus with ID '{corpus_id}' already exists"
        )

    # Create corpus
    corpus = Corpus(
        id=corpus_id,
        type=request.type,
        name=request.name,
        description=request.description or f"{request.name} corpus",
        metadata=request.metadata,
    )

    corpus_store.create_corpus(corpus)

    return CorpusDetail(
        id=corpus.id,
        type=corpus.type,
        name=corpus.name,
        created_at=corpus.created_at,
        document_count=0,
    )
