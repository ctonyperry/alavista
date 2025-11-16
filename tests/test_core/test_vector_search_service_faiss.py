import asyncio
from pathlib import Path

import pytest

from alavista.vector import (
    FaissVectorSearchService,
    VectorSearchError,
    _HAS_FAISS,
)


pytestmark = pytest.mark.skipif(not _HAS_FAISS, reason="faiss not installed")


def _run(coro):
    try:
        loop = asyncio.get_running_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


def test_faiss_index_and_search(tmp_path: Path):
    svc = FaissVectorSearchService(root_dir=tmp_path, normalize=True)
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


def test_faiss_persistence_round_trip(tmp_path: Path):
    svc = FaissVectorSearchService(root_dir=tmp_path, normalize=False)
    _run(svc.index_embeddings("c2", [("doc1", "chunk1", [1.0, 0.0])]))

    # Recreate service to force load from disk
    svc2 = FaissVectorSearchService(root_dir=tmp_path, normalize=False)
    hits = _run(svc2.search("c2", [1.0, 0.0], k=1))
    assert len(hits) == 1
    assert hits[0].document_id == "doc1"


def test_faiss_duplicate_keys_error(tmp_path: Path):
    svc = FaissVectorSearchService(root_dir=tmp_path)
    _run(svc.index_embeddings("c3", [("doc1", "chunk1", [1.0, 0.0])]))
    with pytest.raises(VectorSearchError):
        _run(svc.index_embeddings("c3", [("doc1", "chunk1", [1.0, 0.0])]))


def test_faiss_dimension_mismatch(tmp_path: Path):
    svc = FaissVectorSearchService(root_dir=tmp_path)
    _run(svc.index_embeddings("c4", [("doc1", "chunk1", [1.0, 2.0, 3.0])]))
    with pytest.raises(VectorSearchError):
        _run(svc.search("c4", [1.0, 2.0], k=1))
