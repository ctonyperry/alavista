"""MCP (Model Context Protocol) server interface for Alavista."""

from interfaces.mcp.corpora_tools import list_corpora_tool, get_corpus_tool
from interfaces.mcp.search_tools import semantic_search_tool, keyword_search_tool
from interfaces.mcp.graph_tools import (
    graph_find_entity_tool,
    graph_neighbors_tool,
    graph_paths_tool,
)
from interfaces.mcp.persona_tools import list_personas_tool, persona_query_tool
from interfaces.mcp.ontology_tools import (
    ontology_list_entities_tool,
    ontology_list_relations_tool,
    ontology_describe_type_tool,
)
from interfaces.mcp.ingest_tools import ingest_text_tool, ingest_file_tool

__all__ = [
    # Corpora tools
    "list_corpora_tool",
    "get_corpus_tool",
    # Search tools
    "semantic_search_tool",
    "keyword_search_tool",
    # Graph tools
    "graph_find_entity_tool",
    "graph_neighbors_tool",
    "graph_paths_tool",
    # Persona tools
    "list_personas_tool",
    "persona_query_tool",
    # Ontology tools
    "ontology_list_entities_tool",
    "ontology_list_relations_tool",
    "ontology_describe_type_tool",
    # Ingest tools
    "ingest_text_tool",
    "ingest_file_tool",
]
