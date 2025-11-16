"""
CorpusStore implementation for persisting corpora and documents.

This module provides SQLite-backed storage for corpus and document management
with deduplication support.
"""

import json
import sqlite3
from pathlib import Path
from typing import Protocol

from alavista.core.models import Corpus, Document


class CorpusStore(Protocol):
    """
    Protocol defining the interface for corpus and document storage.

    This allows for different implementations (SQLite, PostgreSQL, etc.)
    while maintaining a consistent interface.
    """

    def create_corpus(self, corpus: Corpus) -> Corpus:
        """Create a new corpus."""
        ...

    def get_corpus(self, corpus_id: str) -> Corpus | None:
        """Get a corpus by ID."""
        ...

    def list_corpora(self) -> list[Corpus]:
        """List all corpora."""
        ...

    def delete_corpus(self, corpus_id: str) -> bool:
        """Delete a corpus and all its documents."""
        ...

    def add_document(self, document: Document) -> Document:
        """Add a document to a corpus."""
        ...

    def get_document(self, doc_id: str) -> Document | None:
        """Get a document by ID."""
        ...

    def list_documents(self, corpus_id: str) -> list[Document]:
        """List all documents in a corpus."""
        ...

    def find_by_hash(self, corpus_id: str, content_hash: str) -> Document | None:
        """Find a document by content hash for deduplication."""
        ...


class SQLiteCorpusStore:
    """
    SQLite-backed implementation of CorpusStore.

    Stores corpora and documents in a SQLite database with JSON metadata support.
    """

    def __init__(self, db_path: Path | str):
        """
        Initialize the corpus store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with foreign keys enabled.

        Returns:
            SQLite connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS corpora (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    persona_id TEXT,
                    topic_id TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    corpus_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (corpus_id) REFERENCES corpora(id) ON DELETE CASCADE
                )
            """)

            # Index for deduplication
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_hash
                ON documents(corpus_id, content_hash)
            """)

            # Index for corpus lookup
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_corpus
                ON documents(corpus_id)
            """)

            conn.commit()

    def create_corpus(self, corpus: Corpus) -> Corpus:
        """
        Create a new corpus.

        Args:
            corpus: Corpus to create

        Returns:
            The created corpus

        Raises:
            sqlite3.IntegrityError: If corpus with same ID already exists
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO corpora (id, type, persona_id, topic_id, name, description, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    corpus.id,
                    corpus.type,
                    corpus.persona_id,
                    corpus.topic_id,
                    corpus.name,
                    corpus.description,
                    json.dumps(corpus.metadata),
                    corpus.created_at.isoformat(),
                ),
            )
            conn.commit()

        return corpus

    def get_corpus(self, corpus_id: str) -> Corpus | None:
        """
        Get a corpus by ID.

        Args:
            corpus_id: ID of the corpus to retrieve

        Returns:
            Corpus if found, None otherwise
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM corpora WHERE id = ?",
                (corpus_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return Corpus(
            id=row["id"],
            type=row["type"],
            persona_id=row["persona_id"],
            topic_id=row["topic_id"],
            name=row["name"],
            description=row["description"],
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
        )

    def list_corpora(self) -> list[Corpus]:
        """
        List all corpora.

        Returns:
            List of all corpora
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM corpora ORDER BY created_at DESC")
            rows = cursor.fetchall()

        return [
            Corpus(
                id=row["id"],
                type=row["type"],
                persona_id=row["persona_id"],
                topic_id=row["topic_id"],
                name=row["name"],
                description=row["description"],
                metadata=json.loads(row["metadata"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def delete_corpus(self, corpus_id: str) -> bool:
        """
        Delete a corpus and all its documents.

        Args:
            corpus_id: ID of the corpus to delete

        Returns:
            True if corpus was deleted, False if not found
        """
        with self._get_connection() as conn:
            # SQLite handles CASCADE delete for documents
            cursor = conn.execute("DELETE FROM corpora WHERE id = ?", (corpus_id,))
            conn.commit()
            return cursor.rowcount > 0

    def add_document(self, document: Document) -> Document:
        """
        Add a document to a corpus.

        Args:
            document: Document to add

        Returns:
            The added document

        Raises:
            sqlite3.IntegrityError: If document with same ID already exists
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents (id, corpus_id, text, content_hash, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    document.id,
                    document.corpus_id,
                    document.text,
                    document.content_hash,
                    json.dumps(document.metadata),
                    document.created_at.isoformat(),
                ),
            )
            conn.commit()

        return document

    def get_document(self, doc_id: str) -> Document | None:
        """
        Get a document by ID.

        Args:
            doc_id: ID of the document to retrieve

        Returns:
            Document if found, None otherwise
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM documents WHERE id = ?",
                (doc_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return Document(
            id=row["id"],
            corpus_id=row["corpus_id"],
            text=row["text"],
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
        )

    def list_documents(self, corpus_id: str) -> list[Document]:
        """
        List all documents in a corpus.

        Args:
            corpus_id: ID of the corpus

        Returns:
            List of documents in the corpus
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM documents WHERE corpus_id = ? ORDER BY created_at DESC",
                (corpus_id,),
            )
            rows = cursor.fetchall()

        return [
            Document(
                id=row["id"],
                corpus_id=row["corpus_id"],
                text=row["text"],
                content_hash=row["content_hash"],
                metadata=json.loads(row["metadata"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def find_by_hash(self, corpus_id: str, content_hash: str) -> Document | None:
        """
        Find a document by content hash for deduplication.

        Args:
            corpus_id: ID of the corpus to search in
            content_hash: Content hash to search for

        Returns:
            Document if found, None otherwise
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM documents WHERE corpus_id = ? AND content_hash = ?",
                (corpus_id, content_hash),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return Document(
            id=row["id"],
            corpus_id=row["corpus_id"],
            text=row["text"],
            content_hash=row["content_hash"],
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
        )
