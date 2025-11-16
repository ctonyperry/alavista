import asyncio

import pytest

from alavista.core.corpus_store import SQLiteCorpusStore
from alavista.core.embeddings import DeterministicFallbackEmbeddingService
from alavista.core.models import Chunk, Corpus, Document
from alavista.search.search_service import SearchService
from alavista.vector import InMemoryVectorSearchService


def _run(coro):
    try:
        loop = asyncio.get_running_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    except RuntimeError:
        return asyncio.run(coro)


@pytest.fixture
def embed_service():
    return DeterministicFallbackEmbeddingService(dim=8)


@pytest.fixture
def vector_service():
    return InMemoryVectorSearchService(normalize=True)


@pytest.fixture
def corpus_store(tmp_path):
    db_path = tmp_path / "vec.db"
    return SQLiteCorpusStore(db_path)


@pytest.fixture
def sample_corpus(corpus_store):
    corpus = Corpus(id="c1", type="research", name="Corpus 1")
    return corpus_store.create_corpus(corpus)


@pytest.fixture
def chunks(corpus_store, sample_corpus):
    doc1 = Document(
        id="d1",
        corpus_id=sample_corpus.id,
        text="Cats are friendly animals that like to purr.",
        content_hash="h1",
        metadata={},
    )
    doc2 = Document(
        id="d2",
        corpus_id=sample_corpus.id,
        text="Quantum physics discusses particles and waves.",
        content_hash="h2",
        metadata={},
    )
    corpus_store.add_document(doc1)
    corpus_store.add_document(doc2)

    return [
        Chunk(
            id="d1::c0",
            document_id="d1",
            corpus_id=sample_corpus.id,
            text=doc1.text,
            start_offset=0,
            end_offset=len(doc1.text),
            metadata={},
        ),
        Chunk(
            id="d2::c0",
            document_id="d2",
            corpus_id=sample_corpus.id,
            text=doc2.text,
            start_offset=0,
            end_offset=len(doc2.text),
            metadata={},
        ),
    ]


@pytest.fixture
def search_service(corpus_store, vector_service, embed_service):
    return SearchService(
        corpus_store=corpus_store,
        vector_search_service=vector_service,
        embedding_service=embed_service,
    )


def _index_chunks(chunks, embed_service, vector_service):
    vectors = _run(embed_service.embed_texts([c.text for c in chunks]))
    items = [(c.document_id, c.id, vectors[i]) for i, c in enumerate(chunks)]
    _run(vector_service.index_embeddings(chunks[0].corpus_id, items))


class TestVectorAndHybridSearch:
    def test_vector_mode_returns_hits(self, search_service, chunks, vector_service, embed_service):
        _index_chunks(chunks, embed_service, vector_service)

        hits = search_service.search(
            corpus_id="c1",
            chunks=chunks,
            query="friendly cats",
            mode="vector",
            k=2,
        )

        assert len(hits) >= 1
        assert hits[0].doc_id == "d1"

    def test_hybrid_combines_scores(self, search_service, chunks, vector_service, embed_service):
        _index_chunks(chunks, embed_service, vector_service)

        hits = search_service.search(
            corpus_id="c1",
            chunks=chunks,
            query="friendly animals",
            mode="hybrid",
            k=2,
            w_bm25=0.6,
            w_vector=0.4,
        )

        assert len(hits) == 2
        # deterministic tie-break on doc_id/chunk_id if scores are equal
        assert hits[0].doc_id in {"d1", "d2"}

    def test_vector_mode_requires_backend(self, corpus_store):
        svc = SearchService(corpus_store=corpus_store, vector_search_service=None)
        with pytest.raises(ValueError):
            svc.search(corpus_id="missing", chunks=[], query="q", mode="vector")
