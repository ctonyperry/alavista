"""Main CLI entry point for Alavista."""

import typer
from rich.console import Console

from cli.commands import corpora, graph, ingest, search

# Create the main app
app = typer.Typer(
    name="alavista",
    help="Alavista - Local-first investigative analysis platform",
    no_args_is_help=True,
)

# Create console for rich output
console = Console()

# Register command groups
app.add_typer(corpora.app, name="corpora", help="Manage corpora")
app.add_typer(ingest.app, name="ingest", help="Ingest documents")
app.add_typer(search.app, name="search", help="Search documents")
app.add_typer(graph.app, name="graph", help="Graph operations")


@app.command()
def version():
    """Show version information."""
    console.print("[bold blue]Alavista[/bold blue] version 0.1.0")
    console.print("Local-first investigative analysis platform")


def run():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    run()
