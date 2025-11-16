"""Corpus management routes."""

from fastapi import APIRouter, HTTPException

from alavista.core.container import Container
from interfaces.api.schemas import CorpusDetail, CorpusSummary

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
