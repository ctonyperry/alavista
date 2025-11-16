"""
Search service for querying documents in a corpus.

Provides BM25-based search over document chunks with result formatting.
"""

from typing import Protocol

from alavista.core.models import Chunk, SearchResult
from alavista.search.bm25 import BM25Index


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
    Service for searching documents using BM25 indexing.

    Builds an index from corpus chunks and provides search functionality
    with structured SearchResult objects.
    """

    def __init__(self, corpus_store: CorpusStoreProtocol,
                 k1: float = 1.5, b: float = 0.75, remove_stopwords: bool = False):
        """
        Initialize SearchService.

        Args:
            corpus_store: CorpusStore instance for accessing documents
            k1: BM25 k1 parameter (term frequency saturation)
            b: BM25 b parameter (length normalization)
            remove_stopwords: Whether to remove stopwords during indexing
        """
        self.corpus_store = corpus_store
        self.k1 = k1
        self.b = b
        self.remove_stopwords = remove_stopwords

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
