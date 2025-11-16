# Alavista – Product Overview

## 1. What Alavista Is

Alavista is a **local‑first investigative analysis platform** that combines:

- Document ingestion (FOIA drops, court filings, dumps, reports)
- Semantic search (BM25 + embeddings)
- A typed **entity/relationship graph** with provenance
- A minimal **ontology** for domain clarity
- **Analysis profile-driven reasoning** (e.g., investigative journalist, financial forensics)
- An **MCP server** so LLMs can use it as a tool
- An optional **HTTP API** for UI and automation

The initial flagship use case is deep analysis of the **Epstein corpus**, but the design must generalize to any investigative collection.

The intent is **civic and subversive**: give journalists, researchers, and citizens a serious tool to map structure and evidence, not just “search text.”


## 2. Core Principles

1. **Local‑first & privacy‑respecting**  
   - Runs locally on a single machine.
   - No required cloud LLMs or external APIs.
   - Target: 16 GB GPU for local LLMs & embeddings.

2. **Evidence‑first, not vibes‑first**  
   - All structural claims (who is connected to whom, via what) must be backed by:
     - document IDs,
     - snippets,
     - clear relation types,
     - confidence scores.

3. **Clear separation of layers**  
   - Text + corpora (documents, ingestion)
   - Semantic retrieval (BM25 + vector search)
   - Graph (typed nodes/edges with provenance)
   - Ontology (entity and relation vocab)
   - Analysis Profiles (how experts think)
   - LLM runtime (planning + QA)
   - Interfaces (MCP, HTTP)

4. **Minimal but explicit ontology**  
   - A small set of entity and relation types.
   - Enough to constrain reasoning and graphs.
   - Easy to extend later.

5. **Analysis profile-driven reasoning**  
   - Each analysis profile has:
     - “manual” corpora (how they work),
     - ontology whitelists (what they care about),
     - structured prompts.
   - The same corpus can be explored differently by different analysis profiles.

6. **Explainability & provenance**  
   - Every answer should be able to say:
     - “Here is the reasoning style used (analysis profile).”
     - “Here are the documents and relationships I relied on.”
     - “Here is how strong the evidence is.”

7. **Defensive licensing**  
   - Code: **AGPL‑3.0** to prevent proprietary capture.
   - Docs/data: can later use CC BY‑SA or similar.
   - Large organizations can use it, but must share modifications.

8. **Extensibility over cleverness**  
   - Clean modules & interfaces beat clever hacks.
   - The system should be pleasant to extend for new domains.


## 3. Target Users

- **Investigative journalists**  
  FOIA documents, emails, flight logs, banking records.

- **Civic researchers / watchdog NGOs**  
  Corruption, procurement, conflicts of interest, regulatory capture.

- **Power users / citizen investigators**  
  Technically capable individuals combining multiple public sources.

- **Domain‑specific analysts**  
  E.g., financial forensics, OSINT, policy analysis.


## 4. Key Capabilities (MVP Roadmap)

1. **Ingestion & corpora**
   - Create named corpora (research topics, analysis profile manuals).
   - Ingest text, URLs, and files.
   - Deduplicate via content hash.
   - Optional chunking of large documents.

2. **Search**
   - BM25 keyword search per corpus.
   - Vector search via embeddings.
   - Hybrid search combining both.

3. **Graph layer**
   - Typed nodes (person, organization, document, flight, account, etc.).
   - Typed edges (APPEARS_IN, MENTIONED_WITH, ON_FLIGHT, OWNS, HOLDS, TRANSFERRED_FUNDS, …).
   - Provenance for each edge (doc, snippet, page, confidence).

4. **Ontology layer**
   - Minimal, versioned ontology in a flat JSON file.
   - Defines valid entity and relation types + semantics.
   - Used by:
     - extraction,
     - graph validation,
     - analysis profiles,
     - LLM prompts.

5. **Analysis Profiles**
   - Analysis Profile definition files (YAML/JSON).
   - Each analysis profile has:
     - a manual corpus,
     - ontology whitelists (entity/relation types),
     - interpretation strength rules (strong/medium/weak evidence).

6. **Analysis Profile Runtime** (implemented as `PersonaRuntime`, to be renamed)
   - Given:
     - analysis profile,
     - research corpus,
     - question.
   - It:
     - consults analysis profile manuals,
     - queries semantic search,
     - optionally queries graph,
     - produces an answer + evidence. 

7. **MCP server**
   - Exposes ingest, search, graph, ontology, and analysis profile Q&A tools.
   - LLMs can use Alavista as a structured “brain” instead of ad‑hoc scraping.

8. **HTTP API**
   - Lightweight FastAPI surface.
   - For UI, scripts, dashboards, and local integrations.


## 5. Non‑Goals (for the near term)

- Full autonomous agents that wander the web unsupervised.
- Predictive models of human behavior or “guilt scoring.”
- Social graphs beyond literal textual evidence.
- Cloud hosting platform. The project is **local‑first**.
- Full UI/UX for non‑technical users in v1 (can come later).


## 6. Safety & Ethics Guardrails

1. **No speculation in the graph**
   - Edges represent relationships explicitly stated in text.
   - No “associated with,” “linked to,” etc. unless the text says so.

2. **Clear distinction between evidence and narrative**
   - The graph & ontology define evidence.
   - Analysis Profile answers are narrative *based on* evidence and must cite it.

3. **No magic labeling of guilt or criminality**
   - The system maps structure, not moral judgements.

4. **User is responsible for legal/ethical use**
   - The README and spec must clearly state intent and expected use.

5. **LLM prompts enforce this discipline**
   - System prompts must tell the model:
     - what concepts exist,
     - how to describe them,
     - what it must never claim without explicit support.


## 7. Licensing

- **Code**: use **AGPL‑3.0**.
- **Sample corpora / manuals / prompts**: later can be CC BY‑SA or similar.
- A short LICENSE section in the README must explain the rationale:
  - *“This is a civic‑oriented project intended to remain a public good and to resist proprietary enclosure.”*


## 8. How This File Should Guide AI Assistants

When AI assistants (Copilot/Cursor/ChatGPT) read this file, they should:

- Understand the *mission* and *constraints*.
- Avoid adding features that contradict:
  - local‑first,
  - evidence‑first,
  - no speculative social graphs.
- Use this as the conceptual backbone when implementing modules in other spec files.
- Preserve the layered architecture and keep concerns separate.

This file sets **intent**. All other files set **implementation detail**.
