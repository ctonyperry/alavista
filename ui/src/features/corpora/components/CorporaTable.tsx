import { Corpus } from "../../../lib/api/types";

type Props = {
  corpora: Corpus[];
  isLoading?: boolean;
};

export function CorporaTable({ corpora, isLoading }: Props) {
  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading corpora…</div>;
  }

  if (!corpora?.length) {
    return <div className="text-sm text-muted-foreground">No corpora yet.</div>;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
      <table className="min-w-full divide-y divide-border text-sm">
        <thead className="bg-muted/50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-foreground">Name</th>
            <th className="px-4 py-2 text-left font-medium text-foreground">Type</th>
            <th className="px-4 py-2 text-left font-medium text-foreground">Docs</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {corpora.map((c) => (
            <tr key={c.id} className="hover:bg-muted/50">
              <td className="px-4 py-2 font-medium">{c.name}</td>
              <td className="px-4 py-2">{c.type}</td>
              <td className="px-4 py-2">{c.doc_count ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default CorporaTable;
