import { FormEvent, useState } from "react";
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
        <div className="space-y-2">
          <label htmlFor="corpus-name" className="text-sm font-medium">
            Name
          </label>
          <Input
            id="corpus-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="e.g., foia_2024_dump"
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="corpus-type" className="text-sm font-medium">
            Type
          </label>
          <Select value={type} onValueChange={setType}>
            <SelectTrigger id="corpus-type">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {corpusTypes.map((c) => (
                <SelectItem key={c.value} value={c.value}>
                  {c.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button type="submit" disabled={isSubmitting} className="w-fit">
          {isSubmitting ? "Creating…" : "Create"}
        </Button>
      </form>
    </div>
  );
}

export default CreateCorpusCard;
