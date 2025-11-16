# Refactor: Rename "Personas" to "Analysis Profiles"

## 1. Motivation

Alavista originally used the term **persona** to describe domain-scoped expert configurations that guide how the system investigates a question.

However, the word "persona" is anthropomorphic and suggests an LLM "character" or simulated person. That is not what Alavista implements. The actual behavior is closer to:

- **Configuration + policy**
- that defines a **mode of analysis**
- which can be **selected per question**.

To better reflect this, we will move from **personas** to **analysis profiles**:

- Emphasize *function* (how the system reasons), not *identity* (a pretend person).
- Make clear that these are **configurable analysis strategies**, not agent "personalities".
- Improve conceptual clarity for contributors and integrators reading the docs and APIs.

For a transitional period, docs may refer to **"analysis profiles (formerly called personas)"** to maintain continuity.

## 2. What Personas Do Today

Based on the existing documentation:

- Personas are defined as **domain-constrained expert reasoning engines**, tied into:
  - ontology constraints (entity and relation whitelists),
  - graph + semantic search tools,
  - safety scaffolding (no speculation, provenance requirements),
  - curated corpus subsets,
  - persona-specific ingestion.

- They are implemented as **YAML configuration profiles** under something like:

  ```text
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

- A persona profile bundles:
  - Metadata (name, description, domain)
  - Tool whitelists (which MCP tools are allowed)
  - Ontology constraints (entity & relation whitelists)
  - Strategy rules (how to reason, escalate, narrow scope)
  - Persona-specific corpora (manuals, best practices, examples)
  - Safety rules (disclaimers, provenance requirements)
  - LLM prompt scaffolding
  - Memory / working context

- At runtime, **PersonaRuntime** and related services use the persona config to:
  - Interpret a question through an expert lens.
  - Select tools based on whitelists and ontology relevance.
  - Plan an investigation (via `PersonaPlanner`).
  - Pull in evidence from:
    - persona manuals (corpus type `persona_manual`),
    - research corpora,
    - graph and ontology services.
  - Produce a structured answer plus evidence (`PersonaAnswer`).

- The rest of the system surfaces personas via:
  - HTTP routes: `/personas`, `/personas/{persona_id}`, `/personas/{persona_id}/answer`, etc.
  - UI: "Persona Workbench" with a persona selector and persona-scoped Q&A.
  - MCP tools: `persona_list`, `persona_query`, `persona_ingest_resource`, etc.
  - Data models: `persona_id`, corpus `type: "persona_manual"`, etc.

In short: **personas are not people**; they are **switchable analysis configurations**.

## 3. New Term: "Analysis Profile"

### 3.1 Chosen Term

We adopt **Analysis Profile** as the primary, function-oriented replacement for "persona".

Rationale:

- **"Analysis"** matches Alavista's purpose as an investigative analysis platform.
- **"Profile"** clearly conveys configuration/policy, not an agent identity.
- The term scales across:
  - configuration files (profile definitions),
  - runtime logic (profile runtime / planner),
  - HTTP and MCP APIs (profile-scoped questions),
  - UI ("Analysis Workbench" / "Analysis Profiles").

During the transition, docs should clarify:

> "Analysis profiles (formerly called personas)" where needed.

### 3.2 Alternatives Considered

- **Investigation Profile**
  - Pros: Strong investigative flavor; fits forensic and graph-centric workflows.
  - Cons: Slightly more niche; "analysis" is broader and applies even when not strictly investigative.
- **Reasoning Profile**
  - Pros: Emphasizes epistemic and methodological constraints.
  - Cons: Somewhat abstract; less immediately obvious to new users than "analysis".
- **Analysis Mode / Investigation Mode**
  - Pros: Nicely conveys "switch system mode".
  - Cons: "Mode" sounds more ephemeral/temporary; "profile" better communicates structured config and policy.

Given this, **"Analysis Profile"** is chosen, with others rejected for now.

## 4. Conceptual Rename Mapping

Conceptually:

- **Persona** → **Analysis Profile**
- **Persona framework** → **Analysis Profile framework**
- **Persona-driven reasoning** → **Analysis-profile-driven reasoning**

In transitional docs, we can say:

- "Analysis profile framework (formerly persona framework)"
- "Analysis profiles (previously called personas)"

## 5. Planned Code-Level Mapping (Future Implementation)

This PR/document is **documentation-focused** only; code and APIs remain unchanged for now. However, to enable a future mechanical rename, here is the recommended mapping:

### 5.1 Classes, Modules, and Types

- `PersonaBase` → `AnalysisProfileBase`
- `PersonaRuntime` → `AnalysisProfileRuntime`
- `PersonaRegistry` → `AnalysisProfileRegistry`
- `PersonaPlanner` → `AnalysisProfilePlanner` (or keep `Planner` but adjust docstrings)
- `PersonaAnswer` → `AnalysisProfileAnswer` (if/when data models are renamed)

Directory/module paths (future):

- `core/personas/` → `core/analysis_profiles/` (or `core/profiles/`)
- `persona_profiles/` → `analysis_profiles/`
- YAML files:
  - `financial_forensics.yaml`, `flight_analysis.yaml`, etc. stay the same filenames but are now "analysis profile definitions" in docs.

### 5.2 Identifiers and Fields

- `persona_id` → `analysis_profile_id`
- Corpus type:
  - `type: "persona_manual"` → `type: "analysis_manual"` or `type: "profile_manual"` (to be decided; doc should explain mapping).
- Any model named `Persona` → `AnalysisProfile` where feasible.

### 5.3 API Routes and MCP Tools

HTTP routes (future mapping):

- `GET /personas` → `GET /analysis-profiles`
- `GET /personas/{persona_id}` → `GET /analysis-profiles/{profile_id}`
- `POST /personas/{persona_id}/answer` → `POST /analysis-profiles/{profile_id}/answer`
- Optional ingestion routes:
  - `/personas/{persona_id}/ingest/*` → `/analysis-profiles/{profile_id}/ingest/*`

MCP tools (future mapping):

- `persona_list()` → `analysis_profile_list()` or `profile_list()`
- `persona_select(id)` → `analysis_profile_select(id)`
- `persona_query(id, question)` → `analysis_profile_query(id, question)`
- `persona_ingest_resource(id, url | file)` → `analysis_profile_ingest_resource(...)`
- `persona_inspect(id)` → `analysis_profile_inspect(id)`
- `persona_explain(id, question)` → `analysis_profile_explain(id, question)`

**Backwards compatibility recommendation**: keep old names as aliases for at least one version, with deprecation warnings in docs.

## 6. Documentation Changes in This PR

This refactor is **doc-only**; no code or API behavior changes are introduced. The documentation should be updated as follows:

### 6.1 Product Overview (`docs/01_product_overview.md`)

- Replace "Persona-driven reasoning" with **"Analysis-profile-driven reasoning (formerly persona-driven)"**.
- Clarify that:
  - Each **analysis profile** has:
    - a manual corpus,
    - ontology whitelists (entities/relations),
    - interpretation strength rules (strong/medium/weak evidence).
- Where the term "persona" appears, adjust to:
  - "analysis profile (formerly called persona)" on first mention.
  - "analysis profile" thereafter.

### 6.2 Architecture Overview (`docs/02_architecture_overview.md`)

- Wherever the directory structure lists `personas/`, clarify in narrative:
  - "`personas/` — current code directory for analysis profiles (formerly called personas)."
- For route names that still use `/personas`, describe them as:
  - "Analysis profile routes (current path prefix: `/personas`)".

### 6.3 Data Models (`docs/03_data_models.md`)

- For `Corpus.type` and `persona_id`:
  - Document that `type: "persona_manual"` and `persona_id` are **legacy names** and conceptually refer to **analysis profiles**.
  - Add a note under `Corpus` explaining that future versions may rename:
    - `type: "persona_manual"` → `type: "analysis_manual"` / `type: "profile_manual"`,
    - `persona_id` → `analysis_profile_id`.

### 6.4 Core Services (`docs/04_core_services.md`)

- In sections describing `PersonaRuntime` and `PersonaPlanner`:
  - Add language like: "`PersonaRuntime` implements the analysis profile runtime (historically named with 'persona')."
  - Explain that each **analysis profile**:
    - is loaded via the existing `PersonaRegistry`,
    - has a manual corpus,
    - drives planning and answer generation.
- Clarify that `persona_id` in the runtime interface is conceptually the **analysis profile ID**.

### 6.5 Persona Framework Spec (`docs/07_persona_framework.md`)

- Retitle or subtitle the document as:
  - "Analysis Profile Framework (formerly Persona Framework)".
- Throughout the doc:
  - Replace conceptual mentions of "persona" with "analysis profile".
  - When referring to concrete code (e.g., `PersonaBase`, `core/personas/`), keep the code name but annotate:
    - "`PersonaBase` (base class for analysis profiles)"
    - "`core/personas/` directory (current home of analysis profiles)".
- At the top, explicitly state:
  - "In the code, these are currently called personas. Conceptually they are analysis profiles."

### 6.6 Roadmaps and Interfaces Docs

- `docs/roadmap_part_3_phases_6-8.md`:
  - "Persona Framework" → "Analysis Profile Framework".
  - "Each persona:" → "Each analysis profile (legacy term: persona):".
- `docs/roadmap_part_5_phases_12-14.md`:
  - "Persona Workbench" → "Analysis Workbench" or "Analysis Profile Workbench".
  - Add a parenthetical note that API paths currently use `/personas`, but conceptually these are analysis profiles.
- `docs/08_interfaces_and_tools.md`:
  - "Persona Routes", "Persona Q&A Routes" → "Analysis Profile Routes / Q&A Routes".
  - Explicitly note that:
    - `GET /personas` = "list analysis profiles".
    - `POST /personas/{persona_id}/answer` = "execute an analysis-profile-scoped reasoning pass".

### 6.7 Top-Level Package Docstring (`alavista/__init__.py`)

- Update the descriptive phrase from:
  - "persona-driven investigative reasoning"
  - to something like:
  - "analysis-profile-driven investigative reasoning (configurable analysis profiles, formerly called personas)."

## 7. Staging and Backwards Compatibility

Because code and API names are currently built around "persona", the rename should be staged:

1. **Stage 1 (this PR / doc-only)**:
   - Update **conceptual** language in docs to "analysis profiles".
   - Explain the historical "persona" naming and how it maps to analysis profiles.
   - Add this refactors document to guide future implementation work.

2. **Stage 2 (code + API rename)**:
   - Introduce new class names, modules, and endpoints using the "analysis profile" terminology.
   - Maintain old names as aliases or compatibility layers.
   - Update tests and internal references.

3. **Stage 3 (deprecation)**:
   - Deprecate the old "persona" names in docs and, if applicable, via API deprecation notices.
   - Eventually remove or freeze the legacy terminology.

This document is meant to guide and justify that process for future contributors.
