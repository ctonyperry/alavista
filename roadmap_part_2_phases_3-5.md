
# Roadmap Part 2 — Phases 3–5 (Full Detail)

This file covers:

- **Phase 3** – Embeddings + Vector Search
- **Phase 4** – Graph Layer v1 (Nodes/Edges/Queries)
- **Phase 5** – Ontology Layer v0.1

It assumes Phases 0–2 are in place: CorpusStore, DocumentStore, IngestionService, and BM25-based SearchService v1.

---

## Phase 3 — Embeddings + Vector Search

### Goals

- Add **semantic vector search** over document chunks.
- Implement **EmbeddingService** with pluggable backends (local vs remote).
- Implement **VectorSearchService** using FAISS.
- Integrate with SearchService to support `mode = "bm25" | "vector" | "hybrid"`.
- Preserve deterministic behavior for tests.

### Design Principles

- Keep embeddings **stateless** and **idempotent**: same text → same vector.
- Vector store is an **implementation detail** behind `VectorSearchService`.
- Hybrid search remains a thin orchestrator; no application logic in the vector layer.
- All operations use **document_id + chunk_id** as stable keys.

### Components

#### 3.1 EmbeddingService

Module: `core/embeddings/service.py`

Responsibilities:

- Wrap the actual embedding model (e.g., sentence-transformers or an HTTP LLM).
- Provide batch embedding APIs.
- Hide backend-specific config and retry logic.

Interface (Python-ish):

```python
class EmbeddingService(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text in the same order."""
```

Implementation detail for MVP:

- Use a local model (e.g., `all-MiniLM-L6-v2`) via sentence-transformers OR an Ollama embedding model.
- Batch size configurable via Settings.
- Timeouts and errors surfaced as `EmbeddingError` (custom exception).

TDD:

- Unit test that `embed_texts` returns vectors with consistent dimensions.
- Test that batch size is respected (e.g., chunking internally).
- Test error propagation when backend fails (mock underlying library).

---

#### 3.2 VectorSearchService

Module: `core/vector/vector_search_service.py`

Responsibilities:

- Store vectors for each `(corpus_id, document_id, chunk_id)`.
- Execute kNN queries over embeddings.
- Provide simple persistence (FAISS index + metadata table).

Interface:

```python
class VectorSearchService(Protocol):

    async def index_embeddings(
        self,
        corpus_id: str,
        items: list[tuple[str, str, list[float]]],  # (document_id, chunk_id, vector)
    ) -> None:
        ...

    async def search(
        self,
        corpus_id: str,
        query_vector: list[float],
        k: int = 20,
    ) -> list["VectorHit"]:
        ...
```

`VectorHit`:

```python
class VectorHit(BaseModel):
    document_id: str
    chunk_id: str
    score: float  # cosine similarity or inner product
```

Persistence approach:

- Use FAISS with an `IndexFlatIP` (inner product).
- Normalize embeddings prior to indexing if required.
- Store mapping from FAISS index positions → `(document_id, chunk_id)` in a metadata table or sidecar JSON.

TDD:

- Index a small set of embeddings, test that self-query returns highest score.
- Test that requesting `k > N` caps at N.
- Test behavior for empty corpus (returns empty list).

---

#### 3.3 Hybrid Search in SearchService

Module: `core/search/search_service.py`

Extend existing `SearchService` to support modes:

- `"bm25"` – existing functionality only.
- `"vector"` – vector-only results.
- `"hybrid"` – combine BM25 and vector scores.

Hybrid strategy (MVP):

- Run BM25 search → `k_bm25` hits.
- Run vector search → `k_vector` hits.
- Merge on `(document_id, chunk_id)` with normalized scores:
  - `score_final = w_bm25 * bm25_score_normalized + w_vec * vector_score_normalized`
- Sort by `score_final` descending.

TDD:

- Unit tests for hybrid combination with mocked BM25 and vector hits.
- Edge case where only one modality has hits.
- Ensure deterministic ordering for identical scores (tie-break by doc_id/chunk_id).

---

#### 3.4 Embedding Pipeline

Module: `core/embeddings/pipeline.py`

Responsibilities:

- Generate embeddings for all chunks in a corpus.
- Support incremental updates (new documents only).
- Provide a CLI or script entry for re-indexing.

Algorithm:

1. Query `DocumentStore` for chunks lacking embeddings (no row in embedding metadata).
2. Batch texts into `EmbeddingService.embed_texts`.
3. Store vectors via `VectorSearchService.index_embeddings`.
4. Mark chunks as embedded.

TDD:

- Mock EmbeddingService + VectorSearchService and validate:
  - Only non-embedded chunks are processed.
  - Metadata updated correctly.

### Phase 3 Exit Criteria

- `SearchService` can execute `mode="bm25"`, `"vector"`, `"hybrid"`.
- Embeddings can be (re)built for any corpus from ingestion-only state.
- Unit and integration tests cover:
  - embedding generation
  - vector indexing
  - hybrid ranking
- Performance reasonable for 50k–100k chunks locally.

---

## Phase 4 — Graph Layer v1 (Nodes/Edges/Queries)

### Goals

- Implement a **minimal but functional** graph over entities and documents.
- Support:
  - `find_entity(name)`
  - `neighbors(node_id, depth)`
  - `paths(start_id, end_id, max_hops)`
  - `stats(node_id)`
- Integrate with ontology types at a basic level (entity/edge types exist as strings, full ontology enforcement comes in Phase 5).

### Design Principles

- Graph is **edge- and provenance-first**.
- Store only literal relationships from text (no inference).
- Provide a clean separation:
  - GraphStore (persistence + retrieval)
  - GraphService (domain-level operations)

---

### 4.1 Graph Models

Module: `core/graph/models.py`

```python
class GraphNode(BaseModel):
    id: str
    type: str         # e.g. "Person", "Organization", "Document"
    name: str
    aliases: list[str] = []
    metadata: dict = {}
    created_at: datetime
    updated_at: datetime


class GraphEdge(BaseModel):
    id: str
    type: str         # e.g. "APPEARS_IN", "MENTIONED_WITH"
    source: str       # node_id
    target: str       # node_id

    doc_id: str
    chunk_id: str | None = None
    excerpt: str | None = None
    page: int | None = None
    confidence: float = 1.0
    extraction_method: str  # "regex", "llm", "hybrid"
    created_at: datetime
```

TDD:

- Basic model instantiation and validation tests.
- Serialization round-trip tests.

---

### 4.2 GraphStore

Module: `core/graph/graph_store.py`

Backed by SQLite for MVP.

Tables:

- `graph_nodes(id TEXT PRIMARY KEY, type TEXT, name TEXT, aliases JSON, metadata JSON, created_at TEXT, updated_at TEXT)`
- `graph_edges(id TEXT PRIMARY KEY, type TEXT, source TEXT, target TEXT,
               doc_id TEXT, chunk_id TEXT, excerpt TEXT, page INTEGER,
               confidence REAL, extraction_method TEXT, created_at TEXT)`

Interface:

```python
class GraphStore(Protocol):
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
```

Implementation Details:

- `neighbors`:
  - BFS up to `depth`, collecting unique node_ids.
- `find_paths`:
  - BFS with path reconstruction.
  - Cap number of returned paths to avoid explosion.

TDD:

- Insert nodes and edges; assert they can be retrieved.
- Test `edges_from`, `edges_to`, `edges_between`.
- Test `neighbors` for depth=1 and depth>1.
- Test `find_paths` with small graph and known paths.

---

### 4.3 Entity Resolution (v1)

Module: `core/graph/resolution.py`

Purpose:

- Merge multiple entity mentions (names) into canonical nodes.
- Leave full ontology-aware logic to Phase 5; here we just do:
  - normalization
  - approximate string matching

Algorithm (MVP):

1. Normalize names:
   - lowercase
   - strip punctuation
   - collapse whitespace
2. Maintain a mapping:
   - normalized name → node_id
3. When inserting a new entity:
   - If normalized name already exists: treat as the same node.
   - Else: create new node.

TDD:

- Ensure that "Jeffrey Epstein" and "jeffrey epstein" resolve to one node.
- Ensure that significantly different names create distinct nodes.

Note: more sophisticated resolution (embeddings, alias lists) can be added later; for MVP this is enough to make the graph usable.

---

### 4.4 Extraction Pipeline (v1)

Module: `core/graph/extraction.py`

Purpose:

- Turn chunks into entity + relation candidates.
- For MVP, focus on:
  - `APPEARS_IN` (entity → document)
  - `MENTIONED_WITH` (entity ↔ entity)

Inputs:

- `document_id`
- `chunk_id`
- `text`

Outputs:

```python
class RawExtraction(BaseModel):
    entities: list[dict]   # {name, type?}
    relations: list[dict]  # {type, entity_a, entity_b, excerpt, confidence}
```

MVP behavior:

- Use heuristic regex + simple NER if available (e.g., spaCy), but keep this optional.
- For each named entity:
  - Create node via resolution logic.
  - Add `APPEARS_IN` edge to Document node.
- For co-occurring entities in the same sentence:
  - Add `MENTIONED_WITH` edges.

TDD:

- Mock text input and assert expected nodes + edges.
- Ensure no edges are created when no entities found.
- Ensure excerpt snippets are stored.

---

### 4.5 GraphService

Module: `core/graph/graph_service.py`

High-level API:

```python
class GraphService:
    def find_entity(self, name: str) -> list[GraphNode]: ...
    def graph_neighbors(self, node_id: str, depth: int = 1) -> GraphNeighborhood: ...
    def graph_paths(self, start_id: str, end_id: str, max_hops: int = 4) -> list[GraphPath]: ...
    def graph_stats(self, node_id: str) -> dict: ...
```

`GraphNeighborhood` contains:

- nodes
- edges
- provenance summary per node

`GraphStats` example:

```python
{
  "degree": 7,
  "in_degree": 3,
  "out_degree": 4,
  "relations_by_type": {"APPEARS_IN": 5, "MENTIONED_WITH": 2},
  "connected_docs": 3
}
```

TDD:

- Use a small fixture graph to validate:
  - `find_entity` returns correct candidates.
  - `graph_neighbors` returns correct sets.
  - `graph_paths` returns shortest paths.
  - `graph_stats` reports correct values.

### Phase 4 Exit Criteria

- GraphStore + GraphService fully implemented and tested.
- Extraction pipeline can populate graph from a sample corpus.
- MCP/HTTP layers (later phases) will be able to use find/neighbor/path/stats without modification.

---

## Phase 5 — Ontology Layer v0.1

### Goals

- Introduce a **minimal ontology** describing:
  - entity types
  - relation types
  - domain/range constraints
- Enforce ontology in:
  - extraction (reject invalid types/relations)
  - graph insertion (GraphStore/GraphService)
- Provide OntologyService for introspection and validation.

### Ontology Storage

File: `ontology/ontology_v0.1.json`

Shape:

```json
{
  "version": "0.1",
  "entities": {
    "Person": { "description": "...", "aliases": ["Individual"] },
    "Organization": { "description": "...", "aliases": ["Org"] },
    "Document": { "description": "...", "aliases": ["Doc"] }
  },
  "relations": {
    "APPEARS_IN": {
      "description": "Entity explicitly appears in a document.",
      "domain": ["Person", "Organization"],
      "range": ["Document"]
    },
    "MENTIONED_WITH": {
      "description": "Two entities co-mentioned in text.",
      "domain": ["Person", "Organization"],
      "range": ["Person", "Organization"]
    }
  }
}
```

MVP entities/relations:

- Entities:
  - Person
  - Organization
  - Document
- Relations:
  - APPEARS_IN
  - MENTIONED_WITH

Later versions add Flights, Accounts, Properties, Transactions, etc.

---

### 5.1 OntologyService

Module: `core/ontology/service.py`

Responsibilities:

- Load ontology JSON.
- Provide lookup and validation APIs.

Interface:

```python
class OntologyService:

    def list_entity_types(self) -> list[str]: ...

    def list_relation_types(self) -> list[str]: ...

    def get_entity_info(self, entity_type: str) -> dict: ...

    def get_relation_info(self, relation_type: str) -> dict: ...

    def resolve_entity_type(self, name_or_alias: str) -> str | None: ...

    def validate_relation(
        self,
        subject_type: str,
        relation_type: str,
        object_type: str,
    ) -> bool:
        ...
```

TDD:

- Load ontology and verify types/relations.
- Test alias resolution.
- Test domain/range validation for valid and invalid combinations.

---

### 5.2 Integration with Extraction

Modify `core/graph/extraction.py`:

- When creating entities:
  - If a type is inferred or specified, validate via `OntologyService`.
  - If unknown type: either default to "Person"/"Organization" or discard (depending on persona + config later).
- When creating relations:
  - Only create if `OntologyService.validate_relation(subject_type, relation_type, object_type)` returns true.

TDD:

- Tests where extraction tries to create invalid relation; ensure it is dropped.
- Tests where valid relations survive.

---

### 5.3 Integration with GraphService

GraphService now:

- Rejects insertion of edges whose `type` is not recognized by the ontology.
- Optionally logs a warning or raises a controlled `OntologyError` if strict mode is enabled.

TDD:

- Insert edge with invalid relation type → error/ignored.
- Insert node with invalid type → error/ignored.

---

### 5.4 Ontology Introspection for Higher Layers

OntologyService is also used by:

- PersonaRuntime (later): to limit reasoning to allowed entity/relation types.
- MCP tools and HTTP API: to surface ontology definitions and help agents decide which tools/queries to run.

For now (Phase 5):

- Ensure OntologyService can be safely called from outside core (exported via DI).
- Do not yet build MCP/HTTP endpoints (those come in later phases).

---

### Phase 5 Exit Criteria

- `ontology_v0.1.json` is present and well-formed.
- OntologyService fully implemented and tested.
- Extraction + GraphService enforce ontology constraints.
- Graph nodes/edges have valid types and relations only.
- Higher layers can safely assume ontology discipline, reducing hallucination risk later.

---

**End of Roadmap Part 2 (Phases 3–5).**
