"""
Tests for the SearchService module.
"""

import pytest

from alavista.core.container import Container
from alavista.core.corpus_store import SQLiteCorpusStore
from alavista.core.models import Chunk, Corpus, Document, SearchResult
from alavista.search.search_service import SearchService


@pytest.fixture
def corpus_store(tmp_path):
    """Create a temporary corpus store."""
    db_path = tmp_path / "test_corpus.db"
    return SQLiteCorpusStore(db_path)


@pytest.fixture
def search_service(corpus_store):
    """Create a search service."""
    return SearchService(corpus_store)


@pytest.fixture
def sample_corpus(corpus_store):
    """Create a sample corpus with documents."""
    corpus = Corpus(
        id="test-corpus",
        type="research",
        name="Test Corpus"
    )
    corpus_store.create_corpus(corpus)

    # Add some documents
    doc1 = Document(
        id="doc1",
        corpus_id="test-corpus",
        text="Machine learning is a subset of artificial intelligence.",
        content_hash="hash1",
        metadata={"source": "doc1.txt"}
    )
    doc2 = Document(
        id="doc2",
        corpus_id="test-corpus",
        text="Deep learning is a type of machine learning using neural networks.",
        content_hash="hash2",
        metadata={"source": "doc2.txt"}
    )
    doc3 = Document(
        id="doc3",
        corpus_id="test-corpus",
        text="Natural language processing involves understanding human language.",
        content_hash="hash3",
        metadata={"source": "doc3.txt"}
    )

    corpus_store.add_document(doc1)
    corpus_store.add_document(doc2)
    corpus_store.add_document(doc3)

    return corpus


@pytest.fixture
def sample_chunks(sample_corpus):
    """Create sample chunks from the corpus."""
    return [
        Chunk(
            id="doc1::chunk0",
            document_id="doc1",
            corpus_id="test-corpus",
            text="Machine learning is a subset of artificial intelligence.",
            start_offset=0,
            end_offset=57,
            metadata={"source": "doc1.txt"}
        ),
        Chunk(
            id="doc2::chunk0",
            document_id="doc2",
            corpus_id="test-corpus",
            text="Deep learning is a type of machine learning using neural networks.",
            start_offset=0,
            end_offset=67,
            metadata={"source": "doc2.txt"}
        ),
        Chunk(
            id="doc3::chunk0",
            document_id="doc3",
            corpus_id="test-corpus",
            text="Natural language processing involves understanding human language.",
            start_offset=0,
            end_offset=66,
            metadata={"source": "doc3.txt"}
        ),
    ]


class TestSearchService:
    """Test SearchService functionality."""

    def test_search_basic(self, search_service, sample_corpus, sample_chunks):
        """Test basic search functionality."""
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="machine learning"
        )

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_results_structure(self, search_service, sample_corpus, sample_chunks):
        """Test that search results have correct structure."""
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="machine learning"
        )

        assert len(results) > 0
        result = results[0]

        assert hasattr(result, 'doc_id')
        assert hasattr(result, 'chunk_id')
        assert hasattr(result, 'score')
        assert hasattr(result, 'excerpt')
        assert hasattr(result, 'metadata')

        assert isinstance(result.score, float)
        assert result.score > 0

    def test_search_no_results(self, search_service, sample_corpus, sample_chunks):
        """Test search with no matching results."""
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="nonexistent term xyz"
        )

        assert results == []

    def test_search_empty_query(self, search_service, sample_corpus, sample_chunks):
        """Test search with empty query."""
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query=""
        )

        assert results == []

    def test_search_with_limit(self, search_service, sample_corpus, sample_chunks):
        """Test search result limiting."""
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="learning",
            k=1
        )

        assert len(results) <= 1

    def test_search_sorted_by_score(self, search_service, sample_corpus, sample_chunks):
        """Test that results are sorted by score."""
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="machine learning"
        )

        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    def test_search_nonexistent_corpus(self, search_service, sample_chunks):
        """Test search on non-existent corpus."""
        with pytest.raises(ValueError, match="Corpus.*not found"):
            search_service.search_bm25(
                corpus_id="nonexistent",
                chunks=sample_chunks,
                query="test"
            )

    def test_search_empty_chunks(self, search_service, sample_corpus):
        """Test search with no chunks."""
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=[],
            query="test"
        )

        assert results == []

    def test_excerpt_generation(self, search_service, sample_corpus, sample_chunks):
        """Test that excerpts are generated correctly."""
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="machine learning"
        )

        assert len(results) > 0
        for result in results:
            assert len(result.excerpt) > 0
            assert isinstance(result.excerpt, str)

    def test_excerpt_truncation(self, search_service, sample_corpus):
        """Test that long excerpts are truncated."""
        long_text = "word " * 100  # 500 chars
        chunks = [
            Chunk(
                id="doc1::chunk0",
                document_id="doc1",
                corpus_id="test-corpus",
                text=long_text,
                start_offset=0,
                end_offset=len(long_text),
                metadata={}
            )
        ]

        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=chunks,
            query="word",
            excerpt_length=50
        )

        assert len(results) > 0
        assert len(results[0].excerpt) <= 53  # 50 + "..."

    def test_metadata_preserved(self, search_service, sample_corpus, sample_chunks):
        """Test that document metadata is preserved in results."""
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="machine learning"
        )

        assert len(results) > 0
        for result in results:
            assert 'source' in result.metadata

    def test_index_caching(self, search_service, sample_corpus, sample_chunks):
        """Test that index is cached between searches."""
        # First search
        results1 = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="machine"
        )

        # Second search should use cached index
        results2 = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="learning"
        )

        # Both should work
        assert len(results1) > 0
        assert len(results2) > 0

    def test_invalidate_cache_specific(self, search_service, sample_corpus, sample_chunks):
        """Test invalidating cache for specific corpus."""
        # Build index
        search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="test"
        )

        # Invalidate
        search_service.invalidate_cache("test-corpus")

        # Should still work after invalidation
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="test"
        )
        assert isinstance(results, list)

    def test_invalidate_cache_all(self, search_service, sample_corpus, sample_chunks):
        """Test invalidating all caches."""
        # Build index
        search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="test"
        )

        # Invalidate all
        search_service.invalidate_cache()

        # Should still work after invalidation
        results = search_service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="test"
        )
        assert isinstance(results, list)

    def test_custom_bm25_parameters(self, corpus_store, sample_corpus, sample_chunks):
        """Test SearchService with custom BM25 parameters."""
        service = SearchService(corpus_store, k1=2.0, b=0.5)

        results = service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="machine learning"
        )

        assert len(results) > 0

    def test_stopword_removal(self, corpus_store, sample_corpus, sample_chunks):
        """Test SearchService with stopword removal."""
        service = SearchService(corpus_store, remove_stopwords=True)

        results = service.search_bm25(
            corpus_id="test-corpus",
            chunks=sample_chunks,
            query="the machine learning"
        )

        # Should still find results even with stopwords in query
        assert len(results) > 0

    def test_multiple_corpora(self, corpus_store, search_service):
        """Test searching different corpora separately."""
        # Create two corpora
        corpus1 = Corpus(id="corpus1", type="research", name="Corpus 1")
        corpus2 = Corpus(id="corpus2", type="research", name="Corpus 2")
        corpus_store.create_corpus(corpus1)
        corpus_store.create_corpus(corpus2)

        chunks1 = [
            Chunk(
                id="doc1::chunk0",
                document_id="doc1",
                corpus_id="corpus1",
                text="Python programming language",
                start_offset=0,
                end_offset=27,
                metadata={}
            )
        ]

        chunks2 = [
            Chunk(
                id="doc2::chunk0",
                document_id="doc2",
                corpus_id="corpus2",
                text="JavaScript web development",
                start_offset=0,
                end_offset=26,
                metadata={}
            )
        ]

        # Search each corpus
        results1 = search_service.search_bm25("corpus1", chunks1, "Python")
        results2 = search_service.search_bm25("corpus2", chunks2, "JavaScript")

        assert len(results1) > 0
        assert len(results2) > 0
        # Verify results are from different documents/chunks
        assert results1[0].chunk_id != results2[0].chunk_id


class TestContainerIntegration:
    """Test SearchService integration with Container."""

    def test_create_search_service(self, tmp_path):
        """Test creating SearchService via Container."""
        settings = Container.create_settings(data_dir=tmp_path)
        corpus_store = Container.create_corpus_store(settings)
        search_service = Container.create_search_service(corpus_store)

        assert search_service is not None
        assert isinstance(search_service, SearchService)

    def test_get_search_service_singleton(self):
        """Test getting SearchService singleton from Container."""
        service1 = Container.get_search_service()
        service2 = Container.get_search_service()

        assert service1 is service2
