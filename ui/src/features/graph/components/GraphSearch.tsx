import { FormEvent, useState } from "react";
import { GraphResponse } from "../../../lib/api/types";

type Props = {
  onFind: (args: { query: string }) => Promise<GraphResponse> | Promise<void> | void;
  onNeighbors: (args: { node_id: string; depth?: number }) => Promise<GraphResponse> | Promise<void> | void;
  onPath: (args: { source_id: string; target_id: string; max_depth?: number }) => Promise<GraphResponse> | Promise<void> | void;
  results?: GraphResponse | null;
  isLoading?: boolean;
  error?: string | null;
};

export function GraphSearch({ onFind, onNeighbors, onPath, results, isLoading, error }: Props) {
  const [findQuery, setFindQuery] = useState("");
  const [nodeId, setNodeId] = useState("");
  const [neighborDepth, setNeighborDepth] = useState(1);
  const [source, setSource] = useState("");
  const [target, setTarget] = useState("");
  const [pathDepth, setPathDepth] = useState(3);

  async function handleFind(e: FormEvent) {
    e.preventDefault();
    await onFind({ query: findQuery });
  }
  async function handleNeighbors(e: FormEvent) {
    e.preventDefault();
    await onNeighbors({ node_id: nodeId, depth: neighborDepth });
  }
  async function handlePath(e: FormEvent) {
    e.preventDefault();
    await onPath({ source_id: source, target_id: target, max_depth: pathDepth });
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold">Find Entity</h3>
        <form className="mt-2 flex gap-2" onSubmit={handleFind}>
          <input
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Entity name"
            value={findQuery}
            onChange={(e) => setFindQuery(e.target.value)}
          />
          <button className="rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground" disabled={isLoading}>
            Find
          </button>
        </form>
      </div>

      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold">Neighbors</h3>
        <form className="mt-2 flex gap-2" onSubmit={handleNeighbors}>
          <input
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Node ID"
            value={nodeId}
            onChange={(e) => setNodeId(e.target.value)}
          />
          <input
            className="w-24 rounded-md border border-input bg-background px-3 py-2 text-sm"
            type="number"
            min={1}
            max={5}
            value={neighborDepth}
            onChange={(e) => setNeighborDepth(Number(e.target.value))}
          />
          <button className="rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground" disabled={isLoading}>
            Fetch
          </button>
        </form>
      </div>

      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold">Path</h3>
        <form className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-4" onSubmit={handlePath}>
          <input
            className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Source ID"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          />
          <input
            className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            placeholder="Target ID"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          />
          <input
            className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            type="number"
            min={1}
            max={10}
            value={pathDepth}
            onChange={(e) => setPathDepth(Number(e.target.value))}
          />
          <button className="rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground" disabled={isLoading}>
            Path
          </button>
        </form>
      </div>

      {isLoading && <div className="text-sm text-muted-foreground">Fetching graph…</div>}
      {error && <div className="text-sm text-destructive">{error}</div>}
      {results && (
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="text-sm font-semibold">Results</div>
          <div className="mt-2 text-xs text-muted-foreground">Nodes: {results.nodes.length} • Edges: {results.edges.length}</div>
          <div className="mt-2 space-y-2 text-sm">
            <div>
              <div className="font-semibold">Nodes</div>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {results.nodes.map((n) => (
                  <li key={n.id}>
                    {n.id} — {n.label} {n.type ? `(${n.type})` : ""}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="font-semibold">Edges</div>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {results.edges.map((e, idx) => (
                  <li key={`${e.source}-${e.target}-${idx}`}>
                    {e.source} -> {e.target} {e.type ? `(${e.type})` : ""}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default GraphSearch;
