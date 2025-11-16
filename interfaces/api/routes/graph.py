"""Graph routes."""

from fastapi import APIRouter

from alavista.core.container import Container
from interfaces.api.schemas import (
    GraphEdge,
    GraphFindEntityRequest,
    GraphFindEntityResponse,
    GraphNeighborsRequest,
    GraphNeighborsResponse,
    GraphNode,
    GraphPathsRequest,
    GraphPathsResponse,
)

router = APIRouter(tags=["graph"])


@router.post("/graph/find_entity", response_model=GraphFindEntityResponse)
def find_entity(request: GraphFindEntityRequest):
    """Find entities by name."""
    graph_service = Container.get_graph_service()

    nodes = graph_service.find_entity(name=request.name)

    # Limit results if requested
    limited_nodes = nodes[: request.limit]

    return GraphFindEntityResponse(
        nodes=[
            GraphNode(
                id=node.id,
                type=node.type,
                name=node.name,
                properties=node.properties,
            )
            for node in limited_nodes
        ]
    )


@router.post("/graph/neighbors", response_model=GraphNeighborsResponse)
def get_neighbors(request: GraphNeighborsRequest):
    """Get neighbors of a node."""
    graph_service = Container.get_graph_service()

    neighborhood = graph_service.graph_neighbors(
        node_id=request.node_id,
        depth=request.depth,
    )

    return GraphNeighborsResponse(
        nodes=[
            GraphNode(
                id=node.id,
                type=node.type,
                name=node.name,
                properties=node.properties,
            )
            for node in neighborhood.nodes
        ],
        edges=[
            GraphEdge(
                source_id=edge.source_id,
                target_id=edge.target_id,
                relation_type=edge.relation_type,
                properties=edge.properties,
            )
            for edge in neighborhood.edges
        ],
    )


@router.post("/graph/paths", response_model=GraphPathsResponse)
def find_paths(request: GraphPathsRequest):
    """Find paths between nodes."""
    graph_service = Container.get_graph_service()

    graph_paths = graph_service.graph_paths(
        start_id=request.start_node_id,
        end_id=request.end_node_id,
        max_hops=request.max_depth,
    )

    return GraphPathsResponse(paths=[path.nodes for path in graph_paths])
