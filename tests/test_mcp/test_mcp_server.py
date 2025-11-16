"""Tests for MCP server."""

import pytest

from interfaces.mcp.mcp_server import MCPServer, get_mcp_server


def test_mcp_server_initialization():
    """Test MCP server initializes and registers tools."""
    server = MCPServer()
    assert len(server.tools) > 0
    assert "alavista.list_corpora" in server.tools
    assert "alavista.semantic_search" in server.tools
    assert "alavista.persona_query" in server.tools


def test_list_tools():
    """Test listing all registered tools."""
    server = MCPServer()
    tools = server.list_tools()

    assert isinstance(tools, list)
    assert len(tools) > 0
    assert "alavista.list_corpora" in tools
    assert "alavista.graph_find_entity" in tools


def test_execute_tool_not_found():
    """Test error handling for unknown tool."""
    server = MCPServer()

    with pytest.raises(ValueError, match="Tool .* not found"):
        server.execute_tool("nonexistent.tool", {})


def test_get_tool_info():
    """Test getting tool information."""
    server = MCPServer()
    info = server.get_tool_info()

    assert isinstance(info, dict)
    assert "alavista.semantic_search" in info
    assert "description" in info["alavista.semantic_search"]
    assert "args" in info["alavista.semantic_search"]


def test_get_mcp_server_singleton():
    """Test global server singleton."""
    server1 = get_mcp_server()
    server2 = get_mcp_server()

    assert server1 is server2


def test_all_tools_registered():
    """Test that all expected tools are registered."""
    server = MCPServer()
    expected_tools = [
        "alavista.list_corpora",
        "alavista.get_corpus",
        "alavista.semantic_search",
        "alavista.keyword_search",
        "alavista.graph_find_entity",
        "alavista.graph_neighbors",
        "alavista.graph_paths",
        "alavista.list_personas",
        "alavista.persona_query",
        "alavista.ontology_list_entities",
        "alavista.ontology_list_relations",
        "alavista.ontology_describe_type",
        "alavista.ingest_text",
        "alavista.ingest_file",
    ]

    for tool_name in expected_tools:
        assert tool_name in server.tools, f"Tool {tool_name} not registered"
