import { Persona } from "../../../lib/api/types";

type Props = {
  personas: Persona[];
  isLoading?: boolean;
};

export function PersonaList({ personas, isLoading }: Props) {
  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading personas…</div>;
  }
  if (!personas?.length) {
    return <div className="text-sm text-muted-foreground">No personas found.</div>;
  }

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {personas.map((p) => (
        <div key={p.id} className="rounded-lg border border-border bg-card p-4">
          <div className="text-sm font-semibold">{p.name}</div>
          <div className="mt-1 text-sm text-muted-foreground">{p.description || "No description"}</div>
        </div>
      ))}
    </div>
  );
}

export default PersonaList;
