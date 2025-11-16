"""
Integration tests for end-to-end workflows.
"""

from pathlib import Path

import pytest

from alavista.core.container import Container
from alavista.core.corpus_store import SQLiteCorpusStore
from alavista.core.ingestion_service import IngestionService
from alavista.core.models import Corpus


class TestEndToEndIngestion:
    """Test end-to-end ingestion workflows."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path: Path) -> Path:
        """Create a temporary data directory."""
        return tmp_path / "data"

    @pytest.fixture
    def corpus_store(self, temp_data_dir: Path) -> SQLiteCorpusStore:
        """Create a corpus store for testing."""
        db_path = temp_data_dir / "corpus.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return SQLiteCorpusStore(db_path)

    @pytest.fixture
    def ingestion_service(self, corpus_store: SQLiteCorpusStore) -> IngestionService:
        """Create an ingestion service for testing."""
        return IngestionService(corpus_store=corpus_store)

    def test_complete_workflow(
        self,
        corpus_store: SQLiteCorpusStore,
        ingestion_service: IngestionService,
    ):
        """Test complete workflow: create corpus, ingest documents, verify storage."""
        # Step 1: Create a corpus
        corpus = Corpus(
            id="research-corpus-1",
            type="research",
            name="Test Research Corpus",
            description="A corpus for integration testing",
        )
        created_corpus = corpus_store.create_corpus(corpus)

        assert created_corpus.id == corpus.id

        # Step 2: Ingest multiple documents
        doc1_text = """
        This is the first test document.

        It contains multiple paragraphs to test chunking behavior.
        The ingestion service should split this into appropriate chunks.

        Each chunk should maintain references to the parent document.
        """

        doc2_text = """
        Second document with different content.

        This document discusses different topics and should be stored separately.
        It also tests deduplication functionality.
        """

        doc1, chunks1 = ingestion_service.ingest_text(
            corpus.id,
            doc1_text,
            metadata={"title": "Document 1", "author": "Test Author"},
        )

        doc2, chunks2 = ingestion_service.ingest_text(
            corpus.id,
            doc2_text,
            metadata={"title": "Document 2", "author": "Test Author"},
        )

        # Step 3: Verify documents are stored
        retrieved_doc1 = corpus_store.get_document(doc1.id)
        assert retrieved_doc1 is not None
        assert retrieved_doc1.id == doc1.id
        assert retrieved_doc1.metadata["title"] == "Document 1"

        retrieved_doc2 = corpus_store.get_document(doc2.id)
        assert retrieved_doc2 is not None
        assert retrieved_doc2.id == doc2.id

        # Step 4: Verify listing documents
        all_docs = corpus_store.list_documents(corpus.id)
        assert len(all_docs) == 2
        doc_ids = {d.id for d in all_docs}
        assert doc1.id in doc_ids
        assert doc2.id in doc_ids

        # Step 5: Verify chunks were created
        assert len(chunks1) >= 1
        assert len(chunks2) >= 1

        # All chunks should reference their parent documents
        for chunk in chunks1:
            assert chunk.document_id == doc1.id
            assert chunk.corpus_id == corpus.id

        for chunk in chunks2:
            assert chunk.document_id == doc2.id
            assert chunk.corpus_id == corpus.id

        # Step 6: Test deduplication
        doc1_duplicate, chunks1_dup = ingestion_service.ingest_text(
            corpus.id,
            doc1_text,
            metadata={"title": "Duplicate", "author": "Different Author"},
        )

        # Should return the same document ID (deduplicated)
        assert doc1_duplicate.id == doc1.id

        # Should still only have 2 documents
        all_docs = corpus_store.list_documents(corpus.id)
        assert len(all_docs) == 2

    def test_multiple_corpora_isolation(
        self,
        corpus_store: SQLiteCorpusStore,
        ingestion_service: IngestionService,
    ):
        """Test that documents are isolated by corpus."""
        # Create two corpora
        corpus1 = Corpus(id="corpus-1", type="global", name="Corpus 1")
        corpus2 = Corpus(id="corpus-2", type="global", name="Corpus 2")

        corpus_store.create_corpus(corpus1)
        corpus_store.create_corpus(corpus2)

        # Add documents to each corpus
        doc1, _ = ingestion_service.ingest_text(
            corpus1.id,
            "Document in corpus 1",
            metadata={"corpus": "1"},
        )

        doc2, _ = ingestion_service.ingest_text(
            corpus2.id,
            "Document in corpus 2",
            metadata={"corpus": "2"},
        )

        # Verify documents are in the correct corpus
        corpus1_docs = corpus_store.list_documents(corpus1.id)
        corpus2_docs = corpus_store.list_documents(corpus2.id)

        assert len(corpus1_docs) == 1
        assert len(corpus2_docs) == 1
        assert corpus1_docs[0].id == doc1.id
        assert corpus2_docs[0].id == doc2.id

        # Same content in different corpora should NOT deduplicate
        doc3, _ = ingestion_service.ingest_text(
            corpus2.id,
            "Document in corpus 1",  # Same text as doc1
            metadata={"corpus": "2"},
        )

        # Should create a new document (different corpus)
        assert doc3.id != doc1.id

        corpus2_docs = corpus_store.list_documents(corpus2.id)
        assert len(corpus2_docs) == 2

    def test_file_ingestion_workflow(
        self,
        corpus_store: SQLiteCorpusStore,
        ingestion_service: IngestionService,
        tmp_path: Path,
    ):
        """Test file ingestion workflow."""
        # Create a corpus
        corpus = Corpus(id="file-corpus", type="research", name="File Corpus")
        corpus_store.create_corpus(corpus)

        # Create test files
        txt_file = tmp_path / "document.txt"
        txt_file.write_text("This is a text file for testing.")

        md_file = tmp_path / "README.md"
        md_file.write_text("# Markdown Test\n\nThis is markdown content.")

        # Ingest files
        doc1, chunks1 = ingestion_service.ingest_file(
            corpus.id,
            txt_file,
            metadata={"category": "text"},
        )

        doc2, chunks2 = ingestion_service.ingest_file(
            corpus.id,
            md_file,
            metadata={"category": "markdown"},
        )

        # Verify both were ingested
        assert doc1.metadata["file_name"] == "document.txt"
        assert doc1.metadata["file_format"] == ".txt"
        assert doc2.metadata["file_name"] == "README.md"
        assert doc2.metadata["file_format"] == ".md"

        # Verify they're in the corpus
        docs = corpus_store.list_documents(corpus.id)
        assert len(docs) == 2

    def test_corpus_deletion_cascade(
        self,
        corpus_store: SQLiteCorpusStore,
        ingestion_service: IngestionService,
    ):
        """Test that deleting a corpus also deletes its documents."""
        # Create corpus and add documents
        corpus = Corpus(id="temp-corpus", type="global", name="Temporary")
        corpus_store.create_corpus(corpus)

        doc1, _ = ingestion_service.ingest_text(corpus.id, "Document 1")
        doc2, _ = ingestion_service.ingest_text(corpus.id, "Document 2")

        # Verify documents exist
        assert corpus_store.get_document(doc1.id) is not None
        assert corpus_store.get_document(doc2.id) is not None

        # Delete corpus
        corpus_store.delete_corpus(corpus.id)

        # Verify corpus is gone
        assert corpus_store.get_corpus(corpus.id) is None

        # Verify documents are also gone (cascade delete)
        assert corpus_store.get_document(doc1.id) is None
        assert corpus_store.get_document(doc2.id) is None


class TestContainerIntegration:
    """Test dependency injection container integration."""

    def test_container_services(self, tmp_path: Path):
        """Test that container correctly wires services."""
        # Create custom settings
        settings = Container.create_settings(data_dir=tmp_path / "test_data")

        # Create services via container
        corpus_store = Container.create_corpus_store(settings)
        ingestion_service = Container.create_ingestion_service(corpus_store)

        # Verify services work together
        corpus = Corpus(id="container-test", type="global", name="Container Test")
        corpus_store.create_corpus(corpus)

        doc, chunks = ingestion_service.ingest_text(
            corpus.id,
            "Test document via container",
        )

        # Verify document was stored
        retrieved = corpus_store.get_document(doc.id)
        assert retrieved is not None
        assert retrieved.id == doc.id
