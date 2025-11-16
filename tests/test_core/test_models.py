"""
Tests for core data models.
"""

from datetime import datetime

from alavista.core.models import Chunk, Corpus, Document


class TestCorpus:
    """Test suite for Corpus model."""

    def test_corpus_creation(self):
        """Test basic corpus creation."""
        corpus = Corpus(
            id="test-corpus-1",
            type="research",
            name="Test Corpus",
            description="A test corpus",
        )

        assert corpus.id == "test-corpus-1"
        assert corpus.type == "research"
        assert corpus.name == "Test Corpus"
        assert corpus.description == "A test corpus"
        assert corpus.persona_id is None
        assert corpus.topic_id is None
        assert isinstance(corpus.metadata, dict)
        assert isinstance(corpus.created_at, datetime)

    def test_corpus_with_persona(self):
        """Test corpus with persona association."""
        corpus = Corpus(
            id="persona-corpus-1",
            type="persona_manual",
            persona_id="investigative_journalist",
            name="Journalist Manual",
        )

        assert corpus.type == "persona_manual"
        assert corpus.persona_id == "investigative_journalist"

    def test_corpus_with_topic(self):
        """Test corpus with topic association."""
        corpus = Corpus(
            id="research-corpus-1",
            type="research",
            topic_id="epstein_core",
            name="Epstein Research",
        )

        assert corpus.type == "research"
        assert corpus.topic_id == "epstein_core"

    def test_corpus_with_metadata(self):
        """Test corpus with custom metadata."""
        corpus = Corpus(
            id="test-corpus-2",
            type="global",
            name="Global Corpus",
            metadata={"source": "test", "version": 1},
        )

        assert corpus.metadata == {"source": "test", "version": 1}


class TestDocument:
    """Test suite for Document model."""

    def test_document_creation(self):
        """Test basic document creation."""
        doc = Document(
            id="doc-1",
            corpus_id="corpus-1",
            text="This is a test document.",
            content_hash="abc123",
        )

        assert doc.id == "doc-1"
        assert doc.corpus_id == "corpus-1"
        assert doc.text == "This is a test document."
        assert doc.content_hash == "abc123"
        assert isinstance(doc.metadata, dict)
        assert isinstance(doc.created_at, datetime)

    def test_document_with_metadata(self):
        """Test document with metadata."""
        doc = Document(
            id="doc-2",
            corpus_id="corpus-1",
            text="Test content",
            content_hash="xyz789",
            metadata={
                "source_type": "file",
                "source_path": "/path/to/file.txt",
                "title": "Test Document",
            },
        )

        assert doc.metadata["source_type"] == "file"
        assert doc.metadata["source_path"] == "/path/to/file.txt"
        assert doc.metadata["title"] == "Test Document"


class TestChunk:
    """Test suite for Chunk model."""

    def test_chunk_creation(self):
        """Test basic chunk creation."""
        chunk = Chunk(
            id="doc-1::chunk_0",
            document_id="doc-1",
            corpus_id="corpus-1",
            text="This is a test chunk.",
            start_offset=0,
            end_offset=21,
        )

        assert chunk.id == "doc-1::chunk_0"
        assert chunk.document_id == "doc-1"
        assert chunk.corpus_id == "corpus-1"
        assert chunk.text == "This is a test chunk."
        assert chunk.start_offset == 0
        assert chunk.end_offset == 21
        assert isinstance(chunk.metadata, dict)

    def test_chunk_with_metadata(self):
        """Test chunk with metadata."""
        chunk = Chunk(
            id="doc-1::chunk_1",
            document_id="doc-1",
            corpus_id="corpus-1",
            text="Second chunk",
            start_offset=22,
            end_offset=34,
            metadata={"chunk_index": 1, "total_chunks": 3},
        )

        assert chunk.metadata["chunk_index"] == 1
        assert chunk.metadata["total_chunks"] == 3
