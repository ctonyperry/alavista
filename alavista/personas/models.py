"""Persona models and data structures."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class PersonaAnswer(BaseModel):
    """Structured answer from a persona."""

    answer_text: str = Field(description="The main answer text")
    evidence: list[dict[str, Any]] = Field(
        default_factory=list, description="Document/chunk citations"
    )
    graph_evidence: list[dict[str, Any]] = Field(
        default_factory=list, description="Graph nodes/edges used"
    )
    reasoning_summary: str = Field(
        default="", description="Short explanation of approach used"
    )
    persona_id: str = Field(description="ID of the persona that answered")
    disclaimers: list[str] = Field(default_factory=list, description="Safety disclaimers")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PersonaConfig(BaseModel):
    """Configuration for a persona loaded from YAML."""

    name: str = Field(description="Display name of the persona")
    id: str = Field(description="Unique identifier")
    description: str = Field(description="What this persona does")

    entity_whitelist: list[str] = Field(
        default_factory=list, description="Allowed entity types"
    )
    relation_whitelist: list[str] = Field(
        default_factory=list, description="Allowed relation types"
    )
    strength_rules: dict[str, list[str]] = Field(
        default_factory=dict, description="Categorization of relation strengths"
    )
    tools_allowed: list[str] = Field(
        default_factory=list, description="Tools this persona can use"
    )

    corpus: dict[str, Any] = Field(
        default_factory=dict, description="Persona-specific corpus configuration"
    )
    reasoning: dict[str, Any] = Field(
        default_factory=dict, description="Reasoning approach and constraints"
    )
    safety: dict[str, Any] = Field(
        default_factory=dict, description="Safety rules and disclaimers"
    )

    model_config = {"extra": "allow"}  # Allow additional fields from YAML


class QuestionCategory(BaseModel):
    """Categorization of a user question."""

    category: str = Field(
        description="One of: semantic, structural, timeline, comparison, other"
    )
    confidence: float = Field(default=1.0, description="Confidence in categorization")
    reasoning: str = Field(default="", description="Why this category was chosen")
