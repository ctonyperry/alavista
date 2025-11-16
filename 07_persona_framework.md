# Alavista – Persona Framework Specification

Personas are not gimmicks.  
They are *domain-constrained expert reasoning engines*, tied directly into:

- ontology constraints  
- graph + semantic search tools  
- safety scaffolding  
- curated corpus subsets  
- persona-specific ingestion  

A persona is a disciplined expert with a defined worldview — not an LLM “character.”

This document defines the entire persona runtime architecture.

---

# 1. Purpose

The Persona Framework exists to:

1. Provide **domain-specific reasoning** without hallucination.  
2. Ensure each persona uses **only legitimate tools** based on ontology constraints.  
3. Bind personas to **their own corpora + vector DBs** (training guides, techniques, best practices).  
4. Allow investigative questions to be interpreted through **expert lenses**.  
5. Keep the whole system explainable and safe by enforcing **epistemic boundaries**.  

Personas turn Alavista from a search engine into a **modular investigative workstation.**

---

# 2. Architecture Overview

Directory structure:

```
core/personas/
    persona_base.py
    persona_registry.py
    persona_runtime.py
    persona_profiles/
        financial_forensics.yaml
        flight_analysis.yaml
        legal_review.yaml
        victimology.yaml
        pattern_mapping.yaml
        general_investigator.yaml
```

Personas consist of:

1. **Metadata** (name, description, domain)  
2. **Tool whitelists** (which MCP tools are allowed)  
3. **Ontology constraints** (entity & relation whitelists)  
4. **Strategy rules** (how to reason, escalate, or narrow scope)  
5. **Persona-specific corpora**  
6. **Safety rules**  
7. **LLM prompt scaffolding**  
8. **Memory / working context**  

---

# 3. Persona Definition Format

Stored as YAML:

```yaml
name: "Financial Forensics Analyst"
description: "Tracks monetary flow, asset structures, and hidden ownership."
id: "financial_forensics"

entity_whitelist:
  - Person
  - Organization
  - Account
  - Property
  - Transaction

relation_whitelist:
  - OWNS
  - HOLDS
  - TRANSFERRED_FUNDS
  - APPEARS_IN
  - MENTIONED_WITH   # treated as weak links

strength_rules:
  strong:
    - OWNS
    - HOLDS
    - TRANSFERRED_FUNDS
  weak:
    - MENTIONED_WITH
  contextual:
    - APPEARS_IN

tools_allowed:
  - semantic_search
  - hybrid_search
  - graph_find_entity
  - graph_neighbors
  - graph_paths
  - graph_stats
  - ingest_resource
  - corpus_lookup

corpus:
  vector_db_path: "personas/financial_forensics/vec.faiss"
  metadata_path: "personas/financial_forensics/meta.jsonl"
  allow_user_extension: true

reasoning:
  approach: |
    Prioritize financial evidence. Build timelines of assets, accounts,
    transfers, intermediaries. Cross-reference entity identities with ownership
    edges and document sources. Associate high-confidence relations first,
    then consider weak signals cautiously.

  disallowed_phrases:
    - "likely"
    - "probably"
    - "suggests"
    - "appears to imply"

safety:
  disclaimers:
    - "This persona interprets only explicit evidence. No inference."
  provenance_required: true
```

This YAML is loaded and validated by the PersonaRegistry.

---

# 4. PersonaBase (persona_base.py)

Abstract class:

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
    corpus_paths: dict

    @abstractmethod
    def select_tools(self, query: str) -> list[str]:
        ...

    @abstractmethod
    def refine_query(self, query: str) -> str:
        ...

    @abstractmethod
    def format_answer(self, result: dict) -> str:
        ...
```

Purpose:

- Normalize persona behaviors  
- Encapsulate domain epistemology  
- Ensure every persona outputs consistent narrative + provenance  

---

# 5. PersonaRuntime (persona_runtime.py)

The brains of the persona subsystem.

Takes:

- Persona definition  
- User question  
- Tools available  
- Ontology  
- Graph & Search Services  

Produces:

- A multi-step expert reasoning sequence  
- Final answer constrained by ontology + persona rules  
- A provenance-enriched explanation  

## 5.1 Workflow

1. **Interpret the question**  
   - classify: structural, semantic, timeline, comparison, adjacency  
   - extract key entities (using ontology)

2. **Select tools**  
   - based on persona’s tool whitelist  
   - query category  
   - ontology-type relevance  
   - safety rules (e.g., forbid speculation)

3. **Plan execution**  
   - Determine search or graph-first order  
   - Graph-first for structural questions (“Who is connected to X?”)  
   - Semantic-first for content questions (“What happened on this date?”)  

4. **Perform calls** to MCP tools or internal services

5. **Aggregate results**  
   - graph edges  
   - semantic hits  
   - persona corpus context  

6. **Apply reasoning rules**  
   - strong relations emphasized  
   - weak relations flagged explicitly  
   - speculation removed  

7. **Format answer**  
   - clear evidence chain  
   - explicit provenance  
   - persona’s “voice” (methodological, not personality)  

---

# 6. Persona Registry (persona_registry.py)

Loads YAML persona definitions, validates them, and produces PersonaBase instances.

API:

```python
class PersonaRegistry:

    def load_all(self) -> None:
        ...

    def get_persona(self, persona_id: str) -> PersonaBase:
        ...

    def list_personas(self) -> list[str]:
        ...
```

The registry ensures consistency between:

- ontology  
- tool names  
- corpus locations  

---

# 7. Persona-Specific Corpora

Each persona has:

- **its own FAISS index**  
- **its own metadata JSONL**  
- **its own corpus ingestion tool**  
- **its own best-practices knowledge base**

These provide:

- investigative techniques  
- real-world examples  
- definitions  
- procedures  
- analytic frameworks  
- domain reasoning scaffolds  

This turns personas into **well-trained analysts**, not just prompt presets.

### MVP:  
local, static, vector DB.

### v1.1:  
MCP tool `persona_ingest_resource(url | file)` adds new info to persona corpus.

---

# 8. Integration With Rest of System

The persona runtime hooks into:

- **SearchService**  
  - BM25, vector, hybrid  

- **GraphService**  
  - structural queries  
  - relations interpretation  

- **OntologyService**  
  - constrain relationships  
  - restrict tool usage  

- **LLM Client**  
  - controlled reasoning  
  - no unauthorized interpretations  

---

# 9. MCP Tools for Personas

1. `persona_list()` — enumerate available personas  
2. `persona_select(id)` — switch active persona  
3. `persona_query(id, question)` — full reasoning cycle  
4. `persona_ingest_resource(id, url | file)` — extend persona’s corpus  
5. `persona_inspect(id)` — return config + rules  
6. `persona_explain(id, question)` — show step-by-step reasoning plan  

---

# 10. Safety & Hallucination Controls

1. No relation may be invented outside ontology.  
2. No chain-of-inference longer than what the graph directly supports.  
3. All weak links (co-mentions) must be labeled as weak.  
4. All persona answers must show provenance if any structural claim is made.  
5. Persona must decline questions that require speculation.

Example:

> “Is X guilty?”

→ Persona responds:

> This cannot be answered. Only evidence-backed relationships can be returned.

---

# 11. Test Plan

## Unit Tests

- YAML loading  
- Entity & relation whitelists  
- Tool selector logic  
- Query→category classification  
- Query refinement rules  
- Persona-level safety filters  

## Integration Tests

- persona_query end-to-end  
- persona reasoning vs ontology constraints  
- persona → graph queries  
- persona → semantic queries  
- persona corpus ingestion  

## Black-Box Tests

Simulated investigative questions for each persona:

- Financial Forensics: follow-the-money  
- Flight Analysis: manifest reconstruction  
- Legal Review: identify filing linkages  
- Victimology: cross-deposition synthesis  
- General Investigator: broad search-first reasoning  

---

# 12. Definition of Done

Persona framework is complete when:

- Persona definitions exist  
- PersonaRegistry loads YAML correctly  
- PersonaRuntime can perform multi-step reasoning  
- Tool selection is ontology-constrained  
- Corpus-per-persona vector DBs working  
- Ingestion tool operational  
- Persona MCP tools integrated  
- 80%+ test coverage  
- Documented clearly  

