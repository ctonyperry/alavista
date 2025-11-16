"""
Vector embeddings module for Alavista.

This module manages vector representations of text:
- Embedding generation using local models
- Vector index building and maintenance
- Similarity search operations
- Embedding model management and caching
- Support for multiple embedding strategies
"""

from .vector_search_service import (
    FaissVectorSearchService,
    InMemoryVectorSearchService,
    VectorHit,
    VectorSearchError,
    VectorSearchService,
    _HAS_FAISS,
)

__all__ = [
    "FaissVectorSearchService",
    "InMemoryVectorSearchService",
    "VectorHit",
    "VectorSearchError",
    "VectorSearchService",
    "_HAS_FAISS",
]
