from __future__ import annotations

import json
import sqlite3
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from alavista.graph.models import GraphEdge, GraphNode


class GraphStoreProtocol(Protocol):
    def upsert_node(self, node: GraphNode) -> GraphNode: ...
    def get_node(self, node_id: str) -> GraphNode | None: ...
    def find_nodes_by_name(self, name: str) -> list[GraphNode]: ...
    def list_nodes(self) -> list[GraphNode]: ...

    def add_edge(self, edge: GraphEdge) -> GraphEdge: ...
    def get_edge(self, edge_id: str) -> GraphEdge | None: ...
    def edges_from(self, node_id: str) -> list[GraphEdge]: ...
    def edges_to(self, node_id: str) -> list[GraphEdge]: ...
    def edges_between(self, node_a: str, node_b: str) -> list[GraphEdge]: ...

    def neighbors(self, node_id: str, depth: int = 1) -> list[GraphNode]: ...
    def find_paths(self, start_id: str, end_id: str, max_hops: int = 4) -> list[list[str]]: ...


@dataclass
class SQLiteGraphStore:
    db_path: Path

    def __post_init__(self) -> None:
        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    aliases TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS graph_edges (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    chunk_id TEXT,
                    excerpt TEXT,
                    page INTEGER,
                    confidence REAL,
                    extraction_method TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source) REFERENCES graph_nodes(id) ON DELETE CASCADE,
                    FOREIGN KEY (target) REFERENCES graph_nodes(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_name ON graph_nodes(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target)")
            conn.commit()

    # Node operations
    def upsert_node(self, node: GraphNode) -> GraphNode:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO graph_nodes (id, type, name, aliases, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type=excluded.type,
                    name=excluded.name,
                    aliases=excluded.aliases,
                    metadata=excluded.metadata,
                    updated_at=excluded.updated_at
                """,
                (
                    node.id,
                    node.type,
                    node.name,
                    json.dumps(node.aliases),
                    json.dumps(node.metadata),
                    node.created_at.isoformat(),
                    node.updated_at.isoformat(),
                ),
            )
            conn.commit()
        return node

    def get_node(self, node_id: str) -> GraphNode | None:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM graph_nodes WHERE id = ?", (node_id,))
            row = cur.fetchone()
        if not row:
            return None
        return self._row_to_node(row)

    def find_nodes_by_name(self, name: str) -> list[GraphNode]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT * FROM graph_nodes WHERE lower(name) = lower(?)",
                (name,),
            )
            rows = cur.fetchall()
        return [self._row_to_node(r) for r in rows]

    def list_nodes(self) -> list[GraphNode]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM graph_nodes")
            rows = cur.fetchall()
        return [self._row_to_node(r) for r in rows]

    # Edge operations
    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO graph_edges
                (id, type, source, target, doc_id, chunk_id, excerpt, page, confidence, extraction_method, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edge.id,
                    edge.type,
                    edge.source,
                    edge.target,
                    edge.doc_id,
                    edge.chunk_id,
                    edge.excerpt,
                    edge.page,
                    edge.confidence,
                    edge.extraction_method,
                    edge.created_at.isoformat(),
                ),
            )
            conn.commit()
        return edge

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM graph_edges WHERE id = ?", (edge_id,))
            row = cur.fetchone()
        if not row:
            return None
        return self._row_to_edge(row)

    def edges_from(self, node_id: str) -> list[GraphEdge]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM graph_edges WHERE source = ?", (node_id,))
            rows = cur.fetchall()
        return [self._row_to_edge(r) for r in rows]

    def edges_to(self, node_id: str) -> list[GraphEdge]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM graph_edges WHERE target = ?", (node_id,))
            rows = cur.fetchall()
        return [self._row_to_edge(r) for r in rows]

    def edges_between(self, node_a: str, node_b: str) -> list[GraphEdge]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                """
                SELECT * FROM graph_edges
                WHERE (source = ? AND target = ?) OR (source = ? AND target = ?)
                """,
                (node_a, node_b, node_b, node_a),
            )
            rows = cur.fetchall()
        return [self._row_to_edge(r) for r in rows]

    def neighbors(self, node_id: str, depth: int = 1) -> list[GraphNode]:
        depth = max(depth, 1)
        visited = {node_id}
        result: dict[str, GraphNode] = {}
        frontier = deque([(node_id, 0)])

        while frontier:
            current, d = frontier.popleft()
            if d >= depth:
                continue
            for edge in self.edges_from(current) + self.edges_to(current):
                neighbor_id = edge.target if edge.source == current else edge.source
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)
                node = self.get_node(neighbor_id)
                if node:
                    result[neighbor_id] = node
                frontier.append((neighbor_id, d + 1))
        return list(result.values())

    def find_paths(self, start_id: str, end_id: str, max_hops: int = 4) -> list[list[str]]:
        if start_id == end_id:
            return [[start_id]]
        max_hops = max(1, max_hops)
        paths: list[list[str]] = []
        queue = deque([[start_id]])
        visited = {start_id}
        while queue:
            path = queue.popleft()
            current = path[-1]
            if len(path) > max_hops + 1:
                continue
            for edge in self.edges_from(current) + self.edges_to(current):
                neighbor = edge.target if edge.source == current else edge.source
                if neighbor in path:
                    continue
                new_path = path + [neighbor]
                if neighbor == end_id:
                    paths.append(new_path)
                else:
                    queue.append(new_path)
                    visited.add(neighbor)
        return paths

    def _row_to_node(self, row: sqlite3.Row) -> GraphNode:
        return GraphNode(
            id=row["id"],
            type=row["type"],
            name=row["name"],
            aliases=json.loads(row["aliases"]),
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_edge(self, row: sqlite3.Row) -> GraphEdge:
        return GraphEdge(
            id=row["id"],
            type=row["type"],
            source=row["source"],
            target=row["target"],
            doc_id=row["doc_id"],
            chunk_id=row["chunk_id"],
            excerpt=row["excerpt"],
            page=row["page"],
            confidence=row["confidence"],
            extraction_method=row["extraction_method"],
            created_at=row["created_at"],
        )
