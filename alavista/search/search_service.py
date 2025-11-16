"""
Search service for querying documents in a corpus.

Provides BM25-based search over document chunks with result formatting, plus optional
vector and hybrid search for Phase 3.3.
"""

import asyncio
from typing import Protocol

from alavista.core.models import Chunk, SearchResult
from alavista.vector import VectorHit, VectorSearchService
from alavista.search.bm25 import BM25Index
from alavista.core.embeddings import get_default_embedding_service


class CorpusStoreProtocol(Protocol):
    """Protocol for CorpusStore to avoid circular imports."""

    def get_corpus(self, corpus_id: str) -> object | None:
        """Get corpus by ID."""
        ...

    def list_documents(self, corpus_id: str) -> list[object]:
        """List documents in corpus."""
        ...


class SearchService:
    """
    Service for searching documents using BM25 and optional vector/hybrid modes.
    """

    def __init__(
        self,
        corpus_store: CorpusStoreProtocol,
        k1: float = 1.5,
        b: float = 0.75,
        remove_stopwords: bool = False,
        vector_search_service: VectorSearchService | None = None,
        embedding_service=None,
    ):
        """
        Initialize SearchService.

        Args:
            corpus_store: CorpusStore instance for accessing documents
            k1: BM25 k1 parameter (term frequency saturation)
            b: BM25 b parameter (length normalization)
            remove_stopwords: Whether to remove stopwords during indexing
            vector_search_service: Optional vector backend
            embedding_service: Optional embedding backend for query embeddings
        """
        self.corpus_store = corpus_store
        self.k1 = k1
        self.b = b
        self.remove_stopwords = remove_stopwords
        self.vector_search_service = vector_search_service
        self.embedding_service = embedding_service

        # Cache of indices by corpus_id
        self._indices: dict[str, BM25Index] = {}

    def _build_index_for_corpus(self, corpus_id: str, chunks: list[Chunk]) -> BM25Index:
        """
        Build BM25 index for a corpus from its chunks.

        Args:
            corpus_id: Corpus ID
            chunks: List of Chunk objects

        Returns:
            BM25Index instance
        """
        # Convert chunks to document format for indexing
        documents = []
        for chunk in chunks:
            documents.append({
                'id': chunk.id,
                'text': chunk.text,
                'document_id': chunk.document_id,
                'corpus_id': chunk.corpus_id,
                'start_offset': chunk.start_offset,
                'end_offset': chunk.end_offset,
                'metadata': chunk.metadata
            })

        # Build index
        index = BM25Index(k1=self.k1, b=self.b, remove_stopwords=self.remove_stopwords)
        index.build(documents)

        return index

    def _get_or_build_index(self, corpus_id: str, chunks: list[Chunk]) -> BM25Index:
        """
        Get cached index or build a new one.

        Args:
            corpus_id: Corpus ID
            chunks: List of chunks (used if index needs to be built)

        Returns:
            BM25Index instance
        """
        if corpus_id not in self._indices:
            self._indices[corpus_id] = self._build_index_for_corpus(corpus_id, chunks)
        return self._indices[corpus_id]

    def invalidate_cache(self, corpus_id: str | None = None) -> None:
        """
        Invalidate index cache for a corpus or all corpora.

        Args:
            corpus_id: Corpus ID to invalidate, or None to invalidate all
        """
        if corpus_id is None:
            self._indices.clear()
        elif corpus_id in self._indices:
            del self._indices[corpus_id]

    def search_bm25(self, corpus_id: str, chunks: list[Chunk], query: str, k: int = 20,
                    excerpt_length: int = 200) -> list[SearchResult]:
        """
        Search a corpus using BM25 scoring.

        Args:
            corpus_id: ID of the corpus to search
            chunks: List of Chunk objects to search over
            query: Search query string
            k: Maximum number of results to return (default: 20)
            excerpt_length: Maximum length of excerpt to include (default: 200)

        Returns:
            List of SearchResult objects, sorted by relevance score
        """
        # Validate corpus exists
        corpus = self.corpus_store.get_corpus(corpus_id)
        if corpus is None:
            raise ValueError(f"Corpus {corpus_id} not found")

        if not chunks:
            return []

        # Get or build index
        index = self._get_or_build_index(corpus_id, chunks)

        # Search
        results = index.search(query, k=k)

        # Format results
        search_results = []
        for doc_id, score in results:
            doc = index.get_document(doc_id)
            if doc is None:
                continue

            # Create excerpt (truncate if needed)
            text = doc['text']
            if len(text) > excerpt_length:
                excerpt = text[:excerpt_length] + "..."
            else:
                excerpt = text

            # Build SearchResult
            search_result = SearchResult(
                doc_id=doc['document_id'],
                chunk_id=doc['id'],
                score=score,
                excerpt=excerpt,
                metadata=doc['metadata']
            )
            search_results.append(search_result)

        return search_results

    def search(
        self,
        corpus_id: str,
        chunks: list[Chunk],
        query: str,
        k: int = 20,
        mode: str = "bm25",
        k_bm25: int | None = None,
        k_vector: int | None = None,
        w_bm25: float = 0.5,
        w_vector: float = 0.5,
        excerpt_length: int = 200,
    ) -> list[SearchResult]:
        """
        Unified search entrypoint supporting bm25, vector, or hybrid modes.
        """
        if mode == "bm25":
            return self.search_bm25(corpus_id, chunks, query, k=k, excerpt_length=excerpt_length)

        if mode not in {"vector", "hybrid"}:
            raise ValueError(f"Unsupported search mode: {mode}")

        if not self.vector_search_service:
            raise ValueError("Vector search requested but no vector backend is configured")

        # Validate corpus exists
        corpus = self.corpus_store.get_corpus(corpus_id)
        if corpus is None:
            raise ValueError(f"Corpus {corpus_id} not found")

        chunk_map = {chunk.id: chunk for chunk in chunks}
        if mode == "vector":
            return self._vector_only(corpus_id, query, k_vector or k, chunk_map, excerpt_length)

        # hybrid path
        bm25_hits = self.search_bm25(
            corpus_id, chunks, query, k=k_bm25 or k, excerpt_length=excerpt_length
        )
        vector_hits = self._vector_only(corpus_id, query, k_vector or k, chunk_map, excerpt_length)
        return self._combine_hybrid(bm25_hits, vector_hits, w_bm25, w_vector)

    def _vector_only(
        self,
        corpus_id: str,
        query: str,
        k: int,
        chunk_map: dict[str, Chunk],
        excerpt_length: int,
    ) -> list[SearchResult]:
        """Run vector-only search."""
        query_vec = self._embed_query(query)[0]
        hits = self._run_coro(self.vector_search_service.search(corpus_id, query_vec, k=k))
        results: list[SearchResult] = []
        for hit in hits:
            chunk = chunk_map.get(hit.chunk_id)
            if not chunk:
                continue
            text = chunk.text
            excerpt = text[:excerpt_length] + ("..." if len(text) > excerpt_length else "")
            results.append(
                SearchResult(
                    doc_id=hit.document_id,
                    chunk_id=hit.chunk_id,
                    score=hit.score,
                    excerpt=excerpt,
                    metadata=chunk.metadata,
                )
            )
        return results

    def _combine_hybrid(
        self,
        bm25_hits: list[SearchResult],
        vector_hits: list[SearchResult],
        w_bm25: float,
        w_vector: float,
    ) -> list[SearchResult]:
        """Combine BM25 and vector hits with normalized scores."""
        bm25_norm = self._normalize_hits(bm25_hits)
        vector_norm = self._normalize_hits(vector_hits)

        combined: dict[tuple[str, str], float] = {}
        keys = set(bm25_norm.keys()) | set(vector_norm.keys())
        for key in keys:
            score = 0.0
            if key in bm25_norm:
                score += w_bm25 * bm25_norm[key]
            if key in vector_norm:
                score += w_vector * vector_norm[key]
            combined[key] = score

        # Produce SearchResult objects using whichever hit object is available
        hit_lookup: dict[tuple[str, str], SearchResult] = {}
        for hit in bm25_hits + vector_hits:
            key = (hit.doc_id, hit.chunk_id)
            if key not in hit_lookup:
                hit_lookup[key] = hit

        results = []
        for key, score in combined.items():
            base_hit = hit_lookup.get(key)
            if not base_hit:
                continue
            results.append(
                SearchResult(
                    doc_id=base_hit.doc_id,
                    chunk_id=base_hit.chunk_id,
                    score=score,
                    excerpt=base_hit.excerpt,
                    metadata=base_hit.metadata,
                )
            )

        # Deterministic tie-breaking by doc_id/chunk_id
        results.sort(key=lambda r: (-r.score, r.doc_id, r.chunk_id))
        return results

    def _normalize_hits(self, hits: list[SearchResult]) -> dict[tuple[str, str], float]:
        if not hits:
            return {}
        scores = [h.score for h in hits]
        max_s = max(scores)
        min_s = min(scores)
        if max_s == min_s:
            return {(h.doc_id, h.chunk_id): 1.0 for h in hits}
        return {(h.doc_id, h.chunk_id): (h.score - min_s) / (max_s - min_s) for h in hits}

    def _embed_query(self, query: str) -> list[list[float]]:
        if self.embedding_service is None:
            self.embedding_service = get_default_embedding_service()
        return self._run_coro(self.embedding_service.embed_texts([query]))

    def _run_coro(self, coro):
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(coro, loop).result()
        except RuntimeError:
            return asyncio.run(coro)
