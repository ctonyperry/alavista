# Alavista – Analysis Profile Framework Specification

Analysis Profiles are not gimmicks.  
They are *domain-constrained expert reasoning engines*, tied directly into:

- ontology constraints  
- graph + semantic search tools  
- safety scaffolding  
- curated corpus subsets  
- analysis profile-specific ingestion  

An analysis profile is a disciplined expert with a defined worldview — not an LLM “character.”

This document defines the entire analysis profile runtime architecture.

---

# 1. Purpose

The Analysis Profile Framework exists to:

1. Provide **domain-specific reasoning** without hallucination.  
2. Ensure each analysis profile uses **only legitimate tools** based on ontology constraints.  
3. Bind analysis profiles to **their own corpora + vector DBs** (training guides, techniques, best practices).  
4. Allow investigative questions to be interpreted through **expert lenses**.  
5. Keep the whole system explainable and safe by enforcing **epistemic boundaries**.  

Analysis Profiles turn Alavista from a search engine into a **modular investigative workstation.**

---

# 2. Architecture Overview

Directory structure (current implementation, to be renamed in future refactor):

```
core/personas/                    # To be renamed to core/analysis_profiles/
    persona_base.py              # To be renamed to analysis_profile_base.py
    persona_registry.py          # To be renamed to analysis_profile_registry.py
    persona_runtime.py           # To be renamed to analysis_profile_runtime.py
    persona_profiles/            # To be renamed to profile_definitions/
        financial_forensics.yaml
        flight_analysis.yaml
        legal_review.yaml
        victimology.yaml
        pattern_mapping.yaml
        general_investigator.yaml
```

Analysis Profiles consist of:

1. **Metadata** (name, description, domain)  
2. **Tool whitelists** (which MCP tools are allowed)  
3. **Ontology constraints** (entity & relation whitelists)  
4. **Strategy rules** (how to reason, escalate, or narrow scope)  
5. **Analysis Profile-specific corpora**  
6. **Safety rules**  
7. **LLM prompt scaffolding**  
8. **Memory / working context**  

---

# 3. Analysis Profile Definition Format

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
    - "This analysis profile interprets only explicit evidence. No inference."
  provenance_required: true
```

This YAML is loaded and validated by the `PersonaRegistry` (to be renamed `AnalysisProfileRegistry`).

---

# 4. PersonaBase (persona_base.py) — to be renamed `AnalysisProfileBase`

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

- Normalize analysis profile behaviors  
- Encapsulate domain epistemology  
- Ensure every analysis profile outputs consistent narrative + provenance  

---

# 5. PersonaRuntime (persona_runtime.py) — to be renamed `AnalysisProfileRuntime`

The brains of the analysis profile subsystem.

Takes:

- Analysis Profile definition  
- User question  
- Tools available  
- Ontology  
- Graph & Search Services  

Produces:

- A multi-step expert reasoning sequence  
- Final answer constrained by ontology + analysis profile rules  
- A provenance-enriched explanation  

## 5.1 Workflow

1. **Interpret the question**  
   - classify: structural, semantic, timeline, comparison, adjacency  
   - extract key entities (using ontology)

2. **Select tools**  
   - based on analysis profile’s tool whitelist  
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
   - analysis profile corpus context  

6. **Apply reasoning rules**  
   - strong relations emphasized  
   - weak relations flagged explicitly  
   - speculation removed  

7. **Format answer**  
   - clear evidence chain  
   - explicit provenance  
   - analysis profile’s “voice” (methodological, not personality)  

---

# 6. Analysis Profile Registry (persona_registry.py) — to be renamed `analysis_profile_registry.py`

Loads YAML analysis profile definitions, validates them, and produces `PersonaBase` instances (to be renamed `AnalysisProfileBase`).

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

# 7. Analysis Profile-Specific Corpora

Each analysis profile has:

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

This turns analysis profiles into **well-trained analysts**, not just prompt presets.

### MVP:  
local, static, vector DB.

### v1.1:  
MCP tool `persona_ingest_resource(url | file)` adds new info to analysis profile corpus.

---

# 8. Integration With Rest of System

The analysis profile runtime hooks into:

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

# 9. MCP Tools for Analysis Profiles

Current tool names (to be renamed in future implementation):

1. `persona_list()` — enumerate available analysis profiles (to be renamed `analysis_profile_list` or `profile_list`)  
2. `persona_select(id)` — switch active analysis profile (to be renamed `analysis_profile_select` or `profile_select`)  
3. `persona_query(id, question)` — full reasoning cycle (to be renamed `analysis_profile_query` or `profile_query`)  
4. `persona_ingest_resource(id, url | file)` — extend analysis profile’s corpus  
5. `persona_inspect(id)` — return config + rules (to be renamed `analysis_profile_inspect` or `profile_inspect`)  
6. `persona_explain(id, question)` — show step-by-step reasoning plan (to be renamed `analysis_profile_explain` or `profile_explain`)  

---

# 10. Safety & Hallucination Controls

1. No relation may be invented outside ontology.  
2. No chain-of-inference longer than what the graph directly supports.  
3. All weak links (co-mentions) must be labeled as weak.  
4. All analysis profile answers must show provenance if any structural claim is made.  
5. Analysis Profile must decline questions that require speculation.

Example:

> “Is X guilty?”

→ Analysis Profile responds:

> This cannot be answered. Only evidence-backed relationships can be returned.

---

# 11. Test Plan

## Unit Tests

- YAML loading  
- Entity & relation whitelists  
- Tool selector logic  
- Query→category classification  
- Query refinement rules  
- Analysis Profile-level safety filters  

## Integration Tests

- persona_query end-to-end  
- analysis profile reasoning vs ontology constraints  
- analysis profile → graph queries  
- analysis profile → semantic queries  
- analysis profile corpus ingestion  

## Black-Box Tests

Simulated investigative questions for each analysis profile:

- Financial Forensics: follow-the-money  
- Flight Analysis: manifest reconstruction  
- Legal Review: identify filing linkages  
- Victimology: cross-deposition synthesis  
- General Investigator: broad search-first reasoning  

---

# 12. Definition of Done

Analysis Profile framework is complete when:

- Analysis Profile definitions exist  
- PersonaRegistry loads YAML correctly  
- PersonaRuntime can perform multi-step reasoning  
- Tool selection is ontology-constrained  
- Corpus-per-analysis profile vector DBs working  
- Ingestion tool operational  
- Analysis Profile MCP tools integrated  
- 80%+ test coverage  
- Documented clearly  

