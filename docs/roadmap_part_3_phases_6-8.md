
# Roadmap Part 3 — Phases 6–8 (Full Detail)

This file covers:

- **Phase 6** – Persona Framework (PersonaRuntime + Profiles)
- **Phase 7** – MCP Server v1
- **Phase 8** – HTTP API (FastAPI)

It assumes Phases 0–5 are complete: ingestion, BM25, embeddings, hybrid search, graph v1, and ontology v0.1.

---

## Phase 6 — Persona Framework (PersonaRuntime + Profiles)

### Goals

- Implement a **Persona Framework** that turns Alavista into a set of domain experts, not just a generic search box.
- Each persona:
  - Has a scoped view of ontology (entity + relation whitelists).
  - Uses a specific combination of tools (search, graph, ingestion).
  - Operates with strict safety rules (no speculation, provenance required).
  - Optionally has its own **persona corpus** (best practices, methods, examples).
- Build a **PersonaRuntime** that:
  - Takes a question + persona.
  - Plans a reasoning strategy.
  - Executes calls against core services.
  - Returns a structured answer plus evidence.

### Design Principles

- Personas are **configuration + policy**, not custom code for each.
- PersonaRuntime is **stateless per call** (state lives in question context, not long-running sessions).
- All persona logic must remain **observable and explainable**.

---

### 6.1 Persona Model & Profiles

Directory:

```
core/personas/
  persona_base.py
  persona_registry.py
  persona_runtime.py
  persona_profiles/
    financial_forensics.yaml
    flight_analysis.yaml
    legal_review.yaml
    general_investigator.yaml
```

Personas defined in YAML as previously specced. Example profile:

```yaml
name: "General Investigator"
id: "general_investigator"
description: "Broad investigative persona that balances structural and semantic evidence."

entity_whitelist:
  - Person
  - Organization
  - Document

relation_whitelist:
  - APPEARS_IN
  - MENTIONED_WITH

strength_rules:
  strong:
    - APPEARS_IN
  weak:
    - MENTIONED_WITH

tools_allowed:
  - semantic_search
  - keyword_search
  - graph_find_entity
  - graph_neighbors
  - graph_paths

corpus:
  vector_db_path: null
  metadata_path: null
  allow_user_extension: false

reasoning:
  approach: |
    Begin by understanding the question type. Use hybrid search by default
    to pull in high-signal documents, then use graph tools for structural
    clarification when relationships are requested. Always ground answers
    in citations.

  disallowed_phrases:
    - "probably"
    - "appears to"
    - "might be"

safety:
  disclaimers:
    - "This persona reflects only explicit evidence from the corpus."
  provenance_required: true
```

### TDD for Profiles

- YAML load test to ensure all persona files parse correctly.
- Validation test to ensure whitelists only reference valid ontology types and registered tools.

---

### 6.2 PersonaBase

Module: `core/personas/persona_base.py`

Interface:

```python
class PersonaBase(ABC):
    id: str
    name: str
    description: str

    entity_whitelist: list[str]
    relation_whitelist: list[str]
    tools_allowed: list[str]

    strength_rules: dict[str, list[str]]
    reasoning_approach: str
    safety_config: dict
    corpus_config: dict

    @abstractmethod
    def select_tools(self, question: str) -> list[str]:
        ...

    @abstractmethod
    def categorize_question(self, question: str) -> str:
        """Return one of: semantic, structural, timeline, comparison."""
        ...

    @abstractmethod
    def format_answer(self, result: "PersonaAnswer") -> str:
        ...
```

Implementation approach:

- Provide a **DefaultPersona** implementation that uses heuristics:
  - Semantic vs structural: if question contains “connected to”, “relationship”, “path”, etc. → structural.
  - Timeline: if question contains explicit dates or phrases like “over time”.
  - Comparison: “compare”, “vs”, “difference between”.

Advanced classification can later use an LLM, but MVP can rely on regex/keywords.

TDD:

- Unit test heuristics for categorize_question on representative examples.
- Unit test select_tools returns only allowed tools.

---

### 6.3 PersonaRegistry

Module: `core/personas/persona_registry.py`

Responsibilities:

- Load YAML persona profiles on startup.
- Validate them (ontology + tools).
- Provide lookup by `persona_id`.

Interface:

```python
class PersonaRegistry:
    def __init__(self, ontology_service: OntologyService, tool_catalog: list[str]): ...

    def load_all(self, directory: Path) -> None: ...

    def get_persona(self, persona_id: str) -> PersonaBase: ...

    def list_personas(self) -> list[PersonaBase]: ...
```

Validation rules:

- `entity_whitelist` subset of ontology entity types.
- `relation_whitelist` subset of ontology relation types.
- `tools_allowed` subset of registered tool names (MCP tool catalog or core tool registry).

TDD:

- Invalid persona config should raise a clear error (e.g., unknown entity type).
- `list_personas` returns expected count and IDs.

---

### 6.4 PersonaRuntime

Module: `core/personas/persona_runtime.py`

Responsibilities:

- Execute one **persona-scoped reasoning cycle**:

Inputs:

- `persona_id`
- `question`
- (optionally) `topic_corpus_id` or `global_corpus_id`

Outputs:

- `PersonaAnswer` object containing:
  - `answer_text`
  - `evidence` (list of doc/chunk citations)
  - `graph_evidence` (list of nodes/edges used)
  - `reasoning_summary` (short explanation of approach)

Internal flow:

1. **Retrieve persona** from PersonaRegistry.
2. **Categorize question** using persona’s logic.
3. **Select tools** (search vs graph priority).
4. **Run retrieval**:
   - For semantic/timeline: `SearchService.search` with `mode="hybrid"`.
   - For structural: `GraphService.find_entity`, `graph_neighbors`, `graph_paths`.
5. **Aggregate evidence**:
   - Deduplicate documents and graph elements.
6. **Construct answer draft**:
   - Use LLMClient (from core/llm) to synthesize a persona-appropriate answer:
     - Provide retrieved passages.
     - Provide graph snippets.
     - Provide persona’s safety and language rules.
7. **Postprocess answer**:
   - Ensure provenance is attached.
   - Insert disclaimers if required.
   - Remove disallowed phrases.

TDD (mix of unit + integration):

- Unit tests:
  - Tool selection logic for different question types.
  - Evidence aggregation merges correctly.
- Integration tests (with mocked LLMClient):
  - `answer_question` returns populated PersonaAnswer.
  - Structural vs semantic question flows exercise different tool sets.

### Phase 6 Exit Criteria

- Persona YAMLs load and validate.
- PersonaRuntime can answer simple questions using SearchService + GraphService.
- Safety + provenance rules applied.
- All components fully unit-tested and basic integration tests pass.

---

## Phase 7 — MCP Server v1

### Goals

- Expose core Alavista capabilities to LLMs (Claude Desktop, Copilot, etc.) via MCP.
- Tools must be:
  - **Small**, **typed**, and **stateless**.
  - Mapped directly to core services.
  - Designed to operate predictably under LLM orchestration.

MCP is the “hands and eyes” of the agent; the heavy thinking lives in the core.

---

### 7.1 MCP Layout

Directory (already planned):

```
interfaces/mcp/
  mcp_server.py
  corpora_tools.py
  ingest_tools.py
  search_tools.py
  graph_tools.py
  persona_tools.py
  ontology_tools.py
```

### 7.2 Tool Design Principles

- Each tool:
  - accepts a **minimal JSON payload**.
  - returns a **structured JSON result**.
- No freeform text.
- No side effects beyond what’s explicitly part of the tool’s job.

---

### 7.3 Example Tool Definitions

#### 7.3.1 Search Tool

`search_tools.py`:

```python
async def semantic_search_tool(args: dict) -> dict:
    corpus_id = args["corpus_id"]
    query = args["query"]
    k = int(args.get("k", 20))

    result = await search_service.search(
        corpus_id=corpus_id,
        query=query,
        mode="hybrid",
        k=k,
    )

    return {
        "hits": [
            {
                "document_id": hit.document_id,
                "chunk_id": hit.chunk_id,
                "score": hit.score,
                "excerpt": hit.excerpt,
                "metadata": hit.metadata,
            }
            for hit in result.hits
        ]
    }
```

TDD:

- Test input validation (missing corpus_id/query).
- Test correct mapping from SearchService result to JSON.

---

#### 7.3.2 Graph Tool

`graph_tools.py`:

```python
async def graph_neighbors_tool(args: dict) -> dict:
    node_id = args["node_id"]
    depth = int(args.get("depth", 1))

    neighborhood = graph_service.graph_neighbors(node_id=node_id, depth=depth)

    return {
        "nodes": [n.dict() for n in neighborhood.nodes],
        "edges": [e.dict() for e in neighborhood.edges],
    }
```

TDD:

- Mock GraphService to return a small neighborhood.
- Ensure JSON structure stable and explicit.

---

#### 7.3.3 Persona Tool

`persona_tools.py`:

```python
async def persona_query_tool(args: dict) -> dict:
    persona_id = args["persona_id"]
    question = args["question"]
    topic_corpus_id = args.get("topic_corpus_id")

    answer = await persona_runtime.answer_question(
        persona_id=persona_id,
        question=question,
        topic_corpus_id=topic_corpus_id,
    )

    return {
        "answer_text": answer.answer_text,
        "evidence": [e.dict() for e in answer.evidence],
        "graph_evidence": [g.dict() for g in answer.graph_evidence],
        "reasoning_summary": answer.reasoning_summary,
    }
```

TDD:

- Integration test with mocked PersonaRuntime:
  - Validate JSON shape.
  - Validate required keys exist.

---

### 7.4 MCP Server Entrypoint

`mcp_server.py`:

- Register all tools with descriptive names:
  - `alavista.semantic_search`
  - `alavista.keyword_search`
  - `alavista.graph_find_entity`
  - `alavista.graph_neighbors`
  - `alavista.persona_query`
  - `alavista.ontology_describe_type`
- Initialize core services via DI container.
- Expose configuration flags (e.g., which corpora to expose).

TDD:

- Tool registry contains expected names.
- Health-check tool (if implemented) returns OK.

### Phase 7 Exit Criteria

- MCP server runs locally with a configured set of tools.
- LLM clients can:
  - list corpora
  - ingest resources
  - run search
  - inspect graph
  - query personas
  - introspect ontology
- Tools have tests verifying input/output contracts.

---

## Phase 8 — HTTP API (FastAPI)

### Goals

- Provide an HTTP interface for:
  - ingestion
  - search
  - persona Q&A
  - graph exploration
  - ontology inspection
- Serve as backend for future React UI or other clients.

---

### 8.1 App Layout

Files:

- `interfaces/api/schemas.py` – Pydantic models for requests/responses.
- `interfaces/api/router.py` – aggregate routers.
- `interfaces/api/routes/*.py` – route modules by domain.
- `app.py` – FastAPI app factory.

---

### 8.2 Routes (Detailed)

#### 8.2.1 Ingestion

`routes/ingest.py`:

- `POST /api/v1/ingest/text`
  - Body: `{ corpus_id: str, text: str, metadata?: dict }`
  - Calls `IngestionService.ingest_text`.
  - Returns: `{ document_id, chunk_count }`.

- `POST /api/v1/ingest/url`
  - Body: `{ corpus_id: str, url: str, metadata?: dict }`
  - Same pattern.

TDD:

- Test valid requests → 200 w/ correct response.
- Test invalid corpus_id → 404 (if CorpusStore denies it).

---

#### 8.2.2 Search

`routes/search.py`:

- `POST /api/v1/search`
  - Body: `SearchRequest`:
    - `corpus_id: str`
    - `query: str`
    - `mode: "bm25" | "vector" | "hybrid"`
    - `k: int`
  - Calls `SearchService.search`.
  - Returns `SearchResponse`.

TDD:

- Test each mode with stubbed SearchService.
- Test validation errors (missing query).

---

#### 8.2.3 Personas

`routes/personas.py`:

- `GET /api/v1/personas`
  - Returns a list of persona summaries: `{id, name, description}`.

- `GET /api/v1/personas/{persona_id}`
  - Returns a detailed persona summary (without internal config like disallowed phrases unless explicitly exposed).

`routes/persona_qna.py`:

- `POST /api/v1/personas/{persona_id}/answer`
  - Body: `PersonaQuestionRequest`.
  - Calls `PersonaRuntime.answer_question`.
  - Returns `PersonaAnswerResponse`.

TDD:

- Ensure `GET /personas` returns non-empty list after registry init.
- Q&A route returns shape that matches `PersonaAnswerResponse`.

---

#### 8.2.4 Graph

`routes/graph.py`:

- `POST /api/v1/graph/find_entity`
- `POST /api/v1/graph/neighbors`
- `POST /api/v1/graph/paths`
- `GET /api/v1/graph/stats/{node_id}`

Each route thinly delegates to GraphService.

TDD:

- GraphService mocked; responses shape-checked.

---

#### 8.2.5 Ontology

`routes/ontology.py`:

- `GET /api/v1/ontology/entities`
- `GET /api/v1/ontology/relations`
- `GET /api/v1/ontology/entity/{type}`
- `GET /api/v1/ontology/relation/{type}`

Backed by OntologyService.

TDD:

- Basic coverage to ensure all routes respond and match schema.

---

### 8.3 App Factory & Wiring

`app.py`:

```python
def create_app() -> FastAPI:
    settings = Settings()
    container = build_container(settings)

    app = FastAPI(title="Alavista API", version="0.1.0")

    app.include_router(build_corpora_router(container), prefix="/api/v1")
    app.include_router(build_ingest_router(container), prefix="/api/v1")
    app.include_router(build_search_router(container), prefix="/api/v1")
    app.include_router(build_persona_router(container), prefix="/api/v1")
    app.include_router(build_persona_qna_router(container), prefix="/api/v1")
    app.include_router(build_graph_router(container), prefix="/api/v1")
    app.include_router(build_ontology_router(container), prefix="/api/v1")

    return app
```

TDD:

- Use `TestClient` to instantiate app and hit each route.
- Ensure DI container wiring works and services are resolved.

---

### 8.4 CORS & Security (MVP)

- CORS:
  - disabled for local use or set to `["http://localhost:3000"]` if React UI is running.
- Auth:
  - not implemented for MVP; all endpoints assume trusted environment.
  - design API so authentication middleware can be inserted later without breaking route contracts.

---

### Phase 8 Exit Criteria

- `uvicorn app:create_app` runs, exposing `/api/v1` endpoints.
- All ingestion, search, persona, graph, and ontology endpoints behave as expected.
- Tests cover:
  - request validation
  - core-service integration via mocks
  - basic error conditions

---

**End of Roadmap Part 3 (Phases 6–8).**
