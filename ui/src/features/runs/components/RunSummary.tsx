import { Run } from "../../../lib/api/types";

type Props = {
  run: Run;
};

export function RunSummary({ run }: Props) {
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex items-center justify-between text-sm">
          <div className="font-semibold">{run.task}</div>
          <span className="rounded-md bg-muted px-2 py-1 text-xs font-medium uppercase">{run.status}</span>
        </div>
      </div>
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="font-semibold">Plan</div>
        <ul className="mt-2 space-y-1 text-sm">
          {run.plan.map((p) => (
            <li key={p.id}>
              <span className="mr-2 rounded bg-muted px-2 py-1 text-xs uppercase">{p.status}</span>
              {p.title}
            </li>
          ))}
        </ul>
      </div>
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="font-semibold">Steps</div>
        <ul className="mt-2 space-y-2 text-sm">
          {run.steps.map((s) => (
            <li key={s.id} className="rounded border border-border px-3 py-2">
              <div className="flex items-center justify-between">
                <span className="font-medium">{s.title}</span>
                <span className="rounded bg-muted px-2 py-1 text-xs uppercase">{s.status}</span>
              </div>
              {s.summary ? <p className="mt-1 text-muted-foreground">{s.summary}</p> : null}
            </li>
          ))}
        </ul>
      </div>
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="font-semibold">Evidence</div>
        <ul className="mt-2 space-y-1 text-sm">
          {run.evidence.map((e) => (
            <li key={e.id} className="rounded bg-muted px-3 py-2">
              <div className="text-xs uppercase text-muted-foreground">{e.source_type}</div>
              <div className="font-medium">{e.ref}</div>
              {e.snippet ? <div className="text-muted-foreground">{e.snippet}</div> : null}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default RunSummary;
