"""MCP tools for ontology inspection."""

from alavista.core.container import Container


def ontology_list_entities_tool(args: dict) -> dict:
    """List all entity types defined in the ontology.

    Args:
        args: Empty dict (no arguments required)

    Returns:
        dict with 'entity_types' list
    """
    ontology_service = Container.get_ontology_service()
    entity_types = ontology_service.list_entity_types()

    return {"entity_types": entity_types}


def ontology_list_relations_tool(args: dict) -> dict:
    """List all relation types defined in the ontology.

    Args:
        args: Empty dict (no arguments required)

    Returns:
        dict with 'relation_types' list
    """
    ontology_service = Container.get_ontology_service()
    relation_types = ontology_service.list_relation_types()

    return {"relation_types": relation_types}


def ontology_describe_type_tool(args: dict) -> dict:
    """Get detailed information about an entity or relation type.

    Args:
        args: dict with 'type_name' and 'type_kind' ('entity' or 'relation')

    Returns:
        dict with type information

    Raises:
        ValueError: If required args missing or type not found
    """
    type_name = args.get("type_name")
    type_kind = args.get("type_kind", "entity")

    if not type_name:
        raise ValueError("type_name is required")

    ontology_service = Container.get_ontology_service()

    if type_kind == "entity":
        info = ontology_service.get_entity_info(type_name)
        if not info:
            raise ValueError(f"Entity type '{type_name}' not found in ontology")
        return {"type": "entity", "name": type_name, "info": info}

    elif type_kind == "relation":
        info = ontology_service.get_relation_info(type_name)
        if not info:
            raise ValueError(f"Relation type '{type_name}' not found in ontology")
        return {"type": "relation", "name": type_name, "info": info}

    else:
        raise ValueError(f"Invalid type_kind '{type_kind}'. Must be 'entity' or 'relation'")
