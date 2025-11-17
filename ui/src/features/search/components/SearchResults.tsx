import { SearchResult, SearchMode } from "../../../lib/api/types";

type Props = {
  results: SearchResult[];
  mode: SearchMode;
  isLoading?: boolean;
  error?: string | null;
};

export function SearchResults({ results, mode, isLoading, error }: Props) {
  if (isLoading) {
    return <div className="mt-4 text-sm text-muted-foreground">Fetching results…</div>;
  }

  if (error) {
    return (
      <div className="mt-4 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
        {error}
      </div>
    );
  }

  if (!results?.length) {
    return <div className="mt-4 text-sm text-muted-foreground">No results yet.</div>;
  }

  return (
    <div className="mt-4 space-y-3">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">Mode: {mode}</div>
      {results.map((r, idx) => (
        <div key={`${r.doc_id}-${r.chunk_id ?? idx}`} className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
            <span>Score: {r.score.toFixed(4)}</span>
            <span>
              Doc: {r.doc_id}
              {r.chunk_id ? ` • Chunk: ${r.chunk_id}` : ""}
            </span>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-foreground">{r.excerpt}</p>
        </div>
      ))}
    </div>
  );
}

export default SearchResults;
