import asyncio

import pytest

from alavista.vector import InMemoryVectorSearchService, VectorSearchError


def _run(coro):
    try:
        loop = asyncio.get_running_loop()
        # If we already have a running loop, schedule and gather manually.
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


def test_index_and_search_prioritizes_best_match():
    svc = InMemoryVectorSearchService()
    _run(
        svc.index_embeddings(
            "c1",
            [
                ("doc1", "chunk1", [1.0, 0.0]),
                ("doc2", "chunk2", [0.0, 1.0]),
            ],
        )
    )

    hits = _run(svc.search("c1", [0.9, 0.1], k=2))
    assert len(hits) == 2
    assert hits[0].document_id == "doc1"
    assert hits[0].score >= hits[1].score


def test_k_greater_than_available_caps_results():
    svc = InMemoryVectorSearchService()
    _run(
        svc.index_embeddings(
            "c2",
            [
                ("doc1", "chunk1", [1.0, 0.0]),
                ("doc2", "chunk2", [0.0, 1.0]),
            ],
        )
    )

    hits = _run(svc.search("c2", [1.0, 0.0], k=10))
    assert len(hits) == 2


def test_empty_corpus_returns_no_hits():
    svc = InMemoryVectorSearchService()
    hits = _run(svc.search("missing", [1.0], k=3))
    assert hits == []


def test_dimension_mismatch_errors():
    svc = InMemoryVectorSearchService()
    _run(svc.index_embeddings("c3", [("doc1", "chunk1", [1.0, 2.0, 3.0])]))

    with pytest.raises(VectorSearchError):
        _run(svc.index_embeddings("c3", [("doc2", "chunk2", [1.0, 2.0])]))

    with pytest.raises(VectorSearchError):
        _run(svc.search("c3", [1.0, 2.0], k=1))


def test_zero_vector_normalization_errors():
    svc = InMemoryVectorSearchService()
    with pytest.raises(VectorSearchError):
        _run(svc.index_embeddings("c4", [("doc1", "chunk1", [0.0, 0.0])]))


def test_duplicate_keys_error():
    svc = InMemoryVectorSearchService()
    _run(svc.index_embeddings("c5", [("doc1", "chunk1", [1.0, 0.0])]))
    with pytest.raises(VectorSearchError):
        _run(svc.index_embeddings("c5", [("doc1", "chunk1", [0.5, 0.5])]))
