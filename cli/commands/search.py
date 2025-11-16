"""CLI commands for searching documents."""

import typer
from rich.console import Console
from rich.table import Table

from alavista.core.container import Container
from alavista.core.models import Chunk

app = typer.Typer()
console = Console()


@app.command()
def run(
    corpus_id: str = typer.Argument(..., help="Corpus ID"),
    query: str = typer.Argument(..., help="Search query"),
    mode: str = typer.Option("bm25", "--mode", help="Search mode (bm25, vector, hybrid)"),
    k: int = typer.Option(10, "--k", "-k", help="Number of results to return"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Search documents in a corpus."""
    corpus_store = Container.get_corpus_store()
    search_service = Container.get_search_service()

    # Verify corpus exists
    corpus = corpus_store.get_corpus(corpus_id)
    if not corpus:
        console.print(f"[red]Error:[/red] Corpus '{corpus_id}' not found")
        raise typer.Exit(1)

    # Get documents and create chunks
    documents = corpus_store.list_documents(corpus_id)
    if not documents:
        console.print(f"[yellow]No documents in corpus '{corpus_id}'[/yellow]")
        raise typer.Exit(0)

    chunks = []
    for doc in documents:
        chunk = Chunk(
            id=f"{doc.id}::chunk_0",
            document_id=doc.id,
            corpus_id=corpus_id,
            text=doc.text,
            start_offset=0,
            end_offset=len(doc.text),
            metadata={"chunk_index": 0, "total_chunks": 1},
        )
        chunks.append(chunk)

    # Execute search
    try:
        results = search_service.search_bm25(
            corpus_id=corpus_id, chunks=chunks, query=query, k=k
        )

        if json_output:
            import json

            output = [
                {
                    "document_id": r.doc_id,
                    "chunk_id": r.chunk_id,
                    "score": r.score,
                    "excerpt": r.excerpt,
                }
                for r in results
            ]
            console.print(json.dumps(output, indent=2))
        else:
            if not results:
                console.print("[yellow]No results found[/yellow]")
                return

            console.print(f"\n[bold]Search Results[/bold] ({len(results)} hits)\n")

            for i, result in enumerate(results, 1):
                console.print(f"[bold cyan]{i}.[/bold cyan] Score: [green]{result.score:.4f}[/green]")
                console.print(f"[dim]Document:[/dim] {result.doc_id}")
                console.print(f"[dim]Chunk:[/dim] {result.chunk_id}")
                console.print(f"\n{result.excerpt}\n")
                console.print("[dim]" + "-" * 80 + "[/dim]\n")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
