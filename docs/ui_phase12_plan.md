# Phase 12 UI Plan (React + Tailwind + Radix + shadcn/ui)

This document captures the locked frontend stack decision, integration approach, and scaffolding plan for the lightweight UI in Phase 12.

## Stack Decision & Rationale

- React (Vite SPA) + TypeScript
- Tailwind CSS with design tokens + CSS variables (light/dark)
- Radix UI primitives
- shadcn/ui generated components (Tailwind + Radix wrappers)
- lucide-react icons
- React Query for server state
- react-hook-form + zod for forms/validation
- Vitest + React Testing Library + MSW for tests

Why: polished defaults without a designer, AI/codegen friendly, composable and themeable, modern/accessibility-focused, fits local-first/open-source posture, keeps UI thin over FastAPI.

## Integration & Project Layout

UI calls HTTP API only; business logic stays in FastAPI/core services. MCP parity is preserved by avoiding UI-only logic.

```
ui/
  src/
    components/                  # shared shadcn-based components
    features/
      corpora/
      ingestion/
      search/
      personas/
      graph/
      runs/                      # optional if Run model exposed
      .../components             # feature-scoped components
    lib/
      api/                       # client.ts, types.ts, hooks.ts
      theme/                     # tokens, css vars
      hooks/                     # shared hooks
    pages/ | routes/             # route-level views
    index.css                    # tailwind base
  public/
  tailwind.config.ts
  postcss.config.js
  tsconfig.json
  vite.config.ts
  package.json
```

## Theming, Tokens, Accessibility

- Tokens: colors (primary/secondary/surface/neutral), spacing scale, radius, shadows, typography.
- Tailwind extends tokens; use CSS variables for light/dark aligned with shadcn defaults.
- Accessibility: Radix primitives for focus/ARIA; AA contrast; focus-visible styles; aria-live for async updates; keyboard navigation enforced.

## Development Plan (Phase 12)

1) Bootstrap Vite + React + TS in `ui/`; add Tailwind/PostCSS; base `LayoutShell` with sidebar/topbar.
2) Install/configure Radix, shadcn/ui (generate button, input, select, textarea, dialog, sheet, tabs, card, badge, table, tooltip, dropdown-menu, toast, skeleton, pagination), lucide-react, React Query, react-hook-form + zod, MSW, Vitest + RTL.
3) API client: `lib/api/client.ts` (fetcher with error handling), `types.ts` (DTOs for corpus/doc/search/persona/graph/run/evidence), `hooks.ts` (React Query wrappers).
4) Routing: `/` home, `/corpora`, `/ingest`, `/search`, `/personas`, `/graph`, `/runs` (optional). Shell layout with responsive sidebar.
5) State: React Query for server state; local UI state otherwise; avoid global store initially.
6) Backend touchpoints:
   - Corpora: `GET/POST /api/v1/corpora`, optional stats endpoint.
   - Ingestion: `POST /api/v1/ingest/text|url|file` (corpus id required).
   - Search: `POST /api/v1/search` (`bm25|vector|hybrid`).
   - Personas: `GET /api/v1/personas`, persona Q&A endpoint.
   - Graph: `POST /api/v1/graph/find_entity|neighbors|paths` (or current names).
   - Runs (if available): `GET/POST /api/v1/runs`, `GET /api/v1/runs/{id}`, control endpoints for step/resume/cancel.

## Design Spec (Pages & Interactions)

- Layout: sidebar + topbar shell; cards/sections; tabs for modes; toasts for async feedback; skeletons for loading; alerts for errors.
- Home: cards for system status and recent corpora/personas; quick actions.
- Corpora: table + create dialog; badges for types; doc counts if available.
- Ingestion: tabs for text/url/file; select corpus; show `doc_id` + `chunk_count`; inline errors; toasts on success.
- Search: mode tabs; query input; corpus select; results list with score/excerpt/doc/chunk; empty/loading states.
- Personas: list/detail; ask question; answer with citations/evidence placeholders.
- Graph Explorer: find/neighbors/paths; tables for nodes/edges; depth/limit indicators; optional viz placeholder.
- Runs (optional): plan/stepper + evidence list; controls for pause/resume/step if API supports.

Visual hierarchy: primary actions at top-right of panels; consistent spacing; sm tables, md forms; focus-visible; AA contrast.

## Component Scaffolding (First Pass)

Shared (`src/components/`):
- `LayoutShell` (sidebar/topbar), `DataTable`, `PageHeader`, `StatusBadge`, form wrappers (shadcn + RHF).

Corpora (`features/corpora/components/`):
- `CorporaTable` (props: `corpora`, `isLoading`)
- `CreateCorpusDialog` (props: `isOpen`, `onOpenChange`, `onSubmit`, `isSubmitting`)

Ingestion (`features/ingestion/components/`):
- `IngestionTabs` (props: `corpora`, handlers for text/url/file ingest, success/error display)

Search (`features/search/components/`):
- `SearchForm` (props: `corpora`, `defaultMode`, `onSubmit`, `isSubmitting`)
- `SearchResults` (props: `results`, `mode`, `isLoading`, `error?`)

Personas (`features/personas/components/`):
- `PersonaList` (props: `personas`, `isLoading`)
- `PersonaQA` (props: `personaId`, `onAsk`, `answer?`, `citations?`, `isLoading`, `error?`)

Graph (`features/graph/components/`):
- `GraphSearch` (props: `onFindNode`, `onNeighbors`, `onPath`, `results`, `isLoading`, `error?`; list/table + viz placeholder)

Runs (`features/runs/components/`, optional):
- `RunSummary` (props: `run`, control callbacks; renders plan/steps/evidence)

## Reference API Shapes

- Corpus: `{ id: string; name: string; type: 'persona_manual'|'research'|'global'; doc_count?: number }`
- Ingest result: `{ doc_id: string; chunk_count: number }`
- Search result: `{ score: number; excerpt: string; doc_id: string; chunk_id?: string; corpus_id?: string }`
- Persona: `{ id: string; name: string; description?: string }`
- Persona answer: `{ answer: string; citations?: Array<{ doc_id?: string; corpus_id?: string; snippet?: string }> }`
- Graph: `{ nodes: Array<{ id: string; label: string; type?: string }>; edges: Array<{ source: string; target: string; type?: string }> }`
- Run (if exposed): `{ id: string; status: 'created'|'running'|'completed'|'error'|'cancelled'; task: string; plan: Step[]; steps: StepExec[]; evidence: Evidence[] }`

## Testing Strategy

- Use Vitest + React Testing Library for components/pages.
- MSW for API mocking in tests.
- Prefer behavior assertions over snapshots; include accessibility role/text checks.
