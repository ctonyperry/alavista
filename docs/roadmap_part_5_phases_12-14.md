
# Roadmap Part 5 — Phases 12–14 (Full Detail)

This file covers:

- **Phase 12** – Lightweight UI (Optional but strongly recommended)
- **Phase 13** – Optimization, Hardening, Packaging
- **Phase 14** – v1.0 Release

It assumes Phases 0–11 are complete and stable.

---

## Phase 12 — Lightweight UI (Optional but Recommended)

### Goals

- Provide a **minimal but effective web UI** on top of the HTTP API:
  - Ingest documents into corpora.
  - Run semantic + hybrid search.
  - Explore analysis profiles and ask analysis profile-scoped questions.
  - Inspect graph neighborhoods and paths.
- Keep it **thin and replaceable**:
  - No business logic in the UI.
  - UI only calls HTTP API and presents results.

This is not meant to be “the final product UI,” but a **reference dashboard** for humans and a debugging surface for devs.

---

### 12.1 Tech Stack

- **Frontend framework**: React (Vite or Next.js in SPA mode).
- **Language**: TypeScript.
- **UI components**: Lightweight, e.g.,:
  - Tailwind CSS or simple CSS modules.
- **Graph visualization**: 
  - `react-force-graph`, `Cytoscape.js`, or similar light graph lib.

Backend remains FastAPI (already built in Phase 8).

---

### 12.2 UI Pages / Views

#### 12.2.1 Home / Overview

- Shows:
  - List of corpora.
  - List of analysis profiles.
  - Basic system status (e.g., connected to API, graph/ontology loaded).

Implementation:

- `GET /api/v1/corpora`
- `GET /api/v1/personas` (to be renamed `/api/v1/analysis-profiles` or `/profiles`)

---

#### 12.2.2 Corpus Management

Features:

- **List corpora**:
  - name, id, type, document count (optional count endpoint or metadata).
- **Create corpus**:
  - Name
  - Type: `persona_manual  # To be renamed profile_manual` | `research` | `global`
- **Inspect corpus**:
  - Show recent ingested documents (requires `list_documents` API or approximate metadata listing).

HTTP usage:

- Existing `/corpora` endpoints.
- Add a `GET /api/v1/corpora/{id}/stats` if needed to expose doc count, chunk count.

UI behavior:

- Simple forms and tables.
- Inputs validated client-side and server-side.

---

#### 12.2.3 Ingestion Panel

Features:

- Select target corpus.
- Tabs for:
  - **Text** input (multiline text → `ingest/text`).
  - **URL** (single URL → `ingest/url`).
  - **File upload** (.txt, .md, .pdf) → `ingest/file`.

Implementation:

- Use the existing `/ingest` HTTP endpoints from Phase 8.
- Show immediate feedback:
  - success: doc_id, chunk_count
  - error: message from API.

---

#### 12.2.4 Search Console

Features:

- Select corpus.
- Choose mode: `bm25`, `vector`, `hybrid`.
- Enter query.
- View results as a list:

For each hit:

- Score
- Excerpt
- doc_id / chunk_id
- Link to “view in context” (optional future feature).

HTTP usage:

- `POST /api/v1/search`

Optional enhancements:

- Filter by metadata (in future, when search supports this).
- Show which retrieval mode was used.

---

#### 12.2.5 Analysis Profile Workbench

Features:

- Analysis profile selector (dropdown).
- Question input.
- Optional selection of topic corpus (if relevant).
- Show:
  - Persona’s description and constraints.
  - Answer.
  - Evidence citations (doc/chunk IDs, maybe preview).
  - Graph evidence summary (e.g., list of nodes/edges referenced).

HTTP usage:

- `GET /api/v1/personas` (to be renamed `/api/v1/analysis-profiles` or `/profiles`)
- `GET /api/v1/personas/{persona_id}` (to be renamed `/api/v1/analysis-profiles/{profile_id}`)
- `POST /api/v1/personas/{persona_id}/answer` (to be renamed `/api/v1/analysis-profiles/{profile_id}/answer`)

Optional persona ingestion UI:

- From analysis profile detail page:
  - Ingest analysis profile resources (URL, text, file).
  - Calls `/api/v1/personas/{persona_id}/ingest/*` (to be renamed with `/analysis-profiles/`).

---

#### 12.2.6 Graph Explorer

Features:

- **Find Entity**:
  - Input: name → `graph/find_entity`.
  - Show list of candidate nodes (select one).
- **Neighbors**:
  - Node selection → show neighbors and edges.
  - Render as a graph visualization:
    - Nodes = persons/docs/orgs.
    - Edges = relation types.
- **Paths**:
  - Start node, end node → `graph/paths`.
  - Show list of paths and optionally visualize one at a time.

HTTP usage:

- `POST /api/v1/graph/find_entity`
- `POST /api/v1/graph/neighbors`
- `POST /api/v1/graph/paths`
- `GET /api/v1/graph/stats/{node_id}`

TDD (front-end side):

- Use component-level tests (React Testing Library) for:
  - API interaction mocks.
  - Rendering states: loading, error, empty, success.
- No hard requirement to unit-test CSS/styling.

---

### 12.3 Frontend Project Layout (High Level)

Suggested structure:

```
ui/
  src/
    api/
      client.ts         # axios/fetch wrapper
      corpora.ts
      ingest.ts
      search.ts
      analysis profiles.ts
      graph.ts
      ontology.ts
    components/
      Layout.tsx
      CorpusTable.tsx
      SearchForm.tsx
      SearchResults.tsx
      PersonaPanel.tsx
      GraphViewer.tsx
    pages/
      Home.tsx
      CorporaPage.tsx
      IngestPage.tsx
      SearchPage.tsx
      PersonaPage.tsx
      GraphPage.tsx
    hooks/
      useApi.ts
    styles/
  vite.config.ts
  package.json
```

---

### 12.4 Phase 12 Exit Criteria

- UI can:
  - list corpora
  - create new corpora
  - ingest text/url/file into a corpus
  - run search over a corpus
  - show analysis profiles and answer a question using an analysis profile
  - perform basic graph exploration (find entity, neighbors, paths)
- UI is **optional to run**, but when run against the API, it works with no code changes.

---

## Phase 13 — Optimization, Hardening, Packaging

### Goals

- Make Alavista **robust, repeatable, and ready to share**:
  - Reasonable performance on mid-range hardware.
  - Solid test coverage and CI.
  - Sensible logging and observability.
  - Easy local deployment (Docker).
- Focus here is not micro-optimizing, but **removing footguns**.

---

### 13.1 Performance Tuning

Areas to tune:

1. **BM25 Search**:
   - Ensure indexes are built once and reused.
   - Cache tokenization results.
2. **Embedding Pipeline**:
   - Batch size tuning for GPU vs CPU.
   - Ensure embeddings and FAISS updates are not done per-document when ingesting large batches (use jobs).
3. **Graph Queries**:
   - Ensure indexes on node/edge tables for common patterns:
     - `source`, `target`, `type`, `doc_id`.
4. **LLM Calls**:
   - Cache frequently-used summaries and repeated question patterns.

TDD / Benchmarks:

- Add simple perf tests (not strict unit tests) to:
  - measure search latency for common queries.
  - measure graph operations on moderately sized graphs.
  - ensure no obvious regressions.

---

### 13.2 Robust Error Handling

Core rules:

- Core services should never raise raw low-level exceptions up to interfaces.
  - Wrap in domain-specific exceptions:
    - `SearchError`
    - `EmbeddingError`
    - `GraphError`
    - `OntologyError`
    - `PersonaError`
- HTTP and MCP layers:
  - Map domain errors to:
    - HTTP 4xx/5xx as appropriate.
    - MCP error objects.

Implementation tasks:

- Audit all `raise` sites in core services.
- Introduce a common `errors.py` per domain or a shared `core/errors.py`.

TDD:

- Tests that simulate backend failures (e.g., embedding model not reachable) and validate:
  - APIs return structured error responses.

---

### 13.3 Logging & Observability

Logging:

- Use Python’s `logging` with a structured formatter (JSON logs if desired).
- Standard fields:
  - timestamp
  - level
  - service (search, graph, persona, api, mcp)
  - request_id (if present)
- Log events:
  - ingestion job started/finished
  - graph extraction tasks
  - analysis profile queries (without sensitive user input if privacy is a concern)
  - errors and warnings

Metrics (lightweight MVP):

- Counters:
  - number of ingestion operations
  - number of search queries
  - number of analysis profile queries
- Latency histograms (if using something like Prometheus later).

TDD:

- Unit tests for logger configuration.
- Tests ensuring error logs contain expected fields.

---

### 13.4 Packaging & Dockerization

Docker:

- Base image:
  - Python slim image.
- Steps:
  - Install system deps as needed (e.g., for sentence-transformers, if using).
  - Install project via `uv` or `pip`.
  - Include entrypoints:
    - `alavista api` to run FastAPI (uvicorn).
    - `alavista mcp` to run the MCP server.
- Multi-stage build recommended:
  - Builder image for deps.
  - Final runtime image trimmed down.

Docker Compose:

- `docker-compose.yml`:
  - `api` service (FastAPI).
  - `ollama` service.
  - Maybe `db` if using Postgres later; for MVP, SQLite is file-based.

Tests:

- Run `pytest` as part of CI before building images.

---

### 13.5 CI Pipeline (Optional but Strongly Recommended)

Use GitHub Actions or similar:

- On push / PR:
  - Run lint (`ruff`, `mypy` optional).
  - Run tests (`pytest`).
  - Optionally build Docker images.

No need for deployment automation at this stage unless you want to.

---

### 13.6 Phase 13 Exit Criteria

- The system:
  - Handles error conditions gracefully.
  - Logs meaningful information for debugging.
  - Runs at acceptable performance levels on local hardware.
- There is a **documented way** to:
  - Run tests.
  - Run API.
  - Run MCP server.
  - Build images (if Docker is used).

---

## Phase 14 — v1.0 Release

### Goals

- Package Alavista as a coherent, self-contained open-source project.
- Provide enough docs, examples, and guardrails that:
  - Journalists
  - Researchers
  - Technically-minded citizens
- can actually use it against real-world corpora.

---

### 14.1 Documentation Set

Key docs:

1. **README.md**
   - What Alavista is.
   - Core concepts: corpus, persona, graph, ontology, graph-guided RAG.
   - Quickstart:
     - `docker compose up` (or local run).
     - ingest sample data.
     - run a search.
     - run an analysis profile query.
   - Links to deeper docs.

2. **docs/architecture.md**
   - High-level description of:
     - core services
     - data flows
     - ontologies & graph
     - analysis profiles & graph-guided RAG
   - Reference for maintainers and contributors.

3. **docs/usage_journalist.md**
   - Simple workflow using:
     - FOIA docs.
     - corpora ingestion.
     - graph exploration.
     - analysis profile queries.

4. **docs/deployment.md**
   - Local usage.
   - Running via Docker.
   - Optional notes on remote hosting (if you choose to include).

5. **docs/analysis profiles.md**
   - How analysis profiles work.
   - How to create/modify an analysis profile.
   - Safety guidelines.

TDD (informal):

- Docs should be runnable as “copy-paste” sessions wherever possible.
- Example commands actually work against a sample dataset.

---

### 14.2 Sample Data & Walkthroughs

Provide:

- `examples/epstein_minimal/`:
  - Tiny subset of the corpus (legally safe & small).
  - Prebuilt:
    - corpus ingested
    - some graph edges extracted
    - possibly sample analysis profile config.

- Notebook or markdown-based walkthrough:
  - Load minimal corpus.
  - Run:
    - basic search.
    - graph find → neighbors.
    - persona query → answer with citations.

This turns the repo from “promising” into **immediately useful**.

---

### 14.3 Release Checklist

Before tagging v1.0.0:

- [ ] All roadmap core phases (0–11) implemented.
- [ ] If chosen, Phase 12 UI implemented at least minimally.
- [ ] Phase 13 hardening complete (core error handling, logging, config).
- [ ] Test suite passing.
- [ ] Linting clean or with clearly documented exceptions.
- [ ] README updated to match actual behavior.
- [ ] At least one real-world demo flow documented.

Tagging:

- Use semantic versioning:
  - v1.0.0 = first stable semantics.
- Create a GitHub Release:
  - Include:
    - summary of features.
    - link to docs.
    - screenshots of UI or CLI usage.
    - note about limitations and future work.

---

### 14.4 Future Work (Post-v1, Not Blocking Release)

Document (in `ROADMAP.md` or similar):

- Richer ontology (Flights, Accounts, Transactions…).
- Advanced entity resolution with embeddings.
- Time-aware graphs (temporal edges).
- Per-analysis-profile advanced reasoning behaviors.
- Federated / multi-tenant setups.
- Integration with external investigative tools (e.g., Maltego, Neo4j, etc.).
- Richer UI: timelines, heat maps, clustering visualizations.

These are **explicitly post-v1** so the project doesn’t get stuck chasing perfection.

---

### Phase 14 Exit Criteria

- v1.0.0 tagged and released.
- Someone who is not you can:
  - clone the repo,
  - follow the README,
  - ingest some docs,
  - run an analysis profile query,
  - explore a small graph,
  - and understand what the tool is for.

At that point, Alavista is no longer just a personal experiment — it’s a **publicly usable investigative engine**.

---

**End of Roadmap Part 5 (Phases 12–14).**
