"""CLI commands for managing corpora."""

import typer
from rich.console import Console
from rich.table import Table

from alavista.core.container import Container
from alavista.core.models import Corpus

app = typer.Typer()
console = Console()


@app.command("list")
def list_corpora():
    """List all corpora."""
    corpus_store = Container.get_corpus_store()
    corpora = corpus_store.list_corpora()

    if not corpora:
        console.print("[yellow]No corpora found[/yellow]")
        return

    table = Table(title="Corpora")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type", style="blue")
    table.add_column("Documents", justify="right", style="magenta")
    table.add_column("Created", style="dim")

    for corpus in corpora:
        doc_count = len(corpus_store.list_documents(corpus.id))
        table.add_row(
            corpus.id,
            corpus.name,
            corpus.type,
            str(doc_count),
            corpus.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@app.command("create")
def create_corpus(
    name: str = typer.Argument(..., help="Corpus name"),
    corpus_id: str = typer.Option(None, "--id", help="Custom corpus ID (optional)"),
    corpus_type: str = typer.Option(
        "research", "--type", help="Corpus type (persona_manual, research, global)"
    ),
):
    """Create a new corpus."""
    corpus_store = Container.get_corpus_store()

    # Generate ID if not provided
    if not corpus_id:
        import re

        corpus_id = re.sub(r"[^a-z0-9_]", "_", name.lower())

    # Check if exists
    existing = corpus_store.get_corpus(corpus_id)
    if existing:
        console.print(f"[red]Error:[/red] Corpus with ID '{corpus_id}' already exists")
        raise typer.Exit(1)

    # Create corpus
    corpus = Corpus(id=corpus_id, type=corpus_type, name=name)
    corpus_store.create_corpus(corpus)

    console.print(f"[green]OK[/green] Created corpus '{name}' (ID: {corpus_id})")


@app.command("info")
def corpus_info(
    corpus_id: str = typer.Argument(..., help="Corpus ID"),
):
    """Show detailed corpus information."""
    corpus_store = Container.get_corpus_store()
    corpus = corpus_store.get_corpus(corpus_id)

    if not corpus:
        console.print(f"[red]Error:[/red] Corpus '{corpus_id}' not found")
        raise typer.Exit(1)

    documents = corpus_store.list_documents(corpus_id)

    console.print(f"\n[bold]Corpus:[/bold] {corpus.name}")
    console.print(f"[dim]ID:[/dim] {corpus.id}")
    console.print(f"[dim]Type:[/dim] {corpus.type}")
    console.print(f"[dim]Created:[/dim] {corpus.created_at}")
    console.print(f"[dim]Documents:[/dim] {len(documents)}")

    if corpus.description:
        console.print(f"[dim]Description:[/dim] {corpus.description}")


@app.command("delete")
def delete_corpus(
    corpus_id: str = typer.Argument(..., help="Corpus ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a corpus and all its documents."""
    corpus_store = Container.get_corpus_store()
    corpus = corpus_store.get_corpus(corpus_id)

    if not corpus:
        console.print(f"[red]Error:[/red] Corpus '{corpus_id}' not found")
        raise typer.Exit(1)

    doc_count = len(corpus_store.list_documents(corpus_id))

    if not force:
        confirm = typer.confirm(
            f"Delete corpus '{corpus.name}' with {doc_count} documents?"
        )
        if not confirm:
            console.print("Cancelled")
            raise typer.Exit(0)

    corpus_store.delete_corpus(corpus_id)
    console.print(f"[green]OK[/green] Deleted corpus '{corpus.name}'")
