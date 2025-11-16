import asyncio

from alavista.core.embeddings.service import (
    DeterministicFallbackEmbeddingService,
    EmbeddingError,
    SentenceTransformersEmbeddingService,
    _HAS_ST,
    get_default_embedding_service,
)


def test_fallback_dim_and_determinism():
    svc = DeterministicFallbackEmbeddingService(dim=16)
    texts = ["hello world", "hello world", "different"]
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(svc.embed_texts(texts))
    assert len(out) == 3
    assert all(len(v) == 16 for v in out)
    # identical inputs produce identical vectors
    assert out[0] == out[1]
    # different input should differ
    assert out[0] != out[2]


def test_default_service_available():
    svc = get_default_embedding_service()
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(svc.embed_texts(["a test"]))
    assert len(out) == 1
    assert len(out[0]) > 0


def test_sentence_transformers_installed():
    # Only run this if sentence-transformers is available in the environment.
    if not _HAS_ST:
        return
    svc = SentenceTransformersEmbeddingService(batch_size=2)
    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(svc.embed_texts(["one", "two", "three"]))
    assert len(out) == 3
    # all-MiniLM-L6-v2 produces 384-dim vectors
    assert all(len(v) == 384 for v in out)
