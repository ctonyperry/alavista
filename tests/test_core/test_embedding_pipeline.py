import asyncio
from dataclasses import dataclass

import pytest

from alavista.core.embeddings.pipeline import EmbeddingPipeline
from alavista.core.models import Chunk, Corpus, Document


class FakeEmbeddingService:
    def __init__(self):
        self.calls: list[list[str]] = []

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[float(len(t))] for t in texts]


class FakeVectorSearchService:
    def __init__(self):
        self.indexed: list[tuple[str, str, list[float]]] = []

    async def index_embeddings(self, corpus_id: str, items):
        for item in items:
            self.indexed.append(item)

    async def search(self, corpus_id: str, query_vector, k: int = 20):
        return []


@dataclass
class FakeCorpusStore:
    corpus: Corpus
    documents: list[Document]

    def get_corpus(self, corpus_id: str):
        return self.corpus if self.corpus.id == corpus_id else None

    def list_documents(self, corpus_id: str):
        if corpus_id != self.corpus.id:
            return []
        return self.documents


def _run(coro):
    try:
        loop = asyncio.get_running_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    except RuntimeError:
        return asyncio.run(coro)


def test_pipeline_embeds_only_missing_chunks():
    corpus = Corpus(id="c1", type="research", name="C1")
    doc = Document(
        id="d1",
        corpus_id="c1",
        text="alpha beta gamma",
        content_hash="h1",
        metadata={},
    )
    store = FakeCorpusStore(corpus=corpus, documents=[doc])
    embed = FakeEmbeddingService()
    vector = FakeVectorSearchService()
    pipeline = EmbeddingPipeline(store, embed, vector, batch_size=2)

    # pre-mark one chunk as embedded
    existing_chunk = Chunk(
        id="d1::chunk_0",
        document_id="d1",
        corpus_id="c1",
        text="alpha beta gamma",
        start_offset=0,
        end_offset=16,
        metadata={"embedded": True},
    )
    embedded = pipeline.embed_chunks("c1", [existing_chunk], force=False)
    assert embedded == 0
    assert not vector.indexed


def test_pipeline_embed_corpus_builds_chunks_and_marks_metadata():
    corpus = Corpus(id="c2", type="research", name="C2")
    doc = Document(
        id="d2",
        corpus_id="c2",
        text="short text for chunking",
        content_hash="h2",
        metadata={},
    )
    store = FakeCorpusStore(corpus=corpus, documents=[doc])
    embed = FakeEmbeddingService()
    vector = FakeVectorSearchService()
    pipeline = EmbeddingPipeline(store, embed, vector, batch_size=1)

    embedded = pipeline.embed_corpus("c2")
    assert embedded == 1
    assert vector.indexed
    # embedding service should be called with the document text
    assert embed.calls
