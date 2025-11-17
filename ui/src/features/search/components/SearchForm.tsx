import { FormEvent, useState } from "react";
import { Corpus, SearchMode } from "../../../lib/api/types";

type Props = {
  corpora: Corpus[];
  defaultMode?: SearchMode;
  onSubmit: (args: { corpus_id: string; query: string; mode: SearchMode }) => Promise<void> | void;
  isSubmitting?: boolean;
};

export function SearchForm({ corpora, defaultMode = "hybrid", onSubmit, isSubmitting }: Props) {
  const [query, setQuery] = useState("");
  const [corpusId, setCorpusId] = useState(corpora[0]?.id ?? "");
  const [mode, setMode] = useState<SearchMode>(defaultMode);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await onSubmit({ corpus_id: corpusId, query, mode });
  }

  return (
    <form className="rounded-lg border border-border bg-card p-4" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <label className="text-sm font-medium">
          Corpus
          <select
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={corpusId}
            onChange={(e) => setCorpusId(e.target.value)}
          >
            {corpora.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium">
          Mode
          <select
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={mode}
            onChange={(e) => setMode(e.target.value as SearchMode)}
          >
            <option value="bm25">BM25</option>
            <option value="vector">Vector</option>
            <option value="hybrid">Hybrid</option>
          </select>
        </label>
        <label className="text-sm font-medium md:col-span-1 md:hidden">Query</label>
      </div>
      <div className="mt-3">
        <input
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What do you want to find?"
          required
        />
      </div>
      <div className="mt-3">
        <button
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Searching…" : "Search"}
        </button>
      </div>
    </form>
  );
}

export default SearchForm;
