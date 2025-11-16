"""
Tests for the BM25 index module.
"""


from alavista.search.bm25 import BM25Index


class TestBM25Index:
    """Test BM25 indexing and search."""

    def test_empty_index(self):
        """Test index with no documents."""
        index = BM25Index()
        index.build([])

        results = index.search("test query")
        assert results == []
        assert index.doc_count == 0

    def test_single_document(self):
        """Test indexing a single document."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'hello world'}
        ]
        index.build(docs)

        assert index.doc_count == 1
        assert 'doc1' in index.documents

    def test_multiple_documents(self):
        """Test indexing multiple documents."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'hello world'},
            {'id': 'doc2', 'text': 'goodbye world'},
            {'id': 'doc3', 'text': 'hello goodbye'}
        ]
        index.build(docs)

        assert index.doc_count == 3
        assert len(index.documents) == 3

    def test_search_single_term(self):
        """Test searching with a single term."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'hello world'},
            {'id': 'doc2', 'text': 'goodbye world'},
            {'id': 'doc3', 'text': 'hello goodbye'}
        ]
        index.build(docs)

        results = index.search("hello")
        assert len(results) == 2
        # Check that results contain doc1 and doc3
        doc_ids = [doc_id for doc_id, _ in results]
        assert 'doc1' in doc_ids
        assert 'doc3' in doc_ids

    def test_search_multiple_terms(self):
        """Test searching with multiple terms."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'the quick brown fox'},
            {'id': 'doc2', 'text': 'the lazy dog'},
            {'id': 'doc3', 'text': 'quick brown dog'}
        ]
        index.build(docs)

        results = index.search("quick brown")
        assert len(results) > 0
        # Doc1 and doc3 should be in results
        doc_ids = [doc_id for doc_id, _ in results]
        assert 'doc1' in doc_ids
        assert 'doc3' in doc_ids

    def test_search_no_results(self):
        """Test search with no matching documents."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'hello world'},
            {'id': 'doc2', 'text': 'goodbye world'}
        ]
        index.build(docs)

        results = index.search("nonexistent")
        assert results == []

    def test_search_empty_query(self):
        """Test search with empty query."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'hello world'}
        ]
        index.build(docs)

        results = index.search("")
        assert results == []

    def test_search_with_limit(self):
        """Test search result limiting."""
        index = BM25Index()
        docs = [
            {'id': f'doc{i}', 'text': f'document number {i} with word test'}
            for i in range(10)
        ]
        index.build(docs)

        results = index.search("test", k=5)
        assert len(results) <= 5

    def test_search_results_sorted(self):
        """Test that search results are sorted by score."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'machine learning'},
            {'id': 'doc2', 'text': 'machine learning machine learning'},  # More occurrences
            {'id': 'doc3', 'text': 'deep learning'}
        ]
        index.build(docs)

        results = index.search("machine learning")
        # Results should be sorted by score descending
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i][1] >= results[i + 1][1]

    def test_bm25_scoring_stability(self):
        """Test that BM25 scoring is stable/deterministic."""
        index1 = BM25Index()
        index2 = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'machine learning algorithms'},
            {'id': 'doc2', 'text': 'deep learning networks'},
            {'id': 'doc3', 'text': 'machine learning applications'}
        ]

        index1.build(docs)
        index2.build(docs)

        results1 = index1.search("machine learning")
        results2 = index2.search("machine learning")

        assert results1 == results2

    def test_get_document(self):
        """Test retrieving a document by ID."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'hello world', 'metadata': {'source': 'test'}}
        ]
        index.build(docs)

        doc = index.get_document('doc1')
        assert doc is not None
        assert doc['id'] == 'doc1'
        assert doc['text'] == 'hello world'
        assert doc['metadata'] == {'source': 'test'}

    def test_get_nonexistent_document(self):
        """Test retrieving a non-existent document."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'hello world'}
        ]
        index.build(docs)

        doc = index.get_document('nonexistent')
        assert doc is None

    def test_rebuild_index(self):
        """Test rebuilding the index with new documents."""
        index = BM25Index()
        docs1 = [
            {'id': 'doc1', 'text': 'hello world'}
        ]
        index.build(docs1)
        assert index.doc_count == 1

        # Rebuild with different docs
        docs2 = [
            {'id': 'doc2', 'text': 'goodbye world'},
            {'id': 'doc3', 'text': 'hello goodbye'}
        ]
        index.build(docs2)
        assert index.doc_count == 2
        assert index.get_document('doc1') is None
        assert index.get_document('doc2') is not None

    def test_stopword_removal(self):
        """Test BM25 with stopword removal."""
        index = BM25Index(remove_stopwords=True)
        docs = [
            {'id': 'doc1', 'text': 'the quick brown fox'},
            {'id': 'doc2', 'text': 'quick brown dog'}
        ]
        index.build(docs)

        # Search with stopwords - they should be ignored
        results = index.search("the quick brown")
        assert len(results) > 0

    def test_custom_bm25_parameters(self):
        """Test BM25 with custom k1 and b parameters."""
        index = BM25Index(k1=2.0, b=0.5)
        docs = [
            {'id': 'doc1', 'text': 'test document'},
            {'id': 'doc2', 'text': 'test document test'}
        ]
        index.build(docs)

        results = index.search("test")
        assert len(results) == 2

    def test_case_insensitive_search(self):
        """Test that search is case-insensitive."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'Hello World'}
        ]
        index.build(docs)

        results1 = index.search("hello")
        results2 = index.search("HELLO")
        results3 = index.search("Hello")

        assert results1 == results2 == results3

    def test_document_metadata_preserved(self):
        """Test that document metadata is preserved."""
        index = BM25Index()
        docs = [
            {
                'id': 'doc1',
                'text': 'test document',
                'metadata': {'source': 'file.txt', 'author': 'test'}
            }
        ]
        index.build(docs)

        doc = index.get_document('doc1')
        assert doc['metadata'] == {'source': 'file.txt', 'author': 'test'}

    def test_long_documents(self):
        """Test indexing and searching long documents."""
        index = BM25Index()
        long_text = ' '.join(['word'] * 1000)
        docs = [
            {'id': 'doc1', 'text': long_text},
            {'id': 'doc2', 'text': 'short document'}
        ]
        index.build(docs)

        results = index.search("word")
        assert len(results) > 0

    def test_special_characters(self):
        """Test handling of special characters."""
        index = BM25Index()
        docs = [
            {'id': 'doc1', 'text': 'test@example.com'},
            {'id': 'doc2', 'text': 'user-name_123'}
        ]
        index.build(docs)

        # Special chars are removed, but the words should be indexed
        results = index.search("test")
        assert len(results) > 0
