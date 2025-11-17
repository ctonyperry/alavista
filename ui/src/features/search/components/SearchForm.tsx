import { FormEvent, useState } from "react";
import { Corpus, SearchMode } from "../../../lib/api/types";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../components/ui/select";

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
        <div className="space-y-2">
          <label htmlFor="search-corpus" className="text-sm font-medium">
            Corpus
          </label>
          <Select value={corpusId} onValueChange={setCorpusId}>
            <SelectTrigger id="search-corpus">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {corpora.map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <label htmlFor="search-mode" className="text-sm font-medium">
            Mode
          </label>
          <Select value={mode} onValueChange={(v) => setMode(v as SearchMode)}>
            <SelectTrigger id="search-mode">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="bm25">BM25</SelectItem>
              <SelectItem value="vector">Vector</SelectItem>
              <SelectItem value="hybrid">Hybrid</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="mt-3 space-y-2">
        <label htmlFor="search-query" className="text-sm font-medium">
          Query
        </label>
        <Input
          id="search-query"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What do you want to find?"
          required
        />
      </div>
      <div className="mt-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Searching…" : "Search"}
        </Button>
      </div>
    </form>
  );
}

export default SearchForm;
