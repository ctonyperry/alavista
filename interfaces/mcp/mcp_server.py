"""MCP (Model Context Protocol) server for Alavista.

This module provides the MCP server implementation that exposes Alavista's
capabilities to LLM clients via the Model Context Protocol.

The server registers all available tools and handles tool execution requests.
"""

import logging
from typing import Any, Callable

from interfaces.mcp import (
    get_corpus_tool,
    graph_find_entity_tool,
    graph_neighbors_tool,
    graph_paths_tool,
    ingest_file_tool,
    ingest_text_tool,
    keyword_search_tool,
    list_corpora_tool,
    list_personas_tool,
    ontology_describe_type_tool,
    ontology_list_entities_tool,
    ontology_list_relations_tool,
    persona_query_tool,
    semantic_search_tool,
)

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP server that exposes Alavista tools to LLM clients."""

    def __init__(self):
        """Initialize the MCP server and register all tools."""
        self.tools: dict[str, Callable] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all available tools with the server."""
        # Corpus management tools
        self.tools["alavista.list_corpora"] = list_corpora_tool
        self.tools["alavista.get_corpus"] = get_corpus_tool

        # Search tools
        self.tools["alavista.semantic_search"] = semantic_search_tool
        self.tools["alavista.keyword_search"] = keyword_search_tool

        # Graph tools
        self.tools["alavista.graph_find_entity"] = graph_find_entity_tool
        self.tools["alavista.graph_neighbors"] = graph_neighbors_tool
        self.tools["alavista.graph_paths"] = graph_paths_tool

        # Persona tools
        self.tools["alavista.list_personas"] = list_personas_tool
        self.tools["alavista.persona_query"] = persona_query_tool

        # Ontology tools
        self.tools["alavista.ontology_list_entities"] = ontology_list_entities_tool
        self.tools["alavista.ontology_list_relations"] = ontology_list_relations_tool
        self.tools["alavista.ontology_describe_type"] = ontology_describe_type_tool

        # Ingestion tools
        self.tools["alavista.ingest_text"] = ingest_text_tool
        self.tools["alavista.ingest_file"] = ingest_file_tool

        logger.info(f"Registered {len(self.tools)} MCP tools")

    def list_tools(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def execute_tool(self, tool_name: str, args: dict) -> dict:
        """Execute a tool by name with the provided arguments.

        Args:
            tool_name: Name of the tool to execute
            args: Arguments to pass to the tool

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
            Exception: Any exception raised by the tool
        """
        if tool_name not in self.tools:
            raise ValueError(
                f"Tool '{tool_name}' not found. "
                f"Available tools: {', '.join(self.list_tools())}"
            )

        tool = self.tools[tool_name]
        logger.info(f"Executing tool: {tool_name}")

        try:
            result = tool(args)
            logger.info(f"Tool {tool_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            raise

    def get_tool_info(self) -> dict[str, dict[str, Any]]:
        """Get information about all registered tools.

        Returns:
            Dict mapping tool names to their info
        """
        return {
            "alavista.list_corpora": {
                "description": "List all available corpora",
                "args": {},
            },
            "alavista.get_corpus": {
                "description": "Get detailed information about a specific corpus",
                "args": {"corpus_id": "string (required)"},
            },
            "alavista.semantic_search": {
                "description": "Execute semantic/hybrid search over a corpus",
                "args": {
                    "corpus_id": "string (required)",
                    "query": "string (required)",
                    "k": "integer (optional, default 20)",
                },
            },
            "alavista.keyword_search": {
                "description": "Execute keyword (BM25) search over a corpus",
                "args": {
                    "corpus_id": "string (required)",
                    "query": "string (required)",
                    "k": "integer (optional, default 20)",
                },
            },
            "alavista.graph_find_entity": {
                "description": "Find entities by name in the knowledge graph",
                "args": {"name": "string (required)"},
            },
            "alavista.graph_neighbors": {
                "description": "Get neighbors of a node in the knowledge graph",
                "args": {
                    "node_id": "string (required)",
                    "depth": "integer (optional, default 1)",
                },
            },
            "alavista.graph_paths": {
                "description": "Find paths between two nodes",
                "args": {
                    "start_id": "string (required)",
                    "end_id": "string (required)",
                    "max_hops": "integer (optional, default 4)",
                },
            },
            "alavista.list_personas": {
                "description": "List all available personas (analysis profiles)",
                "args": {},
            },
            "alavista.persona_query": {
                "description": "Execute a persona-scoped question answering pass",
                "args": {
                    "persona_id": "string (required)",
                    "question": "string (required)",
                    "corpus_id": "string (required)",
                    "k": "integer (optional, default 20)",
                },
            },
            "alavista.ontology_list_entities": {
                "description": "List all entity types in the ontology",
                "args": {},
            },
            "alavista.ontology_list_relations": {
                "description": "List all relation types in the ontology",
                "args": {},
            },
            "alavista.ontology_describe_type": {
                "description": "Get detailed information about an entity or relation type",
                "args": {
                    "type_name": "string (required)",
                    "type_kind": "string (optional, 'entity' or 'relation', default 'entity')",
                },
            },
            "alavista.ingest_text": {
                "description": "Ingest raw text into a corpus",
                "args": {
                    "corpus_id": "string (required)",
                    "text": "string (required)",
                    "metadata": "object (optional)",
                },
            },
            "alavista.ingest_file": {
                "description": "Ingest a file into a corpus",
                "args": {
                    "corpus_id": "string (required)",
                    "file_path": "string (required)",
                    "metadata": "object (optional)",
                },
            },
        }


# Global server instance
_server: MCPServer | None = None


def get_mcp_server() -> MCPServer:
    """Get the global MCP server instance.

    Returns:
        MCPServer singleton instance
    """
    global _server
    if _server is None:
        _server = MCPServer()
    return _server
