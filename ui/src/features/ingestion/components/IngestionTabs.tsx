import { FormEvent, useState } from "react";
import { Corpus } from "../../../lib/api/types";

type Props = {
  corpora: Corpus[];
  onIngestText: (args: { corpus_id: string; text: string }) => Promise<void> | void;
  onIngestUrl: (args: { corpus_id: string; url: string }) => Promise<void> | void;
  onIngestFile?: (args: { corpus_id: string; file: File }) => Promise<void> | void;
  isSubmitting?: boolean;
  resultMessage?: string;
  errorMessage?: string;
};

export function IngestionTabs({
  corpora,
  onIngestText,
  onIngestUrl,
  onIngestFile,
  isSubmitting,
  resultMessage,
  errorMessage
}: Props) {
  const [corpusId, setCorpusId] = useState(corpora[0]?.id ?? "");
  const [tab, setTab] = useState<"text" | "url" | "file">("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");

  const targetCorpus =
    corpora.find((c) => c.id === corpusId)?.name ?? (corpora.length ? corpora[0].name : "No corpora");

  async function handleText(e: FormEvent) {
    e.preventDefault();
    await onIngestText({ corpus_id: corpusId, text });
    setText("");
  }

  async function handleUrl(e: FormEvent) {
    e.preventDefault();
    await onIngestUrl({ corpus_id: corpusId, url });
    setUrl("");
  }

  async function handleFile(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const files = (e.currentTarget.elements.namedItem("file") as HTMLInputElement | null)?.files;
    const file = files?.[0];
    if (file && onIngestFile) {
      await onIngestFile({ corpus_id: corpusId, file });
      (e.currentTarget.elements.namedItem("file") as HTMLInputElement).value = "";
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="text-sm font-medium">Target corpus</div>
        <select
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={corpusId}
          onChange={(e) => setCorpusId(e.target.value)}
        >
          {corpora.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.type})
            </option>
          ))}
        </select>
      </div>

      <div className="mt-4 flex gap-2 text-sm">
        {(["text", "url", "file"] as const).map((t) => (
          <button
            key={t}
            type="button"
            className={`rounded-md px-3 py-1 font-semibold ${
              tab === t ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
            }`}
            onClick={() => setTab(t)}
          >
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      {tab === "text" && (
        <form className="mt-4 flex flex-col gap-3" onSubmit={handleText}>
          <label className="text-sm font-medium">
            Text to ingest
            <textarea
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              rows={6}
              value={text}
              onChange={(e) => setText(e.target.value)}
              required
            />
          </label>
          <button
            className="w-fit rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Ingesting…" : `Ingest to ${targetCorpus}`}
          </button>
        </form>
      )}

      {tab === "url" && (
        <form className="mt-4 flex flex-col gap-3" onSubmit={handleUrl}>
          <label className="text-sm font-medium">
            URL
            <input
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              placeholder="https://example.com/article"
            />
          </label>
          <button
            className="w-fit rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Ingesting…" : `Fetch & ingest to ${targetCorpus}`}
          </button>
        </form>
      )}

      {tab === "file" && (
        <form className="mt-4 flex flex-col gap-3" onSubmit={handleFile}>
          <label className="text-sm font-medium">
            File
            <input
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              type="file"
              name="file"
              required
              accept=".txt,.md,.pdf"
            />
          </label>
          <button
            className="w-fit rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
            disabled={isSubmitting || !onIngestFile}
            title={onIngestFile ? undefined : "File ingest not yet wired"}
          >
            {isSubmitting ? "Uploading…" : `Upload to ${targetCorpus}`}
          </button>
        </form>
      )}

      {resultMessage && <div className="mt-3 text-sm text-foreground">{resultMessage}</div>}
      {errorMessage && <div className="mt-2 text-sm text-destructive">{errorMessage}</div>}
    </div>
  );
}

export default IngestionTabs;
