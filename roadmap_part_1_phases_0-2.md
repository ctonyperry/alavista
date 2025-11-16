
# Roadmap Part 1 — Phases 0–2 (Full Detail)

## Phase 0 — Project Foundation
### Goals
- Establish project structure with clear module boundaries.
- Init Python environment with uv/poetry; adopt ruff for linting.
- Stand up unit test framework (pytest) and folder layout.
- Create Docker Compose stack for app + Ollama.
- Implement configuration system using Pydantic Settings.

### Directory Structure
alavista/
  core/
  interfaces/
  mcp/
  api/
  ingestion/
  search/
  vector/
  graph/
  ontology/
  personas/
  tests/
  docker/
  scripts/

### Core Steps
- Implement Settings class (pydantic), load `.env` and defaults.
- Add dependency injection container (simple factory funcs).
- Configure logging with structured logs.
- Write basic smoke test to verify test infra.

### Acceptance Criteria
- `pytest` runs and passes.
- `docker compose up` runs llm + app skeleton.
- Settings resolve from env and defaults.
- Repo structure matches above.

---

## Phase 1 — CorpusStore + Document Ingestion
### Goals
- Build persistent CorpusStore as SQLite + filesystem hybrid.
- Support ingest of: plain text, markdown, HTML, PDF (text only MVP).
- Chunk documents deterministically with configurable boundaries.
- Store document metadata including source_type, source_path.

### Components
#### CorpusStore
- create_corpus(name) -> corpus_id
- list_corpora() -> [...]
- get_corpus(corpus_id)
- delete_corpus(corpus_id)

#### DocumentStore
- add_document(corpus_id, text, metadata) -> document_id
- get_document(doc_id)
- list_documents(corpus_id)

#### IngestionService
- ingest_text(corpus_id, text, metadata)
- ingest_file(corpus_id, file_path)
- ingest_url(corpus_id, url)

### Chunking Rules
- Split by paragraphs; fallback to sentence splitting if paragraphs too large.
- Approximate target chunk size (e.g., 500–1500 chars).
- Normalize whitespace, preserve simple formatting markers.

### TDD Requirements
- Test corpus creation, listing, deletion.
- Test ingest_text round-trip.
- Test file ingestion of .txt and .md.
- Test chunking edge cases (empty lines, long lines, no punctuation).
- Test URL ingestion with deterministic fetch mock.

### Exit Criteria
- End-to-end ingestion pipeline works.
- CorpusStore + DocumentStore fully wired with tests.
- Search phase can consume chunked docs immediately.

---

## Phase 2 — BM25 Search + Core Indexing
### Goals
- Implement BM25 index builder.
- SearchService v1 using BM25 scoring.
- Re-rank results by match density and metadata boosts (MVP minimal).
- Return structured SearchResult objects, not freeform strings.

### Components
#### Tokenizer
- simple tokenizer splitting on whitespace, punctuation.
- lowercase + unicode normalize.
- filter stopwords in MVP (optional).

#### BM25Index
- build(corpus_chunks) -> internal index
- search(query, k) -> ranked hits

#### SearchService
- search_bm25(corpus_id, query, k=20)
- return: List[SearchResult(
    doc_id,
    chunk_id,
    score,
    excerpt,
    metadata
  )]

### TDD Requirements
- Test tokenizer determinism.
- Test bm25 scoring stability.
- Test multi-term query scoring.
- Test structured SearchResult format.
- Test negative cases (no results).

### Exit Criteria
- Querying BM25 over entire corpus works within ~100ms for <50k chunks.
- Search results consistently return structured objects.
- This layer becomes the retrieval spine for embeddings and graph extraction.
