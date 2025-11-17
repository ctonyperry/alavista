"""API routes."""

from interfaces.api.routes.corpora import router as corpora_router
from interfaces.api.routes.graph import router as graph_router
from interfaces.api.routes.graph_rag import router as graph_rag_router
from interfaces.api.routes.ingest import router as ingest_router
from interfaces.api.routes.ontology import router as ontology_router
from interfaces.api.routes.personas import router as personas_router
from interfaces.api.routes.runs import router as runs_router
from interfaces.api.routes.search import router as search_router

__all__ = [
    "corpora_router",
    "graph_router",
    "graph_rag_router",
    "ingest_router",
    "ontology_router",
    "personas_router",
    "runs_router",
    "search_router",
]
