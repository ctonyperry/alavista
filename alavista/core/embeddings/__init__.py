"""Embeddings package for Phase 3.1 placed under the alavista package."""

from .service import (
    DeterministicFallbackEmbeddingService,
    EmbeddingError,
    SentenceTransformersEmbeddingService,
    get_default_embedding_service,
)
from .pipeline import EmbeddingPipeline

__all__ = [
    "DeterministicFallbackEmbeddingService",
    "EmbeddingError",
    "SentenceTransformersEmbeddingService",
    "get_default_embedding_service",
    "EmbeddingPipeline",
]
