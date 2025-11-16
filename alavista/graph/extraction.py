from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from alavista.ontology.service import OntologyService


def filter_entities(
    entities: Iterable[Dict[str, Any]],
    ontology: OntologyService,
) -> List[Dict[str, Any]]:
    """
    Keep only entities whose type is recognized by the ontology.
    Unknown types are discarded.
    """
    accepted = []
    for ent in entities:
        etype = ent.get("type")
        if not etype:
            continue
        resolved = ontology.resolve_entity_type(etype)
        if resolved:
            ent["type"] = resolved
            accepted.append(ent)
    return accepted


def filter_relations(
    relations: Iterable[Dict[str, Any]],
    ontology: OntologyService,
) -> List[Dict[str, Any]]:
    """
    Keep only relations whose (subject_type, relation_type, object_type)
    are valid per ontology.
    """
    accepted = []
    for rel in relations:
        subj = rel.get("subject_type")
        rel_type = rel.get("type")
        obj = rel.get("object_type")
        if not (subj and rel_type and obj):
            continue
        if ontology.validate_relation(subj, rel_type, obj):
            accepted.append(rel)
    return accepted
