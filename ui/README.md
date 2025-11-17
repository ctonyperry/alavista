# Alavista UI (Phase 12)

Lightweight React UI using Tailwind + Radix + shadcn/ui. Thin layer over the FastAPI HTTP API.

## Quickstart

```bash
cd ui
npm install
npm run dev
# set VITE_API_BASE_URL if your API is not at http://localhost:8000/api/v1
```

## Structure

- `src/components`: shared layout primitives.
- `src/features/*/components`: feature-scoped UI pieces.
- `src/lib/api`: fetcher, DTOs, React Query hooks.
- `src/lib/theme`: tokens/placeholders for theme variables.

## Notes

- UI is optional; all business logic stays server-side.
- React Query handles server state; avoid global stores for now.
- shadcn/ui components should be generated into `src/components` as needed.
