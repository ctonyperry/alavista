
# Alavista – Interfaces & Tools Specification (MCP + HTTP API)

This document defines how external actors communicate with Alavista via two primary surfaces:

1. **MCP Tools** – for LLM agents (Claude Desktop, Copilot Agents, GPT-based orchestrators).  
2. **HTTP API (FastAPI)** – for UIs, scripts, dashboards, or headless programmatic usage.

The interfaces layer must be:

- Thin  
- Declarative  
- Free of business logic  
- Fully dependent on the core services (never the reverse)  
- Stable and versionable

---

# 1. Architecture Overview

```
interfaces/
  api/
    schemas.py
    router.py
    routes/
      corpora.py
      ingest.py
      search.py
      analysis profiles.py
      persona_qna.py
      graph.py
      ontology.py

  mcp/
    mcp_server.py
    corpora_tools.py
    ingest_tools.py
    search_tools.py
    persona_tools.py
    graph_tools.py
    ontology_tools.py
```

Bootstraps:

- `app.py` – creates the FastAPI app, wires core services and routers  
- `mcp_entry.py` – instantiates the MCP server, registers tools, begins runtime  

---

# 2. Shared Schemas (`api/schemas.py`)

Schemas mirror core models but are API‑friendly. Examples:

```python
class CorpusCreateRequest(BaseModel):
    id: str | None = None
    type: Literal["persona_manual", "research", "global"] = "research"
    persona_id: str | None = None
    topic_id: str | None = None
    name: str
    description: str | None = None
    metadata: dict = {}
```

Search:

```python
class SearchRequest(BaseModel):
    corpus_id: str
    query: str
    mode: Literal["bm25", "vector", "hybrid"] = "hybrid"
    k: int = 20
```

Analysis Profile Q&A:

```python
class PersonaQuestionRequest(BaseModel):  # To be renamed AnalysisProfileQuestionRequest
    persona_id: str  # To be renamed analysis_profile_id or profile_id
    topic_corpus_id: str
    question: str
```

Graph:

```python
class GraphFindEntityRequest(BaseModel):
    name: str
```

Ontology:

```python
class OntologyTypeDescribeRequest(BaseModel):
    type: str
```

---

# 3. HTTP API Specification

All endpoints serve JSON and follow REST semantics.

Base path: `/api/v1`

## 3.1 Corpora Routes

**POST** `/corpora`  
Create a new corpus.

**GET** `/corpora`  
List corpora.

**GET** `/corpora/{corpus_id}`  
Fetch metadata for a corpus.

---

## 3.2 Ingestion Routes

**POST** `/ingest/text`  
- `{ corpus_id, text, metadata? }`  
- Calls `IngestionService.ingest_text`.

**POST** `/ingest/url`  
- `{ corpus_id, url, metadata? }`  
- Calls `IngestionService.ingest_url`.

**POST** `/ingest/file`  
- Accepts multipart upload  
- Calls `IngestionService.ingest_file`.

---

## 3.3 Search Routes

**POST** `/search`  
- Performs semantic, hybrid, or BM25 search  
- Calls `SearchService.search`.

---

## 3.4 Analysis Profile Routes

**GET** `/personas`  (to be renamed `/analysis-profiles` or `/profiles`)
List available analysis profiles.

**GET** `/personas/{persona_id}`  (to be renamed `/analysis-profiles/{profile_id}`)
Return analysis profile metadata.

---

## 3.5 Analysis Profile Q&A Routes

**POST** `/personas/{persona_id}/answer`  (to be renamed `/analysis-profiles/{profile_id}/answer`)
- Executes `PersonaRuntime` (to be renamed `AnalysisProfileRuntime`) reasoning  
- Returns structured `PersonaAnswer` (to be renamed `AnalysisProfileAnswer`).

---

## 3.6 Graph Routes

**POST** `/graph/find_entity`  
Identifier resolution.

**POST** `/graph/neighbors`  
Local subgraph extraction.

**POST** `/graph/paths`  
Multi-hop path discovery.

**GET** `/graph/stats/{node_id}`  
Return degree, relation distribution, etc.

---

## 3.7 Ontology Routes

**GET** `/ontology/entities`  
List ontology entity types.

**GET** `/ontology/relations`  
List ontology relation types.

**GET** `/ontology/entity/{type}`  
Inspect entity type.

**GET** `/ontology/relation/{type}`  
Inspect relation type.

---

# 4. MCP Tool Specification

The MCP server provides typesafe tools for LLMs.  
Tools must be:

- Stateless  
- Pure adapters  
- Structured  
- Deterministic

## 4.1 Corpora Tools

- `list_corpora()`
- `create_corpus({...})`

## 4.2 Ingestion Tools

- `ingest_text({...})`
- `ingest_url({...})`
- `ingest_file_reference({...})`

## 4.3 Search Tools

- `semantic_search({...})`
- `keyword_search({...})`

## 4.4 Graph Tools

- `graph_find_entity(name)`
- `graph_neighbors({node_id, depth, filters})`
- `graph_paths({start_id, end_id, max_hops})`
- `graph_stats(node_id)`

## 4.5 Analysis Profile Tools

Current tool names (to be renamed in future implementation):

- `persona_list()` (to be renamed `analysis_profile_list` or `profile_list`)
- `persona_query({persona_id, topic_corpus_id, question})` (to be renamed with `analysis_profile_id` or `profile_id`)
- `persona_ingest_resource({persona_id, url|file})` (to be renamed `analysis_profile_ingest_resource`)
- `persona_inspect(persona_id)` (to be renamed `analysis_profile_inspect` or `profile_inspect`)
- `persona_explain({persona_id, question})` (to be renamed `analysis_profile_explain` or `profile_explain`)

## 4.6 Ontology Tools

- `ontology_describe_type(type)`
- `ontology_list_relations_for_entity_type(type)`
- `ontology_help()`

---

# 5. Error Handling

Errors are mapped to clean surface formats:

HTTP:
- 400 for invalid input  
- 404 for missing resource  
- 422 for validation errors  
- 503 for backend LLM issues  

MCP:
```json
{
  "error": {
    "type": "SearchError",
    "message": "Invalid query mode"
  }
}
```

---

# 6. Security Considerations

MVP assumes trusted local deployment.  
Future extensions:

- API keys  
- Analysis Profile‑scoped RBAC  
- Source ingestion permissioning  

No decisions here constrain future hardening.

---

# 7. Testing Strategy

FastAPI TestClient for HTTP:

- corpora CRUD  
- ingest text/url/file  
- search  
- persona_qna  
- graph  
- ontology  

MCP unit tests:

- validate tool argument schemas  
- validate correct mapping to core services  
- validate structured response shapes  

---

# 8. Definition of Done

Interfaces layer is complete when:

- HTTP API routes for corpora, ingest, search, analysis profiles, persona_qna, graph, ontology implemented  
- MCP tools for all major capabilities implemented  
- All mapping functions use core services without embedding logic  
- 80%+ test coverage for both HTTP and MCP surfaces  
- One‑line local startup for both API and MCP servers  

