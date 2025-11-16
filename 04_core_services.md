# Alavista – Core Services Specification

The **core services layer** implements all domain logic and must stay free of:

- HTTP frameworks (FastAPI, Flask)
- MCP-specific code
- UI concerns
- Hard-coded LLM model choices
- Hard-coded corpus IDs or persona IDs

It is the **engine** of Alavista — everything else adapts *to* this layer.

This document defines:

1. Core module responsibilities  
2. Required abstractions  
3. Data flow  
4. Interfaces and methods  
5. Error semantics  
6. Unit and integration test baselines  
7. LLM interaction patterns  
8. Implementation constraints  


---

## 1. Guiding Principles

1. **Strict separation of concerns**  
   No business logic in API or MCP layers. They call into core services, never the other way around.

2. **Local-first architecture**  
   All core services must work **offline** with local text, embeddings, and models. No cloud assumptions.

3. **Replaceability**  
   Each service must be swappable without requiring downstream code changes. Achieve this via clear protocols/interfaces.

4. **Structured outputs**  
   Every service returns Pydantic models or simple Python types, not free-form strings.

5. **No graph or ontology speculation**  
   All extraction and relationships are evidence-driven; no invented relations.

6. **Deterministic behavior where possible**  
   LLM calls are only used where inherently nondeterministic reasoning is needed (planning, synthesis). Everything else should be deterministic and testable.


---

## 2. Core Components

Core-level modules (excluding graph- and ontology-specific ones):

```text
core/
├── models.py
├── corpus_store.py
├── ingestion_service.py
├── vector_index.py
├── bm25_index.py
├── search_service.py
├── embedding_provider.py
├── llm_client.py
├── llm_tools.py
├── persona_runtime.py
└── prompt_manager.py
```

Graph and ontology services are specified in their own documents but must integrate cleanly with these core components.


---

## 3. Component Specifications

### 3.1 `CorpusStore`

**Purpose:** Persist and retrieve corpora and documents, with deduplication and basic metadata handling.

The CorpusStore is the only layer allowed to directly interact with the underlying database or file storage for documents. Other services must go through it.

#### Interface (Protocol)

```python
from typing import Protocol
from .models import Corpus, Document


class CorpusStore(Protocol):

    # Corpus management
    def create_corpus(self, corpus: Corpus) -> Corpus: ...

    def get_corpus(self, corpus_id: str) -> Corpus | None: ...

    def list_corpora(self) -> list[Corpus]: ...

    # Document management
    def add_document(self, document: Document) -> Document: ...

    def get_document(self, doc_id: str) -> Document | None: ...

    def list_documents(self, corpus_id: str) -> list[Document]: ...

    def find_by_hash(
        self,
        corpus_id: str,
        content_hash: str,
    ) -> Document | None: ...
```

#### Implementation Notes

- Initial implementation can be a SQLite-backed store with tables for:
  - `corpora`
  - `documents`
- Each `Document` must include:
  - `id`
  - `corpus_id`
  - `text`
  - `content_hash` (SHA-256 of normalized text)
  - `metadata` (JSON blob)
- The store does **not** create embeddings or update indices — that is `IngestionService`’s job.
- The store must be safe for use from multiple services within a single process.


---

### 3.2 `EmbeddingProvider`

**Purpose:** Provide vector embeddings for text using a local embedding model.

This must be abstract enough to support different providers (e.g., sentence-transformers, local Qwen, etc.).

#### Interface (Protocol)

```python
import numpy as np
from typing import Protocol, Sequence


class EmbeddingProvider(Protocol):
    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Return a 2D numpy array of shape (len(texts), embedding_dim)."""
```

#### Requirements

- Deterministic for a given model and input.
- Batched execution for performance.
- Handle CPU/GPU differences gracefully (configured via settings, not hardcoded).
- Should not perform caching on its own; caching can be layered above if desired.


---

### 3.3 `VectorIndex`

**Purpose:** Store and query embeddings for document chunks.

This is a per-corpus index. It does **not** own documents; it knows only about chunk IDs and embeddings.

#### Models

```python
from pydantic import BaseModel
from typing import Any


class VectorSearchHit(BaseModel):
    corpus_id: str
    chunk_id: str
    document_id: str
    score: float
    metadata: dict[str, Any] = {}
```

#### Interface (Protocol)

```python
from typing import Protocol, Sequence
import numpy as np


class VectorIndex(Protocol):

    def add_embeddings(
        self,
        corpus_id: str,
        chunk_ids: Sequence[str],
        embeddings: np.ndarray,
        document_ids: Sequence[str],
    ) -> None: ...

    def search(
        self,
        corpus_id: str,
        query_embedding: np.ndarray,
        k: int = 20,
    ) -> list[VectorSearchHit]: ...
```

#### Implementation Notes

- Initial implementation can use FAISS (FlatIP or HNSW) with one index per corpus.
- Embeddings are assumed to be L2-normalized upstream, or normalization is done consistently at this layer.
- Metadata about chunk-to-document mapping should be persisted, either in a sidecar SQLite table or a simple local file.


---

### 3.4 `BM25Index`

**Purpose:** Support lexical keyword search as a complement to vector search.

#### Models

```python
from pydantic import BaseModel


class BM25Hit(BaseModel):
    corpus_id: str
    document_id: str
    score: float
```

#### Interface (Protocol)

```python
from typing import Protocol, Sequence


class BM25Index(Protocol):

    def add_documents(
        self,
        corpus_id: str,
        doc_ids: Sequence[str],
        tokenized_docs: Sequence[list[str]],
    ) -> None: ...

    def search(
        self,
        corpus_id: str,
        query_tokens: list[str],
        k: int = 20,
    ) -> list[BM25Hit]: ...
```

#### Implementation Notes

- Start with a simple implementation using `rank_bm25`.
- Tokenization can be a very simple “lowercase + split on whitespace + strip punctuation” to begin with.
- The BM25 index does not need to be persisted across restarts in v1, but it’s preferable if it can be rebuilt cheaply from `CorpusStore` contents.


---

### 3.5 `IngestionService`

**Purpose:** Convert raw input (text, files, URLs) into stored documents and indexed chunks.

It orchestrates:

- deduplication via `CorpusStore`
- chunking of large texts
- embedding via `EmbeddingProvider`
- indexing via `VectorIndex` and `BM25Index`

#### Interface

```python
from pathlib import Path
from typing import Any


class IngestionService:

    def __init__(
        self,
        corpus_store: CorpusStore,
        embedding_provider: EmbeddingProvider,
        vector_index: VectorIndex,
        bm25_index: BM25Index | None = None,
    ):
        ...

    def ingest_text(
        self,
        corpus_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> Document: ...

    def ingest_file(
        self,
        corpus_id: str,
        path: Path,
        metadata: dict[str, Any] | None = None,
    ) -> Document: ...

    def ingest_url(
        self,
        corpus_id: str,
        url: str,
        metadata: dict[str, Any] | None = None,
    ) -> Document: ...
```

#### Behavior

1. **Normalization and hashing**
   - Normalize text (e.g., normalize newlines, strip trailing spaces).
   - Compute `content_hash = sha256(normalized_text)`.

2. **Deduplication**
   - Check `CorpusStore.find_by_hash(corpus_id, content_hash)`.
   - If a document exists, return it directly.

3. **Document creation**
   - Create a new `Document` with:
     - `id` (UUID)
     - `corpus_id`
     - `text`
     - `content_hash`
     - `metadata` (include source info; e.g., URL, file path).

4. **Chunking**
   - Split the document text into chunks of reasonable size (e.g., ~512 tokens or ~2000 characters).
   - Each chunk is associated with:
     - a `chunk_id` (e.g., `"{doc_id}::chunk_{n}"`)
     - offset metadata (character or token start/end).

5. **Embeddings + VectorIndex**
   - Use `EmbeddingProvider` to embed each chunk’s text.
   - Call `VectorIndex.add_embeddings` with `corpus_id`, `chunk_ids`, embeddings, and document IDs.

6. **BM25Index (optional)**
   - If `bm25_index` is configured, tokenize the document text or chunk texts and call `BM25Index.add_documents` accordingly.

7. **Return**
   - Return the `Document` object (representing the full doc, not the chunks).

#### Error Handling

- For `ingest_url`:
  - Network errors → raise `IngestionError` with appropriate message.
- For `ingest_file`:
  - Unsupported format or I/O error → raise `IngestionError`.

All such exceptions must be domain-specific, not HTTP-coded.


---

### 3.6 `SearchService`

**Purpose:** Provide unified search across BM25, vector, and hybrid modes.

#### Models

Assume `SearchHit` and `SearchResult` defined in `core/models.py`:

```python
from pydantic import BaseModel
from typing import Any


class SearchHit(BaseModel):
    corpus_id: str
    document_id: str
    chunk_id: str | None = None
    score: float
    snippet: str | None = None
    metadata: dict[str, Any] = {}


class SearchResult(BaseModel):
    corpus_id: str
    query: str
    hits: list[SearchHit]
```

#### Interface

```python
from typing import Literal


class SearchService:

    def __init__(
        self,
        corpus_store: CorpusStore,
        vector_index: VectorIndex | None,
        bm25_index: BM25Index | None,
        embedding_provider: EmbeddingProvider | None,
    ):
        ...

    def search(
        self,
        corpus_id: str,
        query: str,
        *,
        mode: Literal["bm25", "vector", "hybrid"] = "hybrid",
        k: int = 20,
    ) -> SearchResult: ...
```

#### Behavior

- **BM25 mode**:
  - Tokenize query.
  - Call `BM25Index.search`.
  - Fetch corresponding `Document`s (if needed) from `CorpusStore`.
  - Build `SearchHit` objects with scores and optional snippets.

- **Vector mode**:
  - Use `EmbeddingProvider.embed([query])` to create query embedding.
  - Call `VectorIndex.search`.
  - Fetch `Document`s as needed.
  - Build `SearchHit` objects.

- **Hybrid mode**:
  - Run both BM25 and vector search.
  - Normalize scores from both into [0, 1].
  - Combine by weighted sum:

    ```text
    combined_score = alpha * bm25_norm + beta * vector_norm
    ```

    with default `alpha = 0.5`, `beta = 0.5`.

  - Merge hits by `(corpus_id, document_id, chunk_id)` keys.
  - Sort by combined score and trim to top `k`.

- Snippet extraction can be naive at first (first N characters of chunk), with potential to improve later.

#### Error Handling

- If `mode="bm25"` but `bm25_index` is `None` → raise a configuration error (`SearchError`).
- If `mode="vector"` or `"hybrid"` but `vector_index` or `embedding_provider` is `None` → also raise `SearchError`.


---

### 3.7 `LLMClient`

**Purpose:** Provide a unified interface for calling local LLMs for generation tasks such as planning, QA, and extraction (graph layer uses it too).

#### Models

```python
from pydantic import BaseModel
from typing import Any


class LLMResult(BaseModel):
    text: str
    raw: Any | None = None
```

#### Interface (Protocol)

```python
from typing import Protocol


class LLMClient(Protocol):

    async def generate(
        self,
        user_prompt: str,
        *,
        system_prompt: str | None = None,
        json_schema: dict | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> LLMResult: ...
```

#### Requirements

- Must support:
  - standard text generation;
  - constrained JSON generation when `json_schema` is provided.
- Should include basic retry logic when the JSON output fails to parse:
  - re-prompt the model with an error message and the invalid JSON.
- A separate wrapper (e.g., `CachingLLMClient`) may:
  - hash `(system_prompt, user_prompt, json_schema, model_name)`
  - store responses in a local SQLite cache.

LLMClient must not assume a specific vendor or model; wiring happens in `llm_models/load_model.py` and config.


---

### 3.8 `PromptManager`

**Purpose:** Centralize prompt templates and variations for persona planning, research QA, extraction, and ontology usage.

#### Responsibilities

- Store base templates (e.g., in `./prompts/` directory or inline in code).
- Provide functions like:

```python
class PromptManager:

    def build_persona_planner_prompt(
        self,
        persona,
        question: str,
        manual_snippets: list[str],
        ontology_summary: str | None = None,
    ) -> tuple[str, str]:
        """Return (system_prompt, user_prompt)."""

    def build_research_qa_prompt(
        self,
        persona,
        question: str,
        evidence_snippets: list[str],
        ontology_summary: str | None = None,
    ) -> tuple[str, str]:
        ...
```

- Provide consistent grounding for the LLM about:
  - ontology types,
  - evidence semantics,
  - what is allowed and forbidden (e.g., no speculative edges).


---

### 3.9 `LLM Tools` (Planner & Research QA)

These tools orchestrate LLM calls and parse structured results.

#### `PersonaPlanner`

Purpose: Given persona manuals + question, produce a structured plan for how to investigate.

```python
from typing import Any
from .models import Persona


class PersonaPlanner:

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_manager: PromptManager,
    ):
        ...

    async def plan(
        self,
        persona: Persona,
        question: str,
        manual_snippets: list[str],
        ontology_context: str | None = None,
    ) -> dict[str, Any]:
        """Return a JSON-like plan (dict) describing steps, evidence priorities, and graph/search usage hints."""
```

The exact JSON structure can be refined, but it should include at least:

- high-level steps
- what entity types to focus on
- what relation types matter
- whether graph queries should be used

#### `ResearchQA`

Purpose: Given a question and a set of evidence chunks, produce an answer with citations.

```python
class ResearchQA:

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_manager: PromptManager,
    ):
        ...

    async def answer(
        self,
        persona: Persona,
        question: str,
        evidence_snippets: list[str],
        evidence_metadata: list[dict[str, Any]],
        ontology_context: str | None = None,
    ) -> dict[str, Any]:
        """Return structured answer data, including:
        - answer text
        - reasoning summary
        - list of cited document IDs / chunk IDs
        - assessment of evidence strength (if requested)
        """
```

The returned dict will typically be used to populate a `PersonaAnswer` model.


---

### 3.10 `PersonaRuntime`

**Purpose:** Coordinate the end-to-end flow of answering a question using a specific persona and topic corpus.

#### Inputs

- `persona_id`
- `topic_corpus_id` (research corpus)
- `question`

The PersonaRuntime must:

1. Load persona definition from `personas/` (via a `PersonaRegistry` or loader in `core/personas.py`).
2. Identify the persona’s manual corpus (`persona.manual_corpus_id`).
3. Use `SearchService` on the manual corpus to retrieve relevant snippets about how to approach such a question.
4. Use `PersonaPlanner` to generate a plan (possibly referencing ontology constraints).
5. Use `SearchService` on the research corpus to retrieve candidate evidence documents/chunks.
6. Optionally call into graph services (later phases) to refine the evidence set based on structural relationships.
7. Use `ResearchQA` to produce an answer and citations.
8. Return a `PersonaAnswer` model.

#### Interface

```python
from .models import PersonaAnswer


class PersonaRuntime:

    def __init__(
        self,
        corpus_store: CorpusStore,
        search_service: SearchService,
        persona_loader,  # e.g., a function or registry
        planner: PersonaPlanner,
        research_qa: ResearchQA,
        # later: graph_service, ontology_registry, etc.
    ):
        ...

    async def answer_question(
        self,
        persona_id: str,
        topic_corpus_id: str,
        question: str,
    ) -> PersonaAnswer:
        ...
```

#### Implementation Notes

- In early phases, graph and ontology integration can be stubbed or omitted.
- Evidence selection logic should remain simple and explicit:
  - top `N` hits from search;
  - optional re-ranking.


---

## 4. Error Semantics

All core services must use domain-specific exception types defined in a shared module (e.g., `core/errors.py`):

```python
class AlavistaError(Exception):
    """Base error for all domain-specific exceptions."""


class IngestionError(AlavistaError):
    ...


class VectorIndexError(AlavistaError):
    ...


class BM25IndexError(AlavistaError):
    ...


class SearchError(AlavistaError):
    ...


class LLMError(AlavistaError):
    ...


class PersonaError(AlavistaError):
    ...
```

No HTTP status codes or MCP error codes should appear in core. API and MCP adapters translate these into their own error formats.


---

## 5. Testing Strategy

### 5.1 Unit Tests

Core services must be thoroughly unit-tested with fakes/mocks where needed.

**Key unit test areas:**

- `CorpusStore`:
  - create/get/list corpora
  - add/get/list documents
  - dedupe via `content_hash`

- `IngestionService`:
  - ingest simple text
  - dedupe behavior
  - chunking output
  - error conditions for file/url ingestion (with fake I/O)

- `BM25Index` / `VectorIndex`:
  - adding docs/embeddings
  - basic search behavior

- `SearchService`:
  - BM25-only search
  - vector-only search
  - hybrid search combining results

- `LLMClient` wrappers:
  - caching behavior (if implemented)
  - JSON re-try logic (with fake LLM)

- `PersonaRuntime` (with fake LLM tools):
  - calls manual corpus search
  - calls research search
  - uses planner and QA output correctly

### 5.2 Integration Tests

Integration tests (in `tests/`) should cover:

- end-to-end: `IngestionService` → `SearchService` for a simple corpus;
- persona-driven flow with:
  - small test corpora,
  - fake LLMClient producing deterministic JSON/text.

Graph and ontology integration are covered in their own specs but will eventually hook into these flows.


---

## 6. Implementation Constraints and Anti-Patterns

- **No global singletons** for services; use explicit wiring in app/bootstrap code.
- **No long-running blocking I/O** in async functions.
- **No direct HTTP or MCP calls** inside core.
- **No hard-coded paths**; use configuration from `config/settings.py`.
- **No business logic in tests**; tests validate behavior, they don’t define it.


---

## 7. Definition of Done for Core Services (v1)

Core services are considered “v1 complete” when:

- CorpusStore, IngestionService, BM25Index, VectorIndex, SearchService, LLMClient, PromptManager, PersonaRuntime, and LLM tools are implemented as above.
- All have unit tests with meaningful coverage.
- A minimal end-to-end flow works:
  - create corpora,
  - ingest documents,
  - run hybrid search,
  - run a persona answer flow (even with stubbed LLMs).

At that point, the project has a **fully functioning semantic + persona reasoning engine**, ready for:

- Graph layer integration,
- Ontology constraints,
- MCP and HTTP adapters,
- UI and visualization layers.
