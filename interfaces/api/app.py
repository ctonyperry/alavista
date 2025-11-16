"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alavista.core.container import Container
from interfaces.api.routes import (
    corpora_router,
    graph_rag_router,
    graph_router,
    ingest_router,
    ontology_router,
    personas_router,
    search_router,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Initialize services via DI container
    Container.get_settings()

    app = FastAPI(
        title="Alavista API",
        description="Local-first investigative analysis platform",
        version="0.1.0",
    )

    # Configure CORS for local development
    # In production, this should be restricted to specific origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # React dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(corpora_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(personas_router, prefix="/api/v1")
    app.include_router(graph_router, prefix="/api/v1")
    app.include_router(graph_rag_router, prefix="/api/v1")
    app.include_router(ontology_router, prefix="/api/v1")
    app.include_router(ingest_router, prefix="/api/v1")

    @app.get("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "ok"}

    return app
