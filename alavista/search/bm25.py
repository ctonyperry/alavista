"""
BM25 indexing and search implementation.

BM25 is a probabilistic ranking function used for information retrieval.
This module provides an in-memory BM25 index builder and search functionality.
"""

import math
from collections import Counter, defaultdict
from typing import Any

from alavista.search.tokenizer import tokenize


class BM25Index:
    """
    BM25 index for keyword-based search.

    Builds an inverted index from documents and scores queries using BM25 algorithm.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75, remove_stopwords: bool = False):
        """
        Initialize BM25 index.

        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
            remove_stopwords: Whether to remove stopwords during tokenization
        """
        self.k1 = k1
        self.b = b
        self.remove_stopwords = remove_stopwords

        # Index structures
        self.doc_count = 0
        self.avg_doc_length = 0.0
        self.doc_lengths: dict[str, int] = {}
        self.doc_term_freqs: dict[str, Counter[str]] = {}
        self.inverted_index: dict[str, set[str]] = defaultdict(set)
        self.idf_cache: dict[str, float] = {}
        self.documents: dict[str, dict[str, Any]] = {}

    def build(self, documents: list[dict[str, Any]]) -> None:
        """
        Build the BM25 index from a list of documents.

        Each document should have:
        - 'id': unique identifier
        - 'text': text content to index
        - any other fields to store as document metadata

        Args:
            documents: List of document dictionaries
        """
        if not documents:
            return

        # Clear existing index
        self._clear()

        # Index each document
        total_length = 0
        for doc in documents:
            doc_id = doc['id']
            text = doc['text']

            # Tokenize
            tokens = tokenize(text, lowercase=True, remove_stopwords=self.remove_stopwords)

            # Store document
            self.documents[doc_id] = doc

            # Compute term frequencies
            term_freqs = Counter(tokens)
            self.doc_term_freqs[doc_id] = term_freqs

            # Track document length
            doc_length = len(tokens)
            self.doc_lengths[doc_id] = doc_length
            total_length += doc_length

            # Update inverted index
            for term in term_freqs:
                self.inverted_index[term].add(doc_id)

        # Compute average document length
        self.doc_count = len(documents)
        self.avg_doc_length = total_length / self.doc_count if self.doc_count > 0 else 0.0

        # Pre-compute IDF values
        self._compute_idf()

    def _clear(self) -> None:
        """Clear the index."""
        self.doc_count = 0
        self.avg_doc_length = 0.0
        self.doc_lengths.clear()
        self.doc_term_freqs.clear()
        self.inverted_index.clear()
        self.idf_cache.clear()
        self.documents.clear()

    def _compute_idf(self) -> None:
        """Compute IDF values for all terms in the index."""
        for term, doc_set in self.inverted_index.items():
            df = len(doc_set)  # document frequency
            # IDF formula: log((N - df + 0.5) / (df + 0.5) + 1)
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1.0)
            self.idf_cache[term] = idf

    def _score_document(self, doc_id: str, query_terms: list[str]) -> float:
        """
        Compute BM25 score for a document given query terms.

        Args:
            doc_id: Document ID
            query_terms: List of query terms

        Returns:
            BM25 score
        """
        score = 0.0
        doc_length = self.doc_lengths[doc_id]
        term_freqs = self.doc_term_freqs[doc_id]

        # Compute normalized document length
        norm_doc_length = doc_length / self.avg_doc_length if self.avg_doc_length > 0 else 0.0

        for term in query_terms:
            if term not in self.idf_cache:
                continue

            idf = self.idf_cache[term]
            tf = term_freqs.get(term, 0)

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * norm_doc_length)
            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, k: int = 20) -> list[tuple[str, float]]:
        """
        Search the index using BM25 scoring.

        Args:
            query: Search query string
            k: Maximum number of results to return

        Returns:
            List of (doc_id, score) tuples, sorted by score descending
        """
        if not query or self.doc_count == 0:
            return []

        # Tokenize query
        query_terms = tokenize(query, lowercase=True, remove_stopwords=self.remove_stopwords)

        if not query_terms:
            return []

        # Find candidate documents (documents containing at least one query term)
        candidate_docs = set()
        for term in query_terms:
            if term in self.inverted_index:
                candidate_docs.update(self.inverted_index[term])

        if not candidate_docs:
            return []

        # Score each candidate document
        scores: list[tuple[str, float]] = []
        for doc_id in candidate_docs:
            score = self._score_document(doc_id, query_terms)
            if score > 0:
                scores.append((doc_id, score))

        # Sort by score descending and return top k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """
        Retrieve a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document dictionary or None if not found
        """
        return self.documents.get(doc_id)
