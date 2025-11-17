import { FormEvent, useState } from "react";
import { PersonaAnswer } from "../../../lib/api/types";

type Props = {
  personaId: string;
  onAsk: (args: { persona_id: string; question: string }) => Promise<PersonaAnswer> | Promise<void> | void;
  answer?: PersonaAnswer | null;
  isLoading?: boolean;
  error?: string | null;
};

export function PersonaQA({ personaId, onAsk, answer, isLoading, error }: Props) {
  const [question, setQuestion] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await onAsk({ persona_id: personaId, question });
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
        <label className="text-sm font-medium">
          Ask persona
          <textarea
            className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            required
          />
        </label>
        <button
          className="w-fit rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
          disabled={isLoading}
        >
          {isLoading ? "Asking…" : "Ask"}
        </button>
      </form>

      {error && <div className="mt-3 text-sm text-destructive">{error}</div>}
      {answer && (
        <div className="mt-3 rounded-md border border-border bg-background p-3 text-sm">
          <div className="font-semibold">Answer</div>
          <p className="mt-1 leading-relaxed">{answer.answer}</p>
          {answer.citations?.length ? (
            <div className="mt-2 text-xs text-muted-foreground">
              Citations:{" "}
              {answer.citations.map((c, idx) => (
                <span key={idx} className="mr-2">
                  {c.doc_id ?? "doc"} {c.snippet ? `(${c.snippet.slice(0, 40)}…)` : ""}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

export default PersonaQA;
