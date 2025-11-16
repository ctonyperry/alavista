"""MCP tools for document ingestion."""

from pathlib import Path

from alavista.core.container import Container


def ingest_text_tool(args: dict) -> dict:
    """Ingest raw text into a corpus.

    Args:
        args: dict with 'corpus_id', 'text', and optional 'metadata'

    Returns:
        dict with 'document_id' and 'chunk_count'

    Raises:
        ValueError: If required args missing or corpus not found
    """
    corpus_id = args.get("corpus_id")
    text = args.get("text")
    metadata = args.get("metadata", {})

    if not corpus_id:
        raise ValueError("corpus_id is required")
    if not text:
        raise ValueError("text is required")

    corpus_store = Container.get_corpus_store()
    ingestion_service = Container.get_ingestion_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(corpus_id)
    if not corpus:
        raise ValueError(f"Corpus '{corpus_id}' not found")

    # Ingest text
    document, chunks = ingestion_service.ingest_text(
        corpus_id=corpus_id,
        text=text,
        metadata=metadata,
    )

    return {
        "document_id": document.id,
        "chunk_count": len(chunks),
        "content_hash": document.content_hash,
    }


def ingest_file_tool(args: dict) -> dict:
    """Ingest a file into a corpus.

    Args:
        args: dict with 'corpus_id', 'file_path', and optional 'metadata'

    Returns:
        dict with 'document_id' and 'chunk_count'

    Raises:
        ValueError: If required args missing, corpus not found, or file invalid
    """
    corpus_id = args.get("corpus_id")
    file_path = args.get("file_path")
    metadata = args.get("metadata", {})

    if not corpus_id:
        raise ValueError("corpus_id is required")
    if not file_path:
        raise ValueError("file_path is required")

    corpus_store = Container.get_corpus_store()
    ingestion_service = Container.get_ingestion_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(corpus_id)
    if not corpus:
        raise ValueError(f"Corpus '{corpus_id}' not found")

    # Verify file exists
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise ValueError(f"File '{file_path}' not found")

    # Ingest file
    document, chunks = ingestion_service.ingest_file(
        corpus_id=corpus_id,
        file_path=file_path_obj,
        metadata=metadata,
    )

    return {
        "document_id": document.id,
        "chunk_count": len(chunks),
        "content_hash": document.content_hash,
        "file_path": str(file_path_obj),
    }
