
# Roadmap Part 4 — Phases 9–11 (Full Detail)

This file covers:

- **Phase 9** – Admin & Developer UX Tools (CLI + Config)
- **Phase 10** – Analysis Profile Resource Ingestion (MCP + HTTP)
- **Phase 11** – Graph-Guided RAG

It assumes Phases 0–8 are complete and stable.

---

## Phase 9 — Admin & Developer UX Tools

### Goals

- Make Alavista **usable without touching Python** for common flows:
  - creating corpora
  - ingesting data
  - running searches
  - basic graph inspection
- Provide a simple but powerful **CLI** for local workflows.
- Implement a clean **configuration loader** so agents and humans can run the system consistently.

---

### 9.1 Configuration System

Module: `core/config/settings.py`

Use `pydantic-settings` or standard Pydantic `BaseSettings`.

Key settings:

```python
class Settings(BaseSettings):
    env: str = "dev"

    # Paths
    data_dir: Path = Path("./data")
    db_path: Path = Path("./data/alavista.db")

    # LLM / Embeddings
    ollama_base_url: str = "http://localhost:11434"
    embedding_model_name: str = "all-minilm-l6-v2"
    llm_model_tier_default: str = "reasoning_default"

    # HTTP / MCP
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
```

TDD:

- Test loading defaults with no `.env`.
- Test overriding via env vars.
- Test invalid setting types raise useful errors.

---

### 9.2 CLI Tooling

Binary name: `alavista`

Implementation: `typer` or `click`, under `cli/` module.

Directory:

```
cli/
  __init__.py
  main.py
  commands/
    corpora.py
    ingest.py
    search.py
    graph.py
```

Entrypoint:

```python
# cli/main.py
import typer

app = typer.Typer(help="Alavista CLI")

# register subcommands...

def run():
    app()
```

Setup entry point in `pyproject.toml`:

```toml
[project.scripts]
alavista = "cli.main:run"
```

---

### 9.3 CLI Commands

#### 9.3.1 `alavista corpora`

- `alavista corpora list`
  - Calls CorpusStore via a small adapter to list corpora.
- `alavista corpora create NAME`
  - Creates a new corpus.
  - Options:
    - `--id` (optional)
    - `--type` (persona_manual  # To be renamed profile_manual | research | global)

TDD:

- Use a test DB; verify corpora are created and listed.

---

#### 9.3.2 `alavista ingest`

- `alavista ingest file CORPUS_ID PATH`
  - Detect file type (txt, md, pdf).
  - Calls IngestionService.ingest_file.
  - Prints document count and chunk count.

- `alavista ingest url CORPUS_ID URL`
  - Calls IngestionService.ingest_url.

- `alavista ingest text CORPUS_ID "some text here"`
  - Calls IngestionService.ingest_text.

TDD:

- Mock IngestionService.
- Ensure correct arguments are passed from CLI to service.
- Ensure error messages are clear (e.g., missing corpus).

---

#### 9.3.3 `alavista search`

- `alavista search CORPUS_ID "query string" [--mode bm25|vector|hybrid] [--k 10]`
  - Calls SearchService.search.
  - Displays top-k with:
    - doc_id
    - score
    - short snippet.

Optional:
- Flags for JSON output: `--json` to print raw JSON.

TDD:

- Mock SearchService and assert correct mapping and print.

---

#### 9.3.4 `alavista graph`

- `alavista graph find-entity "Name"`
  - Calls GraphService.find_entity.
  - Prints candidates (id, type, name).

- `alavista graph neighbors NODE_ID [--depth 2]`
  - Calls GraphService.graph_neighbors.
  - Prints adjacency list.

- `alavista graph paths START_ID END_ID [--max-hops 4]`
  - Calls GraphService.graph_paths.

TDD:

- Mock GraphService and test argument wiring and console formatting.

---

### Phase 9 Exit Criteria

- `alavista` CLI installed and usable after project install.
- Common operations (create corpus, ingest, search, graph inspect) can be run from the command line.
- Config is loaded via Settings and can be overridden via `.env` and env vars.
- Good error messages and `--help` outputs.

---

## Phase 10 — Analysis Profile Resource Ingestion (MCP + HTTP)

### Goals

- Allow analysis profiles to **grow their own knowledge base** by ingesting:
  - URLs
  - files
  - short text notes
- Extend the ingestion pipeline so analysis profile corpora:
  - are separate from main investigative corpora
  - hold how-to docs, best practices, references
- Provide MCP tools and HTTP endpoints so agents and UIs can enrich analysis profiles over time.

---

### 10.1 Analysis Profile Corpora Model

Design decision:

- Profile-specific corpora are just special corpora in `CorpusStore`, with:
  - `type = "persona_manual  # To be renamed profile_manual"`
  - `persona_id` (to be renamed `analysis_profile_id`) annotated in metadata.

Implementation:

- On startup, `PersonaRegistry` (to be renamed `AnalysisProfileRegistry`) checks if a manual corpus exists for each analysis profile.
  - If not, optionally create one (config flag: `auto_create_persona_corpora`, to be renamed).
- Store reference to `persona_manual  # To be renamed profile_manual_corpus_id` in analysis profile runtime configuration.

TDD:

- Ensure manual corpora are created if missing, when the flag is enabled.
- Ensure persona runtime can retrieve its own corpus id.

---

### 10.2 IngestionService Enhancements

Add profile-specific helper methods:

```python
class IngestionService:

    async def ingest_persona_url(self, persona_id: str, url: str, metadata: dict | None = None) -> Document:
        # find or create persona manual corpus, delegate to ingest_url

    async def ingest_persona_file(self, persona_id: str, file_path: Path, metadata: dict | None = None) -> Document:
        ...

    async def ingest_persona_text(self, persona_id: str, text: str, metadata: dict | None = None) -> Document:
        ...
```

TDD:

- Mock CorpusStore + DocumentStore.
- Ensure persona ingestion maps to the correct analysis profile corpus.

---

### 10.3 Duplicate Detection & Deduplication

To avoid analysis profile corpora blowing up with redundant copies:

- Maintain a `hash` column in DocumentStore (e.g., SHA256 of normalized text).
- For persona ingestion:
  - Before inserting, compute hash.
  - If a document with same hash exists in the analysis profile corpus:
    - Optionally skip or mark as another reference (configurable).

TDD:

- Ingest same text twice; second attempt either:
  - is skipped
  - or returns existing document id with a flag (config setting determines behavior).
- Ensure hash is consistent for equivalent texts.

---

### 10.4 MCP Tools for Persona Ingestion

In `persona_tools.py`:

- `persona_ingest_resource` becomes fully implemented:

Arguments:

```json
{
  "persona_id": "financial_forensics",
  "resource_type": "url" | "file" | "text",
  "value": "...",
  "metadata": { ... }
}
```

Behavior:

- Validate persona exists.
- Route to appropriate `IngestionService.ingest_persona_*` function.
- Return:
  - `document_id`
  - `corpus_id`
  - `chunk_count`

TDD:

- Mock IngestionService and PersonaRegistry.
- Validate correct routing based on `resource_type`.
- Validate JSON shape of responses.

---

### 10.5 HTTP API for Persona Ingestion

`routes/persona_ingest.py` (new file):

- `POST /api/v1/personas/{persona_id}/ingest/url`
  - Body: `{ url: str, metadata?: dict }`
  - Calls `IngestionService.ingest_persona_url`.

- `POST /api/v1/personas/{persona_id}/ingest/file`
  - Multipart upload with `file` and optional `metadata`.
  - Calls `IngestionService.ingest_persona_file`.

- `POST /api/v1/personas/{persona_id}/ingest/text`
  - Body: `{ text: str, metadata?: dict }`
  - Calls `IngestionService.ingest_persona_text`.

TDD:

- Use TestClient to call each route with stubbed services.
- Verify correct HTTP status and body shapes.

---

### 10.6 PersonaRuntime Awareness

PersonaRuntime should optionally draw on analysis profile corpus when:

- Interpreting the question (e.g., injection of persona methods and best practices).
- Planning the reasoning approach.

MVP behavior:

- When answering a question:
  - Run a short hybrid search over persona manual corpus with the question as query.
  - Inject top N persona-manual snippets as **“persona context”** into the LLM call that synthesizes the final answer.

TDD:

- With mocked SearchService:
  - Ensure persona manual retrieval is invoked when manual corpus exists.
  - Ensure persona context is included in LLM call parameters.

### Phase 10 Exit Criteria

- Analysis Profiles can ingest resources via MCP and HTTP.
- Persona manual corpora exist and are used in reasoning.
- Duplicate detection works for persona docs.
- Tests cover ingestion, wiring, and persona runtime integration points.

---

## Phase 11 — Graph-Guided RAG

### Goals

- Combine:
  - **Graph structure** (who/what is connected)
  - **Semantic retrieval** (what the docs say)
- into a **graph-guided RAG pipeline** that sharply narrows the search space for complex questions.
- Make this usable by PersonaRuntime and by direct tools later.

---

### 11.1 Graph-Guided Retrieval Strategy

Core idea:

1. Use question + persona to:
   - Identify key entities and relation focus.
2. Use GraphService to:
   - Resolve entities.
   - Identify relevant neighborhoods / paths.
3. Use SearchService to:
   - Run semantic/hybrid search **within the documents attached to those neighborhoods**.
4. Feed LLM:
   - Focused set of high-signal chunks.
   - Graph context (paths, neighbors, stats).
   - Persona manual context.

---

### 11.2 GraphRAGService

Module: `core/rag/graph_rag_service.py`

Interface:

```python
class GraphRAGService:

    async def answer(
        self,
        question: str,
        persona: PersonaBase,
        topic_corpus_id: str | None = None,
    ) -> GraphRAGResult:
        ...
```

`GraphRAGResult`:

```python
class GraphRAGResult(BaseModel):
    answer_text: str
    evidence_docs: list[EvidenceItem]
    graph_context: list[GraphPath | GraphNeighborhood]
    retrieval_summary: str
```

Algorithm (MVP):

1. **Entity & intent extraction**:
   - Use lightweight heuristic or an LLM prompt to extract:
     - candidate entity names
     - whether the question is structural, temporal, or content-focused.
2. **Graph narrowing**:
   - For each entity name:
     - `GraphService.find_entity(name)` → choose top candidate(s).
   - If structural:
     - `graph_paths` between key entities.
   - Else:
     - `graph_neighbors` around key entity up to `depth=1` or `2`.
   - Collect all referenced `doc_id`s from edges and nodes.
3. **Semantic narrowing**:
   - If we have relevant doc_ids:
     - Run `SearchService.search` with filter:
       - `corpus_id = topic_corpus_id or global_corpus`
       - `doc_ids in rel_doc_ids`
   - If no graph hits:
     - Fallback to pure `SearchService.search`.
4. **LLM synthesis**:
   - Provide:
     - top K chunks from search
     - graph paths/neighbors summary
     - persona manual context (if available)
   - Ask LLM to answer:
     - in persona’s method style
     - with explicit citations

TDD:

- Unit tests:
  - For a fake GraphService + SearchService, ensure:
    - graph narrowing filters doc_ids.
    - fallback to pure search when no graph hits.
- Integration tests (with stub LLM):
  - Ensure `GraphRAGService.answer` returns a fully populated GraphRAGResult.

---

### 11.3 PersonaRuntime Integration

Update PersonaRuntime:

- For structural or mixed questions:
  - Prefer `GraphRAGService.answer` over plain search+graph manual composition.
- For purely semantic questions:
  - Plain RAG (no graph context) is fine.
- For questions explicitly about connections:
  - GraphRAG is mandatory.

Implementation:

- Add a dependency on `GraphRAGService`.
- Extend question categorization to support:
  - `semantic`
  - `structural`
  - `hybrid` (content + structure)

TDD:

- With stub GraphRAGService:
  - Structural questions invoke graph-guided RAG.
  - Semantic questions do not.

---

### 11.4 Tooling Hooks (Optional at this Phase)

Optional but useful:

- Expose a **graph_rag** tool via MCP:
  - LLMs can explicitly request graph-guided RAG when they want deeper reasoning.
- Expose `/api/v1/graph_rag` via HTTP:
  - Direct clients can call it.

TDD:

- Similar to other MCP/HTTP tests: use mocks and verify data shape.

---

### Phase 11 Exit Criteria

- Graph-guided RAG is implemented and tested.
- PersonaRuntime can leverage GraphRAGService for complex structural questions.
- Investigative answers can now:
  - Reference explicit graph paths.
  - Show how structural context shaped retrieval.
- The system transitions from “smart search” to a **true investigative assistant**.

---

**End of Roadmap Part 4 (Phases 9–11).**
