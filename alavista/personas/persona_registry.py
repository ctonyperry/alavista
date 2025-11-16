"""Persona registry for loading and managing persona configurations."""

import logging
from pathlib import Path
from typing import Optional

import yaml

from alavista.ontology.service import OntologyService
from alavista.personas.models import PersonaConfig
from alavista.personas.persona_base import DefaultPersona, PersonaBase

logger = logging.getLogger(__name__)


class PersonaValidationError(Exception):
    """Raised when a persona configuration is invalid."""

    pass


class PersonaRegistry:
    """Registry for loading and managing personas."""

    def __init__(
        self, ontology_service: OntologyService, allowed_tools: Optional[list[str]] = None
    ):
        """Initialize the registry.

        Args:
            ontology_service: Service for validating entity/relation types
            allowed_tools: Optional list of allowed tool names. If None, all tools allowed.
        """
        self.ontology_service = ontology_service
        self.allowed_tools = allowed_tools or []
        self._personas: dict[str, PersonaBase] = {}

    def load_all(self, directory: Path) -> None:
        """Load all persona YAML files from a directory.

        Args:
            directory: Path to directory containing persona YAML files

        Raises:
            PersonaValidationError: If any persona is invalid
        """
        if not directory.exists():
            logger.warning(f"Persona directory does not exist: {directory}")
            return

        yaml_files = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))

        if not yaml_files:
            logger.warning(f"No YAML files found in {directory}")
            return

        for yaml_file in yaml_files:
            try:
                self.load_from_file(yaml_file)
            except Exception as e:
                logger.error(f"Failed to load persona from {yaml_file}: {e}")
                raise PersonaValidationError(
                    f"Failed to load persona from {yaml_file}: {e}"
                ) from e

        logger.info(f"Loaded {len(self._personas)} personas from {directory}")

    def load_from_file(self, filepath: Path) -> PersonaBase:
        """Load a single persona from a YAML file.

        Args:
            filepath: Path to YAML file

        Returns:
            Loaded PersonaBase instance

        Raises:
            PersonaValidationError: If persona is invalid
        """
        with open(filepath) as f:
            data = yaml.safe_load(f)

        config = PersonaConfig(**data)

        # Validate the configuration
        self._validate_config(config)

        # Create persona instance (using DefaultPersona for now)
        persona = DefaultPersona(config)

        # Register it
        self._personas[persona.id] = persona

        logger.info(f"Loaded persona: {persona.id} ({persona.name})")
        return persona

    def _validate_config(self, config: PersonaConfig) -> None:
        """Validate a persona configuration.

        Args:
            config: PersonaConfig to validate

        Raises:
            PersonaValidationError: If configuration is invalid
        """
        # Validate entity types
        entity_types = self.ontology_service.list_entity_types()
        for entity_type in config.entity_whitelist:
            if entity_type not in entity_types:
                raise PersonaValidationError(
                    f"Unknown entity type '{entity_type}' in persona '{config.id}'. "
                    f"Valid types: {entity_types}"
                )

        # Validate relation types
        relation_types = self.ontology_service.list_relation_types()
        for relation_type in config.relation_whitelist:
            if relation_type not in relation_types:
                raise PersonaValidationError(
                    f"Unknown relation type '{relation_type}' in persona '{config.id}'. "
                    f"Valid types: {relation_types}"
                )

        # Validate tools (if allowed_tools is specified)
        if self.allowed_tools:
            for tool in config.tools_allowed:
                if tool not in self.allowed_tools:
                    raise PersonaValidationError(
                        f"Unknown tool '{tool}' in persona '{config.id}'. "
                        f"Valid tools: {self.allowed_tools}"
                    )

        # Validate strength rules reference valid relations
        for strength_category in config.strength_rules.values():
            for relation in strength_category:
                if relation not in config.relation_whitelist:
                    raise PersonaValidationError(
                        f"Strength rule references relation '{relation}' "
                        f"not in relation_whitelist for persona '{config.id}'"
                    )

    def get_persona(self, persona_id: str) -> Optional[PersonaBase]:
        """Get a persona by ID.

        Args:
            persona_id: ID of the persona

        Returns:
            PersonaBase instance or None if not found
        """
        return self._personas.get(persona_id)

    def list_personas(self) -> list[PersonaBase]:
        """List all loaded personas.

        Returns:
            List of PersonaBase instances
        """
        return list(self._personas.values())

    def list_persona_ids(self) -> list[str]:
        """List all persona IDs.

        Returns:
            List of persona IDs
        """
        return list(self._personas.keys())

    def get_persona_summary(self, persona_id: str) -> Optional[dict]:
        """Get a summary of a persona (safe for API exposure).

        Args:
            persona_id: ID of the persona

        Returns:
            Dictionary with id, name, description or None if not found
        """
        persona = self.get_persona(persona_id)
        if not persona:
            return None

        return {
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "entity_types": persona.entity_whitelist,
            "relation_types": persona.relation_whitelist,
            "tools": persona.tools_allowed,
        }

    def list_persona_summaries(self) -> list[dict]:
        """List summaries of all personas.

        Returns:
            List of persona summary dictionaries
        """
        return [
            self.get_persona_summary(persona_id)
            for persona_id in self.list_persona_ids()
            if self.get_persona_summary(persona_id) is not None
        ]
