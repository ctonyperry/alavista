"""Ontology routes."""

from fastapi import APIRouter, HTTPException

from alavista.core.container import Container
from interfaces.api.schemas import (
    EntityTypeDetail,
    EntityTypeSummary,
    OntologyListResponse,
    RelationTypeDetail,
    RelationTypeSummary,
)

router = APIRouter(tags=["ontology"])


@router.get("/ontology/entities", response_model=list[EntityTypeSummary])
def list_entity_types():
    """List all entity types."""
    ontology_service = Container.get_ontology_service()
    entity_type_names = ontology_service.list_entity_types()

    return [
        EntityTypeSummary(
            name=name,
            description=ontology_service.get_entity_info(name).get(
                "description", "No description"
            ),
        )
        for name in entity_type_names
    ]


@router.get("/ontology/relations", response_model=list[RelationTypeSummary])
def list_relation_types():
    """List all relation types."""
    ontology_service = Container.get_ontology_service()
    relation_type_names = ontology_service.list_relation_types()

    return [
        RelationTypeSummary(
            name=name,
            description=ontology_service.get_relation_info(name).get(
                "description", "No description"
            ),
            domain=ontology_service.get_relation_info(name).get("domain", []),
            range=ontology_service.get_relation_info(name).get("range", []),
        )
        for name in relation_type_names
    ]


@router.get("/ontology/entity/{type_name}", response_model=EntityTypeDetail)
def get_entity_type(type_name: str):
    """Get detailed entity type information."""
    ontology_service = Container.get_ontology_service()
    entity_info = ontology_service.get_entity_info(type_name)

    if not entity_info:
        raise HTTPException(
            status_code=404, detail=f"Entity type {type_name} not found"
        )

    return EntityTypeDetail(
        name=type_name,
        description=entity_info.get("description", "No description"),
        properties=entity_info.get("properties", {}),
    )


@router.get("/ontology/relation/{type_name}", response_model=RelationTypeDetail)
def get_relation_type(type_name: str):
    """Get detailed relation type information."""
    ontology_service = Container.get_ontology_service()
    relation_info = ontology_service.get_relation_info(type_name)

    if not relation_info:
        raise HTTPException(
            status_code=404, detail=f"Relation type {type_name} not found"
        )

    return RelationTypeDetail(
        name=type_name,
        description=relation_info.get("description", "No description"),
        domain=relation_info.get("domain", []),
        range=relation_info.get("range", []),
        properties=relation_info.get("properties", {}),
    )
