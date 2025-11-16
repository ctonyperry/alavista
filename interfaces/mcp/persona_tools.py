"""MCP tools for persona operations."""

from pathlib import Path

from alavista.core.container import Container


def list_personas_tool(args: dict) -> dict:
    """List all available personas (analysis profiles).

    Args:
        args: Empty dict (no arguments required)

    Returns:
        dict with 'personas' list containing persona summaries
    """
    persona_registry = Container.get_persona_registry()
    summaries = persona_registry.list_persona_summaries()

    return {"personas": summaries}


def persona_query_tool(args: dict) -> dict:
    """Execute a persona-scoped question answering pass.

    Args:
        args: dict with 'persona_id', 'question', 'corpus_id', and optional 'k' (default 20)

    Returns:
        dict with answer, evidence, graph_evidence, and reasoning_summary

    Raises:
        ValueError: If required args missing
    """
    persona_id = args.get("persona_id")
    question = args.get("question")
    corpus_id = args.get("corpus_id")
    k = int(args.get("k", 20))

    if not persona_id:
        raise ValueError("persona_id is required")
    if not question:
        raise ValueError("question is required")
    if not corpus_id:
        raise ValueError("corpus_id is required")

    persona_runtime = Container.get_persona_runtime()

    answer = persona_runtime.answer_question(
        persona_id=persona_id,
        question=question,
        corpus_id=corpus_id,
        k=k,
    )

    return {
        "answer_text": answer.answer_text,
        "evidence": answer.evidence,
        "graph_evidence": answer.graph_evidence,
        "reasoning_summary": answer.reasoning_summary,
        "persona_id": answer.persona_id,
        "disclaimers": answer.disclaimers,
        "timestamp": answer.timestamp.isoformat(),
    }


def persona_ingest_resource_tool(args: dict) -> dict:
    """Ingest a resource (text, file, or URL) into a persona's manual corpus.

    Args:
        args: dict with required keys:
            - persona_id: ID of the persona
            - resource_type: "text", "file", or "url"
            - content: For text type, the text content
            - file_path: For file type, the path to the file
            - url: For url type, the URL to fetch
            - metadata: Optional dict of additional metadata

    Returns:
        dict with document_id, chunk_count, and status

    Raises:
        ValueError: If required args missing or invalid resource_type
    """
    persona_id = args.get("persona_id")
    resource_type = args.get("resource_type")
    metadata = args.get("metadata", {})

    if not persona_id:
        raise ValueError("persona_id is required")
    if not resource_type:
        raise ValueError("resource_type is required")

    ingestion_service = Container.get_ingestion_service()

    # Handle different resource types
    if resource_type == "text":
        content = args.get("content")
        if not content:
            raise ValueError("content is required for resource_type='text'")

        document, chunks = ingestion_service.ingest_persona_text(
            persona_id=persona_id,
            text=content,
            metadata=metadata,
        )

    elif resource_type == "file":
        file_path = args.get("file_path")
        if not file_path:
            raise ValueError("file_path is required for resource_type='file'")

        document, chunks = ingestion_service.ingest_persona_file(
            persona_id=persona_id,
            file_path=Path(file_path),
            metadata=metadata,
        )

    elif resource_type == "url":
        url = args.get("url")
        if not url:
            raise ValueError("url is required for resource_type='url'")

        document, chunks = ingestion_service.ingest_persona_url(
            persona_id=persona_id,
            url=url,
            metadata=metadata,
        )

    else:
        raise ValueError(
            f"Invalid resource_type '{resource_type}'. "
            "Must be 'text', 'file', or 'url'"
        )

    return {
        "status": "success",
        "document_id": document.id,
        "chunk_count": len(chunks),
        "persona_id": persona_id,
        "resource_type": resource_type,
    }
