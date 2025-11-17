
# Roadmap Part 5 — Phases 12–14 (Full Detail)

This file covers:

- **Phase 12** – Lightweight UI (Optional but strongly recommended)
- **Phase 13** – Optimization, Hardening, Packaging
- **Phase 14** – v1.0 Release

### Post Phases 10–11 Reprioritization

Phases 10–11 (persona resource ingestion + graph-guided RAG) are complete (`docs/PHASE_10-11_COMPLETED.md`). Remaining work is reprioritized as follows:

- **Phase 12 (Lightweight UI + Agent Foundations)**:
  - Lock frontend stack (React + Tailwind + Radix + shadcn/ui).
  - Define Run model + evidence-first structures to support agent UI.
  - Ship thin UI surfaces for corpora, ingestion, search, personas, graph; optional run/plan view.
- **Phase 13 (Hardening & Packaging)**:
  - Robust error handling/logging/metrics, perf tuning, Docker/CI.
  - Evaluation + replay for Runs; optional external research tool with safety toggles.
- **Phase 14 (v1.0 Release)**:
  - Docs, sample data, release checklist; UI remains optional but should work against API.

It assumes Phases 0–11 are complete and stable.

---

## Phase 12 — Lightweight UI (Optional but Recommended)

### Goals

- Provide a **minimal but effective web UI** on top of the HTTP API:
  - Ingest documents into corpora.
  - Run semantic + hybrid search.
  - Explore personas and ask persona-scoped questions.
  - Inspect graph neighborhoods and paths.
- Keep it **thin and replaceable**:
  - No business logic in the UI.
  - UI only calls HTTP API and presents results.

This is not meant to be “the final product UI,” but a **reference dashboard** for humans and a debugging surface for devs.

---

### 12.1 Tech Stack (Decision Locked)

- **Framework**: React (Vite SPA), TypeScript.
- **Styling**: Tailwind CSS with design tokens + CSS variables (light/dark).
- **Primitives**: Radix UI.
- **Components**: shadcn/ui (Tailwind + Radix wrappers; generated into repo).
- **Icons**: lucide-react.
- **State**: React Query (server state), local component state otherwise.
- **Forms/validation**: react-hook-form + zod.
- **Testing**: Vitest + React Testing Library + MSW.
- **Graph visualization**: lightweight lib considered later (placeholder ok in Phase 12).

Rationale:

- Polished UI without a dedicated designer; coherent defaults.
- Code-generation-friendly for AI scaffolding.
- Composable and easily themed; modern, accessible primitives.
- Fits local-first, open-source deployment and optional UI stance.

Frontend stays thin: all business logic remains in FastAPI/MCP layers; UI only calls HTTP API.

---

### 12.2 UI Pages / Views

#### 12.2.1 Home / Overview

- Shows:
  - List of corpora.
  - List of personas.
  - Basic system status (e.g., connected to API, graph/ontology loaded).

Implementation:

- `GET /api/v1/corpora`
- `GET /api/v1/personas`

---

#### 12.2.2 Corpus Management

Features:

- **List corpora**:
  - name, id, type, document count (optional count endpoint or metadata).
- **Create corpus**:
  - Name
  - Type: `persona_manual` | `research` | `global`
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

#### 12.2.5 Persona Workbench

Features:

- Persona selector (dropdown).
- Question input.
- Optional selection of topic corpus (if relevant).
- Show:
  - Persona’s description and constraints.
  - Answer.
  - Evidence citations (doc/chunk IDs, maybe preview).
  - Graph evidence summary (e.g., list of nodes/edges referenced).

HTTP usage:

- `GET /api/v1/personas`
- `GET /api/v1/personas/{persona_id}`
- `POST /api/v1/personas/{persona_id}/answer`

Optional persona ingestion UI:

- From persona detail page:
  - Ingest persona resources (URL, text, file).
  - Calls `/api/v1/personas/{persona_id}/ingest/*`.

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

### 12.3 UI Project Layout, Theming, Accessibility

- **Layout**:
  - New frontend root: `ui/`
  - `src/components/` (shared shadcn-based components)
  - `src/features/{corpora,ingestion,search,personas,graph,runs}/components`
  - `src/lib/api/` (client, hooks, types), `src/lib/theme/` (tokens), `src/lib/hooks/`
  - `src/pages/` or `src/routes/` (route-level views), `public/`, `tailwind.config.ts`.
- **Integration**: UI calls HTTP API only; MCP parity maintained by keeping logic in FastAPI/core services.
- **Theming/tokens**: Tailwind config extended with color/spacing/typography/radius/shadow tokens; CSS variables for light/dark, aligned with shadcn defaults.
- **Accessibility**: Radix primitives for ARIA/focus; AA contrast; focus-visible styles; aria-live for async states; keyboard nav enforced.

---

### 12.4 UI Development Plan

1) Bootstrap: Vite + React + TS in `ui/`; add Tailwind/PostCSS config; base `LayoutShell` with sidebar/topbar.
2) Install/configure: Radix, shadcn/ui (generate button/input/select/textarea/dialog/sheet/tabs/card/badge/table/tooltip/dropdown-menu/toast/skeleton/pagination), lucide-react, React Query, react-hook-form + zod, MSW, Vitest + RTL.
3) API client: `src/lib/api/client.ts` (fetcher), `types.ts` (DTOs: corpus/doc/search/persona/graph/run/evidence), `hooks.ts` (React Query wrappers).
4) Routing: `/` home, `/corpora`, `/ingest`, `/search`, `/personas`, `/graph`, `/runs` (optional if Run model present); shell layout with responsive sidebar.
5) State: React Query for server state; local UI state otherwise; avoid global stores initially.
6) Backend endpoints: corpora (`GET/POST`), ingest (`/ingest/text|url|file`), search (`/search` with `bm25|vector|hybrid`), personas (`/personas` + Q&A), graph (`/graph/find|neighbors|paths`), runs (`/runs` lifecycle if present).

---

### 12.5 UI Design Spec & Component Scaffolding (First Pass)

- **Layout**: Sidebar + topbar shell; cards/sections; tabs for modes; toasts for async feedback; skeletons for loading; alerts for errors.
- **Pages**:
  - Home: cards for system status, recent corpora/personas; quick actions.
  - Corpora: table + create dialog; badges for types; doc counts if available.
  - Ingestion: tabs for text/url/file; select corpus; show `doc_id` + `chunk_count`; inline errors.
  - Search: mode tabs; query input; corpus select; results list with score/excerpt/doc/chunk; empty/loading states.
  - Personas: list/detail; question box; answer with citations/evidence slots.
  - Graph Explorer: find/neighbors/paths; tables for nodes/edges; depth/limit indicators; placeholder for viz.
  - Runs (optional): plan/stepper + evidence list; controls for pause/resume/step if API supports.
- **Components to scaffold** (feature folders):
  - Corpora: `CorporaTable`, `CreateCorpusDialog`.
  - Ingestion: `IngestionTabs` (handlers for text/url/file ingest).
  - Search: `SearchForm`, `SearchResults`.
  - Personas: `PersonaList`, `PersonaQA`.
  - Graph: `GraphSearch` (find/neighbors/paths panel).
  - Runs: `RunSummary` (plan/steps/evidence view).
  - Shared: `LayoutShell`, `DataTable`, `PageHeader`, `StatusBadge`, form wrappers for RHF+shadcn.
- **API shape (reference)**:
  - Corpus `{id,name,type,doc_count?}`
  - Ingest result `{doc_id,chunk_count}`
  - Search result `{score,excerpt,doc_id,chunk_id?,corpus_id?}`
  - Persona `{id,name,description?}`; answer `{answer,citations?}`
  - Graph `{nodes:[{id,label,type?}],edges:[{source,target,type?}]}`; neighbors/paths similar.
  - Run `{id,status,task,plan:[...],steps:[...],evidence:[...]}` if Run model added.

---

### 12.6 Phase 12 Exit Criteria

- UI can:
  - list corpora
  - create new corpora
  - ingest text/url/file into a corpus
  - run search over a corpus
  - show personas and answer a question using a persona
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

**Scope updates (post wishlist triage):**

- Introduce basic Run replay/evaluation to support agent quality.
- Optional external research tool stays off-by-default with clear labeling/toggles.
- Keep MCP/API parity via core services layer; avoid duplicate logic.

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
  - persona queries (without sensitive user input if privacy is a concern)
  - errors and warnings

Metrics (lightweight MVP):

- Counters:
  - number of ingestion operations
  - number of search queries
  - number of persona queries
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
     - run a persona query.
   - Links to deeper docs.

2. **docs/architecture.md**
   - High-level description of:
     - core services
     - data flows
     - ontologies & graph
     - personas & graph-guided RAG
   - Reference for maintainers and contributors.

3. **docs/usage_journalist.md**
   - Simple workflow using:
     - FOIA docs.
     - corpora ingestion.
     - graph exploration.
     - persona queries.

4. **docs/deployment.md**
   - Local usage.
   - Running via Docker.
   - Optional notes on remote hosting (if you choose to include).

5. **docs/personas.md**
   - How personas work.
   - How to create/modify a persona profile.
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
    - possibly sample persona config.

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
- Per-persona advanced reasoning behaviors.
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
  - run a persona query,
  - explore a small graph,
  - and understand what the tool is for.

At that point, Alavista is no longer just a personal experiment — it’s a **publicly usable investigative engine**.

---

**End of Roadmap Part 5 (Phases 12–14).**
