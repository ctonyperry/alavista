"""MCP tools for search operations."""

from alavista.core.container import Container
from alavista.core.models import Chunk


def semantic_search_tool(args: dict) -> dict:
    """Execute semantic (hybrid) search over a corpus.

    Args:
        args: dict with 'corpus_id', 'query', and optional 'k' (default 20)

    Returns:
        dict with 'hits' list containing search results

    Raises:
        ValueError: If required args missing or corpus not found
    """
    corpus_id = args.get("corpus_id")
    query = args.get("query")
    k = int(args.get("k", 20))

    if not corpus_id:
        raise ValueError("corpus_id is required")
    if not query:
        raise ValueError("query is required")

    corpus_store = Container.get_corpus_store()
    search_service = Container.get_search_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(corpus_id)
    if not corpus:
        raise ValueError(f"Corpus '{corpus_id}' not found")

    # Get documents and create chunks
    documents = corpus_store.list_documents(corpus_id)
    chunks = []
    for doc in documents:
        # Simplified: create one chunk per document
        chunk = Chunk(
            id=f"{doc.id}::chunk_0",
            document_id=doc.id,
            corpus_id=corpus_id,
            text=doc.text,
            start_offset=0,
            end_offset=len(doc.text),
            metadata={"chunk_index": 0, "total_chunks": 1},
        )
        chunks.append(chunk)

    # Execute search
    results = search_service.search_bm25(
        corpus_id=corpus_id,
        chunks=chunks,
        query=query,
        k=k,
    )

    return {
        "hits": [
            {
                "document_id": result.doc_id,
                "chunk_id": result.chunk_id,
                "score": result.score,
                "excerpt": result.excerpt,
                "metadata": result.metadata,
            }
            for result in results
        ]
    }


def keyword_search_tool(args: dict) -> dict:
    """Execute keyword (BM25) search over a corpus.

    This is an alias for semantic_search_tool with mode='bm25'.
    Currently both use BM25 search.

    Args:
        args: dict with 'corpus_id', 'query', and optional 'k' (default 20)

    Returns:
        dict with 'hits' list containing search results
    """
    return semantic_search_tool(args)
