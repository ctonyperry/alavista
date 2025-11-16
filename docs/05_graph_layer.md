
# Alavista – Graph Layer Specification

The graph layer gives Alavista structure.  
Search tells you *what’s relevant*, but the graph tells you *how things connect*.

This document defines:

1. Graph model  
2. Provenance and confidence model  
3. Extraction pipeline  
4. Entity resolution  
5. GraphStore  
6. GraphService  
7. Graph-guided RAG  
8. Safety/ethics constraints  
9. Testing strategy  

---

# 1. Design Philosophy

The graph must uphold:

### **1. Evidence-first**
Edges represent *only literal relationships* found in text.

### **2. Explicit provenance**
Every node and edge must include:

- `doc_id`
- `chunk_id`
- `excerpt`
- `page` (optional)
- `confidence`
- `extraction_method` (regex/LLM/hybrid)

### **3. Typed schema**
Nodes and edges use ontology types (defined in `ontology_v0.1.json`).

### **4. No hallucinated relations**
The extraction pipeline must be conservative.

### **5. Clean separation from LLMs**
The graph is deterministic; LLMs assist *only* with extraction, not inference.

### **6. Graph as a separate subsystem**
Graph logic lives in `core/graph/` and integrates with core search and ontology layers.

---

# 2. Graph Model

Directory:

```
core/graph/
    models.py
    extraction.py
    resolution.py
    graph_store.py
    graph_service.py
    graph_rag.py
```

---

## 2.1 Node Model

```python
class GraphNode(BaseModel):
    id: str                  # canonical entity ID
    type: str                # ontology entity type
    name: str                # human-readable canonical name
    aliases: list[str] = []  # merged aliases during resolution
    metadata: dict = {}      # arbitrary metadata

    created_at: datetime
    updated_at: datetime
```

Examples:

- `type="Person"`
- `type="Organization"`
- `type="Flight"`
- `type="Document"`

---

## 2.2 Edge Model

```python
class GraphEdge(BaseModel):
    id: str
    type: str                   # ontology relation type
    source: str                 # node_id
    target: str                 # node_id

    # provenance
    doc_id: str
    chunk_id: str | None = None
    excerpt: str | None = None
    page: int | None = None
    confidence: float = 1.0
    extraction_method: str      # "regex", "llm", "hybrid"

    created_at: datetime
```

Edges are **directed**, even if logically symmetric (e.g., MENTIONED_WITH).  
This allows easier path exploration.

---

## 2.3 Provenance

Every edge contains:

- `doc_id` — primary record  
- `chunk_id` — embedding chunk where detection happened  
- `excerpt` — literal text snippet  
- `source_text_range` (optional later)  
- `extraction_method` — `"regex"` or `"llm"`  
- `confidence` — 0.0–1.0 rated by extraction model 

---

# 3. Extraction Pipeline (extraction.py)

### **Purpose:**  
Transform raw text → entity mentions → relations → edges.

Works per document chunk.

---

## 3.1 Extraction Modes

### **1. Heuristic/regex**
Used for:

- Flight numbers  
- Dates  
- Dollar amounts  
- Property descriptors  
- Document metadata (people lists, email headers)

### **2. LLM-based extraction**
For contextual relationships between entities.

### **3. Hybrid mode**
Regex/heuristic extract straightforward entities;  
LLM used for relationship detection.

---

## 3.2 Extraction Output Format

```python
class RawExtraction(BaseModel):
    entities: list[dict]
    relations: list[dict]
```
Example entity:

```json
{
  "type": "Person",
  "name": "Virginia Giuffre",
  "aliases": ["Virginia Roberts"]
}
```

Example relation:

```json
{
  "type": "MENTIONED_WITH",
  "entity_a": "Jeffrey Epstein",
  "entity_b": "Alan Dershowitz",
  "excerpt": "…Epstein and Dershowitz were mentioned together...",
  "confidence": 0.83
}
```

---

# 4. Entity Resolution (resolution.py)

Merge multiple mentions of the same entity.

---

## 4.1 Resolution Algorithm

1. **Normalization**  
2. **BM25-based match**  
3. **Embedding similarity**  
4. **Alias merging**  

---

## 4.2 Output

```python
class ResolvedEntity(BaseModel):
    canonical_id: str
    type: str
    name: str
    aliases: list[str]
    merged_from: list[str]
```

---

# 5. GraphStore (graph_store.py)

SQLite-backed storage.

## 5.1 Node:

```python
def upsert_node(self, node: GraphNode) -> GraphNode: ...
def get_node(self, node_id: str) -> GraphNode | None: ...
def find_nodes_by_name(self, name: str) -> list[GraphNode]: ...
def list_nodes(self) -> list[GraphNode]: ...
```

## 5.2 Edges:

```python
def add_edge(self, edge: GraphEdge) -> GraphEdge: ...
def edges_from(self, node_id: str) -> list[GraphEdge]: ...
def edges_to(self, node_id: str) -> list[GraphEdge]: ...
def edges_between(self, a: str, b: str) -> list[GraphEdge]: ...
```

## 5.3 Graph Queries

```python
def neighbors(self, node_id: str, depth=1) -> list[GraphNode]: ...
def find_paths(self, start_id: str, end_id: str, max_hops=4): ...
def subgraph(self, node_ids: list[str]): ...
```

---

# 6. GraphService

High-level operations for investigative reasoning.

## 6.1 Find Entity

```python
def find_entity(self, name: str) -> list[GraphNode]:
```

## 6.2 Neighborhoods

```python
def graph_neighbors(self, node_id: str, depth=1, filters=None)
```

## 6.3 Paths

```python
def graph_paths(self, start_id, end_id, max_hops=4)
```

## 6.4 Stats

Return degrees, relation types, connected documents, etc.

---

# 7. Graph-RAG

Structural retrieval augmentation:

1. Identify graph entities in a question  
2. Get neighbors  
3. Fetch docs tied to edges  
4. Feed docs into SearchService  
5. Merge graph and semantic hits  

---

# 8. Safety & Ethics

1. **Only literal relationships**  
2. **Ontology-constrained extraction**  
3. **Confidence propagation**  
4. **Full provenance visible**  
5. **Clear separation: graph evidence vs analysis profile narrative**  

---

# 9. Tests

### Unit Tests:
- Node/Edge model  
- GraphStore CRUD  
- Resolution algorithm  
- Extraction regex  
- Graph queries  

### Integration Tests:
- ingest → extract → resolve → insert → query  
- graph_neighbors  
- multi-hop paths  
- graph-RAG  

---

# 10. Definition of Done

- Node/edge schema implemented  
- GraphStore finished  
- Extraction pipeline working  
- Resolution functioning  
- GraphService supports neighbors, paths, stats  
- Graph-RAG available  
- Tests > 80% coverage  

