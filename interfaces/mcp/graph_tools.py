"""MCP tools for graph operations."""

from alavista.core.container import Container


def graph_find_entity_tool(args: dict) -> dict:
    """Find entities by name in the knowledge graph.

    Args:
        args: dict with 'name' to search for

    Returns:
        dict with 'entities' list containing matching nodes

    Raises:
        ValueError: If name is missing
    """
    name = args.get("name")
    if not name:
        raise ValueError("name is required")

    graph_service = Container.get_graph_service()
    nodes = graph_service.find_entity(name)

    return {
        "entities": [
            {
                "id": node.id,
                "type": node.type,
                "name": node.name,
                "aliases": node.aliases,
                "metadata": node.metadata,
            }
            for node in nodes
        ]
    }


def graph_neighbors_tool(args: dict) -> dict:
    """Get neighbors of a node in the knowledge graph.

    Args:
        args: dict with 'node_id' and optional 'depth' (default 1)

    Returns:
        dict with 'nodes' and 'edges' lists

    Raises:
        ValueError: If node_id is missing
    """
    node_id = args.get("node_id")
    depth = int(args.get("depth", 1))

    if not node_id:
        raise ValueError("node_id is required")

    graph_service = Container.get_graph_service()
    neighborhood = graph_service.graph_neighbors(node_id=node_id, depth=depth)

    return {
        "nodes": [
            {
                "id": node.id,
                "type": node.type,
                "name": node.name,
                "aliases": node.aliases,
                "metadata": node.metadata,
            }
            for node in neighborhood.nodes
        ],
        "edges": [
            {
                "id": edge.id,
                "type": edge.type,
                "source": edge.source,
                "target": edge.target,
                "doc_id": edge.doc_id,
                "chunk_id": edge.chunk_id,
                "excerpt": edge.excerpt,
                "confidence": edge.confidence,
            }
            for edge in neighborhood.edges
        ],
    }


def graph_paths_tool(args: dict) -> dict:
    """Find paths between two nodes in the knowledge graph.

    Args:
        args: dict with 'start_id', 'end_id', and optional 'max_hops' (default 4)

    Returns:
        dict with 'paths' list, each path is a list of node IDs

    Raises:
        ValueError: If start_id or end_id is missing
    """
    start_id = args.get("start_id")
    end_id = args.get("end_id")
    max_hops = int(args.get("max_hops", 4))

    if not start_id:
        raise ValueError("start_id is required")
    if not end_id:
        raise ValueError("end_id is required")

    graph_service = Container.get_graph_service()
    paths = graph_service.graph_paths(
        start_id=start_id,
        end_id=end_id,
        max_hops=max_hops,
    )

    return {
        "paths": [
            {"node_ids": path.node_ids, "length": len(path.node_ids) - 1}
            for path in paths
        ]
    }
