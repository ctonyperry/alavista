"""
Tests for CorpusStore implementation.
"""

import sqlite3
from pathlib import Path

import pytest

from alavista.core.corpus_store import SQLiteCorpusStore
from alavista.core.models import Corpus, Document


class TestSQLiteCorpusStore:
    """Test suite for SQLiteCorpusStore."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> SQLiteCorpusStore:
        """Create a test corpus store."""
        db_path = tmp_path / "test_corpus.db"
        return SQLiteCorpusStore(db_path)

    @pytest.fixture
    def sample_corpus(self) -> Corpus:
        """Create a sample corpus for testing."""
        return Corpus(
            id="test-corpus-1",
            type="research",
            name="Test Corpus",
            description="A test corpus",
            metadata={"source": "test"},
        )

    @pytest.fixture
    def sample_document(self) -> Document:
        """Create a sample document for testing."""
        return Document(
            id="doc-1",
            corpus_id="test-corpus-1",
            text="This is a test document with some content.",
            content_hash="abc123",
            metadata={"source_type": "text"},
        )

    def test_store_initialization(self, tmp_path: Path):
        """Test that store initializes database correctly."""
        db_path = tmp_path / "test.db"
        SQLiteCorpusStore(db_path)

        assert db_path.exists()

        # Verify tables exist
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}

            assert "corpora" in tables
            assert "documents" in tables

    def test_create_corpus(self, store: SQLiteCorpusStore, sample_corpus: Corpus):
        """Test corpus creation."""
        created = store.create_corpus(sample_corpus)

        assert created.id == sample_corpus.id
        assert created.name == sample_corpus.name
        assert created.type == sample_corpus.type

    def test_get_corpus(self, store: SQLiteCorpusStore, sample_corpus: Corpus):
        """Test retrieving a corpus by ID."""
        store.create_corpus(sample_corpus)

        retrieved = store.get_corpus(sample_corpus.id)

        assert retrieved is not None
        assert retrieved.id == sample_corpus.id
        assert retrieved.name == sample_corpus.name
        assert retrieved.metadata == sample_corpus.metadata

    def test_get_nonexistent_corpus(self, store: SQLiteCorpusStore):
        """Test retrieving a corpus that doesn't exist."""
        result = store.get_corpus("nonexistent-id")
        assert result is None

    def test_list_corpora(self, store: SQLiteCorpusStore):
        """Test listing all corpora."""
        # Create multiple corpora
        corpus1 = Corpus(id="corpus-1", type="global", name="Corpus 1")
        corpus2 = Corpus(id="corpus-2", type="research", name="Corpus 2")
        corpus3 = Corpus(id="corpus-3", type="persona_manual", name="Corpus 3")

        store.create_corpus(corpus1)
        store.create_corpus(corpus2)
        store.create_corpus(corpus3)

        corpora = store.list_corpora()

        assert len(corpora) == 3
        corpus_ids = {c.id for c in corpora}
        assert corpus_ids == {"corpus-1", "corpus-2", "corpus-3"}

    def test_list_corpora_empty(self, store: SQLiteCorpusStore):
        """Test listing corpora when none exist."""
        corpora = store.list_corpora()
        assert corpora == []

    def test_delete_corpus(self, store: SQLiteCorpusStore, sample_corpus: Corpus):
        """Test deleting a corpus."""
        store.create_corpus(sample_corpus)

        # Verify it exists
        assert store.get_corpus(sample_corpus.id) is not None

        # Delete it
        result = store.delete_corpus(sample_corpus.id)
        assert result is True

        # Verify it's gone
        assert store.get_corpus(sample_corpus.id) is None

    def test_delete_nonexistent_corpus(self, store: SQLiteCorpusStore):
        """Test deleting a corpus that doesn't exist."""
        result = store.delete_corpus("nonexistent-id")
        assert result is False

    def test_delete_corpus_cascades_to_documents(
        self, store: SQLiteCorpusStore, sample_corpus: Corpus, sample_document: Document
    ):
        """Test that deleting a corpus also deletes its documents."""
        store.create_corpus(sample_corpus)
        store.add_document(sample_document)

        # Verify document exists
        assert store.get_document(sample_document.id) is not None

        # Delete corpus
        store.delete_corpus(sample_corpus.id)

        # Verify document is also deleted
        assert store.get_document(sample_document.id) is None

    def test_add_document(
        self, store: SQLiteCorpusStore, sample_corpus: Corpus, sample_document: Document
    ):
        """Test adding a document."""
        store.create_corpus(sample_corpus)
        added = store.add_document(sample_document)

        assert added.id == sample_document.id
        assert added.text == sample_document.text

    def test_get_document(
        self, store: SQLiteCorpusStore, sample_corpus: Corpus, sample_document: Document
    ):
        """Test retrieving a document by ID."""
        store.create_corpus(sample_corpus)
        store.add_document(sample_document)

        retrieved = store.get_document(sample_document.id)

        assert retrieved is not None
        assert retrieved.id == sample_document.id
        assert retrieved.text == sample_document.text
        assert retrieved.content_hash == sample_document.content_hash
        assert retrieved.metadata == sample_document.metadata

    def test_get_nonexistent_document(self, store: SQLiteCorpusStore):
        """Test retrieving a document that doesn't exist."""
        result = store.get_document("nonexistent-id")
        assert result is None

    def test_list_documents(
        self, store: SQLiteCorpusStore, sample_corpus: Corpus
    ):
        """Test listing documents in a corpus."""
        store.create_corpus(sample_corpus)

        # Add multiple documents
        doc1 = Document(
            id="doc-1",
            corpus_id=sample_corpus.id,
            text="Document 1",
            content_hash="hash1",
        )
        doc2 = Document(
            id="doc-2",
            corpus_id=sample_corpus.id,
            text="Document 2",
            content_hash="hash2",
        )
        doc3 = Document(
            id="doc-3",
            corpus_id=sample_corpus.id,
            text="Document 3",
            content_hash="hash3",
        )

        store.add_document(doc1)
        store.add_document(doc2)
        store.add_document(doc3)

        documents = store.list_documents(sample_corpus.id)

        assert len(documents) == 3
        doc_ids = {d.id for d in documents}
        assert doc_ids == {"doc-1", "doc-2", "doc-3"}

    def test_list_documents_empty(
        self, store: SQLiteCorpusStore, sample_corpus: Corpus
    ):
        """Test listing documents when corpus has none."""
        store.create_corpus(sample_corpus)
        documents = store.list_documents(sample_corpus.id)
        assert documents == []

    def test_find_by_hash(
        self, store: SQLiteCorpusStore, sample_corpus: Corpus, sample_document: Document
    ):
        """Test finding a document by content hash."""
        store.create_corpus(sample_corpus)
        store.add_document(sample_document)

        found = store.find_by_hash(sample_corpus.id, sample_document.content_hash)

        assert found is not None
        assert found.id == sample_document.id
        assert found.content_hash == sample_document.content_hash

    def test_find_by_hash_not_found(
        self, store: SQLiteCorpusStore, sample_corpus: Corpus
    ):
        """Test finding a document by hash when it doesn't exist."""
        store.create_corpus(sample_corpus)

        found = store.find_by_hash(sample_corpus.id, "nonexistent-hash")
        assert found is None

    def test_find_by_hash_different_corpus(
        self, store: SQLiteCorpusStore, sample_document: Document
    ):
        """Test that hash search is scoped to corpus."""
        # Create two corpora
        corpus1 = Corpus(id="corpus-1", type="global", name="Corpus 1")
        corpus2 = Corpus(id="corpus-2", type="global", name="Corpus 2")

        store.create_corpus(corpus1)
        store.create_corpus(corpus2)

        # Add document to corpus1
        doc = Document(
            id="doc-1",
            corpus_id=corpus1.id,
            text="Test",
            content_hash="hash123",
        )
        store.add_document(doc)

        # Should find in corpus1
        found = store.find_by_hash(corpus1.id, "hash123")
        assert found is not None

        # Should not find in corpus2
        found = store.find_by_hash(corpus2.id, "hash123")
        assert found is None

    def test_duplicate_corpus_id(
        self, store: SQLiteCorpusStore, sample_corpus: Corpus
    ):
        """Test that duplicate corpus IDs are rejected."""
        store.create_corpus(sample_corpus)

        with pytest.raises(sqlite3.IntegrityError):
            store.create_corpus(sample_corpus)

    def test_duplicate_document_id(
        self, store: SQLiteCorpusStore, sample_corpus: Corpus, sample_document: Document
    ):
        """Test that duplicate document IDs are rejected."""
        store.create_corpus(sample_corpus)
        store.add_document(sample_document)

        with pytest.raises(sqlite3.IntegrityError):
            store.add_document(sample_document)
