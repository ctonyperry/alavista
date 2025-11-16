"""
Tests for IngestionService.
"""

from pathlib import Path

import pytest

from alavista.core.corpus_store import SQLiteCorpusStore
from alavista.core.ingestion_service import (
    IngestionError,
    IngestionService,
    UnsupportedFormatError,
)
from alavista.core.models import Corpus


class TestIngestionService:
    """Test suite for IngestionService."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> SQLiteCorpusStore:
        """Create a test corpus store."""
        db_path = tmp_path / "test_corpus.db"
        return SQLiteCorpusStore(db_path)

    @pytest.fixture
    def service(self, store: SQLiteCorpusStore) -> IngestionService:
        """Create a test ingestion service."""
        return IngestionService(corpus_store=store)

    @pytest.fixture
    def corpus(self, store: SQLiteCorpusStore) -> Corpus:
        """Create a test corpus."""
        corpus = Corpus(
            id="test-corpus-1",
            type="research",
            name="Test Corpus",
        )
        return store.create_corpus(corpus)

    def test_ingest_text_basic(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test basic text ingestion."""
        text = "This is a simple test document."

        doc, chunks = service.ingest_text(corpus.id, text)

        assert doc.id is not None
        assert doc.corpus_id == corpus.id
        assert doc.text.strip() == text.strip()
        assert doc.content_hash is not None
        assert len(chunks) >= 1

    def test_ingest_text_with_metadata(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test text ingestion with metadata."""
        text = "Test document"
        metadata = {"title": "Test", "author": "Tester"}

        doc, chunks = service.ingest_text(corpus.id, text, metadata)

        assert doc.metadata["title"] == "Test"
        assert doc.metadata["author"] == "Tester"
        assert doc.metadata["source_type"] == "text"

    def test_ingest_empty_text(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test that empty text raises error."""
        with pytest.raises(IngestionError, match="empty"):
            service.ingest_text(corpus.id, "")

        with pytest.raises(IngestionError, match="empty"):
            service.ingest_text(corpus.id, "   ")

    def test_ingest_nonexistent_corpus(self, service: IngestionService):
        """Test ingestion to nonexistent corpus raises error."""
        with pytest.raises(IngestionError, match="not found"):
            service.ingest_text("nonexistent-corpus", "Test")

    def test_deduplication(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test that duplicate content is not re-ingested."""
        text = "This is a test document for deduplication."

        # Ingest first time
        doc1, chunks1 = service.ingest_text(corpus.id, text)

        # Ingest same text again
        doc2, chunks2 = service.ingest_text(corpus.id, text)

        # Should return the same document
        assert doc1.id == doc2.id
        assert doc1.content_hash == doc2.content_hash

        # Chunks should also be the same
        assert len(chunks1) == len(chunks2)

    def test_deduplication_ignores_whitespace(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test that deduplication normalizes whitespace."""
        text1 = "This is a test."
        text2 = "This    is    a    test."  # Extra spaces
        text3 = "This is a test."  # Extra line breaks

        doc1, _ = service.ingest_text(corpus.id, text1)
        doc2, _ = service.ingest_text(corpus.id, text2)
        doc3, _ = service.ingest_text(corpus.id, text3)

        # All should resolve to same document (after normalization)
        assert doc1.content_hash == doc2.content_hash == doc3.content_hash
        assert doc1.id == doc2.id == doc3.id

    def test_chunking_small_document(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test chunking of a small document."""
        text = "This is a small document."

        doc, chunks = service.ingest_text(corpus.id, text)

        # Small document should produce one chunk
        assert len(chunks) == 1
        assert chunks[0].document_id == doc.id
        assert chunks[0].corpus_id == corpus.id

    def test_chunking_large_document(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test chunking of a large document."""
        # Create a large document
        paragraphs = [
            f"This is paragraph {i}. " * 20  # ~400 chars per paragraph
            for i in range(10)
        ]
        text = "\n\n".join(paragraphs)

        doc, chunks = service.ingest_text(corpus.id, text)

        # Should produce multiple chunks
        assert len(chunks) > 1

        # Verify chunk properties
        for i, chunk in enumerate(chunks):
            assert chunk.id == f"{doc.id}::chunk_{i}"
            assert chunk.document_id == doc.id
            assert chunk.corpus_id == corpus.id
            assert chunk.text  # Not empty
            assert chunk.metadata["chunk_index"] == i
            assert chunk.metadata["total_chunks"] == len(chunks)

    def test_chunk_offsets(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test that chunk offsets are reasonable."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."

        doc, chunks = service.ingest_text(corpus.id, text)

        # All chunks should have valid offsets
        for chunk in chunks:
            assert chunk.start_offset >= 0
            assert chunk.end_offset > chunk.start_offset

    def test_ingest_file_txt(
        self, service: IngestionService, corpus: Corpus, tmp_path: Path
    ):
        """Test ingestion of a .txt file."""
        # Create a test file
        file_path = tmp_path / "test.txt"
        file_path.write_text("This is a test text file.")

        doc, chunks = service.ingest_file(corpus.id, file_path)

        assert doc.text.strip() == "This is a test text file."
        assert doc.metadata["source_type"] == "file"
        assert doc.metadata["source_path"] == str(file_path)
        assert doc.metadata["file_name"] == "test.txt"
        assert doc.metadata["file_format"] == ".txt"

    def test_ingest_file_markdown(
        self, service: IngestionService, corpus: Corpus, tmp_path: Path
    ):
        """Test ingestion of a .md file."""
        # Create a test markdown file
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test\n\nThis is markdown.")

        doc, chunks = service.ingest_file(corpus.id, file_path)

        assert "# Test" in doc.text
        assert "markdown" in doc.text
        assert doc.metadata["file_format"] == ".md"

    def test_ingest_file_not_found(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test that missing file raises error."""
        with pytest.raises(IngestionError, match="not found"):
            service.ingest_file(corpus.id, "/nonexistent/file.txt")

    def test_ingest_file_unsupported_format(
        self, service: IngestionService, corpus: Corpus, tmp_path: Path
    ):
        """Test that unsupported file format raises error."""
        # Create an unsupported file
        file_path = tmp_path / "test.pdf"
        file_path.write_text("PDF content")

        with pytest.raises(UnsupportedFormatError):
            service.ingest_file(corpus.id, file_path)

    def test_ingest_file_with_metadata(
        self, service: IngestionService, corpus: Corpus, tmp_path: Path
    ):
        """Test file ingestion with additional metadata."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Test content")

        metadata = {"author": "Test Author", "title": "Custom Title"}

        doc, chunks = service.ingest_file(corpus.id, file_path, metadata)

        assert doc.metadata["author"] == "Test Author"
        assert doc.metadata["title"] == "Custom Title"
        assert doc.metadata["source_type"] == "file"  # Should still be set

    def test_ingest_url_not_implemented(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test that URL ingestion raises not implemented error."""
        with pytest.raises(IngestionError, match="not yet implemented"):
            service.ingest_url(corpus.id, "https://example.com")

    def test_configurable_chunk_sizes(
        self, store: SQLiteCorpusStore, corpus: Corpus
    ):
        """Test that chunk sizes can be configured."""
        # Create service with small chunks
        small_service = IngestionService(
            corpus_store=store,
            min_chunk_size=50,
            max_chunk_size=100,
        )

        # Create service with large chunks
        large_service = IngestionService(
            corpus_store=store,
            min_chunk_size=500,
            max_chunk_size=1500,
        )

        text = "Paragraph. " * 100  # ~1100 chars

        doc1, small_chunks = small_service.ingest_text(corpus.id, text)
        # Need to clear the deduplication for the second ingest
        # by using slightly different text
        doc2, large_chunks = large_service.ingest_text(corpus.id, text + " Extra.")

        # Small chunks should produce more chunks
        assert len(small_chunks) > len(large_chunks)

    def test_unicode_handling(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test handling of unicode content."""
        text = "Test with émojis 🎉 and spëcial çharacters."

        doc, chunks = service.ingest_text(corpus.id, text)

        assert "émojis" in doc.text
        assert "🎉" in doc.text
        assert len(chunks) >= 1

    def test_multiline_document(
        self, service: IngestionService, corpus: Corpus
    ):
        """Test ingestion of multi-line document."""
        text = """Line 1
        Line 2
        Line 3

        New paragraph.

        Another paragraph."""

        doc, chunks = service.ingest_text(corpus.id, text)

        assert doc.text  # Should have content
        assert len(chunks) >= 1
