"""CLI commands for graph operations."""

import typer
from rich.console import Console
from rich.table import Table

from alavista.core.container import Container

app = typer.Typer()
console = Console()


@app.command("find-entity")
def find_entity(
    name: str = typer.Argument(..., help="Entity name to search for"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum results"),
):
    """Find entities by name."""
    graph_service = Container.get_graph_service()

    try:
        nodes = graph_service.find_entity(name=name)

        if not nodes:
            console.print(f"[yellow]No entities found matching '{name}'[/yellow]")
            return

        # Limit results
        nodes = nodes[:limit]

        table = Table(title=f"Entities matching '{name}'")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="blue")

        for node in nodes:
            table.add_row(node.id, node.name, node.type)

        console.print(table)
        console.print(f"\n[dim]Found {len(nodes)} entities[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("neighbors")
def neighbors(
    node_id: str = typer.Argument(..., help="Node ID"),
    depth: int = typer.Option(1, "--depth", "-d", help="Search depth"),
):
    """Get neighbors of a node."""
    graph_service = Container.get_graph_service()

    try:
        neighborhood = graph_service.graph_neighbors(node_id=node_id, depth=depth)

        if not neighborhood.nodes:
            console.print(f"[yellow]Node '{node_id}' not found or has no neighbors[/yellow]")
            return

        console.print(f"\n[bold]Neighbors of node '{node_id}'[/bold] (depth={depth})\n")

        # Show nodes
        nodes_table = Table(title="Nodes")
        nodes_table.add_column("ID", style="cyan")
        nodes_table.add_column("Name", style="green")
        nodes_table.add_column("Type", style="blue")

        for node in neighborhood.nodes:
            nodes_table.add_row(node.id, node.name, node.type)

        console.print(nodes_table)

        # Show edges
        if neighborhood.edges:
            console.print()
            edges_table = Table(title="Edges")
            edges_table.add_column("Source", style="cyan")
            edges_table.add_column("Relation", style="yellow")
            edges_table.add_column("Target", style="cyan")

            for edge in neighborhood.edges:
                edges_table.add_row(edge.source_id, edge.relation_type, edge.target_id)

            console.print(edges_table)

        console.print(
            f"\n[dim]Found {len(neighborhood.nodes)} nodes and {len(neighborhood.edges)} edges[/dim]"
        )

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("paths")
def paths(
    start_id: str = typer.Argument(..., help="Start node ID"),
    end_id: str = typer.Argument(..., help="End node ID"),
    max_hops: int = typer.Option(4, "--max-hops", "-m", help="Maximum path length"),
):
    """Find paths between two nodes."""
    graph_service = Container.get_graph_service()

    try:
        graph_paths = graph_service.graph_paths(
            start_id=start_id, end_id=end_id, max_hops=max_hops
        )

        if not graph_paths:
            console.print(
                f"[yellow]No paths found between '{start_id}' and '{end_id}'[/yellow]"
            )
            return

        console.print(
            f"\n[bold]Paths from '{start_id}' to '{end_id}'[/bold] (max hops={max_hops})\n"
        )

        for i, path in enumerate(graph_paths, 1):
            console.print(f"[cyan]Path {i}:[/cyan] {' → '.join(path.nodes)}")

        console.print(f"\n[dim]Found {len(graph_paths)} paths[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("stats")
def stats(
    node_id: str = typer.Argument(..., help="Node ID"),
):
    """Show statistics for a node."""
    graph_service = Container.get_graph_service()

    try:
        node_stats = graph_service.graph_stats(node_id=node_id)

        if not node_stats:
            console.print(f"[yellow]Node '{node_id}' not found[/yellow]")
            return

        console.print(f"\n[bold]Node Statistics:[/bold] {node_id}\n")
        console.print(f"[dim]Degree:[/dim] {node_stats.get('degree', 0)}")
        console.print(f"[dim]In-degree:[/dim] {node_stats.get('in_degree', 0)}")
        console.print(f"[dim]Out-degree:[/dim] {node_stats.get('out_degree', 0)}")

        relations = node_stats.get("relations_by_type", {})
        if relations:
            console.print(f"\n[bold]Relations by Type:[/bold]")
            for rel_type, count in relations.items():
                console.print(f"  [cyan]{rel_type}:[/cyan] {count}")

        console.print(
            f"\n[dim]Connected documents:[/dim] {node_stats.get('connected_docs', 0)}"
        )

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
