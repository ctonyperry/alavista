# Alavista – Architecture Overview

This document defines the **system blueprint**: the main layers, components, and data flows. It should give an AI coding assistant (and humans) a clear mental model of how everything fits together.

## 1. High‑Level Layers

Alavista is organized into the following conceptual layers:

1. **Data & Corpora**  
   - Raw documents, corpora, and metadata.
   - Ingestion, dedupe, and basic document management.

2. **Semantic Retrieval Layer**  
   - BM25 keyword search.
   - Embedding‑based vector search.
   - Hybrid search combining both.

3. **Graph Layer**  
   - Typed nodes and edges.
   - Provenance and confidence scores.
   - Structural queries (neighbors, paths, subgraphs, stats).

4. **Ontology Layer**  
   - Minimal schema defining allowed entity types, relation types, and evidence semantics.
   - Acts as a guardrail for graph building, extraction, and persona reasoning.

5. **Personas & Runtime**  
   - Persona definitions (manual corpora + ontology config).
   - PersonaRuntime, PersonaPlanner, ResearchQA LLM tools.

6. **LLM Runtime & Prompts**  
   - Local LLM clients (generation and embeddings).
   - Prompt templates and structured responses.
   - Caching layer for expensive calls.

7. **Interfaces**  
   - MCP server: Alavista as a tool suite for LLMs.
   - HTTP API: FastAPI routes for programmatic use and UIs.


## 2. Project Layout (Top‑Level)

A minimal but realistic layout:

```text
alavista/
├── app.py                      # FastAPI entrypoint
├── mcp_entry.py                # MCP server entrypoint
├── config/
│   └── settings.py             # Pydantic settings (models, paths, ports)
├── core/
│   ├── models.py               # Shared data models
│   ├── corpus_store.py         # Corpus/document persistence abstraction
│   ├── vector_index.py         # Vector index interface + impl
│   ├── bm25_index.py           # BM25 index interface + impl
│   ├── embedding_provider.py   # EmbeddingProvider interfaces
│   ├── ingestion_service.py    # Ingestion pipeline
│   ├── search_service.py       # SearchService (bm25/vector/hybrid)
│   ├── llm_client.py           # LLMClient + caching wrapper
│   ├── llm_tools.py            # PersonaPlanner + ResearchQA
│   ├── persona_runtime.py      # PersonaRuntime orchestration
│   ├── prompt_manager.py       # Prompt templates & helpers
│   ├── personas.py             # Persona definitions loader/registry
│   └── graph/
│       ├── models.py           # Node, Edge, Provenance, ResolvedEntity
│       ├── graph_store.py      # GraphStore abstraction
│       ├── extraction.py       # Entity & relation extraction
│       ├── resolution.py       # Entity resolution
│       ├── graph_service.py    # High‑level graph querying
│       └── graph_rag.py        # Graph‑guided RAG helpers
├── core/ontology/
│   ├── models.py               # Ontology entity & relation models
│   ├── registry.py             # OntologyRegistry
│   └── validators.py           # Type & relation validation helpers
├── interfaces/
│   ├── api/
│   │   ├── schemas.py          # API request/response models
│   │   └── routes/
│   │       ├── corpora.py
│   │       ├── personas.py
│   │       ├── ingest.py
│   │       ├── search.py
│   │       └── persona_qna.py
│   └── mcp/
│       ├── mcp_server.py       # Registers tools with MCP runtime
│       └── graph_tools.py      # Graph‑focused MCP tools
├── llm_models/
│   ├── load_model.py           # Local LLM loading helpers
│   └── embeddings.py           # EmbeddingProvider implementations
├── ontology/
│   └── ontology_v0.1.json      # Minimal ontology definition
├── personas/
│   ├── investigative_journalist.yaml
│   └── financial_forensics.yaml
├── tests/
│   ├── test_models.py
│   ├── test_corpus_store.py
│   ├── test_vector_index.py
│   ├── test_bm25_index.py
│   ├── test_ingestion_service.py
│   ├── test_search_service.py
│   ├── test_graph_store.py
│   ├── test_graph_service.py
│   ├── test_ontology_registry.py
│   ├── test_persona_runtime.py
│   └── test_mcp_tools.py
└── README.md
```

This structure is flexible but must preserve the separation between **core logic** and **interfaces**.


## 3. Data Flow (End‑to‑End)

### 3.1 Ingestion

1. User (or MCP tool) calls ingest:
   - text, URL, or file → `IngestionService`.
2. `IngestionService`:
   - normalizes and chunks text if needed,
   - computes content hash,
   - checks dedupe via `CorpusStore`,
   - persists new documents,
   - calls `EmbeddingProvider` to embed chunks,
   - updates `VectorIndex` and optional `BM25Index`.
3. Later, graph extraction pipeline can:
   - read documents,
   - run `graph/extraction.py` + LLM to extract entities/relations,
   - run `graph/resolution.py` to merge entities,
   - push nodes/edges into `GraphStore`.


### 3.2 Retrieval

1. User/LLM calls `SearchService.search` (through MCP or HTTP).
2. `SearchService`:
   - optionally embeds the query,
   - runs BM25 and/or vector search,
   - does hybrid combination,
   - fetches full documents via `CorpusStore`,
   - returns structured `SearchResult` with `SearchHit`s.
3. For graph‑guided RAG:
   - Query graph first (via `GraphService`),
   - use provenance to fetch relevant documents,
   - feed those documents into `SearchService` and/or LLM.


### 3.3 Persona‑Driven Question Answering

1. User/LLM calls MCP tool `persona_answer_question(persona_id, topic_id, question)`.
2. MCP layer calls `PersonaRuntime` with:
   - persona definition,
   - research corpus ID,
   - question.
3. `PersonaRuntime`:
   - fetches persona manual corpus docs,
   - asks `PersonaPlanner` LLM tool for a plan,
   - runs `SearchService` on manual corpus (to adapt plan),
   - runs `SearchService` and optionally graph queries on research corpus,
   - calls `ResearchQA` LLM tool with evidence docs,
   - returns structured `PersonaAnswer` with answer text, plan, and evidence doc IDs.


## 4. Responsibilities by Layer

### 4.1 `core/`

- Knows nothing about HTTP or MCP.
- Contains:
  - domain models,
  - persistence abstractions,
  - search logic,
  - graph logic,
  - persona runtime,
  - LLM abstraction.
- All **business logic** lives here.

### 4.2 `interfaces/api/` (FastAPI)

- Thin HTTP shell:
  - parse requests,
  - call core services,
  - serialize results.
- No business rules.

### 4.3 `interfaces/mcp/`

- Registers tools with an MCP runtime.
- Each tool’s implementation is just an adapter:
  - parse arguments,
  - call core services,
  - wrap response in MCP format.

### 4.4 `llm_models/`

- Deals with actual local LLMs and embeddings.
- Provides instances conforming to `LLMClient` and `EmbeddingProvider` interfaces.
- Can be mocked/faked in tests.

### 4.5 `ontology/` + `core/ontology`

- Stores and interprets the ontology.
- Validates entity/relation types.
- Used in:
  - graph building,
  - persona configs,
  - LLM prompts.


## 5. Extensibility Strategy

The architecture should support:

- Adding new entity types or relation types by:
  - updating `ontology_v0.1.json`,
  - possibly adding persona rules.

- Swapping out vector/BM25 implementations without changing:
  - MCP layer,
  - HTTP routes,
  - PersonaRuntime.

- Extending personas by adding YAML files and minor prompt tweaks.

- Adding more LLM models or switching embedding providers via config settings.

The **contract between layers** is through clear Python interfaces and Pydantic models defined in `core/models.py` and `core/*_index.py`.


## 6. How AI Assistants Should Use This File

When generating code, AI assistants must:

- Maintain the separation of layers exactly as described.
- Avoid leaking FastAPI or MCP concerns into `core/` modules.
- Respect the project layout when creating new files.
- Use the data flows described here to decide where logic belongs.
- Prefer composition (services calling each other) over inheritance or deep magic.

This file is the **map**; the other spec documents are the **details**.
