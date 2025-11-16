"""MCP tools for corpus management."""

from alavista.core.container import Container


def list_corpora_tool(args: dict) -> dict:
    """List all available corpora.

    Args:
        args: Empty dict (no arguments required)

    Returns:
        dict with 'corpora' list containing corpus summaries
    """
    corpus_store = Container.get_corpus_store()
    corpora = corpus_store.list_corpora()

    return {
        "corpora": [
            {
                "id": corpus.id,
                "type": corpus.type,
                "name": corpus.name,
                "metadata": corpus.metadata,
                "created_at": corpus.created_at.isoformat(),
            }
            for corpus in corpora
        ]
    }


def get_corpus_tool(args: dict) -> dict:
    """Get detailed information about a specific corpus.

    Args:
        args: dict with 'corpus_id' key

    Returns:
        dict with corpus details and document count

    Raises:
        ValueError: If corpus_id is missing or corpus not found
    """
    corpus_id = args.get("corpus_id")
    if not corpus_id:
        raise ValueError("corpus_id is required")

    corpus_store = Container.get_corpus_store()
    corpus = corpus_store.get_corpus(corpus_id)

    if not corpus:
        raise ValueError(f"Corpus '{corpus_id}' not found")

    documents = corpus_store.list_documents(corpus_id)

    return {
        "corpus": {
            "id": corpus.id,
            "type": corpus.type,
            "name": corpus.name,
            "metadata": corpus.metadata,
            "created_at": corpus.created_at.isoformat(),
            "document_count": len(documents),
        }
    }
