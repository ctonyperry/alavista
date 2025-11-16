from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OntologyError(Exception):
    pass


class OntologyService:
    def __init__(self, ontology_path: Path):
        self.ontology_path = Path(ontology_path)
        if not self.ontology_path.exists():
            raise OntologyError(f"Ontology file not found: {self.ontology_path}")
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        try:
            with self.ontology_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise OntologyError(f"Failed to load ontology: {e}") from e

    def list_entity_types(self) -> list[str]:
        return list(self._data.get("entities", {}).keys())

    def list_relation_types(self) -> list[str]:
        return list(self._data.get("relations", {}).keys())

    def get_entity_info(self, entity_type: str) -> dict | None:
        return self._data.get("entities", {}).get(entity_type)

    def get_relation_info(self, relation_type: str) -> dict | None:
        return self._data.get("relations", {}).get(relation_type)

    def resolve_entity_type(self, name_or_alias: str) -> str | None:
        name_lower = name_or_alias.lower()
        entities = self._data.get("entities", {})
        for etype, info in entities.items():
            if etype.lower() == name_lower:
                return etype
            for alias in info.get("aliases", []):
                if alias.lower() == name_lower:
                    return etype
        return None

    def validate_relation(self, subject_type: str, relation_type: str, object_type: str) -> bool:
        rel = self._data.get("relations", {}).get(relation_type)
        if not rel:
            return False
        domain = rel.get("domain", [])
        range_ = rel.get("range", [])
        return subject_type in domain and object_type in range_
