import { useState } from "react";
import { Route, Routes, useNavigate } from "react-router-dom";
import LayoutShell from "./components/LayoutShell";
import { Toaster } from "./components/ui/toaster";
import { useToast } from "./hooks/use-toast";
import {
  useCorpora,
  useCreateCorpus,
  useGraphFind,
  useGraphNeighbors,
  useGraphPaths,
  useIngestText,
  useIngestUrl,
  usePersonas,
  usePersonaQuestion,
  useRuns,
  useSearch
} from "./lib/api/hooks";
import CorporaTable from "./features/corpora/components/CorporaTable";
import CreateCorpusCard from "./features/corpora/components/CreateCorpusCard";
import IngestionTabs from "./features/ingestion/components/IngestionTabs";
import SearchForm from "./features/search/components/SearchForm";
import SearchResults from "./features/search/components/SearchResults";
import PersonaList from "./features/personas/components/PersonaList";
import PersonaQA from "./features/personas/components/PersonaQA";
import GraphSearch from "./features/graph/components/GraphSearch";
import RunSummary from "./features/runs/components/RunSummary";
import type { SearchMode } from "./lib/api/types";

const navItems = [
  { label: "Home", path: "/" },
  { label: "Corpora", path: "/corpora" },
  { label: "Ingestion", path: "/ingest" },
  { label: "Search", path: "/search" },
  { label: "Personas", path: "/personas" },
  { label: "Graph", path: "/graph" },
  { label: "Runs", path: "/runs" }
];

function HomePage() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="text-base font-semibold">Welcome</div>
        <p className="mt-2 text-sm text-muted-foreground">
          This lightweight UI connects to the Alavista HTTP API. Use the sidebar to manage corpora, ingest data, run search, and explore graph/persona features.
        </p>
      </div>
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="text-base font-semibold">System status</div>
        <p className="mt-2 text-sm text-muted-foreground">
          Configure API base via <code className="rounded bg-muted px-1 py-0.5">VITE_API_BASE_URL</code>. Defaults to <code className="rounded bg-muted px-1 py-0.5">http://localhost:8000/api/v1</code>.
        </p>
      </div>
    </div>
  );
}

function CorporaPage() {
  const { data: corpora = [], isLoading, refetch } = useCorpora();
  const createMutation = useCreateCorpus();
  const { toast } = useToast();

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="md:col-span-2">
          <CorporaTable corpora={corpora} isLoading={isLoading} />
        </div>
        <CreateCorpusCard
          isSubmitting={createMutation.isPending}
          onSubmit={async (input) => {
            try {
              await createMutation.mutateAsync(input);
              await refetch();
              toast({
                title: "Success",
                description: `Corpus "${input.name}" created successfully.`,
              });
            } catch (error) {
              toast({
                title: "Error",
                description: `Failed to create corpus: ${(error as Error).message}`,
                variant: "destructive",
              });
            }
          }}
        />
      </div>
    </div>
  );
}

function IngestionPage() {
  const { data: corpora = [], isLoading: isLoadingCorpora, refetch } = useCorpora();
  const ingestText = useIngestion("text");
  const ingestUrl = useIngestion("url");
  const { toast } = useToast();

  const isSubmitting = ingestText.isPending || ingestUrl.isPending;

  if (isLoadingCorpora) {
    return <div className="text-sm text-muted-foreground">Loading corpora…</div>;
  }
  if (!corpora.length) {
    return (
      <div className="text-sm text-muted-foreground">
        No corpora available. Create one first on the Corpora page.
        <button className="ml-2 text-primary underline" onClick={() => refetch()}>
          Refresh
        </button>
      </div>
    );
  }

  return (
    <IngestionTabs
      corpora={corpora}
      onIngestText={async (args) => {
        try {
          const result = await ingestText.mutateAsync(args);
          toast({
            title: "Success",
            description: `Document ingested: ${result.document_id} (${result.chunk_count} chunks)`,
          });
        } catch (error) {
          toast({
            title: "Error",
            description: `Failed to ingest text: ${(error as Error).message}`,
            variant: "destructive",
          });
        }
      }}
      onIngestUrl={async (args) => {
        try {
          const result = await ingestUrl.mutateAsync(args);
          toast({
            title: "Success",
            description: `Document ingested from URL: ${result.document_id} (${result.chunk_count} chunks)`,
          });
        } catch (error) {
          toast({
            title: "Error",
            description: `Failed to ingest URL: ${(error as Error).message}`,
            variant: "destructive",
          });
        }
      }}
      isSubmitting={isSubmitting}
    />
  );
}

function useIngestion(kind: "text" | "url") {
  const mutation = kind === "text" ? useIngestText() : useIngestUrl();
  return mutation;
}

function SearchPage() {
  const { data: corpora = [], isLoading: isLoadingCorpora } = useCorpora();
  const search = useSearch();
  const [mode, setMode] = useState<SearchMode>("hybrid");

  if (isLoadingCorpora) {
    return <div className="text-sm text-muted-foreground">Loading corpora…</div>;
  }
  if (!corpora.length) {
    return <div className="text-sm text-muted-foreground">No corpora available. Create one first.</div>;
  }

  return (
    <div className="space-y-4">
      <SearchForm
        corpora={corpora}
        defaultMode={mode}
        onSubmit={async (body) => {
          setMode(body.mode);
          await search.mutateAsync(body);
        }}
        isSubmitting={search.isPending}
      />
      <SearchResults
        results={search.data ?? []}
        mode={mode}
        isLoading={search.isPending}
        error={(search.error as Error)?.message ?? null}
      />
    </div>
  );
}

function PersonasPage() {
  const { data: personas = [], isLoading } = usePersonas();
  const ask = usePersonaQuestion();
  const [selectedPersona, setSelectedPersona] = useState<string | undefined>();

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <select
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={selectedPersona}
          onChange={(e) => setSelectedPersona(e.target.value)}
        >
          <option value="">Select persona</option>
          {personas.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>
      <PersonaList personas={personas} isLoading={isLoading} />
      {selectedPersona ? (
        <PersonaQA
          personaId={selectedPersona}
          onAsk={(args) => ask.mutateAsync(args)}
          answer={ask.data ?? null}
          isLoading={ask.isPending}
          error={(ask.error as Error)?.message ?? null}
        />
      ) : null}
    </div>
  );
}

function GraphPage() {
  const find = useGraphFind();
  const neighbors = useGraphNeighbors();
  const paths = useGraphPaths();
  const [result, setResult] = useState(find.data ?? null);
  const isLoading = find.isPending || neighbors.isPending || paths.isPending;
  const error = (find.error as Error)?.message ?? (neighbors.error as Error)?.message ?? (paths.error as Error)?.message ?? null;

  return (
    <GraphSearch
      onFind={async (args) => {
        const res = await find.mutateAsync(args);
        setResult(res);
      }}
      onNeighbors={async (args) => {
        const res = await neighbors.mutateAsync(args);
        setResult(res);
      }}
      onPath={async (args) => {
        const res = await paths.mutateAsync(args);
        setResult(res);
      }}
      results={result}
      isLoading={isLoading}
      error={error}
    />
  );
}

function RunsPage() {
  const { data: runs = [], isLoading } = useRuns();
  const navigate = useNavigate();

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading runs…</div>;
  }

  if (!runs.length) {
    return (
      <div className="text-sm text-muted-foreground">
        No runs yet. Trigger an investigation via API, then refresh.
        <button className="ml-2 text-primary underline" onClick={() => navigate(0)}>
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {runs.map((run) => (
        <RunSummary key={run.id} run={run} />
      ))}
    </div>
  );
}

function App() {
  return (
    <LayoutShell navItems={navItems}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/corpora" element={<CorporaPage />} />
        <Route path="/ingest" element={<IngestionPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/personas" element={<PersonasPage />} />
        <Route path="/graph" element={<GraphPage />} />
        <Route path="/runs" element={<RunsPage />} />
      </Routes>
      <Toaster />
    </LayoutShell>
  );
}

export default App;
