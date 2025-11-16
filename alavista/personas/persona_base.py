"""Base persona interface and default implementation."""

import re
from abc import ABC, abstractmethod

from alavista.personas.models import PersonaAnswer, PersonaConfig, QuestionCategory


class PersonaBase(ABC):
    """Abstract base class for all personas."""

    def __init__(self, config: PersonaConfig):
        """Initialize persona with configuration.

        Args:
            config: Persona configuration loaded from YAML
        """
        self.config = config
        self.id = config.id
        self.name = config.name
        self.description = config.description
        self.entity_whitelist = config.entity_whitelist
        self.relation_whitelist = config.relation_whitelist
        self.tools_allowed = config.tools_allowed
        self.strength_rules = config.strength_rules
        self.reasoning_approach = config.reasoning.get("approach", "")
        self.safety_config = config.safety
        self.corpus_config = config.corpus

    @abstractmethod
    def select_tools(self, question: str, category: QuestionCategory) -> list[str]:
        """Select which tools to use for this question.

        Args:
            question: The user's question
            category: Categorization of the question

        Returns:
            List of tool names to use
        """
        pass

    @abstractmethod
    def categorize_question(self, question: str) -> QuestionCategory:
        """Categorize the question type.

        Args:
            question: The user's question

        Returns:
            QuestionCategory with type and confidence
        """
        pass

    @abstractmethod
    def format_answer(self, result: PersonaAnswer) -> str:
        """Format the answer for display.

        Args:
            result: The PersonaAnswer object

        Returns:
            Formatted string for display
        """
        pass


class DefaultPersona(PersonaBase):
    """Default persona implementation with heuristic-based logic."""

    # Question categorization patterns
    STRUCTURAL_PATTERNS = [
        r"\bconnected to\b",
        r"\brelationship\b",
        r"\bpath\b",
        r"\blinks?\b",
        r"\bassociat(ed|ion)\b",
        r"\btie(s|d)? to\b",
        r"\bnetwork\b",
    ]

    TIMELINE_PATTERNS = [
        r"\bover time\b",
        r"\btimeline\b",
        r"\bwhen\b",
        r"\bdate(s)?\b",
        r"\bchronolog",
        r"\bhistor",
        r"\bevolution\b",
        r"\b\d{4}\b",  # Year mention
    ]

    COMPARISON_PATTERNS = [
        r"\bcompare\b",
        r"\bvs\.?\b",
        r"\bversus\b",
        r"\bdifference(s)?\b",
        r"\bsimilarit(y|ies)\b",
        r"\bsimilar\b",
        r"\bcontrast\b",
        r"\bbetter\b",
        r"\bworse\b",
    ]

    def categorize_question(self, question: str) -> QuestionCategory:
        """Categorize question using heuristic patterns.

        Args:
            question: The user's question

        Returns:
            QuestionCategory object
        """
        question_lower = question.lower()

        # Check patterns in priority order
        if any(re.search(pattern, question_lower) for pattern in self.STRUCTURAL_PATTERNS):
            return QuestionCategory(
                category="structural",
                confidence=0.8,
                reasoning="Question contains structural/relationship keywords",
            )

        if any(re.search(pattern, question_lower) for pattern in self.TIMELINE_PATTERNS):
            return QuestionCategory(
                category="timeline",
                confidence=0.7,
                reasoning="Question contains temporal keywords",
            )

        if any(re.search(pattern, question_lower) for pattern in self.COMPARISON_PATTERNS):
            return QuestionCategory(
                category="comparison",
                confidence=0.7,
                reasoning="Question contains comparison keywords",
            )

        # Default to semantic
        return QuestionCategory(
            category="semantic",
            confidence=0.5,
            reasoning="No specific patterns matched, defaulting to semantic search",
        )

    def select_tools(self, question: str, category: QuestionCategory) -> list[str]:
        """Select tools based on question category.

        Args:
            question: The user's question
            category: Categorization result

        Returns:
            List of tool names to use
        """
        tools = []

        if category.category == "structural":
            # Prioritize graph tools for structural questions
            if "graph_find_entity" in self.tools_allowed:
                tools.append("graph_find_entity")
            if "graph_neighbors" in self.tools_allowed:
                tools.append("graph_neighbors")
            if "graph_paths" in self.tools_allowed:
                tools.append("graph_paths")
            # Still include search for context
            if "semantic_search" in self.tools_allowed:
                tools.append("semantic_search")

        elif category.category == "timeline":
            # Timeline questions benefit from search + potential graph context
            if "semantic_search" in self.tools_allowed:
                tools.append("semantic_search")
            if "keyword_search" in self.tools_allowed:
                tools.append("keyword_search")

        elif category.category == "comparison":
            # Comparison needs search to gather both sides
            if "semantic_search" in self.tools_allowed:
                tools.append("semantic_search")
            if "graph_neighbors" in self.tools_allowed:
                tools.append("graph_neighbors")

        else:
            # Semantic default: hybrid search
            if "semantic_search" in self.tools_allowed:
                tools.append("semantic_search")
            if "keyword_search" in self.tools_allowed:
                tools.append("keyword_search")

        # Return only allowed tools
        return [tool for tool in tools if tool in self.tools_allowed]

    def format_answer(self, result: PersonaAnswer) -> str:
        """Format answer with citations and disclaimers.

        Args:
            result: PersonaAnswer object

        Returns:
            Formatted markdown string
        """
        output = []

        # Add answer text
        output.append(result.answer_text)
        output.append("")

        # Add evidence if present
        if result.evidence:
            output.append("## Evidence")
            for i, ev in enumerate(result.evidence[:5], 1):  # Limit to top 5
                doc_id = ev.get("document_id", "unknown")
                excerpt = ev.get("excerpt", "")[:200]
                output.append(f"{i}. `{doc_id}`: {excerpt}...")

            if len(result.evidence) > 5:
                output.append(f"\n_({len(result.evidence) - 5} more citations available)_")
            output.append("")

        # Add graph evidence if present
        if result.graph_evidence:
            output.append("## Graph Connections")
            for i, ge in enumerate(result.graph_evidence[:5], 1):
                node_type = ge.get("type", "Node")
                name = ge.get("name", "unknown")
                output.append(f"{i}. **{node_type}**: {name}")

            if len(result.graph_evidence) > 5:
                output.append(
                    f"\n_({len(result.graph_evidence) - 5} more graph elements available)_"
                )
            output.append("")

        # Add reasoning summary
        if result.reasoning_summary:
            output.append(f"**Approach**: {result.reasoning_summary}")
            output.append("")

        # Add disclaimers
        if result.disclaimers:
            output.append("---")
            for disclaimer in result.disclaimers:
                output.append(f"_{disclaimer}_")

        return "\n".join(output)
