"""Search routes."""

from fastapi import APIRouter, HTTPException

from alavista.core.container import Container
from alavista.core.models import Chunk
from interfaces.api.schemas import SearchRequest, SearchResponse, SearchHit

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """Execute search query."""
    corpus_store = Container.get_corpus_store()
    search_service = Container.get_search_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(request.corpus_id)
    if not corpus:
        raise HTTPException(
            status_code=404, detail=f"Corpus {request.corpus_id} not found"
        )

    # Get documents and create chunks
    documents = corpus_store.list_documents(request.corpus_id)
    chunks = []
    for doc in documents:
        # Simplified: create one chunk per document
        chunk = Chunk(
            id=f"{doc.id}::chunk_0",
            document_id=doc.id,
            corpus_id=request.corpus_id,
            text=doc.text,
            start_offset=0,
            end_offset=len(doc.text),
            metadata={"chunk_index": 0, "total_chunks": 1},
        )
        chunks.append(chunk)

    # Execute search (only BM25 for now)
    results = search_service.search_bm25(
        corpus_id=request.corpus_id,
        chunks=chunks,
        query=request.query,
        k=request.k,
    )

    # Convert to response
    hits = [
        SearchHit(
            document_id=hit.doc_id,
            chunk_id=hit.chunk_id,
            score=hit.score,
            excerpt=hit.excerpt,
            metadata=hit.metadata,
        )
        for hit in results
    ]

    return SearchResponse(
        hits=hits,
        total_hits=len(hits),
        query=request.query,
        mode=request.mode,
    )
