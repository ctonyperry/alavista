````markdown name=docs/wishlist.md
# Wishlist

> This document captures high-level wishlist features and design ideas for the system.
> Each item here is intentionally described at a conceptual level.
> **Important:** Before any wishlist item moves into the roadmap, it must be *carefully reasoned about* and pressure-tested (we will use GPT-based analysis for that step).

---

## 1. Local Investigative Agent Frontend (React)

**Idea:**
A React-based frontend that runs against the local API + local LLM, providing a Claude-like experience but entirely on local/private infrastructure.

**Goals / Behavior:**

- Present a **task-oriented chat UI** where the user can:
  - Define research tasks (e.g., “Investigate Company X’s relationships to Y between 2018–2021.”).
  - Ask follow-up questions and refine the investigation scope.
- Expose **multi-step, agentic workflows**:
  - The agent proposes an investigation plan.
  - The user can approve/modify the plan.
  - The agent executes the plan step-by-step, calling internal tools (graph, semantic, vector, etc.).
- Emphasize:
  - Conservative inference,
  - Explicit evidence vs analysis vs speculation,
  - High transparency of intermediate steps and sources.

**Key UI Surfaces:**

- **Chat Panel:**
  - User ↔ agent dialogue, with clearly labeled:
    - Initial task,
    - Proposed plan,
    - Step updates,
    - Interim and final summaries.

- **Plan / Step Viewer:**
  - A list of investigation steps:
    - Status per step (`planned`, `running`, `completed`, `failed`, `skipped`).
    - Short description of each step.
  - Ability to:
    - Pause or resume execution.
    - Advance one step at a time.
    - Re-plan from a given step or checkpoint.

- **Tool Log & Evidence Panel:**
  - Summarized view of tool calls (which tool, arguments, high-level result).
  - Evidence list with:
    - Source type (internal doc, graph edge, external web resource, etc.).
    - Short snippet or description.
    - Link back to the originating tool call.

**Notes:**

- The design should match existing docs conventions (explicit phases, clear responsibilities, and separation of concerns).
- Before implementation, this needs a **careful reasoning pass** to:
  - Validate UX complexity vs. value,
  - Decide on the minimal viable set of views,
  - Define concrete data contracts between backend and frontend.

---

## 2. Run / Investigation Abstraction

**Idea:**
Introduce a first-class “Run” (or “Investigation”) abstraction that models long-lived, multi-step tasks across tools, and is shared between the API and the agent logic.

**Responsibilities:**

- Represent an investigation as a persistent object with:
  - `id`, `status`, `task`.
  - Ordered `messages` (user + agent).
  - `plan` (list of steps with metadata).
  - `steps` (actual executed steps with summaries and references).
  - `tool_calls` (log for reproducibility and audit).
  - `evidence` (normalized references to documents, nodes, and external resources).

- Provide a clean lifecycle:
  - `created` → `running` → `completed` or `error` (with optional `cancelled`).
  - Optional step-wise control (`pause`, `step`, `resume`).

- Support:
  - Replaying / inspecting past runs.
  - Forking: start a new run from a previous checkpoint or state.

**Integration Points:**

- The React frontend uses Run objects via the HTTP API.
- The agent engine updates Run state as it:
  - Plans,
  - Calls tools,
  - Synthesizes intermediate and final results.

**Notes:**

- The Run model should be documented at the same level of precision as the existing docs for tools and workflows.
- Needs a **careful reasoning pass** (via GPT) to:
  - Define which fields are essential vs optional,
  - Avoid overfitting to a single agent persona,
  - Keep the model extensible for future workflows.

---

## 3. Core Services Layer (Shared Between API and MCP)

**Idea:**
Create a clearly defined “core services” layer that contains all domain logic (search, graph, vector, investigation engine), with both MCP and HTTP APIs as thin adapters on top.

**Components:**

- `search_service`:
  - Semantic search, vector search, graph queries, and any composite queries.
  - Pure Python functions or classes, no transport/protocol concerns.

- `agent_engine`:
  - Local-LLM-based orchestration:
    - Planning, tool selection, validation loops.
    - Run lifecycle management (creating, stepping, finalizing).
  - Uses `search_service` directly.

- `run_store`:
  - Persistence for Runs, steps, tool logs, evidence.
  - Initial implementation may be in-memory; later can be swapped for a database.

**Adapter Layers:**

- MCP server:
  - Wraps `search_service` functions as MCP tools for external MCP hosts (e.g., Claude Desktop).
- HTTP API (e.g., FastAPI):
  - Wraps `agent_engine` and optionally `search_service` for the React frontend.

**Notes:**

- This separation is critical for keeping parity between MCP and API behavior.
- Needs **careful reasoning** to:
  - Define clear, minimal interfaces for `search_service` and `agent_engine`,
  - Avoid leaking transport-specific logic into the core.

---

## 4. Evidence-First Reporting and Corroboration

**Idea:**
Systematically structure all agent outputs so that evidence, analysis, and speculative hypotheses are explicitly separated and link back to concrete tool outputs.

**Behavioral Requirements:**

- Every investigative summary should be structured as:
  1. **Evidence** – source-specific, with citations.
  2. **Analysis** – reasoning based only on the presented evidence.
  3. **Hypotheses** – clearly labeled, with stated confidence and gaps.

- Evidence objects should:
  - Identify:
    - Source type (e.g., internal document, graph edge, external article).
    - Originating tool call.
    - Minimal identifying metadata (id, title, date, etc.).
  - Be reusable across:
    - Different runs,
    - Different views (evidence panel, citations in summaries).

- Corroboration:
  - Encourage the agent to seek multiple, independent sources for key claims.
  - Highlight when:
    - A claim is based on a single weak source,
    - Internal data contradicts external data.

**UI/UX Affordances (Wishlist):**

- Visual distinction between:
  - Internal vs external sources,
  - Direct vs indirect evidence.
- “Challenge this conclusion” action:
  - Triggers a secondary pass where the agent actively searches for counter-evidence or alternative explanations.

**Notes:**

- Aligns with the investigative journalist persona and with conservative inference.
- Requires a **careful reasoning pass** to:
  - Define a robust evidence schema,
  - Decide on how much structure to enforce on agent outputs vs. post-processing.

---

## 5. Local LLM Orchestration & Safety Defaults

**Idea:**
Standardize how the local LLM (via Ollama or similar) is used for orchestration, including safety defaults, planning constraints, and resource usage limits.

**Considerations:**

- Model selection:
  - Target 7–8B class models (e.g., Llama 3.1 8B, Qwen2.5 7B) optimized for:
    - Tool use,
    - Multi-step reasoning,
    - Low hallucination under constrained prompts.

- Prompting strategy:
  - Shared system prompts that:
    - Define the investigative persona,
    - Enforce evidence-first reasoning,
    - Penalize speculation without support.
  - Separate prompts for:
    - Planning,
    - Tool argument construction,
    - Synthesis/reporting.

- Resource and safety controls:
  - Hard limits on:
    - Max steps per Run,
    - Max tokens per response,
    - Max depth of graph exploration per request (to prevent unbounded “thousands of hops” runaway behavior).
  - Logging and diagnostics suitable for:
    - Debugging planning failures,
    - Analyzing incorrect tool use.

**Notes:**

- The exact prompting and safety configuration should be derived from experiments and GPT-assisted design.
- Needs a **careful reasoning pass** to:
  - Balance thoroughness with latency,
  - Define a minimal viable “safe default” configuration.

---

## 6. Optional External Research Integration (Web Search as a Tool)

**Idea:**
Treat web / external research as an optional, explicit tool in the system, clearly separated from internal corpus access, to preserve privacy expectations and auditability.

**Behavior:**

- Web search exposed as a single, well-scoped tool:
  - Minimal input: short queries, no raw documents or sensitive content.
  - Outputs: summarized results plus citations/links.

- System behavior with external research:
  - Clearly marks which claims rely on external sources.
  - Option to disable external search at:
    - Run level,
    - System level.

- UI affordances:
  - Toggles or indicators that:
    - Show when external search is active.
    - Allow the user to restrict or expand external research usage.

**Notes:**

- Should remain optional and off by default in privacy-sensitive contexts.
- Needs careful reasoning (with GPT) to:
  - Define how queries are constructed to avoid leaking sensitive internal information,
  - Specify safeguards for mixing internal and external evidence.

---

## 7. Evaluation and Replay of Investigations

**Idea:**
Provide an internal mechanism to replay, inspect, and evaluate investigations to improve prompts, tool design, and agent strategies over time.

**Capabilities:**

- Run replay:
  - Ability to re-run an investigation with:
    - The same inputs (task, options),
    - Possibly different model/prompt/tool configurations.
  - Compare:
    - Tool usage patterns,
    - Final summaries,
    - Evidence sets.

- Evaluation:
  - Define a small set of benchmark tasks (internal corpus only) to:
    - Measure tool selection quality,
    - Measure factual accuracy vs known ground truth,
    - Detect regression when models or prompts change.

- Diagnostics:
  - Aggregate metrics:
    - Average steps per run,
    - Common failure modes (e.g., missing key entity, shallow graph exploration),
    - Frequency of unsupported claims.

**Notes:**

- This is foundational for improving agent quality given a smaller local model.
- Requires a careful reasoning pass to:
  - Decide on a minimal and realistic evaluation protocol,
  - Integrate with existing logging and run storage.

---

## 8. Documentation & UX Coherence

**Idea:**
Ensure the new API, agent engine, and frontend are documented in a way that is consistent with the existing `docs/` style and conventions.

**Documentation Areas:**

- High-level architecture:
  - Relationship between:
    - MCP server,
    - Core services (`search_service`, `agent_engine`),
    - API,
    - React frontend,
    - Local LLM runtime.

- Run model:
  - Fields,
  - Lifecycle,
  - Example Run JSON.

- Frontend flows:
  - Example “Task → Plan → Steps → Evidence → Summary” walkthrough.
  - Screenshots or diagrams once available.

**Notes:**

- As with other wishlist items, documentation structure should be reasoned about, and we can use GPT to:
  - Propose initial outlines,
  - Check for completeness and consistency with existing docs.
````