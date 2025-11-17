import { FormEvent, useState } from "react";

type Props = {
  onSubmit: (args: { name: string; type: string }) => Promise<void> | void;
  isSubmitting?: boolean;
};

const corpusTypes = [
  { value: "persona_manual", label: "Persona manual" },
  { value: "research", label: "Research" },
  { value: "global", label: "Global" }
];

export function CreateCorpusCard({ onSubmit, isSubmitting }: Props) {
  const [name, setName] = useState("");
  const [type, setType] = useState(corpusTypes[0]?.value ?? "research");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await onSubmit({ name, type });
    setName("");
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h2 className="text-base font-semibold">Create Corpus</h2>
      <form className="mt-3 flex flex-col gap-3" onSubmit={handleSubmit}>
        <label className="text-sm font-medium">
          Name
          <input
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="e.g., foia_2024_dump"
          />
        </label>
        <label className="text-sm font-medium">
          Type
          <select
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={type}
            onChange={(e) => setType(e.target.value)}
          >
            {corpusTypes.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex w-fit items-center rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {isSubmitting ? "Creating…" : "Create"}
        </button>
      </form>
    </div>
  );
}

export default CreateCorpusCard;
