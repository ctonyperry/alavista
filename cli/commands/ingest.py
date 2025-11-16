"""CLI commands for document ingestion."""

from pathlib import Path

import typer
from rich.console import Console

from alavista.core.container import Container

app = typer.Typer()
console = Console()


@app.command("text")
def ingest_text(
    corpus_id: str = typer.Argument(..., help="Corpus ID"),
    text: str = typer.Argument(..., help="Text to ingest"),
):
    """Ingest plain text into a corpus."""
    corpus_store = Container.get_corpus_store()
    ingestion_service = Container.get_ingestion_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(corpus_id)
    if not corpus:
        console.print(f"[red]Error:[/red] Corpus '{corpus_id}' not found")
        raise typer.Exit(1)

    # Ingest
    try:
        document, chunks = ingestion_service.ingest_text(
            corpus_id=corpus_id, text=text, metadata={"source_type": "cli_text"}
        )

        console.print(f"[green]OK[/green] Ingested text")
        console.print(f"[dim]Document ID:[/dim] {document.id}")
        console.print(f"[dim]Chunks:[/dim] {len(chunks)}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("file")
def ingest_file(
    corpus_id: str = typer.Argument(..., help="Corpus ID"),
    file_path: Path = typer.Argument(..., help="Path to file", exists=True),
):
    """Ingest a file into a corpus."""
    corpus_store = Container.get_corpus_store()
    ingestion_service = Container.get_ingestion_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(corpus_id)
    if not corpus:
        console.print(f"[red]Error:[/red] Corpus '{corpus_id}' not found")
        raise typer.Exit(1)

    # Ingest
    try:
        console.print(f"Ingesting [cyan]{file_path.name}[/cyan]...")
        document, chunks = ingestion_service.ingest_file(
            corpus_id=corpus_id,
            file_path=str(file_path),
            metadata={"source_type": "cli_file", "filename": file_path.name},
        )

        console.print(f"[green]OK[/green] Ingested file '{file_path.name}'")
        console.print(f"[dim]Document ID:[/dim] {document.id}")
        console.print(f"[dim]Chunks:[/dim] {len(chunks)}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("url")
def ingest_url(
    corpus_id: str = typer.Argument(..., help="Corpus ID"),
    url: str = typer.Argument(..., help="URL to ingest"),
):
    """Ingest content from a URL into a corpus."""
    corpus_store = Container.get_corpus_store()
    ingestion_service = Container.get_ingestion_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(corpus_id)
    if not corpus:
        console.print(f"[red]Error:[/red] Corpus '{corpus_id}' not found")
        raise typer.Exit(1)

    # Ingest
    try:
        console.print(f"Fetching [cyan]{url}[/cyan]...")
        document, chunks = ingestion_service.ingest_url(
            corpus_id=corpus_id, url=url, metadata={"source_type": "cli_url", "url": url}
        )

        console.print(f"[green]OK[/green] Ingested URL")
        console.print(f"[dim]Document ID:[/dim] {document.id}")
        console.print(f"[dim]Chunks:[/dim] {len(chunks)}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
